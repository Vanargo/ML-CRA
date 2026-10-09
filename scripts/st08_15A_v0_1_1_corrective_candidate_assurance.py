from __future__ import annotations

import argparse
import copy
import csv
import email
import hashlib
import json
import re
import shutil
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from scripts import st08_09_release_assurance as release_assurance
    from scripts import st08_14A_release_candidate_finalization_assurance as build_base
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance
    import st08_14A_release_candidate_finalization_assurance as build_base


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_15A_v0_1_1_corrective_candidate_implementation_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_15A_v0_1_1_corrective_candidate_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_15A_v0_1_1_corrective_candidate_implementation_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_15A_v0_1_1_corrective_candidate_implementation_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
CITATION_PATH = PROJECT_ROOT / "CITATION.cff"
APPLICATION_PATH = PROJECT_ROOT / "src/mlcra/application.py"
RELEASE_NOTES_PATH = PROJECT_ROOT / "RELEASE_NOTES_0.1.1.md"
VERSION = "0.1.1"
READINESS_SCOPE = "packaged_content_only_no_publication_authority"


class CorrectiveCandidateError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CorrectiveCandidateError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise CorrectiveCandidateError(f"CSV is empty or lacks rows: {path}")
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


def _parse_cff(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - explicit prerequisite
        raise CorrectiveCandidateError("PyYAML from the assurance lock is required") from error
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, dict):
        raise CorrectiveCandidateError("CITATION.cff root must be a mapping")
    return value


def _assert_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise CorrectiveCandidateError("authority object missing")
    if authority.get("authorized_task_label") != (
        "NEXT_BLOCK_AUTHORIZED: ST08_15A_v0_1_1_corrective_candidate_implementation"
    ):
        raise CorrectiveCandidateError("John task authority is missing")
    allowed = {
        "candidate_implementation_authorized",
        "package_version_0_1_1_authorized",
        "local_candidate_asset_build_authorized",
    }
    for key, value in authority.items():
        if key in {"accepted_and_closed_previous_task", "authorized_task_label"}:
            continue
        if key in allowed:
            if value is not True:
                raise CorrectiveCandidateError(f"authorized operation disabled: {key}")
        elif key.endswith("_authorized") and value is not False:
            raise CorrectiveCandidateError(f"future or external authority overstated: {key}")


def validate_metadata(
    root: Path = PROJECT_ROOT,
    contract: Mapping[str, Any] | None = None,
    *,
    citation: Mapping[str, Any] | None = None,
    application_text: str | None = None,
    readme_text: str | None = None,
    readme_ru_text: str | None = None,
    notes_text: str | None = None,
) -> dict[str, Any]:
    contract = contract or _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    _assert_authority(contract)
    with (root / PYPROJECT_PATH.relative_to(PROJECT_ROOT)).open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project.get("version") != VERSION:
        raise CorrectiveCandidateError("pyproject version must be 0.1.1")
    if "Development Status :: 3 - Alpha" not in project.get("classifiers", []):
        raise CorrectiveCandidateError("Alpha maturity classifier missing")

    application = application_text if application_text is not None else (
        root / APPLICATION_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_application = [
        'PROJECT_VERSION = "0.1.1"',
        '"schema_version": "mlcra_doctor_report_v01"',
        '"release_ready": True',
        '"release_blockers": []',
        f'"release_readiness_scope": "{READINESS_SCOPE}"',
    ]
    missing = [token for token in required_application if token not in application]
    if missing:
        raise CorrectiveCandidateError(f"runtime corrective semantics missing: {missing}")
    forbidden_runtime = ["John_release_authorization_not_granted", 'PROJECT_VERSION = "0.1.0"']
    if any(token in application for token in forbidden_runtime):
        raise CorrectiveCandidateError("runtime retains superseded 0.1.0 readiness state")

    citation = citation or _parse_cff(root / CITATION_PATH.relative_to(PROJECT_ROOT))
    if citation.get("cff-version") != "1.2.0" or citation.get("version") != VERSION:
        raise CorrectiveCandidateError("CITATION.cff candidate version mismatch")
    if "date-released" in citation or "commit" in citation:
        raise CorrectiveCandidateError("CITATION.cff prematurely claims release execution")

    readme_text = readme_text if readme_text is not None else (root / "README.md").read_text(encoding="utf-8")
    readme_ru_text = readme_ru_text if readme_ru_text is not None else (root / "README_RU.md").read_text(encoding="utf-8")
    for label, text in (("README.md", readme_text), ("README_RU.md", readme_ru_text)):
        required = [VERSION, "RELEASE_NOTES_0.1.1.md", READINESS_SCOPE, "v0.1.0"]
        absent = [token for token in required if token not in text]
        if absent:
            raise CorrectiveCandidateError(f"{label} omits current candidate boundary: {absent}")

    notes = notes_text if notes_text is not None else (
        root / RELEASE_NOTES_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_notes = [
        "## English", "## Русский", "mlcra_doctor_report_v01", READINESS_SCOPE,
        "do not create a tag", "не создавались тег", "MiniBooNE", "UCI Wine Quality",
        "SOURCE_DATE_EPOCH", "ml_cra-0.1.1.tar.gz", "ml_cra-0.1.1-py3-none-any.whl",
        "SHA256SUMS", "TestPyPI", "PyPI", "v0.1.0",
    ]
    absent = [token for token in required_notes if token not in notes]
    if absent:
        raise CorrectiveCandidateError(f"0.1.1 notes omit required boundary: {absent}")
    hash_commands = re.findall(r"Get-FileHash[^\r\n]+", notes)
    if len(hash_commands) != 2 or hash_commands[0] != hash_commands[1]:
        raise CorrectiveCandidateError("bilingual SHA-256 commands differ")

    predecessor = contract["immutable_release_0_1_0"]
    predecessor_path = root / predecessor["release_notes_path"]
    if _sha256_file(predecessor_path) != predecessor["release_notes_sha256"]:
        raise CorrectiveCandidateError("immutable v0.1.0 candidate notes changed")
    return {
        "version": VERSION,
        "doctor_schema": "mlcra_doctor_report_v01",
        "release_ready": True,
        "release_blockers": [],
        "release_readiness_scope": READINESS_SCOPE,
        "citation_date_released": "ABSENT",
        "external_release_claimed": False,
    }


def _tracked_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    policy = release_assurance._load_json(root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    forbidden = [
        path for path in tracked
        if release_assurance.classify_public_path(path, policy, root)
        not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}
    ]
    if forbidden:
        raise CorrectiveCandidateError(f"tracked candidate tree contains excluded paths: {forbidden}")
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise CorrectiveCandidateError(f"cycle-breaking path is not tracked: {missing}")
    return tracked


def _manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    rows = []
    for relative in _tracked_paths(root, contract):
        if relative in exclusions:
            continue
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append({"relative_path": relative, "sha256": _sha256_bytes(payload), "size_bytes": str(len(payload))})
    return rows


def write_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    rows = _manifest_rows(root, contract)
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=contract["successor_manifest"]["fields"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tracked = sorted([row["relative_path"] for row in rows] + contract["successor_manifest"]["cycle_breaking_exclusions"])
    return {
        "status": "PASS", "paths": len(tracked), "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked), "manifest_sha256": _sha256_file(path),
    }


def validate_manifest(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    if fields != contract["successor_manifest"]["fields"]:
        raise CorrectiveCandidateError("successor manifest schema mismatch")
    paths = [row["relative_path"] for row in rows]
    if paths != sorted(set(paths)):
        raise CorrectiveCandidateError("successor manifest paths are not unique and sorted")
    tracked = _tracked_paths(root, contract)
    exclusions = sorted(contract["successor_manifest"]["cycle_breaking_exclusions"])
    expected = sorted(set(tracked) - set(exclusions))
    if paths != expected:
        raise CorrectiveCandidateError("successor manifest path set mismatch")
    for row in rows:
        payload = release_assurance.git_index_blob_bytes(row["relative_path"], root)
        if row["sha256"] != _sha256_bytes(payload) or row["size_bytes"] != str(len(payload)):
            raise CorrectiveCandidateError(f"successor manifest byte mismatch: {row['relative_path']}")
    manifest_payload = release_assurance.git_index_blob_bytes(MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root)
    all_paths = sorted(paths + exclusions)
    return {
        "paths": len(all_paths), "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(all_paths),
        "manifest_sha256": _sha256_bytes(manifest_payload),
        "cycle_breaking_exclusions": exclusions,
    }


def validate_candidate_assets(sdist: Path, wheel: Path, checksum_file: Path) -> dict[str, Any]:
    if sdist.name != "ml_cra-0.1.1.tar.gz" or wheel.name != "ml_cra-0.1.1-py3-none-any.whl":
        raise CorrectiveCandidateError("candidate asset filename mismatch")
    archive_result = release_assurance.verify_archives(sdist, wheel)
    with tarfile.open(sdist, "r:gz") as archive:
        pkg_info = next((member for member in archive.getmembers() if member.isfile() and member.name.endswith("/PKG-INFO")), None)
        if pkg_info is None:
            raise CorrectiveCandidateError("sdist PKG-INFO missing")
        stream = archive.extractfile(pkg_info)
        if stream is None:
            raise CorrectiveCandidateError("sdist PKG-INFO unreadable")
        metadata = email.message_from_bytes(stream.read())
        if PurePosixPath(pkg_info.name).parts[0] != "ml_cra-0.1.1" or metadata.get("Version") != VERSION:
            raise CorrectiveCandidateError("sdist root or metadata version mismatch")
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next((name for name in archive.namelist() if name.endswith(".dist-info/METADATA")), None)
        if metadata_name is None or PurePosixPath(metadata_name).parts[0] != "ml_cra-0.1.1.dist-info":
            raise CorrectiveCandidateError("wheel dist-info version mismatch")
        metadata = email.message_from_bytes(archive.read(metadata_name))
        if metadata.get("Version") != VERSION:
            raise CorrectiveCandidateError("wheel Core Metadata version mismatch")
    expected = sorted([
        f"{_sha256_file(sdist)}  {sdist.name}",
        f"{_sha256_file(wheel)}  {wheel.name}",
    ])
    if checksum_file.read_text(encoding="ascii").splitlines() != expected:
        raise CorrectiveCandidateError("SHA256SUMS does not exactly bind both assets")
    return {"sdist": archive_result["sdist"], "wheel": archive_result["wheel"], "checksums": 2}


def build_candidate(output_dir: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    validate_metadata(root, contract)
    output_dir = output_dir.resolve()
    permitted = (root / "dist").resolve()
    if output_dir == permitted or permitted not in output_dir.parents:
        raise CorrectiveCandidateError("candidate output must be a dedicated dist subdirectory")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise CorrectiveCandidateError("candidate output directory must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    epoch = int(contract["candidate_asset_contract"]["source_date_epoch"])
    builds: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="st08_15A_build_") as temporary:
        temporary_root = Path(temporary)
        for index in (1, 2):
            source = temporary_root / f"source_{index}"
            raw = temporary_root / f"raw_{index}"
            normalized = temporary_root / f"normalized_{index}.tar.gz"
            build_base._checkout_index(source, root)
            sdist, wheel = build_base._run_build(source, raw, epoch, root)
            normalized_result = build_base.normalize_sdist(sdist, normalized, epoch)
            builds.append({
                "sdist": normalized, "sdist_sha256": normalized_result["sha256"],
                "wheel": wheel, "wheel_sha256": _sha256_file(wheel),
            })
        if len({row["sdist_sha256"] for row in builds}) != 1:
            raise CorrectiveCandidateError("normalized sdist builds are not byte-reproducible")
        if len({row["wheel_sha256"] for row in builds}) != 1:
            raise CorrectiveCandidateError("wheel builds are not byte-reproducible")
        final_sdist = output_dir / "ml_cra-0.1.1.tar.gz"
        final_wheel = output_dir / "ml_cra-0.1.1-py3-none-any.whl"
        shutil.copyfile(builds[0]["sdist"], final_sdist)
        shutil.copyfile(builds[0]["wheel"], final_wheel)
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text("\n".join(sorted([
        f"{_sha256_file(final_sdist)}  {final_sdist.name}",
        f"{_sha256_file(final_wheel)}  {final_wheel.name}",
    ])) + "\n", encoding="ascii", newline="\n")
    archive = validate_candidate_assets(final_sdist, final_wheel, checksums)
    return {
        "status": "PASS", "version": VERSION, "source_representation": "canonical_Git_index_checkout",
        "source_date_epoch": epoch, "independent_builds": 2,
        "normalized_sdist_reproducible": True, "wheel_reproducible": True,
        "assets": {path.name: {"sha256": _sha256_file(path), "size_bytes": path.stat().st_size} for path in [final_sdist, final_wheel, checksums]},
        "archive_assurance": archive, "release_actions_performed": 0,
    }


def _load_scope(path: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(path)
    if fields != ["change_kind", "relative_path", "reason"]:
        raise CorrectiveCandidateError("unexpected ST08_15A scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_contract_bindings(
    contract: Mapping[str, Any], root: Path = PROJECT_ROOT, workflow_text: str | None = None,
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_15A_v0_1_1_corrective_candidate_implementation" or contract.get("profile") != "CHANGE":
        raise CorrectiveCandidateError("task identifier or profile mismatch")
    metadata = validate_metadata(root, contract)
    for item in contract.get("immutable_ST08_15", []):
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item["sha256"]:
            raise CorrectiveCandidateError(f"immutable ST08_15 artifact changed: {item['path']}")
    if len(contract.get("immutable_ST08_15", [])) != 6:
        raise CorrectiveCandidateError("immutable ST08_15 set must contain six artifacts")
    manifest = validate_manifest(root, contract)
    protected = release_assurance.validate_protected_hashes(root, inventory="published")
    expected_scope = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    observed_scope = _load_scope(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise CorrectiveCandidateError("actual change scope differs from planned changes")
    workflow = workflow_text if workflow_text is not None else (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    required_workflow = [
        "st08_15A_v0_1_1_corrective_candidate_assurance.py contract",
        "st08_15A_v0_1_1_corrective_candidate_assurance.py mutations",
        "tests.test_v0_1_1_corrective_candidate_st08_15A",
        "st08_15A_v0_1_1_corrective_candidate_assurance.py build-candidate",
        "st08_15A_v0_1_1_corrective_candidate_assurance.py final-evidence",
        "gh release verify v0.1.0 --repo Vanargo/ML-CRA",
    ]
    absent = [token for token in required_workflow if token not in workflow]
    if absent:
        raise CorrectiveCandidateError(f"workflow omits ST08_15A control: {absent}")
    candidate_wheel_selector = (
        "$wheel = Get-ChildItem -LiteralPath dist/st08_15A-ci -Filter *.whl"
    )
    predecessor_wheel_selector = (
        "$wheel = Get-ChildItem -LiteralPath dist/st08_14C-ci -Filter *.whl"
    )
    if workflow.count(candidate_wheel_selector) != 2:
        raise CorrectiveCandidateError(
            "workflow must validate and clean-install the current v0.1.1 candidate wheel"
        )
    if predecessor_wheel_selector in workflow:
        raise CorrectiveCandidateError(
            "workflow must not install the immutable v0.1.0 predecessor as the current candidate"
        )
    forbidden = ["gh release create", "pypa/gh-action-pypi-publish", "id-token: write", "contents: write"]
    if any(token in workflow for token in forbidden):
        raise CorrectiveCandidateError("workflow gained publication authority")
    for relative in [ROADMAP_PATH, STAGE_PATH]:
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [contract["task_id"], "release_actions_performed: 0", "ST08_15B_authorized: false"]:
            if token not in text:
                raise CorrectiveCandidateError(f"canonical task registration missing: {relative}/{token}")
    if len(contract.get("authoritative_support", [])) != 8:
        raise CorrectiveCandidateError("authoritative source set mismatch")
    return {"metadata": metadata, "manifest": manifest, "protected": protected, "immutable_ST08_15": 6, "change_scope": len(observed_scope), "release_actions_performed": 0}


def run_mutations(contract: Mapping[str, Any], root: Path = PROJECT_ROOT) -> dict[str, Any]:
    passed = 0
    mutations: list[tuple[str, Any]] = []
    unauthorized = copy.deepcopy(contract)
    unauthorized["authority"]["GitHub_release_authorized"] = True
    mutations.append(("reject_external_authority", lambda: _assert_authority(unauthorized)))
    wrong_version = _parse_cff(root / CITATION_PATH.relative_to(PROJECT_ROOT)); wrong_version["version"] = "0.1.0"
    mutations.append(("reject_citation_version", lambda: validate_metadata(root, contract, citation=wrong_version)))
    dated = _parse_cff(root / CITATION_PATH.relative_to(PROJECT_ROOT)); dated["date-released"] = "2026-10-09"
    mutations.append(("reject_premature_date", lambda: validate_metadata(root, contract, citation=dated)))
    application = (root / APPLICATION_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    mutations.append(("reject_false_readiness", lambda: validate_metadata(root, contract, application_text=application.replace('"release_ready": True', '"release_ready": False'))))
    mutations.append(("reject_removed_scope", lambda: validate_metadata(root, contract, application_text=application.replace(READINESS_SCOPE, "removed_scope"))))
    notes = (root / RELEASE_NOTES_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    mutations.append(("reject_missing_Russian_notes", lambda: validate_metadata(root, contract, notes_text=notes.replace("## Русский", "## Removed", 1))))
    scope_missing = copy.deepcopy(contract); scope_missing["planned_changes"].pop()
    mutations.append(("reject_scope_omission", lambda: validate_contract_bindings(scope_missing, root)))
    workflow = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8") + "\n# gh release create v0.1.1\n"
    mutations.append(("reject_release_command", lambda: validate_contract_bindings(contract, root, workflow)))
    clean_install_predecessor = (
        root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8").replace(
        "$wheel = Get-ChildItem -LiteralPath dist/st08_15A-ci -Filter *.whl",
        "$wheel = Get-ChildItem -LiteralPath dist/st08_14C-ci -Filter *.whl",
    )
    mutations.append((
        "reject_predecessor_wheel_clean_install",
        lambda: validate_contract_bindings(
            contract, root, clean_install_predecessor
        ),
    ))
    immutable = copy.deepcopy(contract); immutable["immutable_ST08_15"][0]["sha256"] = "0" * 64
    mutations.append(("reject_predecessor_mutation", lambda: validate_contract_bindings(immutable, root)))
    for name, mutation in mutations:
        try:
            mutation()
        except (CorrectiveCandidateError, build_base.CandidateFinalizationError, release_assurance.AssuranceError):
            passed += 1
        else:
            raise CorrectiveCandidateError(f"mutation was not rejected: {name}")
    return {"status": "PASS", "mutations": len(mutations), "rejected": passed}


def validate_evidence(evidence: Mapping[str, Any], contract: Mapping[str, Any], bindings: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_15A_v0_1_1_corrective_candidate_implementation_evidence_v01":
        raise CorrectiveCandidateError("unexpected evidence schema")
    if evidence.get("task_id") != contract["task_id"] or evidence.get("profile") != "CHANGE":
        raise CorrectiveCandidateError("evidence task or profile mismatch")
    expected_manifest = dict(bindings["manifest"]); expected_manifest["status"] = "PASS"
    if evidence.get("successor_manifest") != expected_manifest:
        raise CorrectiveCandidateError("evidence manifest binding mismatch")
    assets = evidence.get("candidate_assets")
    if not isinstance(assets, Mapping) or sorted(assets) != sorted(contract["candidate_asset_contract"]["required_assets"]):
        raise CorrectiveCandidateError("candidate asset evidence set mismatch")
    for filename, row in assets.items():
        if not isinstance(row, Mapping) or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            raise CorrectiveCandidateError(f"candidate asset digest missing: {filename}")
        if not isinstance(row.get("size_bytes"), int) or row["size_bytes"] <= 0:
            raise CorrectiveCandidateError(f"candidate asset size invalid: {filename}")
    reconciliation = evidence.get("change_reconciliation")
    if reconciliation != {"planned_paths": 23, "actual_paths": 23, "unplanned_paths": [], "omitted_paths": [], "status": "PASS_exact_planned_path_set"}:
        raise CorrectiveCandidateError("change reconciliation mismatch")
    if any(evidence.get(key) is not False for key in ["release_authorized", "release_performed"]):
        raise CorrectiveCandidateError("external release is overstated")
    if any(evidence.get(key) != 0 for key in ["release_actions_performed", "training_runs", "scientific_artifact_changes"]):
        raise CorrectiveCandidateError("forbidden side effect recorded")
    hosted = evidence.get("hosted_assurance")
    if not isinstance(hosted, Mapping):
        raise CorrectiveCandidateError("hosted assurance evidence missing")
    expected_readiness = (
        "READY_FOR_JOHN_ACCEPTANCE"
        if hosted.get("status") == "PASS"
        else "NOT_READY"
    )
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != expected_readiness:
        raise CorrectiveCandidateError("technical status or hosted-dependent readiness mismatch")
    return {"status": "PASS", "version": VERSION, "candidate_assets": 3, "release_actions_performed": 0}


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": validate_contract_bindings(contract, root)}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": bindings, "evidence": validate_evidence(evidence, contract, bindings)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_15A v0.1.1 corrective-candidate assurance")
    parser.add_argument("command", choices=("metadata", "contract", "mutations", "build-candidate", "write-manifest", "final-evidence"))
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        contract = _load_json(CONTRACT_PATH)
        if args.command == "metadata":
            result = {"status": "PASS", "metadata": validate_metadata(contract=contract)}
        elif args.command == "contract":
            result = validate_contract()
        elif args.command == "mutations":
            result = run_mutations(contract)
        elif args.command == "build-candidate":
            if args.output_dir is None:
                raise CorrectiveCandidateError("--output-dir is required for build-candidate")
            result = build_candidate(args.output_dir)
        elif args.command == "write-manifest":
            result = write_manifest()
        else:
            result = validate_final_evidence()
    except (
        CorrectiveCandidateError, build_base.CandidateFinalizationError,
        release_assurance.AssuranceError, csv.Error, json.JSONDecodeError,
        OSError, KeyError, TypeError, ValueError,
    ) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
