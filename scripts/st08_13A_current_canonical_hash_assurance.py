from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration_contract_v01.json"
REQUIREMENTS_V01_PATH = PROJECT_ROOT / "configs/project_readiness/stage08_project_completion_and_release_readiness_requirements_v01.csv"
REQUIREMENTS_V02_PATH = PROJECT_ROOT / "configs/project_readiness/stage08_project_completion_and_release_readiness_requirements_v02.csv"
STATE_MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_13A_current_canonical_state_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"


class CanonicalHashAssuranceError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CanonicalHashAssuranceError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_list_sha256(paths: Iterable[str]) -> str:
    payload = "".join(f"{path}\n" for path in sorted(paths)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise CanonicalHashAssuranceError(f"CSV is empty or lacks a header: {path}")
    return fields, rows


def _require_unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise CanonicalHashAssuranceError(f"{label} must occur exactly once: {duplicates}")
    return values


def validate_requirement_migration(
    rows_v01: Sequence[Mapping[str, str]],
    rows_v02: Sequence[Mapping[str, str]],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    migration = contract["requirements_migration"]
    if len(rows_v01) != int(migration["row_count"]) or len(rows_v02) != int(migration["row_count"]):
        raise CanonicalHashAssuranceError("requirements row count mismatch")
    ids_v01 = _require_unique((str(row.get("requirement_id", "")) for row in rows_v01), "v01 requirement")
    ids_v02 = _require_unique((str(row.get("requirement_id", "")) for row in rows_v02), "v02 requirement")
    if ids_v01 != ids_v02:
        raise CanonicalHashAssuranceError("requirements order or identifier set changed")
    by_id_v01 = {row["requirement_id"]: dict(row) for row in rows_v01}
    by_id_v02 = {row["requirement_id"]: dict(row) for row in rows_v02}
    targets = set(migration["authorized_requirement_ids"])
    changed_fields = set(migration["authorized_changed_fields"])
    immutable_fields = set(migration["immutable_fields_for_target_rows"])
    observed_target_differences: dict[str, list[str]] = {}
    for requirement_id in ids_v01:
        before = by_id_v01[requirement_id]
        after = by_id_v02[requirement_id]
        if set(before) != set(after):
            raise CanonicalHashAssuranceError(f"requirements schema changed: {requirement_id}")
        differences = sorted(key for key in before if before[key] != after[key])
        if requirement_id not in targets:
            if differences:
                raise CanonicalHashAssuranceError(f"unauthorized requirement change: {requirement_id}/{differences}")
            continue
        if set(differences) != changed_fields:
            raise CanonicalHashAssuranceError(
                f"target requirement must change exactly the authorized fields: {requirement_id}/{differences}"
            )
        if any(before[key] != after[key] for key in immutable_fields):
            raise CanonicalHashAssuranceError(f"target immutable field changed: {requirement_id}")
        observed_target_differences[requirement_id] = differences
    if set(observed_target_differences) != targets:
        raise CanonicalHashAssuranceError("REQ08/REQ12 migration set mismatch")
    if any(row.get("design_status") != migration["prospective_design_status"] for row in rows_v02):
        raise CanonicalHashAssuranceError("prospective requirements must remain NOT_EVALUATED")
    return {
        "rows": len(rows_v02),
        "changed_requirement_ids": sorted(observed_target_differences),
        "changed_fields": sorted(changed_fields),
        "reaudit_performed": False,
    }


def _eligible_state_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    exclusions = set(contract["canonical_state_manifest"]["cycle_breaking_exclusions"])
    repository = release_assurance.repository_paths(root)
    missing_exclusions = sorted(path for path in exclusions if path not in repository)
    if missing_exclusions:
        raise CanonicalHashAssuranceError(f"cycle-breaking excluded path is absent: {missing_exclusions}")
    return [path for path in repository if path not in exclusions]


def build_state_manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = []
    for relative in _eligible_state_paths(root, contract):
        path = root / relative
        rows.append({"relative_path": relative, "sha256": _sha256(path), "size_bytes": str(path.stat().st_size)})
    return rows


def write_state_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    path = root / STATE_MANIFEST_PATH.relative_to(PROJECT_ROOT)
    rows = build_state_manifest_rows(root, contract)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["relative_path", "sha256", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return {"status": "PASS", "path": path.relative_to(root).as_posix(), "entries": len(rows), "sha256": _sha256(path)}


def validate_state_manifest_rows(
    fields: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    root: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    expected_fields = contract["canonical_state_manifest"]["fields"]
    if list(fields) != expected_fields:
        raise CanonicalHashAssuranceError(f"state manifest fields mismatch: {fields}")
    observed_paths = _require_unique((str(row.get("relative_path", "")) for row in rows), "state manifest path")
    expected_paths = _eligible_state_paths(root, contract)
    if observed_paths != sorted(observed_paths):
        raise CanonicalHashAssuranceError("state manifest paths are not in ascending ordinal order")
    if observed_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(observed_paths))
        extra = sorted(set(observed_paths) - set(expected_paths))
        raise CanonicalHashAssuranceError(f"state manifest path set mismatch: missing={missing} extra={extra}")
    for row in rows:
        relative = str(row["relative_path"])
        expected_hash = _sha256(root / relative)
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))) or row["sha256"] != expected_hash:
            raise CanonicalHashAssuranceError(f"state manifest SHA-256 mismatch: {relative}")
        expected_size = str((root / relative).stat().st_size)
        if str(row.get("size_bytes", "")) != expected_size:
            raise CanonicalHashAssuranceError(f"state manifest size mismatch: {relative}")
    return {
        "entries": len(rows),
        "eligible_path_list_sha256": _path_list_sha256(observed_paths),
        "manifest_sha256": _sha256(root / STATE_MANIFEST_PATH.relative_to(PROJECT_ROOT)),
        "excluded_paths": contract["canonical_state_manifest"]["cycle_breaking_exclusions"],
    }


def validate_evidence_relations(
    evidence: Mapping[str, Any],
    contract: Mapping[str, Any],
    migration_summary: Mapping[str, Any],
    state_summary: Mapping[str, Any],
    public_summary: Mapping[str, Any],
    protected_summary: Mapping[str, Any],
) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration_evidence_v01":
        raise CanonicalHashAssuranceError("unexpected evidence schema_version")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "CHANGE":
        raise CanonicalHashAssuranceError("evidence task/profile mismatch")
    if evidence.get("status") != "prospective_migration_complete_not_reaudited":
        raise CanonicalHashAssuranceError("evidence migration status mismatch")
    authority = evidence.get("authority")
    if not isinstance(authority, Mapping):
        raise CanonicalHashAssuranceError("evidence authority missing")
    if authority.get("john_decision_text") != contract["authority"]["john_decision_text"]:
        raise CanonicalHashAssuranceError("John authorization text mismatch")
    for key in ("reserved_NEXT_BLOCK_AUTHORIZED_label_claimed_by_agent", "external_repository_action_authorized", "publication_or_release_authorized", "scientific_change_authorized"):
        if authority.get(key) is not False:
            raise CanonicalHashAssuranceError(f"authority boundary overstated: {key}")
    historical = evidence.get("historical_integrity")
    expected_historical = contract["immutable_historical_files"]
    if not isinstance(historical, Mapping) or historical.get("files") != expected_historical or historical.get("status") != "PASS_UNCHANGED":
        raise CanonicalHashAssuranceError("historical integrity evidence mismatch")
    expected_migration = {
        "historical_requirements_sha256": contract["requirements_migration"]["historical_sha256"],
        "prospective_requirements_sha256": contract["requirements_migration"]["prospective_sha256"],
        "rows": migration_summary["rows"],
        "changed_requirement_ids": migration_summary["changed_requirement_ids"],
        "changed_fields": migration_summary["changed_fields"],
        "status": "PASS_MIGRATED_NOT_REAUDITED"
    }
    if evidence.get("requirements_migration") != expected_migration:
        raise CanonicalHashAssuranceError("requirements migration evidence mismatch")
    expected_state = dict(state_summary)
    expected_state.update({"algorithm": "SHA-256", "status": "PASS"})
    if evidence.get("canonical_state_manifest") != expected_state:
        raise CanonicalHashAssuranceError("canonical state manifest evidence mismatch")
    expected_public = {
        "paths": public_summary["paths"],
        "path_list_sha256": public_summary["path_list_sha256"],
        "status": "PASS"
    }
    if evidence.get("public_path_inventory") != expected_public:
        raise CanonicalHashAssuranceError("public path inventory evidence mismatch")
    if evidence.get("protected_artifacts") != {"expected": protected_summary["expected"], "mismatches": 0, "status": "PASS"}:
        raise CanonicalHashAssuranceError("protected artifact evidence mismatch")
    disposition = evidence.get("prospective_disposition")
    if disposition != {
        "ST08-REQ-08": "MIGRATED_NOT_REAUDITED",
        "ST08-REQ-12": "MIGRATED_NOT_REAUDITED",
        "historical_ST08_13_REQ08": "FAIL_PRESERVED",
        "historical_ST08_13_REQ12": "BLOCKED_PRESERVED"
    }:
        raise CanonicalHashAssuranceError("prospective versus historical disposition mismatch")
    if evidence.get("external_actions_performed") != 0 or evidence.get("scientific_artifact_changes") != 0 or evidence.get("training_runs") != 0:
        raise CanonicalHashAssuranceError("forbidden side effect recorded")
    next_block = evidence.get("next_block_reference")
    if not isinstance(next_block, Mapping) or next_block.get("status") != "proposed_not_authorized":
        raise CanonicalHashAssuranceError("next block must remain proposed_not_authorized")
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise CanonicalHashAssuranceError("technical status/readiness mismatch")
    return {"status": "PASS", "historical_files": len(expected_historical), "manifest_entries": state_summary["entries"]}


def validate_repository_bindings(
    contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
    root: Path = PROJECT_ROOT,
    workflow_text: str | None = None,
) -> dict[str, Any]:
    for item in contract["immutable_historical_files"]:
        path = root / item["path"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise CanonicalHashAssuranceError(f"immutable historical file changed: {item['path']}")
    migration = contract["requirements_migration"]
    if _sha256(root / migration["prospective_path"]) != migration["prospective_sha256"]:
        raise CanonicalHashAssuranceError("prospective requirements v02 hash mismatch")
    fields_v01, rows_v01 = _load_csv(root / migration["historical_path"])
    fields_v02, rows_v02 = _load_csv(root / migration["prospective_path"])
    if fields_v01 != fields_v02:
        raise CanonicalHashAssuranceError("requirements CSV headers differ")
    migration_summary = validate_requirement_migration(rows_v01, rows_v02, contract)
    manifest_fields, manifest_rows = _load_csv(root / STATE_MANIFEST_PATH.relative_to(PROJECT_ROOT))
    state_summary = validate_state_manifest_rows(manifest_fields, manifest_rows, root, contract)
    public_summary = release_assurance.validate_public_manifest(root)
    protected_summary = release_assurance.validate_protected_hashes(root)

    workflow_text = workflow_text if workflow_text is not None else (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    required_ci = [
        "scripts/st08_13A_current_canonical_hash_assurance.py",
        "tests.test_current_canonical_hash_assurance_st08_13A",
        "scripts/st08_13_release_candidate_reaudit.py",
        "tests.test_release_candidate_reaudit_st08_13"
    ]
    missing_ci = [value for value in required_ci if value not in workflow_text]
    if missing_ci:
        raise CanonicalHashAssuranceError(f"configured CI omits canonical assurance: {missing_ci}")

    _, scope_rows = _load_csv(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    planned = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    actual = [(row["change_kind"], row["relative_path"]) for row in scope_rows]
    if actual != planned or len(actual) != len(set(actual)):
        raise CanonicalHashAssuranceError("change scope differs from the planned change set")
    for path, tokens in {
        STAGE_PATH.relative_to(PROJECT_ROOT).as_posix(): [contract["task_id"], "FAIL_PRESERVED", "BLOCKED_PRESERVED"],
        ROADMAP_PATH.relative_to(PROJECT_ROOT).as_posix(): [contract["task_id"], "FAIL_PRESERVED", "BLOCKED_PRESERVED"]
    }.items():
        text = (root / path).read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in text]
        if missing:
            raise CanonicalHashAssuranceError(f"canonical document registration missing: {path}/{missing}")

    evidence_summary = validate_evidence_relations(
        evidence, contract, migration_summary, state_summary, public_summary, protected_summary
    )
    return {
        "migration": migration_summary,
        "state_manifest": state_summary,
        "public_manifest": {key: value for key, value in public_summary.items() if key != "included_paths"},
        "protected": protected_summary,
        "evidence": evidence_summary,
        "change_scope": len(actual),
        "CI_commands": required_ci
    }


def validate_registered_migration(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": validate_repository_bindings(contract, evidence, root)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_13A prospective canonical SHA-256 assurance")
    parser.add_argument("command", nargs="?", choices=("validate", "write-manifest"), default="validate")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = write_state_manifest() if args.command == "write-manifest" else validate_registered_migration()
    except (CanonicalHashAssuranceError, release_assurance.AssuranceError, csv.Error, json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
