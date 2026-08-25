from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import unquote

try:
    from scripts import st08_09_release_assurance as release_assurance
except ImportError:  # pragma: no cover - direct script execution
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_11_tabular_regression_protocol_core_and_CLI_support_contract_v01.json"
PATH_CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_10_root_and_bilingual_user_documentation_contract_v01.json"
PROTECTED_SOURCE = PROJECT_ROOT / "data_registry/st08_04_public_product_scope_and_release_train_contract_design_evidence_v01.json"
README_EN = PROJECT_ROOT / "README.md"
README_RU = PROJECT_ROOT / "README_RU.md"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
APPLICATION = PROJECT_ROOT / "src/mlcra/application.py"
WORKFLOW = PROJECT_ROOT / ".github/workflows/ci.yml"


class DocumentationAssuranceError(RuntimeError):
    pass


def default_inventory(inventory: str | None = None) -> str:
    selected = inventory or os.environ.get("MLCRA_ASSURANCE_INVENTORY", "working")
    if selected not in {"working", "published"}:
        raise DocumentationAssuranceError(f"unsupported assurance inventory: {selected}")
    return selected


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DocumentationAssuranceError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _section_markers(text: str) -> list[str]:
    return re.findall(r"<!-- ST08-10:([a-z-]+) -->", text)


def _powershell_blocks(text: str) -> list[str]:
    return re.findall(r"```powershell\r?\n(.*?)\r?\n```", text, flags=re.DOTALL)


def validate_bilingual_documents(
    english_path: Path = README_EN,
    russian_path: Path = README_RU,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or _load_json(CONTRACT_PATH)
    english = english_path.read_text(encoding="utf-8")
    russian = russian_path.read_text(encoding="utf-8")
    expected_markers = contract["documentation_architecture"]["section_markers"]
    for language, text in (("EN", english), ("RU", russian)):
        observed = _section_markers(text)
        if observed != expected_markers:
            raise DocumentationAssuranceError(
                f"{language} section markers mismatch: {observed}/{expected_markers}"
            )
        for token in contract["documentation_architecture"]["required_shared_tokens"]:
            if token not in text:
                raise DocumentationAssuranceError(f"{language} required token missing: {token}")
        lowered = text.lower()
        for claim in contract["documentation_architecture"]["forbidden_claims"]:
            if claim.lower() in lowered:
                raise DocumentationAssuranceError(f"{language} forbidden claim present: {claim}")
    if "[Русская версия](README_RU.md)" not in english:
        raise DocumentationAssuranceError("English README language switch missing")
    if "[English version](README.md)" not in russian:
        raise DocumentationAssuranceError("Russian README language switch missing")
    english_blocks = _powershell_blocks(english)
    russian_blocks = _powershell_blocks(russian)
    expected_blocks = int(contract["documentation_architecture"]["powershell_blocks"])
    if english_blocks != russian_blocks or len(english_blocks) != expected_blocks:
        raise DocumentationAssuranceError(
            f"PowerShell walkthrough mismatch: EN={len(english_blocks)} RU={len(russian_blocks)} expected={expected_blocks}"
        )
    return {
        "sections_per_language": len(expected_markers),
        "powershell_blocks_per_language": expected_blocks,
        "command_parity": True,
    }


def markdown_local_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)


def validate_markdown_links(paths: Sequence[Path]) -> dict[str, Any]:
    checked = 0
    failures: list[dict[str, str]] = []
    for document in paths:
        for raw_target in markdown_local_links(document):
            target = raw_target.strip().strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_part = unquote(target.partition("#")[0])
            if not local_part:
                continue
            checked += 1
            if local_part.startswith("/"):
                resolved = PROJECT_ROOT / local_part.lstrip("/")
            else:
                resolved = document.parent / local_part
            if not resolved.exists():
                failures.append(
                    {"document": document.relative_to(PROJECT_ROOT).as_posix(), "target": target}
                )
    if failures:
        raise DocumentationAssuranceError(f"broken local Markdown links: {failures}")
    return {"documents": len(paths), "local_links": checked, "broken": 0}


def validate_current_path_reconciliation(
    contract: dict[str, Any] | None = None,
    inventory: str = "working",
) -> dict[str, Any]:
    contract = contract or _load_json(PATH_CONTRACT_PATH)
    published_paths = (
        set(release_assurance.tracked_repository_paths(PROJECT_ROOT))
        if inventory == "published"
        else None
    )
    checked_fragments = 0
    policy_excluded_paths = 0
    for row in contract["current_path_reconciliation"]:
        document = PROJECT_ROOT / row["document"]
        text = document.read_text(encoding="utf-8")
        for fragment in row["forbidden_current_fragments"]:
            checked_fragments += 1
            if fragment in text:
                raise DocumentationAssuranceError(
                    f"obsolete current reference remains in {row['document']}: {fragment}"
                )
        for fragment in row["required_current_fragments"]:
            checked_fragments += 1
            if fragment not in text:
                raise DocumentationAssuranceError(
                    f"required current reference missing in {row['document']}: {fragment}"
                )
            if published_paths is not None and fragment not in published_paths:
                policy_excluded_paths += 1
            elif not (PROJECT_ROOT / fragment).exists():
                raise DocumentationAssuranceError(f"registered current path does not exist: {fragment}")
    exception = contract["protected_historical_exception"]
    protected_text = (PROJECT_ROOT / exception["document"]).read_text(encoding="utf-8")
    archive_path = exception["required_archive_path"]
    archive_exists_or_excluded = (
        (PROJECT_ROOT / archive_path).is_file()
        if published_paths is None
        else archive_path not in published_paths or (PROJECT_ROOT / archive_path).is_file()
    )
    if archive_path not in protected_text or not archive_exists_or_excluded:
        raise DocumentationAssuranceError("protected historical path exception is not explicitly reconciled")
    return {
        "documents": len(contract["current_path_reconciliation"]),
        "fragments": checked_fragments,
        "protected_historical_exceptions": 1,
        "policy_excluded_paths": policy_excluded_paths,
    }


def validate_project_metadata() -> dict[str, Any]:
    with PYPROJECT.open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project.get("readme") != "README.md":
        raise DocumentationAssuranceError("pyproject project.readme must be the root README.md")
    if project.get("version") != "0.1.0.dev0":
        raise DocumentationAssuranceError("documentation task must not change the development version")
    return {"readme": project["readme"], "version": project["version"]}


def validate_doctor_and_workflow() -> dict[str, Any]:
    application = APPLICATION.read_text(encoding="utf-8")
    if "RU_and_EN_documentation_deferred_to_ST08_10" in application:
        raise DocumentationAssuranceError("doctor still reports the completed ST08_10 deferral")
    required_blockers = [
        "John_release_authorization_not_granted",
    ]
    missing_blockers = [token for token in required_blockers if token not in application]
    if missing_blockers:
        raise DocumentationAssuranceError(f"doctor current blockers missing: {missing_blockers}")
    retired_blockers = [
        "public_development_gate_not_passed",
        "hosted_CI_run_not_observed",
        "external_GitHub_secret_scanning_not_enabled",
        "release_candidate_reaudit_not_passed",
        "prospective_release_candidate_reaudit_v02_not_passed",
    ]
    stale_blockers = [token for token in retired_blockers if token in application]
    if stale_blockers:
        raise DocumentationAssuranceError(f"doctor completed blockers still present: {stale_blockers}")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    required_commands = [
        "st08_10_documentation_assurance.py source --inventory published",
        "tests.test_documentation_st08_10",
        "st08_10_documentation_assurance.py walkthrough",
        "tests.test_dashboard_st08_12",
    ]
    missing_commands = [command for command in required_commands if command not in workflow]
    if missing_commands:
        raise DocumentationAssuranceError(f"CI documentation commands missing: {missing_commands}")
    return {
        "doctor_blockers": required_blockers,
        "retired_doctor_blockers": retired_blockers,
        "CI_commands": required_commands,
    }


def validate_protected_hashes(inventory: str = "working") -> dict[str, Any]:
    if inventory == "published":
        result = release_assurance.validate_protected_hashes(
            PROJECT_ROOT,
            inventory="published",
        )
        return {"expected": result["expected"], "mismatches": result["mismatches"]}
    source = _load_json(PROTECTED_SOURCE)
    mismatches = []
    for relative, expected in source["protected_artifacts"].items():
        path = PROJECT_ROOT / relative
        actual = _sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append({"path": relative, "expected": expected, "actual": actual})
    if mismatches:
        raise DocumentationAssuranceError(f"protected scientific artifact mismatch: {mismatches}")
    return {"expected": len(source["protected_artifacts"]), "mismatches": 0}


def validate_source(inventory: str | None = None) -> dict[str, Any]:
    inventory = default_inventory(inventory)
    contract = _load_json(CONTRACT_PATH)
    result = {
        "bilingual": validate_bilingual_documents(contract=contract),
        "links": validate_markdown_links([README_EN, README_RU]),
        "paths": validate_current_path_reconciliation(inventory=inventory),
        "metadata": validate_project_metadata(),
        "doctor_and_CI": validate_doctor_and_workflow(),
        "protected": validate_protected_hashes(inventory=inventory),
    }
    result["status"] = "PASS"
    return result


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_walkthrough(mlcra: Path) -> dict[str, Any]:
    if not mlcra.is_file():
        raise DocumentationAssuranceError(f"installed mlcra command missing: {mlcra}")
    scenarios = {
        "classification": (
            PROJECT_ROOT / "tests/fixtures/st08_08/binary_claim_v01.json",
            PROJECT_ROOT / "tests/fixtures/st08_08/binary_data_v01.csv",
        ),
        "regression": (
            PROJECT_ROOT / "tests/fixtures/st08_11/regression_claim_v01.json",
            PROJECT_ROOT / "tests/fixtures/st08_11/regression_data_v01.csv",
        ),
    }
    with tempfile.TemporaryDirectory(prefix="mlcra-st08-11-walkthrough-") as temporary:
        doctor = _run([str(mlcra), "doctor", "--format", "json"])
        if doctor.returncode != 0:
            raise DocumentationAssuranceError(
                f"doctor failed: code={doctor.returncode} stdout={doctor.stdout} stderr={doctor.stderr}"
            )
        doctor_payload = json.loads(doctor.stdout)
        if not doctor_payload.get("environment_pass") or doctor_payload.get("release_ready"):
            raise DocumentationAssuranceError(f"doctor contract mismatch: {doctor_payload}")
        if "RU_and_EN_documentation_deferred_to_ST08_10" in doctor_payload.get("release_blockers", []):
            raise DocumentationAssuranceError("installed doctor still reports the completed ST08_10 deferral")
        expected_files = {
            "run_manifest.json", "input_validation.json", "environment.json",
            "provenance.json", "audit_summary.json", "verdict.json", "warnings.json",
            "artifact_index.json",
        }
        scenario_results: dict[str, Any] = {}
        for name, (claim, data) in scenarios.items():
            bundle = Path(temporary) / f"{name}-bundle"
            audit = _run(
                [
                    str(mlcra), "audit", "--spec", str(claim), "--data", str(data),
                    "--output-dir", str(bundle), "--format", "json",
                ]
            )
            if audit.returncode != 0:
                raise DocumentationAssuranceError(
                    f"{name} audit failed: code={audit.returncode} stdout={audit.stdout} stderr={audit.stderr}"
                )
            audit_payload = json.loads(audit.stdout)
            observed_files = {path.name for path in bundle.iterdir()}
            if audit_payload.get("verdict") != "supported" or observed_files != expected_files:
                raise DocumentationAssuranceError(
                    f"{name} audit walkthrough mismatch: payload={audit_payload} files={sorted(observed_files)}"
                )
            verify = _run([str(mlcra), "verify", "--bundle", str(bundle), "--format", "json"])
            if verify.returncode != 0:
                raise DocumentationAssuranceError(
                    f"{name} verify failed: code={verify.returncode} stdout={verify.stdout} stderr={verify.stderr}"
                )
            verify_payload = json.loads(verify.stdout)
            if (
                verify_payload.get("status") != "PASS"
                or verify_payload.get("verified_artifacts") != 8
                or verify_payload.get("model_fit_performed") is not False
            ):
                raise DocumentationAssuranceError(f"{name} verify walkthrough mismatch: {verify_payload}")
            manifest = json.loads((bundle / "run_manifest.json").read_text(encoding="utf-8"))
            if manifest.get("network_attempts") != 0:
                raise DocumentationAssuranceError(f"{name} walkthrough made a network attempt")
            scenario_results[name] = {
                "audit_exit_code": 0,
                "verdict": "supported",
                "bundle_files": 8,
                "verify_status": "PASS",
            }
        return {
            "doctor": {"exit_code": 0, "environment_pass": True, "release_ready": False},
            "scenarios": scenario_results,
            "verify_model_fit_performed": False,
            "network_attempts": 0,
            "scientific_registration_effect": "NONE_synthetic_fixtures_only",
            "status": "PASS",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Current ST08_11 documentation assurance")
    subparsers = parser.add_subparsers(dest="command", required=True)
    source = subparsers.add_parser("source")
    source.add_argument(
        "--inventory",
        choices=("working", "published"),
        default=default_inventory(),
    )
    walkthrough = subparsers.add_parser("walkthrough")
    walkthrough.add_argument("--mlcra", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = (
            validate_source(inventory=args.inventory)
            if args.command == "source"
            else run_walkthrough(args.mlcra.resolve())
        )
    except (DocumentationAssuranceError, json.JSONDecodeError, OSError, tomllib.TOMLDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
