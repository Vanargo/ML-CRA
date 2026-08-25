from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_13C_prospective_release_candidate_v02_reaudit_contract_v01.json"
REQUIREMENTS_PATH = PROJECT_ROOT / "configs/project_readiness/stage08_project_completion_and_release_readiness_requirements_v02.csv"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_13C_release_candidate_v02_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_13C_prospective_release_candidate_v02_reaudit_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_13C_prospective_release_candidate_v02_reaudit_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"


class ProspectiveReauditError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProspectiveReauditError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise ProspectiveReauditError(f"CSV is empty or lacks a header: {path}")
    return fields, rows


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _path_list_sha256(paths: Iterable[str]) -> str:
    return _sha256_bytes("".join(f"{path}\n" for path in sorted(paths)).encode("utf-8"))


def _unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise ProspectiveReauditError(f"{label} must occur exactly once: {duplicates}")
    return values


def _aggregate(statuses: Sequence[str]) -> str:
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses:
        return "BLOCKED"
    return "PASS"


def _tracked_candidate_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    policy = release_assurance._load_json(root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    forbidden = [
        path
        for path in tracked
        if release_assurance.classify_public_path(path, policy, root)
        not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}
    ]
    if forbidden:
        raise ProspectiveReauditError(f"tracked candidate contains policy-excluded paths: {forbidden}")
    exclusions = set(contract["current_candidate_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise ProspectiveReauditError(f"candidate cycle-breaking path is not tracked: {missing}")
    return tracked


def build_manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    exclusions = set(contract["current_candidate_manifest"]["cycle_breaking_exclusions"])
    rows: list[dict[str, str]] = []
    for relative in _tracked_candidate_paths(root, contract):
        if relative in exclusions:
            continue
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append(
            {
                "relative_path": relative,
                "sha256": _sha256_bytes(payload),
                "size_bytes": str(len(payload)),
            }
        )
    return rows


def write_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    rows = build_manifest_rows(root, contract)
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=contract["current_candidate_manifest"]["fields"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    tracked = sorted(
        [row["relative_path"] for row in rows]
        + list(contract["current_candidate_manifest"]["cycle_breaking_exclusions"])
    )
    return {
        "status": "PASS",
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256(path),
    }


def validate_manifest(
    fields: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    root: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    expected_fields = contract["current_candidate_manifest"]["fields"]
    if list(fields) != expected_fields:
        raise ProspectiveReauditError("candidate manifest schema mismatch")
    row_paths = _unique((str(row.get("relative_path", "")) for row in rows), "candidate manifest path")
    if row_paths != sorted(row_paths):
        raise ProspectiveReauditError("candidate manifest paths are not ordinally sorted")
    tracked = _tracked_candidate_paths(root, contract)
    exclusions = sorted(contract["current_candidate_manifest"]["cycle_breaking_exclusions"])
    expected_rows = sorted(set(tracked) - set(exclusions))
    if row_paths != expected_rows:
        missing = sorted(set(expected_rows) - set(row_paths))
        extra = sorted(set(row_paths) - set(expected_rows))
        raise ProspectiveReauditError(f"candidate manifest path set mismatch: missing={missing} extra={extra}")
    for row in rows:
        relative = row["relative_path"]
        payload = release_assurance.git_index_blob_bytes(relative, root)
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise ProspectiveReauditError(f"invalid SHA-256 syntax: {relative}")
        if row["sha256"] != _sha256_bytes(payload) or row.get("size_bytes") != str(len(payload)):
            raise ProspectiveReauditError(f"candidate byte binding mismatch: {relative}")
    return {
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256(root / MANIFEST_PATH.relative_to(PROJECT_ROOT)),
        "cycle_breaking_exclusions": exclusions,
    }


def validate_requirements(
    requirements: Sequence[Mapping[str, str]], contract: Mapping[str, Any]
) -> dict[str, Any]:
    expected_count = int(contract["assessment"]["requirement_count"])
    if len(requirements) != expected_count:
        raise ProspectiveReauditError("requirements count mismatch")
    ids = _unique((str(row.get("requirement_id", "")) for row in requirements), "requirement")
    dimensions = Counter(row.get("dimension_id") for row in requirements)
    if ids != [f"ST08-REQ-{index:02d}" for index in range(1, 25)]:
        raise ProspectiveReauditError("requirements identifiers or order mismatch")
    if dimensions != Counter({f"D{index:02d}": 3 for index in range(1, 9)}):
        raise ProspectiveReauditError("requirements dimension geometry mismatch")
    required_fields = {
        "requirement_id", "dimension_id", "dimension_name", "requirement",
        "authoritative_basis", "local_evidence_paths", "verification_method",
        "pass_rule", "fail_rule", "blocked_rule", "aggregation_role", "design_status",
    }
    for row in requirements:
        if set(row) != required_fields or any(not str(row[field]).strip() for field in required_fields):
            raise ProspectiveReauditError(f"incomplete requirement row: {row.get('requirement_id')}")
        if row["design_status"] != "NOT_EVALUATED":
            raise ProspectiveReauditError("registered v02 design status must remain NOT_EVALUATED")
        if row["aggregation_role"] not in {"mandatory", "conditional"}:
            raise ProspectiveReauditError("invalid aggregation role")
    return {"requirements": len(requirements), "dimensions": dict(sorted(dimensions.items()))}


def _load_scope(path: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(path)
    if fields != ["change_kind", "relative_path", "reason"]:
        raise ProspectiveReauditError("unexpected ST08_13C change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_candidate_bindings(
    contract: Mapping[str, Any], root: Path = PROJECT_ROOT, workflow_text: str | None = None
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_13C_prospective_release_candidate_v02_reaudit":
        raise ProspectiveReauditError("unexpected task identifier")
    if contract.get("profile") != "SCIENTIFIC_VALIDATION":
        raise ProspectiveReauditError("profile must be SCIENTIFIC_VALIDATION")
    authority = contract.get("authority")
    if not isinstance(authority, Mapping) or authority.get("authorized_task_label") != "NEXT_BLOCK_AUTHORIZED: ST08_13C_prospective_release_candidate_v02_reaudit":
        raise ProspectiveReauditError("John task authority is missing")
    for key in ("version_tag_authorized", "GitHub_release_authorized", "PyPI_publication_authorized", "scientific_claim_protocol_or_verdict_change_authorized"):
        if authority.get(key) is not False:
            raise ProspectiveReauditError(f"authority boundary overstated: {key}")
    requirements_path = root / contract["assessment"]["requirements_path"]
    if _sha256(requirements_path) != contract["assessment"]["requirements_sha256"]:
        raise ProspectiveReauditError("requirements v02 hash mismatch")
    _, requirements = _load_csv(requirements_path)
    requirement_summary = validate_requirements(requirements, contract)
    for item in contract["immutable_history"]:
        path = root / item["path"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise ProspectiveReauditError(f"immutable historical artifact changed: {item['path']}")
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    manifest_summary = validate_manifest(fields, rows, root, contract)
    protected_bindings = _load_json(
        root / "configs/project_readiness/st08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_contract_v01.json"
    )["protected_git_blob_bindings"]
    protected_summary = release_assurance.validate_protected_hashes(
        root, inventory="published", canonical_bindings=protected_bindings
    )
    workflow_text = workflow_text if workflow_text is not None else (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    required_workflow_tokens = [
        "scripts/st08_13C_prospective_release_candidate_v02_reaudit.py candidate-tree",
        "tests.test_prospective_release_candidate_v02_reaudit_st08_13C",
        "scripts/st08_13_release_candidate_reaudit.py --inventory published",
        "scripts/st08_09_release_assurance.py source --inventory published",
    ]
    missing_workflow = [token for token in required_workflow_tokens if token not in workflow_text]
    if missing_workflow:
        raise ProspectiveReauditError(f"workflow omits ST08_13C control: {missing_workflow}")
    expected_scope = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    observed_scope = _load_scope(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise ProspectiveReauditError("actual change scope differs from the planned change set")
    for relative, tokens in {
        STAGE_PATH.relative_to(PROJECT_ROOT).as_posix(): [contract["task_id"], "PROJECT_COMPLETION_VERDICT"],
        ROADMAP_PATH.relative_to(PROJECT_ROOT).as_posix(): [contract["task_id"], "PROJECT_COMPLETION_VERDICT"],
    }.items():
        content = (root / relative).read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in content]
        if missing:
            raise ProspectiveReauditError(f"canonical document registration missing: {relative}/{missing}")
    return {
        "requirements": requirement_summary,
        "manifest": manifest_summary,
        "protected": protected_summary,
        "immutable_history": len(contract["immutable_history"]),
        "change_scope": len(observed_scope),
    }


def validate_evidence_relations(
    evidence: Mapping[str, Any], contract: Mapping[str, Any], requirements: Sequence[Mapping[str, str]]
) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_13C_prospective_release_candidate_v02_reaudit_evidence_v01":
        raise ProspectiveReauditError("unexpected evidence schema")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "SCIENTIFIC_VALIDATION":
        raise ProspectiveReauditError("evidence task/profile mismatch")
    if evidence.get("status") != "prospective_v02_reaudit_complete_release_not_authorized":
        raise ProspectiveReauditError("evidence is not final")
    expected_by_id = {row["requirement_id"]: row for row in requirements}
    results = evidence.get("requirement_results")
    if not isinstance(results, list):
        raise ProspectiveReauditError("requirement_results must be a list")
    result_ids = _unique((str(row.get("requirement_id", "")) for row in results), "evidence requirement")
    if set(result_ids) != set(expected_by_id):
        raise ProspectiveReauditError("evidence requirement set mismatch")
    allowed = set(contract["assessment"]["allowed_requirement_statuses"])
    statuses_by_dimension: dict[str, list[str]] = defaultdict(list)
    finding_references: set[str] = set()
    for result in results:
        requirement_id = result["requirement_id"]
        source = expected_by_id[requirement_id]
        status = result.get("status")
        if status not in allowed:
            raise ProspectiveReauditError(f"invalid requirement status: {requirement_id}/{status}")
        if source["aggregation_role"] == "mandatory" and status == "SKIPPED":
            raise ProspectiveReauditError(f"mandatory requirement cannot be SKIPPED: {requirement_id}")
        if result.get("dimension_id") != source["dimension_id"]:
            raise ProspectiveReauditError(f"dimension mismatch: {requirement_id}")
        if not str(result.get("observed_evidence", "")).strip():
            raise ProspectiveReauditError(f"observed evidence missing: {requirement_id}")
        paths = result.get("evidence_paths")
        findings = result.get("finding_ids")
        if not isinstance(paths, list) or not paths or not all(isinstance(path, str) and path for path in paths):
            raise ProspectiveReauditError(f"evidence paths missing: {requirement_id}")
        if not isinstance(findings, list):
            raise ProspectiveReauditError(f"finding_ids must be a list: {requirement_id}")
        if status == "PASS" and findings:
            raise ProspectiveReauditError(f"PASS cannot carry a blocking finding: {requirement_id}")
        if status != "PASS" and not findings:
            raise ProspectiveReauditError(f"non-PASS is silent: {requirement_id}")
        finding_references.update(str(value) for value in findings)
        statuses_by_dimension[source["dimension_id"]].append(str(status))
    findings = evidence.get("open_findings")
    if not isinstance(findings, list):
        raise ProspectiveReauditError("open_findings must be a list")
    finding_ids = _unique((str(row.get("finding_id", "")) for row in findings), "finding") if findings else []
    if set(finding_ids) != finding_references:
        raise ProspectiveReauditError("finding coverage mismatch")
    dimensions = evidence.get("dimension_results")
    if not isinstance(dimensions, list):
        raise ProspectiveReauditError("dimension_results must be a list")
    dimension_ids = _unique((str(row.get("dimension_id", "")) for row in dimensions), "dimension result")
    expected_dimension_ids = sorted(statuses_by_dimension)
    if sorted(dimension_ids) != expected_dimension_ids:
        raise ProspectiveReauditError("dimension result set mismatch")
    recomputed = {dimension: _aggregate(statuses_by_dimension[dimension]) for dimension in expected_dimension_ids}
    for row in dimensions:
        if row.get("status") != recomputed[row["dimension_id"]]:
            raise ProspectiveReauditError(f"dimension aggregate mismatch: {row['dimension_id']}")
    aggregate = evidence.get("aggregate_verdict")
    if not isinstance(aggregate, Mapping):
        raise ProspectiveReauditError("aggregate_verdict must be an object")
    completion = _aggregate([recomputed[value] for value in contract["aggregation"]["project_completion_dimensions"]])
    release = _aggregate([recomputed[value] for value in contract["aggregation"]["external_release_dimensions"]])
    blockers = aggregate.get("release_blockers")
    if blockers != ["John_release_authorization_not_granted"]:
        raise ProspectiveReauditError("release blocker set must contain only the reserved John gate")
    if release == "PASS" and blockers:
        release = "BLOCKED"
    if aggregate.get("project_completion_verdict") != completion or aggregate.get("external_release_readiness") != release:
        raise ProspectiveReauditError("aggregate verdict mismatch")
    if aggregate.get("release_class") != "not_ready" or aggregate.get("John_release_decision_required") is not True:
        raise ProspectiveReauditError("release class or John decision boundary mismatch")
    requirement_counts = {key: 0 for key in ("PASS", "FAIL", "BLOCKED", "SKIPPED")}
    requirement_counts.update(Counter(str(row["status"]) for row in results))
    dimension_counts = {key: 0 for key in ("PASS", "FAIL", "BLOCKED")}
    dimension_counts.update(Counter(recomputed.values()))
    if aggregate.get("requirement_status_counts") != requirement_counts or aggregate.get("dimension_status_counts") != dimension_counts:
        raise ProspectiveReauditError("aggregate count mismatch")
    if completion != "PASS" or release != "BLOCKED" or requirement_counts["PASS"] != 24:
        raise ProspectiveReauditError("registered final prospective outcome is overstated or incomplete")
    hosted = evidence.get("candidate_hosted_CI")
    manifest = evidence.get("candidate_manifest")
    if not isinstance(hosted, Mapping) or not isinstance(manifest, Mapping):
        raise ProspectiveReauditError("candidate hosted CI or manifest evidence missing")
    if hosted.get("status") != "completed" or hosted.get("conclusion") != "success" or hosted.get("job_name") != "assurance" or hosted.get("job_conclusion") != "success":
        raise ProspectiveReauditError("candidate hosted CI is not successful")
    if not isinstance(hosted.get("run_id"), int) or not re.fullmatch(r"[0-9a-f]{40}", str(hosted.get("head_sha", ""))):
        raise ProspectiveReauditError("candidate hosted CI identity invalid")
    if not str(hosted.get("html_url", "")).startswith("https://github.com/Vanargo/ML-CRA/actions/runs/"):
        raise ProspectiveReauditError("candidate hosted CI URL invalid")
    if evidence.get("historical_disposition") != {
        "ST08_v01_project_completion": "FAIL_PRESERVED",
        "ST08_v01_external_release": "FAIL_PRESERVED",
        "ST08_v01_REQ08": "FAIL_PRESERVED",
        "ST08_v01_REQ12": "BLOCKED_PRESERVED",
        "ST08_13A_migration": "PASS_PRESERVED",
        "ST08_13B_external_controls": "PASS_PRESERVED",
    }:
        raise ProspectiveReauditError("historical disposition mismatch")
    if evidence.get("training_runs") != 0 or evidence.get("scientific_artifact_changes") != 0 or evidence.get("release_actions_performed") != 0:
        raise ProspectiveReauditError("forbidden side effect recorded")
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise ProspectiveReauditError("technical status/readiness mismatch")
    return {
        "requirements": len(results),
        "dimensions": recomputed,
        "project_completion_verdict": completion,
        "external_release_readiness": release,
        "findings": len(findings),
    }


def validate_candidate_tree(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": validate_candidate_bindings(contract, root)}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_candidate_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    _, requirements = _load_csv(root / REQUIREMENTS_PATH.relative_to(PROJECT_ROOT))
    manifest = bindings["manifest"]
    expected_manifest = dict(manifest)
    expected_manifest["status"] = "PASS"
    if evidence.get("candidate_manifest") != expected_manifest:
        raise ProspectiveReauditError("evidence candidate-manifest binding mismatch")
    return {
        "status": "PASS",
        "bindings": bindings,
        "relations": validate_evidence_relations(evidence, contract, requirements),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_13C prospective release-candidate v02 re-audit")
    parser.add_argument("command", choices=("write-manifest", "candidate-tree", "final-evidence"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "candidate-tree":
            result = validate_candidate_tree()
        else:
            result = validate_final_evidence()
    except (ProspectiveReauditError, release_assurance.AssuranceError, csv.Error, json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
