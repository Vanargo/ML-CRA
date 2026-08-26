from __future__ import annotations

import argparse
import copy
import csv
import email
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_14A_release_0_1_0_candidate_finalization_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_14A_release_candidate_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_14A_release_0_1_0_candidate_finalization_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_14A_release_0_1_0_candidate_finalization_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
CITATION_PATH = PROJECT_ROOT / "CITATION.cff"
APPLICATION_PATH = PROJECT_ROOT / "src/mlcra/application.py"
RELEASE_NOTES_PATH = PROJECT_ROOT / "RELEASE_NOTES_0.1.0.md"
VERSION = "0.1.0"


class CandidateFinalizationError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidateFinalizationError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise CandidateFinalizationError(f"CSV is empty or lacks rows: {path}")
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
        raise CandidateFinalizationError(f"{label} must occur exactly once: {duplicates}")
    return values


def _load_yaml_base(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - explicit prerequisite
        raise CandidateFinalizationError("PyYAML from the assurance lock is required") from error
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, dict):
        raise CandidateFinalizationError(f"YAML root must be a mapping: {path}")
    return value


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
        raise CandidateFinalizationError(
            f"tracked candidate tree contains policy-excluded paths: {forbidden}"
        )
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise CandidateFinalizationError(
            f"candidate manifest cycle-breaking path is not tracked: {missing}"
        )
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
    path.parent.mkdir(parents=True, exist_ok=True)
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
        raise CandidateFinalizationError("candidate manifest schema mismatch")
    row_paths = _unique((str(row.get("relative_path", "")) for row in rows), "manifest path")
    if row_paths != sorted(row_paths):
        raise CandidateFinalizationError("candidate manifest paths are not ordinally sorted")
    tracked = _tracked_candidate_paths(root, contract)
    exclusions = sorted(contract["successor_manifest"]["cycle_breaking_exclusions"])
    expected_rows = sorted(set(tracked) - set(exclusions))
    if row_paths != expected_rows:
        missing = sorted(set(expected_rows) - set(row_paths))
        extra = sorted(set(row_paths) - set(expected_rows))
        raise CandidateFinalizationError(
            f"candidate manifest path set mismatch: missing={missing} extra={extra}"
        )
    for row in rows:
        relative = row["relative_path"]
        payload = release_assurance.git_index_blob_bytes(relative, root)
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise CandidateFinalizationError(f"invalid SHA-256 syntax: {relative}")
        if row["sha256"] != _sha256_bytes(payload) or row.get("size_bytes") != str(len(payload)):
            raise CandidateFinalizationError(f"candidate-tree byte binding mismatch: {relative}")
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


def _assert_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise CandidateFinalizationError("authority object missing")
    if authority.get("authorized_task_label") != (
        "NEXT_BLOCK_AUTHORIZED: ST08_14A_release_0_1_0_candidate_finalization"
    ):
        raise CandidateFinalizationError("John task authority is missing")
    if authority.get("candidate_finalization_authorized") is not True:
        raise CandidateFinalizationError("candidate-finalization authority missing")
    allowed = {"package_version_0_1_0_authorized", "candidate_asset_build_authorized"}
    for key, value in authority.items():
        if key in {"authorized_task_label", "candidate_finalization_authorized"}:
            continue
        if key in allowed:
            if value is not True:
                raise CandidateFinalizationError(f"authorized operation disabled: {key}")
        elif key.endswith("_authorized") and value is not False:
            raise CandidateFinalizationError(f"future or external authority overstated: {key}")


def _parse_cff(path: Path) -> dict[str, Any]:
    return _load_yaml_base(path)


def validate_metadata(
    root: Path = PROJECT_ROOT,
    contract: Mapping[str, Any] | None = None,
    *,
    citation: Mapping[str, Any] | None = None,
    readme_text: str | None = None,
    readme_ru_text: str | None = None,
    release_notes_text: str | None = None,
) -> dict[str, Any]:
    contract = contract or _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    _assert_authority(contract)
    with (root / PYPROJECT_PATH.relative_to(PROJECT_ROOT)).open("rb") as stream:
        pyproject = tomllib.load(stream)
    project = pyproject.get("project", {})
    if project.get("version") != VERSION:
        raise CandidateFinalizationError("pyproject version must be 0.1.0")
    classifiers = project.get("classifiers", [])
    if "Development Status :: 3 - Alpha" not in classifiers or any(
        str(value).startswith("Development Status :: 2") for value in classifiers
    ):
        raise CandidateFinalizationError("development classifier must be Alpha only")
    application = (root / APPLICATION_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    if 'PROJECT_VERSION = "0.1.0"' not in application or "DEVELOPMENT_VERSION" in application:
        raise CandidateFinalizationError("runtime version contract mismatch")
    if "0.1.0.dev0" in application:
        raise CandidateFinalizationError("runtime retains the development version")

    citation = citation or _parse_cff(root / CITATION_PATH.relative_to(PROJECT_ROOT))
    if citation.get("cff-version") != "1.2.0" or citation.get("version") != VERSION:
        raise CandidateFinalizationError("CITATION.cff version relation mismatch")
    if "date-released" in citation or "commit" in citation:
        raise CandidateFinalizationError("CITATION.cff prematurely claims an external release")

    readme_text = readme_text if readme_text is not None else (
        root / "README.md"
    ).read_text(encoding="utf-8")
    readme_ru_text = readme_ru_text if readme_ru_text is not None else (
        root / "README_RU.md"
    ).read_text(encoding="utf-8")
    for label, text in [("README.md", readme_text), ("README_RU.md", readme_ru_text)]:
        if VERSION not in text or "RELEASE_NOTES_0.1.0.md" not in text:
            raise CandidateFinalizationError(f"candidate status or release-notes link missing: {label}")
        if "0.1.0.dev0" in text:
            raise CandidateFinalizationError(f"development version remains in current status: {label}")
    forbidden_release_claims = ["has been released", "опубликован релиз", "PyPI package is available"]
    if any(token.casefold() in (readme_text + readme_ru_text).casefold() for token in forbidden_release_claims):
        raise CandidateFinalizationError("README prematurely claims an external release")

    notes = release_notes_text if release_notes_text is not None else (
        root / RELEASE_NOTES_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_note_tokens = [
        "## English", "## Русский", "does not create tag", "не создаёт тег",
        "MiniBooNE", "UCI Wine Quality", "SHA256SUMS", "SOURCE_DATE_EPOCH",
        "ml_cra-0.1.0.tar.gz", "ml_cra-0.1.0-py3-none-any.whl",
        "Windows x64", "CPython `>=3.12,<3.13`", "GitHub Release", "PyPI",
    ]
    missing = [token for token in required_note_tokens if token not in notes]
    if missing:
        raise CandidateFinalizationError(f"release notes omit required boundary: {missing}")
    hash_commands = re.findall(r"Get-FileHash[^\r\n]+", notes)
    if len(hash_commands) != 2 or hash_commands[0] != hash_commands[1]:
        raise CandidateFinalizationError("bilingual SHA-256 verification commands differ")
    return {
        "version": VERSION,
        "classifier": "Development Status :: 3 - Alpha",
        "cff_version": citation["version"],
        "release_date_recorded": False,
        "release_notes_languages": 2,
        "external_release_claimed": False,
    }


def _validate_tar_member(member: tarfile.TarInfo) -> None:
    release_assurance._validate_archive_path(member.name)
    path = PurePosixPath(member.name)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise CandidateFinalizationError(f"unsafe sdist member path: {member.name}")
    if not (member.isfile() or member.isdir()):
        raise CandidateFinalizationError(f"non-regular sdist member forbidden: {member.name}")


def normalize_sdist(source: Path, destination: Path, epoch: int) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(source, "r:gz") as source_archive:
        source_members = source_archive.getmembers()
        for member in source_members:
            _validate_tar_member(member)
        if len({member.name for member in source_members}) != len(source_members):
            raise CandidateFinalizationError("duplicate sdist member path")
        members: list[tuple[tarfile.TarInfo, bytes | None]] = []
        for member in source_members:
            payload = None
            if member.isfile():
                stream = source_archive.extractfile(member)
                if stream is None:
                    raise CandidateFinalizationError(f"cannot read sdist member: {member.name}")
                payload = stream.read()
                if len(payload) != member.size:
                    raise CandidateFinalizationError(f"sdist member size mismatch: {member.name}")
            normalized = copy.copy(member)
            normalized.mtime = epoch
            normalized.uid = 0
            normalized.gid = 0
            normalized.uname = ""
            normalized.gname = ""
            normalized.pax_headers = {}
            members.append((normalized, payload))
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as output:
                for member, payload in sorted(members, key=lambda row: row[0].name):
                    output.addfile(member, io.BytesIO(payload) if payload is not None else None)
    return {
        "filename": destination.name,
        "sha256": _sha256_file(destination),
        "members": len(members),
    }


def _checkout_index(destination: Path, root: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    prefix = destination.resolve().as_posix().rstrip("/") + "/"
    process = subprocess.run(
        ["git", "-C", str(root), "checkout-index", "--all", f"--prefix={prefix}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise CandidateFinalizationError(f"cannot materialize canonical Git index: {process.stderr.strip()}")


def _run_build(source: Path, output: Path, epoch: int, root: Path) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(epoch)
    process = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(output), str(source)],
        cwd=root,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise CandidateFinalizationError(
            f"candidate build failed: exit={process.returncode} stdout={process.stdout[-2000:]} stderr={process.stderr[-2000:]}"
        )
    sdists = list(output.glob("*.tar.gz"))
    wheels = list(output.glob("*.whl"))
    if len(sdists) != 1 or len(wheels) != 1:
        raise CandidateFinalizationError("build must produce exactly one sdist and one wheel")
    return sdists[0], wheels[0]


def _metadata_message(payload: bytes) -> email.message.Message:
    return email.message_from_bytes(payload)


def validate_candidate_assets(sdist: Path, wheel: Path, checksum_file: Path) -> dict[str, Any]:
    if sdist.name != "ml_cra-0.1.0.tar.gz" or wheel.name != "ml_cra-0.1.0-py3-none-any.whl":
        raise CandidateFinalizationError("candidate asset filename mismatch")
    archive_result = release_assurance.verify_archives(sdist, wheel)
    with tarfile.open(sdist, "r:gz") as archive:
        names = [member.name for member in archive.getmembers() if member.isfile()]
        pkg_name = next((name for name in names if name.endswith("/PKG-INFO")), None)
        if pkg_name is None:
            raise CandidateFinalizationError("sdist PKG-INFO missing")
        stream = archive.extractfile(pkg_name)
        if stream is None:
            raise CandidateFinalizationError("sdist PKG-INFO unreadable")
        sdist_metadata = _metadata_message(stream.read())
        root = PurePosixPath(pkg_name).parts[0]
        if root != "ml_cra-0.1.0" or sdist_metadata.get("Version") != VERSION:
            raise CandidateFinalizationError("sdist root or metadata version mismatch")
        if not any(name.endswith("/LICENSE") for name in names):
            raise CandidateFinalizationError("sdist LICENSE missing")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        entry_name = next((name for name in names if name.endswith(".dist-info/entry_points.txt")), None)
        if metadata_name is None or entry_name is None:
            raise CandidateFinalizationError("wheel metadata or entry point missing")
        if PurePosixPath(metadata_name).parts[0] != "ml_cra-0.1.0.dist-info":
            raise CandidateFinalizationError("wheel dist-info version mismatch")
        wheel_metadata = _metadata_message(archive.read(metadata_name))
        if wheel_metadata.get("Version") != VERSION:
            raise CandidateFinalizationError("wheel Core Metadata version mismatch")
        if "Development Status :: 3 - Alpha" not in wheel_metadata.get_all("Classifier", []):
            raise CandidateFinalizationError("wheel Alpha classifier missing")
        if "mlcra = mlcra.cli:main" not in archive.read(entry_name).decode("utf-8"):
            raise CandidateFinalizationError("wheel console entry point mismatch")
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
            raise CandidateFinalizationError("wheel LICENSE missing")
    expected_lines = [
        f"{_sha256_file(sdist)}  {sdist.name}",
        f"{_sha256_file(wheel)}  {wheel.name}",
    ]
    observed = checksum_file.read_text(encoding="ascii").splitlines()
    if observed != sorted(expected_lines):
        raise CandidateFinalizationError("SHA256SUMS does not exactly bind both assets")
    return {
        "sdist": archive_result["sdist"],
        "wheel": archive_result["wheel"],
        "checksums": len(observed),
        "metadata_version": VERSION,
    }


def build_candidate(output_dir: Path, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    validate_metadata(root, contract)
    output_dir = output_dir.resolve()
    permitted = (root / "dist").resolve()
    if output_dir == permitted or permitted not in output_dir.parents:
        raise CandidateFinalizationError("candidate output must be a dedicated subdirectory of dist/")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise CandidateFinalizationError("candidate output directory must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    epoch = int(contract["candidate_asset_contract"]["source_date_epoch"])
    build_rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="st08_14A_build_") as temporary:
        temporary_root = Path(temporary)
        for index in (1, 2):
            source = temporary_root / f"source_{index}"
            raw_output = temporary_root / f"raw_{index}"
            normalized = temporary_root / f"normalized_{index}.tar.gz"
            _checkout_index(source, root)
            sdist, wheel = _run_build(source, raw_output, epoch, root)
            normalized_result = normalize_sdist(sdist, normalized, epoch)
            build_rows.append(
                {
                    "index": index,
                    "normalized_sdist": normalized,
                    "normalized_sdist_sha256": normalized_result["sha256"],
                    "wheel": wheel,
                    "wheel_sha256": _sha256_file(wheel),
                }
            )
        if len({row["normalized_sdist_sha256"] for row in build_rows}) != 1:
            raise CandidateFinalizationError("normalized sdist builds are not byte-reproducible")
        if len({row["wheel_sha256"] for row in build_rows}) != 1:
            raise CandidateFinalizationError("wheel builds are not byte-reproducible")
        final_sdist = output_dir / "ml_cra-0.1.0.tar.gz"
        final_wheel = output_dir / "ml_cra-0.1.0-py3-none-any.whl"
        shutil.copyfile(build_rows[0]["normalized_sdist"], final_sdist)
        shutil.copyfile(build_rows[0]["wheel"], final_wheel)
    checksums = output_dir / "SHA256SUMS"
    checksum_lines = sorted(
        [
            f"{_sha256_file(final_sdist)}  {final_sdist.name}",
            f"{_sha256_file(final_wheel)}  {final_wheel.name}",
        ]
    )
    checksums.write_text("\n".join(checksum_lines) + "\n", encoding="ascii", newline="\n")
    assets = validate_candidate_assets(final_sdist, final_wheel, checksums)
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
            for path in [final_sdist, final_wheel, checksums]
        },
        "archive_assurance": assets,
        "release_actions_performed": 0,
    }


def _load_scope(path: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(path)
    if fields != ["change_kind", "relative_path", "reason"]:
        raise CandidateFinalizationError("unexpected ST08_14A change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_contract_bindings(
    contract: Mapping[str, Any],
    root: Path = PROJECT_ROOT,
    workflow_text: str | None = None,
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_14A_release_0_1_0_candidate_finalization":
        raise CandidateFinalizationError("unexpected task identifier")
    if contract.get("profile") != "CHANGE":
        raise CandidateFinalizationError("profile must be CHANGE")
    metadata = validate_metadata(root, contract)
    for item in contract.get("immutable_ST08_14", []):
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise CandidateFinalizationError(f"immutable ST08_14 artifact changed: {item['path']}")
    if len(contract.get("immutable_ST08_14", [])) != 6:
        raise CandidateFinalizationError("immutable ST08_14 set must contain six artifacts")
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    manifest = validate_manifest(fields, rows, root, contract)
    protected = release_assurance.validate_protected_hashes(root, inventory="published")
    expected_scope = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    observed_scope = _load_scope(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise CandidateFinalizationError("actual change scope differs from planned changes")
    workflow_text = workflow_text if workflow_text is not None else (
        root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_workflow = [
        "SOURCE_DATE_EPOCH: \"1787616000\"",
        "scripts/st08_14A_release_candidate_finalization_assurance.py metadata",
        "tests.test_release_candidate_finalization_st08_14A",
        "scripts/st08_14A_release_candidate_finalization_assurance.py build-candidate",
        "scripts/st08_09_release_assurance.py source --inventory published",
    ]
    missing = [token for token in required_workflow if token not in workflow_text]
    if missing:
        raise CandidateFinalizationError(f"workflow omits ST08_14A control: {missing}")
    forbidden_workflow = [
        "gh release create", "pypa/gh-action-pypi-publish", "id-token: write",
        "contents: write", "attestations: write", "actions/upload-artifact",
    ]
    if any(token in workflow_text for token in forbidden_workflow):
        raise CandidateFinalizationError("assurance workflow gained publication authority")
    for relative in [ROADMAP_PATH, STAGE_PATH]:
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [
            contract["task_id"], "ST08_14_release_0_1_0_scope_channel_and_execution_contract_design",
            "ST08_14B_release_0_1_0_execution_security_preflight", "release_authorized: false",
        ]:
            if token not in text:
                raise CandidateFinalizationError(f"canonical task registration missing: {relative}/{token}")
    sources = contract.get("authoritative_support")
    if not isinstance(sources, list) or len(sources) != 8:
        raise CandidateFinalizationError("authoritative source set mismatch")
    return {
        "metadata": metadata,
        "manifest": manifest,
        "protected": protected,
        "immutable_ST08_14": 6,
        "change_scope": len(observed_scope),
        "release_actions_performed": 0,
    }


def validate_evidence_relations(
    evidence: Mapping[str, Any],
    contract: Mapping[str, Any],
    bindings: Mapping[str, Any],
) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_14A_release_0_1_0_candidate_finalization_evidence_v01":
        raise CandidateFinalizationError("unexpected evidence schema")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "CHANGE":
        raise CandidateFinalizationError("evidence task/profile mismatch")
    if evidence.get("status") != "candidate_finalized_local_external_release_not_authorized":
        raise CandidateFinalizationError("evidence status is not final")
    baseline = evidence.get("source_baseline")
    if not isinstance(baseline, Mapping) or (
        baseline.get("git_commit") != contract["source_baseline"]["git_commit"]
        or baseline.get("project_version_before") != "0.1.0.dev0"
        or baseline.get("project_version_after") != VERSION
    ):
        raise CandidateFinalizationError("source baseline evidence mismatch")
    expected_manifest = dict(bindings["manifest"])
    expected_manifest["status"] = "PASS"
    if evidence.get("successor_manifest") != expected_manifest:
        raise CandidateFinalizationError("evidence successor-manifest binding mismatch")
    assets = evidence.get("candidate_assets")
    required_assets = contract["candidate_asset_contract"]["required_assets"]
    if not isinstance(assets, Mapping) or sorted(assets) != sorted(required_assets):
        raise CandidateFinalizationError("candidate asset evidence set mismatch")
    for filename, row in assets.items():
        if not isinstance(row, Mapping) or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))):
            raise CandidateFinalizationError(f"candidate asset digest missing: {filename}")
        if not isinstance(row.get("size_bytes"), int) or row["size_bytes"] <= 0:
            raise CandidateFinalizationError(f"candidate asset size invalid: {filename}")
    expected_checks = {
        "metadata_assurance": "PASS",
        "candidate_builds": "PASS_2_of_2",
        "normalized_sdist_byte_reproducibility": "PASS_2_of_2",
        "wheel_byte_reproducibility": "PASS_2_of_2",
        "archive_assurance": "PASS",
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
        raise CandidateFinalizationError("observed check record is incomplete or overstated")
    if evidence.get("change_reconciliation") != {
        "planned_paths": 21,
        "actual_paths": 21,
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise CandidateFinalizationError("change reconciliation mismatch")
    if any(evidence.get(key) is not False for key in ["release_authorized", "release_performed"]):
        raise CandidateFinalizationError("external release is overstated")
    if any(evidence.get(key) != 0 for key in ["release_actions_performed", "training_runs", "scientific_artifact_changes"]):
        raise CandidateFinalizationError("forbidden side effect recorded")
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise CandidateFinalizationError("technical status/readiness mismatch")
    return {
        "status": "PASS",
        "version": VERSION,
        "candidate_assets": len(assets),
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
    parser = argparse.ArgumentParser(description="ST08_14A release-candidate finalization assurance")
    parser.add_argument(
        "command", choices=("metadata", "build-candidate", "write-manifest", "contract", "final-evidence")
    )
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "metadata":
            result = {"status": "PASS", "metadata": validate_metadata()}
        elif args.command == "build-candidate":
            if args.output_dir is None:
                raise CandidateFinalizationError("--output-dir is required for build-candidate")
            result = build_candidate(args.output_dir)
        elif args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "contract":
            result = validate_contract()
        else:
            result = validate_final_evidence()
    except (
        CandidateFinalizationError, release_assurance.AssuranceError, csv.Error,
        json.JSONDecodeError, OSError, KeyError, TypeError, ValueError,
    ) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
