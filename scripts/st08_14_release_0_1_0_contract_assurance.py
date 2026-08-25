from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tomllib
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_14_release_0_1_0_scope_channel_and_execution_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_14_release_0_1_0_contract_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_14_release_0_1_0_scope_channel_and_execution_contract_design_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_14_release_0_1_0_scope_channel_and_execution_contract_design_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
CITATION_PATH = PROJECT_ROOT / "CITATION.cff"


class ReleaseContractError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReleaseContractError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise ReleaseContractError(f"CSV is empty or lacks rows: {path}")
    return fields, rows


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _path_list_sha256(paths: Iterable[str]) -> str:
    payload = "".join(f"{path}\n" for path in sorted(paths)).encode("utf-8")
    return _sha256_bytes(payload)


def _unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise ReleaseContractError(f"{label} must occur exactly once: {duplicates}")
    return values


def _tracked_release_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    policy = release_assurance._load_json(
        root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT)
    )
    forbidden = [
        path
        for path in tracked
        if release_assurance.classify_public_path(path, policy, root)
        not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}
    ]
    if forbidden:
        raise ReleaseContractError(
            f"tracked successor tree contains policy-excluded paths: {forbidden}"
        )
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise ReleaseContractError(
            f"successor manifest cycle-breaking path is not tracked: {missing}"
        )
    return tracked


def build_manifest_rows(
    root: Path, contract: Mapping[str, Any]
) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    rows: list[dict[str, str]] = []
    for relative in _tracked_release_paths(root, contract):
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
            fieldnames=contract["successor_manifest"]["fields"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    tracked = sorted(
        [row["relative_path"] for row in rows]
        + list(contract["successor_manifest"]["cycle_breaking_exclusions"])
    )
    return {
        "status": "PASS",
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256_bytes(path.read_bytes()),
    }


def validate_manifest(
    fields: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    root: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    expected_fields = contract["successor_manifest"]["fields"]
    if list(fields) != expected_fields:
        raise ReleaseContractError("successor manifest schema mismatch")
    row_paths = _unique(
        (str(row.get("relative_path", "")) for row in rows),
        "successor manifest path",
    )
    if row_paths != sorted(row_paths):
        raise ReleaseContractError("successor manifest paths are not ordinally sorted")
    tracked = _tracked_release_paths(root, contract)
    exclusions = sorted(contract["successor_manifest"]["cycle_breaking_exclusions"])
    expected_rows = sorted(set(tracked) - set(exclusions))
    if row_paths != expected_rows:
        missing = sorted(set(expected_rows) - set(row_paths))
        extra = sorted(set(row_paths) - set(expected_rows))
        raise ReleaseContractError(
            f"successor manifest path set mismatch: missing={missing} extra={extra}"
        )
    for row in rows:
        relative = row["relative_path"]
        payload = release_assurance.git_index_blob_bytes(relative, root)
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise ReleaseContractError(f"invalid SHA-256 syntax: {relative}")
        if (
            row["sha256"] != _sha256_bytes(payload)
            or row.get("size_bytes") != str(len(payload))
        ):
            raise ReleaseContractError(f"successor byte binding mismatch: {relative}")
    manifest_payload = release_assurance.git_index_blob_bytes(
        MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root
    )
    return {
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256_bytes(manifest_payload),
        "cycle_breaking_exclusions": exclusions,
    }


def validate_decision_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    if matrix.get("method") != "weighted_sum_with_ordinal_1_to_5_scores_and_predeclared_criteria":
        raise ReleaseContractError("unexpected decision-matrix method")
    criteria = matrix.get("criteria")
    options = matrix.get("options")
    if not isinstance(criteria, list) or not isinstance(options, list):
        raise ReleaseContractError("decision matrix rows are missing")
    criterion_ids = _unique(
        (str(row.get("criterion_id", "")) for row in criteria), "criterion"
    )
    weights = {row["criterion_id"]: Decimal(str(row["weight"])) for row in criteria}
    if sum(weights.values()) != Decimal("1.00"):
        raise ReleaseContractError("decision-matrix weights must sum to one")
    option_ids = _unique((str(row.get("option_id", "")) for row in options), "option")
    recomputed: dict[str, Decimal] = {}
    selected = []
    for option in options:
        scores = option.get("scores")
        if not isinstance(scores, Mapping) or set(scores) != set(criterion_ids):
            raise ReleaseContractError(f"decision scores incomplete: {option.get('option_id')}")
        if any(not isinstance(value, int) or value < 1 or value > 5 for value in scores.values()):
            raise ReleaseContractError(f"decision score outside 1..5: {option.get('option_id')}")
        score = sum(weights[key] * Decimal(str(scores[key])) for key in criterion_ids)
        recorded = Decimal(str(option.get("weighted_score")))
        if score.quantize(Decimal("0.01")) != recorded.quantize(Decimal("0.01")):
            raise ReleaseContractError(f"weighted score mismatch: {option.get('option_id')}")
        recomputed[option["option_id"]] = score
        if option.get("disposition") == "selected":
            selected.append(option["option_id"])
    if selected != [matrix.get("selected_option")]:
        raise ReleaseContractError("decision matrix must have one declared selected option")
    winner = max(recomputed, key=recomputed.get)
    if winner != matrix.get("selected_option") or winner != "O03":
        raise ReleaseContractError("selected option is not the highest-scoring phased design")
    return {
        "criteria": len(criteria),
        "options": len(options),
        "selected": winner,
        "scores": {key: float(value) for key, value in recomputed.items()},
    }


def validate_release_scope(contract: Mapping[str, Any], root: Path) -> dict[str, Any]:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise ReleaseContractError("authority object missing")
    if authority.get("authorized_task_label") != (
        "NEXT_BLOCK_AUTHORIZED: "
        "ST08_14_release_0_1_0_scope_channel_and_execution_contract_design"
    ):
        raise ReleaseContractError("John task authority is missing")
    if authority.get("contract_design_authorized") is not True:
        raise ReleaseContractError("contract design authority missing")
    forbidden_authority = [
        "package_version_change_authorized",
        "version_tag_authorized",
        "GitHub_release_authorized",
        "TestPyPI_publication_authorized",
        "PyPI_publication_authorized",
        "release_workflow_execution_authorized",
        "scientific_claim_protocol_or_verdict_change_authorized",
    ]
    if any(authority.get(key) is not False for key in forbidden_authority):
        raise ReleaseContractError("authority boundary is overstated")

    with (root / PYPROJECT_PATH.relative_to(PROJECT_ROOT)).open("rb") as stream:
        pyproject = tomllib.load(stream)
    project = pyproject.get("project", {})
    if project.get("version") != "0.1.0.dev0":
        raise ReleaseContractError("current development version changed")
    classifiers = project.get("classifiers", [])
    if "Development Status :: 2 - Pre-Alpha" not in classifiers:
        raise ReleaseContractError("current development classifier changed")
    citation = (root / CITATION_PATH.relative_to(PROJECT_ROOT)).read_text(
        encoding="utf-8"
    )
    if re.search(r"(?m)^(?:version|date-released):", citation):
        raise ReleaseContractError("CITATION.cff prematurely claims a release")

    decision = contract.get("release_scope_decision")
    if not isinstance(decision, Mapping):
        raise ReleaseContractError("release-scope decision missing")
    expected_assets = [
        "ml_cra-0.1.0.tar.gz",
        "ml_cra-0.1.0-py3-none-any.whl",
        "SHA256SUMS",
    ]
    if (
        decision.get("first_supported_release_version") != "0.1.0"
        or decision.get("pep440_final_version") != "0.1.0"
        or decision.get("git_tag") != "v0.1.0"
        or decision.get("primary_channel") != "GitHub_Release"
        or decision.get("required_assets") != expected_assets
        or decision.get("GitHub_release_immutability_required") is not True
    ):
        raise ReleaseContractError("0.1.0 GitHub release boundary mismatch")
    pypi = decision.get("PyPI")
    if not isinstance(pypi, Mapping) or pypi.get("status") != "deferred_not_authorized":
        raise ReleaseContractError("PyPI must remain deferred and not authorized")
    if pypi.get("long_lived_API_token") != "forbidden_by_default":
        raise ReleaseContractError("long-lived PyPI token policy weakened")

    phases = contract.get("phase_sequence")
    if not isinstance(phases, list) or len(phases) != 5:
        raise ReleaseContractError("release phase sequence must contain five rows")
    if [row.get("order") for row in phases] != list(range(1, 6)):
        raise ReleaseContractError("release phase order mismatch")
    if phases[0].get("status") != "authorized_current_task":
        raise ReleaseContractError("current contract phase status mismatch")
    if any("authorized" not in str(row.get("status")) for row in phases[1:]):
        raise ReleaseContractError("future release phase lacks explicit non-authorization")
    if any(row.get("status") not in {"proposed_not_authorized", "optional_proposed_not_authorized"} for row in phases[1:]):
        raise ReleaseContractError("a future release phase is treated as authorized")
    return {
        "current_version": project["version"],
        "target_version": decision["first_supported_release_version"],
        "tag": decision["git_tag"],
        "assets": len(expected_assets),
        "phases": len(phases),
        "future_phases_authorized": 0,
    }


def _load_scope(path: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(path)
    if fields != ["change_kind", "relative_path", "reason"]:
        raise ReleaseContractError("unexpected ST08_14 change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_contract_bindings(
    contract: Mapping[str, Any],
    root: Path = PROJECT_ROOT,
    workflow_text: str | None = None,
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_14_release_0_1_0_scope_channel_and_execution_contract_design":
        raise ReleaseContractError("unexpected task identifier")
    if contract.get("profile") != "CHANGE":
        raise ReleaseContractError("profile must be CHANGE")
    matrix = validate_decision_matrix(contract["decision_matrix"])
    release_scope = validate_release_scope(contract, root)

    for item in contract.get("immutable_ST08_13C", []):
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise ReleaseContractError(
                f"immutable ST08_13C artifact changed: {item['path']}"
            )
    if len(contract.get("immutable_ST08_13C", [])) != 6:
        raise ReleaseContractError("immutable ST08_13C set must contain six artifacts")

    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    manifest = validate_manifest(fields, rows, root, contract)
    protected = release_assurance.validate_protected_hashes(
        root, inventory="published"
    )

    expected_scope = [
        (row["change_kind"], row["relative_path"])
        for row in contract["planned_changes"]
    ]
    observed_scope = _load_scope(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise ReleaseContractError("actual change scope differs from planned changes")

    workflow_text = workflow_text if workflow_text is not None else (
        root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_workflow = [
        "scripts/st08_14_release_0_1_0_contract_assurance.py contract",
        "tests.test_release_0_1_0_contract_st08_14",
        "scripts/st08_09_release_assurance.py source --inventory published",
    ]
    missing = [token for token in required_workflow if token not in workflow_text]
    if missing:
        raise ReleaseContractError(f"workflow omits ST08_14 control: {missing}")
    forbidden_workflow = [
        "gh release create",
        "pypa/gh-action-pypi-publish",
        "id-token: write",
        "contents: write",
        "attestations: write",
    ]
    if any(token in workflow_text for token in forbidden_workflow):
        raise ReleaseContractError("current assurance workflow gained release authority")

    for relative in [ROADMAP_PATH, STAGE_PATH]:
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [
            contract["task_id"],
            "ST08_13C_prospective_release_candidate_v02_reaudit",
            "ST08_14A_release_0_1_0_candidate_finalization",
            "release_authorized: false",
        ]:
            if token not in text:
                raise ReleaseContractError(
                    f"canonical task registration missing: {relative}/{token}"
                )
    sources = contract.get("authoritative_support")
    if not isinstance(sources, list) or len(sources) != 8:
        raise ReleaseContractError("authoritative source set mismatch")
    uris = {row.get("uri") for row in sources}
    for required_uri in {
        "https://semver.org/",
        "https://packaging.python.org/en/latest/flow/",
        "https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases",
        "https://docs.pypi.org/trusted-publishers/",
        "https://csrc.nist.gov/pubs/sp/800/218/final",
    }:
        if required_uri not in uris:
            raise ReleaseContractError(f"authoritative source omitted: {required_uri}")
    return {
        "decision_matrix": matrix,
        "release_scope": release_scope,
        "manifest": manifest,
        "protected": protected,
        "immutable_ST08_13C": 6,
        "change_scope": len(observed_scope),
        "release_actions_performed": 0,
    }


def validate_evidence_relations(
    evidence: Mapping[str, Any],
    contract: Mapping[str, Any],
    bindings: Mapping[str, Any],
) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_14_release_0_1_0_scope_channel_and_execution_contract_design_evidence_v01":
        raise ReleaseContractError("unexpected evidence schema")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "CHANGE":
        raise ReleaseContractError("evidence task/profile mismatch")
    if evidence.get("status") != "contract_design_complete_external_release_not_authorized":
        raise ReleaseContractError("evidence status is not final")

    baseline = evidence.get("source_baseline")
    if not isinstance(baseline, Mapping):
        raise ReleaseContractError("source baseline evidence missing")
    if (
        baseline.get("git_commit") != contract["source_baseline"]["git_commit"]
        or baseline.get("project_version_before") != "0.1.0.dev0"
        or baseline.get("project_version_after") != "0.1.0.dev0"
        or baseline.get("ST08_13C_project_completion") != "PASS_PRESERVED"
        or baseline.get("ST08_13C_external_release_readiness") != "BLOCKED_PRESERVED"
    ):
        raise ReleaseContractError("source baseline evidence mismatch")

    mape = evidence.get("mape_k_result")
    if not isinstance(mape, Mapping) or mape.get("selected_option") != bindings["decision_matrix"]["selected"]:
        raise ReleaseContractError("MAPE-K decision evidence mismatch")
    if Decimal(str(mape.get("weighted_score"))) != Decimal("5.0"):
        raise ReleaseContractError("selected weighted score mismatch")

    registered = evidence.get("registered_release_decision")
    decision = contract["release_scope_decision"]
    if not isinstance(registered, Mapping) or (
        registered.get("version") != decision["first_supported_release_version"]
        or registered.get("tag") != decision["git_tag"]
        or registered.get("primary_channel") != decision["primary_channel"]
        or registered.get("assets") != decision["required_assets"]
        or registered.get("PyPI") != "deferred_not_authorized"
        or registered.get("future_phases_authorized") != 0
    ):
        raise ReleaseContractError("registered release decision evidence mismatch")

    expected_manifest = dict(bindings["manifest"])
    expected_manifest["status"] = "PASS"
    if evidence.get("successor_manifest") != expected_manifest:
        raise ReleaseContractError("evidence successor-manifest binding mismatch")

    expected_checks = {
        "contract_assurance": "PASS",
        "mutation_tests": "PASS_14_of_14",
        "working_baseline": "PASS",
        "published_baseline": "PASS",
        "source_assurance": "PASS",
        "documentation_assurance": "PASS",
        "secret_pattern_scan": "PASS_zero_findings",
        "protected_scientific_artifacts": "PASS_18_of_18",
        "release_actions_performed": 0,
        "training_runs": 0,
        "scientific_artifact_changes": 0,
    }
    if evidence.get("observed_checks") != expected_checks:
        raise ReleaseContractError("observed check record is incomplete or overstated")
    reconciliation = evidence.get("change_reconciliation")
    if reconciliation != {
        "planned_paths": 13,
        "actual_paths": 13,
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise ReleaseContractError("change reconciliation mismatch")
    if (
        evidence.get("package_version_changed") is not False
        or evidence.get("release_authorized") is not False
        or evidence.get("release_performed") is not False
        or evidence.get("release_actions_performed") != 0
        or evidence.get("training_runs") != 0
        or evidence.get("scientific_artifact_changes") != 0
    ):
        raise ReleaseContractError("forbidden side effect recorded")
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise ReleaseContractError("technical status/readiness mismatch")
    return {
        "status": "PASS",
        "version": registered["version"],
        "primary_channel": registered["primary_channel"],
        "future_phases_authorized": 0,
        "release_actions_performed": 0,
    }


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": validate_contract_bindings(contract, root)}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {
        "status": "PASS",
        "bindings": bindings,
        "evidence": validate_evidence_relations(evidence, contract, bindings),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ST08_14 release 0.1.0 contract assurance"
    )
    parser.add_argument(
        "command", choices=("write-manifest", "contract", "final-evidence")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "contract":
            result = validate_contract()
        else:
            result = validate_final_evidence()
    except (
        ReleaseContractError,
        release_assurance.AssuranceError,
        csv.Error,
        json.JSONDecodeError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(
            json.dumps(
                {"status": "FAIL", "error": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
