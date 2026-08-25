from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.nested_artifacts import (  # noqa: E402
    ARTIFACT_IDS,
    NestedCVArtifacts,
    compare_v02_runs,
    read_v02_artifacts,
)


TASK_ID = "ST07_18_nested_cv_v02_dual_run_reproducibility_validation"
EVIDENCE_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "st07_18_nested_cv_v02_dual_run_reproducibility_validation_evidence_v01.json"
)
PRIOR_ATTEMPT_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "st07_18_nested_cv_v02_implementation_attempt_01_v01.json"
)
RUNNER_PATH = PROJECT_ROOT / "scripts" / "st07_17_miniboone_v02_runner.py"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
)
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "ml-cra-venv",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
EXPECTED_CLASS_COLUMN_COUNTS = {"A": 69, "B": 38, "C": 2, "D": 9}
EXPECTED_ARTIFACT_ROWS = {
    "outer_scores": 30,
    "selected_params": 10,
    "summary": 3,
    "quality_checks": 16,
    "warnings": None,
    "environment": 8,
    "numeric_runtime": 2,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_sha256(manifest: dict[str, str]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_protected_manifest() -> dict[str, str]:
    manifest: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(PROJECT_ROOT, topdown=True):
        directory_path = Path(directory)
        dirnames[:] = sorted(
            [
                name
                for name in dirnames
                if name.casefold() not in EXCLUDED_DIRECTORY_NAMES
            ],
            key=str.casefold,
        )
        for filename in sorted(filenames, key=str.casefold):
            path = directory_path / filename
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            pure = PurePosixPath(relative)
            if (
                pure.suffix.casefold() in EXCLUDED_SUFFIXES
                or path.resolve() == EVIDENCE_PATH.resolve()
            ):
                continue
            manifest[relative] = sha256_file(path)
    return manifest


def require_safe_empty_work_root(work_root: Path) -> Path:
    resolved = work_root.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved == project or project in resolved.parents:
        raise ValueError("validation work root must be outside the project root")
    resolved.mkdir(parents=True, exist_ok=True)
    if any(resolved.iterdir()):
        raise ValueError("validation work root must be empty")
    return resolved


def schema_rows(schema: pd.DataFrame, artifact_id: str) -> pd.DataFrame:
    return schema.loc[schema["artifact_id"].eq(artifact_id)].sort_values(
        "column_position", kind="mergesort"
    )


def artifact_inventory(
    output_dir: Path,
    artifacts: NestedCVArtifacts,
) -> dict[str, dict[str, Any]]:
    return {
        artifact_id: {
            "filename": frame_path.name,
            "rows": len(frame),
            "columns": len(frame.columns),
            "sha256": sha256_file(frame_path),
        }
        for artifact_id, frame in artifacts.as_dict().items()
        for frame_path in [
            next(
                path
                for path in output_dir.iterdir()
                if path.name.startswith(f"openml_miniboone_nested_v02_{artifact_id}")
            )
            if artifact_id not in {"outer_scores", "selected_params", "quality_checks"}
            else output_dir
            / {
                "outer_scores": "openml_miniboone_nested_v02_outer_scores.csv",
                "selected_params": "openml_miniboone_nested_v02_selected_params.csv",
                "quality_checks": "openml_miniboone_nested_v02_quality_checks.csv",
            }[artifact_id]
        ]
    }


def run_one(label: str, cache_server_dir: Path, output_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(RUNNER_PATH),
        "--full-run",
        "--cache-server-dir",
        str(cache_server_dir),
        "--output-dir",
        str(output_dir),
    ]
    started = perf_counter()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    if stdout_lines:
        try:
            parsed = json.loads(stdout_lines[-1])
        except json.JSONDecodeError as error:
            parse_error = str(error)
    else:
        parse_error = "runner stdout did not contain a JSON result"
    return {
        "label": label,
        "command": [
            "<python>",
            "scripts/st07_17_miniboone_v02_runner.py",
            "--full-run",
            "--cache-server-dir",
            "<registered_local_cache>",
            "--output-dir",
            f"<{label}_noncanonical_output>",
        ],
        "return_code": completed.returncode,
        "elapsed_seconds": perf_counter() - started,
        "stdout_line_count": len(stdout_lines),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode("utf-8")).hexdigest(),
        "stderr_text": completed.stderr,
        "parse_error": parse_error,
        "runner_result": parsed,
    }


def diagnose_comparison_classes(
    run_a: NestedCVArtifacts,
    run_b: NestedCVArtifacts,
    schema: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    frames_a = run_a.as_dict()
    frames_b = run_b.as_dict()
    for comparison_class in ("A", "B", "C", "D"):
        errors: list[str] = []
        count = 0
        for artifact_id in ARTIFACT_IDS:
            rows = schema_rows(schema, artifact_id)
            columns = rows.loc[
                rows["comparison_class"].eq(comparison_class), "column_name"
            ].tolist()
            count += len(columns)
            if not columns:
                continue
            left = frames_a[artifact_id][columns].reset_index(drop=True)
            right = frames_b[artifact_id][columns].reset_index(drop=True)
            try:
                if comparison_class in {"A", "B"}:
                    pd.testing.assert_frame_equal(
                        left, right, check_exact=True, check_dtype=False
                    )
                elif comparison_class == "C":
                    for frame in (left, right):
                        numeric = frame.apply(pd.to_numeric, errors="raise")
                        if (
                            not np.isfinite(numeric.to_numpy(dtype=float)).all()
                            or (numeric < 0).any().any()
                        ):
                            raise ValueError("timing is not finite and nonnegative")
                else:
                    left = left.sort_values(columns, kind="mergesort").reset_index(
                        drop=True
                    )
                    right = right.sort_values(columns, kind="mergesort").reset_index(
                        drop=True
                    )
                    pd.testing.assert_frame_equal(
                        left, right, check_exact=True, check_dtype=False
                    )
            except (AssertionError, TypeError, ValueError) as error:
                errors.append(f"{artifact_id}: {error}")
        results[comparison_class] = {
            "status": "pass" if not errors else "fail",
            "column_count": count,
            "errors": errors,
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-server-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()

    work_root = require_safe_empty_work_root(args.work_root)
    if EVIDENCE_PATH.exists():
        raise FileExistsError("ST07_18 evidence path must not already exist")
    schema = read_csv_checked(SCHEMA_PATH)
    prior_attempt = json.loads(PRIOR_ATTEMPT_PATH.read_text(encoding="utf-8"))
    if (
        prior_attempt.get("task_id") != TASK_ID
        or prior_attempt.get("attempt_number") != 1
        or prior_attempt.get("scientific_verdict_eligible") is not False
    ):
        raise ValueError("registered implementation-attempt record is invalid")
    canonical_paths = sorted(
        {
            (PROJECT_ROOT / path).resolve()
            for path in schema["canonical_path"].tolist()
        }
    )
    canonical_absent_before = all(not path.exists() for path in canonical_paths)
    protected_before = build_protected_manifest()

    process_records: list[dict[str, Any]] = []
    for label in ("run_a", "run_b"):
        output_dir = work_root / label
        process_records.append(run_one(label, args.cache_server_dir, output_dir))

    run_artifacts: dict[str, NestedCVArtifacts] = {}
    artifact_records: dict[str, dict[str, Any]] = {}
    artifact_errors: dict[str, str] = {}
    for record in process_records:
        label = record["label"]
        try:
            artifacts = read_v02_artifacts(work_root / label, schema)
            run_artifacts[label] = artifacts
            artifact_records[label] = artifact_inventory(
                work_root / label, artifacts
            )
        except Exception as error:
            artifact_errors[label] = f"{type(error).__name__}: {error}"

    comparison_classes = {
        key: {
            "status": "not_evaluated",
            "column_count": value,
            "errors": [],
        }
        for key, value in EXPECTED_CLASS_COLUMN_COUNTS.items()
    }
    comparator_result: dict[str, Any] | None = None
    comparator_error: str | None = None
    if set(run_artifacts) == {"run_a", "run_b"}:
        comparison_classes = diagnose_comparison_classes(
            run_artifacts["run_a"], run_artifacts["run_b"], schema
        )
        try:
            comparator_result = compare_v02_runs(
                run_artifacts["run_a"], run_artifacts["run_b"], schema
            )
        except Exception as error:
            comparator_error = f"{type(error).__name__}: {error}"

    protected_after = build_protected_manifest()
    changed_protected = sorted(
        path
        for path in set(protected_before) | set(protected_after)
        if protected_before.get(path) != protected_after.get(path)
    )
    canonical_absent_after = all(not path.exists() for path in canonical_paths)
    process_pass = (
        len(process_records) == 2
        and all(record["return_code"] == 0 for record in process_records)
        and all(record["parse_error"] is None for record in process_records)
        and all(
            record["runner_result"] is not None
            and record["runner_result"].get("status") == "pass"
            and record["runner_result"].get("network_attempts") == 0
            and record["runner_result"].get("runtime_backend_count") == 2
            and record["runner_result"].get("runtime_threads") == [1, 1]
            and record["runner_result"].get("quality_pass_count") == 16
            for record in process_records
        )
    )
    artifact_rows_pass = set(artifact_records) == {"run_a", "run_b"} and all(
        inventory[artifact_id]["rows"] >= 1
        if expected is None
        else inventory[artifact_id]["rows"] == expected
        for inventory in artifact_records.values()
        for artifact_id, expected in EXPECTED_ARTIFACT_ROWS.items()
    )
    comparison_pass = (
        comparator_result is not None
        and comparator_error is None
        and comparator_result.get("class_column_counts")
        == EXPECTED_CLASS_COLUMN_COUNTS
        and all(
            item["status"] == "pass"
            and item["column_count"] == EXPECTED_CLASS_COLUMN_COUNTS[key]
            for key, item in comparison_classes.items()
        )
    )
    checks = {
        "run_processes_and_exit_status": process_pass,
        "candidate_artifacts_and_row_policies": artifact_rows_pass,
        "registered_comparison": comparison_pass,
        "offline_network_attempts_zero": all(
            record["runner_result"] is not None
            and record["runner_result"].get("network_attempts") == 0
            for record in process_records
        ),
        "quality_checks_16_of_16_per_run": all(
            record["runner_result"] is not None
            and record["runner_result"].get("quality_pass_count") == 16
            for record in process_records
        ),
        "runtime_two_backends_one_thread_per_run": all(
            record["runner_result"] is not None
            and record["runner_result"].get("runtime_backend_count") == 2
            and record["runner_result"].get("runtime_threads") == [1, 1]
            for record in process_records
        ),
        "protected_artifacts_unchanged": not changed_protected,
        "canonical_v02_outputs_absent": (
            canonical_absent_before and canonical_absent_after
        ),
        "claim_or_verdict_change_none": True,
        "promotion_not_performed": True,
    }
    technical_status = "PASS" if all(checks.values()) else "FAIL"
    evidence = {
        "evidence_schema_version": "st07_18_evidence_v01",
        "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "technical_status": technical_status,
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        "scientific_interpretation": (
            "same_environment_computational_reproducibility_only; "
            "not_universal_model_superiority; not_stage05_claim_support"
        ),
        "protocol_id": "miniboone_nested_cv_v02",
        "validation_run_count": 2,
        "implementation_attempts": [prior_attempt],
        "fresh_process_invocations": 2,
        "separate_noncanonical_directories": ["run_a", "run_b"],
        "process_records": process_records,
        "artifact_records": artifact_records,
        "artifact_errors": artifact_errors,
        "expected_artifact_rows": EXPECTED_ARTIFACT_ROWS,
        "comparison_classes": comparison_classes,
        "authoritative_comparator_result": comparator_result,
        "authoritative_comparator_error": comparator_error,
        "checks": checks,
        "protected_file_count": len(protected_before),
        "protected_manifest_sha256_before": manifest_sha256(protected_before),
        "protected_manifest_sha256_after": manifest_sha256(protected_after),
        "changed_protected_paths": changed_protected,
        "canonical_output_count": len(canonical_paths),
        "canonical_outputs_absent_before": canonical_absent_before,
        "canonical_outputs_absent_after": canonical_absent_after,
        "candidate_artifacts_promoted": 0,
        "stage05_claim_or_verdict_changed": False,
    }
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return 0 if technical_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
