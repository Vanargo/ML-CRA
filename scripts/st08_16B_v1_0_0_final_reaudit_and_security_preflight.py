from __future__ import annotations

import argparse
import copy
import csv
import email
import hashlib
import json
import re
import shutil
import tarfile
import tempfile
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from scripts import st08_09_release_assurance as release_assurance
    from scripts import st08_14A_release_candidate_finalization_assurance as build_tools
    from scripts import st08_16A_v1_0_0_candidate_finalization_assurance as candidate_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance
    import st08_14A_release_candidate_finalization_assurance as build_tools
    import st08_16A_v1_0_0_candidate_finalization_assurance as candidate_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_16B_v1_0_0_final_reaudit_and_security_preflight_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_16B_v1_0_0_final_candidate_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_16B_v1_0_0_final_reaudit_and_security_preflight_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_16B_v1_0_0_final_reaudit_and_security_preflight_change_scope_v01.csv"
RUNBOOK_PATH = PROJECT_ROOT / "docs/release/release_1_0_0_GitHub_execution_runbook_v01.md"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
VERSION = "1.0.0"


class FinalCandidatePreflightError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FinalCandidatePreflightError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise FinalCandidatePreflightError(f"CSV is empty or lacks rows: {path}")
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


def _unique(values: Sequence[str], label: str) -> list[str]:
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise FinalCandidatePreflightError(f"{label} must occur exactly once: {duplicates}")
    return list(values)


def _assert_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise FinalCandidatePreflightError("authority object missing")
    if authority.get("authorized_decision") != "NEXT_BLOCK_AUTHORIZED":
        raise FinalCandidatePreflightError("reserved John authorization decision missing")
    if authority.get("resolved_context_task_id") != contract.get("task_id"):
        raise FinalCandidatePreflightError("contextual task resolution does not bind this task")
    allowed_true = {
        "final_candidate_reaudit_authorized",
        "local_candidate_rebuild_authorized",
        "read_only_GitHub_observation_authorized",
    }
    for key, value in authority.items():
        if key in {
            "accepted_and_closed_previous_task",
            "authorized_decision",
            "resolved_context_task_id",
            "resolution_basis",
        }:
            continue
        if key in allowed_true:
            if value is not True:
                raise FinalCandidatePreflightError(f"authorized validation operation disabled: {key}")
        elif key.endswith("_authorized") and value is not False:
            raise FinalCandidatePreflightError(f"external, product, scientific or future authority overstated: {key}")


def _tracked_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    policy = release_assurance._load_json(root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    forbidden = [
        path
        for path in tracked
        if release_assurance.classify_public_path(path, policy, root)
        not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}
    ]
    if forbidden:
        raise FinalCandidatePreflightError(f"tracked preflight tree contains excluded paths: {forbidden}")
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise FinalCandidatePreflightError(f"cycle-breaking path is not tracked: {missing}")
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
        raise FinalCandidatePreflightError("successor manifest schema mismatch")
    paths = _unique([row["relative_path"] for row in rows], "manifest path")
    if paths != sorted(paths):
        raise FinalCandidatePreflightError("successor manifest paths are not ordinally sorted")
    tracked = _tracked_paths(root, contract)
    exclusions = sorted(contract["successor_manifest"]["cycle_breaking_exclusions"])
    expected = sorted(set(tracked) - set(exclusions))
    if paths != expected:
        missing = sorted(set(expected) - set(paths))
        extra = sorted(set(paths) - set(expected))
        raise FinalCandidatePreflightError(f"successor manifest path mismatch: missing={missing} extra={extra}")
    for row in rows:
        payload = release_assurance.git_index_blob_bytes(row["relative_path"], root)
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise FinalCandidatePreflightError(f"invalid SHA-256 syntax: {row['relative_path']}")
        if row["sha256"] != _sha256_bytes(payload) or row["size_bytes"] != str(len(payload)):
            raise FinalCandidatePreflightError(f"manifest byte binding mismatch: {row['relative_path']}")
    manifest_payload = release_assurance.git_index_blob_bytes(
        MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root
    )
    all_paths = sorted(paths + exclusions)
    return {
        "paths": len(all_paths),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(all_paths),
        "manifest_sha256": _sha256_bytes(manifest_payload),
        "cycle_breaking_exclusions": exclusions,
    }


def _validate_immutable_predecessor(contract: Mapping[str, Any], root: Path) -> None:
    items = contract.get("immutable_ST08_16A", [])
    if len(items) != 7:
        raise FinalCandidatePreflightError("immutable ST08_16A set must contain seven artifacts")
    for item in items:
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise FinalCandidatePreflightError(f"immutable ST08_16A artifact changed: {item['path']}")


def validate_transition_surfaces(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    surfaces = {
        "README.md": ["unreleased local candidate", "No `v1.0.0` tag or GitHub"],
        "README_RU.md": ["неопубликованным локальным кандидатом", "Тег или GitHub Release `v1.0.0` ещё не существует"],
        "RELEASE_NOTES_1.0.0.md": ["unreleased local candidate", "do not claim", "неопубликованный локальный кандидат", "не утверждают"],
        "CITATION.cff": ['version: "1.0.0"'],
    }
    for relative, tokens in surfaces.items():
        text = (root / relative).read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in text]
        if missing:
            raise FinalCandidatePreflightError(f"registered transition surface drift: {relative}/{missing}")
        if relative == "CITATION.cff" and "date-released:" in text:
            raise FinalCandidatePreflightError("candidate CITATION prematurely contains date-released")
    return {
        "status": "PASS",
        "surfaces": list(surfaces),
        "publication_without_transition": "FORBIDDEN",
    }


def validate_runbook_text(text: str) -> None:
    required = [
        "не разрешением на выпуск",
        "отдельно авторизованном John блоке ST08_16C",
        "повторит известный",
        "точного SHA",
        "gh release verify v1.0.0",
        "gh release verify-asset v1.0.0",
        "TestPyPI и PyPI не входят",
        "SHA-256 подтверждает совпадение байтов, но не доказывает корректность",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise FinalCandidatePreflightError(f"release runbook omits required boundary: {missing}")
    ordered = [
        "Финализировать четыре release-state",
        "Зафиксировать переход",
        "Повторно построить",
        "Убедиться в отсутствии",
        "Создать draft GitHub Release",
        "До публикации прикрепить",
        "Сверить имена",
        "Один раз опубликовать",
        "После публикации выполнить",
        "Зарегистрировать URL",
    ]
    positions = [text.find(token) for token in ordered]
    if -1 in positions or positions != sorted(positions):
        raise FinalCandidatePreflightError("release runbook state-machine order mismatch")


def validate_workflow_text(text: str) -> None:
    required = [
        "permissions:\n  contents: read",
        "fetch-depth: 0",
        "st08_16B_v1_0_0_final_reaudit_and_security_preflight.py contract",
        "st08_16B_v1_0_0_final_reaudit_and_security_preflight.py mutations",
        "tests.test_v1_0_0_final_reaudit_and_security_preflight_st08_16B",
        "st08_16B_v1_0_0_final_reaudit_and_security_preflight.py build-preflight",
        "st08_16B_v1_0_0_final_reaudit_and_security_preflight.py validate-built",
        "st08_16B_v1_0_0_final_reaudit_and_security_preflight.py final-evidence",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise FinalCandidatePreflightError(f"workflow omits ST08_16B control: {missing}")
    forbidden = [
        "contents: write",
        "id-token: write",
        "attestations: write",
        "actions/upload-artifact",
        "gh release create",
        "pypa/gh-action-pypi-publish",
        "pull_request_target",
        "python scripts/st08_16A_v1_0_0_candidate_finalization_assurance.py",
    ]
    if any(token in text for token in forbidden):
        raise FinalCandidatePreflightError("assurance workflow gained release or unsafe authority")


def _scope_rows(root: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if fields != ["change_kind", "relative_path", "reason"]:
        raise FinalCandidatePreflightError("unexpected ST08_16B change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def _validate_scope(contract: Mapping[str, Any], observed: Sequence[tuple[str, str]]) -> None:
    expected = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    if list(observed) != expected or len(observed) != len(set(observed)):
        raise FinalCandidatePreflightError("actual change scope differs from planned changes")


def validate_external_observations(observed: Mapping[str, Any]) -> None:
    exact = {
        "repository": "Vanargo/ML-CRA",
        "default_branch": "main",
        "ruleset_id": 21408995,
        "required_status_check": "assurance",
        "existing_tags": ["v0.1.0", "v0.1.1"],
        "existing_releases": ["v0.1.0", "v0.1.1"],
        "v1_0_0_tag_exists": False,
        "v1_0_0_release_exists": False,
        "secret_scanning_enabled": True,
        "push_protection_enabled": True,
        "private_vulnerability_reporting_enabled": True,
        "dependabot_alerts_enabled": True,
        "open_dependabot_alerts": 0,
        "release_immutability_enabled": True,
        "ruleset_required_controls_pass": True,
        "GitHub_CLI_available": True,
        "ST08_16A_post_merge_assurance_conclusion": "success",
        "ST08_16A_post_merge_sha": "236bc4c48ef4ff40b170b68c860b600e788a7710",
        "v0_1_0_immutable": True,
        "v0_1_0_commit": "9d530b60fd262f21cfe63eb2482722972a24c3d2",
        "v0_1_1_immutable": True,
        "v0_1_1_commit": "1cfa920ec91d85341525f1ca6ef57a060dcb9cce",
    }
    mismatches = {key: (observed.get(key), value) for key, value in exact.items() if observed.get(key) != value}
    if mismatches:
        raise FinalCandidatePreflightError(f"external preflight observation missing or mismatched: {mismatches}")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T[^ ]+Z", str(observed.get("authenticated_owner_observed_at", ""))):
        raise FinalCandidatePreflightError("authenticated observation timestamp missing")
    if not re.fullmatch(
        r"https://github\.com/Vanargo/ML-CRA/actions/runs/\d+(?:/job/\d+)?",
        str(observed.get("ST08_16A_post_merge_run_url", "")),
    ):
        raise FinalCandidatePreflightError("exact post-merge assurance URL missing")
    if not re.match(r"gh version \d+\.\d+\.\d+", str(observed.get("GitHub_CLI_version", ""))):
        raise FinalCandidatePreflightError("observed GitHub CLI version missing")
    assets = observed.get("v0_1_0_assets")
    expected_assets = {
        "SHA256SUMS": "e663f0789d00fdc3c5dcedb100d42b5816d8fb553f53978b6dcb2a2db9f59279",
        "ml_cra-0.1.0-py3-none-any.whl": "9c8ccfd75a099354ece47cb27cd002aaee4824517986b6c735b5198f3423238a",
        "ml_cra-0.1.0.tar.gz": "56d40c2c78ca8bff4b51911ed01224a1899462a0a310d0f6bda1c7d971e43d13",
    }
    if assets != expected_assets:
        raise FinalCandidatePreflightError("immutable v0.1.0 asset observation mismatch")
    assets = observed.get("v0_1_1_assets")
    expected_assets = {
        "SHA256SUMS": "169022a8181f2d51ca7a795dc8ab138109c2b86500dc5197357ad265f80aaab2",
        "ml_cra-0.1.1-py3-none-any.whl": "2ce7ffbc8d030b61623539b5707a160db290c5fe28363d9a33d977bb0f144dcb",
        "ml_cra-0.1.1.tar.gz": "69316f4e99dc41de1d15a92c780ed4a22c77a73a64cdd5f750765463f0bb788a",
    }
    if assets != expected_assets:
        raise FinalCandidatePreflightError("immutable v0.1.1 asset observation mismatch")


def _asset_rows(candidate_dir: Path) -> tuple[Path, Path, Path]:
    sdists = list(candidate_dir.glob("*.tar.gz"))
    wheels = list(candidate_dir.glob("*.whl"))
    checksums = candidate_dir / "SHA256SUMS"
    if len(sdists) != 1 or len(wheels) != 1 or not checksums.is_file():
        raise FinalCandidatePreflightError("candidate directory must contain one sdist, one wheel and SHA256SUMS")
    return sdists[0], wheels[0], checksums


def validate_candidate_assets(sdist: Path, wheel: Path, checksum_file: Path) -> dict[str, Any]:
    if sdist.name != "ml_cra-1.0.0.tar.gz" or wheel.name != "ml_cra-1.0.0-py3-none-any.whl":
        raise FinalCandidatePreflightError("candidate asset filename mismatch")
    archive_result = release_assurance.verify_archives(sdist, wheel)
    with tarfile.open(sdist, "r:gz") as archive:
        names = [member.name for member in archive.getmembers() if member.isfile()]
        pkg_name = next((name for name in names if name.endswith("/PKG-INFO")), None)
        if pkg_name is None:
            raise FinalCandidatePreflightError("sdist PKG-INFO missing")
        stream = archive.extractfile(pkg_name)
        if stream is None:
            raise FinalCandidatePreflightError("sdist PKG-INFO unreadable")
        metadata = email.message_from_bytes(stream.read())
        if PurePosixPath(pkg_name).parts[0] != "ml_cra-1.0.0" or metadata.get("Version") != VERSION:
            raise FinalCandidatePreflightError("sdist root or metadata version mismatch")
        if "Development Status :: 5 - Production/Stable" not in metadata.get_all("Classifier", []):
            raise FinalCandidatePreflightError("sdist stable classifier missing")
        if not any(name.endswith("/LICENSE") for name in names):
            raise FinalCandidatePreflightError("sdist LICENSE missing")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        entry_name = next((name for name in names if name.endswith(".dist-info/entry_points.txt")), None)
        if metadata_name is None or entry_name is None:
            raise FinalCandidatePreflightError("wheel metadata or entry point missing")
        if PurePosixPath(metadata_name).parts[0] != "ml_cra-1.0.0.dist-info":
            raise FinalCandidatePreflightError("wheel dist-info version mismatch")
        metadata = email.message_from_bytes(archive.read(metadata_name))
        if metadata.get("Version") != VERSION:
            raise FinalCandidatePreflightError("wheel Core Metadata version mismatch")
        if "Development Status :: 5 - Production/Stable" not in metadata.get_all("Classifier", []):
            raise FinalCandidatePreflightError("wheel stable classifier missing")
        if "mlcra = mlcra.cli:main" not in archive.read(entry_name).decode("utf-8"):
            raise FinalCandidatePreflightError("wheel console entry point mismatch")
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
            raise FinalCandidatePreflightError("wheel LICENSE missing")
    expected_lines = sorted(
        [
            f"{_sha256_file(sdist)}  {sdist.name}",
            f"{_sha256_file(wheel)}  {wheel.name}",
        ]
    )
    if checksum_file.read_text(encoding="ascii").splitlines() != expected_lines:
        raise FinalCandidatePreflightError("SHA256SUMS does not exactly bind both assets")
    return {"status": "PASS", "metadata_version": VERSION, "archive_assurance": archive_result}


def build_candidate(output_dir: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    candidate_assurance.validate_metadata(root)
    output_dir = output_dir.resolve()
    permitted = (root / "dist").resolve()
    if output_dir == permitted or permitted not in output_dir.parents:
        raise FinalCandidatePreflightError("candidate output must be a dedicated subdirectory of dist/")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FinalCandidatePreflightError("candidate output directory must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    epoch = int(contract["candidate_preflight"]["source_date_epoch"])
    builds: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="st08_16B_build_") as temporary:
        temporary_root = Path(temporary)
        for index in (1, 2):
            source = temporary_root / f"source_{index}"
            raw_output = temporary_root / f"raw_{index}"
            normalized = temporary_root / f"normalized_{index}.tar.gz"
            build_tools._checkout_index(source, root)
            sdist, wheel = build_tools._run_build(source, raw_output, epoch, root)
            normalized_result = build_tools.normalize_sdist(sdist, normalized, epoch)
            builds.append(
                {
                    "index": index,
                    "normalized_sdist": normalized,
                    "sdist_sha256": normalized_result["sha256"],
                    "wheel": wheel,
                    "wheel_sha256": _sha256_file(wheel),
                }
            )
        if len({row["sdist_sha256"] for row in builds}) != 1:
            raise FinalCandidatePreflightError("normalized sdist builds are not byte-identical")
        if len({row["wheel_sha256"] for row in builds}) != 1:
            raise FinalCandidatePreflightError("wheel builds are not byte-identical")
        final_sdist = output_dir / "ml_cra-1.0.0.tar.gz"
        final_wheel = output_dir / "ml_cra-1.0.0-py3-none-any.whl"
        shutil.copyfile(builds[0]["normalized_sdist"], final_sdist)
        shutil.copyfile(builds[0]["wheel"], final_wheel)
    checksums = output_dir / "SHA256SUMS"
    checksum_lines = sorted(
        [
            f"{_sha256_file(final_sdist)}  {final_sdist.name}",
            f"{_sha256_file(final_wheel)}  {final_wheel.name}",
        ]
    )
    checksums.write_text("\n".join(checksum_lines) + "\n", encoding="ascii", newline="\n")
    archive = validate_candidate_assets(final_sdist, final_wheel, checksums)
    return {
        "status": "PASS",
        "version": VERSION,
        "source_representation": "canonical_Git_index_checkout",
        "source_date_epoch": epoch,
        "independent_builds": 2,
        "normalized_sdist_reproducible": True,
        "wheel_reproducible": True,
        "assets": {
            path.name: {"sha256": _sha256_file(path), "size_bytes": path.stat().st_size}
            for path in (final_sdist, final_wheel, checksums)
        },
        "archive_assurance": archive,
        "release_actions_performed": 0,
    }


def validate_built_candidate(candidate_dir: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    sdist, wheel, checksums = _asset_rows(candidate_dir)
    validate_candidate_assets(sdist, wheel, checksums)
    observed = {
        path.name: {"sha256": _sha256_file(path), "size_bytes": path.stat().st_size}
        for path in (sdist, wheel, checksums)
    }
    expected = contract["candidate_preflight"]["ST08_16B_assets"]
    if observed != expected:
        raise FinalCandidatePreflightError(f"exact ST08_16B asset binding mismatch: {observed}")
    return {
        "status": "PASS",
        "assets": observed,
        "registered_assets_match": True,
    }


def build_preflight(output_dir: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    _assert_authority(contract)
    result = build_candidate(output_dir, root)
    validated = validate_built_candidate(output_dir.resolve(), contract)
    return {
        "status": "PASS",
        "candidate": result,
        "preflight": validated,
        "release_actions_performed": 0,
    }


def validate_contract_bindings(contract: Mapping[str, Any], root: Path = PROJECT_ROOT) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_16B_v1_0_0_final_reaudit_and_security_preflight":
        raise FinalCandidatePreflightError("unexpected task identifier")
    if contract.get("profile") != "SCIENTIFIC_VALIDATION":
        raise FinalCandidatePreflightError("profile must be SCIENTIFIC_VALIDATION")
    _assert_authority(contract)
    if contract.get("decision_policy", {}).get("scientific_effect") != "NONE_no_new_training_claim_protocol_result_or_verdict":
        raise FinalCandidatePreflightError("scientific-effect boundary missing")
    if contract.get("legacy_gate_disposition") != {
        "ST08_16A_artifacts": "immutable_hash_verified_by_ST08_16B",
        "ST08_16A_state_dependent_validator": "historical_not_executed_against_successor_tree",
        "active_hosted_gate": "ST08_16B_successor_compatible",
    }:
        raise FinalCandidatePreflightError("legacy predecessor gate disposition mismatch")
    _validate_immutable_predecessor(contract, root)
    metadata = candidate_assurance.validate_metadata(root)
    protected = release_assurance.validate_protected_hashes(root, inventory="published")
    manifest = validate_manifest(root, contract)
    _validate_scope(contract, _scope_rows(root))
    transition = validate_transition_surfaces(root)
    validate_runbook_text((root / RUNBOOK_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8"))
    validate_workflow_text((root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8"))
    for relative in (ROADMAP_PATH, STAGE_PATH):
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [contract["task_id"], "release_actions_performed: 0", "ST08_16C_authorized: false"]:
            if token not in text:
                raise FinalCandidatePreflightError(f"canonical task registration missing: {relative}/{token}")
    if len(contract.get("authoritative_support", [])) != 9:
        raise FinalCandidatePreflightError("authoritative source set mismatch")
    return {
        "status": "PASS",
        "metadata": metadata,
        "manifest": manifest,
        "protected": protected,
        "immutable_ST08_16A": 7,
        "change_scope": len(contract["planned_changes"]),
        "transition": transition,
        "release_actions_performed": 0,
    }


def validate_evidence(evidence: Mapping[str, Any], contract: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_16B_v1_0_0_final_reaudit_and_security_preflight_evidence_v01":
        raise FinalCandidatePreflightError("unexpected evidence schema")
    if evidence.get("task_id") != contract["task_id"] or evidence.get("profile") != "SCIENTIFIC_VALIDATION":
        raise FinalCandidatePreflightError("evidence task or profile mismatch")
    expected_manifest = dict(bindings["manifest"])
    expected_manifest["status"] = "PASS"
    if evidence.get("successor_manifest") != expected_manifest:
        raise FinalCandidatePreflightError("evidence manifest binding mismatch")
    validate_external_observations(evidence.get("external_observations", {}))
    if evidence.get("candidate_assets") != contract["candidate_preflight"]["ST08_16B_assets"]:
        raise FinalCandidatePreflightError("candidate asset evidence mismatch")
    verdict = evidence.get("validation_verdict", {})
    if verdict.get("preflight") != "PASS_WITH_REQUIRED_RELEASE_STATE_TRANSITION":
        raise FinalCandidatePreflightError("bounded preflight verdict mismatch")
    if verdict.get("scientific_effect") != "NONE":
        raise FinalCandidatePreflightError("scientific effect overstated")
    if evidence.get("change_reconciliation") != {
        "planned_paths": 14,
        "actual_paths": 14,
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise FinalCandidatePreflightError("change reconciliation mismatch")
    if any(evidence.get(key) is not False for key in ["release_authorized", "release_performed"]):
        raise FinalCandidatePreflightError("release authority or action overstated")
    if any(evidence.get(key) != 0 for key in ["release_actions_performed", "training_runs", "scientific_artifact_changes"]):
        raise FinalCandidatePreflightError("forbidden side effect recorded")
    hosted = evidence.get("hosted_assurance")
    if not isinstance(hosted, Mapping):
        raise FinalCandidatePreflightError("hosted assurance evidence missing")
    expected_failed_attempt = {
        "attempt": 1,
        "status": "FAIL",
        "pull_request": 28,
        "run_id": 39425088682,
        "job_id": 118635516629,
        "head_sha": "9980b274c9c9b3f4da8f8fcb752b6527f40391e4",
        "event": "pull_request",
        "conclusion": "failure",
        "run_url": "https://github.com/Vanargo/ML-CRA/actions/runs/39425088682",
        "job_url": "https://github.com/Vanargo/ML-CRA/actions/runs/39425088682/job/118635516629",
        "failed_step": "Validate the v1.0.0 candidate finalization",
        "failed_step_number": 14,
        "failed_command": "python scripts/st08_16A_v1_0_0_candidate_finalization_assurance.py contract",
        "error": "successor manifest differs from the canonical Git index",
        "successful_github_steps_before_failure": 13,
        "skipped_github_steps_after_failure": 10,
        "completed_at": "2026-10-20T12:51:51Z",
        "root_cause": "superseded_state_dependent_ST08_16A_gate_executed_on_ST08_16B_successor_tree",
        "corrective_disposition": "remove_legacy_execution_preserve_immutable_hash_verification_require_new_exact_SHA_run",
    }
    expected_successful_attempt = {
        "attempt": 2,
        "status": "PASS",
        "pull_request": 28,
        "run_id": 39427719949,
        "job_id": 118644381949,
        "head_sha": "646e39e5f45cafce0a9b6662c2615992d9c5a1da",
        "event": "pull_request",
        "conclusion": "success",
        "run_url": "https://github.com/Vanargo/ML-CRA/actions/runs/39427719949",
        "job_url": "https://github.com/Vanargo/ML-CRA/actions/runs/39427719949/job/118644381949",
        "required_step": "Validate the v1.0.0 final re-audit and security preflight",
        "required_step_number": 14,
        "required_step_conclusion": "success",
        "successful_github_steps": 23,
        "skipped_github_steps": 0,
        "completed_at": "2026-10-20T13:13:40Z",
    }
    if evidence.get("hosted_attempts") != [expected_failed_attempt, expected_successful_attempt]:
        raise FinalCandidatePreflightError("hosted attempt sequence evidence mismatch")
    expected_hosted = {
        "status": "PASS",
        "pull_request": 28,
        "run_id": 39427719949,
        "job_id": 118644381949,
        "head_sha": "646e39e5f45cafce0a9b6662c2615992d9c5a1da",
        "event": "pull_request",
        "conclusion": "success",
        "run_url": "https://github.com/Vanargo/ML-CRA/actions/runs/39427719949",
        "job_url": "https://github.com/Vanargo/ML-CRA/actions/runs/39427719949/job/118644381949",
        "required_step": "Validate the v1.0.0 final re-audit and security preflight",
        "required_step_conclusion": "success",
        "final_evidence": "PASS",
        "primary_steps": 22,
        "completed_at": "2026-10-20T13:13:40Z",
        "pr_state": "OPEN",
        "is_draft": False,
        "mergeable": "MERGEABLE",
        "merge_state_status": "CLEAN",
    }
    if hosted != expected_hosted:
        raise FinalCandidatePreflightError("successful hosted assurance binding mismatch")
    expected_readiness = "READY_FOR_JOHN_ACCEPTANCE" if hosted.get("status") == "PASS" else "NOT_READY"
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != expected_readiness:
        raise FinalCandidatePreflightError("technical status or hosted-dependent readiness mismatch")
    return {
        "status": "PASS",
        "preflight": verdict["preflight"],
        "hosted_status": hosted.get("status"),
        "release_actions_performed": 0,
    }


def _expect_rejection(label: str, action: Any) -> str:
    try:
        action()
    except (
        FinalCandidatePreflightError,
        candidate_assurance.CandidateFinalizationError,
        build_tools.CandidateFinalizationError,
        release_assurance.AssuranceError,
    ):
        return label
    raise FinalCandidatePreflightError(f"negative mutation was accepted: {label}")


def run_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    workflow = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    runbook = (root / RUNBOOK_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    mutations: list[str] = []
    mutated = copy.deepcopy(contract)
    mutated["authority"]["authorized_decision"] = "MISSING"
    mutations.append(_expect_rejection("wrong_authority", lambda: _assert_authority(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["authority"]["GitHub_release_authorized"] = True
    mutations.append(_expect_rejection("release_authority", lambda: _assert_authority(mutated)))
    mutated = copy.deepcopy(contract)
    mutated["immutable_ST08_16A"][0]["sha256"] = "0" * 64
    mutations.append(_expect_rejection("immutable_predecessor", lambda: _validate_immutable_predecessor(mutated, root)))
    mutations.append(_expect_rejection("workflow_write", lambda: validate_workflow_text(workflow.replace("contents: read", "contents: write"))))
    mutations.append(_expect_rejection("workflow_upload", lambda: validate_workflow_text(workflow + "\nactions/upload-artifact")))
    mutations.append(_expect_rejection("shallow_checkout", lambda: validate_workflow_text(workflow.replace("fetch-depth: 0", "fetch-depth: 1"))))
    mutations.append(_expect_rejection("legacy_ST08_16A_gate", lambda: validate_workflow_text(workflow + "\npython scripts/st08_16A_v1_0_0_candidate_finalization_assurance.py contract")))
    mutations.append(_expect_rejection("missing_transition_order", lambda: validate_runbook_text(runbook.replace("2. Зафиксировать переход", "2. Removed"))))
    mutated = copy.deepcopy(contract)
    mutated["planned_changes"].pop()
    mutations.append(_expect_rejection("scope_omission", lambda: _validate_scope(mutated, _scope_rows(root))))
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    bad_external = dict(evidence["external_observations"], v1_0_0_tag_exists=True)
    mutations.append(_expect_rejection("existing_v1_0_0_tag", lambda: validate_external_observations(bad_external)))
    bad_external = dict(evidence["external_observations"], open_dependabot_alerts=1)
    mutations.append(_expect_rejection("open_dependabot_alert", lambda: validate_external_observations(bad_external)))
    bad_external = dict(evidence["external_observations"], release_immutability_enabled=False)
    mutations.append(_expect_rejection("release_immutability_disabled", lambda: validate_external_observations(bad_external)))
    mutated_evidence = copy.deepcopy(evidence)
    mutated_evidence["release_actions_performed"] = 1
    bindings = validate_contract_bindings(contract, root)
    mutations.append(_expect_rejection("release_side_effect", lambda: validate_evidence(mutated_evidence, contract, bindings)))
    if len(mutations) != 13 or len(set(mutations)) != 13:
        raise FinalCandidatePreflightError("mutation inventory must contain exactly 13 unique rejections")
    return {"status": "PASS", "mutations_rejected": len(mutations), "labels": mutations}


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    return validate_contract_bindings(contract, root)


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": bindings, "evidence": validate_evidence(evidence, contract, bindings)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_16B v1.0.0 final candidate re-audit and security preflight")
    parser.add_argument(
        "command",
        choices=("write-manifest", "contract", "mutations", "build-preflight", "validate-built", "final-evidence"),
    )
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--candidate-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        contract = _load_json(CONTRACT_PATH)
        if args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "contract":
            result = validate_contract()
        elif args.command == "mutations":
            result = run_mutations()
        elif args.command == "build-preflight":
            if args.output_dir is None:
                raise FinalCandidatePreflightError("--output-dir is required for build-preflight")
            result = build_preflight(args.output_dir)
        elif args.command == "validate-built":
            if args.candidate_dir is None:
                raise FinalCandidatePreflightError("--candidate-dir is required for validate-built")
            result = validate_built_candidate(args.candidate_dir.resolve(), contract)
        else:
            result = validate_final_evidence()
    except (
        FinalCandidatePreflightError,
        candidate_assurance.CandidateFinalizationError,
        build_tools.CandidateFinalizationError,
        release_assurance.AssuranceError,
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
