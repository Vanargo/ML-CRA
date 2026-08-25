from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PROJECT_ROOT / "configs/project_readiness/st08_09_CI_security_and_release_candidate_assurance_contract_v01.json"
PUBLIC_MANIFEST = PROJECT_ROOT / "configs/project_readiness/st08_06_public_repository_asset_manifest_v01.json"
PROTECTED_SOURCE = PROJECT_ROOT / "data_registry/st08_04_public_product_scope_and_release_train_contract_design_evidence_v01.json"
RUNTIME_LOCK = PROJECT_ROOT / "requirements/locks/st08_07-py312-windows-x86_64.txt"
TOOLS_LOCK = PROJECT_ROOT / "requirements/locks/st08_09-assurance-tools-py312-windows-x86_64.txt"
WORKFLOW = PROJECT_ROOT / ".github/workflows/ci.yml"
PUBLICATION_TREE_MANIFEST = PROJECT_ROOT / "data_registry/st08_14_release_0_1_0_contract_manifest_v01.csv"
PUBLICATION_EVIDENCE = PROJECT_ROOT / "data_registry/st08_14_release_0_1_0_scope_channel_and_execution_contract_design_evidence_v01.json"
PUBLICATION_CONTRACT = PROJECT_ROOT / "configs/project_readiness/st08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_contract_v01.json"


class AssuranceError(RuntimeError):
    pass


def default_inventory(inventory: str | None = None) -> str:
    selected = inventory or os.environ.get("MLCRA_ASSURANCE_INVENTORY", "working")
    if selected not in {"working", "published"}:
        raise AssuranceError(f"unsupported assurance inventory: {selected}")
    return selected


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssuranceError(f"JSON root must be an object: {path}")
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


def validate_lock(path: Path, expected_count: int) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if "--require-hashes" not in text or "--only-binary=:all:" not in text:
        raise AssuranceError(f"lock options missing: {path}")
    if re.search(r"(?m)^\s*(?:-e|--editable|https?://)", text):
        raise AssuranceError(f"editable or URL requirement forbidden: {path}")
    requirements = re.findall(r"(?m)^([A-Za-z0-9_.-]+)==([^\s\\]+)\s*\\\s*$", text)
    hashes = re.findall(r"(?m)^\s*--hash=sha256:([0-9a-f]{64})\s*$", text)
    if len(requirements) != expected_count or len(hashes) != expected_count:
        raise AssuranceError(
            f"lock count mismatch for {path}: requirements={len(requirements)} hashes={len(hashes)} expected={expected_count}"
        )
    normalized = [name.lower().replace("_", "-") for name, _ in requirements]
    if len(normalized) != len(set(normalized)):
        raise AssuranceError(f"duplicate normalized requirement in {path}")
    return {"path": path.relative_to(PROJECT_ROOT).as_posix(), "requirements": len(requirements), "hashes": len(hashes)}


def _infrastructure_excluded(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    if not parts:
        return True
    if parts[0] in {".git", "ml-cra-venv", ".venv", "venv", "build", "dist"}:
        return True
    if any(part == "__pycache__" or part.endswith(".egg-info") for part in parts):
        return True
    if any(part.startswith(".tmp_st08_09") for part in parts):
        return True
    return relative.endswith((".pyc", ".pyo"))


def repository_paths(root: Path = PROJECT_ROOT) -> list[str]:
    paths: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if not _infrastructure_excluded(relative):
            paths.append(relative)
    return sorted(paths)


def tracked_repository_paths(root: Path = PROJECT_ROOT) -> list[str]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise AssuranceError(f"Git tracked-path inventory unavailable: {process.stderr.decode('utf-8', errors='replace').strip()}")
    paths = [value.decode("utf-8") for value in process.stdout.split(b"\0") if value]
    if not paths or paths != sorted(paths) or len(paths) != len(set(paths)):
        raise AssuranceError("Git tracked-path inventory must be nonempty, unique and ordinally sorted")
    return paths


def git_index_blob_bytes(relative_path: str, root: Path = PROJECT_ROOT) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(root), "show", f":{relative_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise AssuranceError(
            f"cannot read Git index blob for {relative_path}: {detail}"
        )
    return process.stdout


def _contains_miniboone_reference(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return re.search(r"(?i)miniboone|41150", text) is not None


def classify_public_path(relative: str, manifest: dict[str, Any], root: Path = PROJECT_ROOT) -> str:
    rules = {row["rule_id"]: row for row in manifest["rules"]}
    if relative in rules["ST08-06-MANIFEST-01"]["selectors"]:
        return "ST08-06-MANIFEST-01"
    if relative in rules["ST08-06-MANIFEST-02"]["selectors"]:
        return "ST08-06-MANIFEST-02"
    if relative in rules["ST08-06-MANIFEST-03"]["selectors"]:
        return "ST08-06-MANIFEST-03"
    if relative.startswith("docs/archive/"):
        return "ST08-06-MANIFEST-04"
    lowered = relative.lower()
    if any(fragment.lower() in lowered for fragment in rules["ST08-06-MANIFEST-05"]["selectors"]):
        return "ST08-06-MANIFEST-05"
    if _contains_miniboone_reference(root / relative):
        return "ST08-06-MANIFEST-06"
    return "ST08-06-MANIFEST-07"


def validate_public_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    manifest = _load_json(root / PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    paths = repository_paths(root)
    universe = manifest["inventory_universe"]
    expected_count = int(universe["approved_path_count"])
    expected_digest = universe["approved_path_list_sha256"]
    observed_digest = _path_list_sha256(paths)
    if len(paths) != expected_count or observed_digest != expected_digest:
        raise AssuranceError(
            f"public manifest path set mismatch: count={len(paths)}/{expected_count} digest={observed_digest}/{expected_digest}"
        )
    counts = {f"ST08-06-MANIFEST-{index:02d}": 0 for index in range(1, 8)}
    for relative in paths:
        counts[classify_public_path(relative, manifest, root)] += 1
    recorded = manifest["validated_inventory_counts"]
    for rule, count in counts.items():
        if int(recorded[rule]) != count:
            raise AssuranceError(f"public manifest rule count mismatch: {rule}={count}/{recorded[rule]}")
    if int(recorded["BLOCK_UNMAPPED"]) != 0 or int(recorded["TOTAL"]) != len(paths):
        raise AssuranceError("public manifest must have zero unmapped paths and exact total")
    included = [path for path in paths if classify_public_path(path, manifest, root) in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}]
    return {"paths": len(paths), "path_list_sha256": observed_digest, "counts": counts, "included_paths": included}


def validate_publication_tree(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    manifest_path = root / PUBLICATION_TREE_MANIFEST.relative_to(PROJECT_ROOT)
    evidence_path = root / PUBLICATION_EVIDENCE.relative_to(PROJECT_ROOT)
    with manifest_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    expected_fields = ["relative_path", "sha256", "size_bytes"]
    if fields != expected_fields or not rows:
        raise AssuranceError("publication-tree manifest is empty or has an unexpected schema")
    row_paths = [row["relative_path"] for row in rows]
    if row_paths != sorted(row_paths) or len(row_paths) != len(set(row_paths)):
        raise AssuranceError("publication-tree manifest paths must be nonempty, unique and ordinally sorted")
    cycle_exclusions = sorted([
        PUBLICATION_TREE_MANIFEST.relative_to(PROJECT_ROOT).as_posix(),
        PUBLICATION_EVIDENCE.relative_to(PROJECT_ROOT).as_posix(),
    ])
    observed_paths = tracked_repository_paths(root)
    expected_paths = sorted(row_paths + cycle_exclusions)
    if observed_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(observed_paths))
        extra = sorted(set(observed_paths) - set(expected_paths))
        raise AssuranceError(f"published Git tree mismatch: missing={missing} extra={extra}")
    public_manifest = _load_json(root / PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    forbidden = []
    for relative in observed_paths:
        rule = classify_public_path(relative, public_manifest, root)
        if rule not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}:
            forbidden.append({"path": relative, "rule": rule})
    if forbidden:
        raise AssuranceError(f"published Git tree contains excluded paths: {forbidden}")
    for row in rows:
        path = root / row["relative_path"]
        payload = git_index_blob_bytes(row["relative_path"], root)
        if (
            not path.is_file()
            or hashlib.sha256(payload).hexdigest() != row["sha256"]
            or str(len(payload)) != row["size_bytes"]
        ):
            raise AssuranceError(f"publication-tree byte binding mismatch: {row['relative_path']}")
    if not manifest_path.is_file() or not evidence_path.is_file():
        raise AssuranceError("publication-tree cycle-breaking files are missing")
    return {
        "paths": len(observed_paths),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(observed_paths),
        "manifest_sha256": hashlib.sha256(
            git_index_blob_bytes(
                PUBLICATION_TREE_MANIFEST.relative_to(PROJECT_ROOT).as_posix(),
                root,
            )
        ).hexdigest(),
        "cycle_breaking_exclusions": cycle_exclusions,
        "included_paths": observed_paths,
    }


def _load_yaml_base(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - explicit prerequisite path
        raise AssuranceError("PyYAML from the ST08_09 assurance lock is required") from error
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(value, dict):
        raise AssuranceError(f"YAML root must be a mapping: {path}")
    return value


def validate_workflow(path: Path = WORKFLOW, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or _load_json(DEFAULT_CONTRACT)
    workflow = _load_yaml_base(path)
    triggers = workflow.get("on")
    if not isinstance(triggers, dict):
        raise AssuranceError("workflow triggers must be an explicit mapping")
    if set(triggers) != {"push", "pull_request", "workflow_dispatch"}:
        raise AssuranceError(f"workflow trigger mismatch: {sorted(triggers)}")
    if any(event in triggers for event in contract["ci_contract"]["forbidden_events"]):
        raise AssuranceError("privileged workflow trigger is forbidden")
    if workflow.get("permissions") != {"contents": "read"}:
        raise AssuranceError(f"workflow permissions are not least privilege: {workflow.get('permissions')}")
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict) or set(jobs) != {"assurance"}:
        raise AssuranceError("workflow must contain exactly the assurance job")
    job = jobs["assurance"]
    if job.get("runs-on") != contract["ci_contract"]["runner"]:
        raise AssuranceError("workflow runner is not the fixed declared label")
    if not job.get("timeout-minutes"):
        raise AssuranceError("workflow job timeout is required")
    if job.get("env") != {"MLCRA_ASSURANCE_INVENTORY": "published"}:
        raise AssuranceError("workflow must declare the published assurance inventory")
    steps = job.get("steps")
    if not isinstance(steps, list):
        raise AssuranceError("workflow steps missing")
    actions = contract["ci_contract"]["actions"]
    expected_uses = {f"{row['repository']}@{row['commit_sha']}" for row in actions}
    observed_uses = {step["uses"] for step in steps if isinstance(step, dict) and "uses" in step}
    if observed_uses != expected_uses:
        raise AssuranceError(f"workflow actions must match immutable allowlist: {observed_uses}")
    checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
    if checkout.get("with", {}).get("persist-credentials") != "false":
        raise AssuranceError("checkout credentials must not persist")
    setup = next(step for step in steps if step.get("uses", "").startswith("actions/setup-python@"))
    if setup.get("with", {}).get("python-version") != contract["ci_contract"]["python"]:
        raise AssuranceError("workflow Python patch must match the declared cell")
    if setup.get("with", {}).get("architecture") != contract["ci_contract"]["architecture"]:
        raise AssuranceError("workflow Python architecture mismatch")
    raw = path.read_text(encoding="utf-8")
    forbidden = ["pull_request_target", "workflow_run:", "${{ secrets.", "actions/upload-artifact"]
    if any(token in raw for token in forbidden):
        raise AssuranceError("workflow contains a forbidden privileged, secret or artifact-upload construct")
    required_commands = [
        "python -m pip install --require-hashes --only-binary=:all: -r requirements/locks/st08_09-assurance-tools-py312-windows-x86_64.txt",
        "python -m pip install --require-hashes --only-binary=:all: -r requirements/locks/st08_07-py312-windows-x86_64.txt",
        "python -m pip install --no-deps --no-build-isolation .",
        "st08_09_release_assurance.py source --inventory published",
        "st08_09_release_assurance.py secrets --inventory published",
        "st08_09_release_assurance.py dependencies",
        "python -m build --no-isolation",
        "st08_09_release_assurance.py archives",
        "pip install --no-index --find-links",
        "pip check",
        "mlcra.exe doctor --format json",
        "tests.test_cli_st08_08",
        "tests.test_release_assurance_st08_09",
        "st08_14_release_0_1_0_contract_assurance.py contract",
        "tests.test_release_0_1_0_contract_st08_14",
        "scripts/agent_verify.py --mode baseline --inventory published",
    ]
    missing = [command for command in required_commands if command not in raw]
    if missing:
        raise AssuranceError(f"workflow required commands missing: {missing}")
    native_exit_guard = "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"
    guarded_native_commands = 0
    for step in steps:
        run = step.get("run") if isinstance(step, dict) else None
        if not isinstance(run, str) or "\n" not in run:
            continue
        lines = [line.strip() for line in run.splitlines() if line.strip()]
        command_indexes = [
            index
            for index, line in enumerate(lines)
            if line.startswith("python ") or re.match(r"^\.tmp[^ ]*\\Scripts\\(?:python|mlcra)\.exe ", line)
        ]
        for position, command_index in enumerate(command_indexes):
            next_index = command_indexes[position + 1] if position + 1 < len(command_indexes) else len(lines)
            if native_exit_guard not in lines[command_index + 1 : next_index]:
                raise AssuranceError(
                    f"native command in multi-command PowerShell step lacks an immediate failure guard: {lines[command_index]}"
                )
            guarded_native_commands += 1
    if guarded_native_commands < 7:
        raise AssuranceError("workflow must contain the declared guarded native-command surface")
    return {"events": sorted(triggers), "actions": sorted(observed_uses), "runner": job["runs-on"]}


def validate_protected_hashes(
    root: Path = PROJECT_ROOT,
    inventory: str = "working",
    canonical_bindings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _load_json(root / PROTECTED_SOURCE.relative_to(PROJECT_ROOT))
    protected = source["protected_artifacts"]
    if inventory == "published":
        if canonical_bindings is None:
            publication_contract = _load_json(
                root / PUBLICATION_CONTRACT.relative_to(PROJECT_ROOT)
            )
            canonical_bindings = publication_contract[
                "protected_git_blob_bindings"
            ]
        binding_paths = [row.get("path") for row in canonical_bindings]
        if (
            binding_paths != list(protected)
            or len(binding_paths) != len(set(binding_paths))
        ):
            raise AssuranceError(
                "published protected-artifact bindings must exactly preserve "
                "the historical protected path order"
            )
        mismatches = []
        for row in canonical_bindings:
            relative = row["path"]
            payload = git_index_blob_bytes(relative, root)
            actual = hashlib.sha256(payload).hexdigest()
            if (
                row.get("legacy_worktree_sha256") != protected[relative]
                or row.get("canonical_git_blob_sha256") != actual
                or row.get("canonical_size_bytes") != len(payload)
                or row.get("relation")
                != "legacy_worktree_CRLF_normalized_to_LF_equals_git_blob"
            ):
                mismatches.append(
                    {
                        "path": relative,
                        "expected_git_blob": row.get(
                            "canonical_git_blob_sha256"
                        ),
                        "actual_git_blob": actual,
                    }
                )
        if mismatches:
            raise AssuranceError(
                f"published protected Git-blob mismatch: {mismatches}"
            )
        return {
            "expected": len(protected),
            "mismatches": 0,
            "representation": "canonical_git_blob",
        }
    if inventory != "working":
        raise AssuranceError(f"unknown protected-artifact inventory: {inventory}")
    mismatches = []
    for relative, expected in protected.items():
        path = root / relative
        actual = _sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append({"path": relative, "expected": expected, "actual": actual})
    if mismatches:
        raise AssuranceError(f"protected scientific artifact mismatch: {mismatches}")
    return {
        "expected": len(protected),
        "mismatches": 0,
        "representation": "historical_worktree_bytes",
    }


def validate_source(
    root: Path = PROJECT_ROOT,
    contract_path: Path = DEFAULT_CONTRACT,
    inventory: str | None = None,
) -> dict[str, Any]:
    inventory = default_inventory(inventory)
    contract = _load_json(contract_path)
    missing = [relative for relative in contract["source_assurance"]["required_paths"] if not (root / relative).is_file()]
    if missing:
        raise AssuranceError(f"required source paths missing: {missing}")
    runtime = validate_lock(root / RUNTIME_LOCK.relative_to(PROJECT_ROOT), 15)
    tools = validate_lock(root / TOOLS_LOCK.relative_to(PROJECT_ROOT), 35)
    workflow = validate_workflow(root / WORKFLOW.relative_to(PROJECT_ROOT), contract)
    manifest = validate_public_manifest(root) if inventory == "working" else validate_publication_tree(root)
    protected = validate_protected_hashes(root, inventory=inventory)
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    for token in ["ml-cra-venv/", "**/__pycache__/", "dist/", ".env", "*.pem", "MiniBooNE_PID.txt"]:
        if token not in gitignore:
            raise AssuranceError(f".gitignore control missing: {token}")
    security = (root / "SECURITY.md").read_text(encoding="utf-8")
    for heading in ["## Поддерживаемое состояние", "## Как сообщить об уязвимости", "## Граница автоматических проверок"]:
        if heading not in security:
            raise AssuranceError(f"SECURITY.md section missing: {heading}")
    codeowners = (root / ".github/CODEOWNERS").read_text(encoding="utf-8")
    if "/.github/ @Vanargo" not in codeowners or "/requirements/locks/ @Vanargo" not in codeowners:
        raise AssuranceError("security-critical CODEOWNERS rules missing")
    dependabot = _load_yaml_base(root / ".github/dependabot.yml")
    ecosystems = [row.get("package-ecosystem") for row in dependabot.get("updates", [])]
    if ecosystems.count("github-actions") != 1 or ecosystems.count("pip") != 2:
        raise AssuranceError("Dependabot must cover Actions, root Python metadata and nested locks")
    return {"status": "PASS", "inventory": inventory, "runtime_lock": runtime, "tools_lock": tools, "workflow": workflow, "manifest": {k: v for k, v in manifest.items() if k != "included_paths"}, "protected": protected}


def _validate_archive_path(name: str) -> None:
    if "\\" in name:
        raise AssuranceError(f"archive member contains backslash: {name}")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise AssuranceError(f"unsafe archive member path: {name}")
    lowered = f"/{name.lower().lstrip('./')}"
    forbidden_fragments = [
        "/.git/", "/ml-cra-venv/", "/__pycache__/", "/.venv/", "/venv/",
        "/.tmp", "/build/", "/dist/", "/data/raw/", "/openml/org/openml/www/datasets/41150/",
        "/miniboone_pid.txt", "/miniboone.arff", "/dataset_41150.pkl.py3", "/dataset_41150.pq",
    ]
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise AssuranceError(f"forbidden archive member: {name}")
    if lowered.endswith((".pyc", ".pyo", ".pem", ".key", ".p12", ".pfx", "/.env")):
        raise AssuranceError(f"forbidden archive file type: {name}")


def verify_sdist(path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    if not path.name.endswith(contract["archive_assurance"]["required_sdist_suffix"]):
        raise AssuranceError(f"unexpected sdist suffix: {path}")
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members if member.isfile()]
        for member in members:
            _validate_archive_path(member.name)
            if not (member.isfile() or member.isdir()):
                raise AssuranceError(f"non-regular sdist member forbidden: {member.name}")
    roots = {PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts}
    if len(roots) != 1:
        raise AssuranceError(f"sdist must have exactly one root directory: {roots}")
    root = next(iter(roots))
    relative_names = {name[len(root) + 1 :] for name in names if name.startswith(root + "/")}
    missing = [name for name in contract["archive_assurance"]["sdist_must_include"] if name not in relative_names]
    if missing:
        raise AssuranceError(f"sdist required members missing: {missing}")
    return {"filename": path.name, "sha256": _sha256(path), "file_entries": len(names), "root": root}


def verify_wheel(path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    if not path.name.endswith(contract["archive_assurance"]["required_wheel_suffix"]):
        raise AssuranceError(f"unexpected wheel suffix: {path}")
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        for name in names:
            _validate_archive_path(name)
        missing = [suffix for suffix in contract["archive_assurance"]["wheel_must_include_suffixes"] if not any(name.endswith(suffix) for name in names)]
        if missing:
            raise AssuranceError(f"wheel required members missing: {missing}")
        entrypoint_name = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        entrypoint = archive.read(entrypoint_name).decode("utf-8")
        if "mlcra = mlcra.cli:main" not in entrypoint:
            raise AssuranceError("wheel console entry point mismatch")
    return {"filename": path.name, "sha256": _sha256(path), "file_entries": len(names)}


def verify_archives(sdist: Path, wheel: Path, contract_path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = _load_json(contract_path)
    if not sdist.is_file() or not wheel.is_file():
        raise AssuranceError("both existing sdist and wheel are required")
    return {"status": "PASS", "sdist": verify_sdist(sdist, contract), "wheel": verify_wheel(wheel, contract)}


def scan_secrets(
    root: Path = PROJECT_ROOT,
    contract_path: Path = DEFAULT_CONTRACT,
    inventory: str = "working",
) -> dict[str, Any]:
    try:
        from detect_secrets import SecretsCollection
        from detect_secrets.settings import transient_settings
    except ImportError as error:  # pragma: no cover - explicit prerequisite path
        raise AssuranceError("detect-secrets from the ST08_09 assurance lock is required") from error
    contract = _load_json(contract_path)
    manifest = validate_public_manifest(root) if inventory == "working" else validate_publication_tree(root)
    plugins = [{"name": name} for name in contract["tooling"]["secret_scan_policy"]["plugins"]]
    findings: list[dict[str, Any]] = []
    with transient_settings({"plugins_used": plugins}):
        secrets = SecretsCollection()
        for relative in manifest["included_paths"]:
            secrets.scan_file(str(root / relative))
        for filename, values in secrets.json().items():
            for value in values:
                findings.append({"path": Path(filename).resolve().relative_to(root.resolve()).as_posix(), "type": value["type"], "line_number": value["line_number"]})
    if findings:
        raise AssuranceError(f"secret scan findings: {findings}")
    return {"status": "PASS", "inventory": inventory, "engine": "detect-secrets==1.5.0", "files_scanned": len(manifest["included_paths"]), "plugins": len(plugins), "findings": 0, "network_verification": False}


def audit_dependencies(lock_paths: list[Path], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for lock_path in lock_paths:
        output = output_dir / f"{lock_path.stem}.json"
        command = [
            sys.executable, "-m", "pip_audit", "--requirement", str(lock_path),
            "--require-hashes", "--disable-pip", "--strict", "--progress-spinner", "off",
            "--format", "json", "--output", str(output),
        ]
        process = subprocess.run(command, cwd=PROJECT_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        payload = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else None
        vulnerability_count = 0
        dependency_count = 0
        if isinstance(payload, dict):
            dependencies = payload.get("dependencies", [])
        elif isinstance(payload, list):
            dependencies = payload
        else:
            dependencies = []
        for dependency in dependencies:
            dependency_count += 1
            vulnerability_count += len(dependency.get("vulns", []))
        if process.returncode != 0 or vulnerability_count:
            raise AssuranceError(
                f"dependency audit failed for {lock_path}: exit={process.returncode} vulnerabilities={vulnerability_count} stderr={process.stderr.strip()}"
            )
        results.append({"lock": lock_path.relative_to(PROJECT_ROOT).as_posix(), "dependencies": dependency_count, "known_vulnerabilities": vulnerability_count, "report": output.as_posix()})
    return {"status": "PASS", "audits": results}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_09 fail-closed release assurance")
    sub = parser.add_subparsers(dest="command", required=True)
    source = sub.add_parser("source")
    source.add_argument(
        "--inventory",
        choices=("working", "published"),
        default=default_inventory(),
    )
    secrets = sub.add_parser("secrets")
    secrets.add_argument("--inventory", choices=("working", "published"), default="working")
    archives = sub.add_parser("archives")
    archives.add_argument("--sdist", required=True, type=Path)
    archives.add_argument("--wheel", required=True, type=Path)
    dependencies = sub.add_parser("dependencies")
    dependencies.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "source":
            result = validate_source(inventory=args.inventory)
        elif args.command == "secrets":
            result = scan_secrets(inventory=args.inventory)
        elif args.command == "archives":
            result = verify_archives(args.sdist, args.wheel)
        else:
            result = audit_dependencies([RUNTIME_LOCK, TOOLS_LOCK], args.output_dir)
    except (AssuranceError, OSError, ValueError, json.JSONDecodeError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
