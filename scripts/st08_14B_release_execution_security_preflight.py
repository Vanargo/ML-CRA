from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
    from scripts import st08_14A_release_candidate_finalization_assurance as candidate_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance
    import st08_14A_release_candidate_finalization_assurance as candidate_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_14B_release_0_1_0_execution_security_preflight_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_14B_release_execution_security_preflight_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_14B_release_0_1_0_execution_security_preflight_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_14B_release_0_1_0_execution_security_preflight_change_scope_v01.csv"
RUNBOOK_PATH = PROJECT_ROOT / "docs/release/release_0_1_0_GitHub_execution_runbook_v01.md"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
SECURITY_PATH = PROJECT_ROOT / "SECURITY.md"
BASELINE_COMMIT = "60dd1379836ee7c76756bf46786f0ba5d691dc17"


class PreflightError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PreflightError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise PreflightError(f"CSV is empty or lacks rows: {path}")
    return fields, rows


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_list_sha256(paths: Iterable[str]) -> str:
    return _sha256_bytes("".join(f"{path}\n" for path in sorted(paths)).encode("utf-8"))


def _unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise PreflightError(f"{label} must occur exactly once: {duplicates}")
    return values


def _assert_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise PreflightError("authority object missing")
    if authority.get("authorized_task_label") != (
        "NEXT_BLOCK_AUTHORIZED: ST08_14B_release_0_1_0_execution_security_preflight"
    ):
        raise PreflightError("John task authority is missing")
    allowed_true = {
        "execution_security_preflight_authorized",
        "local_candidate_rebuild_authorized",
        "read_only_GitHub_observation_authorized",
    }
    for key, value in authority.items():
        if key in {"accepted_and_closed_previous_task", "authorized_task_label"}:
            continue
        if key in allowed_true:
            if value is not True:
                raise PreflightError(f"authorized preflight operation disabled: {key}")
        elif key.endswith("_authorized") and value is not False:
            raise PreflightError(f"external, scientific or future authority overstated: {key}")


def _tracked_candidate_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
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
        raise PreflightError(f"tracked preflight tree contains policy-excluded paths: {forbidden}")
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise PreflightError(f"cycle-breaking path is not tracked: {missing}")
    return tracked


def build_manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
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
        "manifest_sha256": _sha256_file(path),
    }


def validate_manifest(
    fields: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    root: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    if list(fields) != contract["successor_manifest"]["fields"]:
        raise PreflightError("preflight manifest schema mismatch")
    row_paths = _unique((str(row.get("relative_path", "")) for row in rows), "manifest path")
    if row_paths != sorted(row_paths):
        raise PreflightError("preflight manifest paths are not ordinally sorted")
    tracked = _tracked_candidate_paths(root, contract)
    exclusions = sorted(contract["successor_manifest"]["cycle_breaking_exclusions"])
    expected_rows = sorted(set(tracked) - set(exclusions))
    if row_paths != expected_rows:
        missing = sorted(set(expected_rows) - set(row_paths))
        extra = sorted(set(row_paths) - set(expected_rows))
        raise PreflightError(f"preflight manifest path set mismatch: missing={missing} extra={extra}")
    for row in rows:
        relative = row["relative_path"]
        payload = release_assurance.git_index_blob_bytes(relative, root)
        if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            raise PreflightError(f"invalid SHA-256 syntax: {relative}")
        if row["sha256"] != _sha256_bytes(payload) or row.get("size_bytes") != str(len(payload)):
            raise PreflightError(f"preflight-tree byte binding mismatch: {relative}")
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


def _validate_immutable_history(contract: Mapping[str, Any], root: Path) -> None:
    items = contract.get("immutable_ST08_14A", [])
    if len(items) != 6:
        raise PreflightError("immutable ST08_14A set must contain six artifacts")
    for item in items:
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise PreflightError(f"immutable ST08_14A artifact changed: {item['path']}")


def validate_security_text(text: str) -> None:
    required = ["`0.1.0`", "не выпущен", "предварительным", "не получает гарантий стабильного API"]
    missing = [token for token in required if token not in text]
    if missing:
        raise PreflightError(f"SECURITY.md omits candidate boundary: {missing}")
    if "0.1.0.dev0" in text:
        raise PreflightError("SECURITY.md retains the obsolete development version")


def validate_workflow_text(text: str) -> None:
    required = [
        "permissions:\n  contents: read",
        "fetch-depth: 0",
        "scripts/st08_14B_release_execution_security_preflight.py contract",
        "scripts/st08_14B_release_execution_security_preflight.py mutations",
        "scripts/st08_14B_release_execution_security_preflight.py build-preflight",
        "scripts/st08_09_release_assurance.py source --inventory published",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise PreflightError(f"workflow omits ST08_14B control: {missing}")
    forbidden = [
        "contents: write",
        "id-token: write",
        "attestations: write",
        "actions/upload-artifact",
        "gh release create",
        "pypa/gh-action-pypi-publish",
        "pull_request_target",
    ]
    if any(token in text for token in forbidden):
        raise PreflightError("assurance workflow gained release or unsafe authority")


def validate_runbook_text(text: str) -> None:
    required = [
        "не разрешением на выпуск",
        "отдельно авторизованном John блоке ST08_14C",
        "Release immutability",
        "gh release verify v0.1.0",
        "gh release verify-asset v0.1.0",
        "PyPI и TestPyPI не входят",
        "SHA-256 подтверждает совпадение байтов, но не доказывает корректность",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise PreflightError(f"release runbook omits required boundary: {missing}")
    ordered = [
        "Проверить точный commit",
        "Повторно построить",
        "Создать draft GitHub Release",
        "До публикации прикрепить",
        "Сверить имена",
        "Один раз опубликовать",
        "После публикации выполнить",
        "Зарегистрировать URL выпуска",
    ]
    positions = [text.find(token) for token in ordered]
    if -1 in positions or positions != sorted(positions):
        raise PreflightError("release runbook state-machine order mismatch")


def _scope_rows(root: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if fields != ["change_kind", "relative_path", "reason"]:
        raise PreflightError("unexpected ST08_14B change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def _validate_scope(contract: Mapping[str, Any], observed: Sequence[tuple[str, str]]) -> None:
    expected = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    if list(observed) != expected or len(observed) != len(set(observed)):
        raise PreflightError("actual change scope differs from planned changes")


def validate_external_observations(observed: Mapping[str, Any]) -> None:
    exact = {
        "repository": "Vanargo/ML-CRA",
        "default_branch": "main",
        "ruleset_id": 21408995,
        "required_status_check": "assurance",
        "tags": 0,
        "GitHub_releases": 0,
        "secret_scanning_enabled": True,
        "push_protection_enabled": True,
        "private_vulnerability_reporting_enabled": True,
        "dependabot_alerts_enabled": True,
        "release_immutability_enabled": True,
        "ruleset_required_controls_pass": True,
        "GitHub_CLI_available": True,
    }
    mismatches = {key: (observed.get(key), value) for key, value in exact.items() if observed.get(key) != value}
    if mismatches:
        raise PreflightError(f"external preflight observation missing or mismatched: {mismatches}")
    if observed.get("required_assurance_conclusion") != "success":
        raise PreflightError("hosted required assurance is not successful")
    commit = str(observed.get("observed_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit == "0" * 40:
        raise PreflightError("external observed commit is missing")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T[^ ]+Z", str(observed.get("authenticated_owner_observed_at", ""))):
        raise PreflightError("authenticated owner observation timestamp is missing")
    if not re.fullmatch(
        r"https://github\.com/Vanargo/ML-CRA/actions/runs/\d+(?:/job/\d+)?",
        str(observed.get("hosted_run_url", "")),
    ):
        raise PreflightError("exact hosted assurance URL is missing")
    if not re.match(r"gh version \d+\.\d+\.\d+", str(observed.get("GitHub_CLI_version", ""))):
        raise PreflightError("observed GitHub CLI version is missing")


def _changed_release_inputs(root: Path) -> list[str]:
    process = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", BASELINE_COMMIT, "--"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise PreflightError(f"cannot compare source baseline: {process.stderr.strip()}")
    paths = [line.strip().replace("\\", "/") for line in process.stdout.splitlines() if line.strip()]
    inputs = [
        path
        for path in paths
        if path in {"pyproject.toml", "README.md", "LICENSE", "DATASET_ATTRIBUTION.md"}
        or path.startswith("src/")
        or path.startswith("tests/")
    ]
    if inputs != ["tests/test_release_assurance_st08_09.py"]:
        raise PreflightError(f"unexpected release-input change since ST08_14A: {inputs}")
    return inputs


def validate_build_result(result: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    assets = result.get("assets")
    if not isinstance(assets, Mapping):
        raise PreflightError("candidate asset result missing")
    expected_names = contract["candidate_preflight"]["required_assets"]
    if sorted(assets) != sorted(expected_names):
        raise PreflightError("candidate asset name set mismatch")
    prior = contract["candidate_preflight"]["ST08_14A_assets"]
    wheel_name = "ml_cra-0.1.0-py3-none-any.whl"
    sdist_name = "ml_cra-0.1.0.tar.gz"
    if assets[wheel_name]["sha256"] != prior[wheel_name]["sha256"]:
        raise PreflightError("ST08_14B wheel differs from accepted ST08_14A wheel")
    if assets[sdist_name]["sha256"] == prior[sdist_name]["sha256"]:
        raise PreflightError("ST08_14B sdist did not register the required current test correction")
    if result.get("independent_builds") != 2 or not (
        result.get("normalized_sdist_reproducible") and result.get("wheel_reproducible")
    ):
        raise PreflightError("two-build byte reproducibility failed")
    return {
        "assets": assets,
        "wheel_equal_ST08_14A": True,
        "sdist_successor_registered": True,
        "independent_builds": 2,
    }


def build_preflight(output_dir: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    _assert_authority(contract)
    changed_inputs = _changed_release_inputs(root)
    result = candidate_assurance.build_candidate(output_dir, root)
    validated = validate_build_result(result, contract)
    return {
        "status": "PASS",
        "candidate": result,
        "preflight": validated,
        "changed_release_inputs": changed_inputs,
        "release_actions_performed": 0,
    }


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    if contract.get("task_id") != "ST08_14B_release_0_1_0_execution_security_preflight":
        raise PreflightError("unexpected task identifier")
    if contract.get("profile") != "CHANGE":
        raise PreflightError("profile must be CHANGE")
    _assert_authority(contract)
    reconciliation = contract.get("identifier_reconciliation", {})
    if reconciliation.get("historical_ST08_14_phase_name") != "ST08_14B_release_0_1_0_final_candidate_reaudit":
        raise PreflightError("historical ST08_14 identifier drift is not registered")
    if reconciliation.get("current_authorized_name") != contract["task_id"]:
        raise PreflightError("current ST08_14B identifier reconciliation mismatch")
    _validate_immutable_history(contract, root)
    candidate_assurance.validate_metadata(root)
    protected = release_assurance.validate_protected_hashes(root, inventory="published")
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    manifest = validate_manifest(fields, rows, root, contract)
    _validate_scope(contract, _scope_rows(root))
    validate_security_text((root / SECURITY_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8"))
    validate_workflow_text((root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8"))
    validate_runbook_text((root / RUNBOOK_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8"))
    tags = subprocess.run(
        ["git", "-C", str(root), "tag", "--list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if tags.returncode != 0 or tags.stdout.split():
        raise PreflightError("local repository must contain zero tags during ST08_14B")
    if len(contract.get("authoritative_support", [])) != 7:
        raise PreflightError("authoritative source set mismatch")
    return {
        "status": "PASS",
        "manifest": manifest,
        "protected_scientific_artifacts": protected,
        "immutable_ST08_14A": 6,
        "planned_change_paths": len(contract["planned_changes"]),
        "local_tags": 0,
        "release_actions_performed": 0,
    }


def validate_evidence(evidence: Mapping[str, Any], contract: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_14B_release_0_1_0_execution_security_preflight_evidence_v01":
        raise PreflightError("unexpected evidence schema")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "CHANGE":
        raise PreflightError("evidence task/profile mismatch")
    if evidence.get("status") != "preflight_complete_no_release":
        raise PreflightError("external preflight evidence is not complete")
    expected_manifest = dict(bindings["manifest"])
    expected_manifest["status"] = "PASS"
    if evidence.get("successor_manifest") != expected_manifest:
        raise PreflightError("evidence successor-manifest binding mismatch")
    validate_external_observations(evidence.get("external_observations", {}))
    assets = evidence.get("candidate_assets")
    if not isinstance(assets, Mapping):
        raise PreflightError("candidate asset evidence missing")
    validate_build_result(
        {
            "assets": assets,
            "independent_builds": 2,
            "normalized_sdist_reproducible": True,
            "wheel_reproducible": True,
        },
        contract,
    )
    expected_checks = {
        "contract_assurance": "PASS",
        "mutation_tests": "PASS_14_of_14",
        "candidate_builds": "PASS_2_of_2",
        "normalized_sdist_byte_reproducibility": "PASS_2_of_2",
        "wheel_byte_reproducibility": "PASS_2_of_2_equal_ST08_14A",
        "archive_assurance": "PASS",
        "working_baseline": "PASS",
        "published_baseline": "PASS",
        "source_assurance": "PASS",
        "documentation_assurance": "PASS",
        "secret_pattern_scan": "PASS_zero_findings",
        "dependency_audit": "PASS_zero_known_vulnerabilities_50_dependencies_time_stamped_2026_08_26",
        "protected_scientific_artifacts": "PASS_18_of_18",
        "historical_ST08_14A_current_tree_tests": "SKIPPED_superseded_manifest_expected_6_new_paths",
        "hosted_assurance": "PASS",
        "repository_security_preflight": "PASS",
        "release_actions_performed": 0,
        "training_runs": 0,
        "scientific_artifact_changes": 0,
    }
    if evidence.get("observed_checks") != expected_checks:
        raise PreflightError("observed check record is incomplete or overstated")
    if evidence.get("change_reconciliation") != {
        "planned_paths": 14,
        "actual_paths": 14,
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise PreflightError("change reconciliation mismatch")
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise PreflightError("technical status/readiness mismatch")
    if any(evidence.get(key) is not False for key in ["release_authorized", "release_performed"]):
        raise PreflightError("release authority or action is overstated")
    return {"status": "PASS", "release_actions_performed": 0}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract(root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": bindings, "evidence": validate_evidence(evidence, contract, bindings)}


def _expect_rejection(label: str, action: Any) -> str:
    try:
        action()
    except (PreflightError, release_assurance.AssuranceError, candidate_assurance.CandidateFinalizationError):
        return label
    raise PreflightError(f"negative mutation was accepted: {label}")


def run_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    workflow = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    security = (root / SECURITY_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    runbook = (root / RUNBOOK_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    scope = _scope_rows(root)
    external = {
        "repository": "Vanargo/ML-CRA", "default_branch": "main", "ruleset_id": 21408995,
        "required_status_check": "assurance", "tags": 0, "GitHub_releases": 0,
        "secret_scanning_enabled": True, "push_protection_enabled": True,
        "private_vulnerability_reporting_enabled": True, "dependabot_alerts_enabled": True,
        "release_immutability_enabled": True, "ruleset_required_controls_pass": True,
        "GitHub_CLI_available": True, "required_assurance_conclusion": "success",
        "observed_commit": "1" * 40,
        "authenticated_owner_observed_at": "2026-08-26T00:00:00Z",
        "hosted_run_url": "https://github.com/Vanargo/ML-CRA/actions/runs/1/job/2",
        "GitHub_CLI_version": "gh version 2.0.0",
    }
    mutations: list[str] = []
    mutated = copy.deepcopy(contract)
    mutated["authority"]["authorized_task_label"] = "NEXT_BLOCK_AUTHORIZED: ST08_14C"
    mutations.append(_expect_rejection("wrong_authority", lambda: _assert_authority(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["authority"]["GitHub_release_authorized"] = True
    mutations.append(_expect_rejection("release_authority", lambda: _assert_authority(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["immutable_ST08_14A"][0]["sha256"] = "0" * 64
    mutations.append(_expect_rejection("immutable_history", lambda: _validate_immutable_history(mutated, root)))
    mutations.append(_expect_rejection("stale_security_version", lambda: validate_security_text(security + "\n0.1.0.dev0")))
    mutations.append(_expect_rejection("workflow_write", lambda: validate_workflow_text(workflow.replace("contents: read", "contents: write"))))
    mutations.append(_expect_rejection("workflow_upload", lambda: validate_workflow_text(workflow + "\nactions/upload-artifact")))
    mutations.append(_expect_rejection("shallow_checkout", lambda: validate_workflow_text(workflow.replace("fetch-depth: 0", "fetch-depth: 1"))))
    swapped = runbook.replace("3. Создать draft GitHub Release", "3. TEMP").replace("4. До публикации прикрепить", "3. Создать draft GitHub Release").replace("3. TEMP", "4. До публикации прикрепить")
    mutations.append(_expect_rejection("runbook_order", lambda: validate_runbook_text(swapped)))
    altered_rows = copy.deepcopy(rows)
    altered_rows[0]["sha256"] = "0" * 64
    mutations.append(_expect_rejection("manifest_hash", lambda: validate_manifest(fields, altered_rows, root, contract)))
    mutations.append(_expect_rejection("manifest_omission", lambda: validate_manifest(fields, rows[1:], root, contract)))
    mutations.append(_expect_rejection("scope_omission", lambda: _validate_scope(contract, scope[:-1])))
    bad_external = dict(external, tags=1)
    mutations.append(_expect_rejection("existing_tag", lambda: validate_external_observations(bad_external)))
    bad_external = dict(external, release_immutability_enabled=False)
    mutations.append(_expect_rejection("immutable_release_disabled", lambda: validate_external_observations(bad_external)))
    fake_assets = copy.deepcopy(contract["candidate_preflight"]["ST08_14A_assets"])
    fake_assets["ml_cra-0.1.0.tar.gz"]["sha256"] = "1" * 64
    fake_assets["ml_cra-0.1.0-py3-none-any.whl"]["sha256"] = "2" * 64
    mutations.append(_expect_rejection("wheel_drift", lambda: validate_build_result({"assets": fake_assets, "independent_builds": 2, "normalized_sdist_reproducible": True, "wheel_reproducible": True}, contract)))
    if len(mutations) != 14 or len(set(mutations)) != 14:
        raise PreflightError("mutation inventory must contain exactly 14 unique rejections")
    return {"status": "PASS", "mutations_rejected": len(mutations), "labels": mutations}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_14B release execution security preflight")
    parser.add_argument(
        "command",
        choices=("write-manifest", "contract", "mutations", "build-preflight", "final-evidence"),
    )
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "contract":
            result = validate_contract()
        elif args.command == "mutations":
            result = run_mutations()
        elif args.command == "build-preflight":
            if args.output_dir is None:
                raise PreflightError("--output-dir is required for build-preflight")
            result = build_preflight(args.output_dir)
        else:
            result = validate_final_evidence()
    except (
        PreflightError,
        release_assurance.AssuranceError,
        candidate_assurance.CandidateFinalizationError,
        csv.Error,
        json.JSONDecodeError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
