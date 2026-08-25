from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_13_release_candidate_completion_security_and_readiness_reaudit_contract_v01.json"
REQUIREMENTS_PATH = PROJECT_ROOT / "configs/project_readiness/stage08_project_completion_and_release_readiness_requirements_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_13_release_candidate_completion_security_and_readiness_reaudit_evidence_v01.json"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"


class ReauditValidationError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReauditValidationError(f"JSON root must be an object: {path}")
    return value


def _load_requirements(path: Path = REQUIREMENTS_PATH) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ReauditValidationError("requirements registry is empty")
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(key for key, count in Counter(values).items() if count != 1)
    if duplicates:
        raise ReauditValidationError(f"{label} must occur exactly once: {duplicates}")
    return values


def _aggregate(statuses: Sequence[str]) -> str:
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    return "PASS"


def validate_evidence_relations(
    evidence: Mapping[str, Any],
    contract: Mapping[str, Any],
    requirements: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_13_release_candidate_completion_security_and_readiness_reaudit_evidence_v01":
        raise ReauditValidationError("unexpected evidence schema_version")
    if evidence.get("task_id") != contract.get("task_id"):
        raise ReauditValidationError("task id mismatch")
    if evidence.get("profile") != "SCIENTIFIC_VALIDATION":
        raise ReauditValidationError("profile must remain SCIENTIFIC_VALIDATION")

    expected_ids = _unique((row["requirement_id"] for row in requirements), "registered requirement")
    if len(expected_ids) != int(contract["assessment_object"]["requirement_count"]):
        raise ReauditValidationError("registered requirement count mismatch")
    expected_by_id = {row["requirement_id"]: row for row in requirements}
    expected_dimensions = sorted({row["dimension_id"] for row in requirements})
    if len(expected_dimensions) != int(contract["assessment_object"]["dimension_count"]):
        raise ReauditValidationError("registered dimension count mismatch")

    results = evidence.get("requirement_results")
    if not isinstance(results, list):
        raise ReauditValidationError("requirement_results must be a list")
    observed_ids = _unique((str(row.get("requirement_id", "")) for row in results), "evidence requirement")
    if set(observed_ids) != set(expected_ids):
        raise ReauditValidationError("evidence requirement set differs from the 24-row registry")

    allowed = set(contract["assessment_object"]["allowed_requirement_statuses"])
    result_by_id: dict[str, Mapping[str, Any]] = {}
    non_pass_finding_ids: set[str] = set()
    statuses_by_dimension: dict[str, list[str]] = defaultdict(list)
    for result in results:
        requirement_id = str(result["requirement_id"])
        source = expected_by_id[requirement_id]
        status = str(result.get("status", ""))
        if status not in allowed:
            raise ReauditValidationError(f"illegal status for {requirement_id}: {status}")
        if source["aggregation_role"] == "mandatory" and status == "SKIPPED":
            raise ReauditValidationError(f"mandatory requirement cannot be SKIPPED: {requirement_id}")
        if result.get("dimension_id") != source["dimension_id"]:
            raise ReauditValidationError(f"dimension mismatch for {requirement_id}")
        if not str(result.get("observed_evidence", "")).strip():
            raise ReauditValidationError(f"observed evidence missing for {requirement_id}")
        paths = result.get("evidence_paths")
        if not isinstance(paths, list) or not paths or not all(isinstance(path, str) and path for path in paths):
            raise ReauditValidationError(f"evidence paths missing for {requirement_id}")
        finding_ids = result.get("finding_ids")
        if not isinstance(finding_ids, list):
            raise ReauditValidationError(f"finding_ids must be a list for {requirement_id}")
        if status == "PASS" and finding_ids:
            raise ReauditValidationError(f"PASS cannot carry a blocking finding: {requirement_id}")
        if status != "PASS" and not finding_ids:
            raise ReauditValidationError(f"non-PASS is silent: {requirement_id}")
        non_pass_finding_ids.update(str(value) for value in finding_ids)
        statuses_by_dimension[source["dimension_id"]].append(status)
        result_by_id[requirement_id] = result

    findings = evidence.get("open_findings")
    if not isinstance(findings, list):
        raise ReauditValidationError("open_findings must be a list")
    finding_ids = _unique((str(row.get("finding_id", "")) for row in findings), "finding")
    if set(finding_ids) != non_pass_finding_ids:
        raise ReauditValidationError("finding set does not exactly cover all non-PASS results")
    for finding in findings:
        for key in ("severity", "owner", "consequence", "disposition"):
            if not str(finding.get(key, "")).strip():
                raise ReauditValidationError(f"finding field missing: {finding['finding_id']}/{key}")
        references = finding.get("requirement_ids")
        if not isinstance(references, list) or not references:
            raise ReauditValidationError(f"finding has no requirements: {finding['finding_id']}")
        for requirement_id in references:
            if requirement_id not in result_by_id or finding["finding_id"] not in result_by_id[requirement_id]["finding_ids"]:
                raise ReauditValidationError(f"finding relation mismatch: {finding['finding_id']}/{requirement_id}")

    dimension_results = evidence.get("dimension_results")
    if not isinstance(dimension_results, list):
        raise ReauditValidationError("dimension_results must be a list")
    observed_dimension_ids = _unique((str(row.get("dimension_id", "")) for row in dimension_results), "dimension result")
    if sorted(observed_dimension_ids) != expected_dimensions:
        raise ReauditValidationError("dimension result set mismatch")
    recomputed_dimensions = {dimension: _aggregate(statuses_by_dimension[dimension]) for dimension in expected_dimensions}
    for row in dimension_results:
        dimension = str(row["dimension_id"])
        if row.get("status") != recomputed_dimensions[dimension]:
            raise ReauditValidationError(f"dimension aggregate mismatch: {dimension}")

    aggregate = evidence.get("aggregate_verdict")
    if not isinstance(aggregate, Mapping):
        raise ReauditValidationError("aggregate_verdict must be an object")
    completion_statuses = [recomputed_dimensions[value] for value in contract["aggregation"]["project_completion_dimensions"]]
    release_statuses = [recomputed_dimensions[value] for value in contract["aggregation"]["external_release_dimensions"]]
    expected_completion = _aggregate(completion_statuses)
    expected_release = _aggregate(release_statuses)
    release_blockers = aggregate.get("release_blockers")
    if not isinstance(release_blockers, list) or not release_blockers:
        raise ReauditValidationError("current external release verdict must retain explicit blockers")
    if expected_release == "PASS" and release_blockers:
        expected_release = "BLOCKED"
    if aggregate.get("project_completion_verdict") != expected_completion:
        raise ReauditValidationError("project completion aggregate mismatch")
    if aggregate.get("external_release_readiness") != expected_release:
        raise ReauditValidationError("external release aggregate mismatch")
    if aggregate.get("release_class") != ("ready" if expected_release == "PASS" else "not_ready"):
        raise ReauditValidationError("release class mismatch")
    if aggregate.get("John_release_decision_required") is not True:
        raise ReauditValidationError("John release decision boundary missing")

    expected_requirement_counts = {key: 0 for key in ("PASS", "FAIL", "BLOCKED", "SKIPPED")}
    expected_requirement_counts.update(Counter(str(row["status"]) for row in results))
    expected_dimension_counts = {key: 0 for key in ("PASS", "FAIL", "BLOCKED")}
    expected_dimension_counts.update(Counter(recomputed_dimensions.values()))
    if aggregate.get("requirement_status_counts") != expected_requirement_counts:
        raise ReauditValidationError("requirement status counts mismatch")
    if aggregate.get("dimension_status_counts") != expected_dimension_counts:
        raise ReauditValidationError("dimension status counts mismatch")

    gates = evidence.get("external_release_gates")
    if not isinstance(gates, Mapping):
        raise ReauditValidationError("external_release_gates must be an object")
    exact_gates = {
        "hosted_CI": "BLOCKED_NOT_OBSERVED",
        "GitHub_secret_scanning": "BLOCKED_NOT_ENABLED_OR_OBSERVED",
        "public_repository": "BLOCKED_NOT_CREATED",
        "John_release_authorization": "BLOCKED_NOT_GRANTED",
    }
    for key, value in exact_gates.items():
        if gates.get(key) != value:
            raise ReauditValidationError(f"external gate overstated: {key}")
    if gates.get("external_actions_performed") != 0:
        raise ReauditValidationError("external actions must remain zero")

    next_block = evidence.get("next_block_reference")
    if not isinstance(next_block, Mapping) or next_block.get("task_id") != "ST08_14_public_repository_publication_and_external_release" or next_block.get("status") != "proposed_not_authorized":
        raise ReauditValidationError("ST08_14 must remain proposed_not_authorized")
    if evidence.get("audit_procedure_status") != "PASS":
        raise ReauditValidationError("audit procedure did not validate")
    if evidence.get("technical_status") != "FAIL" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise ReauditValidationError("audited-object technical status/readiness mismatch")
    return {
        "requirements": len(results),
        "dimensions": recomputed_dimensions,
        "project_completion_verdict": expected_completion,
        "external_release_readiness": expected_release,
        "findings": len(findings),
    }


def validate_repository_bindings(
    contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
    workflow_text: str | None = None,
) -> dict[str, Any]:
    assessment = contract["assessment_object"]
    if _sha256(PROJECT_ROOT / assessment["requirements_path"]) != assessment["requirements_sha256_before_audit"]:
        raise ReauditValidationError("requirements registry changed during the audit")
    if _sha256(PROJECT_ROOT / assessment["baseline_audit_path"]) != assessment["baseline_audit_sha256"]:
        raise ReauditValidationError("baseline audit changed during the re-audit")

    protected_source = contract["protected_artifacts_source"]
    source_path = PROJECT_ROOT / protected_source["path"]
    if _sha256(source_path) != protected_source["sha256_before_audit"]:
        raise ReauditValidationError("protected-artifact source record changed")
    protected = _load_json(source_path)[protected_source["json_key"]]
    if len(protected) != int(protected_source["expected_count"]):
        raise ReauditValidationError("protected-artifact count mismatch")
    mismatches = []
    for relative, expected in protected.items():
        path = PROJECT_ROOT / relative
        actual = _sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append({"path": relative, "expected": expected, "actual": actual})
    if mismatches:
        raise ReauditValidationError(f"protected scientific artifact mismatch: {mismatches}")

    workflow_text = workflow_text if workflow_text is not None else WORKFLOW_PATH.read_text(encoding="utf-8")
    required_commands = [
        "scripts/st08_13_release_candidate_reaudit.py",
        "tests.test_release_candidate_reaudit_st08_13",
    ]
    missing = [command for command in required_commands if command not in workflow_text]
    if missing:
        raise ReauditValidationError(f"configured CI omits ST08_13 assurance: {missing}")
    if evidence.get("protected_artifacts") != {"expected": len(protected), "mismatches": 0, "status": "PASS"}:
        raise ReauditValidationError("evidence protected-artifact summary mismatch")
    return {"protected": len(protected), "mismatches": 0, "CI_commands": required_commands}


def validate_registered_evidence() -> dict[str, Any]:
    contract = _load_json(CONTRACT_PATH)
    evidence = _load_json(EVIDENCE_PATH)
    relations = validate_evidence_relations(evidence, contract, _load_requirements())
    bindings = validate_repository_bindings(contract, evidence)
    return {"status": "PASS", "relations": relations, "bindings": bindings}


def main() -> int:
    try:
        result = validate_registered_evidence()
    except (ReauditValidationError, csv.Error, json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
