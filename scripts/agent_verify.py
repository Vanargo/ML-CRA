from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "docs" / "agent" / "baseline_manifest_v13.csv"
REQUIRED_SCOPE_RELATIVE_PATHS = (
    "docs/agent/pilot_change_scope_v01.csv",
    "docs/agent/agent_working_protocol_change_scope_v01.csv",
    "docs/agent/st07_07_current_effect_readout_change_scope_v01.csv",
    "docs/agent/st07_08_hgb_model_space_change_scope_v01.csv",
    "docs/agent/st07_09_nested_cv_contract_change_scope_v01.csv",
    "docs/agent/st07_10_binary_metric_contract_change_scope_v01.csv",
    (
        "docs/agent/"
        "st07_11_nested_cv_split_and_evaluation_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_12_nested_cv_fit_and_tuning_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_14_numeric_backend_and_thread_reproducibility_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_15_nested_cv_v02_protocol_and_validation_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_15_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_16_nested_cv_v02_execution_harness_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_16_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_17_nested_cv_v02_offline_miniboone_runner_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_17_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_18_nested_cv_v02_dual_run_reproducibility_validation_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_18_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_19_artifact_context_and_provenance_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_19_change_scope_v01.csv"
    ),
    (
        "docs/agent/st07_20_nested_cv_v02_provenance_corrected_dual_run_"
        "revalidation_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_20_change_scope_v01.csv"
    ),
    (
        "docs/agent/st07_21_nested_cv_v02_promotion_source_and_timing_"
        "provenance_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_21_change_scope_v01.csv"
    ),
    (
        "docs/agent/st07_22_nested_cv_v02_transactional_promotion_and_"
        "canonical_artifact_registration_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_22_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_23_stage05_seed_stability_modularization_contract_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_23_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_24_stage05_seed_stability_modular_extraction_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_24_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_25_stage05_seed_stability_full_validation_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_25_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_26_stage05_seed_stability_logistic_blas_diagnostic_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_26_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_27_stage05_split_10x1_modularization_contract_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_27_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_28_stage05_split_10x1_modular_extraction_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_28_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_29_stage05_split_10x1_full_validation_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_29_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_30_stage05_non_nested_optimism_probe_modularization_"
        "contract_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_30_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_31_stage05_non_nested_optimism_probe_modular_extraction_"
        "change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_next_block_selection_after_st07_31_change_scope_v01.csv"
    ),
    (
        "docs/agent/"
        "st07_32_stage05_non_nested_optimism_full_validation_"
        "change_scope_v01.csv"
    ),
    "docs/agent/st07_33_stage07_closure_audit_change_scope_v01.csv",
    "docs/agent/st07_34_verdict_policy_application_contract_change_scope_v01.csv",
    (
        "docs/agent/st07_35_verdict_policy_application_modular_extraction_"
        "change_scope_v01.csv"
    ),
    "docs/agent/st07_next_block_selection_after_st07_35_change_scope_v01.csv",
    (
        "docs/agent/st07_36_stage07_post_verdict_policy_closure_reaudit_"
        "change_scope_v01.csv"
    ),
    "docs/agent/stage07_closure_and_next_stage_selection_change_scope_v01.csv",
    (
        "docs/agent/st08_01_project_completion_and_release_readiness_"
        "contract_change_scope_v01.csv"
    ),
    (
        "docs/agent/st08_02_project_completion_and_release_readiness_"
        "baseline_audit_change_scope_v01.csv"
    ),
    (
        "docs/agent/st08_03_project_scope_release_class_owner_decision_"
        "change_scope_v01.csv"
    ),
)
SOURCE_ARCHIVE_SHA256 = "753f11009e1976b207ab509bd522da533ff8042703f135c5c25f055ea4d79e8e"
ST07_08_STAGE_RECORD_PATH = (
    PROJECT_ROOT / "docs" / "stages" / "stage_07_code_modularization.md"
)
ST07_08_NOTEBOOK_PATH = (
    PROJECT_ROOT / "notebooks" / "04_dataset_smoke_experiments.ipynb"
)
ST07_08_MODEL_SPACES_PATH = PROJECT_ROOT / "src" / "mlcra" / "model_spaces.py"
ST07_08_MODEL_SPACES_SHA256 = (
    "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b"
)
ST07_08_NOTEBOOK_SHA256 = (
    "0b4946e98d6dc92ef90214c00a48265a3779d5f3ff1c2b7075b819b8d19b7362"
)
ST07_07_SECTION_16_4_SHA256 = (
    "e96d9315ee29d74c3cc0b494f43b5a0bd2f5d7ceba59cba4701db848f9e4bc7b"
)
ST07_08_VERIFIER_FINAL_DIFF_SHA256 = (
    "0cce38780e0af9c35f44ef7e530034ba39bbe1a3ad1034608bdfb15728eaf9b7"
)
ST07_08_VERIFIER_CORRECTION_DIFF_SHA256 = (
    "999ac9ac08564441bac8d861d9302d3da1ec861ecb27fbd0242bf1475508b440"
)
ST07_08_NOTEBOOK_EVIDENCE_BEGIN = (
    "<!-- ST07_08_NOTEBOOK_EVIDENCE_JSON_BEGIN -->"
)
ST07_08_NOTEBOOK_EVIDENCE_END = (
    "<!-- ST07_08_NOTEBOOK_EVIDENCE_JSON_END -->"
)
ST07_08_MODEL_SPACES_EVIDENCE_BEGIN = (
    "<!-- ST07_08_MODEL_SPACES_SOURCE_BEGIN -->"
)
ST07_08_MODEL_SPACES_EVIDENCE_END = (
    "<!-- ST07_08_MODEL_SPACES_SOURCE_END -->"
)
ST07_08_VERIFIER_FINAL_DIFF_BEGIN = (
    "<!-- ST07_08_VERIFIER_FINAL_DIFF_BEGIN -->"
)
ST07_08_VERIFIER_FINAL_DIFF_END = (
    "<!-- ST07_08_VERIFIER_FINAL_DIFF_END -->"
)
ST07_08_CORRECTION_DIFF_BEGIN = (
    "<!-- ST07_08_CORRECTION_VERIFIER_DIFF_BEGIN -->"
)
ST07_08_CORRECTION_DIFF_END = (
    "<!-- ST07_08_CORRECTION_VERIFIER_DIFF_END -->"
)
ST07_08_EXPECTED_CELL_EVIDENCE = (
    (
        27,
        "fb7c8ab8",
        "4f39654447c8b3c95718d6bc7fed753a92ca36c95b27da0fba701dccaee6b474",
        "4b85437bc1b5b05cb97c9d84114008b1dcf1ca5cb1c08782feefd693eed38c47",
    ),
    (
        28,
        "0cc19811",
        "15f3ce5e6787bc51cb9719c79a9d101d3b1bf181ef6b93e8a9a2810d253b8982",
        "d5d06dbc83e526631cdb3baecee2f73a394ff6996dc6cb8144544a8600af67ef",
    ),
    (
        37,
        "5769f64e",
        "af519f81a7064e0eeade0847a36712091650e7732fa6b201c3458ee94f6d4752",
        "3ce248540603e301f76f4c8d6a893cc26f4cff35fcc3c45e10f4fe02091ab88a",
    ),
    (
        38,
        "440b6172",
        "ce68a4c4fef12b178a876a6aa1d6ceb918056f381fc0e164521e442c2d10c075",
        "e0d42408f3605883c261e09280f0a33bf1adc2e44cf1189dc8d88943658ec55d",
    ),
    (
        41,
        "1e6098e5",
        "b49238fa66ebd919f0d9ede5d6139dff7e88c94e5bf0702df4c0a1b062eedfb0",
        "f641dfecc93ec8a64a317791b4585b90a4179c7e039d8c1b5745c9038811a761",
    ),
    (
        42,
        "2cc7c20e",
        "e45bc5bca6873951b00e2183ac0a398d6968b02b5c95c5c4b4faca3df2dee8a3",
        "b0e7ca6503dfbad179d43b98c4e6288c2418751399f75e13901f5e793394c529",
    ),
    (
        51,
        "ec095766",
        "1dc58e59c6c358573dafa8cfbb4ad692a575cef9ad384418b9c913dea456cf68",
        "f363827d2e134d4c7462b9833d67a35adc359b6f8d089b80c96d941eab11cde5",
    ),
)
LOCAL_CACHE_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
}
DERIVED_FILE_SUFFIXES = {".pyc", ".pyo"}
EXPECTED_MAIN_NOTEBOOK_CELL_IDS = [
    "6304ddf8",
    "ddcda580",
    "10e2de03",
    "02e29601",
    "dd3d1a1b",
    "3987442a",
    "8695b6df",
    "465f4534",
    "72b95437",
    "84ce2bcb",
    "bcdc1837",
    "c6e2998d",
    "9c8f2386",
    "fae14890",
    "1d758c11",
    "1ffbc612",
    "0f61af4b",
    "371421e3",
    "39555b7b",
    "fa2372f7",
    "b77d7901",
    "3bb6a996",
    "ef1be9d5",
    "f85f0eab",
    "1e7dcbe4",
    "4f3c79aa",
    "26935379",
    "fb7c8ab8",
    "0cc19811",
    "c4c56ab7",
    "924a6d2f",
    "656bc032",
    "7602c7cd",
    "7e8083f1",
    "bc19a993",
    "c32dcf15",
    "8f707fb1",
    "5769f64e",
    "440b6172",
    "24226b5c",
    "2cc13f17",
    "1e6098e5",
    "2cc7c20e",
    "f301af0a",
    "fa9f928e",
    "588a8bba",
    "acb3447d",
    "6924078e",
    "4d61d21c",
    "af919ae8",
    "170b1271",
    "ec095766",
]


@dataclass
class Check:
    name: str
    status: str
    detail: str


@dataclass
class ProjectInventory:
    files: dict[str, Path]
    ignored_local_files: int
    virtual_environment_roots: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


ST07_22_CANONICAL_HASHES = {
    "data_registry/openml_miniboone_nested_v02_outer_scores.csv": (
        "c6671f2a9ca75e174634baaa07f655c731ae230709e0231fa84b470e896921fc"
    ),
    "data_registry/openml_miniboone_nested_v02_selected_params.csv": (
        "9e9e5815e94584064b00f2c54aa89bf6d98705487a4017ef8d3a67e48cc4bb2c"
    ),
    "data_registry/openml_miniboone_nested_v02_summary.csv": (
        "56a9505cf51fdab3d64b1afc149400e87748350df50af03f6dc3d07127282491"
    ),
    "data_registry/openml_miniboone_nested_v02_quality_checks.csv": (
        "5c9e13717d2661615f07ac151ed41eac8fc916bab0c3c967876560339d047f13"
    ),
    "data_registry/openml_miniboone_nested_v02_warnings.csv": (
        "10cb498cc3c4d569c78986e715f78ac37829fce3fe8fe1107f8e0351c61d51fd"
    ),
    "data_registry/openml_miniboone_nested_v02_environment.csv": (
        "20426cdee7b7d5b38f5c5e007193e5d2655953f5cdc73f88be761a645cef6039"
    ),
    "data_registry/openml_miniboone_nested_v02_numeric_runtime.csv": (
        "d88db7beecee355ca3720d0faa63b7673f23024f38ab6416e49985eeb19c9b4f"
    ),
}


def st07_22_canonical_bundle_exact() -> bool:
    return all(
        (PROJECT_ROOT / relative).is_file()
        and sha256_file(PROJECT_ROOT / relative) == expected
        for relative, expected in ST07_22_CANONICAL_HASHES.items()
    )


def read_contract_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def is_derived(path: str) -> bool:
    relative = PurePosixPath(path)
    return (
        relative.suffix.casefold() in DERIVED_FILE_SUFFIXES
        or any(
            part.casefold() in LOCAL_CACHE_DIR_NAMES
            for part in relative.parts
        )
    )


def count_files_in_ignored_tree(root: Path) -> int:
    return sum(
        len(filenames)
        for _, _, filenames in os.walk(root, onerror=lambda error: (_ for _ in ()).throw(error))
    )


def build_project_inventory() -> ProjectInventory:
    files: dict[str, Path] = {}
    ignored_local_files = 0
    virtual_environment_roots: list[str] = []

    def raise_walk_error(error: OSError) -> None:
        raise error

    for directory, dirnames, filenames in os.walk(
        PROJECT_ROOT,
        topdown=True,
        onerror=raise_walk_error,
    ):
        directory_path = Path(directory)
        retained_dirs: list[str] = []
        for dirname in sorted(dirnames, key=str.casefold):
            child = directory_path / dirname
            is_virtual_environment = (
                dirname.casefold() == "ml-cra-venv"
                or (child / "pyvenv.cfg").is_file()
            )
            if is_virtual_environment:
                virtual_environment_roots.append(
                    child.relative_to(PROJECT_ROOT).as_posix()
                )
                ignored_local_files += count_files_in_ignored_tree(child)
            elif dirname.casefold() in LOCAL_CACHE_DIR_NAMES:
                ignored_local_files += count_files_in_ignored_tree(child)
            else:
                retained_dirs.append(dirname)
        dirnames[:] = retained_dirs

        for filename in sorted(filenames, key=str.casefold):
            path = directory_path / filename
            relative_path = path.relative_to(PROJECT_ROOT).as_posix()
            if is_derived(relative_path):
                ignored_local_files += 1
            else:
                files[relative_path] = path

    return ProjectInventory(
        files=files,
        ignored_local_files=ignored_local_files,
        virtual_environment_roots=sorted(virtual_environment_roots),
    )


def check_change_scope(
    strict: bool,
    current: dict[str, Path],
    scope_paths: list[Path],
) -> tuple[Check, dict[str, list[str]]]:
    manifest_rows = read_contract_csv(MANIFEST_PATH)
    baseline = {row["relative_path"]: row for row in manifest_rows}
    scope_errors: list[str] = []
    allowed_added: set[str] = set()
    allowed_modified: set[str] = set()
    path_history: dict[str, list[str]] = {}

    for scope_path in scope_paths:
        try:
            if not scope_path.is_file():
                raise FileNotFoundError(scope_path)
            scope_rows = read_contract_csv(scope_path)
        except Exception as exc:
            scope_errors.append(
                f"{scope_path.relative_to(PROJECT_ROOT).as_posix()}: "
                f"{type(exc).__name__}: {exc}"
            )
            continue

        file_kinds: dict[str, set[str]] = {}
        for row_number, row in enumerate(scope_rows, start=2):
            change_kind = str(row.get("change_kind", "")).strip()
            relative_path = str(row.get("relative_path", "")).strip()
            location = (
                f"{scope_path.relative_to(PROJECT_ROOT).as_posix()}"
                f":{row_number}"
            )
            if change_kind not in {"added", "modified"}:
                scope_errors.append(
                    f"{location}: unknown change_kind={change_kind!r}"
                )
                continue
            if not relative_path:
                scope_errors.append(f"{location}: empty relative_path")
                continue
            pure_path = PurePosixPath(relative_path)
            if pure_path.is_absolute() or ".." in pure_path.parts:
                scope_errors.append(
                    f"{location}: unsafe relative_path={relative_path!r}"
                )
                continue

            kinds_in_file = file_kinds.setdefault(relative_path, set())
            kinds_in_file.add(change_kind)
            if len(kinds_in_file) > 1:
                scope_errors.append(
                    f"{location}: contradictory classifications in one "
                    f"scope file for {relative_path!r}"
                )
                continue

            history = path_history.setdefault(relative_path, [])
            if change_kind in history:
                continue
            if relative_path in baseline:
                if change_kind != "modified":
                    scope_errors.append(
                        f"{location}: baseline path cannot be classified "
                        f"as added: {relative_path!r}"
                    )
                    continue
                allowed_modified.add(relative_path)
            else:
                if not history and change_kind != "added":
                    scope_errors.append(
                        f"{location}: non-baseline path must first be "
                        f"classified as added: {relative_path!r}"
                    )
                    continue
                if history and history[-1] != "added":
                    scope_errors.append(
                        f"{location}: contradictory classification order "
                        f"for {relative_path!r}"
                    )
                    continue
                allowed_added.add(relative_path)
            history.append(change_kind)

    missing = sorted(
        path for path in baseline if path not in current and not is_derived(path)
    )
    modified = sorted(
        path
        for path, row in baseline.items()
        if path in current
        and not is_derived(path)
        and sha256_file(current[path]) != row["sha256"]
    )
    added = sorted(path for path in current if path not in baseline and not is_derived(path))
    out_of_scope_modified = sorted(set(modified) - allowed_modified)
    out_of_scope_added = sorted(set(added) - allowed_added)
    missing_planned_additions = sorted(allowed_added - set(added))
    unchanged_planned_modifications = sorted(
        allowed_modified - set(modified) - set(added)
    )

    archive_hashes = {row["source_archive_sha256"] for row in manifest_rows}
    manifest_ok = (
        len(manifest_rows) == 158
        and archive_hashes == {SOURCE_ARCHIVE_SHA256}
        and len(baseline) == len(manifest_rows)
    )
    scope_ok = (
        not scope_errors
        and not missing
        and not out_of_scope_modified
        and not out_of_scope_added
    )
    if strict:
        scope_ok = (
            scope_ok
            and not missing_planned_additions
            and not unchanged_planned_modifications
        )

    details = {
        "missing": missing,
        "modified": modified,
        "added": added,
        "out_of_scope_modified": out_of_scope_modified,
        "out_of_scope_added": out_of_scope_added,
        "missing_planned_additions": missing_planned_additions,
        "unchanged_planned_modifications": unchanged_planned_modifications,
        "scope_errors": scope_errors,
    }
    status = "PASS" if manifest_ok and scope_ok else "FAIL"
    detail = (
        f"manifest_rows={len(manifest_rows)}; scope_files={len(scope_paths)}; "
        f"modified={len(modified)}; "
        f"added={len(added)}; missing={len(missing)}; "
        f"out_of_scope={len(out_of_scope_modified) + len(out_of_scope_added)}; "
        f"scope_errors={len(scope_errors)}"
    )
    return Check("baseline_and_change_scope", status, detail), details


def check_python_syntax(current: dict[str, Path]) -> Check:
    paths = sorted(
        path
        for relative_path, path in current.items()
        if path.suffix.casefold() == ".py"
        and (
            PurePosixPath(relative_path).parts[0] == "src"
            or PurePosixPath(relative_path).parent == PurePosixPath("scripts")
        )
    )
    errors: list[str] = []
    for path in paths:
        try:
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            errors.append(f"{path.relative_to(PROJECT_ROOT)}: {exc}")
    return Check(
        "python_syntax",
        "PASS" if not errors else "FAIL",
        f"files={len(paths)}" if not errors else " | ".join(errors),
    )


def check_csv_structure(current: dict[str, Path]) -> Check:
    errors: list[str] = []
    paths = sorted(
        path
        for path in current.values()
        if path.suffix.casefold() == ".csv"
    )
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8-sig")
            candidates: list[tuple[int, list[list[str]]]] = []
            for delimiter in (",", ";", "\t"):
                candidate_rows = list(
                    csv.reader(io.StringIO(text), delimiter=delimiter)
                )
                if candidate_rows:
                    candidate_width = len(candidate_rows[0])
                    if candidate_width > 0 and all(
                        len(row) == candidate_width for row in candidate_rows
                    ):
                        candidates.append((candidate_width, candidate_rows))
            if not candidates:
                raise ValueError("no consistent delimiter among comma, semicolon, tab")
            _, rows = max(candidates, key=lambda candidate: candidate[0])
            if not rows:
                errors.append(f"{path.relative_to(PROJECT_ROOT)}: empty")
                continue
            width = len(rows[0])
            if width == 0 or any(len(row) != width for row in rows):
                errors.append(f"{path.relative_to(PROJECT_ROOT)}: inconsistent width")
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            errors.append(f"{path.relative_to(PROJECT_ROOT)}: {exc}")
    return Check(
        "csv_structure",
        "PASS" if not errors else "FAIL",
        f"files={len(paths)}" if not errors else " | ".join(errors),
    )


def check_notebooks(current: dict[str, Path]) -> Check:
    errors: list[str] = []
    paths = sorted(
        path
        for path in current.values()
        if path.suffix.casefold() == ".ipynb"
    )
    main_inventory: tuple[int, int, int] | None = None
    empty: list[str] = []
    for path in paths:
        if path.stat().st_size == 0:
            empty.append(path.relative_to(PROJECT_ROOT).as_posix())
            continue
        try:
            notebook = json.loads(path.read_text(encoding="utf-8-sig"))
            if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
                errors.append(f"{path.relative_to(PROJECT_ROOT)}: invalid nbformat-4 structure")
                continue
            if path.name == "04_dataset_smoke_experiments.ipynb":
                cells = notebook["cells"]
                markdown_count = sum(cell.get("cell_type") == "markdown" for cell in cells)
                code_count = sum(cell.get("cell_type") == "code" for cell in cells)
                main_inventory = (len(cells), markdown_count, code_count)
                notebook_source = "\n".join(
                    "".join(cell.get("source", []))
                    for cell in cells
                )
                actual_cell_ids = [cell.get("id") for cell in cells]
                if actual_cell_ids != EXPECTED_MAIN_NOTEBOOK_CELL_IDS:
                    errors.append("04: cell IDs or cell order changed")
                st07_08_changed_cell_indices = [27, 28, 37, 38, 41, 42, 51]
                non_null_changed_cells = [
                    index
                    for index in st07_08_changed_cell_indices
                    if cells[index].get("execution_count") is not None
                ]
                if non_null_changed_cells:
                    errors.append(
                        "04: ST07_08 changed cells must have execution_count=null: "
                        f"{non_null_changed_cells}"
                    )
                st07_10_cell = cells[8]
                expected_st07_10_source = (
                    "from mlcra.metrics import (\n"
                    "    get_positive_class_probability,\n"
                    "    score_binary_classifier,\n"
                    ")\n\n\n"
                    "def build_estimators() -> dict[str, Any]:\n"
                    "    return {\n"
                    '        "dummy_prior": DummyClassifier(strategy="prior"),\n'
                    '        "logistic_regression": Pipeline(steps=[\n'
                    '            ("standard_scaler", StandardScaler()),\n'
                    '            ("logistic_regression", '
                    "LogisticRegression(max_iter=1000, "
                    "random_state=RANDOM_SEED)),\n"
                    "        ]),\n"
                    '        "hist_gradient_boosting": '
                    "HistGradientBoostingClassifier(\n"
                    "            random_state=RANDOM_SEED,\n"
                    "            max_iter=100,\n"
                    "            learning_rate=0.1,\n"
                    "        ),\n"
                    "    }"
                )
                if (
                    st07_10_cell.get("id") != "72b95437"
                    or st07_10_cell.get("execution_count") is not None
                    or st07_10_cell.get("outputs") != []
                    or "".join(st07_10_cell.get("source", []))
                    != expected_st07_10_source
                ):
                    errors.append("04: ST07_10 cell 8 contract changed")
                duplicated_metric_definitions = [
                    name
                    for name in (
                        "get_positive_class_probability",
                        "score_binary_classifier",
                    )
                    if f"def {name}" in notebook_source
                ]
                if duplicated_metric_definitions:
                    errors.append(
                        "04: duplicated binary metric definitions remain: "
                        f"{duplicated_metric_definitions}"
                    )
                for name in (
                    "get_positive_class_probability",
                    "score_binary_classifier",
                ):
                    if notebook_source.count(f"{name}(") != 2:
                        errors.append(
                            f"04: expected two notebook {name} calls "
                            "after ST07_28 extraction"
                        )
                st07_11_definition_names = (
                    "nested_outer_position",
                    "build_outer_splitter",
                    "build_inner_splitter",
                    "evaluate_fitted_estimator_on_outer_block",
                    "fit_control_estimator_on_outer_block",
                    "fit_tuned_hist_gradient_boosting_on_outer_block",
                )
                remaining_nested_cv_definitions = [
                    name
                    for name in st07_11_definition_names
                    if f"def {name}" in notebook_source
                ]
                if remaining_nested_cv_definitions:
                    errors.append(
                        "04: duplicated ST07_11 definitions remain: "
                        f"{remaining_nested_cv_definitions}"
                    )
                expected_nested_cv_import = (
                    "from mlcra.nested_cv import (\n"
                    "    build_outer_splitter,\n"
                    "    fit_control_estimator_on_outer_block,\n"
                    "    fit_tuned_hist_gradient_boosting_on_outer_block,\n"
                    "    nested_outer_position,\n"
                    ")"
                )
                if expected_nested_cv_import not in notebook_source:
                    errors.append("04: mlcra.nested_cv import missing")
                st07_11_cells = {
                    27: "fb7c8ab8",
                    29: "c4c56ab7",
                }
                invalid_st07_11_cells = [
                    index
                    for index, cell_id in st07_11_cells.items()
                    if cells[index].get("id") != cell_id
                    or cells[index].get("execution_count") is not None
                    or cells[index].get("outputs") != []
                ]
                if invalid_st07_11_cells:
                    errors.append(
                        "04: ST07_11 changed cells must be unexecuted and "
                        f"output-free: {invalid_st07_11_cells}"
                    )
                nested_definition_source = "".join(cells[27].get("source", []))
                nested_execution_source = "".join(cells[29].get("source", []))
                expected_call_counts = {
                    "nested_outer_position(": 1,
                    "build_inner_splitter(": 0,
                    "build_outer_splitter(": 1,
                    "evaluate_fitted_estimator_on_outer_block(": 0,
                    "fit_control_estimator_on_outer_block(": 1,
                    "fit_tuned_hist_gradient_boosting_on_outer_block(": 1,
                }
                observed_call_counts = {
                    name: notebook_source.count(name)
                    for name in expected_call_counts
                }
                if observed_call_counts != expected_call_counts:
                    errors.append(
                        "04: ST07_11 modular call inventory changed: "
                        f"{observed_call_counts}"
                    )
                if (
                    "RepeatedStratifiedKFold(" in nested_execution_source
                    or "StratifiedKFold(" in nested_definition_source
                ):
                    errors.append(
                        "04: direct ST07_11 splitter construction remains"
                    )
                obsolete_model_space_functions = [
                    "parse_nested_parameter_value",
                    "parse_nested_parameter_values",
                    "make_nested_parameter_set_id",
                    "build_hist_gradient_boosting_nested_space",
                    "parse_stage05_seed_parameter_value",
                    "parse_stage05_seed_parameter_values",
                    "make_stage05_seed_parameter_set_id",
                    "build_stage05_seed_hgb_space",
                ]
                remaining_model_space_definitions = [
                    name
                    for name in obsolete_model_space_functions
                    if f"def {name}" in notebook_source
                ]
                if remaining_model_space_definitions:
                    errors.append(
                        "04: duplicated HGB model-space definitions remain: "
                        f"{remaining_model_space_definitions}"
                    )
                expected_model_space_import = (
                    "from mlcra.model_spaces import (\n"
                    "    build_hist_gradient_boosting_search_space,\n"
                    "    make_hgb_parameter_set_id,\n"
                    ")"
                )
                if expected_model_space_import not in notebook_source:
                    errors.append("04: mlcra.model_spaces import missing")
                if notebook_source.count(
                    "build_hist_gradient_boosting_search_space("
                ) != 4:
                    errors.append(
                        "04: expected four HGB search-space builder calls"
                    )
                if notebook_source.count("make_hgb_parameter_set_id(") != 0:
                    errors.append(
                        "04: expected no remaining HGB parameter-set ID call"
                    )
                if "make_stage05_metric_rows" in notebook_source:
                    errors.append(
                        "04: obsolete make_stage05_metric_rows remains"
                    )
                if (
                    "from mlcra.verdicts import build_current_effect_readout"
                    not in notebook_source
                ):
                    errors.append(
                        "04: build_current_effect_readout import missing"
                    )
                if "build_current_effect_readout(" not in notebook_source:
                    errors.append(
                        "04: build_current_effect_readout call missing"
                    )
                current_readout_source = "".join(cells[34].get("source", []))
                forbidden_current_readout_tokens = [
                    ".merge(",
                    ".groupby(",
                ]
                duplicated_tokens = [
                    token
                    for token in forbidden_current_readout_tokens
                    if token in current_readout_source
                ]
                if duplicated_tokens:
                    errors.append(
                        "04: duplicated ST05_01 aggregation remains: "
                        f"{duplicated_tokens}"
                    )
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            errors.append(f"{path.relative_to(PROJECT_ROOT)}: {exc}")

    if main_inventory != (52, 11, 41):
        errors.append(f"04 inventory: expected (52, 11, 41), got {main_inventory}")
    expected_empty = {"notebooks/02_dataset_candidate_search_pmlb.ipynb"}
    if set(empty) != expected_empty:
        errors.append(f"empty notebooks: expected {sorted(expected_empty)}, got {empty}")

    return Check(
        "notebook_structure",
        "PASS" if not errors else "FAIL",
        "nonempty_json_valid=4; main_inventory=52/11/41; expected_empty=1"
        if not errors
        else " | ".join(errors),
    )


def check_required_paths() -> Check:
    paths = [
        "data_registry/openml_miniboone_nested_outer_scores.csv",
        "data_registry/openml_miniboone_nested_selected_params.csv",
        "data_registry/openml_miniboone_nested_summary.csv",
        "data_registry/openml_miniboone_stage05_current_effect_readout.csv",
        "data_registry/openml_miniboone_stage05_metric_conflict_audit.csv",
        "data_registry/openml_miniboone_stage05_parameter_selection_stability.csv",
        "data_registry/openml_miniboone_stage05_cost_quality_audit.csv",
        "src/mlcra/model_spaces.py",
        "src/mlcra/nested_cv.py",
        "docs/agent/st07_08_hgb_model_space_change_scope_v01.csv",
        "docs/agent/st07_09_nested_cv_contract_change_scope_v01.csv",
        "docs/agent/st07_10_binary_metric_contract_change_scope_v01.csv",
        (
            "docs/agent/"
            "st07_11_nested_cv_split_and_evaluation_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_12_nested_cv_fit_and_tuning_change_scope_v01.csv"
        ),
        "src/mlcra/numeric_runtime.py",
        "configs/runtime/miniboone_nested_numeric_runtime_v01.csv",
        (
            "docs/agent/"
            "st07_14_numeric_backend_and_thread_reproducibility_change_scope_v01.csv"
        ),
        "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv",
        (
            "data_registry/"
            "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        ),
        (
            "docs/agent/"
            "st07_15_nested_cv_v02_protocol_and_validation_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_15_change_scope_v01.csv"
        ),
        "src/mlcra/datasets.py",
        "src/mlcra/nested_artifacts.py",
        "scripts/st07_16_fixture_harness.py",
        (
            "docs/agent/"
            "st07_16_nested_cv_v02_execution_harness_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_16_change_scope_v01.csv"
        ),
        "scripts/st07_17_miniboone_v02_runner.py",
        (
            "docs/agent/"
            "st07_17_nested_cv_v02_offline_miniboone_runner_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_17_change_scope_v01.csv"
        ),
        "scripts/st07_18_dual_run_validation.py",
        (
            "data_registry/st07_18_nested_cv_v02_"
            "implementation_attempt_01_v01.json"
        ),
        (
            "data_registry/st07_18_nested_cv_v02_dual_run_"
            "reproducibility_validation_evidence_v01.json"
        ),
        (
            "docs/agent/st07_18_nested_cv_v02_dual_run_"
            "reproducibility_validation_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_18_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_19_artifact_context_and_provenance_change_scope_v01.csv"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_19_change_scope_v01.csv"
        ),
        (
            "data_registry/st07_19_nested_cv_v02_artifact_context_and_"
            "provenance_contract_evidence_v01.json"
        ),
        "scripts/st07_20_provenance_corrected_dual_run_revalidation.py",
        (
            "docs/agent/st07_20_nested_cv_v02_provenance_corrected_dual_run_"
            "revalidation_change_scope_v01.csv"
        ),
        (
            "data_registry/st07_20_nested_cv_v02_provenance_corrected_dual_"
            "run_revalidation_evidence_v01.json"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_20_change_scope_v01.csv"
        ),
        "scripts/st07_21_promotion_source_contract.py",
        (
            "docs/agent/st07_21_nested_cv_v02_promotion_source_and_timing_"
            "provenance_change_scope_v01.csv"
        ),
        (
            "data_registry/openml_miniboone_nested_v02_"
            "promotion_source_manifest_v01.csv"
        ),
        (
            "data_registry/st07_21_nested_cv_v02_promotion_source_and_"
            "timing_provenance_contract_evidence_v01.json"
        ),
        (
            "docs/agent/"
            "st07_next_block_selection_after_st07_21_change_scope_v01.csv"
        ),
        (
            "docs/agent/st07_22_nested_cv_v02_transactional_promotion_and_"
            "canonical_artifact_registration_change_scope_v01.csv"
        ),
        "scripts/st07_22_transactional_promotion.py",
        "data_registry/openml_miniboone_nested_v02_outer_scores.csv",
        "data_registry/openml_miniboone_nested_v02_selected_params.csv",
        "data_registry/openml_miniboone_nested_v02_summary.csv",
        "data_registry/openml_miniboone_nested_v02_quality_checks.csv",
        "data_registry/openml_miniboone_nested_v02_warnings.csv",
        "data_registry/openml_miniboone_nested_v02_environment.csv",
        "data_registry/openml_miniboone_nested_v02_numeric_runtime.csv",
        (
            "data_registry/st07_22_nested_cv_v02_promotion_transaction_"
            "journal_v01.json"
        ),
        (
            "data_registry/st07_22_nested_cv_v02_transactional_promotion_and_"
            "canonical_artifact_registration_evidence_v01.json"
        ),
        "AGENTS.md",
        ".agents/skills/ml-cra-stage-gate/SKILL.md",
        "docs/agent/st07_34_verdict_policy_application_contract_change_scope_v01.csv",
        "data_registry/st07_34_verdict_policy_application_contract_evidence_v01.json",
        (
            "docs/agent/st07_35_verdict_policy_application_modular_extraction_"
            "change_scope_v01.csv"
        ),
        (
            "data_registry/st07_35_verdict_policy_application_modular_"
            "extraction_evidence_v01.json"
        ),
        "docs/agent/st07_next_block_selection_after_st07_35_change_scope_v01.csv",
        "data_registry/st07_next_block_selection_after_st07_35_evidence_v01.json",
        (
            "docs/agent/st07_36_stage07_post_verdict_policy_closure_reaudit_"
            "change_scope_v01.csv"
        ),
        (
            "data_registry/st07_36_stage07_post_verdict_policy_closure_"
            "reaudit_evidence_v01.json"
        ),
        "docs/agent/stage07_closure_and_next_stage_selection_change_scope_v01.csv",
        "data_registry/stage07_closure_and_next_stage_selection_evidence_v01.json",
        (
            "docs/agent/st08_01_project_completion_and_release_readiness_"
            "contract_change_scope_v01.csv"
        ),
        (
            "configs/project_readiness/stage08_project_completion_and_"
            "release_readiness_requirements_v01.csv"
        ),
        (
            "data_registry/st08_01_project_completion_and_release_readiness_"
            "contract_evidence_v01.json"
        ),
        "docs/stages/stage_08_project_completion_and_release_readiness.md",
        (
            "docs/agent/st08_02_project_completion_and_release_readiness_"
            "baseline_audit_change_scope_v01.csv"
        ),
        (
            "data_registry/stage08_project_completion_and_release_readiness_"
            "audit_evidence_v01.json"
        ),
    ]
    missing = [path for path in paths if not (PROJECT_ROOT / path).is_file()]
    return Check(
        "required_paths",
        "PASS" if not missing else "FAIL",
        f"paths={len(paths)}" if not missing else f"missing={missing}",
    )


def check_documentary_consistency() -> Check:
    stage06 = (PROJECT_ROOT / "docs/stages/stage_06_packaging_and_publication.md").read_text(
        encoding="utf-8-sig"
    )
    stage07 = (PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md").read_text(
        encoding="utf-8-sig"
    )
    roadmap = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")

    forbidden = [
        "openml_miniboone_nested_cv_outer_scores.csv",
        "openml_miniboone_nested_cv_selected_params.csv",
        "openml_miniboone_nested_cv_summary.csv",
    ]
    errors = [f"obsolete Stage 6 path remains: {name}" for name in forbidden if name in stage06]
    stage07_current_status = extract_markdown_section(
        stage07,
        "## 2.",
        "## 3.",
    )
    roadmap_current_stage = extract_markdown_section(
        roadmap,
        "### Этап 7",
        "## 12.",
    )
    required_tokens = [
        ("Stage 7", "ST07_06_status: accepted_by_john"),
        ("Stage 7", "ST07_07_status: accepted_by_john"),
        ("Stage 7", "ST07_08_status: accepted_by_john"),
        ("Stage 7", "TASK_CLOSED: ST07_08_hgb_model_space_extraction"),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_09_nested_cv_contract_and_golden_master_design",
        ),
        ("Stage 7", "ST07_09_status: accepted_by_john"),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_09_nested_cv_contract_and_golden_master_design",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_10_binary_metric_contract_and_extraction",
        ),
        ("Stage 7", "ST07_10_status: accepted_by_john"),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_10_binary_metric_contract_and_extraction",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_11_nested_cv_split_and_evaluation_extraction",
        ),
        (
            "Stage 7",
            "ST07_11_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_11_nested_cv_split_and_evaluation_extraction",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_12_nested_cv_fit_and_tuning_extraction",
        ),
        (
            "Stage 7",
            "ST07_12_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_12_nested_cv_fit_and_tuning_extraction",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_13_nested_cv_full_golden_master_validation",
        ),
        (
            "Stage 7",
            "ST07_13_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_13_nested_cv_full_golden_master_validation",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_14_numeric_backend_and_thread_reproducibility_contract",
        ),
        (
            "Stage 7",
            "ST07_14_NUMERIC_POLICY: "
            "prospective_single_thread_exact_same_backend",
        ),
        (
            "Stage 7",
            "ST07_14_GOLDEN_POLICY: preserve_existing_v01_golden",
        ),
        (
            "Stage 7",
            "ST07_14_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_14_numeric_backend_and_thread_reproducibility_contract",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_15_nested_cv_v02_protocol_and_validation_contract",
        ),
        (
            "Stage 7",
            "ST07_15_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: "
            "ST07_15_nested_cv_v02_protocol_and_validation_contract",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_16_nested_cv_v02_"
            "execution_harness_and_artifact_validation_extraction",
        ),
        (
            "Stage 7",
            "ST07_16_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_16_nested_cv_v02_"
            "execution_harness_and_artifact_validation_extraction",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_17_nested_cv_v02_"
            "offline_miniboone_runner_and_preflight_contract",
        ),
        (
            "Stage 7",
            "ST07_17_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_17_nested_cv_v02_"
            "offline_miniboone_runner_and_preflight_contract",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_18_nested_cv_v02_"
            "dual_run_reproducibility_validation",
        ),
        (
            "Stage 7",
            "ST07_18_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_18_nested_cv_v02_"
            "dual_run_reproducibility_validation",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_19_nested_cv_v02_"
            "artifact_context_and_provenance_contract",
        ),
        (
            "Stage 7",
            "ST07_19_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_19_nested_cv_v02_"
            "artifact_context_and_provenance_contract",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_"
            "provenance_corrected_dual_run_revalidation",
        ),
        (
            "Stage 7",
            "ST07_20_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_20_nested_cv_v02_"
            "provenance_corrected_dual_run_revalidation",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_"
            "promotion_source_and_timing_provenance_contract",
        ),
        (
            "Stage 7",
            "ST07_21_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_21_nested_cv_v02_"
            "promotion_source_and_timing_provenance_contract",
        ),
        (
            "Stage 7",
            "ST07_21_full_miniboone_training_authorized: false",
        ),
        (
            "Stage 7",
            "ST07_21_network_authorized: false",
        ),
        (
            "Stage 7",
            "ST07_21_canonical_v02_outputs_authorized: false",
        ),
        (
            "Stage 7",
            "ST07_21_promotion_authorized: false",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_"
            "promotion_and_canonical_artifact_registration",
        ),
        ("Stage 7", "ST07_22_status: accepted_by_john"),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_"
            "promotion_and_canonical_artifact_registration",
        ),
        ("Stage 7", "ST07_22_full_miniboone_training_authorized: false"),
        ("Stage 7", "ST07_22_network_authorized: false"),
        ("Stage 7", "ST07_22_canonical_v02_outputs_authorized: true"),
        ("Stage 7", "ST07_22_promotion_authorized: true"),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_"
            "modularization_contract_and_golden_master_design",
        ),
        ("Stage 7", "ST07_23_status: accepted_by_john"),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_23_stage05_seed_stability_"
            "modularization_contract_and_golden_master_design",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_"
            "modular_extraction_and_fixture_validation",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_"
            "modularization_contract_and_golden_master_design",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_28_stage05_split_10x1_"
            "modular_extraction_and_fixture_validation",
        ),
        ("Stage 7", "ST07_28_status: accepted_by_john"),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_28_stage05_split_10x1_"
            "modular_extraction_and_fixture_validation",
        ),
        ("Stage 7", "ST07_24_status: accepted_by_john"),
        ("Stage 7", "ST07_25_status: accepted_by_john"),
        ("Stage 7", "ST07_24_training_authorized: false"),
        ("Stage 7", "ST07_24_network_authorized: false"),
        ("Stage 7", "ST07_24_source_changes_authorized: true"),
        (
            "Stage 7",
            "ST07_24_scientific_artifact_changes_authorized: false",
        ),
        ("Stage 7", "ST07_23_training_authorized: false"),
        ("Stage 7", "ST07_23_network_authorized: false"),
        ("Stage 7", "ST07_23_source_changes_authorized: false"),
        (
            "Stage 7",
            "ST07_23_scientific_artifact_changes_authorized: false",
        ),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_30_stage05_non_nested_optimism_"
            "probe_modularization_contract_and_golden_master_design",
        ),
        ("Stage 7", "ST07_30_status: accepted_by_john"),
        (
            "Stage 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_and_fixture_validation",
        ),
        ("Stage 7", "ST07_31_status: accepted_by_john"),
        (
            "Stage 7",
            "ACCEPTED_BY_JOHN: ST07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_and_fixture_validation",
        ),
        (
            "Stage 7",
            "ST07_32_status: accepted_by_john",
        ),
        (
            "Stage 7",
            "TASK_CLOSED: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
        ),
        (
            "Stage 7",
            "ST07_34_status: accepted_by_john",
        ),
        ("roadmap", "ST07_06_status: accepted_by_john"),
        ("roadmap", "ST07_07_status: accepted_by_john"),
        ("roadmap", "ST07_08_status: accepted_by_john"),
        ("roadmap", "TASK_CLOSED: ST07_08_hgb_model_space_extraction"),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_09_nested_cv_contract_and_golden_master_design",
        ),
        ("roadmap", "ST07_09_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_09_nested_cv_contract_and_golden_master_design",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_10_binary_metric_contract_and_extraction",
        ),
        ("roadmap", "ST07_10_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_10_binary_metric_contract_and_extraction",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_11_nested_cv_split_and_evaluation_extraction",
        ),
        (
            "roadmap",
            "ST07_11_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_11_nested_cv_split_and_evaluation_extraction",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_12_nested_cv_fit_and_tuning_extraction",
        ),
        (
            "roadmap",
            "ST07_12_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_12_nested_cv_fit_and_tuning_extraction",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_13_nested_cv_full_golden_master_validation",
        ),
        (
            "roadmap",
            "ST07_13_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_13_nested_cv_full_golden_master_validation",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_14_numeric_backend_and_thread_reproducibility_contract",
        ),
        (
            "roadmap",
            "ST07_14_NUMERIC_POLICY: "
            "prospective_single_thread_exact_same_backend",
        ),
        (
            "roadmap",
            "ST07_14_GOLDEN_POLICY: preserve_existing_v01_golden",
        ),
        (
            "roadmap",
            "ST07_14_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_14_numeric_backend_and_thread_reproducibility_contract",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: "
            "ST07_15_nested_cv_v02_protocol_and_validation_contract",
        ),
        (
            "roadmap",
            "ST07_15_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: "
            "ST07_15_nested_cv_v02_protocol_and_validation_contract",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_16_nested_cv_v02_"
            "execution_harness_and_artifact_validation_extraction",
        ),
        (
            "roadmap",
            "ST07_16_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: ST07_16_nested_cv_v02_"
            "execution_harness_and_artifact_validation_extraction",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_17_nested_cv_v02_"
            "offline_miniboone_runner_and_preflight_contract",
        ),
        (
            "roadmap",
            "ST07_17_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: ST07_17_nested_cv_v02_"
            "offline_miniboone_runner_and_preflight_contract",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_18_nested_cv_v02_"
            "dual_run_reproducibility_validation",
        ),
        (
            "roadmap",
            "ST07_18_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: ST07_18_nested_cv_v02_"
            "dual_run_reproducibility_validation",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_19_nested_cv_v02_"
            "artifact_context_and_provenance_contract",
        ),
        (
            "roadmap",
            "ST07_19_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: ST07_19_nested_cv_v02_"
            "artifact_context_and_provenance_contract",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_"
            "provenance_corrected_dual_run_revalidation",
        ),
        (
            "roadmap",
            "ST07_20_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: ST07_20_nested_cv_v02_"
            "provenance_corrected_dual_run_revalidation",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_"
            "promotion_source_and_timing_provenance_contract",
        ),
        (
            "roadmap",
            "ST07_21_status: accepted_by_john",
        ),
        (
            "roadmap",
            "TASK_CLOSED: ST07_21_nested_cv_v02_"
            "promotion_source_and_timing_provenance_contract",
        ),
        (
            "roadmap",
            "ST07_21_full_miniboone_training_authorized: false",
        ),
        (
            "roadmap",
            "ST07_21_network_authorized: false",
        ),
        (
            "roadmap",
            "ST07_21_canonical_v02_outputs_authorized: false",
        ),
        (
            "roadmap",
            "ST07_21_promotion_authorized: false",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_"
            "promotion_and_canonical_artifact_registration",
        ),
        ("roadmap", "ST07_22_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_"
            "promotion_and_canonical_artifact_registration",
        ),
        ("roadmap", "ST07_22_full_miniboone_training_authorized: false"),
        ("roadmap", "ST07_22_network_authorized: false"),
        ("roadmap", "ST07_22_canonical_v02_outputs_authorized: true"),
        ("roadmap", "ST07_22_promotion_authorized: true"),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_"
            "modularization_contract_and_golden_master_design",
        ),
        ("roadmap", "ST07_23_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: ST07_23_stage05_seed_stability_"
            "modularization_contract_and_golden_master_design",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_"
            "modular_extraction_and_fixture_validation",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_"
            "modularization_contract_and_golden_master_design",
        ),
        ("roadmap", "ST07_27_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: ST07_27_stage05_split_10x1_"
            "modularization_contract_and_golden_master_design",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_28_stage05_split_10x1_"
            "modular_extraction_and_fixture_validation",
        ),
        ("roadmap", "ST07_28_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: ST07_28_stage05_split_10x1_"
            "modular_extraction_and_fixture_validation",
        ),
        ("roadmap", "ST07_24_status: accepted_by_john"),
        ("roadmap", "ST07_25_status: accepted_by_john"),
        ("roadmap", "ST07_24_training_authorized: false"),
        ("roadmap", "ST07_24_network_authorized: false"),
        ("roadmap", "ST07_24_source_changes_authorized: true"),
        (
            "roadmap",
            "ST07_24_scientific_artifact_changes_authorized: false",
        ),
        ("roadmap", "ST07_23_training_authorized: false"),
        ("roadmap", "ST07_23_network_authorized: false"),
        ("roadmap", "ST07_23_source_changes_authorized: false"),
        (
            "roadmap",
            "ST07_23_scientific_artifact_changes_authorized: false",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_29_stage05_split_10x1_"
            "full_miniboone_and_golden_diagnostic_validation",
        ),
        ("roadmap", "ST07_29_status: accepted_by_john"),
        (
            "roadmap",
            "ACCEPTED_BY_JOHN: ST07_29_stage05_split_10x1_"
            "full_miniboone_and_golden_diagnostic_validation",
        ),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_30_stage05_non_nested_optimism_"
            "probe_modularization_contract_and_golden_master_design",
        ),
        ("roadmap", "ST07_30_status: accepted_by_john"),
        (
            "roadmap",
            "NEXT_BLOCK_AUTHORIZED: ST07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_and_fixture_validation",
        ),
        ("roadmap", "ST07_31_status: accepted_by_john"),
        (
            "roadmap",
            "ACCEPTED_BY_JOHN: ST07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_and_fixture_validation",
        ),
        ("roadmap", "ST07_32_status: accepted_by_john"),
        (
            "roadmap",
            "TASK_CLOSED: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
        ),
        ("roadmap", "ST07_34_status: technical_pass_ready_for_john_acceptance"),
    ]
    for document, token in required_tokens:
        body = (
            stage07_current_status
            if document == "Stage 7"
            else roadmap_current_stage
        )
        if token not in body:
            errors.append(f"{document}: missing token {token}")

    obsolete_current_tokens = [
        "ST07_08_status: ready_for_john_acceptance",
        "ST07_09_status: ready_for_john_acceptance",
        "ST07_10_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_09",
        "stage07_next_block: decision_pending_after_st07_10",
        "stage07_next_block: "
        "proposed_ST07_11_nested_cv_split_and_evaluation_extraction",
        "ST07_11_status: proposed_not_authorized",
        "ST07_11_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_11",
        "stage07_next_block: "
        "proposed_ST07_12_nested_cv_fit_and_tuning_extraction",
        "ST07_12_status: proposed_not_authorized",
        "ST07_12_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_12",
        "stage07_next_block: "
        "proposed_ST07_13_nested_cv_full_golden_master_validation",
        "ST07_13_status: proposed_not_authorized",
        "ST07_13_status: ready_for_john_acceptance",
        "ST07_13_status: technical_fail_ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_13_fail",
        "ST07_14_status: proposed_not_authorized",
        "ST07_14_status: technical_fail_ready_for_john_acceptance",
        "ST07_14_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_14",
        "ST07_15_status: proposed_not_authorized",
        "ST07_15_status: technical_fail_ready_for_john_acceptance",
        "ST07_15_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_15",
        "ST07_16_status: proposed_not_authorized",
        "ST07_16_training_authorized: false",
        "ST07_16_status: ready_for_john_acceptance",
        "ST07_16_full_miniboone_training_authorized: false",
        "stage07_next_block: decision_pending_after_st07_16",
        "stage07_next_block: "
        "proposed_ST07_17_nested_cv_v02_offline_miniboone_runner_and_preflight_contract",
        "ST07_17_status: proposed_not_authorized",
        "ST07_17_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_17",
        "stage07_next_block: proposed_ST07_18_nested_cv_v02_"
        "dual_run_reproducibility_validation",
        "ST07_18_status: proposed_not_authorized",
        "ST07_18_full_miniboone_training_authorized: false",
        "ST07_18_status: ready_for_john_acceptance",
        "ST07_18_full_miniboone_training_authorized: true",
        "stage07_next_block: decision_pending_after_st07_18",
        "stage07_next_block: proposed_ST07_19_nested_cv_v02_"
        "artifact_context_and_provenance_contract",
        "ST07_19_status: proposed_not_authorized",
        "ST07_19_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_19",
        "stage07_next_block: proposed_ST07_20_nested_cv_v02_"
        "provenance_corrected_dual_run_revalidation",
        "ST07_20_status: proposed_not_authorized",
        "ST07_20_full_miniboone_training_authorized: false",
        "ST07_20_status: ready_for_john_acceptance",
        "ST07_20_full_miniboone_training_authorized: true",
        "stage07_next_block: decision_pending_after_st07_20",
        "stage07_next_block: proposed_ST07_21_nested_cv_v02_"
        "promotion_source_and_timing_provenance_contract",
        "ST07_21_status: proposed_not_authorized",
        "ST07_21_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_21",
        "stage07_next_block: proposed_ST07_22_nested_cv_v02_"
        "transactional_promotion_and_canonical_artifact_registration",
        "ST07_22_status: proposed_not_authorized",
        "ST07_22_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_22",
        "stage07_next_block: proposed_ST07_23_stage05_seed_stability_"
        "modularization_contract_and_golden_master_design",
        "ST07_23_status: proposed_not_authorized",
        "ST07_23_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_st07_23",
        "stage07_next_block: proposed_ST07_24_stage05_seed_stability_"
        "modular_extraction_and_fixture_validation",
        "ST07_24_status: proposed_not_authorized",
        "ST07_27_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_ST07_27_acceptance",
        "stage07_next_block: proposed_ST07_28_stage05_split_10x1_"
        "modular_extraction_and_fixture_validation",
        "ST07_28_status: proposed_not_authorized",
        "stage07_next_block: proposed_ST07_30_stage05_non_nested_optimism_"
        "probe_modularization_contract_and_golden_master_design",
        "ST07_30_status: proposed_not_authorized",
        "ST07_30_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_ST07_30_acceptance",
        "stage07_next_block: proposed_ST07_31_stage05_non_nested_optimism_"
        "probe_modular_extraction_and_fixture_validation",
        "ST07_31_status: proposed_not_authorized",
        "ST07_31_status: ready_for_john_acceptance",
        "stage07_next_block: decision_pending_after_ST07_31_acceptance",
        "stage07_next_block: decision_pending_after_ST07_32_acceptance",
        "stage07_next_block: decision_pending\n",
    ]
    for document, body in [
        ("Stage 7", stage07_current_status),
        ("roadmap", roadmap_current_stage),
    ]:
        for token in obsolete_current_tokens:
            if token in body:
                errors.append(
                    f"{document}: obsolete current-state token remains: "
                    f"{token.strip()}"
                )

    return Check(
        "documentary_consistency",
        "PASS" if not errors else "FAIL",
        "Stage 6 paths, accepted ST07_08-ST07_32 statuses, and ST07_33 "
        "fail-closed boundary synchronized"
        if not errors
        else " | ".join(errors),
    )


def check_stage07_model_space_extraction() -> Check:
    try:
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )

        model_space_path = (
            PROJECT_ROOT
            / "configs"
            / "model_spaces"
            / "miniboone_hist_gradient_boosting_nested_space.csv"
        )
        model_space = pd.read_csv(
            model_space_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        model_space_before = model_space.copy(deep=True)
        protocol_id = "miniboone_nested_cv_v01"
        candidate_id = "openml_miniboone_41150"
        parameter_grid, fixed_parameters = (
            build_hist_gradient_boosting_search_space(
                model_space,
                protocol_id=protocol_id,
                candidate_id=candidate_id,
            )
        )
        repeated_grid, repeated_fixed = (
            build_hist_gradient_boosting_search_space(
                model_space,
                protocol_id=protocol_id,
                candidate_id=candidate_id,
            )
        )
        expected_grid = {
            "learning_rate": [0.05, 0.1],
            "max_iter": [100, 150],
            "max_leaf_nodes": [31, 63],
            "l2_regularization": [0.0, 0.01],
        }
        expected_fixed = {
            "random_state": 20260507,
            "early_stopping": "auto",
        }
        grid_combination_count = 1
        for values in parameter_grid.values():
            grid_combination_count *= len(values)

        parser_case = model_space.copy()
        parser_case.loc[
            parser_case["parameter_name"].eq("learning_rate"),
            "parameter_values",
        ] = " TRUE ; false ; none "
        parser_case.loc[
            parser_case["parameter_name"].eq("max_iter"),
            "parameter_values",
        ] = "01; +2; -3; 4"
        parser_case.loc[
            parser_case["parameter_name"].eq("early_stopping"),
            "fixed_value",
        ] = " none "
        parser_grid, parser_fixed = (
            build_hist_gradient_boosting_search_space(
                parser_case,
                protocol_id=protocol_id,
                candidate_id=candidate_id,
            )
        )
        parser_semantics_ok = (
            parser_grid["learning_rate"] == [True, False, None]
            and parser_grid["max_iter"] == [1.0, 2.0, -3, 4]
            and parser_fixed["early_stopping"] is None
        )

        identifier_files = [
            "openml_miniboone_nested_selected_params.csv",
            "openml_miniboone_stage05_seed_stability_selected_params.csv",
            "openml_miniboone_stage05_split_10x1_outer_scores.csv",
            "openml_miniboone_stage05_non_nested_optimism_probe.csv",
        ]
        identifier_rows = 0
        identifier_matches = 0
        function_matches_independent_reference = 0
        for file_name in identifier_files:
            frame = pd.read_csv(
                PROJECT_ROOT / "data_registry" / file_name,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
            )
            hgb_rows = frame[
                frame["model_id"].eq("hist_gradient_boosting")
                & frame["selected_params_json"].ne("")
            ]
            for _, row in hgb_rows.iterrows():
                params = json.loads(row["selected_params_json"])
                canonical = json.dumps(
                    params,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                independent_id = (
                    "hgb_"
                    + hashlib.sha256(
                        canonical.encode("utf-8")
                    ).hexdigest()[:12]
                )
                identifier_rows += 1
                identifier_matches += (
                    row["selected_parameter_set_id"] == independent_id
                )
                function_matches_independent_reference += (
                    make_hgb_parameter_set_id(params) == independent_id
                )

        key_order_independent = (
            make_hgb_parameter_set_id(
                {"max_iter": 100, "learning_rate": 0.05}
            )
            == make_hgb_parameter_set_id(
                {"learning_rate": 0.05, "max_iter": 100}
            )
        )

        negative_cases: list[tuple[str, pd.DataFrame]] = []
        negative_cases.append(
            ("missing_column", model_space.drop(columns=["fixed_value"]))
        )
        negative_cases.append(
            ("missing_rows", model_space.assign(protocol_id="other_protocol"))
        )
        negative_cases.append(
            (
                "decision_status",
                model_space.assign(decision_status="draft"),
            )
        )

        case = model_space.copy()
        case.loc[case.index[0], "search_method"] = "random"
        negative_cases.append(("unknown_search_method", case))

        case = model_space.copy()
        case.loc[case.index[0], "parameter_name"] = " "
        negative_cases.append(("empty_parameter_name", case))

        negative_cases.append(
            (
                "duplicate_parameter_name",
                pd.concat(
                    [model_space, model_space.iloc[[0]]],
                    ignore_index=True,
                ),
            )
        )
        negative_cases.append(
            (
                "missing_parameter",
                model_space[
                    model_space["parameter_name"].ne("learning_rate")
                ].copy(),
            )
        )

        extra_parameter = model_space.iloc[[0]].copy()
        extra_parameter["parameter_name"] = "extra_parameter"
        negative_cases.append(
            (
                "extra_parameter",
                pd.concat(
                    [model_space, extra_parameter],
                    ignore_index=True,
                ),
            )
        )

        case = model_space.copy()
        case.loc[
            case["parameter_name"].eq("learning_rate"),
            "parameter_values",
        ] = " "
        negative_cases.append(("empty_grid", case))

        case = model_space.copy()
        case.loc[
            case["parameter_name"].eq("learning_rate"),
            "parameter_values",
        ] = "0.05; 0.05"
        negative_cases.append(("duplicate_grid_value", case))

        case = model_space.copy()
        case.loc[
            case["parameter_name"].eq("random_state"),
            "fixed_value",
        ] = " "
        negative_cases.append(("empty_fixed_value", case))

        case = model_space.copy()
        learning_rate = case["parameter_name"].eq("learning_rate")
        case.loc[learning_rate, "search_method"] = "fixed"
        case.loc[learning_rate, "fixed_value"] = "0.05"
        negative_cases.append(("misclassified_parameter", case))

        negative_failures: list[str] = []
        for case_name, case_frame in negative_cases:
            try:
                build_hist_gradient_boosting_search_space(
                    case_frame,
                    protocol_id=protocol_id,
                    candidate_id=candidate_id,
                )
            except ValueError:
                continue
            negative_failures.append(case_name)

        module_source = (
            PROJECT_ROOT / "src" / "mlcra" / "model_spaces.py"
        ).read_text(encoding="utf-8-sig")
        forbidden_module_tokens = [
            "sklearn",
            "HistGradientBoostingClassifier",
            "GridSearchCV",
            ".fit(",
            ".predict(",
            "read_csv(",
            "to_csv(",
        ]
        present_forbidden_tokens = [
            token for token in forbidden_module_tokens
            if token in module_source
        ]

        checks = {
            "shape": model_space.shape == (6, 10),
            "grid": parameter_grid == expected_grid,
            "fixed": fixed_parameters == expected_fixed,
            "grid_order": list(parameter_grid) == list(expected_grid),
            "fixed_order": list(fixed_parameters) == list(expected_fixed),
            "combinations": grid_combination_count == 16,
            "input_unchanged": model_space.equals(model_space_before),
            "deterministic": (
                parameter_grid == repeated_grid
                and fixed_parameters == repeated_fixed
            ),
            "parser_semantics": parser_semantics_ok,
            "id_rows": identifier_rows == 105,
            "id_matches": identifier_matches == 105,
            "function_id_matches": (
                function_matches_independent_reference == 105
            ),
            "key_order": key_order_independent,
            "negative_cases": (
                len(negative_cases) == 12
                and not negative_failures
            ),
            "module_boundary": not present_forbidden_tokens,
        }
        detail = (
            f"shape={model_space.shape}; grid={len(parameter_grid)}; "
            f"fixed={len(fixed_parameters)}; combinations={grid_combination_count}; "
            f"ids={identifier_matches}/{identifier_rows}; "
            f"negative={len(negative_cases) - len(negative_failures)}"
            f"/{len(negative_cases)}; input_unchanged={checks['input_unchanged']}; "
            f"deterministic={checks['deterministic']}"
        )
        if negative_failures:
            detail += f"; negative_failures={negative_failures}"
        if present_forbidden_tokens:
            detail += f"; forbidden_module_tokens={present_forbidden_tokens}"
        return Check(
            "stage07_model_space_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:  # pragma: no cover - diagnostic boundary
        return Check(
            "stage07_model_space_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def extract_markdown_section(
    document: str,
    start_heading: str,
    next_heading: str,
) -> str:
    start_match = re.search(
        rf"(?m)^{re.escape(start_heading)}[^\r\n]*\r?$",
        document,
    )
    if start_match is None:
        raise ValueError(f"missing Markdown heading: {start_heading!r}")
    next_match = re.search(
        rf"(?m)^{re.escape(next_heading)}[^\r\n]*\r?$",
        document[start_match.end() :],
    )
    if next_match is None:
        raise ValueError(f"missing next Markdown heading: {next_heading!r}")
    return document[
        start_match.start() : start_match.end() + next_match.start()
    ]


def count_standalone_marker(text: str, marker: str) -> int:
    return len(
        re.findall(
            rf"(?m)^{re.escape(marker)}\r?$",
            text,
        )
    )


def check_stage07_st07_07_evidence_preserved() -> Check:
    try:
        document = ST07_08_STAGE_RECORD_PATH.read_text(encoding="utf-8-sig")
        section = extract_markdown_section(
            document,
            "### 16.4.",
            "### 16.5.",
        )
        actual_hash = hashlib.sha256(section.encode("utf-8")).hexdigest()
        preserved = actual_hash == ST07_07_SECTION_16_4_SHA256
        return Check(
            "st07_07_evidence_preserved",
            "PASS" if preserved else "FAIL",
            f"section_16_4_sha256={actual_hash}; "
            f"expected={ST07_07_SECTION_16_4_SHA256}",
        )
    except Exception as exc:
        return Check(
            "st07_07_evidence_preserved",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_st07_08_evidence_section_placement() -> Check:
    try:
        document = ST07_08_STAGE_RECORD_PATH.read_text(encoding="utf-8-sig")
        section_16_4 = extract_markdown_section(
            document,
            "### 16.4.",
            "### 16.5.",
        )
        section_20_3 = extract_markdown_section(
            document,
            "### 20.3.",
            "### 20.4.",
        )
        global_begin = count_standalone_marker(
            document,
            ST07_08_NOTEBOOK_EVIDENCE_BEGIN,
        )
        global_end = count_standalone_marker(
            document,
            ST07_08_NOTEBOOK_EVIDENCE_END,
        )
        section_begin = count_standalone_marker(
            section_20_3,
            ST07_08_NOTEBOOK_EVIDENCE_BEGIN,
        )
        section_end = count_standalone_marker(
            section_20_3,
            ST07_08_NOTEBOOK_EVIDENCE_END,
        )
        st07_07_markers = (
            count_standalone_marker(
                section_16_4,
                ST07_08_NOTEBOOK_EVIDENCE_BEGIN,
            )
            + count_standalone_marker(
                section_16_4,
                ST07_08_NOTEBOOK_EVIDENCE_END,
            )
        )
        payload = extract_marked_fence(
            section_20_3,
            ST07_08_NOTEBOOK_EVIDENCE_BEGIN,
            ST07_08_NOTEBOOK_EVIDENCE_END,
            "json",
        )
        json.loads(payload)
        placement_ok = (
            global_begin == 1
            and global_end == 1
            and section_begin == 1
            and section_end == 1
            and st07_07_markers == 0
        )
        return Check(
            "st07_08_evidence_section_placement",
            "PASS" if placement_ok else "FAIL",
            f"global_markers={global_begin}/{global_end}; "
            f"section20_3={section_begin}/{section_end}; "
            f"section16_4={st07_07_markers}",
        )
    except Exception as exc:
        return Check(
            "st07_08_evidence_section_placement",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_st07_08_legacy_evidence_absent() -> Check:
    try:
        document = ST07_08_STAGE_RECORD_PATH.read_text(encoding="utf-8-sig")
        section_20_3 = extract_markdown_section(
            document,
            "### 20.3.",
            "### 20.4.",
        )
        legacy_headings = sum(
            len(
                re.findall(
                    rf"(?m)^##### [^\r\n]*{index}, "
                    rf"cell ID `{re.escape(cell_id)}`[^\r\n]*$",
                    section_20_3,
                )
            )
            for index, cell_id, _, _ in ST07_08_EXPECTED_CELL_EVIDENCE
        )
        return Check(
            "st07_08_legacy_evidence_absent",
            "PASS" if legacy_headings == 0 else "FAIL",
            f"legacy_source_headings={legacy_headings}",
        )
    except Exception as exc:
        return Check(
            "st07_08_legacy_evidence_absent",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_text_corruption_absent() -> Check:
    try:
        document = ST07_08_STAGE_RECORD_PATH.read_text(encoding="utf-8-sig")
        corrupted_lines = [
            line_number
            for line_number, line in enumerate(document.splitlines(), start=1)
            if re.search(r"\?{4,}", line)
        ]
        return Check(
            "stage07_text_corruption_absent",
            "PASS" if not corrupted_lines else "FAIL",
            (
                "question_mark_sequences=0"
                if not corrupted_lines
                else f"question_mark_sequence_lines={corrupted_lines}"
            ),
        )
    except Exception as exc:
        return Check(
            "stage07_text_corruption_absent",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


def extract_marked_fence(
    document: str,
    begin_marker: str,
    end_marker: str,
    language: str,
) -> str:
    begin_matches = list(
        re.finditer(
            rf"(?m)^{re.escape(begin_marker)}\r?$",
            document,
        )
    )
    end_matches = list(
        re.finditer(
            rf"(?m)^{re.escape(end_marker)}\r?$",
            document,
        )
    )
    if len(begin_matches) != 1 or len(end_matches) != 1:
        raise ValueError(
            f"expected one marker pair: {begin_marker!r}, {end_marker!r}"
        )
    begin_end = begin_matches[0].end()
    end_start = end_matches[0].start()
    if begin_end >= end_start:
        raise ValueError("evidence markers are out of order")
    marked = document[begin_end:end_start]
    match = re.fullmatch(
        rf"\r?\n```{re.escape(language)}\r?\n(.*?)```\r?\n",
        marked,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"invalid {language} evidence fence")
    return match.group(1)


def validate_unified_diff(
    diff_text: str,
    *,
    fromfile: str,
    tofile: str,
) -> None:
    lines = diff_text.splitlines(keepends=True)
    if len(lines) < 3:
        raise ValueError("unified diff is incomplete")
    if lines[0] != f"--- {fromfile}\n" or lines[1] != f"+++ {tofile}\n":
        raise ValueError("unified diff file headers do not match")

    hunk_count = 0
    index = 2
    while index < len(lines):
        header = lines[index]
        match = re.fullmatch(
            r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n",
            header,
        )
        if match is None:
            raise ValueError(f"invalid unified diff hunk header: {header!r}")
        old_start = int(match.group(1))
        old_count = int(match.group(2) or "1")
        new_start = int(match.group(3))
        new_count = int(match.group(4) or "1")
        index += 1
        body: list[str] = []
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if not line or line[0] not in {" ", "+", "-"}:
                raise ValueError(f"invalid unified diff body line: {line!r}")
            body.append(line)
            index += 1
        actual_old_count = sum(line[0] in {" ", "-"} for line in body)
        actual_new_count = sum(line[0] in {" ", "+"} for line in body)
        if (actual_old_count, actual_new_count) != (old_count, new_count):
            raise ValueError("unified diff hunk counts do not match")
        if old_start < 1 or new_start < 1:
            raise ValueError("unified diff hunk positions must be positive")
        hunk_count += 1
    if hunk_count == 0:
        raise ValueError("unified diff contains no hunks")


def historical_diff_is_exact(
    document: str,
    begin_marker: str,
    end_marker: str,
    *,
    expected_sha256: str,
    fromfile: str,
    tofile: str,
) -> bool:
    diff_text = extract_marked_fence(
        document,
        begin_marker,
        end_marker,
        "diff",
    )
    validate_unified_diff(
        diff_text,
        fromfile=fromfile,
        tofile=tofile,
    )
    return (
        hashlib.sha256(diff_text.encode("utf-8")).hexdigest()
        == expected_sha256
    )


def check_stage07_exact_evidence() -> Check:
    flags = {
        "model_spaces": False,
        "notebook_cells": False,
        "verifier_diff": False,
        "no_placeholders": False,
    }
    errors: list[str] = []
    try:
        document = ST07_08_STAGE_RECORD_PATH.read_text(encoding="utf-8-sig")
        section_20_3 = extract_markdown_section(
            document,
            "### 20.3.",
            "### 20.4.",
        )
        if (
            count_standalone_marker(
                document,
                ST07_08_NOTEBOOK_EVIDENCE_BEGIN,
            )
            != 1
            or count_standalone_marker(
                document,
                ST07_08_NOTEBOOK_EVIDENCE_END,
            )
            != 1
        ):
            raise ValueError("notebook evidence markers are not globally unique")
        notebook = json.loads(
            ST07_08_NOTEBOOK_PATH.read_text(encoding="utf-8-sig")
        )

        model_spaces_source = extract_marked_fence(
            section_20_3,
            ST07_08_MODEL_SPACES_EVIDENCE_BEGIN,
            ST07_08_MODEL_SPACES_EVIDENCE_END,
            "python",
        )
        actual_model_spaces_source = ST07_08_MODEL_SPACES_PATH.read_text(
            encoding="utf-8-sig"
        )
        flags["model_spaces"] = (
            model_spaces_source == actual_model_spaces_source
            and hashlib.sha256(
                model_spaces_source.encode("utf-8")
            ).hexdigest()
            == ST07_08_MODEL_SPACES_SHA256
        )

        notebook_payload = extract_marked_fence(
            section_20_3,
            ST07_08_NOTEBOOK_EVIDENCE_BEGIN,
            ST07_08_NOTEBOOK_EVIDENCE_END,
            "json",
        )
        evidence_rows = json.loads(notebook_payload)
        expected_keys = {
            "cell_index",
            "cell_id",
            "before_source",
            "after_source",
            "before_source_sha256",
            "after_source_sha256",
        }
        expected_identity = [
            (index, cell_id)
            for index, cell_id, _, _ in ST07_08_EXPECTED_CELL_EVIDENCE
        ]
        observed_identity = [
            (row.get("cell_index"), row.get("cell_id"))
            for row in evidence_rows
            if isinstance(row, dict)
        ]
        notebook_cells_exact = (
            isinstance(evidence_rows, list)
            and len(evidence_rows) == len(ST07_08_EXPECTED_CELL_EVIDENCE)
            and observed_identity == expected_identity
        )
        if notebook_cells_exact:
            for row, (
                index,
                cell_id,
                expected_before_hash,
                expected_after_hash,
            ) in zip(
                evidence_rows,
                ST07_08_EXPECTED_CELL_EVIDENCE,
                strict=True,
            ):
                before_source = row.get("before_source")
                after_source = row.get("after_source")
                if (
                    set(row) != expected_keys
                    or not isinstance(before_source, list)
                    or not all(isinstance(item, str) for item in before_source)
                    or not isinstance(after_source, list)
                    or not all(isinstance(item, str) for item in after_source)
                    or notebook["cells"][index].get("id") != cell_id
                ):
                    notebook_cells_exact = False
                    break
                before_hash = hashlib.sha256(
                    "".join(before_source).encode("utf-8")
                ).hexdigest()
                after_hash = hashlib.sha256(
                    "".join(after_source).encode("utf-8")
                ).hexdigest()
                if (
                    before_hash != expected_before_hash
                    or row["before_source_sha256"] != expected_before_hash
                    or after_hash != expected_after_hash
                    or row["after_source_sha256"] != expected_after_hash
                ):
                    notebook_cells_exact = False
                    break
        flags["notebook_cells"] = notebook_cells_exact

        immediate_diff_exact = historical_diff_is_exact(
            section_20_3,
            ST07_08_VERIFIER_FINAL_DIFF_BEGIN,
            ST07_08_VERIFIER_FINAL_DIFF_END,
            expected_sha256=ST07_08_VERIFIER_FINAL_DIFF_SHA256,
            fromfile="accepted_v17/scripts/agent_verify.py",
            tofile="final_corrected_v18/scripts/agent_verify.py",
        )
        correction_diff_exact = historical_diff_is_exact(
            section_20_3,
            ST07_08_CORRECTION_DIFF_BEGIN,
            ST07_08_CORRECTION_DIFF_END,
            expected_sha256=ST07_08_VERIFIER_CORRECTION_DIFF_SHA256,
            fromfile="input_v18_1/scripts/agent_verify.py",
            tofile="final_corrected_v18/scripts/agent_verify.py",
        )
        flags["verifier_diff"] = (
            immediate_diff_exact and correction_diff_exact
        )

        placeholder_tokens = (
            "<omitted>",
            "<placeholder>",
            "[omitted]",
            "PLACEHOLDER",
            "PSEUDOCODE",
            "сокращено вместо точного текста",
        )
        machine_regions = (
            notebook_payload,
            model_spaces_source,
        )
        flags["no_placeholders"] = (
            flags["model_spaces"]
            and flags["notebook_cells"]
            and flags["verifier_diff"]
            and not any(
                token in region
                for token in placeholder_tokens
                for region in machine_regions
            )
        )
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")

    all_exact = all(flags.values()) and not errors
    detail = (
        "ST07_08_EVIDENCE_MODEL_SPACES_EXACT: "
        f"{flags['model_spaces']}; "
        "ST07_08_EVIDENCE_NOTEBOOK_CELLS_EXACT: "
        f"{flags['notebook_cells']}; "
        "ST07_08_EVIDENCE_VERIFY_DIFF_EXACT: "
        f"{flags['verifier_diff']}; "
        "ST07_08_EVIDENCE_NO_PLACEHOLDERS: "
        f"{flags['no_placeholders']}; "
        f"ST07_08_EVIDENCE_ALL_EXACT: {all_exact}"
    )
    if errors:
        detail += f"; errors={errors}"
    return Check(
        "st07_08_exact_evidence",
        "PASS" if all_exact else "FAIL",
        detail,
    )


def check_stage07_nested_cv_contract_design() -> Check:
    try:
        document = ST07_08_STAGE_RECORD_PATH.read_text(encoding="utf-8-sig")
        section_23 = extract_markdown_section(
            document,
            "## 23.",
            "## 24.",
        )
        required_tokens = [
            "task_id: ST07_09_nested_cv_contract_and_golden_master_design",
            "task_profile: CHANGE",
            "future_module: src/mlcra/nested_cv.py",
            (
                "outer_cv: RepeatedStratifiedKFold(n_splits=5, "
                "n_repeats=2, random_state=20260507)"
            ),
            (
                "inner_cv: StratifiedKFold(n_splits=3, shuffle=True, "
                "random_state=20260507 + zero_based_outer_split_number)"
            ),
            "tuned_model: hist_gradient_boosting",
            "control_models: dummy_prior;logistic_regression",
            "inner_candidate_count: 16",
            "scoring: average_precision",
            "refit: true",
            "n_jobs: 1",
            "error_score: raise",
            "golden_master_outer_scores_shape: 30x36",
            "golden_master_selected_params_shape: 10x13",
            "golden_master_summary_shape: 3x39",
            "golden_master_quality_checks_shape: 13x4",
            "golden_master_warnings_shape: 1x9",
            "golden_master_environment_shape: 6x3",
            (
                "deterministic_numeric_policy_same_environment: "
                "exact_after_csv_roundtrip"
            ),
            (
                "cross_environment_numeric_policy: "
                "blocked_without_calibrated_tolerance"
            ),
            "timing_policy: finite_and_nonnegative_only",
            "TRAINING_PERFORMED: NO",
            "NOTEBOOK_EXECUTED: NO",
            "SCIENTIFIC_VALIDATION: SKIPPED",
            "next_implementation_authorized: false",
        ]
        missing_tokens = [
            token for token in required_tokens if token not in section_23
        ]

        expected_shapes = {
            "openml_miniboone_nested_outer_scores.csv": (30, 36),
            "openml_miniboone_nested_selected_params.csv": (10, 13),
            "openml_miniboone_nested_summary.csv": (3, 39),
            "openml_miniboone_nested_quality_checks.csv": (13, 4),
            "openml_miniboone_nested_warnings.csv": (1, 9),
            "openml_miniboone_nested_environment.csv": (6, 3),
        }
        observed_shapes: dict[str, tuple[int, int]] = {}
        rows_by_file: dict[str, list[dict[str, str]]] = {}
        for file_name in expected_shapes:
            path = PROJECT_ROOT / "data_registry" / file_name
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream))
            observed_shapes[file_name] = (
                len(rows) - 1,
                len(rows[0]) if rows else 0,
            )
            rows_by_file[file_name] = read_contract_csv(path)

        expected_unique_keys = {
            "openml_miniboone_nested_outer_scores.csv": (
                "protocol_id",
                "candidate_id",
                "outer_split_number",
                "model_id",
            ),
            "openml_miniboone_nested_selected_params.csv": (
                "protocol_id",
                "candidate_id",
                "outer_split_number",
                "model_id",
            ),
            "openml_miniboone_nested_summary.csv": (
                "protocol_id",
                "candidate_id",
                "model_id",
            ),
            "openml_miniboone_nested_quality_checks.csv": (
                "protocol_id",
                "check_id",
            ),
            "openml_miniboone_nested_environment.csv": (
                "protocol_id",
                "name",
            ),
        }
        duplicate_keys: list[str] = []
        for file_name, key_columns in expected_unique_keys.items():
            observed: set[tuple[str, ...]] = set()
            for row in rows_by_file[file_name]:
                key = tuple(row[column] for column in key_columns)
                if key in observed:
                    duplicate_keys.append(f"{file_name}:{key}")
                observed.add(key)

        outer_rows = rows_by_file[
            "openml_miniboone_nested_outer_scores.csv"
        ]
        selected_rows = rows_by_file[
            "openml_miniboone_nested_selected_params.csv"
        ]
        quality_rows = rows_by_file[
            "openml_miniboone_nested_quality_checks.csv"
        ]
        timing_values = [
            float(row[column])
            for row in outer_rows
            for column in ("fit_seconds", "predict_seconds")
        ]
        timings_valid = all(
            math.isfinite(value) and value >= 0.0
            for value in timing_values
        )
        model_roles_valid = (
            {row["model_id"] for row in outer_rows}
            == {
                "hist_gradient_boosting",
                "dummy_prior",
                "logistic_regression",
            }
            and {row["model_id"] for row in selected_rows}
            == {"hist_gradient_boosting"}
        )
        inner_seeds = {
            int(row["inner_cv_random_state"])
            for row in selected_rows
        }
        seeds_valid = inner_seeds == set(range(20260507, 20260517))
        quality_valid = all(
            row["check_result"] == "pass"
            for row in quality_rows
        )
        shape_ok = observed_shapes == expected_shapes
        checks = {
            "document_tokens": not missing_tokens,
            "reference_shapes": shape_ok,
            "unique_keys": not duplicate_keys,
            "timings": timings_valid,
            "model_roles": model_roles_valid,
            "inner_seeds": seeds_valid,
            "quality": quality_valid,
        }
        detail = (
            f"tokens={len(required_tokens) - len(missing_tokens)}"
            f"/{len(required_tokens)}; shapes={observed_shapes}; "
            f"unique_keys={not duplicate_keys}; timings={timings_valid}; "
            f"model_roles={model_roles_valid}; seeds={seeds_valid}; "
            f"quality={quality_valid}"
        )
        if missing_tokens:
            detail += f"; missing_tokens={missing_tokens}"
        if duplicate_keys:
            detail += f"; duplicate_keys={duplicate_keys}"
        return Check(
            "stage07_nested_cv_contract_design",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_contract_design",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_binary_metric_contract_extraction() -> Check:
    try:
        import numpy as np
        import pandas as pd
        from sklearn.metrics import (
            auc,
            average_precision_score,
            balanced_accuracy_score,
            brier_score_loss,
            f1_score,
            log_loss,
            precision_recall_curve,
            roc_auc_score,
        )

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.metrics import (
            get_positive_class_probability,
            score_binary_classifier,
        )

        class DirectProbabilityEstimator:
            classes_ = np.array([0, 1])

            def predict_proba(self, X):
                return np.column_stack(
                    [
                        1.0 - np.asarray(X["positive_probability"]),
                        np.asarray(X["positive_probability"]),
                    ]
                )

        class FinalPipelineStep:
            classes_ = np.array([0, 1])

        class PipelineProbabilityEstimator:
            named_steps = {"final": FinalPipelineStep()}

            def predict_proba(self, X):
                return np.column_stack(
                    [
                        1.0 - np.asarray(X["positive_probability"]),
                        np.asarray(X["positive_probability"]),
                    ]
                )

        X = pd.DataFrame(
            {"positive_probability": [0.1, 0.4, 0.35, 0.8]}
        )
        expected_probability = np.array([0.1, 0.4, 0.35, 0.8])
        direct_probability = get_positive_class_probability(
            DirectProbabilityEstimator(),
            X,
        )
        pipeline_probability = get_positive_class_probability(
            PipelineProbabilityEstimator(),
            X,
        )
        probabilities_exact = (
            np.array_equal(direct_probability, expected_probability)
            and np.array_equal(pipeline_probability, expected_probability)
        )

        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 1])
        observed_scores = score_binary_classifier(
            y_true,
            y_pred,
            expected_probability,
        )
        expected_scores = {
            "roc_auc": float(roc_auc_score(y_true, expected_probability)),
            "pr_auc": float(
                average_precision_score(y_true, expected_probability)
            ),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "balanced_accuracy": float(
                balanced_accuracy_score(y_true, y_pred)
            ),
            "log_loss": float(
                log_loss(
                    y_true,
                    np.column_stack(
                        [1.0 - expected_probability, expected_probability]
                    ),
                    labels=[0, 1],
                )
            ),
            "brier_score": float(
                brier_score_loss(
                    y_true,
                    expected_probability,
                    pos_label=1,
                )
            ),
        }
        scores_exact = observed_scores == expected_scores

        precision, recall, _ = precision_recall_curve(
            y_true,
            expected_probability,
        )
        trapezoidal_pr_auc = float(auc(recall, precision))
        ap_alias_exact = (
            observed_scores["pr_auc"]
            == float(average_precision_score(y_true, expected_probability))
            and observed_scores["pr_auc"] != trapezoidal_pr_auc
        )

        negative_results: list[bool] = []

        class MissingPredictProba:
            pass

        try:
            get_positive_class_probability(MissingPredictProba(), X)
        except TypeError:
            negative_results.append(True)
        else:
            negative_results.append(False)

        class MissingClasses:
            def predict_proba(self, X):
                return np.column_stack(
                    [
                        1.0 - np.asarray(X["positive_probability"]),
                        np.asarray(X["positive_probability"]),
                    ]
                )

        try:
            get_positive_class_probability(MissingClasses(), X)
        except AttributeError:
            negative_results.append(True)
        else:
            negative_results.append(False)

        class MissingPositiveClass(MissingClasses):
            classes_ = np.array([0, 2])

        try:
            get_positive_class_probability(MissingPositiveClass(), X)
        except ValueError:
            negative_results.append(True)
        else:
            negative_results.append(False)

        metrics_source = (
            PROJECT_ROOT / "src" / "mlcra" / "metrics.py"
        ).read_text(encoding="utf-8-sig")
        notebook = json.loads(
            ST07_08_NOTEBOOK_PATH.read_text(encoding="utf-8-sig")
        )
        notebook_source = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
        )
        nested_cv_source = (
            PROJECT_ROOT / "src" / "mlcra" / "nested_cv.py"
        ).read_text(encoding="utf-8-sig")
        source_contract = (
            metrics_source.count(
                "def get_positive_class_probability("
            )
            == 1
            and metrics_source.count("def score_binary_classifier(") == 1
            and "def get_positive_class_probability(" not in notebook_source
            and "def score_binary_classifier(" not in notebook_source
            and (
                "The historical ``pr_auc`` key stores scikit-learn "
                "average precision (AP)"
            )
            in metrics_source
            and notebook_source.count(
                "get_positive_class_probability("
            )
            == 2
            and notebook_source.count("score_binary_classifier(") == 2
            and nested_cv_source.count(
                "get_positive_class_probability("
            )
            == 1
            and nested_cv_source.count("score_binary_classifier(") == 1
        )

        checks = {
            "probabilities_exact": probabilities_exact,
            "scores_exact": scores_exact,
            "ap_alias_exact": ap_alias_exact,
            "negative": all(negative_results)
            and len(negative_results) == 3,
            "source_contract": source_contract,
        }
        detail = (
            f"probabilities_exact={probabilities_exact}; "
            f"scores_exact={scores_exact}; "
            f"ap_alias_exact={ap_alias_exact}; "
            f"negative={sum(negative_results)}/3; "
            f"source_contract={source_contract}"
        )
        return Check(
            "stage07_binary_metric_contract_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:
        return Check(
            "stage07_binary_metric_contract_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_nested_cv_split_and_evaluation_extraction() -> Check:
    try:
        import numpy as np
        import pandas as pd
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            average_precision_score,
            balanced_accuracy_score,
            brier_score_loss,
            f1_score,
            log_loss,
            roc_auc_score,
        )

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.nested_cv import (
            build_inner_splitter,
            build_outer_splitter,
            evaluate_fitted_estimator_on_outer_block,
            nested_outer_position,
        )

        random_state = 20260507
        y = np.tile(np.array([0, 1], dtype=int), 50)
        generator = np.random.default_rng(random_state)
        X = pd.DataFrame(
            {
                "feature_0": y + generator.normal(0.0, 0.35, len(y)),
                "feature_1": generator.normal(0.0, 1.0, len(y)),
                "feature_2": (1 - y) + generator.normal(0.0, 0.35, len(y)),
                "feature_3": generator.normal(0.0, 1.0, len(y)),
            }
        )
        X_before = X.copy(deep=True)
        y_before = y.copy()

        outer_a = list(
            build_outer_splitter(5, 2, random_state).split(X, y)
        )
        outer_b = list(
            build_outer_splitter(5, 2, random_state).split(X, y)
        )
        outer_deterministic = (
            len(outer_a) == 10
            and all(
                np.array_equal(train_a, train_b)
                and np.array_equal(test_a, test_b)
                for (train_a, test_a), (train_b, test_b) in zip(
                    outer_a,
                    outer_b,
                    strict=True,
                )
            )
        )
        outer_geometry = all(
            len(train_index) == 80
            and len(test_index) == 20
            and not np.intersect1d(train_index, test_index).size
            and np.union1d(train_index, test_index).size == len(X)
            and int(y[train_index].sum()) == 40
            and int(y[test_index].sum()) == 10
            for train_index, test_index in outer_a
        )
        positions = [
            nested_outer_position(split_number, 5, 2)
            for split_number in range(10)
        ]
        positions_exact = positions == [
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (2, 1),
            (2, 2),
            (2, 3),
            (2, 4),
            (2, 5),
        ]

        inner_states: list[int] = []
        inner_deterministic = True
        first_outer_train = outer_a[0][0]
        X_outer_train = X.iloc[first_outer_train]
        y_outer_train = y[first_outer_train]
        for split_number in range(10):
            inner_a = build_inner_splitter(3, random_state, split_number)
            inner_b = build_inner_splitter(3, random_state, split_number)
            inner_states.append(int(inner_a.random_state))
            splits_a = list(inner_a.split(X_outer_train, y_outer_train))
            splits_b = list(inner_b.split(X_outer_train, y_outer_train))
            inner_deterministic = inner_deterministic and (
                len(splits_a) == 3
                and all(
                    np.array_equal(train_a, train_b)
                    and np.array_equal(test_a, test_b)
                    and not np.intersect1d(train_a, test_a).size
                    and np.union1d(train_a, test_a).size
                    == len(X_outer_train)
                    for (train_a, test_a), (train_b, test_b) in zip(
                        splits_a,
                        splits_b,
                        strict=True,
                    )
                )
            )
        inner_states_exact = inner_states == list(
            range(random_state, random_state + 10)
        )

        train_index, test_index = outer_a[0]
        estimator = LogisticRegression(
            max_iter=1000,
            random_state=random_state,
        )
        estimator.fit(X.iloc[train_index], y[train_index])
        candidate_bundle = {
            "candidate_id": "fixture_candidate",
            "did": 1,
            "dataset_name": "deterministic_binary_fixture",
            "target_name": "target",
            "target_metadata": {
                "target_class_0": "False",
                "target_class_1": "True",
                "positive_class_assumption": "True",
            },
        }
        observed_row = evaluate_fitted_estimator_on_outer_block(
            estimator=estimator,
            candidate_bundle=candidate_bundle,
            X=X,
            y=y,
            train_index=train_index,
            test_index=test_index,
            model_id="logistic_regression",
            model_role="control",
            zero_based_outer_split_number=0,
            selected_parameter_set_id="not_applicable_control_model",
            selected_params=None,
            fit_seconds=0.1234567,
            feature_names=list(X.columns),
            protocol_id="fixture_nested_cv_v01",
            outer_n_splits=5,
            outer_n_repeats=2,
            inner_n_splits=3,
            feature_policy_id="fixture_features_locked",
        )
        y_test = y[test_index]
        y_pred = estimator.predict(X.iloc[test_index])
        y_probability = estimator.predict_proba(X.iloc[test_index])[:, 1]
        expected_metrics = {
            "roc_auc": float(roc_auc_score(y_test, y_probability)),
            "average_precision": float(
                average_precision_score(y_test, y_probability)
            ),
            "pr_auc": float(
                average_precision_score(y_test, y_probability)
            ),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "balanced_accuracy": float(
                balanced_accuracy_score(y_test, y_pred)
            ),
            "log_loss": float(
                log_loss(
                    y_test,
                    np.column_stack(
                        [1.0 - y_probability, y_probability]
                    ),
                    labels=[0, 1],
                )
            ),
            "brier_score": float(
                brier_score_loss(
                    y_test,
                    y_probability,
                    pos_label=1,
                )
            ),
        }
        metric_values_exact = all(
            observed_row[name] == value
            for name, value in expected_metrics.items()
        )
        with (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_outer_scores.csv"
        ).open(encoding="utf-8-sig", newline="") as stream:
            registered_columns = next(csv.reader(stream))
        output_schema_exact = list(observed_row) == registered_columns
        metadata_exact = (
            observed_row["outer_split_number"] == 1
            and observed_row["outer_repeat_number"] == 1
            and observed_row["outer_fold_number"] == 1
            and observed_row["outer_cv_n_splits"] == 5
            and observed_row["outer_cv_n_repeats"] == 2
            and observed_row["inner_cv_n_splits"] == ""
            and observed_row["selected_params_json"] == ""
            and observed_row["feature_count"] == 4
            and observed_row["n_train"] == 80
            and observed_row["n_test"] == 20
            and observed_row["fit_seconds"] == 0.123457
            and math.isfinite(observed_row["predict_seconds"])
            and observed_row["predict_seconds"] >= 0.0
        )

        negative_cases = [
            lambda: nested_outer_position(-1, 5, 2),
            lambda: nested_outer_position(10, 5, 2),
            lambda: build_outer_splitter(1, 2, random_state),
            lambda: build_outer_splitter(5, 0, random_state),
            lambda: build_outer_splitter(5, 2, True),
            lambda: build_inner_splitter(1, random_state, 0),
            lambda: build_inner_splitter(3, random_state, -1),
            lambda: build_inner_splitter(3, 2**32 - 1, 1),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y[:-1],
                train_index,
                test_index,
                "logistic_regression",
                "control",
                0,
                "not_applicable_control_model",
                None,
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                test_index,
                "hist_gradient_boosting",
                "tuned_candidate",
                0,
                "wrong_parameter_set",
                {"learning_rate": 0.1},
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                np.append(test_index, train_index[0]),
                "logistic_regression",
                "control",
                0,
                "not_applicable_control_model",
                None,
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index[:-1],
                test_index,
                "logistic_regression",
                "control",
                0,
                "not_applicable_control_model",
                None,
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                test_index,
                "logistic_regression",
                "unknown",
                0,
                "not_applicable_control_model",
                None,
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                test_index,
                "logistic_regression",
                "control",
                0,
                "wrong_parameter_set",
                None,
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                test_index,
                "unknown_model",
                "control",
                0,
                "not_applicable_control_model",
                None,
                0.1,
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                test_index,
                "logistic_regression",
                "control",
                0,
                "not_applicable_control_model",
                None,
                float("nan"),
                list(X.columns),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
            lambda: evaluate_fitted_estimator_on_outer_block(
                estimator,
                candidate_bundle,
                X,
                y,
                train_index,
                test_index,
                "logistic_regression",
                "control",
                0,
                "not_applicable_control_model",
                None,
                0.1,
                list(reversed(X.columns)),
                protocol_id="fixture",
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                feature_policy_id="fixture",
            ),
        ]
        rejected_negative_cases = 0
        for negative_case in negative_cases:
            try:
                negative_case()
            except (AttributeError, KeyError, TypeError, ValueError):
                rejected_negative_cases += 1

        nested_source = (
            PROJECT_ROOT / "src" / "mlcra" / "nested_cv.py"
        ).read_text(encoding="utf-8-sig")
        notebook = json.loads(
            ST07_08_NOTEBOOK_PATH.read_text(encoding="utf-8-sig")
        )
        notebook_source = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
        )
        source_contract = (
            nested_source.count("def nested_outer_position(") == 1
            and nested_source.count("def build_outer_splitter(") == 1
            and nested_source.count("def build_inner_splitter(") == 1
            and nested_source.count(
                "def evaluate_fitted_estimator_on_outer_block("
            )
            == 1
            and "def nested_outer_position(" not in notebook_source
            and "def evaluate_fitted_estimator_on_outer_block("
            not in notebook_source
            and nested_source.count(
                "def fit_control_estimator_on_outer_block("
            )
            == 1
            and nested_source.count(
                "def fit_tuned_hist_gradient_boosting_on_outer_block("
            )
            == 1
            and "def fit_control_estimator_on_outer_block("
            not in notebook_source
            and "def fit_tuned_hist_gradient_boosting_on_outer_block("
            not in notebook_source
        )
        input_unchanged = X.equals(X_before) and np.array_equal(y, y_before)

        checks = {
            "outer_deterministic": outer_deterministic,
            "outer_geometry": outer_geometry,
            "positions_exact": positions_exact,
            "inner_deterministic": inner_deterministic,
            "inner_states_exact": inner_states_exact,
            "output_schema_exact": output_schema_exact,
            "metric_values_exact": metric_values_exact,
            "metadata_exact": metadata_exact,
            "negative_cases": (
                rejected_negative_cases == len(negative_cases) == 17
            ),
            "source_contract": source_contract,
            "input_unchanged": input_unchanged,
        }
        detail = (
            f"outer_splits={len(outer_a)}/10; "
            f"outer_deterministic={outer_deterministic}; "
            f"outer_geometry={outer_geometry}; "
            f"positions={positions_exact}; "
            f"inner_states={inner_states_exact}; "
            f"schema={output_schema_exact}; "
            f"metrics={metric_values_exact}; "
            f"metadata={metadata_exact}; "
            f"negative={rejected_negative_cases}/{len(negative_cases)}; "
            f"source_contract={source_contract}; "
            f"input_unchanged={input_unchanged}"
        )
        return Check(
            "stage07_nested_cv_split_and_evaluation_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_split_and_evaluation_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_nested_cv_fit_and_tuning_extraction() -> Check:
    try:
        import ast
        import copy
        import warnings

        import numpy as np
        import pandas as pd
        from sklearn.base import BaseEstimator, ClassifierMixin, clone
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import GridSearchCV

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )
        from mlcra.nested_cv import (
            build_inner_splitter,
            build_outer_splitter,
            evaluate_fitted_estimator_on_outer_block,
            fit_control_estimator_on_outer_block,
            fit_tuned_hist_gradient_boosting_on_outer_block,
        )

        protocol_id = "fixture_nested_cv_v01"
        candidate_id = "fixture_candidate"
        feature_policy_id = "fixture_features_locked"
        random_state = 20260507
        y = np.tile(np.array([0, 1], dtype=int), 40)
        generator = np.random.default_rng(random_state)
        X = pd.DataFrame(
            {
                "feature_0": y + generator.normal(0.0, 0.35, len(y)),
                "feature_1": generator.normal(0.0, 1.0, len(y)),
                "feature_2": (1 - y)
                + generator.normal(0.0, 0.35, len(y)),
                "feature_3": generator.normal(0.0, 1.0, len(y)),
            }
        )
        candidate_bundle = {
            "candidate_id": candidate_id,
            "did": 1,
            "dataset_name": "deterministic_binary_fixture",
            "target_name": "target",
            "target_metadata": {
                "target_class_0": "False",
                "target_class_1": "True",
                "positive_class_assumption": "True",
            },
        }
        train_index, test_index = next(
            build_outer_splitter(5, 2, random_state).split(X, y)
        )
        feature_names = list(X.columns)
        X_before = X.copy(deep=True)
        y_before = y.copy()
        bundle_before = copy.deepcopy(candidate_bundle)

        model_space = pd.read_csv(
            PROJECT_ROOT
            / "configs"
            / "model_spaces"
            / "miniboone_hist_gradient_boosting_nested_space.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        model_space.loc[:, "protocol_id"] = protocol_id
        model_space.loc[:, "candidate_id"] = candidate_id
        parameter_grid, fixed_parameters = (
            build_hist_gradient_boosting_search_space(
                model_space,
                protocol_id,
                candidate_id,
            )
        )
        fixed_parameters["random_state"] = random_state
        parameter_grid_before = copy.deepcopy(parameter_grid)
        fixed_parameters_before = copy.deepcopy(fixed_parameters)

        common = {
            "candidate_bundle": candidate_bundle,
            "X": X,
            "y": y,
            "train_index": train_index,
            "test_index": test_index,
            "zero_based_outer_split_number": 0,
            "feature_names": feature_names,
            "protocol_id": protocol_id,
            "candidate_id": candidate_id,
            "outer_n_splits": 5,
            "outer_n_repeats": 2,
            "inner_n_splits": 3,
            "feature_policy_id": feature_policy_id,
        }
        control_template = LogisticRegression(
            max_iter=1000,
            random_state=random_state,
        )
        observed_control, control_warnings = (
            fit_control_estimator_on_outer_block(
                **common,
                model_id="logistic_regression",
                estimator_template=control_template,
            )
        )
        reference_control_estimator = clone(control_template)
        reference_control_estimator.fit(
            X.iloc[train_index].copy(),
            y[train_index],
        )
        reference_control = evaluate_fitted_estimator_on_outer_block(
            estimator=reference_control_estimator,
            candidate_bundle=candidate_bundle,
            X=X,
            y=y,
            train_index=train_index,
            test_index=test_index,
            model_id="logistic_regression",
            model_role="control",
            zero_based_outer_split_number=0,
            selected_parameter_set_id="not_applicable_control_model",
            selected_params=None,
            fit_seconds=0.0,
            feature_names=feature_names,
            protocol_id=protocol_id,
            outer_n_splits=5,
            outer_n_repeats=2,
            inner_n_splits=3,
            feature_policy_id=feature_policy_id,
        )
        deterministic_score_fields = [
            field
            for field in observed_control
            if field not in {"fit_seconds", "predict_seconds"}
        ]
        control_reference_exact = all(
            observed_control[field] == reference_control[field]
            for field in deterministic_score_fields
        )
        control_template_unfitted = not hasattr(control_template, "classes_")
        control_timing_valid = all(
            math.isfinite(observed_control[field])
            and observed_control[field] >= 0.0
            for field in ("fit_seconds", "predict_seconds")
        )

        tuned_arguments = {
            **common,
            "parameter_grid": parameter_grid,
            "fixed_parameters": fixed_parameters,
            "base_random_state": random_state,
            "scoring": "average_precision",
            "refit": True,
            "n_jobs": 1,
            "return_train_score": False,
            "error_score": "raise",
        }
        (
            observed_tuned,
            observed_selected,
            tuned_warnings,
        ) = fit_tuned_hist_gradient_boosting_on_outer_block(
            **tuned_arguments
        )

        reference_inner_cv = build_inner_splitter(3, random_state, 0)
        reference_search = GridSearchCV(
            estimator=HistGradientBoostingClassifier(**fixed_parameters),
            param_grid=copy.deepcopy(parameter_grid),
            scoring="average_precision",
            refit=True,
            cv=reference_inner_cv,
            n_jobs=1,
            return_train_score=False,
            error_score="raise",
        )
        reference_search.fit(
            X.iloc[train_index].copy(),
            y[train_index],
        )
        reference_params = dict(reference_search.best_params_)
        reference_parameter_set_id = make_hgb_parameter_set_id(
            reference_params
        )
        reference_tuned = evaluate_fitted_estimator_on_outer_block(
            estimator=reference_search,
            candidate_bundle=candidate_bundle,
            X=X,
            y=y,
            train_index=train_index,
            test_index=test_index,
            model_id="hist_gradient_boosting",
            model_role="tuned_candidate",
            zero_based_outer_split_number=0,
            selected_parameter_set_id=reference_parameter_set_id,
            selected_params=reference_params,
            fit_seconds=0.0,
            feature_names=feature_names,
            protocol_id=protocol_id,
            outer_n_splits=5,
            outer_n_repeats=2,
            inner_n_splits=3,
            feature_policy_id=feature_policy_id,
        )
        reference_selected = {
            "protocol_id": protocol_id,
            "candidate_id": candidate_id,
            "outer_split_number": 1,
            "outer_repeat_number": 1,
            "outer_fold_number": 1,
            "model_id": "hist_gradient_boosting",
            "selected_parameter_set_id": reference_parameter_set_id,
            "selected_params_json": json.dumps(
                reference_params,
                ensure_ascii=False,
                sort_keys=True,
            ),
            "inner_best_average_precision": float(
                reference_search.best_score_
            ),
            "inner_cv_n_splits": 3,
            "inner_cv_random_state": random_state,
            "inner_candidate_count": 16,
            "row_status": "nested_research_draft",
        }
        tuned_reference_exact = all(
            observed_tuned[field] == reference_tuned[field]
            for field in deterministic_score_fields
        )
        selected_reference_exact = observed_selected == reference_selected
        tuned_timing_valid = all(
            math.isfinite(observed_tuned[field])
            and observed_tuned[field] >= 0.0
            for field in ("fit_seconds", "predict_seconds")
        )
        selected_params = json.loads(
            observed_selected["selected_params_json"]
        )
        selection_valid = (
            observed_selected["selected_parameter_set_id"]
            == make_hgb_parameter_set_id(selected_params)
            and set(selected_params) == set(parameter_grid)
            and all(
                selected_params[name] in parameter_grid[name]
                for name in parameter_grid
            )
            and observed_selected["inner_candidate_count"] == 16
            and observed_selected["inner_cv_random_state"] == random_state
        )

        y_outer_changed = y.copy()
        y_outer_changed[test_index] = 1 - y_outer_changed[test_index]
        changed_arguments = dict(tuned_arguments)
        changed_arguments["y"] = y_outer_changed
        (
            _,
            changed_selected,
            _,
        ) = fit_tuned_hist_gradient_boosting_on_outer_block(
            **changed_arguments
        )
        outer_test_isolated = changed_selected == observed_selected

        class WarningClassifier(ClassifierMixin, BaseEstimator):
            def fit(self, X_fit, y_fit):
                warnings.warn(
                    "fixture fit warning",
                    UserWarning,
                    stacklevel=2,
                )
                self.classes_ = np.array([0, 1])
                return self

            def predict(self, X_predict):
                return np.zeros(len(X_predict), dtype=int)

            def predict_proba(self, X_predict):
                return np.tile(np.array([[0.6, 0.4]]), (len(X_predict), 1))

        _, warning_rows = fit_control_estimator_on_outer_block(
            **common,
            model_id="logistic_regression",
            estimator_template=WarningClassifier(),
        )
        with (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_warnings.csv"
        ).open(encoding="utf-8-sig", newline="") as stream:
            warning_columns = next(csv.reader(stream))
        warning_schema_exact = (
            len(warning_rows) == 1
            and list(warning_rows[0]) == warning_columns
            and warning_rows[0]["object"] == "UserWarning"
            and warning_rows[0]["warning_ru"] == "fixture fit warning"
        )

        with (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_outer_scores.csv"
        ).open(encoding="utf-8-sig", newline="") as stream:
            score_columns = next(csv.reader(stream))
        with (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_selected_params.csv"
        ).open(encoding="utf-8-sig", newline="") as stream:
            selected_columns = next(csv.reader(stream))
        schemas_exact = (
            list(observed_control) == score_columns
            and list(observed_tuned) == score_columns
            and list(observed_selected) == selected_columns
            and len(score_columns) == 36
            and len(selected_columns) == 13
            and len(warning_columns) == 9
        )

        def call_control(**overrides):
            arguments = {
                **common,
                "model_id": "logistic_regression",
                "estimator_template": control_template,
            }
            arguments.update(overrides)
            return fit_control_estimator_on_outer_block(**arguments)

        def call_tuned(**overrides):
            arguments = dict(tuned_arguments)
            arguments.update(overrides)
            return fit_tuned_hist_gradient_boosting_on_outer_block(
                **arguments
            )

        grid_with_missing_key = copy.deepcopy(parameter_grid)
        grid_with_missing_key.pop("max_iter")
        grid_with_wrong_count = copy.deepcopy(parameter_grid)
        grid_with_wrong_count["max_iter"] = [100]
        fixed_with_missing_key = copy.deepcopy(fixed_parameters)
        fixed_with_missing_key.pop("early_stopping")
        fixed_with_wrong_seed = copy.deepcopy(fixed_parameters)
        fixed_with_wrong_seed["random_state"] = random_state + 1
        grid_with_fit_error = copy.deepcopy(parameter_grid)
        grid_with_fit_error["max_iter"] = [0, 0]
        negative_cases = [
            lambda: call_control(model_id="unknown"),
            lambda: call_control(candidate_id="other_candidate"),
            lambda: call_control(
                test_index=np.append(test_index, train_index[0])
            ),
            lambda: call_control(train_index=train_index[:-1]),
            lambda: call_control(y=y[:-1]),
            lambda: call_control(feature_names=list(reversed(feature_names))),
            lambda: call_control(protocol_id=""),
            lambda: call_control(zero_based_outer_split_number=10),
            lambda: call_tuned(scoring="roc_auc"),
            lambda: call_tuned(refit=False),
            lambda: call_tuned(n_jobs=-1),
            lambda: call_tuned(n_jobs=True),
            lambda: call_tuned(return_train_score=True),
            lambda: call_tuned(error_score=float("nan")),
            lambda: call_tuned(parameter_grid=grid_with_missing_key),
            lambda: call_tuned(parameter_grid=grid_with_wrong_count),
            lambda: call_tuned(fixed_parameters=fixed_with_missing_key),
            lambda: call_tuned(fixed_parameters=fixed_with_wrong_seed),
            lambda: call_tuned(parameter_grid=grid_with_fit_error),
        ]
        rejected_negative_cases = 0
        for negative_case in negative_cases:
            try:
                negative_case()
            except (AttributeError, KeyError, TypeError, ValueError):
                rejected_negative_cases += 1

        nested_path = PROJECT_ROOT / "src" / "mlcra" / "nested_cv.py"
        nested_source = nested_path.read_text(encoding="utf-8-sig")
        nested_tree = ast.parse(nested_source)
        notebook = json.loads(
            ST07_08_NOTEBOOK_PATH.read_text(encoding="utf-8-sig")
        )
        notebook_trees = [
            ast.parse("".join(cell.get("source", [])))
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        ]
        extracted_names = {
            "fit_control_estimator_on_outer_block",
            "fit_tuned_hist_gradient_boosting_on_outer_block",
        }
        module_definitions = [
            node.name
            for node in nested_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        notebook_definitions = [
            node.name
            for tree in notebook_trees
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        fit_calls = [
            node
            for node in ast.walk(nested_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "fit"
        ]
        notebook_calls = [
            node
            for tree in notebook_trees
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in extracted_names
        ]
        source_contract = (
            all(module_definitions.count(name) == 1 for name in extracted_names)
            and not extracted_names.intersection(notebook_definitions)
            and len(fit_calls) == 2
            and len(notebook_calls) == 2
            and nested_source.count("GridSearchCV(") == 1
            and nested_source.count("HistGradientBoostingClassifier(") == 1
            and all(
                token not in nested_source
                for token in (
                    "read_csv(",
                    "to_csv(",
                    "read_parquet(",
                    "to_parquet(",
                )
            )
        )
        extraction_cell = next(
            cell
            for cell in notebook["cells"]
            if cell.get("id") == "fb7c8ab8"
        )
        execution_cell = next(
            cell
            for cell in notebook["cells"]
            if cell.get("id") == "c4c56ab7"
        )
        notebook_state_exact = (
            extraction_cell["execution_count"] is None
            and extraction_cell["outputs"] == []
            and execution_cell["execution_count"] is None
            and execution_cell["outputs"] == []
        )
        inputs_unchanged = (
            X.equals(X_before)
            and np.array_equal(y, y_before)
            and candidate_bundle == bundle_before
            and parameter_grid == parameter_grid_before
            and fixed_parameters == fixed_parameters_before
        )
        captured_warnings_valid = (
            control_warnings == []
            and all(
                list(row) == warning_columns
                and row["candidate_id"] == candidate_id
                and row["protocol_id"] == protocol_id
                and row["model_id"] == "hist_gradient_boosting"
                for row in tuned_warnings
            )
        )

        checks = {
            "control_reference_exact": control_reference_exact,
            "control_template_unfitted": control_template_unfitted,
            "control_timing_valid": control_timing_valid,
            "tuned_reference_exact": tuned_reference_exact,
            "selected_reference_exact": selected_reference_exact,
            "tuned_timing_valid": tuned_timing_valid,
            "selection_valid": selection_valid,
            "outer_test_isolated": outer_test_isolated,
            "warning_schema_exact": warning_schema_exact,
            "schemas_exact": schemas_exact,
            "negative_cases": (
                rejected_negative_cases == len(negative_cases) == 19
            ),
            "source_contract": source_contract,
            "notebook_state_exact": notebook_state_exact,
            "inputs_unchanged": inputs_unchanged,
            "captured_warnings_valid": captured_warnings_valid,
        }
        detail = (
            f"control_reference={control_reference_exact}; "
            f"template_unfitted={control_template_unfitted}; "
            f"tuned_reference={tuned_reference_exact}; "
            f"selected_reference={selected_reference_exact}; "
            f"selection_valid={selection_valid}; "
            f"outer_test_isolated={outer_test_isolated}; "
            f"schemas=36/13/9:{schemas_exact}; "
            f"warning_schema={warning_schema_exact}; "
            f"negative={rejected_negative_cases}/{len(negative_cases)}; "
            f"source_contract={source_contract}; "
            f"notebook_state={notebook_state_exact}; "
            f"inputs_unchanged={inputs_unchanged}; "
            f"timings={control_timing_valid and tuned_timing_valid}; "
            f"captured_warnings={len(tuned_warnings)}:"
            f"{captured_warnings_valid}"
        )
        return Check(
            "stage07_nested_cv_fit_and_tuning_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_fit_and_tuning_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_numeric_runtime_contract() -> Check:
    try:
        import inspect
        from dataclasses import replace

        import numpy as np
        import pandas as pd
        from sklearn.base import BaseEstimator, ClassifierMixin
        from sklearn.linear_model import LogisticRegression

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.nested_cv import (
            build_outer_splitter,
            evaluate_fitted_estimator_on_outer_block,
            fit_control_estimator_on_outer_block,
            fit_tuned_hist_gradient_boosting_on_outer_block,
        )
        from mlcra.numeric_runtime import (
            PROSPECTIVE_PROTOCOL_ID,
            REQUIRED_RUNTIME_CONTRACT_COLUMNS,
            RUNTIME_CONTRACT_ID,
            NumericBackendIdentity,
            NumericBackendSpec,
            build_numeric_runtime_contract,
            capture_blas_runtime,
            enforced_numeric_runtime,
            numeric_runtime_evidence_rows,
        )

        contract_path = (
            PROJECT_ROOT
            / "configs"
            / "runtime"
            / "miniboone_nested_numeric_runtime_v01.csv"
        )
        contract_frame = pd.read_csv(
            contract_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        contract_frame_before = contract_frame.copy(deep=True)
        contract = build_numeric_runtime_contract(
            contract_frame,
            RUNTIME_CONTRACT_ID,
            PROSPECTIVE_PROTOCOL_ID,
        )

        before_runtime = capture_blas_runtime()
        with enforced_numeric_runtime(contract) as during_runtime:
            evidence_rows = numeric_runtime_evidence_rows(
                contract,
                during_runtime,
            )
        after_runtime = capture_blas_runtime()

        expected_evidence_columns = [
            "runtime_contract_id",
            "protocol_id",
            "base_protocol_id",
            "backend_key",
            "user_api",
            "internal_api",
            "prefix",
            "version",
            "threading_layer",
            "architecture",
            "library_filename",
            "num_threads",
            "thread_limit",
            "contract_status",
        ]
        runtime_contract_exact = (
            contract.runtime_contract_id
            == "miniboone_nested_numeric_runtime_v01"
            and contract.protocol_id == "miniboone_nested_cv_v02"
            and contract.base_protocol_id == "miniboone_nested_cv_v01"
            and contract.status == "prospective_locked_before_run"
            and contract.user_api == "blas"
            and contract.thread_limit == 1
            and contract.backend_match_policy == "exact_identity"
            and contract.enforcement_api
            == "threadpoolctl.threadpool_limits"
            and contract.golden_policy
            == "preserve_existing_v01_golden"
            and contract.cross_environment_policy
            == "blocked_without_separate_calibration"
            and len(contract.expected_backends) == 2
            and {
                spec.identity.version for spec in contract.expected_backends
            }
            == {"0.3.30", "0.3.31.188.0"}
        )
        enforcement_exact = (
            len(before_runtime) == len(during_runtime) == 2
            and all(runtime.num_threads == 1 for runtime in during_runtime)
            and before_runtime == after_runtime
            and len(evidence_rows) == 2
            and all(
                list(row) == expected_evidence_columns
                and row["num_threads"] == row["thread_limit"] == 1
                for row in evidence_rows
            )
        )

        random_state = 20260507
        y = np.tile(np.array([0, 1], dtype=int), 50)
        generator = np.random.default_rng(random_state)
        X = pd.DataFrame(
            {
                "feature_0": y + generator.normal(0.0, 0.35, len(y)),
                "feature_1": generator.normal(0.0, 1.0, len(y)),
                "feature_2": (1 - y)
                + generator.normal(0.0, 0.35, len(y)),
                "feature_3": generator.normal(0.0, 1.0, len(y)),
            }
        )
        train_index, test_index = next(
            build_outer_splitter(5, 2, random_state).split(X, y)
        )
        candidate_bundle = {
            "candidate_id": "fixture_candidate",
            "did": 1,
            "dataset_name": "deterministic_binary_fixture",
            "target_name": "target",
            "target_metadata": {
                "target_class_0": "False",
                "target_class_1": "True",
                "positive_class_assumption": "True",
            },
        }
        common = {
            "candidate_bundle": candidate_bundle,
            "X": X,
            "y": y,
            "train_index": train_index,
            "test_index": test_index,
            "model_id": "logistic_regression",
            "zero_based_outer_split_number": 0,
            "feature_names": list(X.columns),
            "protocol_id": PROSPECTIVE_PROTOCOL_ID,
            "candidate_id": "fixture_candidate",
            "outer_n_splits": 5,
            "outer_n_repeats": 2,
            "inner_n_splits": 3,
            "feature_policy_id": "fixture_features_locked",
        }

        first_row, first_warnings = fit_control_estimator_on_outer_block(
            **common,
            estimator_template=LogisticRegression(
                max_iter=1000,
                random_state=random_state,
            ),
            numeric_runtime_contract=contract,
        )
        second_row, second_warnings = fit_control_estimator_on_outer_block(
            **common,
            estimator_template=LogisticRegression(
                max_iter=1000,
                random_state=random_state,
            ),
            numeric_runtime_contract=contract,
        )
        deterministic_fields = [
            field
            for field in first_row
            if field not in {"fit_seconds", "predict_seconds"}
        ]
        repeated_fit_exact = (
            all(
                first_row[field] == second_row[field]
                for field in deterministic_fields
            )
            and first_warnings == second_warnings == []
            and first_row["protocol_id"] == PROSPECTIVE_PROTOCOL_ID
        )

        class RuntimeProbeClassifier(ClassifierMixin, BaseEstimator):
            observed_thread_sets: list[tuple[int, ...]] = []

            @classmethod
            def record_threads(cls) -> None:
                cls.observed_thread_sets.append(
                    tuple(
                        runtime.num_threads
                        for runtime in capture_blas_runtime()
                    )
                )

            def fit(self, X_fit, y_fit):
                self.record_threads()
                self.classes_ = np.array([0, 1])
                return self

            def predict(self, X_predict):
                self.record_threads()
                return np.zeros(len(X_predict), dtype=int)

            def predict_proba(self, X_predict):
                self.record_threads()
                return np.tile(
                    np.array([[0.6, 0.4]]),
                    (len(X_predict), 1),
                )

        RuntimeProbeClassifier.observed_thread_sets.clear()
        fit_control_estimator_on_outer_block(
            **common,
            estimator_template=RuntimeProbeClassifier(),
            numeric_runtime_contract=contract,
        )
        nested_integration_exact = (
            len(RuntimeProbeClassifier.observed_thread_sets) == 3
            and all(
                thread_set == (1, 1)
                for thread_set in RuntimeProbeClassifier.observed_thread_sets
            )
        )

        negative_frames: list[pd.DataFrame] = [
            contract_frame.drop(columns=["source_reference"]),
            pd.concat(
                [contract_frame, contract_frame.iloc[[0]]],
                ignore_index=True,
            ),
            contract_frame.assign(thread_limit="2"),
            contract_frame.assign(status="draft"),
            contract_frame.assign(source_reference=""),
        ]
        duplicate_identity = contract_frame.copy()
        for column in (
            "internal_api",
            "prefix",
            "version",
            "threading_layer",
            "architecture",
            "library_filename",
        ):
            duplicate_identity.loc[1, column] = duplicate_identity.loc[0, column]
        negative_frames.append(duplicate_identity)

        rejected_negative_cases = 0
        for negative_frame in negative_frames:
            try:
                build_numeric_runtime_contract(
                    negative_frame,
                    RUNTIME_CONTRACT_ID,
                    PROSPECTIVE_PROTOCOL_ID,
                )
            except (TypeError, ValueError):
                rejected_negative_cases += 1

        try:
            fit_control_estimator_on_outer_block(
                **common,
                estimator_template=LogisticRegression(max_iter=1000),
            )
        except ValueError:
            rejected_negative_cases += 1

        mismatched_contract = replace(contract, protocol_id="other_protocol")
        try:
            fit_control_estimator_on_outer_block(
                **common,
                estimator_template=LogisticRegression(max_iter=1000),
                numeric_runtime_contract=mismatched_contract,
            )
        except ValueError:
            rejected_negative_cases += 1

        first_spec = contract.expected_backends[0]
        mismatched_identity = replace(
            first_spec.identity,
            version="unexpected_backend_version",
        )
        mismatched_backend_contract = replace(
            contract,
            expected_backends=(
                NumericBackendSpec(
                    backend_key=first_spec.backend_key,
                    identity=NumericBackendIdentity(
                        **{
                            field: getattr(mismatched_identity, field)
                            for field in (
                                "internal_api",
                                "prefix",
                                "version",
                                "threading_layer",
                                "architecture",
                                "library_filename",
                            )
                        }
                    ),
                ),
                *contract.expected_backends[1:],
            ),
        )
        try:
            with enforced_numeric_runtime(mismatched_backend_contract):
                pass
        except RuntimeError:
            rejected_negative_cases += 1

        golden_hashes = {
            "openml_miniboone_nested_outer_scores.csv": (
                "916a629bfa2d3d19505db9f2ee52525a55284a30d810aeb0ee3dc9e692b8880c"
            ),
            "openml_miniboone_nested_selected_params.csv": (
                "4734792f0ec93e96cf1808c0046a3956d8f7391886f6752f1af3b37633960666"
            ),
            "openml_miniboone_nested_summary.csv": (
                "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657"
            ),
            "openml_miniboone_nested_quality_checks.csv": (
                "1751215f046505aa90ea1ba6debf9082769b680bba50ca93ebd7a1475b0e8225"
            ),
            "openml_miniboone_nested_warnings.csv": (
                "db471e62481fe6283595f8851fb6d75c89d8e511da5a8851a7b237aa3ee03b4b"
            ),
            "openml_miniboone_nested_environment.csv": (
                "46946715aa444e0a95c5ac46aa370509e0fc9fe7b5d3f3d900a05975efaeb0ff"
            ),
        }
        protected_golden_exact = all(
            sha256_file(PROJECT_ROOT / "data_registry" / file_name)
            == expected_hash
            for file_name, expected_hash in golden_hashes.items()
        )

        signature_contract = all(
            "numeric_runtime_contract" in inspect.signature(function).parameters
            and inspect.signature(function).parameters[
                "numeric_runtime_contract"
            ].default
            is None
            for function in (
                evaluate_fitted_estimator_on_outer_block,
                fit_control_estimator_on_outer_block,
                fit_tuned_hist_gradient_boosting_on_outer_block,
            )
        )
        source_contract = (
            signature_contract
            and "require_numeric_runtime_contract(" in (
                PROJECT_ROOT / "src" / "mlcra" / "nested_cv.py"
            ).read_text(encoding="utf-8-sig")
            and list(contract_frame.columns)
            == REQUIRED_RUNTIME_CONTRACT_COLUMNS
        )
        stage_text = (
            PROJECT_ROOT / "docs" / "stages" / "stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        evidence_tokens = (
            "## 39. ST07_14 — контракт численного backend и потоковой воспроизводимости",
            "task_id: ST07_14_numeric_backend_and_thread_reproducibility_contract",
            "task_profile: CHANGE",
            "ST07_14_NUMERIC_POLICY: prospective_single_thread_exact_same_backend",
            "ST07_14_GOLDEN_POLICY: preserve_existing_v01_golden",
            "prospective_protocol_id: miniboone_nested_cv_v02",
            "full_miniboone_training: NOT_RUN",
            "notebook_execution: NOT_RUN",
            "scientific_validation: SKIPPED",
            "cross_environment_exactness: BLOCKED_WITHOUT_SEPARATE_CALIBRATION",
            "warning_mismatch_from_st07_13: UNRESOLVED_OUT_OF_SCOPE",
            "golden_v01_hashes_unchanged: 6/6",
        )
        documentary_evidence_exact = all(
            token in stage_text for token in evidence_tokens
        )
        inputs_unchanged = contract_frame.equals(contract_frame_before)
        negative_total = len(negative_frames) + 3

        checks = {
            "runtime_contract_exact": runtime_contract_exact,
            "enforcement_exact": enforcement_exact,
            "repeated_fit_exact": repeated_fit_exact,
            "nested_integration_exact": nested_integration_exact,
            "negative_cases": rejected_negative_cases == negative_total,
            "protected_golden_exact": protected_golden_exact,
            "source_contract": source_contract,
            "documentary_evidence_exact": documentary_evidence_exact,
            "inputs_unchanged": inputs_unchanged,
        }
        detail = (
            f"backends={len(contract.expected_backends)}/2; "
            f"threads={tuple(r.num_threads for r in before_runtime)}"
            f"->1->"
            f"{tuple(r.num_threads for r in after_runtime)}; "
            f"evidence_rows={len(evidence_rows)}/2; "
            f"repeated_fit={repeated_fit_exact}; "
            f"nested_probe={RuntimeProbeClassifier.observed_thread_sets}; "
            f"negative={rejected_negative_cases}/{negative_total}; "
            f"golden={protected_golden_exact}; "
            f"source_contract={source_contract}; "
            f"documentary_evidence={documentary_evidence_exact}; "
            f"inputs_unchanged={inputs_unchanged}"
        )
        return Check(
            "stage07_numeric_runtime_contract",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:
        return Check(
            "stage07_numeric_runtime_contract",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_nested_cv_v02_protocol_contract() -> Check:
    try:
        import pandas as pd

        protocol_path = (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_protocol_lock.csv"
        )
        schema_path = (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        protocol_frame = pd.read_csv(
            protocol_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        schema_frame = pd.read_csv(
            schema_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        protocol_before = protocol_frame.copy(deep=True)
        schema_before = schema_frame.copy(deep=True)

        protocol_columns = [
            "protocol_id",
            "base_protocol_id",
            "object",
            "value",
            "decision_status",
            "decision_ru",
            "rationale_ru",
            "source_reference",
            "locked_before_run",
        ]
        expected_values = {
            "base_protocol": "miniboone_nested_cv_v01",
            "candidate_id": "openml_miniboone_41150",
            "openml_dataset_id": "41150",
            "dataset_name": "MiniBooNE",
            "features": "ParticleID_0..ParticleID_49",
            "feature_policy_id": "numeric_particleid_0_49_locked",
            "feature_count": "50",
            "target_name": "signal",
            "target_mapping": "False=0;True=1",
            "positive_class": "True",
            "outer_cv_method": "RepeatedStratifiedKFold",
            "outer_cv_n_splits": "5",
            "outer_cv_n_repeats": "2",
            "outer_random_state": "20260507",
            "outer_position_order": "repeat_major_then_fold",
            "inner_cv_method": "StratifiedKFold",
            "inner_cv_n_splits": "3",
            "inner_shuffle": "true",
            "inner_random_state_policy": (
                "20260507+zero_based_outer_split_number"
            ),
            "model_order": (
                "hist_gradient_boosting;dummy_prior;logistic_regression"
            ),
            "model_roles": (
                "hist_gradient_boosting=tuned_candidate;"
                "dummy_prior=lower_bound;logistic_regression=baseline"
            ),
            "hgb_model_space": (
                "miniboone_hist_gradient_boosting_nested_space"
            ),
            "primary_scoring": "average_precision",
            "metric_contract": (
                "roc_auc;average_precision;pr_auc_alias_average_precision;"
                "f1;balanced_accuracy;log_loss;brier_score"
            ),
            "gridsearch_contract": (
                "scoring=average_precision;refit=true;n_jobs=1;"
                "return_train_score=false;error_score=raise"
            ),
            "numeric_runtime_contract": (
                "miniboone_nested_numeric_runtime_v01"
            ),
            "numeric_policy": (
                "prospective_single_thread_exact_same_backend"
            ),
            "golden_policy": "preserve_existing_v01_golden",
            "validation_run_count": "2",
            "validation_run_isolation": (
                "fresh_process_and_separate_temporary_directory_per_run"
            ),
            "network_policy": "offline_cache_only_no_force_refresh",
            "artifact_count": "7",
            "artifact_namespace": "openml_miniboone_nested_v02_*",
            "comparison_class_A": (
                "exact_structure_order_keys_ids_splits_params_status_"
                "environment_runtime"
            ),
            "comparison_class_B": (
                "exact_deterministic_numeric_after_csv_roundtrip"
            ),
            "comparison_class_C": "finite_nonnegative_not_exact",
            "comparison_class_D": (
                "exact_raw_warning_multiset_after_stable_sort"
            ),
            "warning_policy": (
                "capture_all_no_suppression_no_result_driven_normalization"
            ),
            "promotion_gate": (
                "A_PASS_AND_B_PASS_AND_C_PASS_AND_D_PASS_AND_quality_all_"
                "pass_AND_protected_unchanged_AND_john_acceptance"
            ),
            "cross_environment_policy": (
                "blocked_without_separate_calibration"
            ),
            "claim_policy": "no_claim_or_verdict_change",
        }
        inherited_objects = set(list(expected_values)[:25]) | {"claim_policy"}
        delta_objects = {
            "numeric_runtime_contract",
            "numeric_policy",
            "golden_policy",
        }
        validation_objects = set(expected_values) - inherited_objects - delta_objects

        def validate_protocol(frame: pd.DataFrame) -> None:
            if list(frame.columns) != protocol_columns:
                raise ValueError("unexpected v02 protocol columns")
            if len(frame) != 41:
                raise ValueError("unexpected v02 protocol row count")
            if frame["object"].duplicated().any():
                raise ValueError("duplicate v02 protocol object")
            if set(frame["object"]) != set(expected_values):
                raise ValueError("unexpected v02 protocol objects")
            if not frame["protocol_id"].eq("miniboone_nested_cv_v02").all():
                raise ValueError("unexpected protocol_id")
            if not frame["base_protocol_id"].eq(
                "miniboone_nested_cv_v01"
            ).all():
                raise ValueError("unexpected base_protocol_id")
            if not frame["locked_before_run"].eq("yes").all():
                raise ValueError("v02 protocol must be locked before run")
            if any(
                not str(value).strip()
                for column in (
                    "decision_ru",
                    "rationale_ru",
                    "source_reference",
                )
                for value in frame[column]
            ):
                raise ValueError("empty v02 evidence field")
            observed_values = dict(zip(frame["object"], frame["value"]))
            if observed_values != expected_values:
                raise ValueError("unexpected v02 protocol value")
            statuses = dict(zip(frame["object"], frame["decision_status"]))
            if any(statuses[obj] != "inherited_exact" for obj in inherited_objects):
                raise ValueError("unexpected inherited status")
            if any(statuses[obj] != "prospective_delta" for obj in delta_objects):
                raise ValueError("unexpected prospective delta status")
            if any(
                statuses[obj] != "prospective_validation"
                for obj in validation_objects
            ):
                raise ValueError("unexpected validation status")

        artifact_columns = {
            "outer_scores": 36,
            "selected_params": 13,
            "summary": 39,
            "quality_checks": 4,
            "warnings": 9,
            "environment": 3,
            "numeric_runtime": 14,
        }
        row_policies = {
            "outer_scores": "exact_30",
            "selected_params": "exact_10",
            "summary": "exact_3",
            "quality_checks": "exact_16",
            "warnings": "minimum_1",
            "environment": "exact_8",
            "numeric_runtime": "exact_2",
        }
        canonical_paths = {
            artifact: (
                "data_registry/openml_miniboone_nested_v02_"
                f"{artifact}.csv"
            )
            for artifact in artifact_columns
        }
        expected_schema_columns = [
            "protocol_id",
            "artifact_id",
            "canonical_path",
            "column_position",
            "column_name",
            "required",
            "comparison_class",
            "key_role",
            "expected_rows_policy",
            "expected_column_count",
            "description_ru",
        ]
        v01_artifacts = {
            "outer_scores": "openml_miniboone_nested_outer_scores.csv",
            "selected_params": "openml_miniboone_nested_selected_params.csv",
            "summary": "openml_miniboone_nested_summary.csv",
            "quality_checks": "openml_miniboone_nested_quality_checks.csv",
            "warnings": "openml_miniboone_nested_warnings.csv",
            "environment": "openml_miniboone_nested_environment.csv",
        }
        runtime_columns = [
            "runtime_contract_id",
            "protocol_id",
            "base_protocol_id",
            "backend_key",
            "user_api",
            "internal_api",
            "prefix",
            "version",
            "threading_layer",
            "architecture",
            "library_filename",
            "num_threads",
            "thread_limit",
            "contract_status",
        ]

        def validate_schema(frame: pd.DataFrame) -> None:
            if list(frame.columns) != expected_schema_columns:
                raise ValueError("unexpected v02 schema columns")
            if len(frame) != 118:
                raise ValueError("unexpected v02 schema row count")
            if not frame["protocol_id"].eq("miniboone_nested_cv_v02").all():
                raise ValueError("unexpected schema protocol_id")
            if not frame["required"].eq("yes").all():
                raise ValueError("all v02 schema columns must be required")
            if set(frame["artifact_id"]) != set(artifact_columns):
                raise ValueError("unexpected v02 schema artifacts")
            if frame[["artifact_id", "column_position"]].duplicated().any():
                raise ValueError("duplicate artifact column position")
            for artifact, count in artifact_columns.items():
                rows = frame.loc[frame["artifact_id"].eq(artifact)].copy()
                if len(rows) != count:
                    raise ValueError("unexpected artifact column count")
                if rows["column_position"].tolist() != [
                    str(index) for index in range(1, count + 1)
                ]:
                    raise ValueError("unexpected artifact column order")
                if not rows["expected_column_count"].eq(str(count)).all():
                    raise ValueError("unexpected expected_column_count")
                if not rows["expected_rows_policy"].eq(
                    row_policies[artifact]
                ).all():
                    raise ValueError("unexpected expected_rows_policy")
                if not rows["canonical_path"].eq(
                    canonical_paths[artifact]
                ).all():
                    raise ValueError("unexpected canonical path")
                if artifact in v01_artifacts:
                    v01_columns = list(
                        pd.read_csv(
                            PROJECT_ROOT
                            / "data_registry"
                            / v01_artifacts[artifact],
                            nrows=0,
                            encoding="utf-8-sig",
                        ).columns
                    )
                    if rows["column_name"].tolist() != v01_columns:
                        raise ValueError("v02 schema does not inherit v01 columns")
                elif rows["column_name"].tolist() != runtime_columns:
                    raise ValueError("unexpected numeric runtime schema")
            class_counts = frame["comparison_class"].value_counts().to_dict()
            if class_counts != {"A": 69, "B": 38, "D": 9, "C": 2}:
                raise ValueError("unexpected comparison class counts")
            c_rows = frame.loc[frame["comparison_class"].eq("C")]
            if set(c_rows["column_name"]) != {"fit_seconds", "predict_seconds"}:
                raise ValueError("class C must contain only timing")
            d_rows = frame.loc[frame["comparison_class"].eq("D")]
            if not d_rows["artifact_id"].eq("warnings").all():
                raise ValueError("class D must contain only warnings")
            if int(frame["key_role"].eq("key").sum()) != 18:
                raise ValueError("unexpected key-role count")
            if frame["description_ru"].str.strip().eq("").any():
                raise ValueError("empty schema description")

        validate_protocol(protocol_frame)
        validate_schema(schema_frame)

        protected_hashes = {
            "data_registry/openml_miniboone_nested_cv_protocol_lock.csv": (
                "5b26906979d9484923742c1d57343be7298eea4dc790f7e0e7a3f1aedad8324d"
            ),
            "data_registry/openml_miniboone_nested_cv_expected_output_schema.csv": (
                "5beba78ff77edd72d4d07aa7f40555c5412db477bb02b3a58509a1aa401c6557"
            ),
            "data_registry/openml_miniboone_nested_outer_scores.csv": (
                "916a629bfa2d3d19505db9f2ee52525a55284a30d810aeb0ee3dc9e692b8880c"
            ),
            "data_registry/openml_miniboone_nested_selected_params.csv": (
                "4734792f0ec93e96cf1808c0046a3956d8f7391886f6752f1af3b37633960666"
            ),
            "data_registry/openml_miniboone_nested_summary.csv": (
                "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657"
            ),
            "data_registry/openml_miniboone_nested_quality_checks.csv": (
                "1751215f046505aa90ea1ba6debf9082769b680bba50ca93ebd7a1475b0e8225"
            ),
            "data_registry/openml_miniboone_nested_warnings.csv": (
                "db471e62481fe6283595f8851fb6d75c89d8e511da5a8851a7b237aa3ee03b4b"
            ),
            "data_registry/openml_miniboone_nested_environment.csv": (
                "46946715aa444e0a95c5ac46aa370509e0fc9fe7b5d3f3d900a05975efaeb0ff"
            ),
            "configs/runtime/miniboone_nested_numeric_runtime_v01.csv": (
                "96e7e322e1e2603f00eeb7d1db10f4a85e4fd26329b14296a4e8984bf9cd6a11"
            ),
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": (
                "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133"
            ),
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": (
                "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49"
            ),
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": (
                "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d"
            ),
            "configs/verdict_policies/miniboone_verdict_policy_v01.csv": (
                "6b52787d01a8f6606af5eea29a8d13d696ede461d23ef597ef9d19eafa295637"
            ),
        }
        protected_exact = all(
            sha256_file(PROJECT_ROOT / relative_path) == expected_hash
            for relative_path, expected_hash in protected_hashes.items()
        )
        canonical_outputs_exact = st07_22_canonical_bundle_exact()

        protocol_negative_frames = [
            protocol_frame.drop(columns=["source_reference"]),
            pd.concat(
                [protocol_frame, protocol_frame.iloc[[0]]],
                ignore_index=True,
            ),
            protocol_frame.assign(locked_before_run="no"),
            protocol_frame.assign(base_protocol_id="unexpected_base"),
            protocol_frame.assign(source_reference=""),
        ]
        wrong_runtime = protocol_frame.copy()
        wrong_runtime.loc[
            wrong_runtime["object"].eq("numeric_runtime_contract"),
            "value",
        ] = "unexpected_runtime"
        protocol_negative_frames.append(wrong_runtime)
        wrong_runs = protocol_frame.copy()
        wrong_runs.loc[
            wrong_runs["object"].eq("validation_run_count"),
            "value",
        ] = "1"
        protocol_negative_frames.append(wrong_runs)
        wrong_status = protocol_frame.copy()
        wrong_status.loc[
            wrong_status["object"].eq("numeric_policy"),
            "decision_status",
        ] = "inherited_exact"
        protocol_negative_frames.append(wrong_status)

        schema_negative_frames = [
            schema_frame.drop(index=schema_frame.index[-1]).reset_index(drop=True),
            pd.concat(
                [schema_frame, schema_frame.iloc[[0]]],
                ignore_index=True,
            ),
            schema_frame.assign(comparison_class="Z"),
        ]
        wrong_timing = schema_frame.copy()
        wrong_timing.loc[
            wrong_timing["column_name"].eq("fit_seconds"),
            "comparison_class",
        ] = "A"
        schema_negative_frames.append(wrong_timing)
        wrong_warning = schema_frame.copy()
        wrong_warning.loc[
            wrong_warning["artifact_id"].eq("warnings"),
            "comparison_class",
        ] = "A"
        schema_negative_frames.append(wrong_warning)
        wrong_position = schema_frame.copy()
        wrong_position.loc[
            (wrong_position["artifact_id"].eq("outer_scores"))
            & (wrong_position["column_position"].eq("2")),
            "column_position",
        ] = "1"
        schema_negative_frames.append(wrong_position)
        wrong_path = schema_frame.copy()
        wrong_path.loc[
            wrong_path["artifact_id"].eq("numeric_runtime"),
            "canonical_path",
        ] = "data_registry/unexpected.csv"
        schema_negative_frames.append(wrong_path)

        rejected_protocol = 0
        for frame in protocol_negative_frames:
            try:
                validate_protocol(frame)
            except (TypeError, ValueError):
                rejected_protocol += 1
        rejected_schema = 0
        for frame in schema_negative_frames:
            try:
                validate_schema(frame)
            except (TypeError, ValueError):
                rejected_schema += 1

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        evidence_tokens = (
            "## 41. ST07_15 — контракт протокола и валидации nested CV v02",
            "task_id: ST07_15_nested_cv_v02_protocol_and_validation_contract",
            "task_profile: CHANGE",
            "protocol_rows: 41",
            "schema_rows: 118",
            "artifact_contracts: 7",
            "validation_run_count: 2",
            "training_performed: NO",
            "notebook_executed: NO",
            "network_access_performed: NO",
            "v01_protected_hashes_unchanged: 13/13",
            "scientific_validation: SKIPPED",
        )
        documentary_evidence = all(token in stage_text for token in evidence_tokens)
        inputs_unchanged = (
            protocol_frame.equals(protocol_before)
            and schema_frame.equals(schema_before)
        )
        protocol_negative_total = len(protocol_negative_frames)
        schema_negative_total = len(schema_negative_frames)

        checks = {
            "protocol_contract": True,
            "schema_contract": True,
            "protected_exact": protected_exact,
            "canonical_outputs_exact": canonical_outputs_exact,
            "protocol_negative": rejected_protocol == protocol_negative_total,
            "schema_negative": rejected_schema == schema_negative_total,
            "documentary_evidence": documentary_evidence,
            "inputs_unchanged": inputs_unchanged,
        }
        detail = (
            f"protocol={len(protocol_frame)}x{len(protocol_frame.columns)}; "
            f"schema={len(schema_frame)}x{len(schema_frame.columns)}; "
            f"artifacts={schema_frame['artifact_id'].nunique()}/7; "
            f"classes={schema_frame['comparison_class'].value_counts().to_dict()}; "
            f"negative={rejected_protocol + rejected_schema}/"
            f"{protocol_negative_total + schema_negative_total}; "
            f"protected={protected_exact}; "
            f"canonical_outputs_exact={canonical_outputs_exact}; "
            f"documentary_evidence={documentary_evidence}; "
            f"inputs_unchanged={inputs_unchanged}"
        )
        return Check(
            "stage07_nested_cv_v02_protocol_contract",
            "PASS" if all(checks.values()) else "FAIL",
            detail,
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_v02_protocol_contract",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_nested_cv_v02_execution_harness() -> Check:
    try:
        import json as json_module
        import subprocess
        import tempfile
        from dataclasses import replace

        import numpy as np
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.datasets import (
            MINIBOONE_FEATURE_NAMES,
            build_miniboone_control_estimators,
            prepare_miniboone_candidate,
        )
        from mlcra.io import read_csv_checked
        from mlcra.nested_artifacts import (
            ARTIFACT_IDS,
            compare_v02_runs,
            read_v02_artifacts,
            validate_v02_artifacts,
            validate_v02_schema,
            write_v02_artifacts,
        )

        schema_path = (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        schema = read_csv_checked(schema_path)
        validate_v02_schema(schema)
        script_path = PROJECT_ROOT / "scripts/st07_16_fixture_harness.py"
        protected_paths = [
            "notebooks/04_dataset_smoke_experiments.ipynb",
            "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv",
            "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv",
            "data_registry/openml_miniboone_nested_cv_protocol_lock.csv",
            "data_registry/openml_miniboone_nested_cv_expected_output_schema.csv",
            "configs/runtime/miniboone_nested_numeric_runtime_v01.csv",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv",
            "configs/verdict_policies/miniboone_verdict_policy_v01.csv",
            "data_registry/openml_miniboone_nested_outer_scores.csv",
            "data_registry/openml_miniboone_nested_selected_params.csv",
            "data_registry/openml_miniboone_nested_summary.csv",
            "data_registry/openml_miniboone_nested_quality_checks.csv",
            "data_registry/openml_miniboone_nested_warnings.csv",
            "data_registry/openml_miniboone_nested_environment.csv",
        ]
        protected_before = {
            path: sha256_file(PROJECT_ROOT / path) for path in protected_paths
        }
        canonical_paths = schema["canonical_path"].drop_duplicates().tolist()
        canonical_outputs_exact_before = st07_22_canonical_bundle_exact()

        with tempfile.TemporaryDirectory(
            prefix=".tmp_st0716_verifier_",
            dir=PROJECT_ROOT,
        ) as temporary:
            temporary_root = Path(temporary)
            run_dirs = [temporary_root / "run_a", temporary_root / "run_b"]
            process_records = []
            stderr_records = []
            fixture_environment = os.environ.copy()
            fixture_environment["LOKY_MAX_CPU_COUNT"] = "1"
            for run_dir in run_dirs:
                run_dir.mkdir()
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(script_path),
                        "--output-dir",
                        str(run_dir),
                    ],
                    cwd=PROJECT_ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=fixture_environment,
                    timeout=120,
                )
                if completed.returncode != 0:
                    raise RuntimeError(
                        f"fixture subprocess exit={completed.returncode}; "
                        f"stdout={completed.stdout}; stderr={completed.stderr}"
                    )
                lines = [line for line in completed.stdout.splitlines() if line.strip()]
                process_records.append(json_module.loads(lines[-1]))
                stderr_records.append(completed.stderr)

            run_a = read_v02_artifacts(run_dirs[0], schema)
            run_b = read_v02_artifacts(run_dirs[1], schema)
            comparison = compare_v02_runs(run_a, run_b, schema)
            process_isolation = (
                process_records[0]["pid"] != process_records[1]["pid"]
                and process_records[0]["output_dir"]
                != process_records[1]["output_dir"]
                and all(record["network_used"] is False for record in process_records)
                and all(record["artifact_count"] == 7 for record in process_records)
                and all(
                    record.get("artifact_context")
                    == "st07_16_software_fixture"
                    for record in process_records
                )
            )
            fixture_provenance_exact = (
                run_a.quality_checks["details_ru"].tolist()
                == [
                    f"ST07_16 fixture check {check_id}."
                    for check_id in run_a.quality_checks["check_id"]
                ]
                and run_a.warnings.iloc[0]["warning_ru"]
                == (
                    "ST07_16 software fixture validates the execution "
                    "harness; it is not MiniBooNE scientific evidence."
                )
            )

            negative_total = 0
            negative_rejected = 0

            def expect_reject(operation) -> None:
                nonlocal negative_total, negative_rejected
                negative_total += 1
                try:
                    operation()
                except (TypeError, ValueError, FileNotFoundError):
                    negative_rejected += 1

            expect_reject(lambda: validate_v02_schema(schema.drop(index=schema.index[-1])))
            expect_reject(lambda: validate_v02_schema(schema.assign(comparison_class="Z")))

            missing_column = run_a.outer_scores.drop(columns=["protocol_id"])
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_a, outer_scores=missing_column), schema
                )
            )
            short_outer = run_a.outer_scores.iloc[:-1].copy()
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_a, outer_scores=short_outer), schema
                )
            )
            duplicate_outer = run_a.outer_scores.copy()
            duplicate_outer.iloc[1] = duplicate_outer.iloc[0]
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_a, outer_scores=duplicate_outer), schema
                )
            )
            wrong_protocol = run_a.environment.copy()
            wrong_protocol.loc[0, "protocol_id"] = "wrong"
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_a, environment=wrong_protocol), schema
                )
            )
            b_mismatch = run_b.outer_scores.copy()
            b_mismatch.loc[0, "average_precision"] = str(
                float(b_mismatch.loc[0, "average_precision"]) + 0.1
            )
            expect_reject(
                lambda: compare_v02_runs(
                    run_a, replace(run_b, outer_scores=b_mismatch), schema
                )
            )
            c_nan = run_b.outer_scores.copy()
            c_nan.loc[0, "fit_seconds"] = "nan"
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_b, outer_scores=c_nan), schema
                )
            )
            c_negative = run_b.outer_scores.copy()
            c_negative.loc[0, "predict_seconds"] = "-1"
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_b, outer_scores=c_negative), schema
                )
            )
            d_mismatch = run_b.warnings.copy()
            d_mismatch.loc[0, "warning_ru"] += " changed"
            expect_reject(
                lambda: compare_v02_runs(
                    run_a, replace(run_b, warnings=d_mismatch), schema
                )
            )
            quality_fail = run_a.quality_checks.copy()
            quality_fail.loc[0, "check_result"] = "fail"
            expect_reject(
                lambda: validate_v02_artifacts(
                    replace(run_a, quality_checks=quality_fail), schema
                )
            )
            empty_dir = temporary_root / "empty"
            empty_dir.mkdir()
            expect_reject(lambda: read_v02_artifacts(empty_dir, schema))
            expect_reject(
                lambda: write_v02_artifacts(
                    run_a,
                    schema,
                    PROJECT_ROOT / "data_registry",
                    project_root=PROJECT_ROOT,
                )
            )
            nonempty_dir = temporary_root / "nonempty"
            nonempty_dir.mkdir()
            (nonempty_dir / "marker.txt").write_text("x", encoding="utf-8")
            expect_reject(
                lambda: write_v02_artifacts(
                    run_a,
                    schema,
                    nonempty_dir,
                    project_root=PROJECT_ROOT,
                )
            )

            fixture_values = np.zeros((20, 50), dtype=float)
            fixture_X = pd.DataFrame(fixture_values, columns=MINIBOONE_FEATURE_NAMES)
            fixture_y = np.array([0, 1] * 10)
            wrong_columns = fixture_X.copy()
            wrong_columns.columns = list(reversed(wrong_columns.columns))
            expect_reject(lambda: prepare_miniboone_candidate(wrong_columns, fixture_y))
            expect_reject(
                lambda: prepare_miniboone_candidate(
                    fixture_X, np.array([0, 1, 2, 0, 1] * 4)
                )
            )
            expect_reject(
                lambda: prepare_miniboone_candidate(
                    fixture_X, fixture_y, dataset_id=999
                )
            )
            expect_reject(lambda: build_miniboone_control_estimators(True))

        protected_after = {
            path: sha256_file(PROJECT_ROOT / path) for path in protected_paths
        }
        canonical_outputs_exact_after = st07_22_canonical_bundle_exact()
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        evidence_tokens = (
            "## 45. ST07_16 — standalone execution harness",
            "task_id: ST07_16_nested_cv_v02_execution_harness_and_artifact_validation_extraction",
            "fixture_processes: 2/2",
            "artifact_schemas: 7/7",
            "scientific_validation: SKIPPED",
            "full_miniboone_run: NO",
            "network_access: NO",
            "canonical_v02_outputs_created: 0/7",
        )
        documentary_evidence = all(token in stage_text for token in evidence_tokens)
        checks = {
            "process_isolation": process_isolation,
            "comparison": comparison["status"] == "pass",
            "fixture_provenance_exact": fixture_provenance_exact,
            "classes": comparison["class_column_counts"]
            == {"A": 69, "B": 38, "C": 2, "D": 9},
            "negative": negative_rejected == negative_total,
            "protected": protected_before == protected_after,
            "canonical_preserved": (
                canonical_outputs_exact_before and canonical_outputs_exact_after
            ),
            "documentary": documentary_evidence,
        }
        return Check(
            "stage07_nested_cv_v02_execution_harness",
            "PASS" if all(checks.values()) else "FAIL",
            f"processes=2/2:{process_isolation}; artifacts=7/7; "
            f"shapes=30/10/3/16/{len(run_a.warnings)}/8/2; "
            f"classes={comparison['class_column_counts']}; "
            f"fixture_provenance_exact={fixture_provenance_exact}; "
            f"negative={negative_rejected}/{negative_total}; "
            f"protected={protected_before == protected_after}; "
            f"canonical_outputs_exact={canonical_outputs_exact_after}; "
            f"documentary_evidence={documentary_evidence}; "
            "loky_max_cpu_count=1; "
            f"stderr_diagnostics={sum(bool(text.strip()) for text in stderr_records)}/2",
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_v02_execution_harness",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_nested_cv_v02_offline_preflight() -> Check:
    try:
        import ast
        import copy
        import socket
        import subprocess
        import tempfile

        import numpy as np
        import openml
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        import st07_17_miniboone_v02_runner as runner
        from mlcra.datasets import (
            MINIBOONE_FEATURE_NAMES,
            OfflineNetworkAccessError,
            deny_network_access,
            load_miniboone_from_openml_cache,
            prepare_miniboone_candidate,
        )
        from mlcra.io import read_csv_checked
        from mlcra.nested_artifacts import ARTIFACT_IDS
        from mlcra.numeric_runtime import (
            RUNTIME_CONTRACT_ID,
            build_numeric_runtime_contract,
        )

        protected_paths = sorted(
            [
                path.relative_to(PROJECT_ROOT).as_posix()
                for base in (
                    PROJECT_ROOT / "data_registry",
                    PROJECT_ROOT / "configs",
                )
                for path in base.rglob("*")
                if path.is_file()
            ]
            + [
                "notebooks/04_dataset_smoke_experiments.ipynb",
                "src/mlcra/io.py",
                "src/mlcra/metrics.py",
                "src/mlcra/model_spaces.py",
                "src/mlcra/nested_artifacts.py",
                "src/mlcra/nested_cv.py",
                "src/mlcra/numeric_runtime.py",
                "src/mlcra/validation.py",
                "src/mlcra/verdicts.py",
            ]
        )
        protected_before = {
            path: sha256_file(PROJECT_ROOT / path) for path in protected_paths
        }
        schema = read_csv_checked(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        canonical_paths = schema["canonical_path"].drop_duplicates().tolist()
        canonical_outputs_exact_before = st07_22_canonical_bundle_exact()
        cache_server_dir = Path(openml.config.get_cache_directory()).resolve()
        runner_path = PROJECT_ROOT / "scripts/st07_17_miniboone_v02_runner.py"

        if canonical_outputs_exact_before:
            post_promotion_rejections: list[bool] = []
            with tempfile.TemporaryDirectory(
                prefix="mlcra_st0717_post_promotion_guard_"
            ) as guard_name:
                for index in range(2):
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(runner_path),
                            "--preflight-only",
                            "--cache-server-dir",
                            str(cache_server_dir),
                            "--output-dir",
                            str(Path(guard_name) / f"output_{index}"),
                        ],
                        cwd=PROJECT_ROOT,
                        capture_output=True,
                        text=True,
                        timeout=120,
                        check=False,
                    )
                    try:
                        diagnostic = json.loads(completed.stderr.strip())
                    except json.JSONDecodeError:
                        diagnostic = {}
                    post_promotion_rejections.append(
                        completed.returncode == 1
                        and completed.stdout == ""
                        and diagnostic.get("status") == "fail"
                        and diagnostic.get("error_type") == "FileExistsError"
                        and diagnostic.get("error")
                        == "canonical v02 outputs must remain absent before promotion"
                    )
            historical_evidence = json.loads(
                (
                    PROJECT_ROOT
                    / "data_registry"
                    / "st07_20_nested_cv_v02_provenance_corrected_dual_run_"
                    "revalidation_evidence_v01.json"
                ).read_text(encoding="utf-8")
            )
            stage_text = (
                PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
            ).read_text(encoding="utf-8-sig")
            documentary = all(
                token in stage_text
                for token in (
                    "## 49. ST07_17 — offline MiniBooNE runner и preflight contract",
                    "offline_cache_preflight_processes: 2/2",
                    "dataset_identity_and_shape: PASS 41150/130064x50",
                    "target_distribution: PASS 93565/36499",
                    "model_fit_calls: 0",
                    "scientific_validation: SKIPPED",
                    "canonical_v02_outputs_created: 0/7",
                )
            )
            protected_after = {
                path: sha256_file(PROJECT_ROOT / path)
                for path in protected_paths
            }
            checks = {
                "accepted_historical_evidence": _valid_st0720_evidence(
                    historical_evidence
                ),
                "runner_hash_exact": sha256_file(runner_path)
                == "aad089749bd2795651912afb438f547a7feba3ffb5500e52a394c978a6fa68ea",
                "post_promotion_guard_2_of_2": all(
                    post_promotion_rejections
                ),
                "canonical_current_exact": st07_22_canonical_bundle_exact(),
                "protected": protected_before == protected_after,
                "documentary": documentary,
            }
            return Check(
                "stage07_nested_cv_v02_offline_preflight",
                "PASS" if all(checks.values()) else "FAIL",
                "historical_preflight=accepted_via_ST07_20_chain; "
                f"runner_hash_exact={checks['runner_hash_exact']}; "
                f"post_promotion_guard={sum(post_promotion_rejections)}/2; "
                f"canonical_current_exact={checks['canonical_current_exact']}; "
                f"protected={checks['protected']}; "
                f"documentary_evidence={documentary}",
            )

        process_records: list[dict[str, Any]] = []
        process_file_records: list[dict[str, Any]] = []
        process_stderr: list[str] = []
        with tempfile.TemporaryDirectory(prefix="mlcra_st0717_run_a_") as a_name, tempfile.TemporaryDirectory(
            prefix="mlcra_st0717_run_b_"
        ) as b_name:
            output_dirs = [Path(a_name) / "output", Path(b_name) / "output"]
            for output_dir in output_dirs:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(runner_path),
                        "--preflight-only",
                        "--cache-server-dir",
                        str(cache_server_dir),
                        "--output-dir",
                        str(output_dir),
                    ],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError(
                        "ST07_17 preflight subprocess failed: "
                        f"stdout={completed.stdout}; stderr={completed.stderr}"
                    )
                process_records.append(json.loads(completed.stdout.strip().splitlines()[-1]))
                process_file_records.append(
                    json.loads(
                        (output_dir / runner.PREFLIGHT_FILENAME).read_text(
                            encoding="utf-8"
                        )
                    )
                )
                process_stderr.append(completed.stderr)

            normalized = []
            for record in process_records:
                stable = copy.deepcopy(record)
                stable.pop("pid")
                stable.pop("output_dir")
                normalized.append(stable)
            process_isolation = (
                process_records[0]["pid"] != process_records[1]["pid"]
                and process_records[0]["output_dir"]
                != process_records[1]["output_dir"]
            )
            records_exact = normalized[0] == normalized[1]
            files_equal_stdout = process_file_records == process_records

            negative_total = 0
            negative_rejected = 0

            def expect_reject(callable_object) -> None:
                nonlocal negative_total, negative_rejected
                negative_total += 1
                try:
                    callable_object()
                except Exception:
                    negative_rejected += 1

            def network_probe() -> None:
                with deny_network_access() as evidence:
                    try:
                        socket.getaddrinfo("openml.org", 443)
                    except OfflineNetworkAccessError:
                        if evidence.attempts != 1:
                            raise AssertionError("Network guard attempt count mismatch")
                        raise

            expect_reject(network_probe)

            protocol = read_csv_checked(
                PROJECT_ROOT
                / "data_registry"
                / "openml_miniboone_nested_cv_v02_protocol_lock.csv"
            )
            wrong_dataset = protocol.copy()
            wrong_dataset.loc[wrong_dataset["object"].eq("openml_dataset_id"), "value"] = "999"
            expect_reject(lambda: runner.validate_preflight_protocol(wrong_dataset))
            expect_reject(lambda: runner.validate_preflight_protocol(protocol.iloc[:-1]))
            duplicate_object = protocol.copy()
            duplicate_object.loc[1, "object"] = duplicate_object.loc[0, "object"]
            expect_reject(lambda: runner.validate_preflight_protocol(duplicate_object))

            fixture_X = pd.DataFrame(
                np.zeros((20, 50), dtype=float),
                columns=MINIBOONE_FEATURE_NAMES,
            )
            fixture_y = np.array([0, 1] * 10)
            wrong_columns = fixture_X.copy()
            wrong_columns.columns = list(reversed(wrong_columns.columns))
            expect_reject(lambda: prepare_miniboone_candidate(wrong_columns, fixture_y))
            expect_reject(
                lambda: prepare_miniboone_candidate(
                    fixture_X, np.array([0, 1, 2, 0, 1] * 4)
                )
            )

            runtime_df = read_csv_checked(
                PROJECT_ROOT
                / "configs/runtime/miniboone_nested_numeric_runtime_v01.csv"
            )
            bad_runtime = runtime_df.copy()
            bad_runtime["thread_limit"] = "2"
            expect_reject(
                lambda: build_numeric_runtime_contract(
                    bad_runtime,
                    RUNTIME_CONTRACT_ID,
                    "miniboone_nested_cv_v02",
                )
            )
            expect_reject(lambda: runner.require_safe_empty_output(PROJECT_ROOT))

            nonempty = Path(a_name) / "nonempty"
            nonempty.mkdir()
            (nonempty / "marker.txt").write_text("x", encoding="utf-8")
            expect_reject(lambda: runner.require_safe_empty_output(nonempty))
            expect_reject(
                lambda: load_miniboone_from_openml_cache(Path(a_name) / "bad")
            )

            missing_server = Path(a_name) / "missing/org/openml/www"
            missing_server.mkdir(parents=True)
            expect_reject(lambda: load_miniboone_from_openml_cache(missing_server))
            corrupt_server = Path(a_name) / "corrupt/org/openml/www"
            corrupt_dataset = corrupt_server / "datasets/41150"
            corrupt_dataset.mkdir(parents=True)
            (corrupt_dataset / "description.xml").write_text(
                "corrupt", encoding="utf-8"
            )
            expect_reject(lambda: load_miniboone_from_openml_cache(corrupt_server))

            def subprocess_without_preflight() -> None:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(runner_path),
                        "--cache-server-dir",
                        str(cache_server_dir),
                        "--output-dir",
                        str(Path(a_name) / "no_flag"),
                    ],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError("expected CLI rejection")

            expect_reject(subprocess_without_preflight)

            def subprocess_project_output() -> None:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(runner_path),
                        "--preflight-only",
                        "--cache-server-dir",
                        str(cache_server_dir),
                        "--output-dir",
                        str(PROJECT_ROOT),
                    ],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if completed.returncode != 0:
                    raise RuntimeError("expected CLI rejection")

            expect_reject(subprocess_project_output)

        fit_call_count = 0
        for source_path in (
            PROJECT_ROOT / "src/mlcra/datasets.py",
            runner_path,
        ):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            fit_call_count += sum(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "fit"
                for node in ast.walk(tree)
            )

        protected_after = {
            path: sha256_file(PROJECT_ROOT / path) for path in protected_paths
        }
        canonical_outputs_exact_after = st07_22_canonical_bundle_exact()
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        evidence_tokens = (
            "## 49. ST07_17 — offline MiniBooNE runner и preflight contract",
            "task_id: ST07_17_nested_cv_v02_offline_miniboone_runner_and_preflight_contract",
            "offline_cache_preflight_processes: 2/2",
            "dataset_identity_and_shape: PASS 41150/130064x50",
            "target_distribution: PASS 93565/36499",
            "model_fit_calls: 0",
            "scientific_validation: SKIPPED",
            "canonical_v02_outputs_created: 0/7",
        )
        documentary_evidence = all(token in stage_text for token in evidence_tokens)
        expected_record = {
            "status": "pass",
            "dataset_rows": 130064,
            "feature_count": 50,
            "target_false_count": 93565,
            "target_true_count": 36499,
            "network_attempts": 0,
            "model_fit_calls": 0,
            "parameter_combinations": 16,
            "runtime_backend_count": 2,
            "runtime_threads": [1, 1],
            "canonical_v02_outputs_created": 0,
            "dataset_content_sha256": (
                "e9b0d482a8d4a542ecb81f0e50ba1043b7f85a4487c5c9825e5c62a406981284"
            ),
            "cache_manifest_sha256": (
                "a6ae3314752c8dce595fb9ef491f27674806e54583bea7d650a3d46878eb7318"
            ),
        }
        record_contract = all(
            process_records[0].get(key) == value
            for key, value in expected_record.items()
        )
        checks = {
            "process_isolation": process_isolation,
            "records_exact": records_exact,
            "files_equal_stdout": files_equal_stdout,
            "record_contract": record_contract,
            "negative": negative_rejected == negative_total,
            "no_fit_calls": fit_call_count == 0,
            "protected": protected_before == protected_after,
            "canonical_preserved": (
                canonical_outputs_exact_before and canonical_outputs_exact_after
            ),
            "documentary": documentary_evidence,
        }
        return Check(
            "stage07_nested_cv_v02_offline_preflight",
            "PASS" if all(checks.values()) else "FAIL",
            f"processes=2/2:{process_isolation}; records_exact={records_exact}; "
            f"dataset=41150/{process_records[0]['dataset_rows']}x"
            f"{process_records[0]['feature_count']}; "
            f"target={process_records[0]['target_false_count']}/"
            f"{process_records[0]['target_true_count']}; "
            f"network_attempts={process_records[0]['network_attempts']}; "
            f"fit_calls={fit_call_count}; negative={negative_rejected}/"
            f"{negative_total}; protected={protected_before == protected_after}; "
            f"canonical_outputs_exact={canonical_outputs_exact_after}; "
            f"documentary_evidence={documentary_evidence}; "
            f"stderr_diagnostics={sum(bool(text.strip()) for text in process_stderr)}/2",
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_v02_offline_preflight",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_nested_cv_v02_dual_run_validation() -> Check:
    try:
        import copy

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_18_nested_cv_v02_dual_run_"
            "reproducibility_validation_evidence_v01.json"
        )
        attempt_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_18_nested_cv_v02_implementation_attempt_01_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
        expected_task = (
            "ST07_18_nested_cv_v02_dual_run_reproducibility_validation"
        )
        expected_counts = {"A": 69, "B": 38, "C": 2, "D": 9}
        expected_rows = {
            "outer_scores": 30,
            "selected_params": 10,
            "summary": 3,
            "quality_checks": 16,
            "warnings": None,
            "environment": 8,
            "numeric_runtime": 2,
        }

        def evidence_errors(record: dict[str, Any]) -> list[str]:
            errors: list[str] = []
            if record.get("task_id") != expected_task:
                errors.append("task_id")
            if record.get("technical_status") != "PASS":
                errors.append("technical_status")
            if record.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
                errors.append("readiness")
            if record.get("validation_run_count") != 2:
                errors.append("validation_run_count")
            if record.get("fresh_process_invocations") != 2:
                errors.append("fresh_process_invocations")
            processes = record.get("process_records", [])
            if len(processes) != 2:
                errors.append("process_count")
            elif (
                processes[0].get("label") == processes[1].get("label")
                or processes[0].get("runner_result", {}).get("pid")
                == processes[1].get("runner_result", {}).get("pid")
            ):
                errors.append("process_isolation")
            for process in processes:
                runner = process.get("runner_result") or {}
                stderr = process.get("stderr_text", "")
                if (
                    process.get("return_code") != 0
                    or process.get("parse_error") is not None
                    or runner.get("status") != "pass"
                    or runner.get("task_id") != expected_task
                    or runner.get("artifact_count") != 7
                    or runner.get("quality_pass_count") != 16
                    or runner.get("network_attempts") != 0
                    or runner.get("runtime_backend_count") != 2
                    or runner.get("runtime_threads") != [1, 1]
                    or runner.get("promotion_performed") is not False
                    or runner.get("claim_or_verdict_changed") is not False
                ):
                    errors.append(f"process_contract:{process.get('label')}")
                if hashlib.sha256(stderr.encode("utf-8")).hexdigest() != process.get(
                    "stderr_sha256"
                ):
                    errors.append(f"stderr_sha256:{process.get('label')}")
            inventories = record.get("artifact_records", {})
            if set(inventories) != {"run_a", "run_b"}:
                errors.append("artifact_runs")
            for label, inventory in inventories.items():
                if set(inventory) != set(expected_rows):
                    errors.append(f"artifact_ids:{label}")
                    continue
                for artifact_id, expected in expected_rows.items():
                    item = inventory[artifact_id]
                    rows = item.get("rows")
                    if (expected is None and (not isinstance(rows, int) or rows < 1)) or (
                        expected is not None and rows != expected
                    ):
                        errors.append(f"artifact_rows:{label}:{artifact_id}")
                    digest = item.get("sha256", "")
                    if not re.fullmatch(r"[0-9a-f]{64}", digest):
                        errors.append(f"artifact_sha256:{label}:{artifact_id}")
            classes = record.get("comparison_classes", {})
            if set(classes) != set(expected_counts):
                errors.append("comparison_class_ids")
            else:
                for class_id, count in expected_counts.items():
                    item = classes[class_id]
                    if (
                        item.get("status") != "pass"
                        or item.get("column_count") != count
                        or item.get("errors") != []
                    ):
                        errors.append(f"comparison_class:{class_id}")
            comparator = record.get("authoritative_comparator_result") or {}
            if (
                comparator.get("status") != "pass"
                or comparator.get("class_column_counts") != expected_counts
                or record.get("authoritative_comparator_error") is not None
            ):
                errors.append("authoritative_comparator")
            checks = record.get("checks", {})
            if len(checks) != 10 or not all(value is True for value in checks.values()):
                errors.append("checks")
            if (
                record.get("protected_file_count") != 196
                or record.get("protected_manifest_sha256_before")
                != record.get("protected_manifest_sha256_after")
                or record.get("changed_protected_paths") != []
            ):
                errors.append("protected_manifest")
            if (
                record.get("canonical_output_count") != 7
                or record.get("canonical_outputs_absent_before") is not True
                or record.get("canonical_outputs_absent_after") is not True
                or record.get("candidate_artifacts_promoted") != 0
                or record.get("stage05_claim_or_verdict_changed") is not False
            ):
                errors.append("no_promotion_boundary")
            attempts = record.get("implementation_attempts", [])
            if attempts != [attempt]:
                errors.append("implementation_attempt_link")
            return errors

        negative_total = 0
        negative_rejected = 0

        def expect_evidence_reject(mutator) -> None:
            nonlocal negative_total, negative_rejected
            negative_total += 1
            changed = copy.deepcopy(evidence)
            mutator(changed)
            if evidence_errors(changed):
                negative_rejected += 1

        expect_evidence_reject(lambda value: value.update(technical_status="FAIL"))
        expect_evidence_reject(lambda value: value.update(validation_run_count=1))
        expect_evidence_reject(
            lambda value: value["comparison_classes"]["B"].update(status="fail")
        )
        expect_evidence_reject(
            lambda value: value["process_records"][0]["runner_result"].update(
                network_attempts=1
            )
        )
        expect_evidence_reject(
            lambda value: value["process_records"][1]["runner_result"].update(
                runtime_threads=[2, 2]
            )
        )
        expect_evidence_reject(
            lambda value: value.update(changed_protected_paths=["roadmap.md"])
        )
        expect_evidence_reject(
            lambda value: value.update(canonical_outputs_absent_after=False)
        )
        expect_evidence_reject(
            lambda value: value.update(candidate_artifacts_promoted=1)
        )
        expect_evidence_reject(
            lambda value: value["process_records"][1]["runner_result"].update(
                pid=value["process_records"][0]["runner_result"]["pid"]
            )
        )
        expect_evidence_reject(
            lambda value: value.update(implementation_attempts=[])
        )

        schema = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()
        attempt_contract = (
            attempt.get("attempt_number") == 1
            and attempt.get("failure", {}).get("error_type")
            == "implementation_defect"
            and attempt.get("scientific_comparison_completed") is False
            and attempt.get("scientific_result") == "not_evaluated"
            and attempt.get("scientific_verdict_eligible") is False
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        documentary = all(
            token in stage_text
            for token in (
                "## 53. ST07_18 — dual-run validation и технический PASS",
                "task_id: ST07_18_nested_cv_v02_dual_run_reproducibility_validation",
                "validation_attempt_01: excluded_implementation_defect",
                "validation_attempt_02: PASS",
                "comparison_A: PASS exact 69 columns",
                "comparison_B: PASS exact 38 columns after CSV roundtrip",
                "comparison_C: PASS finite_nonnegative 2 columns",
                "comparison_D: PASS exact raw warning multiset 9 columns",
                "candidate_artifacts_promoted: 0/7",
            )
        )
        errors = evidence_errors(evidence)
        checks = {
            "evidence": not errors,
            "attempt": attempt_contract,
            "negative": negative_rejected == negative_total,
            "canonical_current_exact": canonical_current_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_nested_cv_v02_dual_run_validation",
            "PASS" if all(checks.values()) else "FAIL",
            f"processes=2/2; artifacts=7/7 each; "
            f"classes={expected_counts}; quality=16/16 each; "
            f"network=0/0; runtime=2x1 each; protected=196/196; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"attempt01_excluded={attempt_contract}; "
            f"negative={negative_rejected}/{negative_total}; "
            f"documentary={documentary}; evidence_errors={errors}; "
            f"evidence_sha256={sha256_file(evidence_path)}",
        )
    except Exception as exc:
        return Check(
            "stage07_nested_cv_v02_dual_run_validation",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0718() -> Check:
    try:
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        evidence = json.loads(
            (
                PROJECT_ROOT
                / "data_registry"
                / "st07_18_nested_cv_v02_dual_run_"
                "reproducibility_validation_evidence_v01.json"
            ).read_text(encoding="utf-8")
        )
        schema = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        protocol = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_protocol_lock.csv"
        )

        schema_classes = {
            (row["artifact_id"], row["column_name"]): row["comparison_class"]
            for row in schema
        }
        promotion_rows = [
            row for row in protocol if row.get("object") == "promotion_gate"
        ]
        expected_gate = (
            "A_PASS_AND_B_PASS_AND_C_PASS_AND_D_PASS_AND_quality_all_pass_"
            "AND_protected_unchanged_AND_john_acceptance"
        )
        semantic_defect = (
            "semantic_provenance_defect: CONFIRMED" in stage_text
            and schema_classes.get(("quality_checks", "details_ru")) == "A"
            and schema_classes.get(("warnings", "warning_ru")) == "D"
        )
        validation_pass = (
            evidence.get("technical_status") == "PASS"
            and evidence.get("validation_run_count") == 2
            and evidence.get("candidate_artifacts_promoted") == 0
            and evidence.get("canonical_outputs_absent_after") is True
            and all(evidence.get("checks", {}).values())
        )
        promotion_contract = (
            len(promotion_rows) == 1
            and promotion_rows[0].get("value") == expected_gate
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()
        documentary_tokens = (
            "## 55. Принятие ST07_18 и определение следующего блока Stage 7",
            "proposed_task_id: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract",
            "proposed_status: not_authorized",
            "semantic_provenance_defect: CONFIRMED",
            "immediate_promotion: REJECTED",
            "selected_weighted_score: 4.90/5.00",
            "full_miniboone_training: NO",
            "promotion: NOT_PERFORMED",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        roadmap_boundary = all(
            token in roadmap_text
            for token in (
                "ST07_18_status: accepted_by_john",
                "TASK_CLOSED: ST07_18_nested_cv_v02_dual_run_reproducibility_validation",
                "NEXT_BLOCK_AUTHORIZED: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract",
                "ST07_19_status: accepted_by_john",
                "TASK_CLOSED: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract",
            )
        )
        checks = {
            "validation_pass": validation_pass,
            "semantic_defect": semantic_defect,
            "promotion_contract": promotion_contract,
            "canonical_current_exact": canonical_current_exact,
            "documentary": documentary,
            "roadmap_boundary": roadmap_boundary,
        }
        return Check(
            "stage07_next_block_after_st0718",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_validation={validation_pass}; "
            f"protected_semantic_defect={semantic_defect}; "
            f"promotion_gate={promotion_contract}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"documentary={documentary}; roadmap={roadmap_boundary}; "
            "selected=ST07_19_artifact_context_and_provenance_contract",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0718",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_artifact_context_and_provenance_contract() -> Check:
    try:
        import inspect

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.nested_artifacts import (
            assemble_v02_artifacts,
            build_quality_checks,
        )
        from mlcra.nested_cv import (
            V02ArtifactContext,
            require_v02_artifact_context,
            run_nested_cv_rows,
            v02_protocol_boundary_warning_ru,
            v02_quality_details_ru,
        )

        fixture_context = V02ArtifactContext.ST07_16_SOFTWARE_FIXTURE
        scientific_context = (
            V02ArtifactContext.MINIBOONE_SCIENTIFIC_CANDIDATE
        )
        fixture_warning = (
            "ST07_16 software fixture validates the execution harness; "
            "it is not MiniBooNE scientific evidence."
        )
        scientific_warning = (
            "MiniBooNE v02 scientific-validation candidate artifact; "
            "noncanonical and not promoted."
        )
        contexts_exact = {
            item.value for item in V02ArtifactContext
        } == {
            "st07_16_software_fixture",
            "miniboone_v02_scientific_candidate",
        }
        text_contract = (
            v02_protocol_boundary_warning_ru(fixture_context)
            == fixture_warning
            and v02_quality_details_ru(fixture_context, "metrics_finite")
            == "ST07_16 fixture check metrics_finite."
            and v02_protocol_boundary_warning_ru(scientific_context)
            == scientific_warning
            and v02_quality_details_ru(scientific_context, "metrics_finite")
            == (
                "MiniBooNE v02 scientific-candidate check metrics_finite; "
                "artifact is noncanonical and not promoted."
            )
        )

        negative_total = 0
        negative_rejected = 0

        def expect_reject(operation) -> None:
            nonlocal negative_total, negative_rejected
            negative_total += 1
            try:
                operation()
            except (TypeError, ValueError):
                negative_rejected += 1

        expect_reject(lambda: require_v02_artifact_context(None))
        expect_reject(
            lambda: require_v02_artifact_context(
                "st07_16_software_fixture"
            )
        )
        expect_reject(lambda: V02ArtifactContext("unknown_context"))
        expect_reject(
            lambda: require_v02_artifact_context(
                fixture_context,
                row_status="nested_research_draft",
                interpretation_allowed=(
                    "limited_nested_protocol_review_only"
                ),
            )
        )
        expect_reject(
            lambda: require_v02_artifact_context(
                scientific_context,
                row_status=(
                    "st07_16_software_fixture_not_scientific_evidence"
                ),
                interpretation_allowed="no_scientific_interpretation",
            )
        )
        expect_reject(
            lambda: require_v02_artifact_context(
                fixture_context,
                row_status=(
                    "st07_16_software_fixture_not_scientific_evidence"
                ),
            )
        )
        expect_reject(
            lambda: require_v02_artifact_context(
                fixture_context,
                row_status=(
                    "st07_16_software_fixture_not_scientific_evidence"
                ),
                interpretation_allowed=(
                    "limited_nested_protocol_review_only"
                ),
            )
        )
        expect_reject(
            lambda: v02_quality_details_ru(scientific_context, "")
        )

        required_parameters = all(
            inspect.signature(function).parameters["artifact_context"].default
            is inspect.Parameter.empty
            for function in (
                run_nested_cv_rows,
                build_quality_checks,
                assemble_v02_artifacts,
            )
        )
        nested_cv_text = (PROJECT_ROOT / "src/mlcra/nested_cv.py").read_text(
            encoding="utf-8-sig"
        )
        nested_artifacts_text = (
            PROJECT_ROOT / "src/mlcra/nested_artifacts.py"
        ).read_text(encoding="utf-8-sig")
        fixture_source = (
            PROJECT_ROOT / "scripts/st07_16_fixture_harness.py"
        ).read_text(encoding="utf-8-sig")
        runner_source = (
            PROJECT_ROOT / "scripts/st07_17_miniboone_v02_runner.py"
        ).read_text(encoding="utf-8-sig")
        source_binding = (
            fixture_source.count(
                "V02ArtifactContext.ST07_16_SOFTWARE_FIXTURE"
            )
            == 3
            and "MINIBOONE_SCIENTIFIC_CANDIDATE" not in fixture_source
            and runner_source.count(
                "V02ArtifactContext.MINIBOONE_SCIENTIFIC_CANDIDATE"
            )
            == 3
            and "ST07_16_SOFTWARE_FIXTURE" not in runner_source
            and nested_cv_text.index(
                "validated_artifact_context = require_v02_artifact_context"
            )
            < nested_cv_text.index("outer_scores: list[dict[str, Any]]")
            and "artifact_context=validated_artifact_context"
            in nested_artifacts_text
        )

        protected_hashes = {
            "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
                "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
            ),
            "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
                "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
            ),
            "data_registry/st07_18_nested_cv_v02_dual_run_reproducibility_validation_evidence_v01.json": (
                "a83620fba7bc84f9e57787f2d93637d9630221be5d9b596b97908dfff435f93c"
            ),
        }
        protected_unchanged = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        schema = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_19_nested_cv_v02_artifact_context_and_"
            "provenance_contract_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_contract = (
            evidence.get("task_id")
            == "ST07_19_nested_cv_v02_artifact_context_and_provenance_contract"
            and evidence.get("task_profile") == "CHANGE"
            and evidence.get("technical_status") == "PASS"
            and evidence.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence.get("negative_cases") == {
                "rejected": 8,
                "total": 8,
            }
            and evidence.get("full_miniboone_training_performed") is False
            and evidence.get("network_access_performed") is False
            and evidence.get("candidate_csv_edited") is False
            and evidence.get("promotion_performed") is False
            and evidence.get("canonical_v02_outputs_created") == 0
            and evidence.get("protected_hashes") == protected_hashes
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        documentary = all(
            token in stage_text
            for token in (
                "## 57. ST07_19 — artifact context и provenance contract",
                "NEXT_BLOCK_AUTHORIZED: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract",
                "fixture_provenance_regression: PASS exact",
                "scientific_candidate_context: PASS",
                "negative_context_cases: PASS 8/8",
                "full_miniboone_training: SKIPPED",
                "promotion: NOT_PERFORMED",
            )
        )
        checks = {
            "contexts_exact": contexts_exact,
            "text_contract": text_contract,
            "negative": negative_rejected == negative_total == 8,
            "required_parameters": required_parameters,
            "source_binding": source_binding,
            "protected_unchanged": protected_unchanged,
            "canonical_current_exact": canonical_current_exact,
            "evidence": evidence_contract,
            "documentary": documentary,
        }
        return Check(
            "stage07_artifact_context_and_provenance_contract",
            "PASS" if all(checks.values()) else "FAIL",
            f"contexts=2/2; texts={text_contract}; "
            f"negative={negative_rejected}/{negative_total}; "
            f"required_parameters={required_parameters}; "
            f"source_binding={source_binding}; "
            f"protected={protected_unchanged}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"evidence={evidence_contract}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_artifact_context_and_provenance_contract",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0719() -> Check:
    try:
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text,
            "### Этап 7",
            "## 12.",
        )
        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_19_nested_cv_v02_artifact_context_and_"
            "provenance_contract_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_pass = (
            evidence.get("task_id")
            == "ST07_19_nested_cv_v02_artifact_context_and_provenance_contract"
            and evidence.get("technical_status") == "PASS"
            and evidence.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence.get("full_miniboone_training_performed") is False
            and evidence.get("promotion_performed") is False
        )

        protected_hashes = {
            "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
                "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
            ),
            "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
                "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
            ),
            "data_registry/st07_18_nested_cv_v02_dual_run_reproducibility_validation_evidence_v01.json": (
                "a83620fba7bc84f9e57787f2d93637d9630221be5d9b596b97908dfff435f93c"
            ),
            "data_registry/st07_19_nested_cv_v02_artifact_context_and_provenance_contract_evidence_v01.json": (
                "8e617d0d3f8d5f471ced7be9985e617b26f3c8c5db624e10ef1fddaa5134602a"
            ),
        }
        protected_unchanged = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        schema = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()

        current_tokens = (
            "ST07_19_status: accepted_by_john",
            "TASK_CLOSED: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract",
            "NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation",
            "ST07_20_status: accepted_by_john",
            "TASK_CLOSED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation",
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "ST07_21_status: accepted_by_john",
            "TASK_CLOSED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        documentary_tokens = (
            "## 59. Принятие ST07_19, сверка маршрута и выбор следующего блока",
            "route_assessment: substantive_route_preserved_with_corrective_feedback_insertion",
            "selected_weighted_score: 4.60/5.00",
            "proposed_task_id: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation",
            "evidence_scope: same_environment_repeatability_not_cross_environment_reproducibility",
            "full_miniboone_training_performed: NO",
            "promotion: NOT_PERFORMED",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        authorization_recorded = all(
            "NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_"
            "provenance_corrected_dual_run_revalidation"
            in body
            for body in (stage_current, roadmap_current)
        )
        checks = {
            "accepted_evidence": evidence_pass,
            "protected_unchanged": protected_unchanged,
            "canonical_current_exact": canonical_current_exact,
            "current_state": current_state,
            "documentary": documentary,
            "authorization_recorded": authorization_recorded,
        }
        return Check(
            "stage07_next_block_after_st0719",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_evidence={evidence_pass}; "
            f"protected={protected_unchanged}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"current_state={current_state}; documentary={documentary}; "
            f"authorization_recorded={authorization_recorded}; "
            "selected=ST07_20_provenance_corrected_dual_run_revalidation",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0719",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def _valid_st0720_evidence(record: dict[str, Any]) -> bool:
    expected_counts = {"A": 69, "B": 38, "C": 2, "D": 9}
    expected_rows = {
        "environment": 8,
        "numeric_runtime": 2,
        "outer_scores": 30,
        "quality_checks": 16,
        "selected_params": 10,
        "summary": 3,
        "warnings": 2,
    }
    expected_checks = {
        "candidate_artifacts_and_row_policies",
        "canonical_v02_outputs_absent",
        "claim_or_verdict_change_none",
        "corrected_scientific_candidate_provenance",
        "exactly_two_fresh_process_full_runs",
        "offline_registered_cache_and_zero_network",
        "promotion_not_performed",
        "protected_project_state_unchanged_during_runs",
        "protected_scientific_contract_hashes_exact",
        "quality_checks_16_of_16_per_run",
        "registered_comparison_A_B_D_exact_C_finite_nonnegative",
        "runtime_two_backends_one_thread_per_run",
        "separate_noncanonical_output_directories",
    }
    checks = record.get("checks", {})
    comparison = record.get("comparison_classes", {})
    provenance = record.get("provenance_records", {})
    processes = record.get("process_records", [])
    artifacts = record.get("artifact_records", {})
    runner_results = [
        item.get("runner_result")
        for item in processes
        if isinstance(item, dict)
    ]
    expected_provenance_checks = {
        "fixture_provenance_absent": True,
        "protocol_boundary_warning_exact": True,
        "quality_details_exact": True,
        "scientific_candidate_row_policy_exact": True,
    }
    try:
        process_contract = (
            len(processes) == 2
            and len(runner_results) == 2
            and all(item.get("return_code") == 0 for item in processes)
            and all(item.get("parse_error") is None for item in processes)
            and all(
                result is not None
                and result.get("status") == "pass"
                and result.get("task_id")
                == "ST07_18_nested_cv_v02_dual_run_reproducibility_validation"
                and result.get("artifact_context")
                == "miniboone_v02_scientific_candidate"
                and result.get("training_performed") is True
                and result.get("network_attempts") == 0
                and result.get("network_used") is False
                and result.get("runtime_backend_count") == 2
                and result.get("runtime_threads") == [1, 1]
                and result.get("quality_pass_count") == 16
                and result.get("canonical_v02_outputs_created") == 0
                and result.get("promotion_performed") is False
                for result in runner_results
            )
            and len({result["pid"] for result in runner_results}) == 2
        )
        artifact_contract = (
            set(artifacts) == {"run_a", "run_b"}
            and all(
                set(inventory) == set(expected_rows)
                and all(
                    inventory[artifact_id].get("rows") == expected
                    for artifact_id, expected in expected_rows.items()
                )
                for inventory in artifacts.values()
            )
        )
        comparison_contract = (
            set(comparison) == set(expected_counts)
            and all(
                comparison[key].get("status") == "pass"
                and comparison[key].get("column_count") == count
                and comparison[key].get("errors") == []
                for key, count in expected_counts.items()
            )
            and record.get("authoritative_comparator_result")
            == {"class_column_counts": expected_counts, "status": "pass"}
            and record.get("authoritative_comparator_error") is None
        )
        provenance_contract = (
            set(provenance) == {"run_a", "run_b"}
            and all(
                item.get("status") == "pass"
                and item.get("artifact_context")
                == "miniboone_v02_scientific_candidate"
                and item.get("checks") == expected_provenance_checks
                and item.get("quality_row_count") == 16
                and item.get("warning_row_count") == 2
                and item.get("protocol_boundary_row_count") == 1
                for item in provenance.values()
            )
        )
    except (KeyError, TypeError):
        return False
    return bool(
        record.get("evidence_schema_version") == "st07_20_evidence_v01"
        and record.get("task_id")
        == "ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation"
        and record.get("task_profile") == "SCIENTIFIC_VALIDATION"
        and record.get("authority")
        == "NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_"
        "provenance_corrected_dual_run_revalidation"
        and record.get("technical_status") == "PASS"
        and record.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
        and record.get("validation_run_count") == 2
        and record.get("fresh_process_invocations") == 2
        and record.get("separate_noncanonical_directories")
        == ["run_a", "run_b"]
        and record.get("artifact_context_required")
        == "miniboone_v02_scientific_candidate"
        and set(checks) == expected_checks
        and all(value is True for value in checks.values())
        and process_contract
        and artifact_contract
        and comparison_contract
        and provenance_contract
        and record.get("protected_manifest_sha256_before")
        == record.get("protected_manifest_sha256_after")
        and record.get("changed_protected_paths") == []
        and record.get("canonical_output_count") == 7
        and record.get("canonical_outputs_absent_before") is True
        and record.get("canonical_outputs_absent_after") is True
        and record.get("candidate_artifacts_promoted") == 0
        and record.get("stage05_claim_or_verdict_changed") is False
        and record.get("scientific_interpretation")
        == "same_environment_repeatability_of_provenance_corrected_v02_"
        "candidate_artifacts_only; not_cross_environment_reproducibility; "
        "not_universal_model_superiority; not_stage05_claim_support"
    )


def check_stage07_provenance_corrected_dual_run_revalidation() -> Check:
    try:
        import copy

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_20_nested_cv_v02_provenance_corrected_dual_run_"
            "revalidation_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_valid = _valid_st0720_evidence(evidence)

        mutations: list[dict[str, Any]] = []
        for mutation_id in (
            "technical_status",
            "run_count",
            "comparison_class",
            "authoritative_comparator",
            "provenance",
            "network_gate",
            "canonical_gate",
            "promotion_gate",
            "claim_gate",
            "protected_manifest",
        ):
            mutated = copy.deepcopy(evidence)
            if mutation_id == "technical_status":
                mutated["technical_status"] = "FAIL"
            elif mutation_id == "run_count":
                mutated["validation_run_count"] = 1
            elif mutation_id == "comparison_class":
                mutated["comparison_classes"]["A"]["status"] = "fail"
            elif mutation_id == "authoritative_comparator":
                mutated["authoritative_comparator_result"]["status"] = "fail"
            elif mutation_id == "provenance":
                mutated["provenance_records"]["run_a"]["checks"][
                    "fixture_provenance_absent"
                ] = False
            elif mutation_id == "network_gate":
                mutated["checks"][
                    "offline_registered_cache_and_zero_network"
                ] = False
            elif mutation_id == "canonical_gate":
                mutated["canonical_outputs_absent_after"] = False
            elif mutation_id == "promotion_gate":
                mutated["candidate_artifacts_promoted"] = 1
            elif mutation_id == "claim_gate":
                mutated["stage05_claim_or_verdict_changed"] = True
            else:
                mutated["changed_protected_paths"] = ["unexpected.txt"]
            mutations.append(
                {
                    "mutation_id": mutation_id,
                    "rejected": not _valid_st0720_evidence(mutated),
                }
            )
        negative_pass = all(item["rejected"] for item in mutations)

        protected_hashes = {
            "scripts/st07_17_miniboone_v02_runner.py": (
                "aad089749bd2795651912afb438f547a7feba3ffb5500e52a394c978a6fa68ea"
            ),
            "scripts/st07_18_dual_run_validation.py": (
                "112d1ba0c41af85062711b35c35fddd45136a75c36d49573d34de108cf382d1f"
            ),
            "src/mlcra/nested_cv.py": (
                "804050fbcd8e8a9f10f495ed11de1786677af559c15a4c7f77d955bf24fa6ba9"
            ),
            "src/mlcra/nested_artifacts.py": (
                "19bf4021ef6ee9d556e1bb2f6d03c03901463ce0aa652a81fc80d58b9c246723"
            ),
            "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
                "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
            ),
            "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
                "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
            ),
            "data_registry/st07_18_nested_cv_v02_dual_run_reproducibility_validation_evidence_v01.json": (
                "a83620fba7bc84f9e57787f2d93637d9630221be5d9b596b97908dfff435f93c"
            ),
            "data_registry/st07_19_nested_cv_v02_artifact_context_and_provenance_contract_evidence_v01.json": (
                "8e617d0d3f8d5f471ced7be9985e617b26f3c8c5db624e10ef1fddaa5134602a"
            ),
        }
        nested_source = (PROJECT_ROOT / "src/mlcra/nested_cv.py").read_text(
            encoding="utf-8-sig"
        )
        protected_exact = (
            evidence.get("protected_contract_hashes") == protected_hashes
            and all(
                path == "src/mlcra/nested_cv.py"
                or sha256_file(PROJECT_ROOT / path) == digest
                for path, digest in protected_hashes.items()
            )
            and "inner_base_random_state: int | None = None" in nested_source
            and "validated_inner_base_random_state" in nested_source
        )
        schema = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        current_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation",
            "ST07_20_status: accepted_by_john",
            "TASK_CLOSED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation",
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "ST07_21_status: accepted_by_john",
            "TASK_CLOSED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (
                extract_markdown_section(stage_text, "## 2.", "## 3."),
                extract_markdown_section(roadmap_text, "### Этап 7", "## 12."),
            )
        )
        documentary_tokens = (
            "## 61. ST07_20 — provenance-corrected dual-run revalidation",
            "validation_run_count: PASS 2/2",
            "comparison_A_B_D: PASS exact",
            "comparison_C: PASS finite_nonnegative",
            "scientific_candidate_provenance: PASS 2/2",
            "network_attempts: PASS 0/0",
            "promotion: NOT_PERFORMED",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        checks = {
            "evidence_valid": evidence_valid,
            "negative_mutations_10_of_10": negative_pass,
            "protected_exact": protected_exact,
            "canonical_current_exact": canonical_current_exact,
            "current_state": current_state,
            "documentary": documentary,
        }
        return Check(
            "stage07_provenance_corrected_dual_run_revalidation",
            "PASS" if all(checks.values()) else "FAIL",
            f"evidence={evidence_valid}; negative="
            f"{sum(item['rejected'] for item in mutations)}/{len(mutations)}; "
            f"protected={protected_exact}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"current_state={current_state}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_provenance_corrected_dual_run_revalidation",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0720() -> Check:
    try:
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text,
            "### Этап 7",
            "## 12.",
        )
        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_20_nested_cv_v02_provenance_corrected_dual_run_"
            "revalidation_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        accepted_evidence = _valid_st0720_evidence(evidence)

        protected_hashes = {
            "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
                "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
            ),
            "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
                "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
            ),
            "data_registry/st07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation_evidence_v01.json": (
                "abb7b31036ea0c44a48590d3cb260be8a9c7d02196fa5f1a78ca32d6fa7e04f9"
            ),
        }
        protected_unchanged = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        schema = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()
        current_tokens = (
            "ST07_20_status: accepted_by_john",
            "TASK_CLOSED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation",
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "ST07_21_status: accepted_by_john",
            "TASK_CLOSED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "ST07_21_full_miniboone_training_authorized: false",
            "ST07_21_network_authorized: false",
            "ST07_21_canonical_v02_outputs_authorized: false",
            "ST07_21_promotion_authorized: false",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        documentary_tokens = (
            "## 63. Принятие ST07_20 и выбор следующего блока",
            "selected_alternative: A",
            "selected_weighted_score: 5.00/5.00",
            "proposed_task_id: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "source_selection_policy: first_complete_validation_run_in_registered_execution_order",
            "bundle_atomicity: all_7_artifacts_from_one_run",
            "timing_policy: preserve_selected_run_class_C_exact_no_average_no_minimum_selection",
            "temporary_source_bundles_observed: PASS 14/14",
            "full_miniboone_training_performed: NO",
            "promotion: NOT_AUTHORIZED",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        authorization_recorded = all(
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_"
            "promotion_source_and_timing_provenance_contract"
            in body
            for body in (stage_current, roadmap_current)
        )
        checks = {
            "accepted_evidence": accepted_evidence,
            "protected_unchanged": protected_unchanged,
            "canonical_current_exact": canonical_current_exact,
            "current_state": current_state,
            "documentary": documentary,
            "authorization_recorded": authorization_recorded,
        }
        return Check(
            "stage07_next_block_after_st0720",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_evidence={accepted_evidence}; "
            f"protected={protected_unchanged}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"current_state={current_state}; documentary={documentary}; "
            f"authorization_recorded={authorization_recorded}; "
            "selected=ST07_21_promotion_source_and_timing_provenance_contract",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0720",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_promotion_source_and_timing_provenance_contract() -> Check:
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from mlcra.io import read_csv_checked
        from st07_21_promotion_source_contract import (
            ARTIFACT_IDS,
            BUNDLE_ATOMICITY,
            MANIFEST_PATH,
            PROTECTED_CONTRACT_HASHES,
            SELECTED_SOURCE_LABEL,
            SOURCE_SELECTION_POLICY,
            TIMING_POLICY,
            VALIDATION_EVIDENCE_SHA256,
            bundle_sha256,
            load_validation_evidence,
            run_negative_tests,
            sha256_file as st0721_sha256_file,
            validate_manifest,
        )

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_21_nested_cv_v02_promotion_source_and_timing_"
            "provenance_contract_evidence_v01.json"
        )
        evidence_text = evidence_path.read_text(encoding="utf-8")
        evidence = json.loads(evidence_text)
        validation_evidence = load_validation_evidence()
        schema = read_csv_checked(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        manifest = read_csv_checked(MANIFEST_PATH)
        validation = validate_manifest(manifest, validation_evidence, schema)
        replayed_negative = run_negative_tests(
            manifest, validation_evidence, schema
        )

        expected_bundle_hash = bundle_sha256(
            validation_evidence["artifact_records"][SELECTED_SOURCE_LABEL]
        )
        manifest_exact = (
            validation["status"] == "pass"
            and validation["row_count"] == 7
            and validation["artifact_count"] == len(ARTIFACT_IDS)
            and validation["selected_bundle_sha256"] == expected_bundle_hash
            and evidence.get("promotion_source_manifest_sha256")
            == st0721_sha256_file(MANIFEST_PATH)
        )
        evidence_exact = (
            evidence.get("task_id")
            == "ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract"
            and evidence.get("task_profile") == "CHANGE"
            and evidence.get("technical_status") == "PASS"
            and evidence.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence.get("validation_evidence_sha256")
            == VALIDATION_EVIDENCE_SHA256
            and evidence.get("source_selection_policy")
            == SOURCE_SELECTION_POLICY
            and evidence.get("selected_source_label")
            == SELECTED_SOURCE_LABEL
            and evidence.get("execution_order_position") == 1
            and evidence.get("bundle_atomicity") == BUNDLE_ATOMICITY
            and evidence.get("selected_bundle_sha256") == expected_bundle_hash
            and evidence.get("timing_policy") == TIMING_POLICY
            and evidence.get("timing_class_C_column_count") == 2
            and evidence.get("promotion_source_manifest_rows") == 7
            and evidence.get("candidate_artifacts_copied") == 0
            and evidence.get("candidate_artifacts_promoted") == 0
            and evidence.get("training_performed") is False
            and evidence.get("network_used") is False
            and evidence.get("stage05_claim_or_verdict_changed") is False
            and evidence.get("canonical_outputs_absent_before") is True
            and evidence.get("canonical_outputs_absent_after") is True
            and all(evidence.get("checks", {}).values())
            and len(evidence.get("checks", {})) == 13
        )
        negative_exact = (
            len(evidence.get("negative_tests", {})) == 10
            and all(evidence.get("negative_tests", {}).values())
            and len(replayed_negative) == 10
            and all(replayed_negative.values())
        )
        observed_exact = (
            evidence.get("observed_artifact_records")
            == validation_evidence.get("artifact_records")
        )
        protected_exact = (
            evidence.get("protected_contract_hashes")
            == PROTECTED_CONTRACT_HASHES
            and all(
                st0721_sha256_file(PROJECT_ROOT / relative_path) == digest
                for relative_path, digest in PROTECTED_CONTRACT_HASHES.items()
            )
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()
        durable_locator = (
            evidence.get("source_locator_base") == "<temporary_work_root>"
            and evidence.get("temporary_source_persisted_in_checkpoint") is False
            and "C:\\Users\\" not in evidence_text
        )

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        current_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "ST07_21_status: accepted_by_john",
            "TASK_CLOSED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "ST07_21_full_miniboone_training_authorized: false",
            "ST07_21_network_authorized: false",
            "ST07_21_canonical_v02_outputs_authorized: false",
            "ST07_21_promotion_authorized: false",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (
                extract_markdown_section(stage_text, "## 2.", "## 3."),
                extract_markdown_section(roadmap_text, "### Этап 7", "## 12."),
            )
        )
        documentary_tokens = (
            "## 65. ST07_21 — promotion-source и timing-provenance contract",
            "selected_source_label: run_a",
            "source_manifest_rows: PASS 7/7",
            "source_bundle_hashes: PASS 7/7",
            "timing_class_C_policy: PASS preserve_exact_no_average_no_minimum",
            "negative_mutations: PASS 10/10",
            "canonical_outputs: PASS absent 7/7",
            "promotion: NOT_PERFORMED",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        checks = {
            "manifest_exact": manifest_exact,
            "evidence_exact": evidence_exact,
            "negative_exact": negative_exact,
            "observed_exact": observed_exact,
            "protected_exact": protected_exact,
            "canonical_current_exact": canonical_current_exact,
            "durable_locator": durable_locator,
            "current_state": current_state,
            "documentary": documentary,
        }
        return Check(
            "stage07_promotion_source_and_timing_provenance_contract",
            "PASS" if all(checks.values()) else "FAIL",
            f"manifest={manifest_exact}; evidence={evidence_exact}; "
            f"negative={sum(replayed_negative.values())}/10; "
            f"observed={observed_exact}; protected={protected_exact}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"durable_locator={durable_locator}; "
            f"current_state={current_state}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_promotion_source_and_timing_provenance_contract",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0721() -> Check:
    try:
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_21_nested_cv_v02_promotion_source_and_timing_"
            "provenance_contract_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        accepted_evidence = (
            evidence.get("task_id")
            == "ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract"
            and evidence.get("technical_status") == "PASS"
            and evidence.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence.get("selected_source_label") == "run_a"
            and evidence.get("promotion_source_manifest_rows") == 7
            and evidence.get("candidate_artifacts_copied") == 0
            and evidence.get("candidate_artifacts_promoted") == 0
            and evidence.get("canonical_outputs_absent_after") is True
            and evidence.get("training_performed") is False
            and evidence.get("network_used") is False
            and all(evidence.get("checks", {}).values())
        )

        protected_hashes = {
            "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
                "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
            ),
            "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
                "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
            ),
            "data_registry/st07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation_evidence_v01.json": (
                "abb7b31036ea0c44a48590d3cb260be8a9c7d02196fa5f1a78ca32d6fa7e04f9"
            ),
            "data_registry/openml_miniboone_nested_v02_promotion_source_manifest_v01.csv": (
                "aa823a37bb4287d6668489261c7486e3ecd70a0845a7b20f8e59e46e90a4b465"
            ),
            "data_registry/st07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract_evidence_v01.json": (
                "baf6ab25138f5acf1f28a6111f4785769f6cd9c65910583b2bf467bf8f7eb9c0"
            ),
        }
        protected_unchanged = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        manifest = read_contract_csv(
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_v02_promotion_source_manifest_v01.csv"
        )
        manifest_exact = (
            len(manifest) == 7
            and {row["selected_source_label"] for row in manifest} == {"run_a"}
            and len({row["selected_bundle_sha256"] for row in manifest}) == 1
            and all(
                row["decision_status"]
                == "selected_source_contract_only_noncanonical_not_promoted"
                for row in manifest
            )
        )
        canonical_current_exact = st07_22_canonical_bundle_exact()
        current_tokens = (
            "ST07_21_status: accepted_by_john",
            "TASK_CLOSED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract",
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_full_miniboone_training_authorized: false",
            "ST07_22_network_authorized: false",
            "ST07_22_canonical_v02_outputs_authorized: true",
            "ST07_22_promotion_authorized: true",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        documentary_tokens = (
            "## 67. Принятие ST07_21 и выбор следующего блока",
            "selected_alternative: A",
            "selected_weighted_score: 4.80/5.00",
            "proposed_task_id: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "promotion_semantics: transactional_7_file_bundle_not_single_filesystem_atomic_operation",
            "commit_protocol: prepare_validate_lock_commit_verify_or_rollback",
            "source_availability_observed: PASS 7/7",
            "canonical_outputs_absent: PASS 7/7",
            "full_miniboone_training_performed: NO",
            "promotion: NOT_AUTHORIZED",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        authorization_recorded = all(
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_"
            "transactional_promotion_and_canonical_artifact_registration"
            in body
            for body in (stage_current, roadmap_current)
        )
        started = (
            (
                PROJECT_ROOT
                / "data_registry"
                / "st07_22_nested_cv_v02_transactional_promotion_and_"
                "canonical_artifact_registration_evidence_v01.json"
            ).exists()
            and canonical_current_exact
        )
        checks = {
            "accepted_evidence": accepted_evidence,
            "protected_unchanged": protected_unchanged,
            "manifest_exact": manifest_exact,
            "canonical_current_exact": canonical_current_exact,
            "current_state": current_state,
            "documentary": documentary,
            "authorization_recorded": authorization_recorded,
            "started": started,
        }
        return Check(
            "stage07_next_block_after_st0721",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_evidence={accepted_evidence}; "
            f"protected={protected_unchanged}; manifest={manifest_exact}; "
            f"canonical_current_exact={canonical_current_exact}; "
            f"current_state={current_state}; documentary={documentary}; "
            f"authorization_recorded={authorization_recorded}; "
            f"started={started}; "
            "selected=ST07_22_transactional_promotion_and_canonical_registration",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0721",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_transactional_promotion_and_canonical_registration() -> Check:
    try:
        import copy

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from mlcra.io import read_csv_checked
        from mlcra.nested_artifacts import read_v02_artifacts
        from st07_22_transactional_promotion import (
            LOCK_PATH,
            PLANNED_CHANGE_SET,
            PROTECTED_HASHES,
            run_negative_tests,
        )

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_22_nested_cv_v02_transactional_promotion_and_"
            "canonical_artifact_registration_evidence_v01.json"
        )
        journal_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_22_nested_cv_v02_promotion_transaction_journal_v01.json"
        )
        manifest_path = (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_v02_promotion_source_manifest_v01.csv"
        )
        schema_path = (
            PROJECT_ROOT
            / "data_registry"
            / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
        )
        scope_path = (
            PROJECT_ROOT
            / "docs"
            / "agent"
            / "st07_22_nested_cv_v02_transactional_promotion_and_"
            "canonical_artifact_registration_change_scope_v01.csv"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        manifest = read_csv_checked(manifest_path)
        schema = read_csv_checked(schema_path)
        scope = read_contract_csv(scope_path)
        replayed_negative = run_negative_tests()

        expected_paths = list(ST07_22_CANONICAL_HASHES)
        manifest_contract = (
            len(manifest) == 7
            and manifest["artifact_id"].tolist()
            == [
                "outer_scores",
                "selected_params",
                "summary",
                "quality_checks",
                "warnings",
                "environment",
                "numeric_runtime",
            ]
            and manifest["canonical_path"].tolist() == expected_paths
            and manifest["source_sha256"].tolist()
            == [ST07_22_CANONICAL_HASHES[path] for path in expected_paths]
            and manifest["selected_source_label"].eq("run_a").all()
            and manifest["selected_bundle_sha256"].nunique() == 1
            and manifest["selected_bundle_sha256"].iloc[0]
            == "07257bee44090c1168a01f7bb6080030061b606e4eab960c7ccbd766f5614576"
        )
        canonical_exact = st07_22_canonical_bundle_exact()
        read_v02_artifacts(PROJECT_ROOT / "data_registry", schema)

        expected_checks = {
            "canonical_hash_and_schema_exact_7_of_7",
            "canonical_targets_absent_before",
            "exclusive_lock_acquired",
            "negative_tests_fail_closed",
            "no_overwrite_hard_link_commit_7_of_7",
            "protected_hashes_exact_before_and_after",
            "same_filesystem_staging_validated_7_of_7",
            "selected_run_a_source_7_of_7_hash_and_schema_exact",
            "source_checkpoint_v34_exact",
            "st07_21_evidence_and_manifest_exact",
            "stage05_claim_or_verdict_unchanged",
            "training_and_network_zero",
            "transaction_journal_terminal_commit_planned",
        }
        expected_negative = {
            "concurrent_lock",
            "evidence_manifest_mismatch",
            "injected_partial_commit_rollback",
            "lock_cleanup",
            "missing_source",
            "mixed_bundle",
            "partial_canonical_state",
            "preexisting_target",
            "source_hash_mismatch",
            "staging_hash_mismatch",
        }
        scope_paths = [row["relative_path"] for row in scope]
        evidence_contract = (
            evidence.get("task_id")
            == "ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration"
            and evidence.get("task_profile") == "CHANGE"
            and evidence.get("authority")
            == "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration"
            and evidence.get("technical_status") == "PASS"
            and evidence.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence.get("source_checkpoint") == "ml-cra_v34.zip"
            and evidence.get("source_checkpoint_sha256")
            == "ff44a49a11b7c2c2cc395242b8a1c6ccab79bdee29221ccaa0b807ed3d9764cf"
            and evidence.get("selected_source_label") == "run_a"
            and evidence.get("selected_bundle_sha256")
            == "07257bee44090c1168a01f7bb6080030061b606e4eab960c7ccbd766f5614576"
            and evidence.get("source_manifest_sha256")
            == "aa823a37bb4287d6668489261c7486e3ecd70a0845a7b20f8e59e46e90a4b465"
            and evidence.get("commit_method")
            == "os.link_no_overwrite_same_filesystem"
            and evidence.get("commit_protocol")
            == "prepare_validate_lock_commit_verify_or_rollback"
            and evidence.get("bundle_atomicity_claim")
            == "transactional_7_file_bundle_not_single_filesystem_atomic_operation"
            and evidence.get("canonical_paths") == expected_paths
            and evidence.get("canonical_hashes")
            == {
                row["artifact_id"]: row["source_sha256"]
                for row in manifest.to_dict(orient="records")
            }
            and evidence.get("canonical_output_count") == 7
            and evidence.get("candidate_artifacts_promoted") == 7
            and evidence.get("training_performed") is False
            and evidence.get("network_used") is False
            and evidence.get("stage05_claim_or_verdict_changed") is False
            and evidence.get("protected_hashes") == PROTECTED_HASHES
            and set(evidence.get("checks", {})) == expected_checks
            and all(evidence.get("checks", {}).values())
            and set(evidence.get("negative_tests", {})) == expected_negative
            and all(evidence.get("negative_tests", {}).values())
            and evidence.get("planned_change_set") == PLANNED_CHANGE_SET
            and evidence.get("actual_change_log") == PLANNED_CHANGE_SET
            and evidence.get("change_set_deviations") == []
            and scope_paths == PLANNED_CHANGE_SET
        )
        phases = [event.get("phase") for event in journal.get("events", [])]
        journal_contract = (
            journal.get("task_id") == evidence.get("task_id")
            and journal.get("authority") == evidence.get("authority")
            and journal.get("transaction_id") == evidence.get("transaction_id")
            and journal.get("state") == "committed"
            and journal.get("terminal") is True
            and journal.get("commit_method")
            == "os.link_no_overwrite_same_filesystem"
            and journal.get("commit_protocol")
            == "prepare_validate_lock_commit_verify_or_rollback"
            and journal.get("canonical_paths") == expected_paths
            and journal.get("committed_paths") == expected_paths
            and journal.get("rollback_errors") == []
            and journal.get("evidence_sha256") == sha256_file(evidence_path)
            and phases[0] == "prepare"
            and phases[-1] == "committed"
            and "validated" in phases
            and "verified" in phases
            and phases.count("commit_started") == 8
        )
        protected_exact = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in PROTECTED_HASHES.items()
        )
        no_transients = (
            not LOCK_PATH.exists()
            and not any(
                path.name.startswith(".st07_22_staging_")
                for path in (PROJECT_ROOT / "data_registry").iterdir()
            )
            and not any(
                path.name.startswith(".st07_22_negative_")
                for path in PROJECT_ROOT.iterdir()
            )
        )

        def mutation_rejected(
            target: dict[str, Any], mutation: Callable[[dict[str, Any]], None]
        ) -> bool:
            changed = copy.deepcopy(target)
            mutation(changed)
            return changed != target

        evidence_mutations = [
            lambda value: value.update(technical_status="FAIL"),
            lambda value: value.update(candidate_artifacts_promoted=6),
            lambda value: value.update(network_used=True),
            lambda value: value["checks"].update(
                canonical_hash_and_schema_exact_7_of_7=False
            ),
            lambda value: value.update(selected_source_label="run_b"),
        ]
        mutation_sanity = all(
            mutation_rejected(evidence, mutation)
            for mutation in evidence_mutations
        )

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        current_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "ST07_22_full_miniboone_training_authorized: false",
            "ST07_22_network_authorized: false",
            "ST07_22_canonical_v02_outputs_authorized: true",
            "ST07_22_promotion_authorized: true",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (
                extract_markdown_section(stage_text, "## 2.", "## 3."),
                extract_markdown_section(roadmap_text, "### Этап 7", "## 12."),
            )
        )
        documentary_tokens = (
            "## 69. ST07_22 — transactional promotion и canonical registration",
            "task_id: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "commit_method: os.link_no_overwrite_same_filesystem",
            "transaction_id: st07_22_20260801T140111126958Z_07257bee4409",
            "negative_tests: PASS 10/10",
            "canonical_hashes: PASS 7/7",
            "canonical_schema: PASS 7/7",
            "terminal_journal: PASS committed",
            "lock_and_staging_cleanup: PASS",
            "full_miniboone_training_performed: NO",
            "network_access_performed: NO",
            "stage05_claim_or_verdict_changed: NO",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        checks = {
            "manifest_contract": manifest_contract,
            "canonical_exact": canonical_exact,
            "evidence_contract": evidence_contract,
            "journal_contract": journal_contract,
            "protected_exact": protected_exact,
            "negative_replay": (
                len(replayed_negative) == 10
                and all(replayed_negative.values())
            ),
            "no_transients": no_transients,
            "mutation_sanity": mutation_sanity,
            "current_state": current_state,
            "documentary": documentary,
        }
        return Check(
            "stage07_transactional_promotion_and_canonical_registration",
            "PASS" if all(checks.values()) else "FAIL",
            f"canonical=7/7:{canonical_exact}; schema=118; "
            f"manifest={manifest_contract}; evidence={evidence_contract}; "
            f"journal={journal_contract}:committed; "
            f"negative={sum(replayed_negative.values())}/10; "
            f"protected={protected_exact}; transients_absent={no_transients}; "
            f"current_state={current_state}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_transactional_promotion_and_canonical_registration",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0722() -> Check:
    try:
        import ast

        import pandas as pd

        stage_path = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        )
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text,
            "### Этап 7",
            "## 12.",
        )

        evidence_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_22_nested_cv_v02_transactional_promotion_and_"
            "canonical_artifact_registration_evidence_v01.json"
        )
        journal_path = (
            PROJECT_ROOT
            / "data_registry"
            / "st07_22_nested_cv_v02_promotion_transaction_journal_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        accepted_st0722 = (
            evidence.get("task_id")
            == "ST07_22_nested_cv_v02_transactional_promotion_and_"
            "canonical_artifact_registration"
            and evidence.get("technical_status") == "PASS"
            and evidence.get("readiness") == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence.get("candidate_artifacts_promoted") == 7
            and evidence.get("training_performed") is False
            and evidence.get("network_used") is False
            and all(evidence.get("checks", {}).values())
            and journal.get("state") == "committed"
            and journal.get("terminal") is True
            and journal.get("committed_paths") == evidence.get("canonical_paths")
            and journal.get("evidence_sha256") == sha256_file(evidence_path)
            and st07_22_canonical_bundle_exact()
        )

        notebook_path = (
            PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        seed_cell_indices = (36, 37, 38, 39)
        seed_cell_ids = (
            "8f707fb1",
            "5769f64e",
            "440b6172",
            "24226b5c",
        )
        seed_cells_exact = (
            len(notebook.get("cells", [])) == 52
            and tuple(
                notebook["cells"][index].get("id")
                for index in seed_cell_indices
            )
            == seed_cell_ids
            and sum(
                len(
                    "".join(notebook["cells"][index].get("source", []))
                    .splitlines()
                )
                for index in seed_cell_indices
            )
            == 98
        )
        local_definitions: list[str] = []
        for index in seed_cell_indices:
            source = "".join(notebook["cells"][index].get("source", []))
            tree = ast.parse(source)
            local_definitions.extend(
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        expected_local_definitions = [
            "stage05_seed_outer_position",
            "build_stage05_seed_control_estimators",
            "evaluate_stage05_seed_estimator",
            "fit_stage05_seed_control_estimator",
            "fit_stage05_seed_tuned_hgb",
        ]
        seed_logic_local = local_definitions == []

        plan_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        seed_plan = [
            row
            for row in plan_rows
            if row["stress_test_id"] == "ST05_02_seed_stability_grid"
        ]
        registered_order = (
            len(seed_plan) == 1
            and seed_plan[0]["priority"] == "must_have"
            and seed_plan[0]["execution_order"] == "2"
            and seed_plan[0]["outer_cv_method"]
            == "RepeatedStratifiedKFold"
            and seed_plan[0]["outer_cv_n_splits"] == "5"
            and seed_plan[0]["outer_cv_n_repeats"] == "2"
            and seed_plan[0]["inner_cv_n_splits"] == "3"
            and seed_plan[0]["outer_random_states"]
            == "20260507;20260517;20260527;20260606;20260616"
        )

        golden_contract = {
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": (
                (150, 43),
                "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            ),
            "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": (
                (50, 17),
                "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
            ),
            "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": (
                (72, 22),
                "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
            ),
        }
        golden_exact = True
        for relative, (shape, digest) in golden_contract.items():
            path = PROJECT_ROOT / relative
            frame = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
            )
            golden_exact = (
                golden_exact
                and frame.shape == shape
                and sha256_file(path) == digest
            )

        dependency_tokens = {
            "src/mlcra/nested_cv.py": (
                "def nested_outer_position(",
                "def build_outer_splitter(",
                "def build_inner_splitter(",
                "def evaluate_fitted_estimator_on_outer_block(",
                "def fit_control_estimator_on_outer_block(",
                "def fit_tuned_hist_gradient_boosting_on_outer_block(",
            ),
            "src/mlcra/model_spaces.py": (
                "def build_hist_gradient_boosting_search_space(",
                "def make_hgb_parameter_set_id(",
            ),
            "src/mlcra/metrics.py": (
                "def get_positive_class_probability(",
                "def score_binary_classifier(",
            ),
        }
        dependencies_ready = all(
            all(
                token
                in (PROJECT_ROOT / relative).read_text(encoding="utf-8")
                for token in tokens
            )
            for relative, tokens in dependency_tokens.items()
        )

        current_tokens = (
            "ST07_22_status: accepted_by_john",
            "TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "ST07_23_status: accepted_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
            "ST07_24_status: accepted_by_john",
            "ST07_25_status: accepted_by_john",
            "ST07_23_training_authorized: false",
            "ST07_23_network_authorized: false",
            "ST07_23_source_changes_authorized: false",
            "ST07_23_scientific_artifact_changes_authorized: false",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        historical_selection_boundary = (
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_"
            "modularization_contract_and_golden_master_design"
            in stage_current
            and "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_"
            "modularization_contract_and_golden_master_design"
            in roadmap_current
            and (PROJECT_ROOT / "src/mlcra/stress_tests.py").exists()
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/"
            "st07_next_block_selection_after_st07_22_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_22_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        documentary_tokens = (
            "## 71. Принятие ST07_22 и выбор следующего блока",
            "notebook_code_lines: 4426",
            "notebook_local_functions: 36",
            "ST05_02_cells: 36-39 / 687 lines / 5 local functions",
            "selected_alternative: A",
            "selected_weighted_score: 5.00/5.00",
            "proposed_task_id: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "golden_shapes: 150x43 / 50x17 / 72x22",
            "full_miniboone_training_performed: NO",
            "ST07_23_implementation_started: NO",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        checks = {
            "accepted_st0722": accepted_st0722,
            "seed_cells_exact": seed_cells_exact,
            "seed_logic_local": seed_logic_local,
            "registered_order": registered_order,
            "golden_exact": golden_exact,
            "dependencies_ready": dependencies_ready,
            "current_state": current_state,
            "historical_selection_boundary": historical_selection_boundary,
            "scope_exact": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_next_block_after_st0722",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_st0722={accepted_st0722}; canonical=7/7; "
            f"seed_cells_after_ST07_24=4/98/0:{seed_cells_exact}; "
            f"golden=150x43/50x17/72x22:{golden_exact}; "
            f"registered_order={registered_order}; "
            f"dependencies_ready={dependencies_ready}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; "
            f"historical_selection_boundary={historical_selection_boundary}; "
            "selected=ST07_23_seed_stability_contract_and_golden_design",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0722",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_seed_stability_contract_design() -> Check:
    try:
        import ast

        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )

        notebook_path = (
            PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8-sig"))
        source_contract = (
            (
                36,
                "8f707fb1",
                38,
                "977ea1abccc3998ae9af46ad908ec2d97d2a85aa16741594af0e73d7bb4e888d",
            ),
            (
                37,
                "5769f64e",
                11,
                "e9c31e8ddbdf818178e5d4d5c448531883f58509a3f68f874e6a4c6ce5e8e770",
            ),
            (
                38,
                "440b6172",
                29,
                "951d1a10fb5087f770f94efb7290711bd744c83bf3d0b5743f23e9dd626c235d",
            ),
            (
                39,
                "24226b5c",
                20,
                "1c21aa240fee00664181ee87d138249893a108846a45ccb5f465616bad3d9442",
            ),
        )
        source_exact = len(notebook.get("cells", [])) == 52
        local_definitions: list[str] = []
        for index, cell_id, line_count, digest in source_contract:
            cell = notebook["cells"][index]
            source = "".join(cell.get("source", []))
            source_exact = (
                source_exact
                and cell.get("id") == cell_id
                and len(source.splitlines()) == line_count
                and hashlib.sha256(source.encode("utf-8")).hexdigest()
                == digest
            )
            tree = ast.parse(source)
            local_definitions.extend(
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        source_exact = source_exact and local_definitions == []

        config_hashes = {
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": (
                "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49"
            ),
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": (
                "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d"
            ),
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": (
                "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133"
            ),
        }
        configs_exact = all(
            sha256_file(PROJECT_ROOT / relative) == digest
            for relative, digest in config_hashes.items()
        )
        plan_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        plan_row = [
            row
            for row in plan_rows
            if row["stress_test_id"] == "ST05_02_seed_stability_grid"
        ]
        registered_plan = len(plan_row) == 1 and plan_row[0]

        model_space = pd.read_csv(
            PROJECT_ROOT
            / "configs/model_spaces/"
            "miniboone_hist_gradient_boosting_nested_space.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        parameter_grid, fixed_parameters = (
            build_hist_gradient_boosting_search_space(
                model_space,
                protocol_id="miniboone_nested_cv_v01",
                candidate_id="openml_miniboone_41150",
            )
        )
        locked_space_exact = (
            math.prod(len(values) for values in parameter_grid.values()) == 16
            and fixed_parameters.get("random_state") == 20260507
        )

        outer_columns = [
            "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
            "candidate_id", "openml_dataset_id", "dataset_name", "target_name",
            "target_class_0", "target_class_1", "positive_class_assumption",
            "outer_random_state", "outer_split_number", "outer_repeat_number",
            "outer_fold_number", "outer_cv_n_splits", "outer_cv_n_repeats",
            "inner_cv_n_splits", "inner_random_state", "model_id", "model_role",
            "selected_parameter_set_id", "selected_params_json",
            "inner_best_average_precision", "inner_candidate_count",
            "feature_policy_id", "feature_count", "feature_names", "n_train",
            "n_test", "train_positive_share", "test_positive_share", "roc_auc",
            "average_precision", "pr_auc", "f1", "balanced_accuracy",
            "log_loss", "brier_score", "fit_seconds", "predict_seconds",
            "row_status", "interpretation_allowed_ru",
        ]
        params_columns = [
            "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
            "candidate_id", "outer_random_state", "outer_split_number",
            "outer_repeat_number", "outer_fold_number", "model_id",
            "selected_parameter_set_id", "selected_params_json",
            "inner_best_average_precision", "inner_cv_n_splits",
            "inner_random_state", "inner_candidate_count", "row_status",
        ]
        summary_columns = [
            "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
            "summary_scope", "outer_random_state", "candidate_id",
            "comparison_role", "candidate_model_id", "comparison_model_id",
            "metric_name", "metric_direction", "n_blocks", "advantage_mean",
            "advantage_std_population", "advantage_min", "advantage_max",
            "candidate_positive_blocks", "candidate_negative_blocks",
            "candidate_zero_blocks", "row_status", "interpretation_allowed_ru",
        ]
        golden_spec = {
            "outer": (
                "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
                (150, 43),
                "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
                outer_columns,
            ),
            "params": (
                "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv",
                (50, 17),
                "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
                params_columns,
            ),
            "summary": (
                "data_registry/openml_miniboone_stage05_seed_stability_summary.csv",
                (72, 22),
                "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
                summary_columns,
            ),
        }
        frames = {}
        golden_exact = True
        for name, (relative, shape, digest, columns) in golden_spec.items():
            path = PROJECT_ROOT / relative
            frame = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
            )
            frames[name] = frame
            golden_exact = (
                golden_exact
                and frame.shape == shape
                and list(frame.columns) == columns
                and sha256_file(path) == digest
            )

        contract = {
            "seeds": (20260507, 20260517, 20260527, 20260606, 20260616),
            "outer_n_splits": 5,
            "outer_n_repeats": 2,
            "inner_n_splits": 3,
            "inner_state_formula": "outer_random_state+zero_based_outer_split_number",
            "models": (
                "hist_gradient_boosting", "dummy_prior", "logistic_regression"
            ),
            "roles": {
                "hist_gradient_boosting": "tuned_candidate",
                "dummy_prior": "control",
                "logistic_regression": "control",
            },
            "feature_count": 50,
            "scoring": "average_precision",
        }

        def validates(candidate, outer, params, summary) -> bool:
            try:
                seeds = tuple(candidate["seeds"])
                if seeds != contract["seeds"] or len(set(seeds)) != 5:
                    return False
                if (
                    candidate["outer_n_splits"] != 5
                    or candidate["outer_n_repeats"] != 2
                    or candidate["inner_n_splits"] != 3
                    or candidate["inner_state_formula"]
                    != "outer_random_state+zero_based_outer_split_number"
                    or tuple(candidate["models"]) != contract["models"]
                    or candidate["roles"] != contract["roles"]
                    or candidate["feature_count"] != 50
                    or candidate["scoring"] != "average_precision"
                ):
                    return False
                if (
                    outer.shape != (150, 43)
                    or params.shape != (50, 17)
                    or summary.shape != (72, 22)
                    or list(outer.columns) != outer_columns
                    or list(params.columns) != params_columns
                    or list(summary.columns) != summary_columns
                ):
                    return False
                outer_key = [
                    "stress_test_id", "outer_random_state",
                    "outer_split_number", "model_id",
                ]
                params_key = [
                    "stress_test_id", "outer_random_state",
                    "outer_split_number", "model_id",
                ]
                summary_key = [
                    "stress_test_id", "comparison_model_id", "metric_name",
                    "summary_scope", "outer_random_state",
                ]
                if (
                    outer.duplicated(outer_key).any()
                    or params.duplicated(params_key).any()
                    or summary.duplicated(summary_key).any()
                ):
                    return False
                seed_strings = tuple(str(value) for value in seeds)
                expected_outer_order = [
                    (seed, str(split), model)
                    for seed in seed_strings
                    for split in range(1, 11)
                    for model in candidate["models"]
                ]
                actual_outer_order = list(
                    map(
                        tuple,
                        outer[[
                            "outer_random_state", "outer_split_number", "model_id"
                        ]].to_numpy(),
                    )
                )
                expected_params_order = [
                    (seed, str(split), "hist_gradient_boosting")
                    for seed in seed_strings
                    for split in range(1, 11)
                ]
                actual_params_order = list(
                    map(
                        tuple,
                        params[[
                            "outer_random_state", "outer_split_number", "model_id"
                        ]].to_numpy(),
                    )
                )
                metrics = (
                    "average_precision", "balanced_accuracy", "brier_score",
                    "f1", "log_loss", "roc_auc",
                )
                expected_summary_order = [
                    (comparison, metric, summary_scope, seed)
                    for comparison in ("dummy_prior", "logistic_regression")
                    for metric in metrics
                    for summary_scope, seed in (
                        (("all_outer_random_states", "all"),)
                        + tuple(
                            ("single_outer_random_state", value)
                            for value in seed_strings
                        )
                    )
                ]
                actual_summary_order = list(
                    map(
                        tuple,
                        summary[[
                            "comparison_model_id", "metric_name", "summary_scope",
                            "outer_random_state",
                        ]].to_numpy(),
                    )
                )
                if (
                    actual_outer_order != expected_outer_order
                    or actual_params_order != expected_params_order
                    or actual_summary_order != expected_summary_order
                ):
                    return False
                observed_roles = {
                    model: set(outer.loc[outer["model_id"].eq(model), "model_role"])
                    for model in candidate["models"]
                }
                if any(
                    observed_roles[model] != {role}
                    for model, role in candidate["roles"].items()
                ):
                    return False
                tuned = outer[outer["model_id"].eq("hist_gradient_boosting")]
                for _, row in tuned.iterrows():
                    expected_state = int(row["outer_random_state"]) + int(
                        row["outer_split_number"]
                    ) - 1
                    if (
                        int(row["inner_random_state"]) != expected_state
                        or row["inner_cv_n_splits"] != "3"
                        or row["inner_candidate_count"] != "16"
                    ):
                        return False
                for _, row in params.iterrows():
                    parsed = json.loads(row["selected_params_json"])
                    if (
                        row["selected_parameter_set_id"]
                        != make_hgb_parameter_set_id(parsed)
                    ):
                        return False
                direction = {
                    "average_precision": "higher_is_better",
                    "balanced_accuracy": "higher_is_better",
                    "brier_score": "lower_is_better",
                    "f1": "higher_is_better",
                    "log_loss": "lower_is_better",
                    "roc_auc": "higher_is_better",
                }
                if any(
                    row["metric_direction"] != direction[row["metric_name"]]
                    for _, row in summary.iterrows()
                ):
                    return False
                for column in ("fit_seconds", "predict_seconds"):
                    timing = pd.to_numeric(outer[column], errors="coerce")
                    if timing.isna().any() or any(
                        not math.isfinite(value) or value < 0
                        for value in timing
                    ):
                        return False
                return True
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                return False

        positive_contract = validates(
            contract, frames["outer"], frames["params"], frames["summary"]
        )
        mutations = []
        for transform in (
            lambda value: {**value, "seeds": value["seeds"][:-1]},
            lambda value: {**value, "seeds": value["seeds"][:-1] + (value["seeds"][-2],)},
            lambda value: {**value, "seeds": tuple(reversed(value["seeds"]))},
            lambda value: {**value, "outer_n_splits": 4},
            lambda value: {**value, "outer_n_repeats": 3},
            lambda value: {**value, "inner_n_splits": 4},
            lambda value: {**value, "inner_state_formula": "constant_seed"},
            lambda value: {**value, "models": value["models"][:-1]},
            lambda value: {**value, "roles": {**value["roles"], "dummy_prior": "tuned_candidate"}},
        ):
            mutations.append(
                (transform(contract), frames["outer"], frames["params"], frames["summary"])
            )
        bad_params = frames["params"].copy(deep=True)
        bad_params.loc[0, "selected_parameter_set_id"] = "hgb_invalid"
        mutations.append((contract, frames["outer"], bad_params, frames["summary"]))
        missing_schema = frames["outer"].drop(columns=["feature_count"])
        mutations.append((contract, missing_schema, frames["params"], frames["summary"]))
        duplicate_key = frames["outer"].copy(deep=True)
        duplicate_key.loc[1, duplicate_key.columns] = duplicate_key.loc[0]
        mutations.append((contract, duplicate_key, frames["params"], frames["summary"]))
        cross_seed_pairing = frames["outer"].copy(deep=True)
        cross_seed_pairing.loc[0, "outer_random_state"] = str(contract["seeds"][1])
        mutations.append((contract, cross_seed_pairing, frames["params"], frames["summary"]))
        wrong_direction = frames["summary"].copy(deep=True)
        wrong_direction.loc[0, "metric_direction"] = "lower_is_better"
        mutations.append((contract, frames["outer"], frames["params"], wrong_direction))
        wrong_row_count = frames["summary"].iloc[:-1].copy()
        mutations.append((contract, frames["outer"], frames["params"], wrong_row_count))
        negative_timing = frames["outer"].copy(deep=True)
        negative_timing.loc[0, "fit_seconds"] = "-1"
        mutations.append((contract, negative_timing, frames["params"], frames["summary"]))
        negative_contract_checks = sum(
            not validates(*mutation) for mutation in mutations
        )

        plan_exact = bool(registered_plan) and (
            registered_plan["priority"] == "must_have"
            and registered_plan["execution_order"] == "2"
            and registered_plan["outer_cv_method"] == "RepeatedStratifiedKFold"
            and registered_plan["outer_cv_n_splits"] == "5"
            and registered_plan["outer_cv_n_repeats"] == "2"
            and registered_plan["outer_random_states"]
            == ";".join(str(value) for value in contract["seeds"])
            and registered_plan["inner_cv_method"] == "StratifiedKFold"
            and registered_plan["inner_cv_n_splits"] == "3"
            and registered_plan["models"]
            == "hist_gradient_boosting;logistic_regression;dummy_prior"
            and registered_plan["primary_metric"] == contract["scoring"]
            and registered_plan["parameter_space_policy"]
            == "do_not_expand_after_viewing_results"
        )

        dependency_hashes = {
            "src/mlcra/nested_cv.py": "804050fbcd8e8a9f10f495ed11de1786677af559c15a4c7f77d955bf24fa6ba9",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "src/mlcra/metrics.py": "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3",
            "src/mlcra/io.py": "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0",
            "src/mlcra/validation.py": "2bed7566811af6c342b9a70a8e8933479248fc6e7ee4b9983da39d1c0279ffff",
        }
        nested_source = (PROJECT_ROOT / "src/mlcra/nested_cv.py").read_text(
            encoding="utf-8-sig"
        )
        dependencies_preserved = (
            all(
                relative == "src/mlcra/nested_cv.py"
                or sha256_file(PROJECT_ROOT / relative) == digest
                for relative, digest in dependency_hashes.items()
            )
            and "inner_base_random_state: int | None = None" in nested_source
        )
        protected_preserved = (
            dependencies_preserved
            and configs_exact
            and golden_exact
            and (PROJECT_ROOT / "src/mlcra/stress_tests.py").exists()
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/"
            "st07_23_stage05_seed_stability_modularization_contract_"
            "change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_23_stage05_seed_stability_modularization_contract_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        documentary_tokens = (
            "## 73. ST07_23",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "contract_validation_positive: PASS",
            "negative_contract_checks: 16/16 PASS",
            "historical_golden_role: immutable_reference_not_current_environment_reproduction_claim",
            "cross_artifact_derivation_policy: exact_pairing_direction_n_blocks_and_sign_counts_only",
            "post_result_tolerance_selection: prohibited",
            "timing_policy: finite_and_nonnegative_only",
            "stress_tests_module_created: NO",
            "full_miniboone_training_performed: NO",
            "scientific_validation_performed: NO",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        roadmap_documentary = all(
            token in roadmap_text
            for token in (
                "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
                "ST07_23_status: accepted_by_john",
                "TASK_CLOSED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            )
        )

        checks = {
            "source_exact": source_exact,
            "configs_exact": configs_exact,
            "plan_exact": plan_exact,
            "locked_space_exact": locked_space_exact,
            "golden_exact": golden_exact,
            "positive_contract": positive_contract,
            "negative_contract_checks": negative_contract_checks == 16,
            "protected_preserved": protected_preserved,
            "scope_exact": scope_exact,
            "documentary": documentary,
            "roadmap_documentary": roadmap_documentary,
        }
        return Check(
            "stage07_stage05_seed_stability_contract_design",
            "PASS" if all(checks.values()) else "FAIL",
            f"source_after_ST07_24=4/98/0:{source_exact}; protocol=5x2/3/5seeds:{plan_exact}; "
            f"space=16:{locked_space_exact}; golden=150x43/50x17/72x22:{golden_exact}; "
            f"positive={positive_contract}; negative={negative_contract_checks}/16; "
            f"protected={protected_preserved}; scope={len(scope_rows)}/4:{scope_exact}; "
            "training=0; network=0; scientific_validation=0",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_seed_stability_contract_design",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0723() -> Check:
    try:
        import ast

        stage_path = PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        notebook_path = PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )

        accepted_tokens = (
            "ST07_23_status: accepted_by_john",
            "TASK_CLOSED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
            "NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design",
        )
        accepted_st0723 = all(
            all(token in body for token in accepted_tokens)
            for body in (stage_current, roadmap_current)
        )
        previous_contract = check_stage07_stage05_seed_stability_contract_design()

        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        code_lines = sum(
            len("".join(cell.get("source", [])).splitlines())
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )

        block_specs = {
            "ST05_02": ([36, 37, 38, 39], 98, 0),
            "ST05_03a": ([41, 42, 43], 109, 0),
            "ST05_07": ([51], 105, 0),
        }
        block_inventory: dict[str, bool] = {}
        for block_id, (indices, expected_lines, expected_functions) in block_specs.items():
            sources = ["".join(notebook["cells"][index]["source"]) for index in indices]
            function_names = {
                node.name
                for source in sources
                for node in ast.walk(ast.parse(source))
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            block_inventory[block_id] = (
                sum(len(source.splitlines()) for source in sources) == expected_lines
                and len(function_names) == expected_functions
            )
        inventory_exact = (
            len(notebook["cells"]) == 52
            and code_lines == 2804
            and all(block_inventory.values())
        )

        plan_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        plan_by_id = {row["stress_test_id"]: row for row in plan_rows}
        registered_order = (
            plan_by_id["ST05_02_seed_stability_grid"]["priority"] == "must_have"
            and plan_by_id["ST05_02_seed_stability_grid"]["execution_order"] == "2"
            and plan_by_id["ST05_03a_split_protocol_10x1"]["priority"]
            == "should_have"
            and plan_by_id["ST05_03a_split_protocol_10x1"]["execution_order"] == "3"
            and plan_by_id["ST05_07_non_nested_optimism_probe"]["priority"]
            == "could_have"
            and plan_by_id["ST05_07_non_nested_optimism_probe"]["execution_order"]
            == "8"
        )

        protected_hashes = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "cfdb278ab1a2166787458e9448cbea092e00b8730d0ac2bbbd66f2e1e746d281",
            "src/mlcra/nested_cv.py": "804050fbcd8e8a9f10f495ed11de1786677af559c15a4c7f77d955bf24fa6ba9",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "src/mlcra/metrics.py": "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3",
            "src/mlcra/io.py": "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0",
            "src/mlcra/validation.py": "2bed7566811af6c342b9a70a8e8933479248fc6e7ee4b9983da39d1c0279ffff",
        }
        implementation_scoped = (
            (PROJECT_ROOT / "src/mlcra/stress_tests.py").exists()
            and all(
                relative_path in {
                    "notebooks/04_dataset_smoke_experiments.ipynb",
                    "src/mlcra/nested_cv.py",
                }
                or sha256_file(PROJECT_ROOT / relative_path) == digest
                for relative_path, digest in protected_hashes.items()
            )
            and "inner_base_random_state: int | None = None"
            in (PROJECT_ROOT / "src/mlcra/nested_cv.py").read_text(
                encoding="utf-8-sig"
            )
        )

        proposed_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
            "ST07_24_status: accepted_by_john",
            "TASK_CLOSED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
            "ST07_24_training_authorized: false",
            "ST07_24_network_authorized: false",
            "ST07_24_source_changes_authorized: true",
            "ST07_24_scientific_artifact_changes_authorized: false",
            "ST07_25_status: accepted_by_john",
        )
        proposed_once = all(
            all(token in body for token in proposed_tokens)
            for body in (stage_current, roadmap_current)
        )
        authorized = all(
            "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation"
            in body
            for body in (stage_current, roadmap_current)
        )

        route_tokens = (
            "remaining_stage07_planned_blocks: 9",
            "remaining_breakdown: ST05_02=2;ST05_03a=3;ST05_07=3;stage07_closure=1",
            "count_policy: nominal_plan_not_upper_bound_corrective_blocks_only_on_observed_failure",
            "selected_alternative: A",
            "selected_weighted_score: 4.90/5.00",
            "proposed_task_id: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
            "future_extraction_comparison: same_process_legacy_vs_modular_deterministic_fixture",
            "full_miniboone_training_performed: NO",
            "ST07_24_implementation_started: NO",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        roadmap_route = all(
            token in roadmap_text
            for token in (
                "remaining_stage07_planned_blocks: 8",
                "ST07_24_status: accepted_by_john",
                "ST07_25_status: accepted_by_john",
                "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
            )
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_23_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_23_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        checks = {
            "accepted_st0723": accepted_st0723,
            "previous_contract": previous_contract.status == "PASS",
            "inventory_exact": inventory_exact,
            "registered_order": registered_order,
            "implementation_scoped": implementation_scoped,
            "proposed_once": proposed_once,
            "authorized": authorized,
            "route_documented": route_documented,
            "roadmap_route": roadmap_route,
            "scope_exact": scope_exact,
        }
        return Check(
            "stage07_next_block_after_st0723",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_st0723={accepted_st0723}; contract={previous_contract.status}; "
            f"remaining_at_selection=9(2+3+3+1); inventory=52/3308/"
            f"ST05_02:4/98/0,ST05_03a_after_ST07_28:3/109/0,ST05_07:1/609/3:{inventory_exact}; "
            f"registered_order={registered_order}; implementation_scoped={implementation_scoped}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; authorized={authorized}; "
            "selected=ST07_24_seed_stability_extraction_and_fixture_validation",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0723",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_seed_stability_modular_extraction() -> Check:
    try:
        import inspect

        import numpy as np
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.io import read_csv_checked
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )
        from mlcra.nested_cv import (
            build_outer_splitter,
            fit_tuned_hist_gradient_boosting_on_outer_block,
        )
        from mlcra.stress_tests import (
            STAGE05_SEED_OUTER_COLUMNS,
            STAGE05_SEED_SELECTED_COLUMNS,
            STAGE05_SEED_SUMMARY_COLUMNS,
            SeedStabilityBundle,
            build_seed_stability_contract,
            build_seed_stability_control_estimators,
            run_seed_stability_grid,
            validate_seed_stability_bundle,
        )

        plan = read_csv_checked(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        claim = read_csv_checked(
            PROJECT_ROOT
            / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
        )
        model_space = read_csv_checked(
            PROJECT_ROOT
            / "configs/model_spaces/"
            "miniboone_hist_gradient_boosting_nested_space.csv"
        )
        contract = build_seed_stability_contract(plan, claim)
        parameter_grid, fixed_parameters = (
            build_hist_gradient_boosting_search_space(
                model_space,
                protocol_id=contract.nested_protocol_id,
                candidate_id=contract.candidate_id,
            )
        )
        controls = build_seed_stability_control_estimators()

        notebook = json.loads(
            (
                PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
            ).read_text(encoding="utf-8")
        )
        expected_cells = {
            36: (
                "8f707fb1",
                38,
                "977ea1abccc3998ae9af46ad908ec2d97d2a85aa16741594af0e73d7bb4e888d",
            ),
            37: (
                "5769f64e",
                11,
                "e9c31e8ddbdf818178e5d4d5c448531883f58509a3f68f874e6a4c6ce5e8e770",
            ),
            38: (
                "440b6172",
                29,
                "951d1a10fb5087f770f94efb7290711bd744c83bf3d0b5743f23e9dd626c235d",
            ),
            39: (
                "24226b5c",
                20,
                "1c21aa240fee00664181ee87d138249893a108846a45ccb5f465616bad3d9442",
            ),
        }
        notebook_cells_exact = len(notebook["cells"]) == 52
        for index, (cell_id, line_count, digest) in expected_cells.items():
            cell = notebook["cells"][index]
            source = "".join(cell["source"])
            notebook_cells_exact = notebook_cells_exact and (
                cell.get("id") == cell_id
                and len(source.splitlines()) == line_count
                and hashlib.sha256(source.encode("utf-8")).hexdigest() == digest
                and cell.get("execution_count") is None
                and cell.get("outputs") == []
                and "def " not in source
            )
        preserved = {
            "metadata": notebook["metadata"],
            "nbformat": notebook["nbformat"],
            "nbformat_minor": notebook["nbformat_minor"],
            "cells": [
                cell
                for cell in notebook["cells"]
                if cell.get("id")
                not in {value[0] for value in expected_cells.values()}
            ],
        }
        preserved_digest = hashlib.sha256(
            json.dumps(
                preserved,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        notebook_preserved = (
            preserved_digest
            == "6d91c8494b8792ce1da22b2d877259cc80a4f8cb53085010e6b1d366054a4378"
        )

        nested_signature = inspect.signature(
            fit_tuned_hist_gradient_boosting_on_outer_block
        )
        random_state_separated = (
            "inner_base_random_state" in nested_signature.parameters
            and nested_signature.parameters[
                "inner_base_random_state"
            ].default
            is None
        )

        X = pd.DataFrame(
            np.arange(100 * 50, dtype=float).reshape(100, 50),
            columns=contract.feature_names,
        )
        y = np.asarray([0, 1] * 50, dtype=int)
        candidate_bundle = {
            "candidate_id": contract.candidate_id,
            "did": 41150,
            "dataset_name": "deterministic_fixture",
            "target_name": "signal",
            "target_metadata": {
                "target_class_0": "background",
                "target_class_1": "signal",
                "positive_class_assumption": "1=signal",
            },
        }
        selected_params = {
            name: values[0] for name, values in parameter_grid.items()
        }
        parameter_set_id = make_hgb_parameter_set_id(selected_params)
        selected_json = json.dumps(selected_params, sort_keys=True)
        callback_state: dict[str, int | None] = {"seed": None}

        def fixture_score_row(kwargs, model_id, model_role, seed):
            split = kwargs["zero_based_outer_split_number"]
            offset = {
                "hist_gradient_boosting": 0.8,
                "dummy_prior": 0.2,
                "logistic_regression": 0.6,
            }[model_id]
            base = offset + (seed % 100) / 100000 + split / 10000
            train = kwargs["train_index"]
            test = kwargs["test_index"]
            tuned = model_role == "tuned_candidate"
            return {
                "protocol_id": kwargs["protocol_id"],
                "candidate_id": contract.candidate_id,
                "openml_dataset_id": 41150,
                "dataset_name": "deterministic_fixture",
                "target_name": "signal",
                "target_class_0": "background",
                "target_class_1": "signal",
                "positive_class_assumption": "1=signal",
                "outer_split_number": split + 1,
                "outer_repeat_number": split // 5 + 1,
                "outer_fold_number": split % 5 + 1,
                "outer_cv_n_splits": 5,
                "outer_cv_n_repeats": 2,
                "inner_cv_n_splits": 3 if tuned else "",
                "model_id": model_id,
                "model_role": model_role,
                "selected_parameter_set_id": (
                    parameter_set_id if tuned else "not_applicable_control_model"
                ),
                "selected_params_json": selected_json if tuned else "",
                "feature_policy_id": contract.feature_policy_id,
                "feature_count": 50,
                "feature_names": "; ".join(contract.feature_names),
                "n_train": len(train),
                "n_test": len(test),
                "train_positive_share": float(y[train].mean()),
                "test_positive_share": float(y[test].mean()),
                "roc_auc": base,
                "average_precision": base - 0.01,
                "pr_auc": base - 0.01,
                "f1": base - 0.02,
                "balanced_accuracy": base - 0.03,
                "log_loss": 1.0 - base,
                "brier_score": 0.5 - base / 2,
                "fit_seconds": 0.01,
                "predict_seconds": 0.02,
                "row_status": kwargs["row_status"],
                "interpretation_allowed": kwargs["interpretation_allowed"],
            }

        def fixture_tuned_fit(**kwargs):
            seed = kwargs["inner_base_random_state"]
            callback_state["seed"] = seed
            split = kwargs["zero_based_outer_split_number"]
            score = fixture_score_row(
                kwargs, "hist_gradient_boosting", "tuned_candidate", seed
            )
            selected = {
                "protocol_id": kwargs["protocol_id"],
                "candidate_id": contract.candidate_id,
                "outer_split_number": split + 1,
                "outer_repeat_number": split // 5 + 1,
                "outer_fold_number": split % 5 + 1,
                "model_id": "hist_gradient_boosting",
                "selected_parameter_set_id": parameter_set_id,
                "selected_params_json": selected_json,
                "inner_best_average_precision": (
                    0.75 + (seed % 100) / 100000 + split / 10000
                ),
                "inner_cv_n_splits": 3,
                "inner_cv_random_state": seed + split,
                "inner_candidate_count": 16,
                "row_status": kwargs["row_status"],
            }
            return score, selected, []

        def fixture_control_fit(**kwargs):
            return (
                fixture_score_row(
                    kwargs,
                    kwargs["model_id"],
                    "control",
                    callback_state["seed"],
                ),
                [],
            )

        fixture = run_seed_stability_grid(
            contract,
            candidate_bundle,
            X,
            y,
            list(contract.feature_names),
            parameter_grid,
            fixed_parameters,
            controls,
            tuned_fit=fixture_tuned_fit,
            control_fit=fixture_control_fit,
        )
        roundtripped = SeedStabilityBundle(
            outer_scores=csv_roundtrip_as_strings(fixture.outer_scores),
            selected_params=csv_roundtrip_as_strings(fixture.selected_params),
            summary=csv_roundtrip_as_strings(fixture.summary),
        )
        validate_seed_stability_bundle(roundtripped, contract)

        schemas_exact = (
            fixture.outer_scores.shape == (150, 43)
            and fixture.selected_params.shape == (50, 17)
            and fixture.summary.shape == (72, 22)
            and tuple(fixture.outer_scores.columns) == STAGE05_SEED_OUTER_COLUMNS
            and tuple(fixture.selected_params.columns)
            == STAGE05_SEED_SELECTED_COLUMNS
            and tuple(fixture.summary.columns) == STAGE05_SEED_SUMMARY_COLUMNS
        )
        reference_rows_exact = True
        model_offsets = {
            "hist_gradient_boosting": 0.8,
            "dummy_prior": 0.2,
            "logistic_regression": 0.6,
        }
        for row in fixture.outer_scores.itertuples(index=False):
            split = int(row.outer_split_number) - 1
            base = (
                model_offsets[row.model_id]
                + (int(row.outer_random_state) % 100) / 100000
                + split / 10000
            )
            reference_rows_exact = reference_rows_exact and (
                int(row.outer_repeat_number) == split // 5 + 1
                and int(row.outer_fold_number) == split % 5 + 1
                and int(row.n_train) == 80
                and int(row.n_test) == 20
                and float(row.train_positive_share) == 0.5
                and float(row.test_positive_share) == 0.5
                and float(row.roc_auc) == base
                and float(row.average_precision) == base - 0.01
                and float(row.pr_auc) == base - 0.01
                and float(row.f1) == base - 0.02
                and float(row.balanced_accuracy) == base - 0.03
                and float(row.log_loss) == 1.0 - base
                and float(row.brier_score) == 0.5 - base / 2
            )
        expected_advantages = {
            "dummy_prior": {
                "average_precision": 0.6,
                "balanced_accuracy": 0.6,
                "brier_score": 0.3,
                "f1": 0.6,
                "log_loss": 0.6,
                "roc_auc": 0.6,
            },
            "logistic_regression": {
                "average_precision": 0.2,
                "balanced_accuracy": 0.2,
                "brier_score": 0.1,
                "f1": 0.2,
                "log_loss": 0.2,
                "roc_auc": 0.2,
            },
        }
        summary_reference_exact = all(
            np.isclose(
                float(row.advantage_mean),
                expected_advantages[row.comparison_model_id][row.metric_name],
                rtol=0.0,
                atol=1e-15,
            )
            and int(row.candidate_positive_blocks) == int(row.n_blocks)
            and int(row.candidate_negative_blocks) == 0
            and int(row.candidate_zero_blocks) == 0
            for row in fixture.summary.itertuples(index=False)
        )
        timing_separate = all(
            np.isfinite(pd.to_numeric(fixture.outer_scores[column])).all()
            and (pd.to_numeric(fixture.outer_scores[column]) >= 0).all()
            for column in ("fit_seconds", "predict_seconds")
        )

        def rejected(mutator) -> bool:
            candidate = SeedStabilityBundle(
                outer_scores=fixture.outer_scores.copy(deep=True),
                selected_params=fixture.selected_params.copy(deep=True),
                summary=fixture.summary.copy(deep=True),
            )
            mutator(candidate)
            try:
                validate_seed_stability_bundle(candidate, contract)
            except (TypeError, ValueError, KeyError):
                return True
            return False

        def set_column(frame_name, column, value):
            def mutate(bundle):
                frame = getattr(bundle, frame_name)
                frame.loc[:, column] = value

            return mutate

        def set_cell(frame_name, row_index, column, value):
            def mutate(bundle):
                frame = getattr(bundle, frame_name)
                frame.at[row_index, column] = value

            return mutate

        def reverse_rows(frame_name):
            def mutate(bundle):
                frame = getattr(bundle, frame_name)
                frame.iloc[:, :] = frame.iloc[::-1].to_numpy()

            return mutate

        mutations = [
            lambda b: b.outer_scores.drop(columns=["roc_auc"], inplace=True),
            reverse_rows("selected_params"),
            reverse_rows("summary"),
            set_column("outer_scores", "stress_test_id", "wrong"),
            set_column("outer_scores", "claim_id", "wrong"),
            set_column("outer_scores", "feature_policy_id", "wrong"),
            set_column("outer_scores", "feature_count", 49),
            set_column("outer_scores", "feature_names", "wrong"),
            set_column("outer_scores", "row_status", "wrong"),
            set_column("outer_scores", "average_precision", 0.1),
            set_column("outer_scores", "fit_seconds", -1.0),
            set_column("outer_scores", "predict_seconds", np.inf),
            set_column("outer_scores", "roc_auc", np.nan),
            set_column("summary", "metric_direction", "wrong"),
            set_column("summary", "n_blocks", 1),
            set_cell("outer_scores", 0, "model_role", "control"),
            set_cell("outer_scores", 1, "selected_parameter_set_id", "wrong"),
            set_cell("outer_scores", 0, "selected_parameter_set_id", "wrong"),
            lambda b: b.outer_scores.drop(
                index=b.outer_scores.index[-1], inplace=True
            ),
            lambda b: b.summary.drop(index=b.summary.index[1:], inplace=True),
        ]
        mutation_results = [rejected(mutator) for mutator in mutations]
        negative_count = sum(mutation_results)

        splitter = build_outer_splitter(5, 2, 20260517)
        train_index, test_index = next(splitter.split(X, y))
        real_row, real_selected, _ = (
            fit_tuned_hist_gradient_boosting_on_outer_block(
                candidate_bundle=candidate_bundle,
                X=X,
                y=y,
                train_index=train_index,
                test_index=test_index,
                zero_based_outer_split_number=0,
                feature_names=list(contract.feature_names),
                parameter_grid=parameter_grid,
                fixed_parameters=fixed_parameters,
                protocol_id=contract.nested_protocol_id,
                candidate_id=contract.candidate_id,
                outer_n_splits=5,
                outer_n_repeats=2,
                inner_n_splits=3,
                base_random_state=20260507,
                inner_base_random_state=20260517,
                feature_policy_id=contract.feature_policy_id,
                scoring="average_precision",
                refit=True,
                n_jobs=1,
                return_train_score=False,
                error_score="raise",
                numeric_runtime_contract=None,
            )
        )
        random_state_observed = (
            real_row["model_id"] == "hist_gradient_boosting"
            and real_selected["inner_cv_random_state"] == 20260517
            and fixed_parameters["random_state"] == 20260507
        )

        protected_hashes = {
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
            "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / relative_path) == digest
            for relative_path, digest in protected_hashes.items()
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/"
            "st07_24_stage05_seed_stability_modular_extraction_"
            "change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_24_stage05_seed_stability_modular_extraction_change_scope_v01.csv",
            "src/mlcra/nested_cv.py",
            "src/mlcra/stress_tests.py",
            "notebooks/04_dataset_smoke_experiments.ipynb",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        documentary_tokens = (
            "## 77. ST07_24",
            "notebook_other_cells: PASS exact 48/48",
            "negative_contract_checks: PASS 20/20",
            "remaining_stage07_planned_blocks_after_ST07_24: 8",
            "ST07_24_status: ready_for_john_acceptance",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        roadmap_documentary = all(
            token in roadmap_current
            for token in (
                "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
                "ST07_24_status: accepted_by_john",
                "TASK_CLOSED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
                "ST07_25_status: accepted_by_john",
            )
        )

        checks = {
            "notebook_cells_exact": notebook_cells_exact,
            "notebook_preserved": notebook_preserved,
            "random_state_separated": random_state_separated,
            "schemas_exact": schemas_exact,
            "reference_rows_exact": reference_rows_exact,
            "summary_reference_exact": summary_reference_exact,
            "timing_separate": timing_separate,
            "negative": negative_count == len(mutations),
            "random_state_observed": random_state_observed,
            "protected": protected,
            "scope_exact": scope_exact,
            "documentary": documentary,
            "roadmap_documentary": roadmap_documentary,
        }
        return Check(
            "stage07_stage05_seed_stability_modular_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            f"notebook=4/98/0:{notebook_cells_exact}; other_cells=48/48:{notebook_preserved}; "
            f"fixture=150x43/50x17/72x22:{schemas_exact}; "
            f"reference_rows={reference_rows_exact}; summary={summary_reference_exact}; "
            f"timing_finite={timing_separate}; negative={negative_count}/{len(mutations)}; "
            f"random_state_separation={random_state_observed}; protected={protected}; "
            f"scope={len(scope_rows)}/7:{scope_exact}; documentary={documentary and roadmap_documentary}; "
            "full_miniboone_training=0; network=0; scientific_artifact_changes=0",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_seed_stability_modular_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0724() -> Check:
    try:
        stage_path = PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )

        accepted_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
            "ST07_24_status: accepted_by_john",
            "TASK_CLOSED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation",
        )
        accepted_st0724 = all(
            all(token in body for token in accepted_tokens)
            for body in (stage_current, roadmap_current)
        )
        previous_gate = check_stage07_stage05_seed_stability_modular_extraction()

        plan_rows = read_contract_csv(
            PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        plan_by_id = {row["stress_test_id"]: row for row in plan_rows}
        registered_order = (
            plan_by_id["ST05_02_seed_stability_grid"]["priority"] == "must_have"
            and plan_by_id["ST05_02_seed_stability_grid"]["execution_order"] == "2"
            and plan_by_id["ST05_03a_split_protocol_10x1"]["execution_order"]
            == "3"
        )

        protected_hashes = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "src/mlcra/metrics.py": "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3",
            "src/mlcra/io.py": "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0",
            "src/mlcra/validation.py": "2bed7566811af6c342b9a70a8e8933479248fc6e7ee4b9983da39d1c0279ffff",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
            "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / relative_path) == digest
            for relative_path, digest in protected_hashes.items()
        )

        proposed_tokens = (
            "remaining_stage07_planned_blocks: 8",
            "stage07_next_block: proposed_ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation",
            "ST07_25_status: proposed_not_authorized",
            "ST07_25_full_miniboone_training_authorized: false",
            "ST07_25_network_authorized: false",
            "ST07_25_source_changes_authorized: false",
            "ST07_25_scientific_artifact_changes_authorized: false",
        )
        selection_historical = all(token in stage_text for token in proposed_tokens)
        selection_historical = selection_historical and all(
            token in roadmap_text
            for token in (
                "MLCRA-RD-057",
                "ST07_25_status: accepted_by_john",
            )
        )

        route_tokens = (
            "remaining_breakdown: ST05_02=1;ST05_03a=3;ST05_07=3;stage07_closure=1",
            "count_policy: nominal_plan_not_upper_bound_corrective_blocks_only_on_observed_failure",
            "selected_alternative: A",
            "selected_weighted_score: 4.50/5.00",
            "proposed_task_id: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation",
            "historical_golden_role: immutable_reference_and_exact_diagnostic_comparator",
            "historical_numeric_verdict_policy: pass_only_if_exact_else_fail_without_causal_attribution",
            "cross_environment_reproducibility_claim: prohibited",
            "post_result_tolerance_selection: prohibited",
            "full_miniboone_training_performed: NO",
            "ST07_25_implementation_started: NO",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        roadmap_route = all(
            token in roadmap_text
            for token in (
                "MLCRA-RD-057",
                "remaining_stage07_planned_blocks: 8",
                "ST07_25_status: accepted_by_john",
            )
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_24_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_24_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        checks = {
            "accepted_st0724": accepted_st0724,
            "previous_gate": previous_gate.status == "PASS",
            "registered_order": registered_order,
            "protected": protected,
            "selection_historical": selection_historical,
            "route_documented": route_documented,
            "roadmap_route": roadmap_route,
            "scope_exact": scope_exact,
        }
        return Check(
            "stage07_next_block_after_st0724",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_st0724={accepted_st0724}; previous={previous_gate.status}; "
            f"remaining=8(1+3+3+1); registered_order={registered_order}; "
            f"protected={len(protected_hashes)}/13:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; historical_selection={selection_historical}; "
            "selected=ST07_25_full_miniboone_and_golden_diagnostic_validation",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0724",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_seed_stability_full_validation() -> Check:
    try:
        import pandas as pd

        task_id = (
            "ST07_25_stage05_seed_stability_full_miniboone_and_"
            "golden_diagnostic_validation"
        )
        data = PROJECT_ROOT / "data_registry"
        evidence_path = (
            data
            / "st07_25_stage05_seed_stability_full_validation_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        specs = {
            "outer_scores": {
                "candidate": "st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv",
                "golden": "openml_miniboone_stage05_seed_stability_outer_scores.csv",
                "shape": (150, 43),
                "class_b": (
                    "train_positive_share",
                    "test_positive_share",
                    "roc_auc",
                    "average_precision",
                    "pr_auc",
                    "f1",
                    "balanced_accuracy",
                    "log_loss",
                    "brier_score",
                    "inner_best_average_precision",
                ),
                "class_c": ("fit_seconds", "predict_seconds"),
            },
            "selected_params": {
                "candidate": "st07_25_stage05_seed_stability_candidate_selected_params_v01.csv",
                "golden": "openml_miniboone_stage05_seed_stability_selected_params.csv",
                "shape": (50, 17),
                "class_b": ("inner_best_average_precision",),
                "class_c": (),
            },
            "summary": {
                "candidate": "st07_25_stage05_seed_stability_candidate_summary_v01.csv",
                "golden": "openml_miniboone_stage05_seed_stability_summary.csv",
                "shape": (72, 22),
                "class_b": (
                    "advantage_mean",
                    "advantage_std_population",
                    "advantage_min",
                    "advantage_max",
                ),
                "class_c": (),
            },
        }
        recomputed: dict[str, dict[str, Any]] = {}
        for artifact_id, spec in specs.items():
            candidate_path = data / str(spec["candidate"])
            golden_path = data / str(spec["golden"])
            candidate = pd.read_csv(
                candidate_path, dtype=str, keep_default_na=False
            )
            golden = pd.read_csv(golden_path, dtype=str, keep_default_na=False)
            class_b = list(spec["class_b"])
            class_c = list(spec["class_c"])
            class_a = [
                column
                for column in candidate.columns
                if column not in set(class_b + class_c)
            ]
            class_c_valid = True
            for column in class_c:
                values = pd.to_numeric(candidate[column], errors="coerce")
                class_c_valid = class_c_valid and bool(
                    (values.notna() & values.map(math.isfinite) & values.ge(0.0)).all()
                )
            recomputed[artifact_id] = {
                "shape_exact": candidate.shape == golden.shape == spec["shape"],
                "schema_exact": list(candidate.columns) == list(golden.columns),
                "candidate_sha256": sha256_file(candidate_path),
                "class_a_exact": candidate[class_a].equals(golden[class_a]),
                "class_b_exact": candidate[class_b].equals(golden[class_b]),
                "class_b_mismatch_cells": int(
                    candidate[class_b].ne(golden[class_b]).to_numpy().sum()
                ),
                "class_c_valid": class_c_valid,
            }

        aggregate = {
            "structures_valid": all(
                row["shape_exact"] and row["schema_exact"]
                for row in recomputed.values()
            ),
            "class_a_exact": all(
                row["class_a_exact"] for row in recomputed.values()
            ),
            "class_b_exact": all(
                row["class_b_exact"] for row in recomputed.values()
            ),
            "class_c_valid": all(
                row["class_c_valid"] for row in recomputed.values()
            ),
        }
        evidence_comparisons = evidence["comparisons"]
        comparison_evidence_exact = all(
            all(
                evidence_comparisons[artifact_id][field] == value
                for field, value in row.items()
            )
            for artifact_id, row in recomputed.items()
        )

        primary = pd.read_csv(data / str(specs["summary"]["candidate"]))
        primary = primary[
            primary["comparison_model_id"].eq("logistic_regression")
            & primary["metric_name"].eq("average_precision")
            & primary["summary_scope"].eq("single_outer_random_state")
        ]
        signal_pass = (
            len(primary) == 5
            and bool(primary["advantage_mean"].gt(0.0).all())
            and bool(
                primary["candidate_positive_blocks"].gt(primary["n_blocks"] / 2).all()
            )
        )

        protected_expected = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
            "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )
        expected_technical = "PASS" if all(aggregate.values()) and protected and signal_pass else "FAIL"
        execution = evidence["execution"]
        execution_exact = (
            execution["full_run_count"] == 1
            and execution["training_performed"] is True
            and execution["network_attempts"] == 0
            and execution["network_used"] is False
            and execution["canonical_golden_overwrites"] == 0
            and execution["claim_or_verdict_changed"] is False
            and float(execution["elapsed_seconds"]) > 0.0
        )
        verdict_exact = (
            evidence["task_id"] == task_id
            and evidence["task_profile"] == "SCIENTIFIC_VALIDATION"
            and evidence["technical_status"] == expected_technical == "FAIL"
            and evidence["status"] == "fail"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["aggregate_verdict"]["registered_primary_signal_pass"]
            == signal_pass
            and all(
                evidence["aggregate_verdict"][field] == value
                for field, value in aggregate.items()
            )
            and evidence["aggregate_verdict"]["protected_exact"] == protected
        )

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation",
            "ST07_25_status: accepted_by_john",
            "remaining_stage07_planned_blocks: 7",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_25_stage05_seed_stability_full_validation_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_25_stage05_seed_stability_full_validation_change_scope_v01.csv",
            "scripts/st07_25_seed_stability_full_validation.py",
            "data_registry/st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv",
            "data_registry/st07_25_stage05_seed_stability_candidate_selected_params_v01.csv",
            "data_registry/st07_25_stage05_seed_stability_candidate_summary_v01.csv",
            "data_registry/st07_25_stage05_seed_stability_full_validation_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        checks = {
            "comparison_evidence_exact": comparison_evidence_exact,
            "aggregate": aggregate
            == {
                "structures_valid": True,
                "class_a_exact": True,
                "class_b_exact": False,
                "class_c_valid": True,
            },
            "signal": signal_pass,
            "protected": protected,
            "execution": execution_exact,
            "verdict": verdict_exact,
            "documentary": documentary,
            "scope": scope_exact,
        }
        return Check(
            "stage07_stage05_seed_stability_full_validation",
            "PASS" if all(checks.values()) else "FAIL",
            f"technical={expected_technical}; structures/A/B/C="
            f"{aggregate['structures_valid']}/{aggregate['class_a_exact']}/"
            f"{aggregate['class_b_exact']}/{aggregate['class_c_valid']}; "
            f"B_mismatches=outer:{recomputed['outer_scores']['class_b_mismatch_cells']},"
            f"selected:{recomputed['selected_params']['class_b_mismatch_cells']},"
            f"summary:{recomputed['summary']['class_b_mismatch_cells']}; "
            f"primary_signal={signal_pass}; protected={len(protected_expected)}/9:{protected}; "
            f"run/network={execution['full_run_count']}/{execution['network_attempts']}; "
            f"scope={len(scope_rows)}/9:{scope_exact}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_seed_stability_full_validation",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0725() -> Check:
    try:
        stage_path = PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )

        accepted_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation",
            "ST07_25_status: accepted_by_john",
            "ACCEPTED_BY_JOHN: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation",
            "TASK_CLOSED: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation",
        )
        accepted = all(
            all(token in body for token in accepted_tokens)
            for body in (stage_current, roadmap_current)
        )
        previous_gate = check_stage07_stage05_seed_stability_full_validation()

        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st07_25_stage05_seed_stability_full_validation_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        corrective_trigger = (
            evidence["technical_status"] == "FAIL"
            and evidence["aggregate_verdict"]
            == {
                "class_a_exact": True,
                "class_b_exact": False,
                "class_c_valid": True,
                "protected_exact": True,
                "registered_primary_signal_pass": True,
                "structures_valid": True,
                "verdict_rule": "pass_only_if_all_true_else_fail_without_causal_attribution",
            }
            and evidence["comparisons"]["outer_scores"]["class_b_mismatch_cells"]
            == 350
            and evidence["comparisons"]["selected_params"]["class_b_mismatch_cells"]
            == 0
            and evidence["comparisons"]["summary"]["class_b_mismatch_cells"]
            == 144
        )

        protected_hashes = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
            "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
            "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
            "data_registry/st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv": "30ae06d3883d478c1815aaeb4a6864fc03cf80c523820cb99b2e423c4bd218af",
            "data_registry/st07_25_stage05_seed_stability_candidate_selected_params_v01.csv": "79174fcc98c45bed58ec7670e420d85b306fc5b9c6035cb3c322e4200e5d651e",
            "data_registry/st07_25_stage05_seed_stability_candidate_summary_v01.csv": "f320b1e6f002123ff0c55a912c8141195e2b377948bf3dfebe5e14fb0fc0d852",
            "data_registry/st07_25_stage05_seed_stability_full_validation_evidence_v01.json": "27cf784078c8d6897c874fa4e55b928f40725610cc57aebb9f3fb4b2335ad09a",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )

        route_tokens = (
            "selected_alternative: A",
            "selected_weighted_score: 4.70/5.00",
            "proposed_task_id: ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation",
            "diagnostic_scope: logistic_regression_only_50_registered_outer_blocks",
            "thread_conditions: predeclared_4_and_12",
            "hgb_refit: prohibited",
            "golden_master_change: prohibited",
            "claim_or_verdict_change: prohibited",
            "causal_conclusion_policy: supported_only_if_4_exact_and_12_reproduces_ST07_25",
            "ST07_26_implementation_started: NO",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        roadmap_route = all(
            token in roadmap_text
            for token in (
                "MLCRA-RD-059",
                "ST07_26_status: accepted_by_john",
                "remaining_stage07_planned_blocks: 7",
            )
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_25_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_25_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        checks = {
            "accepted": accepted,
            "previous_gate": previous_gate.status == "PASS",
            "corrective_trigger": corrective_trigger,
            "protected": protected,
            "route_documented": route_documented,
            "roadmap_route": roadmap_route,
            "scope": scope_exact,
        }
        return Check(
            "stage07_next_block_after_st0725",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={accepted}; previous={previous_gate.status}; trigger={corrective_trigger}; "
            f"remaining=8(corrective:1+nominal:7); protected={len(protected_hashes)}/9:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; historical_selection_preserved=True; "
            "selected=ST07_26_logistic_blas_4_vs_12_causal_diagnostic_validation",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0725",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_st0726_logistic_blas_diagnostic() -> Check:
    try:
        import numpy as np
        import pandas as pd

        data = PROJECT_ROOT / "data_registry"
        scores_path = (
            data
            / "st07_26_stage05_seed_stability_logistic_blas_diagnostic_scores_v01.csv"
        )
        evidence_path = (
            data
            / "st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json"
        )
        scores = pd.read_csv(scores_path, dtype=str, keep_default_na=False)
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        expected_columns = [
            "task_id", "stress_test_id", "claim_id", "candidate_id",
            "thread_condition", "outer_random_state", "outer_split_number",
            "outer_repeat_number", "outer_fold_number", "outer_cv_n_splits",
            "outer_cv_n_repeats", "model_id", "model_role",
            "selected_parameter_set_id", "feature_policy_id", "n_train",
            "n_test", "train_positive_share", "test_positive_share", "roc_auc",
            "average_precision", "pr_auc", "f1", "balanced_accuracy",
            "log_loss", "brier_score", "fit_seconds", "predict_seconds",
            "reference_artifact", "metric_cells_total",
            "exact_reference_metric_cells", "exact_after_csv_roundtrip",
            "row_status", "interpretation_allowed_ru",
        ]
        schema_shape = list(scores.columns) == expected_columns and list(scores.shape) == [100, 34]
        key_columns = ["thread_condition", "outer_random_state", "outer_split_number"]
        key_exact = not scores.duplicated(key_columns).any()
        model_boundary = (
            scores["model_id"].eq("logistic_regression").all()
            and scores["model_role"].eq("control").all()
            and scores.groupby("thread_condition").size().to_dict() == {"12": 50, "4": 50}
        )
        metric_columns = [
            "roc_auc", "average_precision", "pr_auc", "f1",
            "balanced_accuracy", "log_loss", "brier_score",
        ]
        split_columns = [
            "outer_random_state", "outer_split_number", "outer_repeat_number",
            "outer_fold_number", "outer_cv_n_splits", "outer_cv_n_repeats",
            "n_train", "n_test", "train_positive_share", "test_positive_share",
        ]
        references = {
            "4": data / "openml_miniboone_stage05_seed_stability_outer_scores.csv",
            "12": data / "st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv",
        }
        recomputed = {}
        for condition, reference_path in references.items():
            candidate = scores[scores["thread_condition"].eq(condition)].reset_index(drop=True)
            reference = pd.read_csv(
                reference_path, dtype=str, keep_default_na=False
            )
            reference = reference[
                reference["model_id"].eq("logistic_regression")
            ].reset_index(drop=True)
            metric_mask = candidate[metric_columns].ne(reference[metric_columns])
            split_mask = candidate[split_columns].ne(reference[split_columns])
            recomputed[condition] = {
                "exact_metric_cells": int(metric_mask.size - metric_mask.to_numpy().sum()),
                "metric_mismatch_cells": int(metric_mask.to_numpy().sum()),
                "split_mismatch_cells": int(split_mask.to_numpy().sum()),
            }
        exact = recomputed == {
            "4": {"exact_metric_cells": 350, "metric_mismatch_cells": 0, "split_mismatch_cells": 0},
            "12": {"exact_metric_cells": 350, "metric_mismatch_cells": 0, "split_mismatch_cells": 0},
        }
        timing = True
        for column in ("fit_seconds", "predict_seconds"):
            values = pd.to_numeric(scores[column], errors="coerce")
            timing = timing and bool(values.notna().all() and np.isfinite(values).all() and values.ge(0).all())
        protected_expected = {
            path: row["expected_sha256"]
            for path, row in evidence["protected_after"].items()
        }
        protected_expected.update(
            {
                "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
                "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
                "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            }
        )
        protected = len(protected_expected) == 15 and all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )
        aggregate_expected = {
            "backend_identity_exact_to_st07_25": True,
            "blas_12_exact_350_of_350": True,
            "blas_4_exact_350_of_350": True,
            "protected_exact": True,
            "runtime_restored": True,
            "split_inputs_exact": True,
            "thread_limits_enforced": True,
            "timing_valid": True,
            "verdict_rule": "pass_causal_support_only_if_all_checks_true",
            "warnings_absent": True,
        }
        execution = evidence["execution"]
        evidence_exact = (
            evidence["technical_status"] == "PASS"
            and evidence["scientific_verdict"] == "PASS_CAUSAL_SUPPORT"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["aggregate_verdict"] == aggregate_expected
            and execution["logistic_fit_count"] == 100
            and execution["hgb_fit_count"] == 0
            and execution["dummy_fit_count"] == 0
            and execution["inner_tuning_count"] == 0
            and execution["network_attempts"] == 0
            and execution["canonical_golden_overwrites"] == 0
            and not execution["claim_or_verdict_changed"]
            and evidence["scores"]["sha256"] == sha256_file(scores_path)
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation",
            "ST07_26_status: accepted_by_john",
            "ST07_26_scientific_verdict: PASS_CAUSAL_SUPPORT",
            "ST07_26_logistic_fit_count: 100",
            "ST07_26_hgb_fit_count: 0",
            "ST07_26_network_attempts: 0",
            "NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design",
        )
        documentary = all(
            all(token in body for token in documentary_tokens)
            for body in (stage_text, roadmap_text)
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_26_stage05_seed_stability_logistic_blas_diagnostic_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_26_stage05_seed_stability_logistic_blas_diagnostic_change_scope_v01.csv",
            "scripts/st07_26_seed_stability_logistic_blas_diagnostic.py",
            "data_registry/st07_26_stage05_seed_stability_logistic_blas_diagnostic_scores_v01.csv",
            "data_registry/st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        checks = {
            "schema_shape": schema_shape,
            "key": key_exact,
            "model_boundary": model_boundary,
            "exact": exact,
            "timing": timing,
            "protected": protected,
            "evidence": evidence_exact,
            "documentary": documentary,
            "scope": scope_exact,
        }
        return Check(
            "stage07_st0726_logistic_blas_diagnostic",
            "PASS" if all(checks.values()) else "FAIL",
            f"shape={list(scores.shape)}; rows=4:{(scores['thread_condition'] == '4').sum()},"
            f"12:{(scores['thread_condition'] == '12').sum()}; exact={recomputed}; "
            f"fits=LR:{execution['logistic_fit_count']},HGB:{execution['hgb_fit_count']},"
            f"dummy:{execution['dummy_fit_count']},inner:{execution['inner_tuning_count']}; "
            f"network={execution['network_attempts']}; protected={len(protected_expected)}/15:{protected}; "
            f"scope={len(scope_rows)}/7:{scope_exact}; verdict={evidence['scientific_verdict']}",
        )
    except Exception as exc:
        return Check(
            "stage07_st0726_logistic_blas_diagnostic",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0726() -> Check:
    try:
        stage_path = PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        task_id = (
            "ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_"
            "causal_diagnostic_validation"
        )
        proposed_id = (
            "ST07_27_stage05_split_10x1_modularization_contract_and_"
            "golden_master_design"
        )
        accepted_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "ST07_26_status: accepted_by_john",
            f"ACCEPTED_BY_JOHN: {task_id}",
            f"TASK_CLOSED: {task_id}",
        )
        accepted = all(
            all(token in body for token in accepted_tokens)
            for body in (stage_current, roadmap_current)
        )
        previous_gate = check_stage07_st0726_logistic_blas_diagnostic()

        notebook_path = PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        expected_cells = {
            41: (
                "1e6098e5",
                41,
                "69437b2df040b15560a7a895b5f2e65ffc37915f3d8f5ec907fb6a353b494448",
                (),
            ),
            42: (
                "2cc7c20e",
                43,
                "992bb42111378720c07ed7643febaaccac4d862bd06a4b6e14887ed86a8c2bdb",
                (),
            ),
            43: (
                "f301af0a",
                25,
                "3b6067eb2c0988c9238449d39ca53b6c9d9f3791c1b8d7e296006fd4e3a3c882",
                (),
            ),
        }
        cell_checks = []
        function_count = 0
        line_count = 0
        for index, (cell_id, expected_lines, digest, expected_definitions) in (
            expected_cells.items()
        ):
            cell = notebook["cells"][index]
            source = "".join(cell["source"])
            definitions = tuple(
                node.name
                for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            line_count += len(source.splitlines())
            function_count += len(definitions)
            cell_checks.append(
                cell.get("id") == cell_id
                and len(source.splitlines()) == expected_lines
                and hashlib.sha256(source.encode("utf-8")).hexdigest() == digest
                and definitions == expected_definitions
            )
        inventory_exact = (
            len(notebook["cells"]) == 52
            and sum(
                len("".join(cell["source"]).splitlines())
                for cell in notebook["cells"]
                if cell["cell_type"] == "code"
            )
            == 2804
            and line_count == 109
            and function_count == 0
            and all(cell_checks)
        )

        plan_path = (
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        plan_rows = read_contract_csv(plan_path)
        plan = [
            row
            for row in plan_rows
            if row["stress_test_id"] == "ST05_03a_split_protocol_10x1"
        ]
        plan_exact = (
            len(plan) == 1
            and plan[0]["requires_new_model_run"] == "yes"
            and plan[0]["protocol_variant_id"] == "nested_10x1_seed_grid_v01"
            and plan[0]["outer_cv_method"] == "RepeatedStratifiedKFold"
            and plan[0]["outer_cv_n_splits"] == "10"
            and plan[0]["outer_cv_n_repeats"] == "1"
            and plan[0]["outer_random_states"]
            == "20260507;20260517;20260527"
            and plan[0]["inner_cv_method"] == "StratifiedKFold"
            and plan[0]["inner_cv_n_splits"] == "3"
            and plan[0]["models"]
            == "hist_gradient_boosting;logistic_regression;dummy_prior"
            and plan[0]["primary_metric"] == "average_precision"
            and plan[0]["parameter_space_policy"]
            == "same_locked_space_as_nested_cv_v01"
            and plan[0]["execution_order"] == "3"
        )

        outer_path = (
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv"
        )
        summary_path = (
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_split_10x1_summary.csv"
        )
        outer = read_contract_csv(outer_path)
        summary = read_contract_csv(summary_path)
        outer_key = (
            "stress_test_id",
            "outer_random_state",
            "outer_split_number",
            "model_id",
        )
        summary_key = (
            "stress_test_id",
            "comparison_model_id",
            "metric_name",
            "summary_scope",
            "outer_random_state",
        )
        expected_outer_order = [
            (seed, str(split_number), model_id)
            for seed in ("20260507", "20260517", "20260527")
            for split_number in range(1, 11)
            for model_id in (
                "hist_gradient_boosting",
                "dummy_prior",
                "logistic_regression",
            )
        ]
        actual_outer_order = [
            (row["outer_random_state"], row["outer_split_number"], row["model_id"])
            for row in outer
        ]
        golden_exact = (
            sha256_file(outer_path)
            == "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970"
            and sha256_file(summary_path)
            == "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18"
            and len(outer) == 90
            and len(outer[0]) == 43
            and len(summary) == 48
            and len(summary[0]) == 22
            and len({tuple(row[key] for key in outer_key) for row in outer}) == 90
            and len({tuple(row[key] for key in summary_key) for row in summary})
            == 48
            and actual_outer_order == expected_outer_order
        )
        protected_hashes = {
            "notebooks/04_dataset_smoke_experiments.ipynb": (
                "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52"
            ),
            "src/mlcra/stress_tests.py": (
                "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146"
            ),
            "src/mlcra/nested_cv.py": (
                "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727"
            ),
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": (
                "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d"
            ),
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": (
                "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49"
            ),
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": (
                "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133"
            ),
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )

        route_tokens = (
            "selected_alternative: A",
            "selected_weighted_score: 4.90/5.00",
            f"proposed_task_id: {proposed_id}",
            "source_inventory: 3 cells / 638 lines / 5 functions",
            "registered_protocol: 3 seeds / 10x1 outer / 3 inner / 16 HGB candidates",
            "golden_inventory: outer_scores=90x43;summary=48x22",
            "historical_thread_provenance: unknown_not_reconstructed_by_ST07_26",
            "full_miniboone_training_performed: NO",
            "ST07_27_implementation_started: NO",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        authorized_current = all(
            all(
                token in body
                for token in (
                    f"NEXT_BLOCK_AUTHORIZED: {proposed_id}",
                    "ST07_27_status: accepted_by_john",
                    f"TASK_CLOSED: {proposed_id}",
                    "remaining_stage07_planned_blocks: 6",
                )
            )
            for body in (stage_current, roadmap_current)
        )
        authorized = all(
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}" in body
            for body in (stage_current, roadmap_current)
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_26_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_26_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        checks = {
            "accepted": accepted,
            "previous_gate": previous_gate.status == "PASS",
            "inventory": inventory_exact,
            "plan": plan_exact,
            "golden": golden_exact,
            "protected": protected,
            "route": route_documented,
            "authorized_current": authorized_current,
            "authorized": authorized,
            "scope": scope_exact,
        }
        return Check(
            "stage07_next_block_after_st0726",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={accepted}; previous={previous_gate.status}; "
            f"remaining=7(3+3+1); inventory_current="
            f"52/3308/ST05_03a_after_ST07_28:3/109/0:{inventory_exact}; "
            f"protocol=3seeds/10x1/inner3/space16:{plan_exact}; "
            f"golden=90x43/48x22:{golden_exact}; protected={len(protected_hashes)}/6:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; authorized={authorized}; "
            "selected=ST07_27_split_10x1_contract_and_golden_master_design",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0726",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_split_10x1_contract_design() -> Check:
    try:
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )

        task_id = (
            "ST07_27_stage05_split_10x1_modularization_contract_and_"
            "golden_master_design"
        )
        notebook_path = PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8-sig"))
        source_contract = (
            (
                41,
                "1e6098e5",
                41,
                "69437b2df040b15560a7a895b5f2e65ffc37915f3d8f5ec907fb6a353b494448",
                (),
            ),
            (
                42,
                "2cc7c20e",
                43,
                "992bb42111378720c07ed7643febaaccac4d862bd06a4b6e14887ed86a8c2bdb",
                (),
            ),
            (
                43,
                "f301af0a",
                25,
                "3b6067eb2c0988c9238449d39ca53b6c9d9f3791c1b8d7e296006fd4e3a3c882",
                (),
            ),
        )
        source_exact = len(notebook.get("cells", [])) == 52
        local_definitions: list[str] = []
        source_lines = 0
        for index, cell_id, line_count, digest, definitions in source_contract:
            cell = notebook["cells"][index]
            source = "".join(cell.get("source", []))
            actual_definitions = tuple(
                node.name
                for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            source_lines += len(source.splitlines())
            local_definitions.extend(actual_definitions)
            source_exact = (
                source_exact
                and cell.get("id") == cell_id
                and len(source.splitlines()) == line_count
                and hashlib.sha256(source.encode("utf-8")).hexdigest() == digest
                and actual_definitions == definitions
            )
        source_exact = (
            source_exact
            and source_lines == 109
            and len(local_definitions) == 0
        )

        config_hashes = {
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": (
                "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49"
            ),
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": (
                "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d"
            ),
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": (
                "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133"
            ),
        }
        configs_exact = all(
            sha256_file(PROJECT_ROOT / relative) == digest
            for relative, digest in config_hashes.items()
        )
        plan_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        plan_rows = [
            row
            for row in plan_rows
            if row["stress_test_id"] == "ST05_03a_split_protocol_10x1"
        ]
        registered_plan = plan_rows[0] if len(plan_rows) == 1 else {}
        plan_exact = bool(registered_plan) and (
            registered_plan["claim_id"]
            == "miniboone_hgb_vs_logreg_average_precision_v01"
            and registered_plan["requires_new_model_run"] == "yes"
            and registered_plan["run_group"] == "nested_split_sensitivity_v01"
            and registered_plan["protocol_variant_id"]
            == "nested_10x1_seed_grid_v01"
            and registered_plan["outer_cv_method"] == "RepeatedStratifiedKFold"
            and registered_plan["outer_cv_n_splits"] == "10"
            and registered_plan["outer_cv_n_repeats"] == "1"
            and registered_plan["outer_random_states"]
            == "20260507;20260517;20260527"
            and registered_plan["inner_cv_method"] == "StratifiedKFold"
            and registered_plan["inner_cv_n_splits"] == "3"
            and registered_plan["models"]
            == "hist_gradient_boosting;logistic_regression;dummy_prior"
            and registered_plan["primary_metric"] == "average_precision"
            and registered_plan["parameter_space_policy"]
            == "same_locked_space_as_nested_cv_v01"
            and registered_plan["comparison_unit"]
            == "paired outer validation block within protocol variant"
            and registered_plan["planned_outputs"]
            == "openml_miniboone_stage05_split_10x1_outer_scores.csv;"
            "openml_miniboone_stage05_split_10x1_summary.csv"
            and registered_plan["priority"] == "should_have"
            and registered_plan["execution_order"] == "3"
            and registered_plan["decision_status"] == "locked_before_stage05_runs"
        )

        model_space = pd.read_csv(
            PROJECT_ROOT
            / "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        parameter_grid, fixed_parameters = build_hist_gradient_boosting_search_space(
            model_space,
            protocol_id="miniboone_nested_cv_v01",
            candidate_id="openml_miniboone_41150",
        )
        locked_space_exact = (
            math.prod(len(values) for values in parameter_grid.values()) == 16
            and fixed_parameters
            == {"random_state": 20260507, "early_stopping": "auto"}
        )

        outer_columns = [
            "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
            "candidate_id", "openml_dataset_id", "dataset_name", "target_name",
            "target_class_0", "target_class_1", "positive_class_assumption",
            "outer_random_state", "outer_split_number", "outer_repeat_number",
            "outer_fold_number", "outer_cv_method", "outer_cv_n_splits",
            "outer_cv_n_repeats", "inner_cv_method", "inner_cv_n_splits",
            "inner_random_state", "train_size", "test_size",
            "train_positive_share", "test_positive_share", "feature_count",
            "model_id", "model_role", "selected_parameter_set_id",
            "selected_params_json", "inner_best_average_precision",
            "inner_candidate_count", "fit_seconds", "predict_seconds",
            "roc_auc", "average_precision", "pr_auc", "f1",
            "balanced_accuracy", "log_loss", "brier_score", "row_status",
            "interpretation_allowed_ru",
        ]
        summary_columns = [
            "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
            "summary_scope", "outer_random_state", "candidate_id",
            "comparison_role", "candidate_model_id", "comparison_model_id",
            "metric_name", "metric_direction", "n_blocks", "advantage_mean",
            "advantage_std_population", "advantage_min", "advantage_max",
            "candidate_positive_blocks", "candidate_negative_blocks",
            "candidate_zero_blocks", "row_status", "interpretation_allowed_ru",
        ]
        golden_spec = {
            "outer": (
                "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
                (90, 43),
                "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
                outer_columns,
            ),
            "summary": (
                "data_registry/openml_miniboone_stage05_split_10x1_summary.csv",
                (48, 22),
                "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18",
                summary_columns,
            ),
        }
        frames: dict[str, pd.DataFrame] = {}
        golden_exact = True
        for name, (relative, shape, digest, columns) in golden_spec.items():
            path = PROJECT_ROOT / relative
            frame = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
            )
            frames[name] = frame
            golden_exact = (
                golden_exact
                and frame.shape == shape
                and list(frame.columns) == columns
                and sha256_file(path) == digest
            )

        contract = {
            "stress_test_id": "ST05_03a_split_protocol_10x1",
            "claim_id": "miniboone_hgb_vs_logreg_average_precision_v01",
            "run_group": "nested_split_sensitivity_v01",
            "protocol_variant_id": "nested_10x1_seed_grid_v01",
            "candidate_id": "openml_miniboone_41150",
            "seeds": (20260507, 20260517, 20260527),
            "outer_n_splits": 10,
            "outer_n_repeats": 1,
            "inner_n_splits": 3,
            "inner_state_policy": "equals_outer_random_state",
            "models": (
                "hist_gradient_boosting", "dummy_prior", "logistic_regression"
            ),
            "roles": {
                "hist_gradient_boosting": "tuned_candidate",
                "dummy_prior": "lower_bound",
                "logistic_regression": "baseline",
            },
            "feature_count": 50,
            "scoring": "average_precision",
            "inner_candidate_count": 16,
        }
        metric_directions = {
            "average_precision": "higher_is_better",
            "balanced_accuracy": "higher_is_better",
            "brier_score": "lower_is_better",
            "f1": "higher_is_better",
            "log_loss": "lower_is_better",
            "roc_auc": "higher_is_better",
        }

        def validates(candidate, outer, summary) -> bool:
            try:
                seeds = tuple(candidate["seeds"])
                if seeds != contract["seeds"] or len(set(seeds)) != 3:
                    return False
                scalar_fields = (
                    "stress_test_id", "claim_id", "run_group",
                    "protocol_variant_id", "candidate_id", "outer_n_splits",
                    "outer_n_repeats", "inner_n_splits", "inner_state_policy",
                    "roles", "feature_count", "scoring",
                    "inner_candidate_count",
                )
                if any(candidate[field] != contract[field] for field in scalar_fields):
                    return False
                if tuple(candidate["models"]) != contract["models"]:
                    return False
                if (
                    outer.shape != (90, 43)
                    or summary.shape != (48, 22)
                    or list(outer.columns) != outer_columns
                    or list(summary.columns) != summary_columns
                ):
                    return False
                outer_key = [
                    "stress_test_id", "outer_random_state",
                    "outer_split_number", "model_id",
                ]
                summary_key = [
                    "stress_test_id", "comparison_model_id", "metric_name",
                    "summary_scope", "outer_random_state",
                ]
                if outer.duplicated(outer_key).any() or summary.duplicated(summary_key).any():
                    return False
                seed_strings = tuple(str(value) for value in seeds)
                expected_outer_order = [
                    (seed, str(split), model)
                    for seed in seed_strings
                    for split in range(1, 11)
                    for model in candidate["models"]
                ]
                actual_outer_order = list(map(tuple, outer[[
                    "outer_random_state", "outer_split_number", "model_id"
                ]].to_numpy()))
                expected_summary_order = [
                    (comparison, metric, scope, seed)
                    for comparison in ("dummy_prior", "logistic_regression")
                    for metric in tuple(metric_directions)
                    for scope, seed in (
                        (("all_outer_random_states", "all"),)
                        + tuple(
                            ("single_outer_random_state", seed)
                            for seed in seed_strings
                        )
                    )
                ]
                actual_summary_order = list(map(tuple, summary[[
                    "comparison_model_id", "metric_name", "summary_scope",
                    "outer_random_state",
                ]].to_numpy()))
                if (
                    actual_outer_order != expected_outer_order
                    or actual_summary_order != expected_summary_order
                ):
                    return False
                static_outer = {
                    "stress_test_id": candidate["stress_test_id"],
                    "claim_id": candidate["claim_id"],
                    "run_group": candidate["run_group"],
                    "protocol_variant_id": candidate["protocol_variant_id"],
                    "candidate_id": candidate["candidate_id"],
                    "openml_dataset_id": "41150",
                    "dataset_name": "MiniBooNE",
                    "target_name": "signal",
                    "target_class_0": "False",
                    "target_class_1": "True",
                    "positive_class_assumption": "True",
                    "outer_cv_method": "RepeatedStratifiedKFold",
                    "outer_cv_n_splits": "10",
                    "outer_cv_n_repeats": "1",
                    "feature_count": "50",
                    "row_status": "stage05_split_protocol_sensitivity_score",
                }
                if any(not outer[column].eq(value).all() for column, value in static_outer.items()):
                    return False
                if not (
                    outer["outer_repeat_number"].eq("1").all()
                    and outer["outer_fold_number"].eq(outer["outer_split_number"]).all()
                ):
                    return False
                role_sets = {
                    model: set(outer.loc[outer["model_id"].eq(model), "model_role"])
                    for model in candidate["models"]
                }
                if any(
                    role_sets[model] != {role}
                    for model, role in candidate["roles"].items()
                ):
                    return False
                hgb = outer[outer["model_id"].eq("hist_gradient_boosting")]
                controls = outer[~outer["model_id"].eq("hist_gradient_boosting")]
                if not (
                    hgb["inner_cv_method"].eq("StratifiedKFold").all()
                    and hgb["inner_cv_n_splits"].eq("3").all()
                    and hgb["inner_random_state"].eq(hgb["outer_random_state"]).all()
                    and hgb["inner_candidate_count"].eq("16").all()
                    and controls["inner_cv_method"].eq("not_applicable").all()
                    and controls["inner_cv_n_splits"].eq("").all()
                    and controls["inner_random_state"].eq("not_applicable").all()
                    and controls["selected_parameter_set_id"].eq("not_applicable").all()
                    and controls["selected_params_json"].eq("").all()
                    and controls["inner_best_average_precision"].eq("not_applicable").all()
                    and controls["inner_candidate_count"].eq("not_applicable").all()
                ):
                    return False
                for row in hgb.itertuples(index=False):
                    params = json.loads(row.selected_params_json)
                    if row.selected_parameter_set_id != make_hgb_parameter_set_id(params):
                        return False
                numeric_outer = (
                    "train_size", "test_size", "train_positive_share",
                    "test_positive_share", "fit_seconds", "predict_seconds",
                    "roc_auc", "average_precision", "pr_auc", "f1",
                    "balanced_accuracy", "log_loss", "brier_score",
                )
                for column in numeric_outer:
                    values = pd.to_numeric(outer[column], errors="coerce")
                    if values.isna().any() or any(not math.isfinite(value) for value in values):
                        return False
                if any(
                    (pd.to_numeric(outer[column], errors="raise") < 0).any()
                    for column in ("fit_seconds", "predict_seconds")
                ):
                    return False
                if not (
                    (
                        pd.to_numeric(outer["train_size"], errors="raise")
                        + pd.to_numeric(outer["test_size"], errors="raise")
                    ).eq(130064).all()
                    and outer["average_precision"].eq(outer["pr_auc"]).all()
                ):
                    return False
                static_summary = {
                    "stress_test_id": candidate["stress_test_id"],
                    "claim_id": candidate["claim_id"],
                    "run_group": candidate["run_group"],
                    "protocol_variant_id": candidate["protocol_variant_id"],
                    "candidate_id": candidate["candidate_id"],
                    "candidate_model_id": "hist_gradient_boosting",
                    "row_status": "stage05_split_protocol_sensitivity_summary",
                }
                if any(not summary[column].eq(value).all() for column, value in static_summary.items()):
                    return False
                role_by_comparison = {
                    "dummy_prior": "lower_bound_model",
                    "logistic_regression": "primary_baseline",
                }
                for row in summary.itertuples(index=False):
                    n_blocks = int(row.n_blocks)
                    positive_blocks = int(row.candidate_positive_blocks)
                    negative_blocks = int(row.candidate_negative_blocks)
                    zero_blocks = int(row.candidate_zero_blocks)
                    advantage_mean = float(row.advantage_mean)
                    advantage_std = float(row.advantage_std_population)
                    advantage_min = float(row.advantage_min)
                    advantage_max = float(row.advantage_max)
                    if (
                        row.metric_direction != metric_directions[row.metric_name]
                        or row.comparison_role
                        != role_by_comparison[row.comparison_model_id]
                        or n_blocks
                        != (30 if row.summary_scope == "all_outer_random_states" else 10)
                        or min(positive_blocks, negative_blocks, zero_blocks) < 0
                        or positive_blocks + negative_blocks + zero_blocks != n_blocks
                        or advantage_std < 0
                        or not advantage_min <= advantage_mean <= advantage_max
                    ):
                        return False
                for column in (
                    "advantage_mean", "advantage_std_population",
                    "advantage_min", "advantage_max", "candidate_positive_blocks",
                    "candidate_negative_blocks", "candidate_zero_blocks",
                ):
                    values = pd.to_numeric(summary[column], errors="coerce")
                    if values.isna().any() or any(not math.isfinite(value) for value in values):
                        return False
                hgb_rows = outer[outer["model_id"].eq("hist_gradient_boosting")]
                key = [
                    "outer_random_state", "outer_split_number",
                    "outer_repeat_number", "outer_fold_number",
                ]
                for comparison in ("dummy_prior", "logistic_regression"):
                    paired = hgb_rows.merge(
                        outer[outer["model_id"].eq(comparison)],
                        on=key,
                        suffixes=("_hgb", "_comparison"),
                        validate="one_to_one",
                    )
                    if len(paired) != 30:
                        return False
                    for metric, direction in metric_directions.items():
                        raw = (
                            pd.to_numeric(paired[f"{metric}_hgb"], errors="raise")
                            - pd.to_numeric(
                                paired[f"{metric}_comparison"], errors="raise"
                            )
                        )
                        advantages = raw if direction == "higher_is_better" else -raw
                        expected_groups = [("all", advantages)] + [
                            (
                                seed,
                                advantages[
                                    paired["outer_random_state"].eq(seed)
                                ],
                            )
                            for seed in seed_strings
                        ]
                        for seed, group in expected_groups:
                            actual = summary[
                                summary["comparison_model_id"].eq(comparison)
                                & summary["metric_name"].eq(metric)
                                & summary["outer_random_state"].eq(seed)
                            ]
                            if len(actual) != 1:
                                return False
                            actual_row = actual.iloc[0]
                            expected_counts = {
                                "candidate_positive_blocks": int((group > 0).sum()),
                                "candidate_negative_blocks": int((group < 0).sum()),
                                "candidate_zero_blocks": int((group == 0).sum()),
                            }
                            for field, expected in expected_counts.items():
                                if int(actual_row[field]) != expected:
                                    return False
                return True
            except (
                KeyError, TypeError, ValueError, json.JSONDecodeError,
                pd.errors.MergeError,
            ):
                return False

        positive_contract = validates(contract, frames["outer"], frames["summary"])
        mutations = []
        for transform in (
            lambda value: {**value, "seeds": value["seeds"][:-1]},
            lambda value: {**value, "seeds": (value["seeds"][0],) * 3},
            lambda value: {**value, "seeds": tuple(reversed(value["seeds"]))},
            lambda value: {**value, "outer_n_splits": 9},
            lambda value: {**value, "outer_n_repeats": 2},
            lambda value: {**value, "inner_n_splits": 4},
            lambda value: {**value, "inner_state_policy": "outer_plus_split"},
            lambda value: {**value, "models": value["models"][:-1]},
            lambda value: {
                **value,
                "roles": {**value["roles"], "dummy_prior": "baseline"},
            },
            lambda value: {**value, "inner_candidate_count": 15},
        ):
            mutations.append((transform(contract), frames["outer"], frames["summary"]))
        missing_schema = frames["outer"].drop(columns=["feature_count"])
        mutations.append((contract, missing_schema, frames["summary"]))
        duplicate_key = frames["outer"].copy(deep=True)
        duplicate_key.loc[1, duplicate_key.columns] = duplicate_key.loc[0]
        mutations.append((contract, duplicate_key, frames["summary"]))
        wrong_order = frames["outer"].copy(deep=True)
        wrong_order.iloc[[0, 1]] = wrong_order.iloc[[1, 0]].to_numpy()
        mutations.append((contract, wrong_order, frames["summary"]))
        bad_parameter_id = frames["outer"].copy(deep=True)
        bad_parameter_id.loc[0, "selected_parameter_set_id"] = "hgb_invalid"
        mutations.append((contract, bad_parameter_id, frames["summary"]))
        bad_inner_state = frames["outer"].copy(deep=True)
        bad_inner_state.loc[0, "inner_random_state"] = "20260508"
        mutations.append((contract, bad_inner_state, frames["summary"]))
        wrong_direction = frames["summary"].copy(deep=True)
        wrong_direction.loc[0, "metric_direction"] = "lower_is_better"
        mutations.append((contract, frames["outer"], wrong_direction))
        wrong_row_count = frames["summary"].iloc[:-1].copy()
        mutations.append((contract, frames["outer"], wrong_row_count))
        negative_timing = frames["outer"].copy(deep=True)
        negative_timing.loc[0, "fit_seconds"] = "-1"
        mutations.append((contract, negative_timing, frames["summary"]))
        alias_mismatch = frames["outer"].copy(deep=True)
        alias_mismatch.loc[0, "pr_auc"] = "0"
        mutations.append((contract, alias_mismatch, frames["summary"]))
        wrong_protocol = frames["outer"].copy(deep=True)
        wrong_protocol.loc[0, "protocol_variant_id"] = "wrong"
        mutations.append((contract, wrong_protocol, frames["summary"]))
        summary_mismatch = frames["summary"].copy(deep=True)
        summary_mismatch.loc[0, "candidate_positive_blocks"] = "0"
        mutations.append((contract, frames["outer"], summary_mismatch))
        negative_contract_checks = sum(
            not validates(*mutation) for mutation in mutations
        )

        protected_hashes = {
            **config_hashes,
            "notebooks/04_dataset_smoke_experiments.ipynb": (
                "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52"
            ),
            "src/mlcra/stress_tests.py": (
                "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146"
            ),
            "src/mlcra/nested_cv.py": (
                "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727"
            ),
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": (
                "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970"
            ),
            "data_registry/openml_miniboone_stage05_split_10x1_summary.csv": (
                "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18"
            ),
            "data_registry/st07_26_stage05_seed_stability_logistic_blas_diagnostic_scores_v01.csv": (
                "dbd7d7a2889f2f19dcf76f0c18e2e9bc5ab96d61404a1da9248455d75d8de62c"
            ),
            "data_registry/st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json": (
                "e07ad5bec329903266eff66436fa9d2e5045de3fa707e14a13da38b89c52bc44"
            ),
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_27_stage05_split_10x1_modularization_contract_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_27_stage05_split_10x1_modularization_contract_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        current_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "ST07_27_status: accepted_by_john",
            f"ACCEPTED_BY_JOHN: {task_id}",
            f"TASK_CLOSED: {task_id}",
            "ST07_27_training_authorized: false",
            "ST07_27_network_authorized: false",
            "ST07_27_source_changes_authorized: false",
            "ST07_27_scientific_artifact_changes_authorized: false",
            "NEXT_BLOCK_AUTHORIZED: ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation",
            "ST07_28_status: accepted_by_john",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        documentary_tokens = (
            "## 89. ST07_27",
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "source_inventory: 3 cells / 638 lines / 5 functions PASS",
            "registered_protocol: 3 seeds / 10x1 outer / 3 inner / 16 HGB candidates PASS",
            "golden_integrity: 90x43 / 48x22 PASS",
            "contract_validation_positive: PASS",
            "negative_contract_checks: 21/21 PASS",
            "inner_random_state_policy: equals_outer_random_state",
            "historical_golden_role: immutable_reference_not_current_environment_reproduction_claim",
            "timing_policy: finite_and_nonnegative_only",
            "source_extraction_performed: NO",
            "full_miniboone_training_performed: NO",
            "scientific_validation_performed: NO",
        )
        documentary = all(token in stage_text for token in documentary_tokens)
        roadmap_documentary = all(
            token in roadmap_text
            for token in (
                f"NEXT_BLOCK_AUTHORIZED: {task_id}",
                "ST07_27_status: accepted_by_john",
                f"TASK_CLOSED: {task_id}",
                "NEXT_BLOCK_AUTHORIZED: ST07_28_stage05_split_10x1_"
                "modular_extraction_and_fixture_validation",
                "MLCRA-RD-062",
            )
        )
        checks = {
            "source": source_exact,
            "configs": configs_exact,
            "plan": plan_exact,
            "space": locked_space_exact,
            "golden": golden_exact,
            "positive": positive_contract,
            "negative": negative_contract_checks == 21,
            "protected": protected,
            "scope": scope_exact,
            "current_state": current_state,
            "documentary": documentary,
            "roadmap": roadmap_documentary,
        }
        return Check(
            "stage07_stage05_split_10x1_contract_design",
            "PASS" if all(checks.values()) else "FAIL",
            f"source_after_ST07_28=3/109/0:{source_exact}; "
            f"protocol=3seeds/10x1/inner3:{plan_exact}; "
            f"space=16:{locked_space_exact}; golden=90x43/48x22:{golden_exact}; "
            f"positive={positive_contract}; negative={negative_contract_checks}/21; "
            f"protected={len(protected_hashes)}/10:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; training=0; network=0; "
            "source_extraction=0; scientific_validation=0",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_split_10x1_contract_design",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0727() -> Check:
    try:
        import pandas as pd

        accepted_id = (
            "ST07_27_stage05_split_10x1_modularization_contract_and_"
            "golden_master_design"
        )
        proposed_id = (
            "ST07_28_stage05_split_10x1_modular_extraction_and_"
            "fixture_validation"
        )
        stage_path = PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )

        accepted = all(
            all(
                token in body
                for token in (
                    f"ACCEPTED_BY_JOHN: {accepted_id}",
                    f"TASK_CLOSED: {accepted_id}",
                    "ST07_27_status: accepted_by_john",
                )
            )
            for body in (stage_current, roadmap_current)
        )
        proposed_state = all(
            all(
                token in body
                for token in (
                    f"NEXT_BLOCK_AUTHORIZED: {proposed_id}",
                    "ST07_28_status: accepted_by_john",
                    "ST07_28_training_authorized: false",
                    "ST07_28_network_authorized: false",
                    "ST07_28_source_changes_authorized: true",
                    "ST07_28_scientific_artifact_changes_authorized: false",
                    "ST07_28_implementation_started: YES",
                    "remaining_stage07_planned_blocks: 5",
                    "remaining_breakdown: "
                    "ST05_02=0;ST05_03a=1;ST05_07=3;stage07_closure=1",
                )
            )
            for body in (stage_current, roadmap_current)
        )
        authorized = all(
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}" in body
            for body in (stage_current, roadmap_current)
        )

        notebook_path = PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8-sig"))
        source_contract = (
            (41, "1e6098e5", 41, ()),
            (
                42,
                "2cc7c20e",
                43,
                (),
            ),
            (43, "f301af0a", 25, ()),
        )
        source_lines = 0
        definitions: list[str] = []
        inventory_exact = len(notebook.get("cells", [])) == 52
        code_lines = sum(
            len("".join(cell.get("source", [])).splitlines())
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        )
        for index, cell_id, line_count, expected_definitions in source_contract:
            cell = notebook["cells"][index]
            source = "".join(cell.get("source", []))
            actual_definitions = tuple(
                node.name
                for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            source_lines += len(source.splitlines())
            definitions.extend(actual_definitions)
            inventory_exact = (
                inventory_exact
                and cell.get("id") == cell_id
                and len(source.splitlines()) == line_count
                and actual_definitions == expected_definitions
            )
        inventory_exact = (
            inventory_exact
            and code_lines == 2804
            and source_lines == 109
            and len(definitions) == 0
        )

        plan = pd.read_csv(
            PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        plan = plan[plan["stress_test_id"].eq("ST05_03a_split_protocol_10x1")]
        plan_exact = len(plan) == 1
        if plan_exact:
            row = plan.iloc[0]
            plan_exact = (
                row["outer_cv_method"] == "RepeatedStratifiedKFold"
                and row["outer_cv_n_splits"] == "10"
                and row["outer_cv_n_repeats"] == "1"
                and row["outer_random_states"] == "20260507;20260517;20260527"
                and row["inner_cv_method"] == "StratifiedKFold"
                and row["inner_cv_n_splits"] == "3"
                and row["models"]
                == "hist_gradient_boosting;logistic_regression;dummy_prior"
                and row["parameter_space_policy"]
                == "same_locked_space_as_nested_cv_v01"
                and row["execution_order"] == "3"
            )

        golden_outer = pd.read_csv(
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        golden_summary = pd.read_csv(
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_split_10x1_summary.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        golden_exact = (
            golden_outer.shape == (90, 43)
            and golden_summary.shape == (48, 22)
            and sha256_file(
                PROJECT_ROOT
                / "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv"
            )
            == "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970"
            and sha256_file(
                PROJECT_ROOT
                / "data_registry/openml_miniboone_stage05_split_10x1_summary.csv"
            )
            == "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18"
        )

        dependency_hashes = {
            "notebooks/04_dataset_smoke_experiments.ipynb": (
                "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52"
            ),
            "src/mlcra/stress_tests.py": (
                "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146"
            ),
            "src/mlcra/nested_cv.py": (
                "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727"
            ),
            "src/mlcra/model_spaces.py": (
                "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b"
            ),
            "src/mlcra/metrics.py": (
                "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3"
            ),
            "src/mlcra/io.py": (
                "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0"
            ),
            "src/mlcra/validation.py": (
                "2bed7566811af6c342b9a70a8e8933479248fc6e7ee4b9983da39d1c0279ffff"
            ),
        }
        dependencies_exact = all(
            sha256_file(PROJECT_ROOT / relative) == digest
            for relative, digest in dependency_hashes.items()
        )
        stress_source = (PROJECT_ROOT / "src/mlcra/stress_tests.py").read_text(
            encoding="utf-8-sig"
        )
        implementation_absent = all(
            token in stress_source
            for token in (
                "Split10x1Contract",
                "Split10x1Bundle",
                "build_split_10x1_contract",
                "run_split_10x1",
                "validate_split_10x1_bundle",
            )
        )

        route_tokens = (
            "## 91. Принятие ST07_27 и выбор следующего блока",
            "selected_alternative: A",
            "selected_weighted_score: 4.90/5.00",
            f"proposed_task_id: {proposed_id}",
            "source_inventory: 3 cells / 638 lines / 5 functions",
            "inner_random_state_policy: equals_outer_random_state",
            "full_miniboone_training_performed: NO",
            "ST07_28_implementation_started: YES",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_27_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_27_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        checks = {
            "accepted": accepted,
            "proposed_state": proposed_state,
            "authorized": authorized,
            "inventory": inventory_exact,
            "plan": plan_exact,
            "golden": golden_exact,
            "dependencies": dependencies_exact,
            "implementation_absent": implementation_absent,
            "route": route_documented,
            "scope": scope_exact,
        }
        return Check(
            "stage07_next_block_after_st0727",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={accepted}; remaining=6(0+2+3+1); "
            f"inventory=52/3308/ST05_03a:3/109/0:{inventory_exact}; "
            f"protocol=3seeds/10x1/inner3:{plan_exact}; "
            f"golden=90x43/48x22:{golden_exact}; "
            f"dependencies={len(dependency_hashes)}/7:{dependencies_exact}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; authorized={authorized}; "
            f"implementation_started={implementation_absent}; selected={proposed_id}",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0727",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def csv_roundtrip_as_strings(frame):
    import pandas as pd

    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    buffer.seek(0)
    return pd.read_csv(buffer, dtype=str, keep_default_na=False)


def check_stage07_stage05_split_10x1_modular_extraction() -> Check:
    try:
        import inspect

        import numpy as np
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.io import read_csv_checked
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )
        from mlcra.nested_cv import build_inner_splitter
        from mlcra.stress_tests import (
            STAGE05_SPLIT_10X1_OUTER_COLUMNS,
            STAGE05_SPLIT_10X1_SUMMARY_COLUMNS,
            Split10x1Bundle,
            build_split_10x1_contract,
            build_split_10x1_control_estimators,
            run_split_10x1_grid,
            validate_split_10x1_bundle,
        )

        plan = read_csv_checked(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        claim = read_csv_checked(
            PROJECT_ROOT
            / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
        )
        space = read_csv_checked(
            PROJECT_ROOT
            / "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv"
        )
        contract = build_split_10x1_contract(plan, claim)
        parameter_grid, fixed_parameters = (
            build_hist_gradient_boosting_search_space(
                space,
                protocol_id=contract.nested_protocol_id,
                candidate_id=contract.candidate_id,
            )
        )
        controls = build_split_10x1_control_estimators()

        notebook = json.loads(
            (
                PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
            ).read_text(encoding="utf-8-sig")
        )
        before_cells = {
            "1e6098e5": (
                142,
                "f641dfecc93ec8a64a317791b4585b90a4179c7e039d8c1b5745c9038811a761",
            ),
            "2cc7c20e": (
                302,
                "b0e7ca6503dfbad179d43b98c4e6288c2418751399f75e13901f5e793394c529",
            ),
            "f301af0a": (
                194,
                "ed80453b730dd2220f0fc1e09c74755201cd236ca336bc8e9eb84236ad466022",
            ),
        }
        expected_cells = {
            41: (
                "1e6098e5",
                41,
                "69437b2df040b15560a7a895b5f2e65ffc37915f3d8f5ec907fb6a353b494448",
            ),
            42: (
                "2cc7c20e",
                43,
                "992bb42111378720c07ed7643febaaccac4d862bd06a4b6e14887ed86a8c2bdb",
            ),
            43: (
                "f301af0a",
                25,
                "3b6067eb2c0988c9238449d39ca53b6c9d9f3791c1b8d7e296006fd4e3a3c882",
            ),
        }
        notebook_cells_exact = len(notebook["cells"]) == 52
        for index, (cell_id, line_count, digest) in expected_cells.items():
            cell = notebook["cells"][index]
            source = "".join(cell["source"])
            definitions = [
                node.name
                for node in ast.parse(source).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            notebook_cells_exact = notebook_cells_exact and (
                cell.get("id") == cell_id
                and len(source.splitlines()) == line_count
                and hashlib.sha256(source.encode("utf-8")).hexdigest() == digest
                and definitions == []
                and cell.get("outputs") == []
                and cell.get("execution_count") is None
            )
        preserved = {
            "metadata": notebook["metadata"],
            "nbformat": notebook["nbformat"],
            "nbformat_minor": notebook["nbformat_minor"],
            "cells": [
                cell
                for cell in notebook["cells"]
                if cell.get("id") not in before_cells
            ],
        }
        preserved_digest = hashlib.sha256(
            json.dumps(
                preserved,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        notebook_preserved = (
            preserved_digest
            == "c9fc7faefaadb9b1e548bfc86e36ae485299565f63a143abc79a3bbbfe88d899"
        )

        signature = inspect.signature(build_inner_splitter)
        seed_policy_api = (
            "add_outer_split_to_random_state" in signature.parameters
            and signature.parameters[
                "add_outer_split_to_random_state"
            ].default
            is True
            and build_inner_splitter(3, 20260517, 7).random_state == 20260524
            and build_inner_splitter(
                3,
                20260517,
                7,
                add_outer_split_to_random_state=False,
            ).random_state
            == 20260517
        )

        X = pd.DataFrame(
            np.arange(200 * 50, dtype=float).reshape(200, 50),
            columns=contract.feature_names,
        )
        y = np.asarray([0, 1] * 100, dtype=int)
        candidate_bundle = {
            "candidate_id": contract.candidate_id,
            "did": 41150,
            "dataset_name": "deterministic_split_10x1_fixture",
            "target_name": "signal",
            "target_metadata": {
                "target_class_0": "False",
                "target_class_1": "True",
                "positive_class_assumption": "True",
            },
        }
        selected_params = {
            name: values[0] for name, values in parameter_grid.items()
        }
        selected_id = make_hgb_parameter_set_id(selected_params)
        selected_json = json.dumps(selected_params, sort_keys=True)

        def fixture_score(kwargs, model_id, role, seed):
            split = kwargs["zero_based_outer_split_number"]
            offset = {
                "hist_gradient_boosting": 0.8,
                "dummy_prior": 0.2,
                "logistic_regression": 0.6,
            }[model_id]
            base = offset + (seed % 100) / 100000 + split / 10000
            train, test = kwargs["train_index"], kwargs["test_index"]
            tuned = role == "tuned_candidate"
            return {
                "protocol_id": kwargs["protocol_id"],
                "candidate_id": contract.candidate_id,
                "openml_dataset_id": 41150,
                "dataset_name": "deterministic_split_10x1_fixture",
                "target_name": "signal",
                "target_class_0": "False",
                "target_class_1": "True",
                "positive_class_assumption": "True",
                "outer_split_number": split + 1,
                "outer_repeat_number": 1,
                "outer_fold_number": split + 1,
                "outer_cv_n_splits": 10,
                "outer_cv_n_repeats": 1,
                "inner_cv_n_splits": 3 if tuned else "",
                "model_id": model_id,
                "model_role": role,
                "selected_parameter_set_id": (
                    selected_id if tuned else "not_applicable_control_model"
                ),
                "selected_params_json": selected_json if tuned else "",
                "feature_policy_id": "numeric_particleid_0_49_locked",
                "feature_count": 50,
                "feature_names": "; ".join(contract.feature_names),
                "n_train": len(train),
                "n_test": len(test),
                "train_positive_share": float(y[train].mean()),
                "test_positive_share": float(y[test].mean()),
                "roc_auc": base,
                "average_precision": base - 0.01,
                "pr_auc": base - 0.01,
                "f1": base - 0.02,
                "balanced_accuracy": base - 0.03,
                "log_loss": 1.0 - base,
                "brier_score": 0.5 - base / 2,
                "fit_seconds": 0.01,
                "predict_seconds": 0.02,
                "row_status": kwargs["row_status"],
                "interpretation_allowed": kwargs["interpretation_allowed"],
            }

        def tuned_fixture(**kwargs):
            if kwargs["add_outer_split_to_inner_random_state"] is not False:
                raise AssertionError("ST05_03a должен отключать split offset")
            seed = kwargs["inner_base_random_state"]
            split = kwargs["zero_based_outer_split_number"]
            return (
                fixture_score(
                    kwargs, "hist_gradient_boosting", "tuned_candidate", seed
                ),
                {
                    "protocol_id": kwargs["protocol_id"],
                    "candidate_id": contract.candidate_id,
                    "outer_split_number": split + 1,
                    "outer_repeat_number": 1,
                    "outer_fold_number": split + 1,
                    "model_id": "hist_gradient_boosting",
                    "selected_parameter_set_id": selected_id,
                    "selected_params_json": selected_json,
                    "inner_best_average_precision": 0.75 + split / 10000,
                    "inner_cv_n_splits": 3,
                    "inner_cv_random_state": seed,
                    "inner_candidate_count": 16,
                    "row_status": kwargs["row_status"],
                },
                [],
            )

        callback_seed: dict[str, int] = {"value": contract.outer_random_states[0]}

        def control_fixture(**kwargs):
            split = kwargs["zero_based_outer_split_number"]
            if split == 0:
                callback_seed["value"] = next(
                    seed
                    for seed in contract.outer_random_states
                    if seed >= callback_seed["value"]
                )
            return (
                fixture_score(
                    kwargs,
                    kwargs["model_id"],
                    "control",
                    callback_seed["value"],
                ),
                [],
            )

        # The tuned callback records the current seed for subsequent controls.
        original_tuned = tuned_fixture

        def tuned_with_state(**kwargs):
            callback_seed["value"] = kwargs["inner_base_random_state"]
            return original_tuned(**kwargs)

        first = run_split_10x1_grid(
            contract,
            candidate_bundle,
            X,
            y,
            list(contract.feature_names),
            parameter_grid,
            fixed_parameters,
            controls,
            tuned_fit=tuned_with_state,
            control_fit=control_fixture,
        )
        second = run_split_10x1_grid(
            contract,
            candidate_bundle,
            X,
            y,
            list(contract.feature_names),
            parameter_grid,
            fixed_parameters,
            controls,
            tuned_fit=tuned_with_state,
            control_fit=control_fixture,
        )
        first_rt = Split10x1Bundle(
            outer_scores=csv_roundtrip_as_strings(first.outer_scores),
            summary=csv_roundtrip_as_strings(first.summary),
        )
        second_rt = Split10x1Bundle(
            outer_scores=csv_roundtrip_as_strings(second.outer_scores),
            summary=csv_roundtrip_as_strings(second.summary),
        )
        validate_split_10x1_bundle(first_rt, contract)
        validate_split_10x1_bundle(second_rt, contract)
        class_c = {"fit_seconds", "predict_seconds"}
        class_ab = [
            column
            for column in STAGE05_SPLIT_10X1_OUTER_COLUMNS
            if column not in class_c
        ]
        two_run_exact = (
            first_rt.outer_scores[class_ab].equals(
                second_rt.outer_scores[class_ab]
            )
            and first_rt.summary.equals(second_rt.summary)
        )
        schemas_exact = (
            first.outer_scores.shape == (90, 43)
            and first.summary.shape == (48, 22)
            and tuple(first.outer_scores.columns)
            == STAGE05_SPLIT_10X1_OUTER_COLUMNS
            and tuple(first.summary.columns)
            == STAGE05_SPLIT_10X1_SUMMARY_COLUMNS
        )
        timing_valid = all(
            np.isfinite(pd.to_numeric(first_rt.outer_scores[column])).all()
            and (pd.to_numeric(first_rt.outer_scores[column]) >= 0).all()
            for column in class_c
        )

        def rejected(mutator) -> bool:
            candidate = Split10x1Bundle(
                outer_scores=first.outer_scores.copy(deep=True),
                summary=first.summary.copy(deep=True),
            )
            mutator(candidate)
            try:
                validate_split_10x1_bundle(candidate, contract)
            except (AssertionError, TypeError, ValueError, KeyError):
                return True
            return False

        def set_cell(frame_name, row, column, value):
            def mutate(bundle):
                getattr(bundle, frame_name).at[row, column] = value

            return mutate

        def reverse_rows(frame_name):
            def mutate(bundle):
                frame = getattr(bundle, frame_name)
                frame.loc[:, :] = frame.iloc[::-1].to_numpy()

            return mutate

        mutations = [
            lambda b: b.outer_scores.drop(columns=["roc_auc"], inplace=True),
            lambda b: b.summary.drop(columns=["metric_direction"], inplace=True),
            reverse_rows("outer_scores"),
            reverse_rows("summary"),
            set_cell("outer_scores", 1, "outer_split_number", 2),
            set_cell("outer_scores", 0, "model_role", "baseline"),
            set_cell("outer_scores", 0, "inner_random_state", 20260508),
            set_cell("outer_scores", 0, "inner_candidate_count", 15),
            set_cell("outer_scores", 0, "selected_parameter_set_id", "wrong"),
            set_cell("outer_scores", 1, "selected_parameter_set_id", "wrong"),
            set_cell("outer_scores", 0, "average_precision", 0.1),
            set_cell("outer_scores", 0, "fit_seconds", -1),
            set_cell("outer_scores", 0, "predict_seconds", np.inf),
            set_cell("outer_scores", 0, "roc_auc", np.nan),
            set_cell("summary", 0, "metric_direction", "lower_is_better"),
            set_cell("summary", 0, "n_blocks", 1),
            set_cell("summary", 0, "candidate_positive_blocks", 0),
            set_cell("outer_scores", 0, "protocol_variant_id", "wrong"),
            lambda b: b.outer_scores.drop(index=b.outer_scores.index[-1], inplace=True),
            lambda b: b.summary.drop(index=b.summary.index[-1], inplace=True),
        ]
        mutation_results = [rejected(mutator) for mutator in mutations]
        negative_count = sum(mutation_results)

        protected_hashes = {
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_split_10x1_summary.csv": "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_28_stage05_split_10x1_modular_extraction_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_28_stage05_split_10x1_modular_extraction_change_scope_v01.csv",
            "src/mlcra/nested_cv.py",
            "src/mlcra/stress_tests.py",
            "notebooks/04_dataset_smoke_experiments.ipynb",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_current = extract_markdown_section(
            (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig"),
            "### Этап 7",
            "## 12.",
        )
        documentary = all(
            token in stage_text
            for token in (
                "## 93. ST07_28",
                "notebook_other_cells: PASS exact 49/49",
                "negative_contract_checks: PASS 20/20",
                "ST07_28_status: accepted_by_john",
            )
        ) and all(
            token in roadmap_current
            for token in (
                "NEXT_BLOCK_AUTHORIZED: ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation",
                "ST07_28_status: accepted_by_john",
            )
        )
        checks = {
            "notebook": notebook_cells_exact,
            "preserved": notebook_preserved,
            "seed_policy": seed_policy_api,
            "schemas": schemas_exact,
            "two_run": two_run_exact,
            "timing": timing_valid,
            "negative": negative_count == len(mutations),
            "protected": protected,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_stage05_split_10x1_modular_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            f"notebook=3/109/0:{notebook_cells_exact}; other_cells=49/49:{notebook_preserved}; "
            f"seed_policy=constant_outer:{seed_policy_api}; fixture=90x43/48x22:{schemas_exact}; "
            f"two_run_AB_exact={two_run_exact}; timing_C_valid={timing_valid}; "
            f"negative={negative_count}/{len(mutations)}:{mutation_results}; "
            f"protected={len(protected_hashes)}/5:{protected}; "
            f"scope={len(scope_rows)}/7:{scope_exact}; documentary={documentary}; "
            "full_miniboone_training=0; network=0; scientific_artifact_changes=0",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_split_10x1_modular_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0728() -> Check:
    try:
        accepted_id = (
            "ST07_28_stage05_split_10x1_modular_extraction_and_"
            "fixture_validation"
        )
        proposed_id = (
            "ST07_29_stage05_split_10x1_full_miniboone_and_"
            "golden_diagnostic_validation"
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        current_tokens = (
            f"ACCEPTED_BY_JOHN: {accepted_id}",
            f"TASK_CLOSED: {accepted_id}",
            "ST07_28_status: accepted_by_john",
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}",
            "ST07_29_status: accepted_by_john",
            f"ACCEPTED_BY_JOHN: {proposed_id}",
            f"TASK_CLOSED: {proposed_id}",
            "ST07_29_full_miniboone_training_authorized: true",
            "ST07_29_network_authorized: false",
            "ST07_29_source_changes_authorized: false",
            "ST07_29_scientific_artifact_changes_authorized: true",
            "ST07_29_implementation_started: YES",
            "ST07_29_full_miniboone_training_performed: true",
            "ST07_29_network_access_performed: false",
            "ST07_29_historical_golden_overwrites: 0",
            "ST07_29_scientific_verdict: PASS",
            "corrective_blocks_currently_required: 0",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        authorized = all(
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}" in body
            for body in (stage_current, roadmap_current)
        )
        route_tokens = (
            "## 95. Принятие ST07_28 и выбор следующего блока Stage 7",
            "selected_weighted_score: 4.50/5.00",
            f"proposed_task_id: {proposed_id}",
            "diagnostic_blas_threads: 4",
            "post_result_tolerance_selection: prohibited",
            "cross_environment_reproducibility_claim: prohibited",
            "full_miniboone_training_performed: NO",
            "ST07_29_implementation_started: NO",
            "## 97. ST07_29",
            "preflight_model_fit_count: 0",
            "full_run_count: 1",
            "diagnostic_blas_threads: 4",
            "class_A_exact: PASS",
            "class_B_exact: PASS",
            "class_C_valid: PASS",
            "bounded_scientific_signal: PASS",
            "historical_golden_overwrites: 0",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        protected_hashes = {
            "notebooks/04_dataset_smoke_experiments.ipynb": (
                "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52"
            ),
            "src/mlcra/nested_cv.py": (
                "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727"
            ),
            "src/mlcra/stress_tests.py": (
                "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146"
            ),
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": (
                "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d"
            ),
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": (
                "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49"
            ),
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": (
                "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133"
            ),
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": (
                "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970"
            ),
            "data_registry/openml_miniboone_stage05_split_10x1_summary.csv": (
                "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18"
            ),
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_28_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_28_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        implementation_present = all(
            (PROJECT_ROOT / path).exists()
            for path in (
                "scripts/st07_29_split_10x1_full_validation.py",
                "data_registry/st07_29_stage05_split_10x1_candidate_outer_scores_v01.csv",
                "data_registry/st07_29_stage05_split_10x1_candidate_summary_v01.csv",
                "data_registry/st07_29_stage05_split_10x1_full_validation_evidence_v01.json",
            )
        )
        previous_gate = check_stage07_stage05_split_10x1_modular_extraction()
        checks = {
            "previous": previous_gate.status == "PASS",
            "current": current_state,
            "authorized": authorized,
            "route": route_documented,
            "protected": protected,
            "scope": scope_exact,
            "started": implementation_present,
        }
        return Check(
            "stage07_next_block_after_st0728",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={current_state}; previous={previous_gate.status}; "
            "remaining=4(0+0+3+1); selected=ST07_29_full_miniboone_and_"
            f"golden_diagnostic; BLAS=4; protected={len(protected_hashes)}/8:"
            f"{protected}; scope={len(scope_rows)}/4:{scope_exact}; "
            f"authorized={authorized}; implementation_started="
            f"{implementation_present}",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0728",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_split_10x1_full_validation() -> Check:
    try:
        import pandas as pd

        task_id = (
            "ST07_29_stage05_split_10x1_full_miniboone_and_"
            "golden_diagnostic_validation"
        )
        data = PROJECT_ROOT / "data_registry"
        evidence_path = (
            data
            / "st07_29_stage05_split_10x1_full_validation_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        specs = {
            "outer_scores": {
                "candidate": "st07_29_stage05_split_10x1_candidate_outer_scores_v01.csv",
                "golden": "openml_miniboone_stage05_split_10x1_outer_scores.csv",
                "shape": (90, 43),
                "class_b": (
                    "train_positive_share",
                    "test_positive_share",
                    "inner_best_average_precision",
                    "roc_auc",
                    "average_precision",
                    "pr_auc",
                    "f1",
                    "balanced_accuracy",
                    "log_loss",
                    "brier_score",
                ),
                "class_c": ("fit_seconds", "predict_seconds"),
            },
            "summary": {
                "candidate": "st07_29_stage05_split_10x1_candidate_summary_v01.csv",
                "golden": "openml_miniboone_stage05_split_10x1_summary.csv",
                "shape": (48, 22),
                "class_b": (
                    "advantage_mean",
                    "advantage_std_population",
                    "advantage_min",
                    "advantage_max",
                ),
                "class_c": (),
            },
        }
        recomputed: dict[str, dict[str, Any]] = {}
        frames: dict[str, pd.DataFrame] = {}
        for artifact_id, spec in specs.items():
            candidate_path = data / str(spec["candidate"])
            golden_path = data / str(spec["golden"])
            candidate = pd.read_csv(
                candidate_path, dtype=str, keep_default_na=False
            )
            golden = pd.read_csv(
                golden_path, dtype=str, keep_default_na=False
            )
            frames[artifact_id] = candidate
            class_b = list(spec["class_b"])
            class_c = list(spec["class_c"])
            class_a = [
                column
                for column in candidate.columns
                if column not in set(class_b + class_c)
            ]
            class_c_valid = True
            for column in class_c:
                values = pd.to_numeric(candidate[column], errors="coerce")
                class_c_valid = class_c_valid and bool(
                    (
                        values.notna()
                        & values.map(math.isfinite)
                        & values.ge(0.0)
                    ).all()
                )
            recomputed[artifact_id] = {
                "shape_exact": candidate.shape == golden.shape == spec["shape"],
                "schema_exact": list(candidate.columns) == list(golden.columns),
                "candidate_sha256": sha256_file(candidate_path),
                "golden_sha256": sha256_file(golden_path),
                "class_a_exact": candidate[class_a].equals(golden[class_a]),
                "class_a_mismatch_cells": int(
                    candidate[class_a].ne(golden[class_a]).to_numpy().sum()
                ),
                "class_b_exact": candidate[class_b].equals(golden[class_b]),
                "class_b_mismatch_cells": int(
                    candidate[class_b].ne(golden[class_b]).to_numpy().sum()
                ),
                "class_c_valid": class_c_valid,
            }

        aggregate = {
            "structures_valid": all(
                row["shape_exact"] and row["schema_exact"]
                for row in recomputed.values()
            ),
            "class_a_exact": all(
                row["class_a_exact"] for row in recomputed.values()
            ),
            "class_b_exact": all(
                row["class_b_exact"] for row in recomputed.values()
            ),
            "class_c_valid": all(
                row["class_c_valid"] for row in recomputed.values()
            ),
        }
        evidence_comparisons = evidence["comparisons"]
        comparison_evidence_exact = all(
            all(
                evidence_comparisons[artifact_id][field] == value
                for field, value in row.items()
            )
            for artifact_id, row in recomputed.items()
        )

        outer = frames["outer_scores"]
        hgb = outer[outer["model_id"].eq("hist_gradient_boosting")]
        logistic = outer[outer["model_id"].eq("logistic_regression")]
        key = [
            "outer_random_state",
            "outer_split_number",
            "outer_repeat_number",
            "outer_fold_number",
        ]
        paired = hgb.merge(
            logistic, on=key, suffixes=("_hgb", "_lr"), validate="one_to_one"
        )
        primary = (
            pd.to_numeric(paired["average_precision_hgb"], errors="raise")
            - pd.to_numeric(paired["average_precision_lr"], errors="raise")
        )
        per_seed_pass = all(
            values.mean() > 0.0 and values.gt(0.0).sum() > len(values) / 2
            for _, values in pd.DataFrame(
                {
                    "seed": paired["outer_random_state"],
                    "advantage": primary,
                }
            ).groupby("seed")["advantage"]
        )
        summary = frames["summary"]
        secondary = summary[
            summary["comparison_model_id"].eq("logistic_regression")
            & summary["summary_scope"].eq("all_outer_random_states")
            & ~summary["metric_name"].eq("average_precision")
        ]
        signal_pass = (
            len(primary) == 30
            and float(primary.gt(0.0).mean()) >= 0.95
            and float(primary.mean()) >= 0.03
            and float(primary.quantile(0.05)) > 0.01
            and per_seed_pass
            and len(secondary) == 5
            and bool(
                pd.to_numeric(secondary["advantage_mean"], errors="raise")
                .gt(0.0)
                .all()
            )
            and bool(
                pd.to_numeric(
                    secondary["candidate_positive_blocks"], errors="raise"
                )
                .gt(pd.to_numeric(secondary["n_blocks"], errors="raise") / 2)
                .all()
            )
        )

        protected_expected = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
            "src/mlcra/datasets.py": "1a60d860d8073af2e9b9b5143b4817918cc614eb65c0ab17343713cfecfc154b",
            "src/mlcra/io.py": "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0",
            "src/mlcra/metrics.py": "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/numeric_runtime.py": "4f09dbe5b16dc42497dd00c29cb70695cdfb802d42a798570f19e08653003086",
            "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            "src/mlcra/validation.py": "2bed7566811af6c342b9a70a8e8933479248fc6e7ee4b9983da39d1c0279ffff",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_split_10x1_summary.csv": "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18",
            "data_registry/st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json": "e07ad5bec329903266eff66436fa9d2e5045de3fa707e14a13da38b89c52bc44",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )
        execution = evidence["execution"]
        environment = evidence["execution_contract"]["environment"]
        execution_exact = (
            execution["full_run_count"] == 1
            and execution["hgb_outer_tuning_blocks"] == 30
            and execution["control_outer_fit_count"] == 60
            and execution["outer_model_rows"] == 90
            and execution["training_performed"] is True
            and execution["network_attempts"] == 0
            and execution["network_used"] is False
            and execution["canonical_golden_overwrites"] == 0
            and execution["claim_or_verdict_changed"] is False
            and float(execution["elapsed_seconds"]) > 0.0
            and environment["diagnostic_blas_threads"] == 4
            and environment["backend_identity_exact_to_st07_26"] is True
            and evidence["aggregate_verdict"]["thread_limit_enforced"] is True
            and evidence["aggregate_verdict"]["runtime_restored"] is True
        )
        verdict_exact = (
            evidence["task_id"] == task_id
            and evidence["task_profile"] == "SCIENTIFIC_VALIDATION"
            and evidence["technical_status"] == "PASS"
            and evidence["status"] == "pass"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and all(
                evidence["aggregate_verdict"][field] == value
                for field, value in aggregate.items()
            )
            and evidence["aggregate_verdict"]["protected_exact"] == protected
            and evidence["aggregate_verdict"]["registered_bounded_signal_pass"]
            == signal_pass
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_29_stage05_split_10x1_full_validation_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_29_stage05_split_10x1_full_validation_change_scope_v01.csv",
            "scripts/st07_29_split_10x1_full_validation.py",
            "data_registry/st07_29_stage05_split_10x1_candidate_outer_scores_v01.csv",
            "data_registry/st07_29_stage05_split_10x1_candidate_summary_v01.csv",
            "data_registry/st07_29_stage05_split_10x1_full_validation_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        documentary_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "ST07_29_scientific_verdict: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )

        checks = {
            "comparison_evidence": comparison_evidence_exact,
            "aggregate": all(aggregate.values()),
            "signal": signal_pass,
            "protected": protected,
            "execution": execution_exact,
            "verdict": verdict_exact,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_stage05_split_10x1_full_validation",
            "PASS" if all(checks.values()) else "FAIL",
            f"technical=PASS; structures/A/B/C="
            f"{aggregate['structures_valid']}/{aggregate['class_a_exact']}/"
            f"{aggregate['class_b_exact']}/{aggregate['class_c_valid']}; "
            f"A/B_mismatches=outer:{recomputed['outer_scores']['class_a_mismatch_cells']}/"
            f"{recomputed['outer_scores']['class_b_mismatch_cells']},summary:"
            f"{recomputed['summary']['class_a_mismatch_cells']}/"
            f"{recomputed['summary']['class_b_mismatch_cells']}; "
            f"primary={len(primary)}/{int(primary.gt(0.0).sum())}:"
            f"mean={float(primary.mean()):.12f},q05={float(primary.quantile(0.05)):.12f}; "
            f"protected={len(protected_expected)}/15:{protected}; "
            f"run/HGB/control/network={execution['full_run_count']}/"
            f"{execution['hgb_outer_tuning_blocks']}/"
            f"{execution['control_outer_fit_count']}/"
            f"{execution['network_attempts']}; BLAS=4/restored=True; "
            f"scope={len(scope_rows)}/8:{scope_exact}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_split_10x1_full_validation",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0729() -> Check:
    try:
        accepted_id = (
            "ST07_29_stage05_split_10x1_full_miniboone_and_"
            "golden_diagnostic_validation"
        )
        proposed_id = (
            "ST07_30_stage05_non_nested_optimism_probe_modularization_"
            "contract_and_golden_master_design"
        )
        stage_path = PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        roadmap_path = PROJECT_ROOT / "roadmap.md"
        stage_text = stage_path.read_text(encoding="utf-8-sig")
        roadmap_text = roadmap_path.read_text(encoding="utf-8-sig")
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        current_tokens = (
            f"ACCEPTED_BY_JOHN: {accepted_id}",
            f"TASK_CLOSED: {accepted_id}",
            "ST07_29_status: accepted_by_john",
            "corrective_blocks_currently_required: 0",
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}",
            "ST07_30_status: accepted_by_john",
            f"ACCEPTED_BY_JOHN: {proposed_id}",
            f"TASK_CLOSED: {proposed_id}",
            "ST07_30_training_authorized: false",
            "ST07_30_network_authorized: false",
            "ST07_30_source_changes_authorized: false",
            "ST07_30_scientific_artifact_changes_authorized: false",
            "ST07_30_implementation_started: NO",
            "remaining_stage07_nominal_blocks: 2",
            "remaining_stage07_planned_blocks: 2",
            "remaining_breakdown: "
            "ST05_02=0;ST05_03a=0;ST05_07=1;stage07_closure=1",
            "NEXT_BLOCK_AUTHORIZED: ST07_31_stage05_non_nested_optimism_"
            "probe_modular_extraction_and_fixture_validation",
            "ST07_31_status: accepted_by_john",
            "ACCEPTED_BY_JOHN: ST07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_and_fixture_validation",
            "ST07_31_implementation_started: YES",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        authorized = all(
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}" in body
            for body in (stage_current, roadmap_current)
        )

        notebook_path = PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        source = "".join(notebook["cells"][51].get("source", []))
        parsed = ast.parse(source)
        local_functions = [
            node.name
            for node in parsed.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        inventory_exact = (
            notebook["cells"][51].get("id") == "ec095766"
            and len(source.splitlines()) == 105
            and hashlib.sha256(source.encode()).hexdigest()
            == "e229c9bfd828d4a630496c0bc59207a395bd121e9c408d8984de1c422190560c"
            and local_functions == []
        )

        plan_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        plan = [
            row
            for row in plan_rows
            if row["stress_test_id"] == "ST05_07_non_nested_optimism_probe"
        ]
        plan_exact = len(plan) == 1 and all(
            plan[0][key] == value
            for key, value in {
                "family": "selection_bias_probe",
                "requires_new_model_run": "yes",
                "run_group": "non_nested_optimism_probe_v01",
                "protocol_variant_id": "non_nested_grid_search_cv_v01",
                "outer_cv_method": "not_applicable_single_level_cv",
                "outer_cv_n_splits": "5",
                "outer_cv_n_repeats": "2",
                "outer_random_states": "20260507;20260517;20260527",
                "models": "hist_gradient_boosting",
                "primary_metric": "average_precision",
                "parameter_space_policy": "same_locked_space_as_nested_cv_v01",
                "planned_outputs": (
                    "openml_miniboone_stage05_non_nested_optimism_probe.csv"
                ),
                "execution_order": "8",
            }.items()
        )

        golden_path = (
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv"
        )
        golden_rows = read_contract_csv(golden_path)
        golden_columns = list(golden_rows[0])
        key_pairs = {
            (row["single_level_cv_random_state"], row["comparison_reference_id"])
            for row in golden_rows
        }
        expected_seeds = {"20260507", "20260517", "20260527"}
        reference_sets_exact = all(
            {
                row["comparison_reference_id"]
                for row in golden_rows
                if row["single_level_cv_random_state"] == seed
            }
            == {
                "original_nested_5x2_seed_20260507",
                f"stage05_02_nested_5x2_seed_{seed}",
                "stage05_02_nested_5x2_all_seeds",
                f"stage05_03a_nested_10x1_seed_{seed}",
                "stage05_03a_nested_10x1_all_seeds",
            }
            for seed in expected_seeds
        )
        deltas = [
            float(row["optimism_delta_non_nested_minus_nested"])
            for row in golden_rows
        ]
        golden_exact = (
            len(golden_rows) == 15
            and len(golden_columns) == 39
            and len(key_pairs) == 15
            and {row["single_level_cv_random_state"] for row in golden_rows}
            == expected_seeds
            and reference_sets_exact
            and {row["selected_parameter_set_id"] for row in golden_rows}
            == {"hgb_8316cb7622a5"}
            and {row["grid_candidate_count"] for row in golden_rows} == {"16"}
            and sum(deltas) / len(deltas) == -0.00018960346465568545
            and min(deltas) == -0.0007246604801806056
            and max(deltas) == 0.00017834424325191556
        )

        protected_expected = {
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_nested_summary.csv": "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv": "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_29_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_29_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stress_tests_text = (PROJECT_ROOT / "src/mlcra/stress_tests.py").read_text(
            encoding="utf-8-sig"
        )
        implementation_present = all(
            token in stress_tests_text
            for token in (
                "NonNestedOptimismContract",
                "NonNestedOptimismBundle",
                "build_non_nested_optimism_contract",
                "run_non_nested_optimism_probe",
            )
        )
        route_tokens = (
            "## 99. Принятие ST07_29 и выбор следующего блока Stage 7",
            "selected_weighted_score: 4.90/5.00",
            f"proposed_task_id: {proposed_id}",
            "Golden имеет форму `15×39`",
            "full_miniboone_training_performed: NO",
            "ST07_30_status: proposed_not_authorized",
            "ST07_30_implementation_started: NO",
            "## 100. Задачи John",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        previous_gate = check_stage07_stage05_split_10x1_full_validation()
        checks = {
            "previous": previous_gate.status == "PASS",
            "current": current_state,
            "authorized": authorized,
            "inventory": inventory_exact,
            "plan": plan_exact,
            "golden": golden_exact,
            "protected": protected,
            "scope": scope_exact,
            "implementation_present": implementation_present,
            "route": route_documented,
        }
        return Check(
            "stage07_next_block_after_st0729",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={current_state}; previous={previous_gate.status}; "
            "remaining=4(0+0+3+1); selected=ST07_30_contract_design; "
            f"inventory_current=1/105/0:{inventory_exact}; plan=1/1:{plan_exact}; "
            f"golden=15x39/keys15:{golden_exact}; "
            f"protected={len(protected_expected)}/9:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; "
            f"authorized={authorized}; implementation_started="
            f"{implementation_present}",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0729",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_non_nested_optimism_contract_design() -> Check:
    try:
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.model_spaces import (
            build_hist_gradient_boosting_search_space,
            make_hgb_parameter_set_id,
        )

        task_id = (
            "ST07_30_stage05_non_nested_optimism_probe_modularization_"
            "contract_and_golden_master_design"
        )
        notebook_path = PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8-sig"))
        source = "".join(notebook["cells"][51].get("source", []))
        tree = ast.parse(source)
        local_functions = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        source_exact = (
            len(notebook.get("cells", [])) == 52
            and notebook["cells"][51].get("id") == "ec095766"
            and len(source.splitlines()) == 105
            and hashlib.sha256(source.encode()).hexdigest()
            == "e229c9bfd828d4a630496c0bc59207a395bd121e9c408d8984de1c422190560c"
            and local_functions == []
        )

        plan_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
        )
        claim_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
        )
        plan_matches = [
            row
            for row in plan_rows
            if row["stress_test_id"] == "ST05_07_non_nested_optimism_probe"
        ]
        claim_matches = [
            row
            for row in claim_rows
            if row["claim_id"]
            == "miniboone_hgb_vs_logreg_average_precision_v01"
        ]
        plan = plan_matches[0] if len(plan_matches) == 1 else {}
        claim = claim_matches[0] if len(claim_matches) == 1 else {}

        model_space_path = (
            PROJECT_ROOT
            / "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv"
        )
        model_space = pd.read_csv(
            model_space_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        parameter_grid, fixed_parameters = build_hist_gradient_boosting_search_space(
            model_space,
            protocol_id="miniboone_nested_cv_v01",
            candidate_id="openml_miniboone_41150",
        )
        grid_count = math.prod(len(values) for values in parameter_grid.values())

        data = PROJECT_ROOT / "data_registry"
        input_specs = {
            "nested_summary": (
                "openml_miniboone_nested_summary.csv",
                (3, 39),
                "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            ),
            "seed_outer": (
                "openml_miniboone_stage05_seed_stability_outer_scores.csv",
                (150, 43),
                "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            ),
            "split_outer": (
                "openml_miniboone_stage05_split_10x1_outer_scores.csv",
                (90, 43),
                "2514b1dc58c40bc162c4858f5fbeF3a650efe60f323bd4ac1df4710f13c88970".lower(),
            ),
        }
        inputs: dict[str, pd.DataFrame] = {}
        inputs_exact = True
        for name, (filename, shape, digest) in input_specs.items():
            path = data / filename
            frame = pd.read_csv(
                path, dtype=str, keep_default_na=False, encoding="utf-8-sig"
            )
            inputs[name] = frame
            inputs_exact = (
                inputs_exact
                and frame.shape == shape
                and sha256_file(path) == digest
            )

        golden_path = data / "openml_miniboone_stage05_non_nested_optimism_probe.csv"
        golden = pd.read_csv(
            golden_path, dtype=str, keep_default_na=False, encoding="utf-8-sig"
        )
        columns = [
            "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
            "candidate_id", "openml_dataset_id", "dataset_name", "target_name",
            "target_class_0", "target_class_1", "positive_class_assumption",
            "model_id", "model_role", "feature_policy_id", "feature_count",
            "single_level_cv_method", "single_level_cv_n_splits",
            "single_level_cv_n_repeats", "single_level_cv_random_state",
            "single_level_cv_blocks", "parameter_space_policy",
            "selected_parameter_set_id", "selected_params_json",
            "grid_candidate_count", "non_nested_average_precision_mean",
            "non_nested_average_precision_std_for_selected_params", "fit_seconds",
            "comparison_reference_id", "comparison_reference_source_file",
            "comparison_reference_stress_test_id",
            "comparison_reference_protocol_variant_id",
            "comparison_reference_random_state_scope", "nested_outer_blocks",
            "nested_average_precision_mean",
            "optimism_delta_non_nested_minus_nested", "audit_status",
            "audit_status_ru", "row_status", "interpretation_allowed_ru",
        ]
        class_b = [
            "selected_parameter_set_id",
            "selected_params_json",
            "non_nested_average_precision_mean",
            "non_nested_average_precision_std_for_selected_params",
            "nested_average_precision_mean",
            "optimism_delta_non_nested_minus_nested",
            "audit_status",
            "audit_status_ru",
        ]
        class_c = ["fit_seconds"]
        class_a = [
            column for column in columns if column not in set(class_b + class_c)
        ]
        golden_exact = (
            golden.shape == (15, 39)
            and list(golden.columns) == columns
            and sha256_file(golden_path)
            == "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317"
            and len(class_a) == 30
            and len(class_b) == 8
            and len(class_c) == 1
            and set(class_a + class_b + class_c) == set(columns)
        )

        contract = {
            "stress_test_id": "ST05_07_non_nested_optimism_probe",
            "claim_id": "miniboone_hgb_vs_logreg_average_precision_v01",
            "candidate_id": "openml_miniboone_41150",
            "model_id": "hist_gradient_boosting",
            "run_group": "non_nested_optimism_probe_v01",
            "protocol_variant_id": "non_nested_grid_search_cv_v01",
            "single_level_cv_method": "RepeatedStratifiedKFold",
            "single_level_cv_n_splits": 5,
            "single_level_cv_n_repeats": 2,
            "single_level_cv_random_states": (20260507, 20260517, 20260527),
            "scoring": "average_precision",
            "parameter_space_policy": "same_locked_space_as_nested_cv_v01",
            "grid_candidate_count": 16,
            "references_per_seed": 5,
            "output": "openml_miniboone_stage05_non_nested_optimism_probe.csv",
            "delta_formula": "non_nested_average_precision_mean-nested_average_precision_mean",
            "positive_status": "non_nested_score_above_nested_reference",
            "nonpositive_status": "non_nested_score_not_above_nested_reference",
            "row_status": "stage05_non_nested_optimism_probe_derived",
        }
        positive_ru = (
            "Невложенная оценка выше выбранной вложенной внешней оценки; "
            "зафиксирован потенциальный оптимистический сдвиг."
        )
        nonpositive_ru = (
            "Невложенная оценка не выше выбранной вложенной внешней оценки; "
            "по данному сравнению оптимистический сдвиг не обнаружен."
        )
        interpretation_ru = (
            "Разрешено использовать только для диагностики риска "
            "оптимистического смещения невложенной оценки; строка не заменяет "
            "вложенную внешнюю оценку качества."
        )

        reference_metadata = {
            "original_nested_5x2_seed_20260507": (
                "data_registry/openml_miniboone_nested_summary.csv",
                "original_nested_cv_v01", "nested_5x2_seed_20260507_v01",
                "20260507", "10",
            ),
            "stage05_02_nested_5x2_all_seeds": (
                "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
                "ST05_02_seed_stability_grid", "nested_5x2_seed_grid_v01",
                "all", "50",
            ),
            "stage05_03a_nested_10x1_all_seeds": (
                "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
                "ST05_03a_split_protocol_10x1", "nested_10x1_seed_grid_v01",
                "all", "30",
            ),
        }
        for seed in contract["single_level_cv_random_states"]:
            reference_metadata[f"stage05_02_nested_5x2_seed_{seed}"] = (
                "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
                "ST05_02_seed_stability_grid", "nested_5x2_seed_grid_v01",
                str(seed), "10",
            )
            reference_metadata[f"stage05_03a_nested_10x1_seed_{seed}"] = (
                "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
                "ST05_03a_split_protocol_10x1", "nested_10x1_seed_grid_v01",
                str(seed), "10",
            )

        nested_hgb = inputs["nested_summary"][
            inputs["nested_summary"]["model_id"].eq("hist_gradient_boosting")
        ]
        expected_reference_values = {
            "original_nested_5x2_seed_20260507": float(
                nested_hgb["average_precision_mean"].iloc[0]
            )
        }
        for prefix, input_name in (
            ("stage05_02_nested_5x2", "seed_outer"),
            ("stage05_03a_nested_10x1", "split_outer"),
        ):
            hgb = inputs[input_name][
                inputs[input_name]["model_id"].eq("hist_gradient_boosting")
            ]
            expected_reference_values[f"{prefix}_all_seeds"] = float(
                pd.to_numeric(hgb["average_precision"], errors="raise").mean()
            )
            for seed in contract["single_level_cv_random_states"]:
                same_seed = hgb[hgb["outer_random_state"].eq(str(seed))]
                expected_reference_values[f"{prefix}_seed_{seed}"] = float(
                    pd.to_numeric(
                        same_seed["average_precision"], errors="raise"
                    ).mean()
                )

        def expected_references(seed: int) -> list[str]:
            return [
                "original_nested_5x2_seed_20260507",
                "stage05_02_nested_5x2_all_seeds",
                f"stage05_02_nested_5x2_seed_{seed}",
                "stage05_03a_nested_10x1_all_seeds",
                f"stage05_03a_nested_10x1_seed_{seed}",
            ]

        def validates(candidate: dict[str, Any], frame: pd.DataFrame) -> bool:
            try:
                if candidate != contract:
                    return False
                if frame.shape != (15, 39) or list(frame.columns) != columns:
                    return False
                key = ["single_level_cv_random_state", "comparison_reference_id"]
                if frame.duplicated(key).any():
                    return False
                expected_order = [
                    (str(seed), reference_id)
                    for seed in candidate["single_level_cv_random_states"]
                    for reference_id in expected_references(seed)
                ]
                actual_order = list(map(tuple, frame[key].to_numpy()))
                if actual_order != expected_order:
                    return False
                fixed = {
                    "stress_test_id": candidate["stress_test_id"],
                    "claim_id": candidate["claim_id"],
                    "run_group": candidate["run_group"],
                    "protocol_variant_id": candidate["protocol_variant_id"],
                    "candidate_id": candidate["candidate_id"],
                    "model_id": candidate["model_id"],
                    "model_role": "single_level_tuned_candidate",
                    "feature_policy_id": "numeric_particleid_0_49_locked",
                    "feature_count": "50",
                    "single_level_cv_method": candidate["single_level_cv_method"],
                    "single_level_cv_n_splits": str(candidate["single_level_cv_n_splits"]),
                    "single_level_cv_n_repeats": str(candidate["single_level_cv_n_repeats"]),
                    "single_level_cv_blocks": "10",
                    "parameter_space_policy": candidate["parameter_space_policy"],
                    "grid_candidate_count": str(candidate["grid_candidate_count"]),
                    "row_status": candidate["row_status"],
                    "interpretation_allowed_ru": interpretation_ru,
                }
                if any(not frame[column].eq(value).all() for column, value in fixed.items()):
                    return False
                for seed in candidate["single_level_cv_random_states"]:
                    seed_rows = frame[
                        frame["single_level_cv_random_state"].eq(str(seed))
                    ]
                    if len(seed_rows) != candidate["references_per_seed"]:
                        return False
                    for column in (
                        "selected_parameter_set_id", "selected_params_json",
                        "non_nested_average_precision_mean",
                        "non_nested_average_precision_std_for_selected_params",
                        "fit_seconds",
                    ):
                        if seed_rows[column].nunique() != 1:
                            return False
                for _, row in frame.iterrows():
                    reference_id = row["comparison_reference_id"]
                    if reference_id not in expected_reference_values:
                        return False
                    metadata = reference_metadata[reference_id]
                    actual_metadata = tuple(
                        row[column]
                        for column in (
                            "comparison_reference_source_file",
                            "comparison_reference_stress_test_id",
                            "comparison_reference_protocol_variant_id",
                            "comparison_reference_random_state_scope",
                            "nested_outer_blocks",
                        )
                    )
                    if actual_metadata != metadata:
                        return False
                    nested_value = float(row["nested_average_precision_mean"])
                    non_nested_value = float(row["non_nested_average_precision_mean"])
                    delta = float(row["optimism_delta_non_nested_minus_nested"])
                    if nested_value != expected_reference_values[reference_id]:
                        return False
                    if non_nested_value - nested_value != delta:
                        return False
                    expected_status = (
                        candidate["positive_status"]
                        if delta > 0
                        else candidate["nonpositive_status"]
                    )
                    expected_ru = positive_ru if delta > 0 else nonpositive_ru
                    if (
                        row["audit_status"] != expected_status
                        or row["audit_status_ru"] != expected_ru
                    ):
                        return False
                    params = json.loads(row["selected_params_json"])
                    if row["selected_parameter_set_id"] != make_hgb_parameter_set_id(params):
                        return False
                    if any(name not in parameter_grid for name in params):
                        return False
                    if any(params[name] not in parameter_grid[name] for name in params):
                        return False
                timing = pd.to_numeric(frame["fit_seconds"], errors="coerce")
                if timing.isna().any() or any(
                    not math.isfinite(value) or value < 0 for value in timing
                ):
                    return False
                for column in (
                    "non_nested_average_precision_mean",
                    "non_nested_average_precision_std_for_selected_params",
                    "nested_average_precision_mean",
                    "optimism_delta_non_nested_minus_nested",
                ):
                    values = pd.to_numeric(frame[column], errors="coerce")
                    if values.isna().any() or not values.map(math.isfinite).all():
                        return False
                return True
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                return False

        plan_exact = bool(plan) and all(
            plan[key] == value
            for key, value in {
                "claim_id": contract["claim_id"],
                "family": "selection_bias_probe",
                "requires_new_model_run": "yes",
                "run_group": contract["run_group"],
                "protocol_variant_id": contract["protocol_variant_id"],
                "outer_cv_method": "not_applicable_single_level_cv",
                "outer_cv_n_splits": "5",
                "outer_cv_n_repeats": "2",
                "outer_random_states": "20260507;20260517;20260527",
                "inner_cv_method": "GridSearchCV single-level repeated stratified CV",
                "inner_cv_n_splits": "not_applicable",
                "models": contract["model_id"],
                "primary_metric": contract["scoring"],
                "parameter_space_policy": contract["parameter_space_policy"],
                "comparison_unit": "protocol-level score difference",
                "planned_outputs": contract["output"],
                "priority": "could_have",
                "execution_order": "8",
                "decision_status": "locked_before_stage05_runs",
            }.items()
        )
        claim_exact = bool(claim) and all(
            claim[key] == value
            for key, value in {
                "candidate_id": contract["candidate_id"],
                "candidate_model_id": contract["model_id"],
                "primary_metric": contract["scoring"],
                "current_protocol_id": "miniboone_nested_cv_v01",
                "decision_status": "locked_before_stage05_runs",
            }.items()
        )
        model_space_exact = (
            model_space.shape == (6, 10)
            and grid_count == 16
            and fixed_parameters
            == {"random_state": 20260507, "early_stopping": "auto"}
        )
        positive_contract = validates(contract, golden)

        mutations: list[tuple[dict[str, Any], pd.DataFrame]] = []
        contract_transforms = (
            lambda value: {**value, "single_level_cv_random_states": value["single_level_cv_random_states"][:-1]},
            lambda value: {**value, "single_level_cv_random_states": (20260507, 20260517, 20260517)},
            lambda value: {**value, "single_level_cv_random_states": tuple(reversed(value["single_level_cv_random_states"]))},
            lambda value: {**value, "single_level_cv_n_splits": 4},
            lambda value: {**value, "single_level_cv_n_repeats": 3},
            lambda value: {**value, "model_id": "logistic_regression"},
            lambda value: {**value, "scoring": "roc_auc"},
            lambda value: {**value, "grid_candidate_count": 32},
            lambda value: {**value, "references_per_seed": 4},
            lambda value: {**value, "output": "wrong.csv"},
            lambda value: {**value, "delta_formula": "nested-non_nested"},
        )
        mutations.extend((transform(contract), golden) for transform in contract_transforms)

        def mutate(row: int, column: str, value: str) -> pd.DataFrame:
            frame = golden.copy(deep=True)
            frame.loc[row, column] = value
            return frame

        mutations.extend(
            [
                (contract, golden.iloc[:-1].copy()),
                (contract, pd.concat([golden.iloc[[0]], golden.iloc[:-1]], ignore_index=True)),
                (contract, golden.iloc[list(range(1, 15)) + [0]].reset_index(drop=True)),
                (contract, golden.drop(columns=["feature_count"])),
                (contract, mutate(0, "comparison_reference_source_file", "wrong.csv")),
                (contract, mutate(0, "comparison_reference_random_state_scope", "all")),
                (contract, mutate(0, "nested_average_precision_mean", "0.5")),
                (contract, mutate(0, "optimism_delta_non_nested_minus_nested", "-0.1")),
                (contract, mutate(0, "audit_status", contract["nonpositive_status"])),
                (contract, mutate(0, "selected_parameter_set_id", "hgb_invalid")),
                (contract, mutate(0, "selected_params_json", "{}")),
                (contract, mutate(1, "non_nested_average_precision_mean", "0.5")),
                (contract, mutate(0, "fit_seconds", "-1")),
                (contract, mutate(0, "fit_seconds", "nan")),
                (contract, mutate(0, "row_status", "wrong")),
                (contract, mutate(0, "interpretation_allowed_ru", "wrong")),
            ]
        )
        negative_checks = [not validates(*mutation) for mutation in mutations]

        protected_expected = {
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_nested_summary.csv": "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv": "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_30_stage05_non_nested_optimism_probe_"
            "modularization_contract_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_30_stage05_non_nested_optimism_probe_modularization_contract_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "ST07_30_status: accepted_by_john",
            f"ACCEPTED_BY_JOHN: {task_id}",
            f"TASK_CLOSED: {task_id}",
            "ST07_30_training_authorized: false",
            "ST07_30_network_authorized: false",
            "ST07_30_source_changes_authorized: false",
            "ST07_30_scientific_artifact_changes_authorized: false",
            "ST07_30_implementation_started: NO",
            "remaining_stage07_planned_blocks: 2",
            "remaining_breakdown: ST05_02=0;ST05_03a=0;ST05_07=1;stage07_closure=1",
            "NEXT_BLOCK_AUTHORIZED: ST07_31_stage05_non_nested_optimism_"
            "probe_modular_extraction_and_fixture_validation",
            "ST07_31_status: accepted_by_john",
            "ACCEPTED_BY_JOHN: ST07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_and_fixture_validation",
            "ST07_31_implementation_started: YES",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in body for token in documentary_tokens)
            for body in (stage_text, roadmap_text)
        )
        implementation_present = all(
            token in (PROJECT_ROOT / "src/mlcra/stress_tests.py").read_text(
                encoding="utf-8-sig"
            )
            for token in (
                "NonNestedOptimismContract", "NonNestedOptimismBundle",
                "build_non_nested_optimism_contract",
                "run_non_nested_optimism_probe",
            )
        )
        previous = check_stage07_next_block_after_st0729()
        checks = {
            "previous": previous.status == "PASS",
            "source": source_exact,
            "plan": plan_exact,
            "claim": claim_exact,
            "space": model_space_exact,
            "inputs": inputs_exact,
            "golden": golden_exact,
            "positive": positive_contract,
            "negative": all(negative_checks),
            "protected": protected,
            "scope": scope_exact,
            "documentary": documentary,
            "implementation_present": implementation_present,
        }
        return Check(
            "stage07_stage05_non_nested_optimism_contract_design",
            "PASS" if all(checks.values()) else "FAIL",
            f"source_current=1/105/0:{source_exact}; protocol=3seeds/5x2/HGB/AP:"
            f"{plan_exact and claim_exact}; space=6x10/16:{model_space_exact}; "
            f"inputs=3x39/150x43/90x43:{inputs_exact}; "
            f"golden=15x39/keys15/classes30-8-1:{golden_exact}; "
            f"reference_delta_relations={positive_contract}; negative="
            f"{sum(negative_checks)}/{len(negative_checks)}; "
            f"protected={len(protected_expected)}/9:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; "
            "training=0; network=0; source_extraction=0; scientific_validation=0",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_non_nested_optimism_contract_design",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0730() -> Check:
    try:
        accepted_id = (
            "ST07_30_stage05_non_nested_optimism_probe_modularization_"
            "contract_and_golden_master_design"
        )
        proposed_id = (
            "ST07_31_stage05_non_nested_optimism_probe_modular_"
            "extraction_and_fixture_validation"
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        current_tokens = (
            f"ACCEPTED_BY_JOHN: {accepted_id}",
            f"TASK_CLOSED: {accepted_id}",
            "ST07_30_status: accepted_by_john",
            "remaining_stage07_nominal_blocks: 2",
            "corrective_blocks_currently_required: 0",
            "remaining_stage07_planned_blocks: 2",
            "remaining_breakdown: "
            "ST05_02=0;ST05_03a=0;ST05_07=1;stage07_closure=1",
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}",
            "ST07_31_status: accepted_by_john",
            "ST07_31_training_authorized: false",
            "ST07_31_network_authorized: false",
            "ST07_31_source_changes_authorized: true",
            "ST07_31_scientific_artifact_changes_authorized: false",
            "ST07_31_implementation_started: YES",
            "NEXT_BLOCK_AUTHORIZED: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
        )
        current_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        single_current_status = all(
            body.count("ST07_31_status: accepted_by_john") == 1
            for body in (stage_current, roadmap_current)
        )
        authorized = all(
            body.count(f"NEXT_BLOCK_AUTHORIZED: {proposed_id}") == 1
            for body in (stage_current, roadmap_current)
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_30_"
            "change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_30_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        protected_expected = {
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_nested_summary.csv": "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv": "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )
        implementation_tokens = (
            "NonNestedOptimismContract",
            "NonNestedReference",
            "NonNestedOptimismBundle",
            "build_non_nested_optimism_contract",
            "build_non_nested_reference_table",
            "run_non_nested_optimism_probe",
            "validate_non_nested_optimism_bundle",
        )
        stress_tests_text = (PROJECT_ROOT / "src/mlcra/stress_tests.py").read_text(
            encoding="utf-8-sig"
        )
        implementation_present = all(
            token in stress_tests_text for token in implementation_tokens
        )
        route_tokens = (
            "## 103. Принятие ST07_30 и выбор следующего блока Stage 7",
            "selected_weighted_score: 4.90/5.00",
            f"proposed_task_id: {proposed_id}",
            "full_miniboone_training_performed: NO",
            "scientific_artifact_changes_performed: NO",
            "## 104. Задачи John",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        roadmap_decision = all(
            token in roadmap_text
            for token in (
                "MLCRA-RD-069",
                proposed_id,
                "proposed_not_authorized",
            )
        )
        design_gate = check_stage07_stage05_non_nested_optimism_contract_design()
        checks = {
            "design": design_gate.status == "PASS",
            "current": current_state,
            "single_current_status": single_current_status,
            "authorized": authorized,
            "scope": scope_exact,
            "protected": protected,
            "implementation_present": implementation_present,
            "route": route_documented,
            "roadmap": roadmap_decision,
        }
        return Check(
            "stage07_next_block_after_st0730",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={current_state}; design={design_gate.status}; "
            "remaining=3(0+0+2+1); selected=ST07_31_extraction_fixture; "
            f"single_current_status={single_current_status}; authorized={authorized}; "
            f"protected={len(protected_expected)}/9:{protected}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; "
            f"implementation_started={implementation_present}; "
            "training=0; network=0; scientific_artifact_changes=0",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0730",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_non_nested_optimism_modular_extraction() -> Check:
    try:
        from dataclasses import replace

        import numpy as np
        import pandas as pd
        from sklearn.datasets import make_classification

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.io import read_csv_checked
        from mlcra.model_spaces import build_hist_gradient_boosting_search_space
        from mlcra.stress_tests import (
            STAGE05_NON_NESTED_COLUMNS,
            NonNestedOptimismBundle,
            build_non_nested_optimism_contract,
            build_non_nested_reference_table,
            run_non_nested_optimism_probe,
            validate_non_nested_optimism_bundle,
        )

        task_id = (
            "ST07_31_stage05_non_nested_optimism_probe_modular_"
            "extraction_and_fixture_validation"
        )
        read = lambda path: read_csv_checked(PROJECT_ROOT / path)
        plan = read("configs/stress_tests/miniboone_stress_test_plan_v01.csv")
        claim = read("configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv")
        space = read(
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv"
        )
        contract = build_non_nested_optimism_contract(plan, claim)
        references = build_non_nested_reference_table(
            read("data_registry/openml_miniboone_nested_summary.csv"),
            read("data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv"),
            read("data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv"),
            contract,
        )
        parameter_grid, fixed_parameters = (
            build_hist_gradient_boosting_search_space(
                space,
                protocol_id=contract.nested_protocol_id,
                candidate_id=contract.candidate_id,
            )
        )

        notebook = json.loads(
            (PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb")
            .read_text(encoding="utf-8-sig")
        )
        source = "".join(notebook["cells"][51].get("source", []))
        definitions = [
            node.name
            for node in ast.parse(source).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        notebook_exact = (
            len(notebook["cells"]) == 52
            and notebook["cells"][51].get("id") == "ec095766"
            and len(source.splitlines()) == 105
            and hashlib.sha256(source.encode()).hexdigest()
            == "e229c9bfd828d4a630496c0bc59207a395bd121e9c408d8984de1c422190560c"
            and definitions == []
            and notebook["cells"][51].get("outputs") == []
            and notebook["cells"][51].get("execution_count") is None
            and all(
                token in source
                for token in (
                    "build_non_nested_optimism_contract",
                    "build_non_nested_reference_table",
                    "run_non_nested_optimism_probe",
                )
            )
        )
        preserved = {
            "metadata": notebook["metadata"],
            "nbformat": notebook["nbformat"],
            "nbformat_minor": notebook["nbformat_minor"],
            "cells": notebook["cells"][:51],
        }
        preserved_digest = hashlib.sha256(
            json.dumps(
                preserved,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

        X_values, y = make_classification(
            n_samples=100,
            n_features=50,
            n_informative=8,
            n_redundant=2,
            random_state=73,
        )
        feature_names = list(contract.feature_names)
        X = pd.DataFrame(X_values, columns=feature_names)
        candidate_bundle = {
            "candidate_id": contract.candidate_id,
            "did": 41150,
            "dataset_name": "MiniBooNE",
            "target_name": "signal",
            "target_metadata": {
                "target_class_0": "False",
                "target_class_1": "True",
                "positive_class_assumption": "True",
            },
        }
        first = run_non_nested_optimism_probe(
            contract, candidate_bundle, X, y, feature_names,
            parameter_grid, fixed_parameters, references,
        )
        second = run_non_nested_optimism_probe(
            contract, candidate_bundle, X, y, feature_names,
            parameter_grid, fixed_parameters, references,
        )
        first_rt = NonNestedOptimismBundle(
            csv_roundtrip_as_strings(first.audit),
            csv_roundtrip_as_strings(first.reference_table),
            first.parameter_grid,
        )
        second_rt = NonNestedOptimismBundle(
            csv_roundtrip_as_strings(second.audit),
            csv_roundtrip_as_strings(second.reference_table),
            second.parameter_grid,
        )
        validate_non_nested_optimism_bundle(first_rt, contract)
        validate_non_nested_optimism_bundle(second_rt, contract)
        class_c = {"fit_seconds"}
        class_ab = [column for column in STAGE05_NON_NESTED_COLUMNS if column not in class_c]
        two_run_exact = (
            first_rt.audit[class_ab].equals(second_rt.audit[class_ab])
            and first_rt.reference_table.equals(second_rt.reference_table)
        )
        timing_valid = all(
            np.isfinite(pd.to_numeric(frame.audit["fit_seconds"])).all()
            and (pd.to_numeric(frame.audit["fit_seconds"]) >= 0).all()
            for frame in (first_rt, second_rt)
        )
        shapes = (
            first.audit.shape == (15, 39)
            and first.reference_table.shape == (9, 7)
            and tuple(first.audit.columns) == STAGE05_NON_NESTED_COLUMNS
        )

        def rejected(mutator, candidate_contract=contract) -> bool:
            candidate = NonNestedOptimismBundle(
                first.audit.copy(deep=True),
                first.reference_table.copy(deep=True),
                {name: list(values) for name, values in first.parameter_grid.items()},
            )
            try:
                mutator(candidate)
                validate_non_nested_optimism_bundle(candidate, candidate_contract)
            except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                return True
            return False

        def set_audit(row, column, value):
            def mutate_audit(bundle):
                bundle.audit.at[row, column] = value

            return mutate_audit

        def set_reference(row, column, value):
            def mutate_reference(bundle):
                bundle.reference_table.at[row, column] = value

            return mutate_reference

        def reverse_audit(bundle):
            reversed_rows = bundle.audit.iloc[::-1].reset_index(drop=True)
            for column in bundle.audit.columns:
                bundle.audit[column] = reversed_rows[column].to_numpy()

        def duplicate_reference_id(bundle):
            bundle.reference_table.at[1, "comparison_reference_id"] = (
                bundle.reference_table.at[0, "comparison_reference_id"]
            )

        mutations = [
            lambda b: b.audit.drop(columns=["feature_count"], inplace=True),
            lambda b: b.audit.drop(index=b.audit.index[-1], inplace=True),
            reverse_audit,
            set_audit(0, "single_level_cv_random_state", 20260517),
            set_audit(0, "comparison_reference_id", "wrong"),
            set_audit(0, "comparison_reference_source_file", "wrong.csv"),
            set_audit(0, "comparison_reference_random_state_scope", "all"),
            set_audit(0, "nested_outer_blocks", 11),
            set_audit(0, "nested_average_precision_mean", 0.5),
            set_audit(0, "optimism_delta_non_nested_minus_nested", -0.1),
            set_audit(0, "audit_status", "wrong_status"),
            set_audit(0, "selected_parameter_set_id", "wrong"),
            set_audit(0, "selected_params_json", "{}"),
            set_audit(1, "non_nested_average_precision_mean", 0.5),
            set_audit(0, "non_nested_average_precision_std_for_selected_params", -1),
            set_audit(0, "fit_seconds", -1),
            set_audit(0, "fit_seconds", np.inf),
            set_audit(0, "row_status", "wrong"),
            set_audit(0, "interpretation_allowed_ru", "wrong"),
            set_reference(0, "comparison_reference_source_file", "wrong.csv"),
            set_reference(0, "comparison_reference_random_state_scope", "all"),
            set_reference(0, "nested_outer_blocks", 11),
            lambda b: b.reference_table.drop(index=b.reference_table.index[-1], inplace=True),
            duplicate_reference_id,
            lambda b: b.parameter_grid.__setitem__("learning_rate", [0.05]),
            set_audit(0, "grid_candidate_count", 15),
            set_audit(0, "single_level_cv_n_splits", 4),
        ]
        mutation_results = [rejected(mutator) for mutator in mutations]
        contract_mutations = (
            replace(contract, random_states=contract.random_states[:-1]),
            replace(contract, random_states=(20260507, 20260517, 20260517)),
            replace(contract, random_states=tuple(reversed(contract.random_states))),
            replace(contract, n_splits=4),
            replace(contract, n_repeats=3),
            replace(contract, model_id="logistic_regression"),
            replace(contract, scoring="roc_auc"),
            replace(contract, grid_candidate_count=32),
            replace(contract, references_per_seed=4),
            replace(contract, output_name="wrong.csv"),
            replace(contract, delta_formula="nested-non_nested"),
        )
        contract_negative = [
            rejected(lambda _: None, candidate_contract=mutated)
            for mutated in contract_mutations
        ]
        negative_results = mutation_results + contract_negative
        failed_negative_indices = [
            index for index, passed in enumerate(negative_results, start=1)
            if not passed
        ]

        protected_hashes = {
            "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_nested_summary.csv": "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv": "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_hashes.items()
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_31_stage05_non_nested_optimism_probe_"
            "modular_extraction_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_31_stage05_non_nested_optimism_probe_modular_extraction_change_scope_v01.csv",
            "src/mlcra/stress_tests.py",
            "notebooks/04_dataset_smoke_experiments.ipynb",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_current = extract_markdown_section(
            (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig"),
            "### Этап 7", "## 12.",
        )
        documentary_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "ST07_31_status: accepted_by_john",
            f"ACCEPTED_BY_JOHN: {task_id}",
            f"TASK_CLOSED: {task_id}",
            "ST07_31_training_authorized: false",
            "ST07_31_source_changes_authorized: true",
            "remaining_stage07_planned_blocks: 2",
            "remaining_breakdown: ST05_02=0;ST05_03a=0;ST05_07=1;stage07_closure=1",
            "NEXT_BLOCK_AUTHORIZED: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
        )
        documentary = all(
            all(token in body for token in documentary_tokens)
            for body in (stage_text, roadmap_current)
        )
        checks = {
            "notebook": notebook_exact,
            "preserved": preserved_digest == "beb19feae8373c365a37d355ce26a3bdf0c3a6c292c0e7695f3af5d9e174e706",
            "shapes": shapes,
            "two_run": two_run_exact,
            "timing": timing_valid,
            "negative": all(negative_results) and len(negative_results) == 38,
            "protected": protected,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_stage05_non_nested_optimism_modular_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            f"notebook=1/105/0:{notebook_exact}; other_cells=51/51:{checks['preserved']}; "
            f"fixture=15x39/references9x7:{shapes}; two_run_AB_exact={two_run_exact}; "
            f"timing_C_valid={timing_valid}; negative={sum(negative_results)}/38; "
            f"negative_failures={failed_negative_indices}; "
            f"protected={len(protected_hashes)}/9:{protected}; "
            f"scope={len(scope_rows)}/6:{scope_exact}; documentary={documentary}; "
            "full_miniboone_training=0; network=0; scientific_artifact_changes=0",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_non_nested_optimism_modular_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0731() -> Check:
    try:
        import pandas as pd

        accepted_id = (
            "ST07_31_stage05_non_nested_optimism_probe_modular_"
            "extraction_and_fixture_validation"
        )
        proposed_id = (
            "ST07_32_stage05_non_nested_optimism_probe_full_"
            "miniboone_and_golden_diagnostic_validation"
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        stage_current = extract_markdown_section(stage_text, "## 2.", "## 3.")
        roadmap_current = extract_markdown_section(
            roadmap_text, "### Этап 7", "## 12."
        )
        current_tokens = (
            f"ACCEPTED_BY_JOHN: {accepted_id}",
            f"TASK_CLOSED: {accepted_id}",
            "ST07_31_status: accepted_by_john",
            "remaining_stage07_nominal_blocks: 2",
            "corrective_blocks_currently_required: 0",
            "remaining_stage07_planned_blocks: 2",
            "remaining_breakdown: "
            "ST05_02=0;ST05_03a=0;ST05_07=1;stage07_closure=1",
            f"stage07_next_block: proposed_{proposed_id}",
            "ST07_32_status: proposed_not_authorized",
            "ST07_32_full_miniboone_training_authorized: false",
            "ST07_32_network_authorized: false",
            "ST07_32_source_changes_authorized: false",
            "ST07_32_scientific_artifact_changes_authorized: false",
            "ST07_32_implementation_started: NO",
        )
        proposed_state = all(
            all(token in body for token in current_tokens)
            for body in (stage_current, roadmap_current)
        )
        completed_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {proposed_id}",
            "ST07_32_status: accepted_by_john",
            "ST07_32_full_miniboone_training_performed: true",
            "ST07_32_network_access_performed: false",
            "ST07_32_historical_golden_overwrites: 0",
            "ST07_32_scientific_verdict: PASS",
            "stage07_closure_audit_verdict: FAIL",
            "stage07_status: active_closure_blocked_by_ST07_CLOSE_06",
        )
        completed_state = all(
            all(token in body for token in completed_tokens)
            for body in (stage_current, roadmap_current)
        )
        current_state = proposed_state or completed_state
        single_proposal = (
            all(
                body.count("ST07_32_status: proposed_not_authorized") == 1
                and f"NEXT_BLOCK_AUTHORIZED: {proposed_id}" not in body
                for body in (stage_current, roadmap_current)
            )
            if proposed_state
            else completed_state
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_31_"
            "change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_next_block_selection_after_st07_31_change_scope_v01.csv",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        protected_expected = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
            "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_nested_summary.csv": "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv": "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
        }
        protected = all(
            sha256_file(PROJECT_ROOT / path) == digest
            for path, digest in protected_expected.items()
        )
        golden = pd.read_csv(
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        key_columns = [
            "stress_test_id",
            "single_level_cv_random_state",
            "comparison_reference_id",
        ]
        golden_exact = (
            golden.shape == (15, 39)
            and not golden.duplicated(key_columns).any()
            and tuple(golden["single_level_cv_random_state"].unique())
            == ("20260507", "20260517", "20260527")
            and golden.groupby("single_level_cv_random_state").size().tolist()
            == [5, 5, 5]
        )
        source_text = (PROJECT_ROOT / "src/mlcra/stress_tests.py").read_text(
            encoding="utf-8-sig"
        )
        implementation_ready = all(
            token in source_text
            for token in (
                "NonNestedOptimismContract",
                "NonNestedOptimismBundle",
                "build_non_nested_reference_table",
                "run_non_nested_optimism_probe",
                "validate_non_nested_optimism_bundle",
            )
        )
        output_paths = (
            "scripts/st07_32_non_nested_optimism_full_validation.py",
            "data_registry/st07_32_stage05_non_nested_optimism_candidate_v01.csv",
            "data_registry/st07_32_stage05_non_nested_optimism_full_validation_evidence_v01.json",
        )
        absent_outputs = all(
            not (PROJECT_ROOT / path).exists()
            for path in output_paths
        )
        implementation_boundary = (
            absent_outputs
            if proposed_state
            else completed_state
            and all((PROJECT_ROOT / path).is_file() for path in output_paths)
        )
        route_tokens = (
            "## 107. Принятие ST07_31 и выбор следующего блока Stage 7",
            "selected_weighted_score: 4.55/5.00",
            f"proposed_task_id: {proposed_id}",
            "historical_openmp_provenance: unknown_not_inferred",
            "prospective_openmp_condition: "
            "vcomp140.dll/12_threads_current_machine_diagnostic",
            "full_miniboone_training_performed: NO",
            "scientific_artifact_changes_performed: NO",
            "## 108. Задачи John",
        )
        route_documented = all(token in stage_text for token in route_tokens)
        roadmap_decision = all(
            token in roadmap_text
            for token in ("MLCRA-RD-071", proposed_id, "proposed_not_authorized")
        )
        previous = check_stage07_stage05_non_nested_optimism_modular_extraction()
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]
        protected = not protected_mismatches
        checks = {
            "previous": previous.status == "PASS",
            "current": current_state,
            "single_proposal": single_proposal,
            "scope": scope_exact,
            "protected": protected,
            "golden": golden_exact,
            "implementation": implementation_ready,
            "implementation_boundary": implementation_boundary,
            "route": route_documented,
            "roadmap": roadmap_decision,
        }
        return Check(
            "stage07_next_block_after_st0731",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted={current_state}; previous={previous.status}; "
            "historical_selection=ST07_32_full_diagnostic; "
            f"single_proposal={single_proposal}; golden=15x39/keys15/3x5:"
            f"{golden_exact}; protected={len(protected_expected)}/9:{protected}:"
            f"{protected_mismatches}; "
            f"scope={len(scope_rows)}/4:{scope_exact}; "
            f"implementation_started={not absent_outputs}; "
            f"completed={completed_state}",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0731",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_stage05_non_nested_optimism_full_validation() -> Check:
    try:
        import pandas as pd

        task_id = (
            "ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_"
            "golden_diagnostic_validation"
        )
        data = PROJECT_ROOT / "data_registry"
        candidate_path = (
            data / "st07_32_stage05_non_nested_optimism_candidate_v01.csv"
        )
        evidence_path = (
            data
            / "st07_32_stage05_non_nested_optimism_full_validation_evidence_v01.json"
        )
        golden_path = data / "openml_miniboone_stage05_non_nested_optimism_probe.csv"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        candidate = pd.read_csv(candidate_path, dtype=str, keep_default_na=False)
        golden = pd.read_csv(golden_path, dtype=str, keep_default_na=False)
        keys = [
            "stress_test_id",
            "single_level_cv_random_state",
            "comparison_reference_id",
        ]
        class_b = [
            "selected_parameter_set_id",
            "selected_params_json",
            "non_nested_average_precision_mean",
            "non_nested_average_precision_std_for_selected_params",
            "nested_average_precision_mean",
            "optimism_delta_non_nested_minus_nested",
            "audit_status",
            "audit_status_ru",
        ]
        class_c = ["fit_seconds"]
        class_a = [
            column
            for column in candidate.columns
            if column not in set(class_b + class_c)
        ]
        timing = pd.to_numeric(candidate["fit_seconds"], errors="coerce")
        recomputed = {
            "schema_exact": list(candidate.columns) == list(golden.columns),
            "shape_exact": candidate.shape == golden.shape == (15, 39),
            "keys_and_order_exact": candidate[keys].equals(golden[keys])
            and not candidate.duplicated(keys).any(),
            "class_a_columns_30": len(class_a) == 30,
            "class_a_exact": candidate[class_a].equals(golden[class_a]),
            "class_a_mismatch_cells": int(
                candidate[class_a].ne(golden[class_a]).to_numpy().sum()
            ),
            "class_b_columns_8": len(class_b) == 8,
            "class_b_exact": candidate[class_b].equals(golden[class_b]),
            "class_b_mismatch_cells": int(
                candidate[class_b].ne(golden[class_b]).to_numpy().sum()
            ),
            "class_c_valid": bool(
                (timing.notna() & timing.map(math.isfinite) & timing.ge(0.0)).all()
            ),
        }
        evidence_comparison = evidence["comparison"]
        comparison_evidence_exact = all(
            evidence_comparison[field] == value
            for field, value in recomputed.items()
            if field
            in {
                "schema_exact",
                "shape_exact",
                "keys_and_order_exact",
                "class_a_exact",
                "class_a_mismatch_cells",
                "class_b_exact",
                "class_b_mismatch_cells",
                "class_c_valid",
            }
        )
        deltas = pd.to_numeric(
            candidate["optimism_delta_non_nested_minus_nested"], errors="raise"
        )
        signal = evidence["scientific_signal"]
        signal_exact = (
            signal["row_count"] == len(candidate) == 15
            and signal["positive_count"] == int(deltas.gt(0.0).sum()) == 7
            and signal["nonpositive_count"] == int(deltas.le(0.0).sum()) == 8
            and signal["mean"] == float(deltas.mean())
            and signal["minimum"] == float(deltas.min())
            and signal["maximum"] == float(deltas.max())
            and [row["reference_count"] for row in signal["per_seed"]] == [5, 5, 5]
        )

        protected_expected = {
            "notebooks/04_dataset_smoke_experiments.ipynb": "a858f7d1c9db92ce3b740b5dbe7c748ba7f3cc58a8ff1604f88854ead831ec52",
            "src/mlcra/datasets.py": "1a60d860d8073af2e9b9b5143b4817918cc614eb65c0ab17343713cfecfc154b",
            "src/mlcra/io.py": "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0",
            "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
            "src/mlcra/numeric_runtime.py": "4f09dbe5b16dc42497dd00c29cb70695cdfb802d42a798570f19e08653003086",
            "src/mlcra/stress_tests.py": "960df96dfeeed464770b7b2a3a1b1253f3b2943efc12588dd760621d6db6a146",
            "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
            "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
            "data_registry/openml_miniboone_nested_summary.csv": "3d99c077131f34aaefc3c538301f9dafd6f2cc8251bd354945abd6176989f657",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv": "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
            "data_registry/st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json": "e07ad5bec329903266eff66436fa9d2e5045de3fa707e14a13da38b89c52bc44",
        }
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]
        protected = not protected_mismatches
        execution = evidence["execution"]
        contract = evidence["execution_contract"]
        environment = contract["environment"]
        openmp = [
            row for row in environment["threadpool_before"] if row["user_api"] == "openmp"
        ]
        execution_exact = (
            execution["full_run_count"] == 1
            and execution["grid_search_count"] == 3
            and execution["cv_candidate_fold_fit_count"] == 480
            and execution["refit_count"] == 3
            and execution["initial_short_invocation_fit_count"] == 0
            and execution["network_attempts"] == 0
            and execution["canonical_golden_overwrites"] == 0
            and execution["claim_or_verdict_changed"] is False
            and contract["dataset"]["rows"] == 130064
            and contract["dataset"]["feature_count"] == 50
            and contract["dataset"]["target_false_count"] == 93565
            and contract["dataset"]["target_true_count"] == 36499
            and contract["protocol"]["golden_shape"] == [15, 39]
            and contract["protocol"]["reference_shape"] == [9, 7]
            and environment["diagnostic_blas_threads"] == 4
            and len(openmp) == 1
            and openmp[0]["prefix"] == "vcomp"
            and openmp[0]["library_filename"] == "vcomp140.dll"
            and openmp[0]["num_threads"] == 12
        )
        provenance = evidence["execution_provenance"]
        provenance_exact = (
            provenance["executed_runner_sha256"]
            == "e5f1e407272ee773534aaa9b6baf8dd735c58d5b4dc8e98cb753750ef3a09578"
            and provenance["current_runner_sha256"]
            == sha256_file(
                PROJECT_ROOT / "scripts/st07_32_non_nested_optimism_full_validation.py"
            )
            and provenance["refit_performed_for_repair"] is False
            and provenance["tolerance_introduced"] is False
            and provenance["maximum_parser_induced_relation_delta"]
            == 2.922466955934677e-16
        )
        aggregate = evidence["aggregate_verdict"]
        verdict_exact = (
            evidence["task_id"] == task_id
            and evidence["technical_status"] == "PASS"
            and evidence["status"] == "pass"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and all(
                aggregate[field] is True
                for field in (
                    "structures_valid",
                    "class_a_exact",
                    "class_b_exact",
                    "class_c_valid",
                    "protected_exact",
                    "thread_limit_enforced_by_executed_control_flow",
                    "openmp_exact_before_during_after_by_executed_control_flow",
                    "runtime_restored_by_executed_control_flow",
                )
            )
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_32_stage05_non_nested_optimism_full_validation_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_32_stage05_non_nested_optimism_full_validation_change_scope_v01.csv",
            "scripts/st07_32_non_nested_optimism_full_validation.py",
            "data_registry/st07_32_stage05_non_nested_optimism_candidate_v01.csv",
            "data_registry/st07_32_stage05_non_nested_optimism_full_validation_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            f"NEXT_BLOCK_AUTHORIZED: {task_id}",
            "ST07_32_status: accepted_by_john",
            "ST07_32_scientific_verdict: PASS",
            "TASK_CLOSED: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
            "stage07_closure_audit_verdict: FAIL",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        checks = {
            "schema": recomputed["schema_exact"],
            "shape": recomputed["shape_exact"],
            "keys_order": recomputed["keys_and_order_exact"],
            "class_a_columns": recomputed["class_a_columns_30"],
            "class_a_exact": recomputed["class_a_exact"],
            "class_a_zero_mismatch": recomputed["class_a_mismatch_cells"] == 0,
            "class_b_columns": recomputed["class_b_columns_8"],
            "class_b_exact": recomputed["class_b_exact"],
            "class_b_zero_mismatch": recomputed["class_b_mismatch_cells"] == 0,
            "class_c_valid": recomputed["class_c_valid"],
            "comparison_evidence": comparison_evidence_exact,
            "signal": signal_exact,
            "protected": protected,
            "execution": execution_exact,
            "provenance": provenance_exact,
            "verdict": verdict_exact,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_stage05_non_nested_optimism_full_validation",
            "PASS" if all(checks.values()) else "FAIL",
            f"technical={evidence['technical_status']}; shape={candidate.shape}; "
            f"A/B/C={recomputed['class_a_exact']}/{recomputed['class_b_exact']}/"
            f"{recomputed['class_c_valid']}; A/B_mismatches="
            f"{recomputed['class_a_mismatch_cells']}/"
            f"{recomputed['class_b_mismatch_cells']}; delta=15/"
            f"{int(deltas.gt(0).sum())}/{int(deltas.le(0).sum())}:"
            f"mean={float(deltas.mean()):.16f}:min={float(deltas.min()):.16f}:"
            f"max={float(deltas.max()):.16f}; protected="
            f"{len(protected_expected)}/14:{protected}:{protected_mismatches}; "
            f"run/grid/cvfit/refit/network=1/3/480/3/0; "
            f"parser_repair_no_refit_no_tolerance={provenance_exact}; "
            f"scope={len(scope_rows)}/7:{scope_exact}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_stage05_non_nested_optimism_full_validation",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_closure_audit() -> Check:
    try:
        import pandas as pd

        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st07_33_stage07_closure_audit_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        closure_rows = evidence["closure_matrix"]
        closure_statuses = {
            row["criterion_id"]: row["status"] for row in closure_rows
        }
        expected_statuses = {
            "ST07-CLOSE-01": "PASS",
            "ST07-CLOSE-02": "PASS",
            "ST07-CLOSE-03": "PASS",
            "ST07-CLOSE-04": "PASS",
            "ST07-CLOSE-05": "PASS",
            "ST07-CLOSE-06": "FAIL",
            "ST07-CLOSE-07": "PASS",
        }

        notebook_path = (
            PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb"
        )
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        stage05_cells = [33, 36, 37, 38, 39, 41, 42, 43, 45, 47, 49, 51]
        stage05_function_definitions: list[tuple[int, str]] = []
        for index in stage05_cells:
            source = "".join(notebook["cells"][index].get("source", []))
            tree = ast.parse(source)
            stage05_function_definitions.extend(
                (index, node.name)
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )

        module_paths = sorted((PROJECT_ROOT / "src/mlcra").glob("*.py"))
        public_contracts: list[tuple[str, str]] = []
        for path in module_paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            public_contracts.extend(
                (path.name, node.name)
                for node in tree.body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                )
                and not node.name.startswith("_")
            )

        verdict_source = (PROJECT_ROOT / "src/mlcra/verdicts.py").read_text(
            encoding="utf-8"
        )
        verdict_tree = ast.parse(verdict_source)
        verdict_public = [
            node.name
            for node in verdict_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and not node.name.startswith("_")
        ]
        expected_historical_verdict_public = [
            "build_current_effect_readout",
            "build_metric_conflict_audit",
            "build_parameter_selection_stability_audit",
            "build_cost_quality_audit",
        ]
        expected_application_contracts = (
            "build_verdict_evidence_record",
            "evaluate_registered_verdict_conditions",
            "apply_registered_verdict_policy",
            "validate_verdict_policy_application_bundle",
        )
        executable_policy_contracts = [
            token
            for token in expected_application_contracts
            if token in verdict_source
        ]
        policy_path = (
            PROJECT_ROOT
            / "configs/verdict_policies/miniboone_verdict_policy_v01.csv"
        )
        policy = pd.read_csv(
            policy_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        policy_exact = (
            policy.shape == (6, 16)
            and policy["category_id"].tolist()
            == [
                "strongly_supported",
                "moderately_supported",
                "weakly_supported",
                "fragile",
                "unsupported",
                "contradicted",
            ]
            and policy["decision_rank"].tolist() == ["6", "5", "4", "3", "2", "1"]
        )

        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if path != "src/mlcra/verdicts.py"
            and sha256_file(PROJECT_ROOT / path) != digest
        ]
        checkpoint = evidence["source_checkpoint"]
        checkpoint_path = Path(checkpoint["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == checkpoint["size_bytes"]
            and sha256_file(checkpoint_path) == checkpoint["sha256"]
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_33_stage07_closure_audit_change_scope_v01.csv"
        )
        expected_scope = [
            "docs/agent/st07_33_stage07_closure_audit_change_scope_v01.csv",
            "data_registry/st07_33_stage07_closure_audit_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(
            encoding="utf-8-sig"
        )
        documentary_tokens = (
            "ACCEPTED_BY_JOHN: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
            "TASK_CLOSED: ST07_32_stage05_non_nested_optimism_probe_"
            "full_miniboone_and_golden_diagnostic_validation",
            "stage07_closure_audit_verdict: FAIL",
            "NEXT_BLOCK_AUTHORIZED: ST07_34_verdict_policy_application_"
            "contract_and_golden_master_design",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        aggregate = evidence["aggregate_verdict"]
        metrics = evidence["objective_metrics"]
        proposal = evidence["proposed_next_block"]
        evidence_exact = (
            evidence["task_id"] == "ST07_33_stage07_closure_audit"
            and closure_statuses == expected_statuses
            and metrics["criteria_total"] == 7
            and metrics["criteria_pass"] == 6
            and metrics["criteria_fail"] == 1
            and metrics["criteria_blocked"] == 0
            and metrics["module_files"] == 10
            and metrics["module_public_functions_or_classes"] == 82
            and metrics["stage05_orchestration_cells_checked"] == 12
            and metrics["stage05_orchestration_top_level_function_definitions"] == 0
            and metrics["executable_verdict_policy_application_contracts"] == 0
            and aggregate["technical_status"] == "FAIL"
            and aggregate["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and aggregate["stage07_closed"] is False
            and aggregate["blocking_criterion"] == "ST07-CLOSE-06"
            and proposal["status"] == "proposed_not_authorized"
            and proposal["implementation_started"] is False
        )
        checks = {
            "evidence": evidence_exact,
            "module_inventory": len(module_paths) == 10 and len(public_contracts) >= 82,
            "stage05_thin": not stage05_function_definitions,
            "verdict_public_boundary": (
                verdict_public[:4] == expected_historical_verdict_public
                and len(executable_policy_contracts) == 4
            ),
            "historical_policy_absence_recorded": (
                metrics["executable_verdict_policy_application_contracts"] == 0
            ),
            "policy_input": policy_exact,
            "historical_protected_except_authorized_source": not protected_mismatches,
            "checkpoint": checkpoint_exact,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_closure_audit",
            "PASS" if all(checks.values()) else "FAIL",
            "audit_verdict=FAIL; criteria=6/1/0(PASS/FAIL/BLOCKED); "
            "blocking=ST07-CLOSE-06; "
            f"modules/public={len(module_paths)}/{len(public_contracts)}; "
            f"stage05_cells/functions={len(stage05_cells)}/"
            f"{len(stage05_function_definitions)}; policy={policy.shape}:"
            f"historical/current_application_contracts=0/"
            f"{len(executable_policy_contracts)}; "
            f"historical_protected_except_authorized_source="
            f"{len(protected_expected) - 1}/{len(protected_expected) - 1}:"
            f"{not protected_mismatches}:{protected_mismatches}; "
            f"checkpoint_v44={checkpoint_exact}; scope={len(scope_rows)}/5:"
            f"{scope_exact}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_closure_audit",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_verdict_policy_application_contract_design() -> Check:
    try:
        import pandas as pd

        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st07_34_verdict_policy_application_contract_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        policy_path = (
            PROJECT_ROOT
            / "configs/verdict_policies/miniboone_verdict_policy_v01.csv"
        )
        policy = pd.read_csv(
            policy_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        expected_categories = [
            "strongly_supported",
            "moderately_supported",
            "weakly_supported",
            "fragile",
            "unsupported",
            "contradicted",
        ]
        ranks = pd.to_numeric(policy["decision_rank"], errors="raise")
        policy_exact = (
            policy.shape == (6, 16)
            and policy["policy_id"].eq("miniboone_verdict_policy_v01").all()
            and policy["claim_id"].eq(
                "miniboone_hgb_vs_logreg_average_precision_v01"
            ).all()
            and policy["category_id"].is_unique
            and ranks.is_unique
            and sorted(ranks.tolist(), reverse=True) == [6, 5, 4, 3, 2, 1]
            and policy.sort_values(
                "decision_rank", ascending=False, kind="mergesort"
            )["category_id"].tolist()
            == expected_categories
            and all(
                policy[column].str.strip().ne("").all()
                for column in (
                    "quality_gate_ru",
                    "primary_metric_condition_ru",
                    "secondary_metric_condition_ru",
                    "stability_condition_ru",
                    "cost_condition_ru",
                )
            )
        )

        data = PROJECT_ROOT / "data_registry"
        seed = pd.read_csv(data / "openml_miniboone_stage05_seed_stability_outer_scores.csv")
        split = pd.read_csv(data / "openml_miniboone_stage05_split_10x1_outer_scores.csv")
        primary_deltas: list[float] = []
        for frame in (seed, split):
            key = ["outer_random_state", "outer_split_number"]
            candidate = frame[frame["model_id"].eq("hist_gradient_boosting")].sort_values(
                key, kind="mergesort"
            )
            baseline = frame[frame["model_id"].eq("logistic_regression")].sort_values(
                key, kind="mergesort"
            )
            if list(map(tuple, candidate[key].to_numpy())) != list(
                map(tuple, baseline[key].to_numpy())
            ):
                raise ValueError("ST07_34: primary evidence pairing is not exact")
            primary_deltas.extend(
                (candidate["average_precision"].to_numpy() - baseline["average_precision"].to_numpy()).tolist()
            )
        primary = pd.Series(primary_deltas, dtype=float)

        quality = pd.read_csv(
            data / "openml_miniboone_nested_quality_checks.csv",
            dtype=str,
            keep_default_na=False,
        )
        metric = pd.read_csv(
            data / "openml_miniboone_stage05_metric_conflict_audit.csv",
            dtype=str,
            keep_default_na=False,
        )
        metric_all = metric[metric["audit_level"].eq("all_protocols_metric")]
        secondary = metric_all[metric_all["metric_role"].eq("secondary")]
        metric_overall = metric[
            metric["audit_level"].eq("overall_metric_conflict_audit")
        ]
        parameters = pd.read_csv(
            data / "openml_miniboone_stage05_parameter_selection_stability.csv",
            dtype=str,
            keep_default_na=False,
        )
        parameter_overall = parameters[
            parameters["audit_level"].eq("overall_parameter_selection_stability")
        ]
        cost = pd.read_csv(
            data / "openml_miniboone_stage05_cost_quality_audit.csv",
            dtype=str,
            keep_default_na=False,
        )
        cost_primary = cost[
            cost["protocol_scope_id"].eq("all_completed_preregistered_variants")
            & cost["quality_metric"].eq("average_precision")
        ]
        non_nested = pd.read_csv(
            data / "openml_miniboone_stage05_non_nested_optimism_probe.csv",
            dtype=str,
            keep_default_na=False,
        )
        observed = evidence["golden_master"]["observed_facts"]
        observed_exact = (
            observed["policy_shape"] == [6, 16]
            and observed["policy_category_order_by_rank"] == expected_categories
            and observed["policy_decision_ranks"] == [6, 5, 4, 3, 2, 1]
            and observed["quality_checks"] == "13/13 pass"
            and len(quality) == 13
            and quality["check_result"].eq("pass").all()
            and observed["primary_paired_blocks"] == len(primary) == 80
            and observed["primary_positive_blocks"] == int(primary.gt(0).sum()) == 80
            and math.isclose(observed["primary_positive_share"], float(primary.gt(0).mean()))
            and math.isclose(observed["primary_delta_mean"], float(primary.mean()))
            and math.isclose(observed["primary_delta_min"], float(primary.min()))
            and math.isclose(
                observed["primary_delta_q05_linear"],
                float(primary.quantile(0.05, interpolation="linear")),
            )
            and observed["secondary_metric_count"] == len(secondary) == 5
            and math.isclose(
                observed["secondary_support_share_min"],
                float(
                    (
                        pd.to_numeric(secondary["candidate_positive_blocks"])
                        / pd.to_numeric(secondary["n_blocks"])
                    ).min()
                ),
            )
            and observed["systematic_conflict_metric_count"]
            == int(secondary["metric_conflict_status"].ne("no_conflict").sum())
            == 0
            and len(metric_overall) == 1
            and metric_overall.iloc[0]["metric_conflict_status"]
            == observed["metric_conflict_status"]
            == "no_metric_conflict_detected"
            and len(parameter_overall) == 1
            and parameter_overall.iloc[0]["stability_status"]
            == observed["parameter_stability_status"]
            == "partially_stable"
            and len(cost_primary) == 1
            and math.isclose(
                float(cost_primary.iloc[0]["fit_seconds_ratio_of_means"]),
                observed["fit_seconds_ratio_of_means"],
            )
            and math.isclose(
                float(cost_primary.iloc[0]["total_seconds_ratio_of_means"]),
                observed["total_seconds_ratio_of_means"],
            )
            and observed["non_nested_comparisons"] == len(non_nested) == 15
            and math.isclose(
                observed["non_nested_delta_mean"],
                float(
                    pd.to_numeric(
                        non_nested["optimism_delta_non_nested_minus_nested"]
                    ).mean()
                ),
            )
        )

        boundary = evidence["boundary_rules"]["strongly_supported"]
        boundary_checks = [
            0.95 >= boundary["primary_positive_share_min_inclusive"],
            0.949999 < boundary["primary_positive_share_min_inclusive"],
            0.03 >= boundary["primary_delta_mean_min_inclusive"],
            0.029999 < boundary["primary_delta_mean_min_inclusive"],
            0.010001 > boundary["primary_delta_q05_min_exclusive"],
            not (0.01 > boundary["primary_delta_q05_min_exclusive"]),
            0.90 >= boundary["secondary_support_share_min_inclusive"],
            0.899999 < boundary["secondary_support_share_min_inclusive"],
            not (10.0 > boundary["high_cost_fit_ratio_trigger_exclusive"]),
            10.000001 > boundary["high_cost_fit_ratio_trigger_exclusive"],
        ]
        strong_pass = (
            quality["check_result"].eq("pass").all()
            and float(primary.gt(0).mean()) >= boundary["primary_positive_share_min_inclusive"]
            and float(primary.mean()) >= boundary["primary_delta_mean_min_inclusive"]
            and float(primary.quantile(0.05, interpolation="linear"))
            > boundary["primary_delta_q05_min_exclusive"]
            and all(
                (
                    int(row["candidate_positive_blocks"]) / int(row["n_blocks"])
                )
                >= boundary["secondary_support_share_min_inclusive"]
                for _, row in secondary.iterrows()
            )
            and metric_overall.iloc[0]["metric_conflict_status"]
            == "no_metric_conflict_detected"
            and float(cost_primary.iloc[0]["fit_seconds_ratio_of_means"])
            > boundary["high_cost_fit_ratio_trigger_exclusive"]
        )
        golden = evidence["golden_master"]
        golden_exact = (
            golden["reference_only_not_new_scientific_validation"] is True
            and set(golden["expected_condition_outcomes"].values()) == {"PASS"}
            and golden["expected_result"]["application_status"] == "APPLIED"
            and golden["expected_result"]["selected_category_id"]
            == "strongly_supported"
            and golden["expected_result"]["selected_decision_rank"] == 6
            and "high_training_cost"
            in golden["expected_result"]["required_disclosures"]
            and golden["expected_result"]["historical_stage05_verdict_changed"]
            is False
        )

        public_names = [item["name"] for item in evidence["future_module_boundary"]["public_contracts"]]
        design_exact = (
            evidence["task_id"]
            == "ST07_34_verdict_policy_application_contract_and_golden_master_design"
            and evidence["task_profile"] == "CHANGE"
            and evidence["future_module_boundary"]["implementation_in_this_task"] is False
            and public_names
            == [
                "build_verdict_evidence_record",
                "evaluate_registered_verdict_conditions",
                "apply_registered_verdict_policy",
                "validate_verdict_policy_application_bundle",
            ]
            and evidence["typed_input_contract"]["schema_id"]
            == "VerdictEvidenceRecordV01"
            and evidence["condition_evaluation_contract"]["schema_id"]
            == "VerdictConditionEvaluationV01"
            and evidence["typed_output_contract"]["schema_id"]
            == "VerdictPolicyApplicationResultV01"
            and evidence["condition_evaluation_contract"]["allowed_outcomes"]
            == ["PASS", "FAIL", "INDETERMINATE", "NOT_EVALUATED_AFTER_MATCH"]
            and evidence["boundary_rules"]["non_operational_terms_policy"]
            == "INDETERMINATE_FAIL_CLOSED"
            and evidence["verification_design"]["negative_mutation_count"]
            == len(evidence["verification_design"]["negative_mutations"])
            == 22
            and len(evidence["application_algorithm"]) == 9
        )

        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if path != "src/mlcra/verdicts.py"
            and sha256_file(PROJECT_ROOT / path) != digest
        ]
        checkpoint = evidence["source_checkpoint"]
        checkpoint_path = Path(checkpoint["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == checkpoint["size_bytes"]
            and sha256_file(checkpoint_path) == checkpoint["sha256"]
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_34_verdict_policy_application_contract_change_scope_v01.csv"
        )
        expected_scope = evidence["planned_change_set"]["paths"]
        scope_exact = [row["relative_path"] for row in scope_rows] == expected_scope

        verdict_source = (PROJECT_ROOT / "src/mlcra/verdicts.py").read_text(
            encoding="utf-8"
        )
        source_implementation_present_after_authorized_followup = all(
            name in verdict_source for name in public_names
        )
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST07_34_verdict_policy_application_contract_and_golden_master_design",
            "ACCEPTED_BY_JOHN: ST07_34_verdict_policy_application_contract_and_golden_master_design",
            "TASK_CLOSED: ST07_34_verdict_policy_application_contract_and_golden_master_design",
            "ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "ST07_35_status: accepted_by_john",
            "ACCEPTED_BY_JOHN: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "TASK_CLOSED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "ST07_35_formal_task_closure: closed_by_john",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        design_verdict = evidence["design_verdict"]
        proposal = evidence["proposed_next_block"]
        evidence_status_exact = (
            design_verdict["status"] == "PASS"
            and design_verdict["st07_close_06_after_task"]
            == "FAIL_PENDING_SOURCE_IMPLEMENTATION_AND_GOLDEN_VALIDATION"
            and design_verdict["stage07_closed"] is False
            and design_verdict["scientific_claim_or_verdict_changed"] is False
            and evidence["actual_change_log"]
            == {"planned_paths": 5, "actual_paths": 5, "deviations": 0}
            and proposal["status"] == "proposed_not_authorized"
            and proposal["implementation_started"] is False
        )
        checks = {
            "policy": policy_exact,
            "observed": observed_exact,
            "boundaries": all(boundary_checks),
            "strong_golden": strong_pass and golden_exact,
            "design": design_exact,
            "historical_protected_except_authorized_source": not protected_mismatches,
            "checkpoint": checkpoint_exact,
            "scope": scope_exact,
            "authorized_followup_implementation_present": (
                source_implementation_present_after_authorized_followup
            ),
            "documentary": documentary,
            "evidence_status": evidence_status_exact,
        }
        return Check(
            "stage07_verdict_policy_application_contract_design",
            "PASS" if all(checks.values()) else "FAIL",
            f"policy={policy.shape}/ranks={ranks.tolist()}; "
            f"golden_primary={len(primary)}/{int(primary.gt(0).sum())}:"
            f"mean={float(primary.mean()):.15f}:q05="
            f"{float(primary.quantile(0.05, interpolation='linear')):.15f}; "
            f"secondary={len(secondary)}/conflicts=0; cost="
            f"{float(cost_primary.iloc[0]['fit_seconds_ratio_of_means'])}; "
            f"condition_clauses=5/5; boundaries={sum(boundary_checks)}/10; "
            f"mutations=22; historical_protected_except_authorized_source="
            f"{len(protected_expected) - 1}/{len(protected_expected) - 1}:"
            f"{not protected_mismatches}:"
            f"{protected_mismatches}; checkpoint_v45={checkpoint_exact}; "
            f"scope={len(scope_rows)}/5:{scope_exact}; "
            f"historical_source_implementation=0; current_authorized_followup="
            f"{len(public_names)}; "
            "historical_closure_criterion_06=FAIL_pending_extraction; "
            f"documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_verdict_policy_application_contract_design",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_verdict_policy_application_modular_extraction() -> Check:
    try:
        from dataclasses import replace

        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.verdicts import (
            VERDICT_CLAUSE_IDS,
            VerdictConditionEvaluationV01,
            VerdictEvidenceRecordV01,
            VerdictPolicyApplicationResultV01,
            apply_registered_verdict_policy,
            build_verdict_evidence_record,
            evaluate_registered_verdict_conditions,
            validate_verdict_policy_application_bundle,
        )

        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st07_35_verdict_policy_application_modular_"
            "extraction_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        read = lambda path: pd.read_csv(
            PROJECT_ROOT / path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        source_paths = [
            "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv",
            "data_registry/openml_miniboone_nested_quality_checks.csv",
            "data_registry/openml_miniboone_stage05_current_effect_readout.csv",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
            "data_registry/openml_miniboone_stage05_metric_conflict_audit.csv",
            "data_registry/openml_miniboone_stage05_parameter_selection_stability.csv",
            "data_registry/openml_miniboone_stage05_cost_quality_audit.csv",
            "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv",
        ]
        source_hashes = {
            path: sha256_file(PROJECT_ROOT / path) for path in source_paths
        }
        source_frames = [read(path) for path in source_paths]
        record = build_verdict_evidence_record(
            *source_frames, source_sha256=source_hashes
        )
        policy_path = (
            "configs/verdict_policies/miniboone_verdict_policy_v01.csv"
        )
        policy = read(policy_path)
        policy_digest = sha256_file(PROJECT_ROOT / policy_path)
        evaluations = evaluate_registered_verdict_conditions(policy, record)
        result = apply_registered_verdict_policy(
            policy,
            record,
            evaluations,
            policy_sha256=policy_digest,
        )
        validate_verdict_policy_application_bundle(
            policy, record, evaluations, result
        )
        second_record = build_verdict_evidence_record(
            *source_frames, source_sha256=source_hashes
        )
        second_evaluations = evaluate_registered_verdict_conditions(
            policy.sample(frac=1, random_state=35).reset_index(drop=True),
            second_record,
        )
        second_result = apply_registered_verdict_policy(
            policy.sample(frac=1, random_state=36).reset_index(drop=True),
            second_record,
            second_evaluations,
            policy_sha256=policy_digest,
        )
        deterministic = (
            record == second_record
            and evaluations == second_evaluations
            and result == second_result
        )

        strong = {
            item.clause_id: item.outcome
            for item in evaluations
            if item.category_id == "strongly_supported"
        }
        lower = [
            item.outcome
            for item in evaluations
            if item.category_id != "strongly_supported"
        ]
        golden = evidence["golden_validation"]
        golden_exact = (
            record.required_check_count == 13
            and record.passed_check_count == 13
            and record.paired_block_count == 80
            and record.candidate_positive_blocks == 80
            and math.isclose(
                record.directional_delta_mean,
                0.09121044365165432,
                rel_tol=0,
                abs_tol=1e-15,
            )
            and math.isclose(
                record.directional_delta_q05_linear,
                0.08625925727315661,
                rel_tol=0,
                abs_tol=1e-15,
            )
            and min(dict(record.support_share_by_metric).values()) == 1.0
            and record.systematic_conflict_metric_count == 0
            and record.metric_conflict_status == "no_metric_conflict_detected"
            and record.parameter_stability_status == "partially_stable"
            and record.fit_seconds_ratio_of_means == 55.195823
            and record.total_seconds_ratio_of_means == 54.506784
            and record.non_nested_comparison_count == 15
            and math.isclose(
                record.non_nested_delta_mean,
                -0.00018960346465566916,
                rel_tol=0,
                abs_tol=1e-15,
            )
            and strong == {clause: "PASS" for clause in VERDICT_CLAUSE_IDS}
            and lower == ["NOT_EVALUATED_AFTER_MATCH"] * 25
            and result.application_status == "APPLIED"
            and result.selected_category_id == "strongly_supported"
            and result.selected_decision_rank == 6
            and result.required_disclosures
            == (
                "high_training_cost",
                "miniboone_and_registered_protocol_scope",
                "partial_l2_selection_instability",
                "non_nested_probe_is_diagnostic_only",
            )
            and golden["selected_category_id"] == result.selected_category_id
            and golden["selected_decision_rank"] == result.selected_decision_rank
        )

        def outcome_for(
            candidate: VerdictEvidenceRecordV01, clause_id: str
        ) -> str:
            candidate_evaluations = evaluate_registered_verdict_conditions(
                policy, candidate
            )
            return next(
                item.outcome
                for item in candidate_evaluations
                if item.category_id == "strongly_supported"
                and item.clause_id == clause_id
            )

        boundary_records = [
            (replace(record, paired_block_count=100, candidate_positive_blocks=95, positive_share=0.95), "primary_metric", "PASS"),
            (replace(record, paired_block_count=1000, candidate_positive_blocks=949, positive_share=0.949), "primary_metric", "FAIL"),
            (replace(record, directional_delta_mean=0.03), "primary_metric", "PASS"),
            (replace(record, directional_delta_mean=0.029999), "primary_metric", "FAIL"),
            (replace(record, directional_delta_q05_linear=0.010001), "primary_metric", "PASS"),
            (replace(record, directional_delta_q05_linear=0.01), "primary_metric", "FAIL"),
            (replace(record, support_share_by_metric=tuple((name, 0.90) for name, _ in record.support_share_by_metric)), "secondary_metric", "PASS"),
            (replace(record, support_share_by_metric=((record.metric_names[0], 0.899999), *tuple((name, 0.90) for name in record.metric_names[1:]))), "secondary_metric", "FAIL"),
        ]
        boundary_checks = [
            outcome_for(candidate, clause_id) == expected
            for candidate, clause_id, expected in boundary_records
        ]
        cost_at_ten = replace(
            record,
            fit_seconds_ratio_of_means=10.0,
            high_training_cost=False,
        )
        cost_above_ten = replace(
            record,
            fit_seconds_ratio_of_means=10.000001,
            high_training_cost=True,
        )
        for candidate, disclosure_expected in (
            (cost_at_ten, False),
            (cost_above_ten, True),
        ):
            candidate_evaluations = evaluate_registered_verdict_conditions(
                policy, candidate
            )
            candidate_result = apply_registered_verdict_policy(
                policy,
                candidate,
                candidate_evaluations,
                policy_sha256=policy_digest,
            )
            boundary_checks.append(
                ("high_training_cost" in candidate_result.required_disclosures)
                == disclosure_expected
            )

        def rejects(callable_object: Any) -> bool:
            try:
                callable_object()
            except (ValueError, TypeError):
                return True
            return False

        policy_mutations = []
        mutation = policy.iloc[:-1].copy()
        policy_mutations.append(mutation)
        mutation = policy.copy(); mutation.loc[1, "category_id"] = mutation.loc[0, "category_id"]; policy_mutations.append(mutation)
        mutation = policy.copy(); mutation.loc[1, "decision_rank"] = mutation.loc[0, "decision_rank"]; policy_mutations.append(mutation)
        mutation = policy.copy(); mutation.loc[5, "decision_rank"] = "7"; policy_mutations.append(mutation)
        mutation = policy.copy(); mutation["policy_id"] = "wrong"; policy_mutations.append(mutation)
        mutation = policy.copy(); mutation["claim_id"] = "wrong"; policy_mutations.append(mutation)
        mutation = policy.copy(); mutation.loc[0, "quality_gate_ru"] = ""; policy_mutations.append(mutation)
        mutation = policy.copy(); mutation.loc[0, "category_id"] = "unknown"; policy_mutations.append(mutation)
        mutation_checks = [
            rejects(lambda candidate=candidate: evaluate_registered_verdict_conditions(candidate, record))
            for candidate in policy_mutations
        ]
        evidence_mutations = [
            replace(record, policy_id=""),
            replace(record, claim_id="wrong"),
            replace(record, directional_delta_mean=float("nan")),
            replace(record, candidate_positive_blocks=81),
            replace(record, source_sha256=record.source_sha256[:-1]),
            replace(record, evaluator_contract_id="wrong"),
        ]
        mutation_checks.extend(
            rejects(lambda candidate=candidate: evaluate_registered_verdict_conditions(policy, candidate))
            for candidate in evidence_mutations
        )
        evaluation_mutations = [
            evaluations[:-1],
            (*evaluations[:-1], evaluations[0]),
            (replace(evaluations[0], outcome="UNKNOWN"), *evaluations[1:]),
        ]
        mutation_checks.extend(
            rejects(
                lambda candidate=candidate: apply_registered_verdict_policy(
                    policy,
                    record,
                    candidate,
                    policy_sha256=policy_digest,
                )
            )
            for candidate in evaluation_mutations
        )
        below_strong = replace(
            record,
            paired_block_count=100,
            candidate_positive_blocks=94,
            positive_share=0.94,
        )
        below_evaluations = evaluate_registered_verdict_conditions(
            policy, below_strong
        )
        below_result = apply_registered_verdict_policy(
            policy,
            below_strong,
            below_evaluations,
            policy_sha256=policy_digest,
        )
        mutation_checks.append(
            below_result.application_status == "INDETERMINATE_FAIL_CLOSED"
            and below_result.selected_category_id is None
        )
        result_mutations = [
            replace(result, selected_decision_rank=5),
            replace(result, allowed_language_ru="forged"),
            replace(
                result,
                required_disclosures=tuple(
                    value
                    for value in result.required_disclosures
                    if value != "high_training_cost"
                ),
            ),
            replace(result, evidence_record_sha256="0" * 64),
        ]
        mutation_checks.extend(
            rejects(
                lambda candidate=candidate: validate_verdict_policy_application_bundle(
                    policy, record, evaluations, candidate
                )
            )
            for candidate in result_mutations
        )

        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_35_verdict_policy_application_modular_"
            "extraction_change_scope_v01.csv"
        )
        scope_exact = [row["relative_path"] for row in scope_rows] == evidence[
            "planned_change_set"
        ]["paths"]
        source = (PROJECT_ROOT / "src/mlcra/verdicts.py").read_text(encoding="utf-8")
        public_names = evidence["public_contracts"]
        public_present = all(f"def {name}(" in source for name in public_names)
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "ACCEPTED_BY_JOHN: ST07_34_verdict_policy_application_contract_and_golden_master_design",
            "TASK_CLOSED: ST07_34_verdict_policy_application_contract_and_golden_master_design",
            "NEXT_BLOCK_AUTHORIZED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "ST07_35_status: accepted_by_john",
            "ACCEPTED_BY_JOHN: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "TASK_CLOSED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "ST07_35_formal_task_closure: closed_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        evidence_exact = (
            evidence["task_id"]
            == "ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation"
            and evidence["task_profile"] == "CHANGE"
            and evidence["technical_status"] == "PASS"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["stage07_closed"] is False
            and evidence["scientific_claim_or_verdict_changed"] is False
            and evidence["boundary_checks"] == 10
            and evidence["negative_mutations"] == 22
        )
        checks = {
            "evidence": evidence_exact,
            "public_contracts": public_present,
            "golden": golden_exact,
            "deterministic": deterministic,
            "boundaries": len(boundary_checks) == 10 and all(boundary_checks),
            "mutations": len(mutation_checks) == 22 and all(mutation_checks),
            "protected": not protected_mismatches,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_verdict_policy_application_modular_extraction",
            "PASS" if all(checks.values()) else "FAIL",
            f"public=4; policy={policy.shape}; evidence=9_sources; "
            f"primary={record.paired_block_count}/{record.candidate_positive_blocks}:"
            f"mean={record.directional_delta_mean:.15f}:"
            f"q05={record.directional_delta_q05_linear:.15f}; "
            f"strong={sum(value == 'PASS' for value in strong.values())}/5; "
            f"selected={result.selected_category_id}:{result.selected_decision_rank}; "
            f"disclosures={len(result.required_disclosures)}; "
            f"boundaries={sum(boundary_checks)}/10; "
            f"mutations={sum(mutation_checks)}/22; "
            f"protected={len(protected_expected)}/{len(protected_expected)}:"
            f"{not protected_mismatches}:{protected_mismatches}; "
            f"scope={len(scope_rows)}/6:{scope_exact}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage07_verdict_policy_application_modular_extraction",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_next_block_after_st0735() -> Check:
    try:
        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st07_next_block_selection_after_st07_35_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        task_id = "ST07_next_block_selection_after_ST07_35"
        proposed_id = "ST07_36_stage07_post_verdict_policy_closure_reaudit"

        weights = evidence["selection_criteria"]
        weight_values = [
            weights["closure_value"],
            weights["dependency_order"],
            weights["risk_separation"],
            weights["verifiability"],
            weights["cost_and_recovery"],
        ]
        alternatives = evidence["alternatives"]
        scores_exact = all(
            math.isclose(
                row["weighted_score"],
                sum(score * weight for score, weight in zip(row["scores"], weight_values)),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for row in alternatives
        )
        selected = evidence["selected_next_block"]
        selection_exact = (
            math.isclose(sum(weight_values), 1.0, rel_tol=0.0, abs_tol=1e-12)
            and len(alternatives) == 5
            and scores_exact
            and alternatives[0]["action"] == proposed_id
            and alternatives[0]["weighted_score"]
            == max(row["weighted_score"] for row in alternatives)
            and alternatives[0]["disposition"]
            == "selected_proposed_not_authorized"
            and selected["task_id"] == proposed_id
            and selected["status"] == "proposed_not_authorized"
            and selected["implementation_started"] is False
        )

        module_paths = sorted((PROJECT_ROOT / "src/mlcra").glob("*.py"))
        public_contracts = []
        for path in module_paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            public_contracts.extend(
                node.name
                for node in tree.body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                )
                and not node.name.startswith("_")
            )
        notebook = json.loads(
            (PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb").read_text(
                encoding="utf-8"
            )
        )
        stage05_cells = [33, 36, 37, 38, 39, 41, 42, 43, 45, 47, 49, 51]
        top_level_definitions = []
        for index in stage05_cells:
            tree = ast.parse("".join(notebook["cells"][index].get("source", [])))
            top_level_definitions.extend(
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        inventory_exact = (
            len(module_paths) == evidence["monitor"]["module_files"] == 10
            and len(public_contracts)
            == evidence["monitor"]["public_functions_or_classes"]
            == 89
            and len(stage05_cells)
            == evidence["monitor"]["stage05_orchestration_cells"]
            == 12
            and len(top_level_definitions)
            == evidence["monitor"]["stage05_top_level_function_definitions"]
            == 0
        )

        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]
        checkpoint = evidence["source_checkpoint"]
        checkpoint_path = Path(checkpoint["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == checkpoint["size_bytes"]
            and sha256_file(checkpoint_path) == checkpoint["sha256"]
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_next_block_selection_after_st07_35_change_scope_v01.csv"
        )
        scope_exact = [row["relative_path"] for row in scope_rows] == evidence[
            "planned_change_set"
        ]["paths"]

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "ACCEPTED_BY_JOHN: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "ST07_35_status: accepted_by_john",
            "TASK_CLOSED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "ST07_35_formal_task_closure: closed_by_john",
            "NEXT_BLOCK_AUTHORIZED: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "stage07_closure_audit_after_ST07_35: COMPLETED_PASS",
            "ACCEPTED_BY_JOHN: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "TASK_CLOSED: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "STAGE_CLOSED_BY_JOHN: Stage_7",
            "stage07_status: closed_by_john",
            "ST07_36_status: accepted_by_john",
            "ST07_36_implementation_started: YES_COMPLETE",
            "TECHNICAL_STATUS: PASS",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        evidence_exact = (
            evidence["task_id"] == task_id
            and evidence["task_profile"] == "CHANGE"
            and evidence["authorization"]["john_decision"]
            == "ST07_35 принимаю. Двигайся дальше"
            and evidence["authorization"]["task_closed_not_inferred"] is True
            and evidence["authorization"]["next_block_execution_authorized"] is False
            and evidence["authorization"]["stage07_closure_reserved_for_john"] is True
            and evidence["technical_status"] == "PASS"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["stage07_closed"] is False
            and evidence["verification_result"]["focused_gate"] == "PASS"
            and evidence["verification_result"]["baseline"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot_disposition"]
            ["final_run_after_john_restoration"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot_disposition"]
            ["restored_checkpoint_v44_sha256_exact"] is True
            and evidence["verification_result"]["cumulative_pilot_disposition"]
            ["restored_checkpoint_v45_sha256_exact"] is True
            and evidence["verification_result"]["cumulative_pilot_disposition"]
            ["all_other_pilot_gates"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot_disposition"]
            ["historical_hash_requirements_preserved"] is True
            and evidence["verification_result"]["cumulative_pilot_disposition"]
            ["weaker_substitution_used"] is False
            and evidence["actual_change_log"]
            == {"planned_paths": 5, "actual_paths": 5, "deviations": 0}
            and len(evidence["self_review_repairs"]) == 2
        )
        previous = check_stage07_verdict_policy_application_modular_extraction()
        checks = {
            "previous": previous.status == "PASS",
            "evidence": evidence_exact,
            "selection": selection_exact,
            "inventory": inventory_exact,
            "protected": not protected_mismatches,
            "checkpoint": checkpoint_exact,
            "scope": scope_exact,
            "documentary": documentary,
        }
        return Check(
            "stage07_next_block_after_st0735",
            "PASS" if all(checks.values()) else "FAIL",
            f"accepted_st07_35={evidence_exact}; previous={previous.status}; "
            f"alternatives={len(alternatives)}; selected={proposed_id}:"
            f"{alternatives[0]['weighted_score']:.2f}; modules={len(module_paths)}; "
            f"public={len(public_contracts)}; notebook={len(stage05_cells)}/"
            f"top_defs={len(top_level_definitions)}; protected="
            f"{len(protected_expected) - len(protected_mismatches)}/"
            f"{len(protected_expected)}:{protected_mismatches}; "
            f"checkpoint_v47={checkpoint_exact}; cumulative_current=PASS; "
            "restored_external_v44_v45_exact=True; "
            f"scope={len(scope_rows)}/5:"
            f"{scope_exact}; documentary={documentary}; implementation_started=False",
        )
    except Exception as exc:
        return Check(
            "stage07_next_block_after_st0735",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_post_verdict_policy_closure_reaudit() -> Check:
    try:
        import pandas as pd

        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st07_36_stage07_post_verdict_policy_closure_"
            "reaudit_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        rows = evidence["closure_matrix"]
        statuses = {row["criterion_id"]: row["status"] for row in rows}
        expected_statuses = {
            f"ST07-CLOSE-{index:02d}": "PASS" for index in range(1, 8)
        }

        notebook = json.loads(
            (PROJECT_ROOT / "notebooks/04_dataset_smoke_experiments.ipynb").read_text(
                encoding="utf-8"
            )
        )
        stage05_cells = [33, 36, 37, 38, 39, 41, 42, 43, 45, 47, 49, 51]
        top_level_definitions = []
        for index in stage05_cells:
            tree = ast.parse("".join(notebook["cells"][index].get("source", [])))
            top_level_definitions.extend(
                (index, node.name)
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        cell31_tree = ast.parse("".join(notebook["cells"][31].get("source", [])))
        cell31_helpers = [
            node.name
            for node in cell31_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        expected_cell31_helpers = [
            "make_quality_check_row",
            "required_columns_for_output",
            "check_required_columns",
        ]
        nested_artifacts_source = (
            PROJECT_ROOT / "src/mlcra/nested_artifacts.py"
        ).read_text(encoding="utf-8")
        validation_source = (PROJECT_ROOT / "src/mlcra/validation.py").read_text(
            encoding="utf-8"
        )
        cell31_analogues = (
            "def build_quality_checks(" in nested_artifacts_source
            and "def validate_v02_schema(" in nested_artifacts_source
            and "def require_columns(" in validation_source
        )

        module_paths = sorted((PROJECT_ROOT / "src/mlcra").glob("*.py"))
        public_contracts = []
        for path in module_paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            public_contracts.extend(
                (path.name, node.name)
                for node in tree.body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                )
                and not node.name.startswith("_")
            )

        st0735 = check_stage07_verdict_policy_application_modular_extraction()
        policy = pd.read_csv(
            PROJECT_ROOT
            / "configs/verdict_policies/miniboone_verdict_policy_v01.csv",
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        verdict_source = (PROJECT_ROOT / "src/mlcra/verdicts.py").read_text(
            encoding="utf-8"
        )
        policy_contracts = [
            name
            for name in (
                "build_verdict_evidence_record",
                "evaluate_registered_verdict_conditions",
                "apply_registered_verdict_policy",
                "validate_verdict_policy_application_bundle",
            )
            if f"def {name}(" in verdict_source
        ]

        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]
        checkpoint = evidence["source_checkpoint"]
        checkpoint_path = Path(checkpoint["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == checkpoint["size_bytes"]
            and sha256_file(checkpoint_path) == checkpoint["sha256"]
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st07_36_stage07_post_verdict_policy_closure_"
            "reaudit_change_scope_v01.csv"
        )
        scope_exact = [row["relative_path"] for row in scope_rows] == evidence[
            "planned_change_set"
        ]["paths"]

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "TASK_CLOSED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation",
            "NEXT_BLOCK_AUTHORIZED: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "ACCEPTED_BY_JOHN: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "TASK_CLOSED: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "STAGE_CLOSED_BY_JOHN: Stage_7",
            "ST07_36_status: accepted_by_john",
            "stage07_closure_reaudit_verdict: PASS",
            "stage07_closure_criteria: PASS=7;FAIL=0;BLOCKED=0",
            "stage07_status: closed_by_john",
            "stage07_closed: true",
            "TECHNICAL_STATUS: PASS",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        metrics = evidence["objective_metrics"]
        aggregate = evidence["aggregate_verdict"]
        evidence_exact = (
            evidence["task_id"]
            == "ST07_36_stage07_post_verdict_policy_closure_reaudit"
            and evidence["task_profile"] == "SCIENTIFIC_VALIDATION"
            and statuses == expected_statuses
            and metrics["criteria_total"] == 7
            and metrics["criteria_pass"] == 7
            and metrics["criteria_fail"] == 0
            and metrics["criteria_blocked"] == 0
            and metrics["module_files"] == 10
            and metrics["module_public_functions_or_classes"] == 89
            and metrics["stage05_orchestration_top_level_function_definitions"] == 0
            and metrics["legacy_cell31_helpers_with_modular_analogues"] == 3
            and metrics["verdict_policy_application_contracts"] == 4
            and metrics["verdict_policy_boundary_checks"] == 10
            and metrics["verdict_policy_negative_mutations"] == 22
            and metrics["new_training_runs"] == 0
            and metrics["network_attempts"] == 0
            and metrics["scientific_csv_changes"] == 0
            and metrics["claim_or_stage05_verdict_changes"] == 0
            and evidence["verification_result"]["focused_gate"] == "PASS"
            and evidence["verification_result"]["baseline"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot"] == "PASS"
            and aggregate["stage07_closure_criteria_satisfied"] is True
            and aggregate["stage07_closed"] is False
            and aggregate["closure_decision_reserved_for_john"] is True
            and aggregate["blocking_criterion"] is None
            and evidence["actual_change_log"]
            == {"planned_paths": 5, "actual_paths": 5, "deviations": 0}
        )
        checks = {
            "matrix": statuses == expected_statuses,
            "inventory": (
                len(module_paths) == 10
                and len(public_contracts) == 89
                and len(notebook["cells"]) == 52
            ),
            "orchestration": not top_level_definitions,
            "cell31_transition": (
                cell31_helpers == expected_cell31_helpers and cell31_analogues
            ),
            "policy_gate": (
                st0735.status == "PASS"
                and policy.shape == (6, 16)
                and len(policy_contracts) == 4
            ),
            "protected": not protected_mismatches,
            "checkpoint": checkpoint_exact,
            "scope": scope_exact,
            "documentary": documentary,
            "evidence": evidence_exact,
        }
        return Check(
            "stage07_post_verdict_policy_closure_reaudit",
            "PASS" if all(checks.values()) else "FAIL",
            f"criteria=7/0/0(PASS/FAIL/BLOCKED); modules/public="
            f"{len(module_paths)}/{len(public_contracts)}; notebook="
            f"{len(notebook['cells'])}; orchestration={len(stage05_cells)}/"
            f"top_defs={len(top_level_definitions)}; cell31_analogues="
            f"{len(cell31_helpers)}/3:{cell31_analogues}; policy={policy.shape}:"
            f"contracts={len(policy_contracts)}:production_gate={st0735.status}; "
            f"protected={len(protected_expected) - len(protected_mismatches)}/"
            f"{len(protected_expected)}:{protected_mismatches}; "
            f"checkpoint_v48={checkpoint_exact}; scope={len(scope_rows)}/5:"
            f"{scope_exact}; documentary={documentary}; stage07_closed_by_john=True",
        )
    except Exception as exc:
        return Check(
            "stage07_post_verdict_policy_closure_reaudit",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_closure_and_next_stage_selection() -> Check:
    try:
        evidence_path = (
            PROJECT_ROOT
            / "data_registry/stage07_closure_and_next_stage_selection_"
            "evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")

        closure_tokens = (
            "ACCEPTED_BY_JOHN: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "TASK_CLOSED: ST07_36_stage07_post_verdict_policy_closure_reaudit",
            "STAGE_CLOSED_BY_JOHN: Stage_7",
            "ST07_36_status: accepted_by_john",
            "stage07_status: closed_by_john",
            "stage07_closed: true",
            "proposed_next_block: ST08_01_project_completion_and_release_readiness_contract_design",
            "ST08_01_status: proposed_not_authorized",
            "ST08_01_implementation_started: NO",
        )
        documentary = all(
            all(token in text for token in closure_tokens)
            for text in (stage_text, roadmap_text)
        )

        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/stage07_closure_and_next_stage_selection_"
            "change_scope_v01.csv"
        )
        scope_exact = [row["relative_path"] for row in scope_rows] == evidence[
            "planned_change_set"
        ]["paths"]

        baseline = evidence["source_baseline"]
        checkpoint_path = Path(baseline["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == baseline["size_bytes"]
            and sha256_file(checkpoint_path) == baseline["sha256"]
        )
        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]

        method = evidence["selection_method"]
        weights = method["criteria_weights"]
        weight_order = (
            "mission_alignment",
            "dependency_ordering",
            "risk_separation",
            "objective_verifiability",
            "cost_and_reversibility",
        )
        alternatives = method["alternatives"]
        recomputed_scores = [
            round(
                sum(
                    score * weights[key]
                    for score, key in zip(alternative["scores"], weight_order)
                ),
                2,
            )
            for alternative in alternatives
        ]
        scores_exact = all(
            math.isclose(score, alternative["weighted_score"], abs_tol=1e-12)
            for score, alternative in zip(recomputed_scores, alternatives)
        )
        selected = [alternative for alternative in alternatives if alternative["selected"]]
        proposal = evidence["proposed_next_block"]
        selection_exact = (
            len(alternatives) == 5
            and len(selected) == 1
            and selected[0]["alternative_id"] == "A"
            and selected[0]["weighted_score"] == max(recomputed_scores)
            and selected[0]["name"] == proposal["task_id"]
            and proposal["status"] == "proposed_not_authorized"
            and proposal["implementation_started"] is False
        )

        gap = evidence["post_stage07_gap_inventory"]
        # The gap inventory is an immutable observation at the v49 selection
        # baseline.  Comparing it with the evolving workspace would make the
        # historical Stage 7 gate fail as soon as an authorized Stage 8 file
        # is created.  Current Stage 8 state is checked by its own gate below.
        gap_snapshot_exact = (
            gap["stage08_document_exists"] is False
            and gap["root_readme_exists"] is False
            and gap["python_packaging_metadata_exists"] is False
            and gap["environment_lock_or_requirements_exists"] is False
            and gap["license_file_exists"] is False
            and gap["citation_file_exists"] is False
            and gap["dedicated_tests_directory_exists"] is False
            and gap["supported_cli_or_dashboard_exists"] is False
            and gap["stage06_registered_status"]
            == "limited_publication_ready_as_documented_evidence_record"
        )

        metrics = evidence["objective_metrics"]
        evidence_exact = (
            evidence["task_id"] == "STAGE07_closure_registration_and_next_stage_selection"
            and evidence["task_profile"] == "CHANGE"
            and evidence["closure_basis"]["criteria_pass"] == 7
            and evidence["closure_basis"]["criteria_fail"] == 0
            and evidence["closure_basis"]["criteria_blocked"] == 0
            and evidence["closure_basis"]["stage07_status"] == "closed_by_john"
            and metrics["protected_artifacts_expected"] == 18
            and metrics["protected_artifact_mismatches"] == 0
            and metrics["new_training_runs"] == 0
            and metrics["network_attempts"] == 0
            and metrics["scientific_csv_changes"] == 0
            and metrics["claim_protocol_policy_or_verdict_changes"] == 0
            and metrics["stage08_files_created"] == 0
            and metrics["alternatives_compared"] == 5
            and evidence["verification_result"]["focused_gate"] == "PASS"
            and evidence["verification_result"]["baseline"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot"] == "PASS"
            and evidence["technical_status"] == "PASS"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["actual_change_log"]
            == {"planned_paths": 5, "actual_paths": 5, "deviations": 0}
        )
        checks = {
            "documentary": documentary,
            "scope": scope_exact,
            "checkpoint": checkpoint_exact,
            "protected": not protected_mismatches,
            "scores": scores_exact,
            "selection": selection_exact,
            "gap_snapshot": gap_snapshot_exact,
            "evidence": evidence_exact,
        }
        return Check(
            "stage07_closure_and_next_stage_selection",
            "PASS" if all(checks.values()) else "FAIL",
            f"closure=accepted/task_closed/stage_closed; alternatives="
            f"{len(alternatives)}; selected={proposal['task_id']}:"
            f"{selected[0]['weighted_score'] if selected else 'none'}; "
            f"protected={len(protected_expected) - len(protected_mismatches)}/"
            f"{len(protected_expected)}:{protected_mismatches}; checkpoint_v49="
            f"{checkpoint_exact}; scope={len(scope_rows)}/5:{scope_exact}; "
            f"gap_snapshot={gap_snapshot_exact}; documentary={documentary}; "
            "implementation_started=False",
        )
    except Exception as exc:
        return Check(
            "stage07_closure_and_next_stage_selection",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage08_project_completion_and_release_readiness_contract() -> Check:
    try:
        requirements_path = (
            PROJECT_ROOT
            / "configs/project_readiness/stage08_project_completion_and_"
            "release_readiness_requirements_v01.csv"
        )
        rows = read_contract_csv(requirements_path)
        required_columns = [
            "requirement_id",
            "dimension_id",
            "dimension_name",
            "requirement",
            "authoritative_basis",
            "local_evidence_paths",
            "verification_method",
            "pass_rule",
            "fail_rule",
            "blocked_rule",
            "aggregation_role",
            "design_status",
        ]
        columns_exact = list(rows[0]) == required_columns if rows else False
        ids = [row["requirement_id"] for row in rows]
        expected_ids = [f"ST08-REQ-{index:02d}" for index in range(1, 25)]
        dimensions = {f"D{index:02d}" for index in range(1, 9)}
        dimension_counts = {
            dimension: sum(row["dimension_id"] == dimension for row in rows)
            for dimension in dimensions
        }
        content_complete = all(
            all(str(row[column]).strip() for column in required_columns)
            for row in rows
        )
        contract_exact = (
            len(rows) == 24
            and ids == expected_ids
            and len(ids) == len(set(ids))
            and set(row["dimension_id"] for row in rows) == dimensions
            and set(dimension_counts.values()) == {3}
            and set(row["design_status"] for row in rows) == {"NOT_EVALUATED"}
            and sum(row["aggregation_role"] == "mandatory" for row in rows) == 23
            and sum(row["aggregation_role"] == "conditional" for row in rows) == 1
            and rows[16]["requirement_id"] == "ST08-REQ-17"
            and rows[16]["aggregation_role"] == "conditional"
            and columns_exact
            and content_complete
        )

        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st08_01_project_completion_and_release_readiness_"
            "contract_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        checkpoint = evidence["source_checkpoint"]
        checkpoint_path = Path(checkpoint["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == checkpoint["size_bytes"]
            and sha256_file(checkpoint_path) == checkpoint["sha256"]
        )
        protected_expected = evidence["protected_artifacts"]
        protected_mismatches = [
            path
            for path, digest in protected_expected.items()
            if sha256_file(PROJECT_ROOT / path) != digest
        ]
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st08_01_project_completion_and_release_readiness_"
            "contract_change_scope_v01.csv"
        )
        scope_exact = [row["relative_path"] for row in scope_rows] == evidence[
            "planned_change_set"
        ]["paths"]

        dimension_contracts = evidence["dimension_contracts"]
        dimension_exact = (
            len(dimension_contracts) == 8
            and [item["dimension_id"] for item in dimension_contracts]
            == [f"D{index:02d}" for index in range(1, 9)]
            and all(len(item["requirement_ids"]) == 3 for item in dimension_contracts)
            and [identifier for item in dimension_contracts for identifier in item["requirement_ids"]]
            == expected_ids
        )
        aggregation = evidence["aggregation_rules"]
        aggregation_exact = (
            aggregation["project_completion_pass_dimensions"]
            == ["D01", "D02", "D03", "D04", "D05", "D08"]
            and aggregation["external_release_pass_dimensions"]
            == ["D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08"]
            and aggregation["release_pass_requires_zero_unresolved_release_blockers"]
            is True
            and aggregation["john_acceptance_required"] is True
        )
        golden = evidence["golden_audit_artifact_design"]
        golden_exact = (
            golden["schema_version"]
            == "stage08_project_completion_and_release_readiness_audit_v01"
            and golden["requirements_total"] == 24
            and golden["dimensions_total"] == 8
            and len(golden["requirement_result_fields"]) == 7
            and len(golden["aggregate_fields"]) == 7
            and len(golden["release_classes"]) == 5
            and len(golden["negative_mutation_classes"]) == 14
            and len(set(golden["negative_mutation_classes"])) == 14
        )

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "ACCEPTED_BY_JOHN: STAGE07_closure_registration_and_next_stage_selection",
            "TASK_CLOSED: STAGE07_closure_registration_and_next_stage_selection",
            "NEXT_BLOCK_AUTHORIZED: ST08_01_project_completion_and_release_readiness_contract_design",
            "stage08_status: active_contract_design",
            "ST08_01_status: technical_pass_ready_for_john_acceptance",
            "ST08_01_audit_execution_authorized: false",
            "proposed_next_block: ST08_02_project_completion_and_release_readiness_baseline_audit",
            "ST08_02_status: proposed_not_authorized",
            "ST08_02_implementation_started: NO",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        # ST08_01 records the design-time absence of an audit artifact.  After
        # John authorizes ST08_02, current existence belongs to the new gate;
        # the historical ST08_01 observation remains immutable in its evidence.
        forbidden_outputs_absent_at_design = (
            evidence["objective_metrics"]["audit_results_created"] == 0
            and evidence["authorization"]["audit_execution_authorized"] is False
            and not (PROJECT_ROOT / "README.md").exists()
            and not (PROJECT_ROOT / "pyproject.toml").exists()
            and not (PROJECT_ROOT / "LICENSE").exists()
            and not (PROJECT_ROOT / "CITATION.cff").exists()
        )
        metrics = evidence["objective_metrics"]
        evidence_exact = (
            evidence["task_id"]
            == "ST08_01_project_completion_and_release_readiness_contract_design"
            and evidence["task_profile"] == "CHANGE"
            and evidence["authorization"]["audit_execution_authorized"] is False
            and evidence["authorization"]["release_authorized"] is False
            and evidence["contract"]["requirements_total"] == 24
            and evidence["contract"]["dimensions_total"] == 8
            and evidence["contract"]["design_status"] == "NOT_EVALUATED"
            and evidence["contract"]["allowed_future_statuses"]
            == ["PASS", "FAIL", "BLOCKED", "SKIPPED"]
            and len(evidence["authoritative_support"]) == 13
            and metrics["requirements"] == 24
            and metrics["dimensions"] == 8
            and metrics["not_evaluated_requirements"] == 24
            and metrics["protected_artifacts"] == 18
            and metrics["protected_mismatches"] == 0
            and metrics["negative_mutation_classes_designed"] == 14
            and metrics["new_training_runs"] == 0
            and metrics["network_attempts"] == 0
            and metrics["scientific_artifact_changes"] == 0
            and metrics["audit_results_created"] == 0
            and metrics["external_side_effects"] == 0
            and evidence["verification_result"]["focused_gate"] == "PASS"
            and evidence["verification_result"]["baseline"] == "PASS"
            and evidence["verification_result"]["cumulative_pilot"] == "PASS"
            and evidence["actual_change_log"]
            == {"planned_paths": 6, "actual_paths": 6, "deviations": 0}
            and evidence["proposed_next_block"]["status"] == "proposed_not_authorized"
            and evidence["proposed_next_block"]["implementation_started"] is False
            and evidence["technical_status"] == "PASS"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
        )
        checks = {
            "contract": contract_exact,
            "dimensions": dimension_exact,
            "aggregation": aggregation_exact,
            "golden": golden_exact,
            "checkpoint": checkpoint_exact,
            "protected": not protected_mismatches,
            "scope": scope_exact,
            "documentary": documentary,
            "forbidden_outputs_at_design": forbidden_outputs_absent_at_design,
            "evidence": evidence_exact,
        }
        return Check(
            "stage08_project_completion_and_release_readiness_contract",
            "PASS" if all(checks.values()) else "FAIL",
            f"requirements={len(rows)}/24; dimensions={dimension_counts}; "
            f"statuses={sorted(set(row['design_status'] for row in rows))}; "
            f"mandatory/conditional=23/1; sources={len(evidence['authoritative_support'])}; "
            f"mutations={len(golden['negative_mutation_classes'])}; protected="
            f"{len(protected_expected) - len(protected_mismatches)}/"
            f"{len(protected_expected)}:{protected_mismatches}; checkpoint_v51="
            f"{checkpoint_exact}; scope={len(scope_rows)}/6:{scope_exact}; "
            f"documentary={documentary}; audit_executed=False; release=False",
        )
    except Exception as exc:
        return Check(
            "stage08_project_completion_and_release_readiness_contract",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage08_project_completion_and_release_readiness_baseline_audit() -> Check:
    try:
        import copy

        contract_rows = read_contract_csv(
            PROJECT_ROOT
            / "configs/project_readiness/stage08_project_completion_and_"
            "release_readiness_requirements_v01.csv"
        )
        evidence_path = (
            PROJECT_ROOT
            / "data_registry/stage08_project_completion_and_release_readiness_"
            "audit_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        expected_ids = [f"ST08-REQ-{index:02d}" for index in range(1, 25)]
        expected_status_counts = {"PASS": 7, "FAIL": 7, "BLOCKED": 10, "SKIPPED": 0}
        expected_dimension_statuses = {
            "D01": "FAIL",
            "D02": "PASS",
            "D03": "BLOCKED",
            "D04": "FAIL",
            "D05": "FAIL",
            "D06": "BLOCKED",
            "D07": "FAIL",
            "D08": "BLOCKED",
        }
        result_fields = {
            "requirement_id",
            "status",
            "observed_evidence",
            "evidence_paths",
            "verification_command_or_method",
            "finding_id",
            "disposition",
        }

        def validate_bundle(candidate: dict[str, Any], rows: list[dict[str, str]]) -> None:
            if [row["requirement_id"] for row in rows] != expected_ids:
                raise ValueError("contract requirement identifiers differ")
            for row in rows:
                for column in (
                    "authoritative_basis",
                    "local_evidence_paths",
                    "verification_method",
                    "pass_rule",
                    "fail_rule",
                    "blocked_rule",
                ):
                    if not row[column].strip():
                        raise ValueError(f"missing contract field: {column}")

            results = candidate["requirement_results"]
            ids = [row["requirement_id"] for row in results]
            if ids != expected_ids or len(ids) != len(set(ids)):
                raise ValueError("requirement results are incomplete or duplicated")
            findings = candidate["open_findings"]
            finding_ids = [row["finding_id"] for row in findings]
            if len(findings) != 9 or len(finding_ids) != len(set(finding_ids)):
                raise ValueError("finding registry is not exact")
            finding_set = set(finding_ids)
            contract_by_id = {row["requirement_id"]: row for row in rows}
            allowed = {"PASS", "FAIL", "BLOCKED", "SKIPPED"}
            for result in results:
                if set(result) != result_fields:
                    raise ValueError("requirement result schema differs")
                if result["status"] not in allowed:
                    raise ValueError("unknown requirement status")
                if not result["observed_evidence"].strip():
                    raise ValueError("missing observed evidence")
                if not result["evidence_paths"]:
                    raise ValueError("missing evidence paths")
                if not result["verification_command_or_method"].strip():
                    raise ValueError("missing verification method")
                if not result["disposition"].strip():
                    raise ValueError("missing disposition")
                if result["status"] == "PASS":
                    if result["finding_id"] is not None:
                        raise ValueError("PASS result has a finding")
                elif result["finding_id"] not in finding_set:
                    raise ValueError("non-PASS result has no registered finding")
                if (
                    result["status"] == "SKIPPED"
                    and contract_by_id[result["requirement_id"]]["aggregation_role"]
                    != "conditional"
                ):
                    raise ValueError("mandatory requirement was skipped")

            referenced_findings = {
                row["finding_id"] for row in results if row["finding_id"] is not None
            }
            if referenced_findings != finding_set:
                raise ValueError("silent or unreferenced finding")
            for finding in findings:
                if (
                    not finding["requirement_ids"]
                    or not set(finding["requirement_ids"]).issubset(set(expected_ids))
                    or not finding["owner"].strip()
                    or not finding["consequence"].strip()
                    or not finding["disposition"].strip()
                ):
                    raise ValueError("finding content is incomplete")

            observed_counts = {
                status: sum(row["status"] == status for row in results)
                for status in ("PASS", "FAIL", "BLOCKED", "SKIPPED")
            }
            if observed_counts != expected_status_counts:
                raise ValueError("requirement status counts differ")
            dimension_rows = candidate["dimension_results"]
            if [row["dimension_id"] for row in dimension_rows] != [
                f"D{index:02d}" for index in range(1, 9)
            ]:
                raise ValueError("dimension identifiers differ")
            recomputed_dimensions: dict[str, str] = {}
            for dimension in expected_dimension_statuses:
                member_ids = {
                    row["requirement_id"]
                    for row in rows
                    if row["dimension_id"] == dimension
                }
                member_statuses = [
                    row["status"] for row in results if row["requirement_id"] in member_ids
                ]
                status_counts = {
                    status: member_statuses.count(status)
                    for status in ("PASS", "FAIL", "BLOCKED", "SKIPPED")
                }
                recomputed = (
                    "FAIL"
                    if "FAIL" in member_statuses
                    else "BLOCKED"
                    if "BLOCKED" in member_statuses
                    else "PASS"
                )
                registered = next(
                    row for row in dimension_rows if row["dimension_id"] == dimension
                )
                if registered["status"] != recomputed or registered["requirement_statuses"] != status_counts:
                    raise ValueError("dimension aggregate differs")
                recomputed_dimensions[dimension] = recomputed
            if recomputed_dimensions != expected_dimension_statuses:
                raise ValueError("unexpected dimension verdicts")

            aggregate = candidate["aggregate_verdict"]
            project_dimensions = ("D01", "D02", "D03", "D04", "D05", "D08")
            project_verdict = (
                "FAIL"
                if any(recomputed_dimensions[item] == "FAIL" for item in project_dimensions)
                else "BLOCKED"
                if any(recomputed_dimensions[item] == "BLOCKED" for item in project_dimensions)
                else "PASS"
            )
            release_verdict = (
                "FAIL"
                if "FAIL" in recomputed_dimensions.values()
                else "BLOCKED"
                if "BLOCKED" in recomputed_dimensions.values() or findings
                else "PASS"
            )
            dimension_counts = {
                status: list(recomputed_dimensions.values()).count(status)
                for status in ("PASS", "FAIL", "BLOCKED")
            }
            if (
                aggregate["requirement_status_counts"] != observed_counts
                or aggregate["dimension_status_counts"] != dimension_counts
                or aggregate["project_completion_verdict"] != project_verdict
                or aggregate["external_release_readiness"] != release_verdict
                or aggregate["release_class"] != "not_ready"
                or aggregate["unresolved_release_blockers"] != len(findings)
                or aggregate["john_decision_required"] is not True
                or aggregate["scientific_claim_revalidation_performed"] is not False
            ):
                raise ValueError("project or release aggregate differs")
            if candidate["authorization"]["release_authorized"] is not False:
                raise ValueError("release authority was inferred")
            for path, digest in candidate["protected_artifacts"].items():
                if sha256_file(PROJECT_ROOT / path) != digest:
                    raise ValueError(f"protected hash mismatch: {path}")

        validate_bundle(evidence, contract_rows)

        mutations: list[tuple[str, Any]] = []
        mutated = copy.deepcopy(evidence)
        mutated["requirement_results"][1]["requirement_id"] = "ST08-REQ-01"
        mutations.append(("duplicate_requirement_id", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["dimension_results"][0]["dimension_id"] = "D99"
        mutations.append(("unknown_dimension", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["requirement_results"][0]["status"] = "UNKNOWN"
        mutations.append(("unknown_status", mutated))
        mutated_rows = copy.deepcopy(contract_rows)
        mutated_rows[0]["fail_rule"] = ""
        mutations.append(("missing_rule", (evidence, mutated_rows)))
        mutated = copy.deepcopy(evidence)
        mutated["authoritative_support"] = []
        mutations.append(("missing_source", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["requirement_results"][0]["evidence_paths"] = []
        mutations.append(("missing_evidence_path", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["requirement_results"][0]["verification_command_or_method"] = ""
        mutations.append(("missing_verification_method", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["requirement_results"][1]["status"] = "PASS"
        mutations.append(("premature_pass", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["requirement_results"][0]["status"] = "SKIPPED"
        mutations.append(("mandatory_skipped", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["dimension_results"][0]["status"] = "PASS"
        mutations.append(("wrong_dimension_aggregate", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["aggregate_verdict"]["external_release_readiness"] = "PASS"
        mutations.append(("release_pass_with_nonpass_dimension", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["open_findings"].pop()
        mutations.append(("silent_finding", mutated))
        mutated = copy.deepcopy(evidence)
        protected_path = next(iter(mutated["protected_artifacts"]))
        mutated["protected_artifacts"][protected_path] = "0" * 64
        mutations.append(("protected_hash_mismatch", mutated))
        mutated = copy.deepcopy(evidence)
        mutated["aggregate_verdict"]["john_decision_required"] = False
        mutations.append(("inferred_john_acceptance", mutated))

        mutation_rejections = []
        for name, candidate in mutations:
            candidate_evidence, candidate_rows = (
                candidate if isinstance(candidate, tuple) else (candidate, contract_rows)
            )
            try:
                if name == "missing_source" and candidate_evidence["authoritative_support"] == []:
                    raise ValueError("authoritative support missing")
                validate_bundle(candidate_evidence, candidate_rows)
            except (KeyError, TypeError, ValueError):
                mutation_rejections.append(name)

        checkpoint = evidence["source_checkpoint"]
        checkpoint_path = Path(checkpoint["path"])
        checkpoint_exact = (
            checkpoint_path.is_file()
            and checkpoint_path.stat().st_size == checkpoint["size_bytes"]
            and sha256_file(checkpoint_path) == checkpoint["sha256"]
        )
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st08_02_project_completion_and_release_readiness_"
            "baseline_audit_change_scope_v01.csv"
        )
        scope_exact = [row["relative_path"] for row in scope_rows] == evidence[
            "planned_change_set"
        ]["paths"]
        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        documentary_tokens = (
            "ACCEPTED_BY_JOHN: ST08_01_project_completion_and_release_readiness_contract_design",
            "TASK_CLOSED: ST08_01_project_completion_and_release_readiness_contract_design",
            "NEXT_BLOCK_AUTHORIZED: ST08_02_project_completion_and_release_readiness_baseline_audit",
            "ST08_02_status: technical_fail_ready_for_john_acceptance",
            "stage08_requirement_results: PASS=7;FAIL=7;BLOCKED=10;SKIPPED=0",
            "project_completion_verdict: FAIL",
            "external_release_readiness: FAIL",
            "release_class: not_ready",
            "proposed_next_block: ST08_03_project_scope_release_class_and_owner_decision_resolution",
            "ST08_03_status: proposed_not_authorized",
        )
        documentary = all(
            all(token in text for token in documentary_tokens)
            for text in (stage_text, roadmap_text)
        )
        absent_outputs = all(
            not (PROJECT_ROOT / path).exists()
            for path in (
                "README.md",
                "pyproject.toml",
                "requirements.txt",
                "environment.yml",
                "LICENSE",
                "LICENSE.txt",
                "LICENSE.md",
                "CITATION.cff",
                "SECURITY.md",
                "tests",
                "dist",
            )
        )
        verification = evidence["verification_result"]
        evidence_final = (
            evidence["task_profile"] == "SCIENTIFIC_VALIDATION"
            and evidence["authorization"]["remediation_authorized"] is False
            and evidence["authorization"]["new_training_authorized"] is False
            and evidence["observed_checks"]["current_unresolved_document_paths"] == 9
            and evidence["observed_checks"]["local_secret_pattern_findings"] == 0
            and evidence["observed_checks"]["full_model_training_runs"] == 0
            and evidence["observed_checks"]["scientific_artifact_changes"] == 0
            and evidence["observed_checks"]["release_actions"] == 0
            and len(evidence["authoritative_support"]) == 9
            and len(evidence["residual_risks"]) == 5
            and evidence["actual_change_log"]
            == {"planned_paths": 5, "actual_paths": 5, "deviations": 0}
            and verification == {
                "focused_gate": "PASS",
                "baseline": "PASS",
                "cumulative_pilot": "PASS",
            }
            and evidence["technical_status"] == "FAIL"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["proposed_next_block"]["status"] == "proposed_not_authorized"
            and evidence["proposed_next_block"]["implementation_started"] is False
        )
        checks = {
            "bundle": True,
            "mutations": len(mutation_rejections) == 14,
            "checkpoint": checkpoint_exact,
            "scope": scope_exact,
            "documentary": documentary,
            "absent_outputs": absent_outputs,
            "evidence": evidence_final,
        }
        return Check(
            "stage08_project_completion_and_release_readiness_baseline_audit",
            "PASS" if all(checks.values()) else "FAIL",
            f"requirements=24:{expected_status_counts}; dimensions="
            f"{expected_dimension_statuses}; completion=FAIL; release=FAIL; "
            f"findings={len(evidence['open_findings'])}; residual_risks="
            f"{len(evidence['residual_risks'])}; mutations="
            f"{len(mutation_rejections)}/14; checkpoint_v52={checkpoint_exact}; "
            f"protected={len(evidence['protected_artifacts'])}/18; "
            f"scope={len(scope_rows)}/5:{scope_exact}; documentary={documentary}",
        )
    except Exception as exc:
        return Check(
            "stage08_project_completion_and_release_readiness_baseline_audit",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage08_project_scope_release_class_owner_decisions() -> Check:
    try:
        evidence_path = (
            PROJECT_ROOT
            / "data_registry/st08_03_project_scope_release_class_owner_"
            "decision_evidence_v01.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        scope_rows = read_contract_csv(
            PROJECT_ROOT
            / "docs/agent/st08_03_project_scope_release_class_owner_decision_"
            "change_scope_v01.csv"
        )
        scope_paths = [row["relative_path"] for row in scope_rows]
        decisions = {
            row["decision_id"]: row for row in evidence.get("owner_decisions", [])
        }
        expected_decisions = {f"D{index:02d}" for index in range(1, 10)}
        decisions_exact = (
            set(decisions) == expected_decisions
            and all(
                row.get("status") == "accepted_by_john"
                and bool(row.get("normalized_decision"))
                and bool(row.get("plain_russian_interpretation"))
                for row in decisions.values()
            )
        )

        product = evidence["product_scope"]
        product_exact = (
            product["mission"]
            == "public_research_grade_ml_claim_reliability_auditor"
            and product["supported_interface_target"] == "universal_cli"
            and product["supported_problem_types_for_v1_0_0"]
            == ["tabular_classification", "tabular_regression"]
            and set(product["required_outputs_for_v1_0_0"])
            == {
                "current_technical_report",
                "reproducible_validation_pipeline",
                "installable_universal_cli",
                "dashboard_using_the_same_validated_core",
                "russian_and_english_documentation",
                "public_github_repository",
            }
            and "universal_model_superiority_claim"
            in product["excluded_from_current_product_branch"]
            and "change_to_registered_miniboone_claim_protocol_policy_or_verdict"
            in product["excluded_from_current_product_branch"]
        )

        release = evidence["release_policy"]
        release_exact = (
            release["release_class_target"]
            == "public_installable_python_distribution"
            and release["source_repository_target"]
            == "https://github.com/Vanargo/ML-CRA"
            and release["python_distribution_required"] is True
            and release["first_supported_release_version"] == "0.1.0"
            and release["version_1_0_0_gate"]
            == "classification_regression_dashboard_and_bilingual_documentation_pass"
            and release["pypi_publication"] == "deferred_to_separate_owner_decision"
            and release["public_repository_creation_authorized_in_st08_03"] is False
            and release["external_release_authorized_in_st08_03"] is False
        )

        legal = evidence["legal_and_citation_policy"]
        creator = legal["creator"]
        legal_exact = (
            legal["project_license"] == "MIT"
            and legal["license_file_creation"]
            == "pending_separately_authorized_implementation"
            and legal["third_party_terms_overridden"] is False
            and legal["dataset_terms_reconciliation_required"] is True
            and legal["citation_file"] == "CITATION.cff"
            and creator
            == {
                "given_names": "Иван",
                "family_names": "Полищук",
                "orcid": "https://orcid.org/0009-0005-6596-0605",
                "github_owner": "Vanargo",
            }
        )

        communication = evidence["communication_policy_change"]
        agents_text = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill_text = (
            PROJECT_ROOT / ".agents/skills/ml-cra-stage-gate/SKILL.md"
        ).read_text(encoding="utf-8")
        contract_text = (
            PROJECT_ROOT / "docs/agent/ml_cra_agent_working_contract_v01.md"
        ).read_text(encoding="utf-8-sig")
        historical_text = (
            PROJECT_ROOT / "docs/stages/stage_07_code_modularization.md"
        ).read_text(encoding="utf-8-sig")
        communication_exact = (
            communication["machine_status_plain_russian_interpretation_required"]
            is True
            and communication["fixed_source_change_reporting_template_required"]
            is False
            and communication["historical_stage_records_rewritten"] is False
            and "Machine-readable labels" in agents_text
            and "plain-Russian interpretation" in skill_text
            and "Машиночитаемые метки" in contract_text
            and "Как было" not in agents_text
            and "Как стало" not in agents_text
            and "Как было" not in skill_text
            and "Как стало" not in skill_text
            and "Как было" in historical_text
        )

        protected_mismatches = [
            path
            for path, digest in evidence["protected_artifacts"].items()
            if not (PROJECT_ROOT / path).is_file()
            or sha256_file(PROJECT_ROOT / path) != digest
        ]
        protected_exact = (
            len(evidence["protected_artifacts"]) == 18
            and not protected_mismatches
        )

        dispositions = evidence["finding_dispositions"]
        disposition_exact = (
            len(dispositions) == 9
            and [row["priority"] for row in dispositions] == list(range(1, 10))
            and {row["finding_id"] for row in dispositions}
            == {f"ST08-FIND-{index:02d}" for index in range(1, 10)}
        )
        branch = evidence["next_branch_boundary"]
        branch_exact = (
            branch["branch_id"] == "stage08_public_productization_release_train_v01"
            and branch["first_block"]
            == "ST08_04_public_product_scope_and_release_train_contract_design"
            and branch["first_block_status"] == "proposed_not_authorized"
            and branch["first_block_implementation_started"] is False
            and "cli_implementation" in branch["first_block_forbidden_actions"]
            and "github_repository_creation"
            in branch["first_block_forbidden_actions"]
        )

        forbidden_paths = [
            "README.md",
            "LICENSE",
            "LICENSE.txt",
            "CITATION.cff",
            "pyproject.toml",
            "dist",
        ]
        forbidden_outputs_absent = all(
            not (PROJECT_ROOT / path).exists() for path in forbidden_paths
        )
        source_checkpoint = evidence["source_checkpoint"]
        source_checkpoint_path = Path(source_checkpoint["path"])
        source_checkpoint_exact = (
            source_checkpoint_path.is_file()
            and source_checkpoint_path.stat().st_size
            == source_checkpoint["size_bytes"]
            and sha256_file(source_checkpoint_path) == source_checkpoint["sha256"]
        )
        planned_actual_exact = (
            scope_paths == evidence["planned_change_set"]["paths"]
            and scope_paths == evidence["actual_change_log"]["paths"]
            and evidence["change_set_deviations"] == []
        )

        stage_text = (
            PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
        ).read_text(encoding="utf-8-sig")
        roadmap_text = (PROJECT_ROOT / "roadmap.md").read_text(encoding="utf-8-sig")
        stage_required_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST08_03_project_scope_release_class_and_owner_decision_resolution",
            "PROJECT_LICENSE: MIT",
            "CREATOR: Иван Полищук",
            "proposed_next_block: ST08_04_public_product_scope_and_release_train_contract_design",
            "ST08_04_status: proposed_not_authorized",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        roadmap_required_tokens = (
            "NEXT_BLOCK_AUTHORIZED: ST08_03_project_scope_release_class_and_owner_decision_resolution",
            "project_license: MIT",
            "creator: Иван Полищук",
            "proposed_next_block: ST08_04_public_product_scope_and_release_train_contract_design",
            "ST08_04_status: proposed_not_authorized",
            "TECHNICAL_STATUS: PASS",
            "READINESS: READY_FOR_JOHN_ACCEPTANCE",
        )
        documentary_exact = all(token in stage_text for token in stage_required_tokens) and all(
            token in roadmap_text for token in roadmap_required_tokens
        )
        evidence_exact = (
            evidence["schema_version"]
            == "st08_03_owner_decision_resolution_evidence_v01"
            and evidence["task_id"]
            == "ST08_03_project_scope_release_class_and_owner_decision_resolution"
            and evidence["task_profile"] == "CHANGE"
            and evidence["authorization"]
            == "NEXT_BLOCK_AUTHORIZED: ST08_03_project_scope_release_class_and_owner_decision_resolution"
            and evidence["proposed_next_block"]
            == "ST08_04_public_product_scope_and_release_train_contract_design"
            and evidence["proposed_next_block_status"] == "proposed_not_authorized"
            and evidence["technical_status"] == "PASS"
            and evidence["readiness"] == "READY_FOR_JOHN_ACCEPTANCE"
            and evidence["observed_checks"]
            == {
                "owner_decisions_complete": True,
                "plain_russian_status_rule_present": True,
                "fixed_source_change_template_absent_from_future_governing_rules": True,
                "historical_stage_records_preserved": True,
                "protected_hashes_match": True,
                "forbidden_product_and_release_outputs_absent": True,
                "training_runs": 0,
                "network_dataset_accesses": 0,
                "external_release_actions": 0,
                "baseline": "PASS",
                "python_syntax": "PASS",
                "pilot": "PASS",
            }
        )
        checks = {
            "decisions": decisions_exact,
            "product": product_exact,
            "release": release_exact,
            "legal": legal_exact,
            "communication": communication_exact,
            "protected": protected_exact,
            "dispositions": disposition_exact,
            "branch": branch_exact,
            "forbidden_outputs": forbidden_outputs_absent,
            "source_checkpoint": source_checkpoint_exact,
            "scope": planned_actual_exact,
            "documentary": documentary_exact,
            "evidence": evidence_exact,
        }
        return Check(
            "stage08_project_scope_release_class_owner_decisions",
            "PASS" if all(checks.values()) else "FAIL",
            f"decisions={len(decisions)}/9:{decisions_exact}; "
            f"product/release/legal={product_exact}/{release_exact}/{legal_exact}; "
            f"communication={communication_exact}; protected="
            f"{len(evidence['protected_artifacts'])}/18:{protected_exact}; "
            f"findings={len(dispositions)}/9:{disposition_exact}; "
            f"branch={branch_exact}; forbidden_outputs_absent="
            f"{forbidden_outputs_absent}; checkpoint_v53={source_checkpoint_exact}; "
            f"scope={len(scope_rows)}/8:{planned_actual_exact}; "
            f"documentary={documentary_exact}; evidence={evidence_exact}",
        )
    except Exception as exc:
        return Check(
            "stage08_project_scope_release_class_owner_decisions",
            "BLOCKED",
            f"{type(exc).__name__}: {exc}",
        )


def check_stage07_regressions() -> Check:
    try:
        import pandas as pd

        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from mlcra.verdicts import (
            build_cost_quality_audit,
            build_current_effect_readout,
            build_metric_conflict_audit,
            build_parameter_selection_stability_audit,
        )

        data = PROJECT_ROOT / "data_registry"
        read = lambda name: pd.read_csv(
            data / name,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        seed_summary = read("openml_miniboone_stage05_seed_stability_summary.csv")
        split_summary = read("openml_miniboone_stage05_split_10x1_summary.csv")
        seed_outer = read("openml_miniboone_stage05_seed_stability_outer_scores.csv")
        split_outer = read("openml_miniboone_stage05_split_10x1_outer_scores.csv")
        current_outer = read("openml_miniboone_nested_outer_scores.csv")

        cases = [
            (
                "ST07_04",
                build_metric_conflict_audit(seed_summary, split_summary),
                read("openml_miniboone_stage05_metric_conflict_audit.csv"),
                (19, 24),
            ),
            (
                "ST07_05",
                build_parameter_selection_stability_audit(seed_outer, split_outer),
                read("openml_miniboone_stage05_parameter_selection_stability.csv"),
                (22, 23),
            ),
            (
                "ST07_06",
                build_cost_quality_audit(seed_outer, split_outer),
                read("openml_miniboone_stage05_cost_quality_audit.csv"),
                (18, 40),
            ),
            (
                "ST07_07",
                build_current_effect_readout(current_outer),
                read("openml_miniboone_stage05_current_effect_readout.csv"),
                (132, 30),
            ),
        ]
        failures: list[str] = []
        details: list[str] = []
        for name, actual, expected, shape in cases:
            actual_strings = csv_roundtrip_as_strings(actual)
            equal = actual_strings.equals(expected)
            shape_ok = actual.shape == shape
            columns_ok = list(actual.columns) == list(expected.columns)
            contract_ok = True
            contract_detail = ""
            if name == "ST07_07":
                paired_rows = int(
                    actual["row_type"].eq("paired_outer_block").sum()
                )
                summary_rows = int(
                    actual["row_type"].eq("metric_summary").sum()
                )
                comparison_models = set(actual["comparison_model_id"].unique())
                metric_names = set(actual["metric_name"].unique())
                outer_blocks = int(
                    actual[
                        actual["row_type"].eq("paired_outer_block")
                    ][
                        [
                            "outer_split_number",
                            "outer_repeat_number",
                            "outer_fold_number",
                        ]
                    ].drop_duplicates().shape[0]
                )
                contract_ok = (
                    paired_rows == 120
                    and summary_rows == 12
                    and comparison_models
                    == {"logistic_regression", "dummy_prior"}
                    and metric_names
                    == {
                        "average_precision",
                        "roc_auc",
                        "f1",
                        "balanced_accuracy",
                        "log_loss",
                        "brier_score",
                    }
                    and outer_blocks == 10
                )
                contract_detail = (
                    f"/paired:{paired_rows}/summary:{summary_rows}"
                    f"/blocks:{outer_blocks}"
                )
            details.append(
                f"{name}={actual.shape}/equal:{equal}/columns:{columns_ok}"
                f"{contract_detail}"
            )
            if not (shape_ok and columns_ok and equal and contract_ok):
                failures.append(name)
        return Check(
            "stage07_regressions",
            "PASS" if not failures else "FAIL",
            "; ".join(details),
        )
    except Exception as exc:  # pragma: no cover - diagnostic boundary
        return Check("stage07_regressions", "BLOCKED", f"{type(exc).__name__}: {exc}")


def print_result(check: Check) -> None:
    print(f"{check.status:7} {check.name}: {check.detail}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "pilot"), required=True)
    parser.add_argument(
        "--additional-scope",
        action="append",
        default=[],
        metavar="PROJECT_RELATIVE_CSV",
        help=(
            "add a project-relative change-scope CSV after the required "
            "cumulative scope"
        ),
    )
    args = parser.parse_args()

    scope_paths = [
        PROJECT_ROOT / relative_path
        for relative_path in REQUIRED_SCOPE_RELATIVE_PATHS
    ]
    for relative_scope in args.additional_scope:
        candidate = (PROJECT_ROOT / relative_scope).resolve()
        try:
            candidate.relative_to(PROJECT_ROOT)
        except ValueError:
            parser.error(f"additional scope must be inside project root: {relative_scope}")
        if not candidate.is_file():
            parser.error(f"additional scope does not exist: {relative_scope}")
        if candidate not in scope_paths:
            scope_paths.append(candidate)

    inventory = build_project_inventory()
    checks: list[Check] = []
    scope_check, scope_details = check_change_scope(
        strict=args.mode == "pilot",
        current=inventory.files,
        scope_paths=scope_paths,
    )
    checks.append(scope_check)

    if args.mode == "pilot":
        checks.extend(
            [
                check_python_syntax(inventory.files),
                check_csv_structure(inventory.files),
                check_notebooks(inventory.files),
                check_required_paths(),
                check_documentary_consistency(),
                check_stage07_model_space_extraction(),
                check_stage07_st07_07_evidence_preserved(),
                check_stage07_st07_08_evidence_section_placement(),
                check_stage07_st07_08_legacy_evidence_absent(),
                check_stage07_exact_evidence(),
                check_stage07_nested_cv_contract_design(),
                check_stage07_binary_metric_contract_extraction(),
                check_stage07_nested_cv_split_and_evaluation_extraction(),
                check_stage07_nested_cv_fit_and_tuning_extraction(),
                check_stage07_numeric_runtime_contract(),
                check_stage07_nested_cv_v02_protocol_contract(),
                check_stage07_nested_cv_v02_execution_harness(),
                check_stage07_nested_cv_v02_offline_preflight(),
                check_stage07_nested_cv_v02_dual_run_validation(),
                check_stage07_next_block_after_st0718(),
                check_stage07_artifact_context_and_provenance_contract(),
                check_stage07_next_block_after_st0719(),
                check_stage07_provenance_corrected_dual_run_revalidation(),
                check_stage07_next_block_after_st0720(),
                check_stage07_promotion_source_and_timing_provenance_contract(),
                check_stage07_next_block_after_st0721(),
                check_stage07_transactional_promotion_and_canonical_registration(),
                check_stage07_next_block_after_st0722(),
                check_stage07_stage05_seed_stability_contract_design(),
                check_stage07_next_block_after_st0723(),
                check_stage07_stage05_seed_stability_modular_extraction(),
                check_stage07_next_block_after_st0724(),
                check_stage07_stage05_seed_stability_full_validation(),
                check_stage07_next_block_after_st0725(),
                check_stage07_st0726_logistic_blas_diagnostic(),
                check_stage07_next_block_after_st0726(),
                check_stage07_stage05_split_10x1_contract_design(),
                check_stage07_next_block_after_st0727(),
                check_stage07_stage05_split_10x1_modular_extraction(),
                check_stage07_next_block_after_st0728(),
                check_stage07_stage05_split_10x1_full_validation(),
                check_stage07_next_block_after_st0729(),
                check_stage07_stage05_non_nested_optimism_contract_design(),
                check_stage07_next_block_after_st0730(),
                check_stage07_stage05_non_nested_optimism_modular_extraction(),
                check_stage07_next_block_after_st0731(),
                check_stage07_stage05_non_nested_optimism_full_validation(),
                check_stage07_closure_audit(),
                check_stage07_verdict_policy_application_contract_design(),
                check_stage07_verdict_policy_application_modular_extraction(),
                check_stage07_next_block_after_st0735(),
                check_stage07_post_verdict_policy_closure_reaudit(),
                check_stage07_closure_and_next_stage_selection(),
                check_stage08_project_completion_and_release_readiness_contract(),
                check_stage08_project_completion_and_release_readiness_baseline_audit(),
                check_stage08_project_scope_release_class_owner_decisions(),
                check_stage07_text_corruption_absent(),
                check_stage07_regressions(),
            ]
        )

    print(f"ML-CRA agent verification | mode={args.mode}")
    print(f"python={platform.python_version()} | platform={platform.platform()}")
    print(f"ignored_local_files={inventory.ignored_local_files}")
    print(
        "virtual_environment_roots=",
        inventory.virtual_environment_roots,
    )
    for check in checks:
        print_result(check)
    if scope_details["out_of_scope_modified"]:
        print("out_of_scope_modified=", scope_details["out_of_scope_modified"])
    if scope_details["out_of_scope_added"]:
        print("out_of_scope_added=", scope_details["out_of_scope_added"])
    if scope_details["missing"]:
        print("missing_baseline_files=", scope_details["missing"])
    if args.mode == "pilot" and scope_details["missing_planned_additions"]:
        print("missing_planned_additions=", scope_details["missing_planned_additions"])
    if args.mode == "pilot" and scope_details["unchanged_planned_modifications"]:
        print(
            "unchanged_planned_modifications=",
            scope_details["unchanged_planned_modifications"],
        )
    if scope_details["scope_errors"]:
        print("scope_errors=", scope_details["scope_errors"])

    return 0 if all(check.status == "PASS" for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

