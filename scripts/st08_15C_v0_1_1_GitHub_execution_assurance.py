from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

try:
    from scripts import st08_09_release_assurance as release_assurance
    from scripts import st08_14A_release_candidate_finalization_assurance as build_base
    from scripts import st08_15A_v0_1_1_corrective_candidate_assurance as candidate_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance
    import st08_14A_release_candidate_finalization_assurance as build_base
    import st08_15A_v0_1_1_corrective_candidate_assurance as candidate_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_15C_v0_1_1_GitHub_execution_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_15C_v0_1_1_GitHub_execution_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_15C_v0_1_1_GitHub_execution_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_15C_v0_1_1_GitHub_execution_change_scope_v01.csv"
RUNBOOK_PATH = PROJECT_ROOT / "docs/release/release_0_1_1_GitHub_execution_runbook_v01.md"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
VERSION = "0.1.1"
TAG = "v0.1.1"
REPOSITORY = "Vanargo/ML-CRA"
ASSET_NAMES = ["ml_cra-0.1.1.tar.gz", "ml_cra-0.1.1-py3-none-any.whl", "SHA256SUMS"]
PREPARED = "PREPARED_PENDING_EXACT_SHA_ASSURANCE_MERGE_AND_RELEASE"
RELEASED_PENDING = "RELEASED_VERIFIED_PENDING_HOSTED_EVIDENCE_CLOSURE"
RELEASED_CLOSED = "RELEASED_VERIFIED_AND_HOSTED_EVIDENCE_CLOSED"


class GitHubExecutionError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GitHubExecutionError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise GitHubExecutionError(f"CSV is empty or lacks rows: {path}")
    return fields, rows


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_list_sha256(paths: Sequence[str]) -> str:
    return _sha256_bytes("".join(f"{path}\n" for path in sorted(paths)).encode("utf-8"))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_git_sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _assert_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise GitHubExecutionError("authority object missing")
    if authority.get("authorized_task_label") != "NEXT_BLOCK_AUTHORIZED: ST08_15C_v0_1_1_GitHub_execution":
        raise GitHubExecutionError("exact John authorization label missing")
    allowed_true = {
        "release_state_finalization_authorized",
        "exact_SHA_pull_request_assurance_authorized",
        "GitHub_release_v0_1_1_execution_authorized",
        "draft_creation_and_asset_upload_authorized",
        "immutable_publication_authorized_after_all_gates",
        "protected_main_merge_requires_separate_John_confirmation",
    }
    for key, value in authority.items():
        if key in {"accepted_and_closed_previous_task", "authorized_task_label"}:
            continue
        if key in allowed_true:
            if value is not True:
                raise GitHubExecutionError(f"authorized ST08_15C operation disabled: {key}")
        elif key.endswith("_authorized") and value is not False:
            raise GitHubExecutionError(f"forbidden or out-of-scope authority overstated: {key}")


def _tracked_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise GitHubExecutionError(f"cycle-breaking path is not tracked: {missing}")
    policy = release_assurance._load_json(root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    forbidden = [
        path
        for path in tracked
        if release_assurance.classify_public_path(path, policy, root)
        not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}
    ]
    if forbidden:
        raise GitHubExecutionError(f"tracked release tree contains excluded paths: {forbidden}")
    return tracked


def _manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    rows: list[dict[str, str]] = []
    for relative in _tracked_paths(root, contract):
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
    rows = _manifest_rows(root, contract)
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=contract["successor_manifest"]["fields"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    all_paths = sorted(
        [row["relative_path"] for row in rows]
        + contract["successor_manifest"]["cycle_breaking_exclusions"]
    )
    return {
        "status": "PASS",
        "paths": len(all_paths),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(all_paths),
        "manifest_sha256": _sha256_file(path),
    }


def validate_manifest(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    if fields != contract["successor_manifest"]["fields"]:
        raise GitHubExecutionError("successor manifest schema mismatch")
    paths = [row["relative_path"] for row in rows]
    if paths != sorted(set(paths)):
        raise GitHubExecutionError("successor manifest paths must be unique and ordinally sorted")
    exclusions = sorted(contract["successor_manifest"]["cycle_breaking_exclusions"])
    tracked = _tracked_paths(root, contract)
    if paths != sorted(set(tracked) - set(exclusions)):
        raise GitHubExecutionError("successor manifest path set mismatch")
    for row in rows:
        payload = release_assurance.git_index_blob_bytes(row["relative_path"], root)
        if row["sha256"] != _sha256_bytes(payload) or row["size_bytes"] != str(len(payload)):
            raise GitHubExecutionError(f"successor manifest byte mismatch: {row['relative_path']}")
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


def _validate_immutable_predecessor(contract: Mapping[str, Any], root: Path) -> None:
    items = contract.get("immutable_ST08_15B", [])
    if len(items) != 4:
        raise GitHubExecutionError("immutable ST08_15B set must contain four non-cycle artifacts")
    for item in items:
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise GitHubExecutionError(f"immutable ST08_15B artifact changed: {item['path']}")


def validate_release_state(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    required = {
        "README.md": [
            "Version `0.1.1` is the current GitHub release",
            "releases/tag/v0.1.1",
            "has not been uploaded to\nTestPyPI or PyPI",
            "packaged_content_only_no_publication_authority",
        ],
        "README_RU.md": [
            "Версия `0.1.1` является текущим выпуском GitHub",
            "releases/tag/v0.1.1",
            "не загружалась в TestPyPI или\nPyPI",
            "packaged_content_only_no_publication_authority",
        ],
        "RELEASE_NOTES_0.1.1.md": [
            "# ML-CRA 0.1.1 release notes",
            "owner-authorized immutable GitHub Release",
            "авторизованный владельцем неизменяемый",
            "ST08_15C builds",
            "ST08_15C дважды собирает",
            "TestPyPI and PyPI remain deferred",
            "TestPyPI и PyPI остаются отложенными",
        ],
        "SECURITY.md": [
            "GitHub Release `v0.1.1` является текущим поддерживаемым выпуском",
            "releases/tag/v0.1.1",
            "`v0.1.0` сохраняется как исторический выпуск",
        ],
    }
    for relative, tokens in required.items():
        text = (root / relative).read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in text]
        if missing:
            raise GitHubExecutionError(f"final release-state surface mismatch: {relative}/{missing}")
    citation = candidate_assurance._parse_cff(root / "CITATION.cff")
    if citation.get("cff-version") != "1.2.0" or citation.get("version") != VERSION:
        raise GitHubExecutionError("CITATION.cff version identity mismatch")
    if "date-released" in citation:
        raise GitHubExecutionError("CITATION.cff must not guess the external release date before publication")
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project.get("version") != VERSION or "Development Status :: 3 - Alpha" not in project.get("classifiers", []):
        raise GitHubExecutionError("package version or maturity boundary mismatch")
    return {"status": "PASS", "version": VERSION, "surfaces": sorted(required), "citation_date_released": "ABSENT"}


def _scope_rows(root: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if fields != ["change_kind", "relative_path", "reason"]:
        raise GitHubExecutionError("unexpected ST08_15C change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def _validate_scope(contract: Mapping[str, Any], observed: Sequence[tuple[str, str]]) -> None:
    expected = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    if list(observed) != expected or len(observed) != len(set(observed)):
        raise GitHubExecutionError("actual ST08_15C change scope differs from planned changes")


def validate_workflow_text(text: str) -> None:
    required = [
        "permissions:\n  contents: read",
        "fetch-depth: 0",
        "st08_15C_v0_1_1_GitHub_execution_assurance.py contract",
        "st08_15C_v0_1_1_GitHub_execution_assurance.py mutations",
        "tests.test_v0_1_1_GitHub_execution_st08_15C",
        "st08_15C_v0_1_1_GitHub_execution_assurance.py build-release --source lifecycle",
        "--verify-contract-assets",
        "st08_15C_v0_1_1_GitHub_execution_assurance.py final-evidence",
        "gh release verify v0.1.0 --repo Vanargo/ML-CRA",
        "gh release verify v0.1.1 --repo Vanargo/ML-CRA",
        "RELEASED_VERIFIED_AND_HOSTED_EVIDENCE_CLOSED",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise GitHubExecutionError(f"workflow omits ST08_15C control: {missing}")
    forbidden = [
        "contents: write",
        "id-token: write",
        "attestations: write",
        "actions/upload-artifact",
        "gh release create",
        "gh release upload",
        "gh release edit",
        "--clobber",
        "pypa/gh-action-pypi-publish",
        "pull_request_target",
    ]
    if any(token in text for token in forbidden):
        raise GitHubExecutionError("assurance workflow gained release-write or unsafe authority")


def _validate_asset_contract(contract: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    assets = contract.get("release_assets", {}).get("assets")
    if not isinstance(assets, Mapping) or list(assets) != ASSET_NAMES:
        raise GitHubExecutionError("release asset contract name or order mismatch")
    result: dict[str, dict[str, Any]] = {}
    for name in ASSET_NAMES:
        row = assets[name]
        if not isinstance(row, Mapping) or not _is_sha256(row.get("sha256")):
            raise GitHubExecutionError(f"release asset SHA-256 missing: {name}")
        if not isinstance(row.get("size_bytes"), int) or row["size_bytes"] <= 0:
            raise GitHubExecutionError(f"release asset size missing: {name}")
        result[name] = {"sha256": row["sha256"], "size_bytes": row["size_bytes"]}
    return result


def validate_contract_bindings(contract: Mapping[str, Any], root: Path = PROJECT_ROOT) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_15C_v0_1_1_GitHub_execution" or contract.get("profile") != "CHANGE":
        raise GitHubExecutionError("task identity or profile mismatch")
    _assert_authority(contract)
    identity = contract.get("release_identity", {})
    exact_identity = {
        "repository": REPOSITORY,
        "version": VERSION,
        "tag": TAG,
        "title": "ML-CRA 0.1.1",
        "prerelease": False,
        "latest": True,
        "immutable_required": True,
    }
    for key, expected in exact_identity.items():
        if identity.get(key) != expected:
            raise GitHubExecutionError(f"release identity mismatch: {key}")
    if identity.get("required_assets") != ASSET_NAMES:
        raise GitHubExecutionError("required asset order mismatch")
    if contract.get("lifecycle_policy", {}).get("allowed_evidence_states") != [PREPARED, RELEASED_PENDING, RELEASED_CLOSED]:
        raise GitHubExecutionError("release lifecycle state set mismatch")
    if len(contract.get("execution_state_machine", [])) != 13:
        raise GitHubExecutionError("release state machine must contain exactly 13 ordered transitions")
    _validate_immutable_predecessor(contract, root)
    state = validate_release_state(root)
    assets = _validate_asset_contract(contract)
    manifest = validate_manifest(root, contract)
    _validate_scope(contract, _scope_rows(root))
    validate_workflow_text((root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8"))
    runbook = (root / RUNBOOK_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    for token in [
        "John отдельно авторизовал",
        "отдельного подтверждения John на слияние",
        "exact main commit",
        "Создать draft GitHub Release",
        "gh release verify v0.1.1",
        "TestPyPI и PyPI не входят",
    ]:
        if token not in runbook:
            raise GitHubExecutionError(f"active runbook boundary missing: {token}")
    for path in (STAGE_PATH, ROADMAP_PATH):
        text = (root / path.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [contract["task_id"], "ST08_15C_profile: CHANGE", "ST08_15C_authorized: true"]:
            if token not in text:
                raise GitHubExecutionError(f"canonical ST08_15C registration missing: {path}/{token}")
    if len(contract.get("authoritative_support", [])) != 9:
        raise GitHubExecutionError("authoritative source set mismatch")
    protected = release_assurance.validate_protected_hashes(root, inventory="published")
    return {
        "status": "PASS",
        "release_state": state,
        "assets": assets,
        "manifest": manifest,
        "immutable_ST08_15B": 4,
        "protected": protected,
        "planned_change_paths": len(contract["planned_changes"]),
    }


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return validate_contract_bindings(_load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT)), root)


def _asset_map(output_dir: Path) -> dict[str, dict[str, Any]]:
    if sorted(path.name for path in output_dir.iterdir() if path.is_file()) != sorted(ASSET_NAMES):
        raise GitHubExecutionError("release directory must contain exactly the three registered assets")
    return {
        name: {"sha256": _sha256_file(output_dir / name), "size_bytes": (output_dir / name).stat().st_size}
        for name in ASSET_NAMES
    }


def _release_source_spec(evidence: Mapping[str, Any]) -> dict[str, Any]:
    state = evidence.get("lifecycle_state")
    if state == PREPARED:
        return {
            "lifecycle_state": state,
            "source_representation": "canonical_Git_index_checkout",
            "commit": None,
            "git_tree": None,
        }
    if state not in {RELEASED_PENDING, RELEASED_CLOSED}:
        raise GitHubExecutionError(f"unknown lifecycle state for release build: {state}")
    release = evidence.get("release")
    if not isinstance(release, Mapping):
        raise GitHubExecutionError("released lifecycle lacks release identity")
    commit = release.get("commit")
    git_tree = release.get("git_tree")
    if not _is_git_sha(commit) or not _is_git_sha(git_tree):
        raise GitHubExecutionError("released lifecycle lacks exact commit or tree SHA")
    return {
        "lifecycle_state": state,
        "source_representation": "exact_released_commit_checkout",
        "commit": commit,
        "git_tree": git_tree,
    }


def _build_release_from_index(
    output_dir: Path,
    source_root: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    validate_release_state(source_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    epoch = int(contract["release_assets"]["source_date_epoch"])
    builds: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="st08_15C_build_") as temporary:
        temporary_root = Path(temporary)
        for index in (1, 2):
            source = temporary_root / f"source_{index}"
            raw = temporary_root / f"raw_{index}"
            normalized = temporary_root / f"normalized_{index}.tar.gz"
            build_base._checkout_index(source, source_root)
            sdist, wheel = build_base._run_build(source, raw, epoch, source_root)
            normalized_result = build_base.normalize_sdist(sdist, normalized, epoch)
            builds.append(
                {
                    "sdist": normalized,
                    "sdist_sha256": normalized_result["sha256"],
                    "wheel": wheel,
                    "wheel_sha256": _sha256_file(wheel),
                }
            )
        if len({row["sdist_sha256"] for row in builds}) != 1:
            raise GitHubExecutionError("normalized sdist builds are not byte-reproducible")
        if len({row["wheel_sha256"] for row in builds}) != 1:
            raise GitHubExecutionError("wheel builds are not byte-reproducible")
        shutil.copyfile(builds[0]["sdist"], output_dir / ASSET_NAMES[0])
        shutil.copyfile(builds[0]["wheel"], output_dir / ASSET_NAMES[1])
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text(
        "\n".join(
            sorted(
                [
                    f"{_sha256_file(output_dir / ASSET_NAMES[0])}  {ASSET_NAMES[0]}",
                    f"{_sha256_file(output_dir / ASSET_NAMES[1])}  {ASSET_NAMES[1]}",
                ]
            )
        )
        + "\n",
        encoding="ascii",
        newline="\n",
    )
    candidate_assurance.validate_candidate_assets(
        output_dir / ASSET_NAMES[0], output_dir / ASSET_NAMES[1], checksums
    )
    observed = _asset_map(output_dir)
    return {
        "status": "PASS",
        "version": VERSION,
        "source_date_epoch": epoch,
        "independent_builds": 2,
        "normalized_sdist_reproducible": True,
        "wheel_reproducible": True,
        "assets": observed,
    }


def build_release(
    output_dir: Path,
    root: Path = PROJECT_ROOT,
    *,
    verify_contract_assets: bool = False,
    source_policy: str = "lifecycle",
) -> dict[str, Any]:
    if source_policy != "lifecycle":
        raise GitHubExecutionError("build-release source policy must be lifecycle")
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    source_spec = _release_source_spec(evidence)
    output_dir = output_dir.resolve()
    permitted = (root / "dist").resolve()
    if output_dir == permitted or permitted not in output_dir.parents:
        raise GitHubExecutionError("release output must be a dedicated dist subdirectory")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise GitHubExecutionError("release output directory must be absent or empty")
    with tempfile.TemporaryDirectory(prefix="st08_15C_source_") as temporary:
        if source_spec["source_representation"] == "canonical_Git_index_checkout":
            source_root = root
        else:
            source_root = Path(temporary) / "release-source"
            process = subprocess.run(
                ["git", "clone", "--quiet", "--no-hardlinks", "--local", str(root), str(source_root)],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if process.returncode:
                raise GitHubExecutionError(f"cannot clone release source: {process.stderr.strip()}")
            for command in [
                ["git", "checkout", "--quiet", "--detach", source_spec["commit"]],
                ["git", "rev-parse", "HEAD"],
                ["git", "rev-parse", "HEAD^{tree}"],
            ]:
                process = subprocess.run(
                    command,
                    cwd=source_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                if process.returncode:
                    raise GitHubExecutionError(
                        f"release source command failed: {' '.join(command)}: {process.stderr.strip()}"
                    )
                if command[-1] == "HEAD" and process.stdout.strip() != source_spec["commit"]:
                    raise GitHubExecutionError("released commit checkout mismatch")
                if command[-1] == "HEAD^{tree}" and process.stdout.strip() != source_spec["git_tree"]:
                    raise GitHubExecutionError("released Git tree checkout mismatch")
            source_contract = _load_json(source_root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
            if source_contract.get("release_assets") != contract.get("release_assets"):
                raise GitHubExecutionError("released source and current release-asset contracts differ")
        build_output = output_dir if source_root == root else source_root / "dist/st08_15C-rebuild"
        result = _build_release_from_index(build_output, source_root, contract)
        if build_output != output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            for name in ASSET_NAMES:
                shutil.copy2(build_output / name, output_dir / name)
            result["assets"] = _asset_map(output_dir)
    if verify_contract_assets and result["assets"] != _validate_asset_contract(contract):
        raise GitHubExecutionError(f"release assets differ from contract: {result['assets']}")
    result.update(source_spec)
    return result


def render_release_body(commit: str, git_tree: str, assets: Mapping[str, Any], root: Path = PROJECT_ROOT) -> str:
    if not _is_git_sha(commit) or not _is_git_sha(git_tree):
        raise GitHubExecutionError("release body requires exact commit and tree SHA")
    if list(assets) != ASSET_NAMES:
        raise GitHubExecutionError("release body asset set mismatch")
    lines = [(root / "RELEASE_NOTES_0.1.1.md").read_text(encoding="utf-8").rstrip(), "", "## Exact release identity and integrity", "", f"- Commit: `{commit}`", f"- Git tree: `{git_tree}`", "- Release assets:"]
    for name in ASSET_NAMES:
        row = assets[name]
        if not _is_sha256(row.get("sha256")) or not isinstance(row.get("size_bytes"), int):
            raise GitHubExecutionError(f"release body asset binding incomplete: {name}")
        lines.append(f"  - `{name}` — `{row['sha256']}` ({row['size_bytes']} bytes)")
    lines.extend(
        [
            "",
            "The SHA-256 values establish byte identity only; they do not by themselves prove software correctness, security, or scientific validity.",
            "TestPyPI and PyPI are not part of this release execution.",
            "",
        ]
    )
    return "\n".join(lines)


def write_release_body(output_path: Path, commit: str, git_tree: str, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    body = render_release_body(commit, git_tree, _validate_asset_contract(contract), root)
    output_path = output_path.resolve()
    permitted = (root / "dist").resolve()
    if permitted not in output_path.parents:
        raise GitHubExecutionError("release body output must be inside dist")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8", newline="\n")
    return {"status": "PASS", "path": output_path.as_posix(), "sha256": _sha256_file(output_path)}


def _validate_hosted_run(value: Mapping[str, Any], label: str) -> None:
    if value.get("status") != "PASS" or value.get("conclusion") != "success":
        raise GitHubExecutionError(f"{label} hosted assurance is not PASS")
    if not isinstance(value.get("run_id"), int) or not isinstance(value.get("job_id"), int):
        raise GitHubExecutionError(f"{label} hosted assurance identifiers missing")
    if not _is_git_sha(value.get("head_sha")):
        raise GitHubExecutionError(f"{label} hosted assurance SHA missing")
    if not re.fullmatch(r"https://github\.com/Vanargo/ML-CRA/actions/runs/\d+", str(value.get("run_url", ""))):
        raise GitHubExecutionError(f"{label} hosted assurance URL missing")


def validate_evidence(evidence: Mapping[str, Any], contract: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_15C_v0_1_1_GitHub_execution_evidence_v01":
        raise GitHubExecutionError("unexpected evidence schema")
    if evidence.get("task_id") != contract["task_id"] or evidence.get("profile") != "CHANGE":
        raise GitHubExecutionError("evidence task or profile mismatch")
    expected_manifest = dict(bindings["manifest"])
    expected_manifest["status"] = "PASS"
    if evidence.get("successor_manifest") != expected_manifest:
        raise GitHubExecutionError("evidence manifest binding mismatch")
    if evidence.get("release_assets") != bindings["assets"]:
        raise GitHubExecutionError("evidence release asset binding mismatch")
    if evidence.get("change_reconciliation") != {
        "planned_paths": 18,
        "actual_paths": 18,
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise GitHubExecutionError("change reconciliation mismatch")
    if any(evidence.get(key) != 0 for key in ["training_runs", "scientific_artifact_changes", "PyPI_uploads", "TestPyPI_uploads", "v0_1_0_mutations"]):
        raise GitHubExecutionError("forbidden side effect recorded")
    state = evidence.get("lifecycle_state")
    if state not in [PREPARED, RELEASED_PENDING, RELEASED_CLOSED]:
        raise GitHubExecutionError("unknown evidence lifecycle state")
    if state == PREPARED:
        if evidence.get("release_performed") is not False or evidence.get("release_actions_performed") != 0:
            raise GitHubExecutionError("prepared evidence overstates release execution")
        if evidence.get("readiness") != "NOT_READY" or evidence.get("hosted_assurance", {}).get("status") != "PENDING":
            raise GitHubExecutionError("prepared evidence readiness or hosted state mismatch")
        release = evidence.get("release")
        if release not in ({}, None):
            raise GitHubExecutionError("prepared evidence must not invent a release object")
    else:
        if evidence.get("release_performed") is not True or evidence.get("release_actions_performed") != 3:
            raise GitHubExecutionError("released evidence action count mismatch")
        _validate_hosted_run(evidence.get("pre_release_assurance", {}), "pre-release")
        _validate_hosted_run(evidence.get("post_merge_assurance", {}), "post-merge")
        release = evidence.get("release", {})
        exact = {
            "repository": REPOSITORY,
            "tag": TAG,
            "title": "ML-CRA 0.1.1",
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "tag_ref_type": "commit",
        }
        for key, expected in exact.items():
            if release.get(key) != expected:
                raise GitHubExecutionError(f"release evidence mismatch: {key}")
        if not isinstance(release.get("release_id"), int) or not _is_git_sha(release.get("commit")) or not _is_git_sha(release.get("git_tree")):
            raise GitHubExecutionError("release identity lacks exact ID commit or tree")
        if release.get("assets") != bindings["assets"]:
            raise GitHubExecutionError("published asset binding mismatch")
        body = render_release_body(release["commit"], release["git_tree"], bindings["assets"])
        if release.get("body_sha256") != _sha256_bytes(body.encode("utf-8")):
            raise GitHubExecutionError("release body digest mismatch")
        commands = evidence.get("verification_commands", [])
        if len(commands) != 4 or any(row.get("exit_code") != 0 or row.get("status") != "PASS" for row in commands):
            raise GitHubExecutionError("four successful GitHub CLI verifications are required")
        attestation = evidence.get("attestation", {})
        if attestation.get("predicate_type") != "https://in-toto.io/attestation/release/v0.2" or attestation.get("release_commit") != release["commit"]:
            raise GitHubExecutionError("release attestation evidence mismatch")
        if attestation.get("asset_sha256") != {name: row["sha256"] for name, row in bindings["assets"].items()}:
            raise GitHubExecutionError("release attestation asset digests mismatch")
        closure = evidence.get("hosted_assurance", {})
        if state == RELEASED_PENDING:
            if closure.get("status") != "PENDING" or evidence.get("readiness") != "NOT_READY":
                raise GitHubExecutionError("released-pending closure state mismatch")
        else:
            _validate_hosted_run(closure, "evidence-closure")
            if evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
                raise GitHubExecutionError("closed evidence is not ready for John acceptance")
    if evidence.get("technical_status") != "PASS":
        raise GitHubExecutionError("technical status must be PASS")
    return {"status": "PASS", "lifecycle_state": state, "readiness": evidence["readiness"]}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": bindings, "evidence": validate_evidence(evidence, contract, bindings)}


def _expect_rejection(label: str, action: Any) -> str:
    try:
        action()
    except (GitHubExecutionError, release_assurance.AssuranceError, candidate_assurance.CorrectiveCandidateError):
        return label
    raise GitHubExecutionError(f"negative mutation accepted: {label}")


def run_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    workflow = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    labels: list[str] = []
    mutated = copy.deepcopy(contract)
    mutated["authority"]["PyPI_publication_authorized"] = True
    labels.append(_expect_rejection("PyPI_authority", lambda: _assert_authority(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["authority"]["protected_main_merge_requires_separate_John_confirmation"] = False
    labels.append(_expect_rejection("merge_gate_removed", lambda: _assert_authority(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["release_assets"]["assets"][ASSET_NAMES[0]]["sha256"] = "0" * 63
    labels.append(_expect_rejection("invalid_asset_digest", lambda: _validate_asset_contract(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["immutable_ST08_15B"][0]["sha256"] = "0" * 64
    labels.append(_expect_rejection("immutable_predecessor", lambda: _validate_immutable_predecessor(mutated, root)))
    labels.append(_expect_rejection("workflow_write", lambda: validate_workflow_text(workflow.replace("contents: read", "contents: write"))))
    labels.append(_expect_rejection("workflow_release_create", lambda: validate_workflow_text(workflow + "\ngh release create v0.1.1")))
    labels.append(_expect_rejection("workflow_clobber", lambda: validate_workflow_text(workflow + "\ngh release upload --clobber")))
    mutated = copy.deepcopy(evidence)
    mutated["release_performed"] = evidence.get("lifecycle_state") == PREPARED
    labels.append(_expect_rejection("premature_release_claim", lambda: validate_evidence(mutated, contract, bindings)))
    mutated = copy.deepcopy(evidence)
    mutated["readiness"] = (
        "NOT_READY"
        if evidence.get("lifecycle_state") == RELEASED_CLOSED
        else "READY_FOR_JOHN_ACCEPTANCE"
    )
    labels.append(_expect_rejection("premature_readiness", lambda: validate_evidence(mutated, contract, bindings)))
    mutated = copy.deepcopy(evidence)
    mutated["PyPI_uploads"] = 1
    labels.append(_expect_rejection("PyPI_side_effect", lambda: validate_evidence(mutated, contract, bindings)))
    labels.append(_expect_rejection("bad_release_body_commit", lambda: render_release_body("0" * 39, "0" * 40, bindings["assets"], root)))
    mutated = copy.deepcopy(contract)
    mutated["planned_changes"].pop()
    labels.append(_expect_rejection("scope_omission", lambda: _validate_scope(mutated, _scope_rows(root))))
    if len(labels) != 12 or len(set(labels)) != 12:
        raise GitHubExecutionError("mutation inventory must contain exactly 12 unique rejections")
    return {"status": "PASS", "mutations_rejected": len(labels), "labels": labels}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_15C v0.1.1 immutable GitHub Release assurance")
    parser.add_argument(
        "command",
        choices=("write-manifest", "contract", "mutations", "build-release", "write-release-body", "final-evidence"),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--commit")
    parser.add_argument("--git-tree")
    parser.add_argument("--verify-contract-assets", action="store_true")
    parser.add_argument("--source", choices=("lifecycle",), default="lifecycle")
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
        elif args.command == "build-release":
            if args.output_dir is None:
                raise GitHubExecutionError("--output-dir is required for build-release")
            result = build_release(
                args.output_dir,
                verify_contract_assets=args.verify_contract_assets,
                source_policy=args.source,
            )
        elif args.command == "write-release-body":
            if args.output_path is None or args.commit is None or args.git_tree is None:
                raise GitHubExecutionError("--output-path --commit and --git-tree are required")
            result = write_release_body(args.output_path, args.commit, args.git_tree)
        else:
            result = validate_final_evidence()
    except (
        GitHubExecutionError,
        release_assurance.AssuranceError,
        candidate_assurance.CorrectiveCandidateError,
        build_base.CandidateFinalizationError,
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
