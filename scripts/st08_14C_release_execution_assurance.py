from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
    from scripts import st08_14A_release_candidate_finalization_assurance as candidate_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance
    import st08_14A_release_candidate_finalization_assurance as candidate_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_CONTRACT = PROJECT_ROOT / "configs/project_readiness/st08_14_release_0_1_0_scope_channel_and_execution_contract_v01.json"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_14C_release_0_1_0_GitHub_execution_evidence_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_14C_release_execution_manifest_v01.csv"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_14C_release_0_1_0_GitHub_execution_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
RELEASE_COMMIT = "9d530b60fd262f21cfe63eb2482722972a24c3d2"
RELEASE_TREE = "d8bda657cc1ee7659ca0a88050c43c54627463a0"
EXPECTED_ASSETS = {
    "ml_cra-0.1.0.tar.gz": {"sha256": "56d40c2c78ca8bff4b51911ed01224a1899462a0a310d0f6bda1c7d971e43d13", "size_bytes": 95342},
    "ml_cra-0.1.0-py3-none-any.whl": {"sha256": "9c8ccfd75a099354ece47cb27cd002aaee4824517986b6c735b5198f3423238a", "size_bytes": 91936},
    "SHA256SUMS": {"sha256": "e663f0789d00fdc3c5dcedb100d42b5816d8fb553f53978b6dcb2a2db9f59279", "size_bytes": 182},
}
IMMUTABLE_ST08_14B = {
    "configs/project_readiness/st08_14B_release_0_1_0_execution_security_preflight_contract_v01.json": "26dda67bac1c061554fa732e8ee60235fcb6e23fb68a58c804257e5066159579",
    "scripts/st08_14B_release_execution_security_preflight.py": "72172d16250529b423242253946b15189a97fbf50fa0e0271961989e3bf34b6b",
    "data_registry/st08_14B_release_execution_security_preflight_manifest_v01.csv": "7043b9a0cf96899bbea131051d99ed97ca1484373a3d5fac46dcfce80f5a6852",
    "data_registry/st08_14B_release_0_1_0_execution_security_preflight_evidence_v01.json": "a9f11a29898646aa6165a147d9d2bc649cc746c7e69dc613dd0f5ff276ad7be7",
    "docs/agent/st08_14B_release_0_1_0_execution_security_preflight_change_scope_v01.csv": "5498d332bec108c025ac5a604a1d05a520f210ad25785e10f7842331707c75e4",
    "docs/release/release_0_1_0_GitHub_execution_runbook_v01.md": "2ba8d29d292fd5b681a8e2504172351fd1239141dc7dee9b0e7dac8d3cb3670b",
}
CYCLE_EXCLUSIONS = sorted([
    EVIDENCE_PATH.relative_to(PROJECT_ROOT).as_posix(),
    MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(),
])
PLANNED_CHANGES = [
    ("added", "scripts/st08_14C_release_execution_assurance.py"),
    ("added", "data_registry/st08_14C_release_execution_manifest_v01.csv"),
    ("added", "data_registry/st08_14C_release_0_1_0_GitHub_execution_evidence_v01.json"),
    ("added", "docs/agent/st08_14C_release_0_1_0_GitHub_execution_change_scope_v01.csv"),
    ("modified", ".github/workflows/ci.yml"),
    ("modified", "scripts/st08_09_release_assurance.py"),
    ("modified", "configs/project_readiness/st08_06_public_repository_asset_manifest_v01.json"),
    ("modified", "docs/agent/pilot_change_scope_v01.csv"),
    ("modified", "README.md"),
    ("modified", "README_RU.md"),
    ("modified", "SECURITY.md"),
    ("modified", "docs/stages/stage_08_project_completion_and_release_readiness.md"),
    ("modified", "roadmap.md"),
]


class ReleaseExecutionError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReleaseExecutionError(f"JSON root must be an object: {path}")
    return value


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


def _run(command: Sequence[str], cwd: Path) -> str:
    process = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if process.returncode:
        raise ReleaseExecutionError(f"command failed ({process.returncode}): {' '.join(command)}: {process.stderr.strip()}")
    return process.stdout.strip()


def build_manifest_rows(root: Path = PROJECT_ROOT) -> list[dict[str, str]]:
    tracked = release_assurance.tracked_repository_paths(root)
    missing = sorted(set(CYCLE_EXCLUSIONS) - set(tracked))
    if missing:
        raise ReleaseExecutionError(f"cycle-breaking files are not tracked: {missing}")
    rows = []
    for relative in sorted(set(tracked) - set(CYCLE_EXCLUSIONS)):
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append({"relative_path": relative, "sha256": _sha256_bytes(payload), "size_bytes": str(len(payload))})
    return rows


def write_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    rows = build_manifest_rows(root)
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["relative_path", "sha256", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tracked = sorted([row["relative_path"] for row in rows] + CYCLE_EXCLUSIONS)
    return {"paths": len(tracked), "hashed_paths": len(rows), "path_list_sha256": _path_list_sha256(tracked), "manifest_sha256": _sha256_file(path), "cycle_breaking_exclusions": CYCLE_EXCLUSIONS, "status": "PASS"}


def validate_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    with (root / MANIFEST_PATH.relative_to(PROJECT_ROOT)).open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if fields != ["relative_path", "sha256", "size_bytes"] or not rows:
        raise ReleaseExecutionError("ST08_14C manifest schema/rows mismatch")
    expected = build_manifest_rows(root)
    if rows != expected:
        raise ReleaseExecutionError("ST08_14C manifest differs from canonical Git index")
    tracked = release_assurance.tracked_repository_paths(root)
    return {"paths": len(tracked), "hashed_paths": len(rows), "path_list_sha256": _path_list_sha256(tracked), "manifest_sha256": _sha256_bytes(release_assurance.git_index_blob_bytes(MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root)), "cycle_breaking_exclusions": CYCLE_EXCLUSIONS, "status": "PASS"}


def _validate_history(root: Path) -> None:
    for relative, expected in IMMUTABLE_ST08_14B.items():
        payload = release_assurance.git_index_blob_bytes(relative, root)
        if _sha256_bytes(payload) != expected:
            raise ReleaseExecutionError(f"immutable ST08_14B artifact changed: {relative}")


def _scope_rows(root: Path) -> list[dict[str, str]]:
    with (root / SCOPE_PATH.relative_to(PROJECT_ROOT)).open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if fields != ["change_kind", "relative_path", "reason"] or not rows:
        raise ReleaseExecutionError("ST08_14C scope schema/rows mismatch")
    return rows


def _validate_workflow(root: Path) -> None:
    raw = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    required = [
        "st08_14C_release_execution_assurance.py contract",
        "st08_14C_release_execution_assurance.py mutations",
        "st08_14C_release_execution_assurance.py final-evidence",
        "st08_14C_release_execution_assurance.py build-release",
        "gh release verify v0.1.0 --repo Vanargo/ML-CRA",
        "gh release verify-asset v0.1.0",
        "GH_TOKEN: ${{ github.token }}",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise ReleaseExecutionError(f"workflow omits ST08_14C controls: {missing}")
    forbidden = ["contents: write", "id-token: write", "attestations: write", "gh release create", "gh release edit", "gh release delete"]
    if any(token in raw for token in forbidden):
        raise ReleaseExecutionError("workflow gained release-write authority")


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / BASE_CONTRACT.relative_to(PROJECT_ROOT))
    phase = [row for row in contract.get("phase_sequence", []) if row.get("task_id") == "ST08_14C_release_0_1_0_GitHub_execution"]
    if len(phase) != 1 or phase[0].get("profile") != "CHANGE" or phase[0].get("order") != 4:
        raise ReleaseExecutionError("registered ST08_14C phase mismatch")
    if contract["release_scope_decision"].get("git_tag") != "v0.1.0" or contract["release_scope_decision"].get("GitHub_release_immutability_required") is not True:
        raise ReleaseExecutionError("release identity/immutability contract mismatch")
    if contract["release_scope_decision"].get("required_assets") != list(EXPECTED_ASSETS):
        raise ReleaseExecutionError("required release asset order mismatch")
    _validate_history(root)
    _validate_workflow(root)
    scope = _scope_rows(root)
    if len(scope) != len({(row["change_kind"], row["relative_path"]) for row in scope}):
        raise ReleaseExecutionError("duplicate ST08_14C scope row")
    observed_scope = [(row["change_kind"], row["relative_path"]) for row in scope]
    if observed_scope != PLANNED_CHANGES:
        raise ReleaseExecutionError("ST08_14C scope differs from the exact planned change set")
    security = (root / "SECURITY.md").read_text(encoding="utf-8")
    if "GitHub Release `v0.1.0` опубликован" not in security or "не выпущен" in security:
        raise ReleaseExecutionError("SECURITY.md does not reflect the published release")
    return {"status": "PASS", "manifest": validate_manifest(root), "immutable_ST08_14B": len(IMMUTABLE_ST08_14B), "planned_change_paths": len(scope), "protected_scientific_artifacts": release_assurance.validate_protected_hashes(root, inventory="published")}


def _validate_asset_map(assets: Mapping[str, Any]) -> None:
    if set(assets) != set(EXPECTED_ASSETS):
        raise ReleaseExecutionError("release asset name set mismatch")
    for name, expected in EXPECTED_ASSETS.items():
        observed = assets[name]
        if observed.get("sha256") != expected["sha256"] or observed.get("size_bytes") != expected["size_bytes"] or observed.get("state") != "uploaded":
            raise ReleaseExecutionError(f"release asset mismatch: {name}")


def validate_evidence(evidence: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_14C_release_0_1_0_GitHub_execution_evidence_v01" or evidence.get("task_id") != "ST08_14C_release_0_1_0_GitHub_execution" or evidence.get("profile") != "CHANGE":
        raise ReleaseExecutionError("evidence identity mismatch")
    authority = evidence.get("authority", {})
    if authority.get("authorized_task_label") != "NEXT_BLOCK_AUTHORIZED: ST08_14C_release_0_1_0_GitHub_execution" or authority.get("release_notes_repair_authorized") is not True:
        raise ReleaseExecutionError("John authority evidence mismatch")
    release = evidence.get("release", {})
    exact = {"repository": "Vanargo/ML-CRA", "release_id": 383873796, "tag": "v0.1.0", "commit": RELEASE_COMMIT, "git_tree": RELEASE_TREE, "tag_ref_type": "commit", "draft": False, "prerelease": False, "immutable": True}
    for key, value in exact.items():
        if release.get(key) != value:
            raise ReleaseExecutionError(f"release evidence mismatch: {key}")
    _validate_asset_map(release.get("assets", {}))
    repair = release.get("release_notes_repair", {})
    if repair.get("authorized") is not True or repair.get("body_exact_after_repair") is not True or repair.get("tag_or_asset_changed") is not False:
        raise ReleaseExecutionError("release-notes repair evidence mismatch")
    attestation = evidence.get("attestation", {})
    if attestation.get("predicate_type") != "https://in-toto.io/attestation/release/v0.2" or attestation.get("release_commit") != RELEASE_COMMIT or attestation.get("asset_sha256") != {name: value["sha256"] for name, value in EXPECTED_ASSETS.items()}:
        raise ReleaseExecutionError("release attestation evidence mismatch")
    commands = evidence.get("verification_commands", [])
    if len(commands) != 4 or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in commands):
        raise ReleaseExecutionError("four successful GitHub CLI verifications are required")
    expected_manifest = dict(bindings["manifest"])
    if evidence.get("successor_manifest") != expected_manifest:
        raise ReleaseExecutionError("successor manifest evidence mismatch")
    hosted = evidence.get("hosted_assurance", {})
    state = hosted.get("status")
    if state == "PENDING":
        if evidence.get("readiness") != "NOT_READY" or hosted.get("run_id") is not None:
            raise ReleaseExecutionError("pending hosted assurance state mismatch")
    elif state == "PASS":
        head_sha = hosted.get("head_sha")
        if evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE" or not isinstance(hosted.get("run_id"), int) or not isinstance(hosted.get("job_id"), int) or hosted.get("conclusion") != "success" or not isinstance(hosted.get("pull_request_url"), str) or not isinstance(head_sha, str) or len(head_sha) != 40 or any(character not in "0123456789abcdef" for character in head_sha):
            raise ReleaseExecutionError("successful hosted assurance evidence incomplete")
    else:
        raise ReleaseExecutionError("hosted assurance status must be PENDING or PASS")
    if evidence.get("technical_status") != "PASS" or evidence.get("scientific_interpretation", {}).get("scientific_validation_performed") is not False:
        raise ReleaseExecutionError("technical/scientific boundary mismatch")
    reconciliation = evidence.get("change_reconciliation", {})
    if reconciliation != {
        "planned_paths": len(PLANNED_CHANGES),
        "actual_paths": len(PLANNED_CHANGES),
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise ReleaseExecutionError("planned/actual change reconciliation mismatch")
    return {"status": "PASS", "hosted_assurance": state, "assets": len(EXPECTED_ASSETS)}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    bindings = validate_contract(root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": bindings, "evidence": validate_evidence(evidence, bindings)}


def build_release(output_dir: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    permitted = (root / "dist").resolve()
    if output_dir == permitted or permitted not in output_dir.parents:
        raise ReleaseExecutionError("output must be a dedicated dist subdirectory")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ReleaseExecutionError("output directory must be absent or empty")
    with tempfile.TemporaryDirectory(prefix="st08_14C_release_") as temporary:
        clone = Path(temporary) / "release-source"
        _run(["git", "clone", "--quiet", "--no-hardlinks", "--local", str(root), str(clone)], root)
        _run(["git", "checkout", "--quiet", "--detach", RELEASE_COMMIT], clone)
        if _run(["git", "rev-parse", "HEAD"], clone) != RELEASE_COMMIT or _run(["git", "rev-parse", "HEAD^{tree}"], clone) != RELEASE_TREE:
            raise ReleaseExecutionError("release commit/tree checkout mismatch")
        built = candidate_assurance.build_candidate(clone / "dist/st08_14C-build", clone)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in EXPECTED_ASSETS:
            shutil.copy2(clone / "dist/st08_14C-build" / name, output_dir / name)
    assets = {name: {"sha256": _sha256_file(output_dir / name), "size_bytes": (output_dir / name).stat().st_size} for name in EXPECTED_ASSETS}
    for name, expected in EXPECTED_ASSETS.items():
        if assets[name] != expected:
            raise ReleaseExecutionError(f"rebuilt release asset mismatch: {name}")
    return {"status": "PASS", "commit": RELEASE_COMMIT, "git_tree": RELEASE_TREE, "independent_builds": built["independent_builds"], "assets": assets}


def _expect_rejection(label: str, action: Any) -> str:
    try:
        action()
    except (ReleaseExecutionError, release_assurance.AssuranceError):
        return label
    raise ReleaseExecutionError(f"negative mutation accepted: {label}")


def run_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    bindings = validate_contract(root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    labels = []
    for label, mutate in [
        ("wrong_authority", lambda value: value["authority"].update(authorized_task_label="wrong")),
        ("mutable_release", lambda value: value["release"].update(immutable=False)),
        ("wrong_commit", lambda value: value["release"].update(commit="0" * 40)),
        ("asset_drift", lambda value: value["release"]["assets"]["SHA256SUMS"].update(sha256="0" * 64)),
        ("attestation_drift", lambda value: value["attestation"].update(release_commit="0" * 40)),
        ("notes_repair_overreach", lambda value: value["release"]["release_notes_repair"].update(tag_or_asset_changed=True)),
        ("verification_failure", lambda value: value["verification_commands"][0].update(exit_code=1, status="FAIL")),
        ("manifest_drift", lambda value: value["successor_manifest"].update(manifest_sha256="0" * 64)),
    ]:
        mutated = copy.deepcopy(evidence)
        mutate(mutated)
        labels.append(_expect_rejection(label, lambda value=mutated: validate_evidence(value, bindings)))
    return {"status": "PASS", "mutations_rejected": len(labels), "labels": labels}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ST08_14C immutable GitHub Release assurance")
    parser.add_argument("command", choices=("write-manifest", "contract", "mutations", "final-evidence", "build-release"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "contract":
            result = validate_contract()
        elif args.command == "mutations":
            result = run_mutations()
        elif args.command == "final-evidence":
            result = validate_final_evidence()
        else:
            if args.output_dir is None:
                raise ReleaseExecutionError("--output-dir is required")
            result = build_release(args.output_dir)
    except (ReleaseExecutionError, release_assurance.AssuranceError, candidate_assurance.CandidateFinalizationError, csv.Error, json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
