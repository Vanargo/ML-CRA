from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_16A_v1_0_0_candidate_finalization_contract_v01.json"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_16A_v1_0_0_candidate_finalization_evidence_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_16A_v1_0_0_candidate_manifest_v01.csv"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_16A_v1_0_0_candidate_finalization_change_scope_v01.csv"
EXIT_CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_16_v0_1_1_post_release_review_and_v1_0_0_exit_contract_v01.json"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
VERSION = "1.0.0"
CLASSIFIER = "Development Status :: 5 - Production/Stable"
HOSTED_PULL_REQUEST = 27
HOSTED_RUN_ID = 39385375464
HOSTED_JOB_ID = 118503826256
HOSTED_HEAD_SHA = "b7cb928d2ceb70f547153d29b79460dec8f21043"
HOSTED_REQUIRED_STEP = "Validate the v1.0.0 candidate finalization"
HOSTED_PRIMARY_STEPS = 23
HOSTED_COMPLETED_AT = "2026-10-20T07:21:47Z"


class CandidateFinalizationError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidateFinalizationError(f"JSON root must be an object: {path}")
    return value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _path_list_sha256(paths: Iterable[str]) -> str:
    return _sha256("".join(f"{path}\n" for path in sorted(paths)).encode("utf-8"))


def _tracked_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise CandidateFinalizationError(f"cycle-breaking paths are not tracked: {missing}")
    return tracked


def _manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    rows: list[dict[str, str]] = []
    for relative in _tracked_paths(root, contract):
        if relative in exclusions:
            continue
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append({"relative_path": relative, "sha256": _sha256(payload), "size_bytes": str(len(payload))})
    return rows


def write_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    rows = _manifest_rows(root, contract)
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=contract["successor_manifest"]["fields"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tracked = _tracked_paths(root, contract)
    return {
        "status": "PASS",
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256(path.read_bytes()),
        "cycle_breaking_exclusions": sorted(contract["successor_manifest"]["cycle_breaking_exclusions"]),
    }


def validate_manifest(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    with (root / MANIFEST_PATH.relative_to(PROJECT_ROOT)).open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if fields != contract["successor_manifest"]["fields"] or rows != _manifest_rows(root, contract):
        raise CandidateFinalizationError("successor manifest differs from the canonical Git index")
    tracked = _tracked_paths(root, contract)
    payload = release_assurance.git_index_blob_bytes(MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root)
    return {
        "status": "PASS",
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256(payload),
        "cycle_breaking_exclusions": sorted(contract["successor_manifest"]["cycle_breaking_exclusions"]),
    }


def _git_blob_at_commit(root: Path, commit: str, relative: str) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{relative}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise CandidateFinalizationError(f"cannot read baseline blob {relative}: {process.stderr.decode(errors='replace')}")
    return process.stdout


def _validate_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority", {})
    if authority.get("authorized_task_label") != "NEXT_BLOCK_AUTHORIZED: ST08_16A_v1_0_0_candidate_finalization":
        raise CandidateFinalizationError("John authority label mismatch")
    if not all(authority.get(key) is True for key in ["candidate_finalization_authorized", "package_version_1_0_0_authorized", "stable_classifier_authorized"]):
        raise CandidateFinalizationError("candidate finalization authority is incomplete")
    forbidden = ["candidate_asset_build_authorized", "tag_or_GitHub_release_authorized", "TestPyPI_or_PyPI_publication_authorized", "scientific_change_authorized", "ST08_16B_authorized"]
    if any(authority.get(key) is not False for key in forbidden):
        raise CandidateFinalizationError("authority boundary is overstated")


def validate_metadata(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project.get("version") != VERSION or CLASSIFIER not in project.get("classifiers", []):
        raise CandidateFinalizationError("pyproject candidate version or maturity classifier mismatch")
    if "Development Status :: 3 - Alpha" in project.get("classifiers", []):
        raise CandidateFinalizationError("superseded Alpha classifier remains")
    application = (root / "src/mlcra/application.py").read_text(encoding="utf-8")
    if application.count('PROJECT_VERSION = "1.0.0"') != 1:
        raise CandidateFinalizationError("runtime version mismatch")
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    if citation.count('version: "1.0.0"') != 1 or "date-released:" in citation:
        raise CandidateFinalizationError("citation candidate version or release-date boundary mismatch")
    required_docs = {
        "README.md": ["unreleased local candidate", "RELEASE_NOTES_1.0.0.md", "current GitHub release", "v0.1.1", "four commands"],
        "README_RU.md": ["неопубликованным локальным кандидатом", "RELEASE_NOTES_1.0.0.md", "текущим выпуском GitHub", "v0.1.1", "четыре команды"],
        "RELEASE_NOTES_1.0.0.md": ["## English", "## Русский", "mlcra audit", "mlcra verify", "mlcra doctor", "mlcra dashboard", "binary_classification_claim_v01", "tabular_regression_claim_v01", "not a release asset", "не является"],
    }
    for relative, tokens in required_docs.items():
        text = (root / relative).read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in text]
        if missing:
            raise CandidateFinalizationError(f"{relative} omits candidate boundary: {missing}")
    notes = (root / "RELEASE_NOTES_1.0.0.md").read_text(encoding="utf-8")
    forbidden = ["release execution is complete", "выполнение выпуска завершено", "date-released:"]
    if any(token in notes for token in forbidden):
        raise CandidateFinalizationError("candidate notes overstate publication")
    return {"version": VERSION, "classifier": CLASSIFIER, "citation_date_released": "ABSENT", "behavior_changes": 0}


def _scope_rows(root: Path) -> list[tuple[str, str]]:
    with (root / SCOPE_PATH.relative_to(PROJECT_ROOT)).open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if fields != ["change_kind", "relative_path", "reason"]:
        raise CandidateFinalizationError("change-scope schema mismatch")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_contract_bindings(contract: Mapping[str, Any], root: Path = PROJECT_ROOT, workflow_text: str | None = None) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_16A_v1_0_0_candidate_finalization" or contract.get("profile") != "CHANGE":
        raise CandidateFinalizationError("task identifier or profile mismatch")
    _validate_authority(contract)
    baseline = contract.get("source_baseline", {})
    if baseline.get("commit") != "e2991bff81348799fd1f961bf8af185d14d5aa6a" or baseline.get("git_tree") != "f7e09312db3aed019d1897b41bb42b70f8da588e" or baseline.get("tracked_paths") != 375:
        raise CandidateFinalizationError("source baseline mismatch")
    exit_contract = _load_json(root / EXIT_CONTRACT_PATH.relative_to(PROJECT_ROOT))
    if exit_contract.get("public_contract_freeze", {}).get("effective_candidate") != VERSION:
        raise CandidateFinalizationError("accepted exit contract target mismatch")
    for item in contract.get("immutable_ST08_16", []):
        expected = item.get("sha256")
        if expected and _sha256(release_assurance.git_index_blob_bytes(item["path"], root)) != expected:
            raise CandidateFinalizationError(f"immutable ST08_16 artifact changed: {item['path']}")
        baseline_expected = item.get("baseline_sha256")
        if baseline_expected and _sha256(_git_blob_at_commit(root, baseline["commit"], item["path"])) != baseline_expected:
            raise CandidateFinalizationError(f"adapted ST08_16 baseline binding changed: {item['path']}")
    metadata = validate_metadata(root)
    candidate = contract.get("candidate_metadata", {})
    if (
        candidate.get("version") != VERSION
        or candidate.get("classifier") != CLASSIFIER
        or candidate.get("citation_date_released") != "ABSENT_until_actual_release_execution"
        or candidate.get("release_notes") != "RELEASE_NOTES_1.0.0.md"
        or candidate.get("publication_effect") != "NONE_unreleased_local_candidate"
    ):
        raise CandidateFinalizationError("candidate metadata contract mismatch")
    frozen = contract.get("frozen_public_contract", {})
    if frozen.get("commands") != ["mlcra audit", "mlcra verify", "mlcra doctor", "mlcra dashboard"] or frozen.get("exit_codes") != [0, 2, 3, 4, 5, 6] or len(frozen.get("claim_schemas", [])) != 2 or frozen.get("behavior_changes_authorized") != [] or frozen.get("scientific_changes_authorized") != []:
        raise CandidateFinalizationError("frozen public contract mismatch")
    expected_scope = [(row["change_kind"], row["relative_path"]) for row in contract.get("planned_changes", [])]
    observed_scope = _scope_rows(root)
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise CandidateFinalizationError("actual change scope differs from planned changes")
    workflow = workflow_text if workflow_text is not None else (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    required = ["st08_16A_v1_0_0_candidate_finalization_assurance.py contract", "st08_16A_v1_0_0_candidate_finalization_assurance.py mutations", "tests.test_v1_0_0_candidate_finalization_st08_16A", "st08_16A_v1_0_0_candidate_finalization_assurance.py final-evidence"]
    missing = [token for token in required if token not in workflow]
    if missing:
        raise CandidateFinalizationError(f"workflow omits ST08_16A gate: {missing}")
    if any(token in workflow for token in ["contents: write", "id-token: write", "gh release create", "pypa/gh-action-pypi-publish"]):
        raise CandidateFinalizationError("workflow gained publication authority")
    for relative in [STAGE_PATH, ROADMAP_PATH]:
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [
            contract["task_id"],
            "ST08_16B_authorized: false",
            "candidate_asset_builds: 0",
            "CANDIDATE_FINALIZED_HOSTED_ASSURANCE_CLOSED_PENDING_JOHN_ACCEPTANCE",
            f"hosted_assurance_run_id: {HOSTED_RUN_ID}",
            f"hosted_assurance_job_id: {HOSTED_JOB_ID}",
        ]:
            if token not in text:
                raise CandidateFinalizationError(f"canonical registration missing: {relative}/{token}")
    manifest = validate_manifest(root, contract)
    protected = release_assurance.validate_protected_hashes(root, inventory="published")
    if len(contract.get("authoritative_support", [])) != 7:
        raise CandidateFinalizationError("authoritative source set mismatch")
    return {"status": "PASS", "metadata": metadata, "manifest": manifest, "protected": protected, "planned_paths": len(expected_scope), "candidate_asset_builds": 0, "release_actions": 0}


def run_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    workflow = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    rejected: list[str] = []
    for mutation_id in contract["negative_mutations"]:
        mutated = copy.deepcopy(contract)
        mutated_workflow = workflow
        if mutation_id == "authorize_ST08_16B": mutated["authority"]["ST08_16B_authorized"] = True
        elif mutation_id == "authorize_candidate_build": mutated["authority"]["candidate_asset_build_authorized"] = True
        elif mutation_id == "change_version": mutated["candidate_metadata"]["version"] = "1.0.1"
        elif mutation_id == "downgrade_classifier": mutated["candidate_metadata"]["classifier"] = "Development Status :: 4 - Beta"
        elif mutation_id == "add_public_command": mutated["frozen_public_contract"]["commands"].append("mlcra serve")
        elif mutation_id == "remove_claim_schema": mutated["frozen_public_contract"]["claim_schemas"].pop()
        elif mutation_id == "add_release_date": mutated["candidate_metadata"]["citation_date_released"] = "2026-10-20"
        elif mutation_id == "claim_published_release": mutated["candidate_metadata"]["publication_effect"] = "PUBLISHED"
        elif mutation_id == "omit_Russian_notes": mutated["candidate_metadata"]["release_notes"] = "RELEASE_NOTES_0.1.1.md"
        elif mutation_id == "remove_hosted_gate": mutated_workflow = workflow.replace("python scripts/st08_16A_v1_0_0_candidate_finalization_assurance.py final-evidence", "# removed ST08_16A gate")
        else: raise CandidateFinalizationError(f"unknown mutation: {mutation_id}")
        try:
            validate_contract_bindings(mutated, root, mutated_workflow)
        except (CandidateFinalizationError, release_assurance.AssuranceError):
            rejected.append(mutation_id)
        else:
            raise CandidateFinalizationError(f"mutation was accepted: {mutation_id}")
    return {"status": "PASS", "registered": len(contract["negative_mutations"]), "rejected": len(rejected), "mutation_ids": rejected}


def validate_evidence(
    root: Path = PROJECT_ROOT,
    *,
    evidence_data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = dict(evidence_data) if evidence_data is not None else _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    if evidence.get("task_id") != contract["task_id"] or evidence.get("profile") != "CHANGE":
        raise CandidateFinalizationError("evidence identity mismatch")
    if evidence.get("manifest") != bindings["manifest"]:
        raise CandidateFinalizationError("evidence manifest binding mismatch")
    if evidence.get("change_reconciliation") != {"planned_paths": 23, "actual_paths": 23, "unplanned_paths": [], "omitted_paths": [], "status": "PASS_exact_planned_path_set"}:
        raise CandidateFinalizationError("change reconciliation mismatch")
    if evidence.get("actions") != {"candidate_asset_builds": 0, "scientific_artifact_changes": 0, "training_runs": 0, "tag_or_release_actions": 0, "TestPyPI_or_PyPI_uploads": 0, "ST08_16B_authorized": False}:
        raise CandidateFinalizationError("evidence action boundary mismatch")
    lifecycle = evidence.get("lifecycle_state")
    readiness = evidence.get("readiness")
    hosted = evidence.get("hosted_assurance", {})
    if evidence.get("technical_status") != "PASS":
        raise CandidateFinalizationError("technical evidence status mismatch")
    if lifecycle != "CANDIDATE_FINALIZED_HOSTED_ASSURANCE_CLOSED_PENDING_JOHN_ACCEPTANCE":
        raise CandidateFinalizationError("candidate evidence lifecycle is not hosted-closed")
    if readiness != "READY_FOR_JOHN_ACCEPTANCE" or hosted.get("status") != "PASS":
        raise CandidateFinalizationError("hosted-closed evidence readiness mismatch")
    expected_hosted = {
        "status": "PASS",
        "pull_request": HOSTED_PULL_REQUEST,
        "run_id": HOSTED_RUN_ID,
        "job_id": HOSTED_JOB_ID,
        "head_sha": HOSTED_HEAD_SHA,
        "event": "pull_request",
        "conclusion": "success",
        "run_url": f"https://github.com/Vanargo/ML-CRA/actions/runs/{HOSTED_RUN_ID}",
        "job_url": f"https://github.com/Vanargo/ML-CRA/actions/runs/{HOSTED_RUN_ID}/job/{HOSTED_JOB_ID}",
        "required_step": HOSTED_REQUIRED_STEP,
        "required_step_conclusion": "success",
        "primary_steps": HOSTED_PRIMARY_STEPS,
        "completed_at": HOSTED_COMPLETED_AT,
    }
    if hosted != expected_hosted:
        raise CandidateFinalizationError("hosted assurance binding mismatch")
    checks = {item.get("check_id"): item for item in evidence.get("checks", [])}
    hosted_check = checks.get("hosted_exact_head_assurance", {})
    if hosted_check.get("status") != "PASS" or HOSTED_HEAD_SHA not in hosted_check.get("result", ""):
        raise CandidateFinalizationError("hosted assurance check is not exact-head PASS")
    uncertainty = evidence.get("uncertainty", [])
    if any("not yet been observed" in item for item in uncertainty):
        raise CandidateFinalizationError("closed evidence retains pending hosted uncertainty")
    if evidence.get("checkpoint", {}).get("status") != "SKIPPED":
        raise CandidateFinalizationError("checkpoint disposition mismatch")
    return {
        "status": "PASS",
        "lifecycle_state": lifecycle,
        "readiness": readiness,
        "checks": len(evidence.get("checks", [])),
        "candidate_asset_builds": 0,
        "hosted_head_sha": hosted["head_sha"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_16A v1.0.0 candidate-finalization assurance")
    parser.add_argument("command", choices=("metadata", "contract", "mutations", "write-manifest", "final-evidence"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "metadata": result = {"status": "PASS", "metadata": validate_metadata()}
        elif args.command == "contract": result = validate_contract_bindings(_load_json(CONTRACT_PATH))
        elif args.command == "mutations": result = run_mutations()
        elif args.command == "write-manifest": result = write_manifest()
        else: result = validate_evidence()
    except (CandidateFinalizationError, release_assurance.AssuranceError, OSError, ValueError, KeyError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
