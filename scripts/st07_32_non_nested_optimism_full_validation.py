from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_info, threadpool_limits


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.datasets import deny_network_access, load_miniboone_from_openml_cache  # noqa: E402
from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.model_spaces import build_hist_gradient_boosting_search_space  # noqa: E402
from mlcra.stress_tests import (  # noqa: E402
    NonNestedOptimismBundle,
    build_non_nested_optimism_contract,
    build_non_nested_reference_table,
    run_non_nested_optimism_probe,
    validate_non_nested_optimism_bundle,
)


TASK_ID = (
    "ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_"
    "golden_diagnostic_validation"
)
BASE_PROTOCOL_ID = "miniboone_nested_cv_v01"
DIAGNOSTIC_BLAS_THREADS = 4
EXPECTED_OPENMP = {
    "user_api": "openmp",
    "internal_api": "openmp",
    "prefix": "vcomp",
    "library_filename": "vcomp140.dll",
    "num_threads": 12,
}
EVIDENCE_FILENAME = (
    "st07_32_stage05_non_nested_optimism_full_validation_evidence_v01.json"
)
CANDIDATE_FILENAME = "st07_32_stage05_non_nested_optimism_candidate_v01.csv"
EXECUTION_CONTRACT_FILENAME = "st07_32_execution_contract_before_fit_v01.json"
GOLDEN_PATH = "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv"
ST0726_EVIDENCE = (
    "data_registry/"
    "st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json"
)
KEY_COLUMNS = [
    "stress_test_id",
    "single_level_cv_random_state",
    "comparison_reference_id",
]
CLASS_B_COLUMNS = [
    "selected_parameter_set_id",
    "selected_params_json",
    "non_nested_average_precision_mean",
    "non_nested_average_precision_std_for_selected_params",
    "nested_average_precision_mean",
    "optimism_delta_non_nested_minus_nested",
    "audit_status",
    "audit_status_ru",
]
CLASS_C_COLUMNS = ["fit_seconds"]

PROTECTED_HASHES = {
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
    GOLDEN_PATH: "cdb9bbd52d9d57738e228dbbd707724f4ebdcad09003b0ea3ce2c1f8e5933317",
    ST0726_EVIDENCE: "e07ad5bec329903266eff66436fa9d2e5045de3fa707e14a13da38b89c52bc44",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_hash_state() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for relative_path, expected in PROTECTED_HASHES.items():
        observed = sha256_file(PROJECT_ROOT / relative_path)
        result[relative_path] = {
            "expected_sha256": expected,
            "observed_sha256": observed,
            "match": observed == expected,
        }
    return result


def require_safe_empty_output(output_dir: Path) -> Path:
    output = output_dir.resolve()
    root = PROJECT_ROOT.resolve()
    if output == root or root in output.parents:
        raise ValueError("ST07_32 output must be outside the project root")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("ST07_32 output directory must be empty")
    return output


def destination_paths(evidence_dir: Path) -> tuple[Path, Path]:
    destination = evidence_dir.resolve()
    if destination != (PROJECT_ROOT / "data_registry").resolve():
        raise ValueError("ST07_32 evidence-dir must be the project data_registry")
    return destination / CANDIDATE_FILENAME, destination / EVIDENCE_FILENAME


def require_absent_destinations(evidence_dir: Path) -> None:
    existing = [str(path) for path in destination_paths(evidence_dir) if path.exists()]
    if existing:
        raise FileExistsError(f"ST07_32 evidence targets already exist: {existing}")


def controller_rows() -> list[dict[str, Any]]:
    fields = (
        "user_api",
        "internal_api",
        "prefix",
        "version",
        "threading_layer",
        "architecture",
        "filepath",
        "num_threads",
    )
    rows: list[dict[str, Any]] = []
    for info in threadpool_info():
        row = {field: info.get(field) for field in fields}
        row["library_filename"] = Path(str(info.get("filepath"))).name.lower()
        rows.append(row)
    return sorted(rows, key=lambda row: (str(row["user_api"]), str(row["filepath"])))


def api_rows(rows: list[dict[str, Any]], user_api: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["user_api"] == user_api]


def identity(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    fields = (
        "user_api",
        "internal_api",
        "prefix",
        "version",
        "threading_layer",
        "architecture",
        "library_filename",
    )
    return sorted(tuple(str(row[field]) for field in fields) for row in rows)


def reference_blas_identity() -> list[tuple[str, ...]]:
    evidence = json.loads((PROJECT_ROOT / ST0726_EVIDENCE).read_text(encoding="utf-8"))
    rows = []
    for source in evidence["execution_contract"]["environment"]["blas_before"]:
        row = dict(source)
        row["user_api"] = "blas"
        rows.append(row)
    return identity(rows)


def verify_runtime(
    rows: list[dict[str, Any]],
    *,
    expected_blas_threads: int | None,
    expected_identity: list[tuple[str, ...]] | None = None,
) -> None:
    blas = api_rows(rows, "blas")
    openmp = api_rows(rows, "openmp")
    if not blas:
        raise RuntimeError("No BLAS controller was registered")
    if expected_identity is not None and identity(blas) != expected_identity:
        raise RuntimeError("Current BLAS backend identity differs from ST07_26")
    if expected_blas_threads is not None and any(
        int(row["num_threads"]) != expected_blas_threads for row in blas
    ):
        raise RuntimeError(
            f"BLAS thread condition differs: expected={expected_blas_threads}; observed={blas}"
        )
    if len(openmp) != 1 or any(
        str(openmp[0].get(field)).lower() != str(expected).lower()
        for field, expected in EXPECTED_OPENMP.items()
    ):
        raise RuntimeError(f"OpenMP condition differs from predeclared state: {openmp}")


def package_versions() -> dict[str, str]:
    names = ("numpy", "pandas", "scipy", "scikit-learn", "openml", "threadpoolctl")
    return {name: importlib.metadata.version(name) for name in names}


def prepare_run(cache_server_dir: Path, evidence_dir: Path) -> dict[str, Any]:
    require_absent_destinations(evidence_dir)
    protected_before = protected_hash_state()
    if not all(row["match"] for row in protected_before.values()):
        raise RuntimeError("Protected ST07_32 source or scientific input hash differs")

    plan = read_csv_checked(
        PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
    )
    claims = read_csv_checked(
        PROJECT_ROOT / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
    )
    contract = build_non_nested_optimism_contract(plan, claims)
    model_space = read_csv_checked(
        PROJECT_ROOT
        / "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv"
    )
    parameter_grid, fixed_parameters = build_hist_gradient_boosting_search_space(
        model_space, BASE_PROTOCOL_ID, contract.candidate_id
    )
    nested = read_csv_checked(
        PROJECT_ROOT / "data_registry/openml_miniboone_nested_summary.csv"
    )
    seeds = read_csv_checked(
        PROJECT_ROOT
        / "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv"
    )
    split = read_csv_checked(
        PROJECT_ROOT
        / "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv"
    )
    references = build_non_nested_reference_table(nested, seeds, split, contract)
    candidate_bundle, X, y, feature_names, cache = load_miniboone_from_openml_cache(
        cache_server_dir
    )
    golden = pd.read_csv(
        PROJECT_ROOT / GOLDEN_PATH,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    if golden.shape != (15, 39) or golden.duplicated(KEY_COLUMNS).any():
        raise RuntimeError("Historical ST05_07 golden schema/shape/key differs")
    if references.shape != (9, 7):
        raise RuntimeError("ST05_07 reference table must be exactly 9x7")
    if (
        len(X) != 130064
        or len(feature_names) != 50
        or cache.target_false_count != 93565
        or cache.target_true_count != 36499
        or cache.network_attempts != 0
    ):
        raise RuntimeError("Offline MiniBooNE dataset contract differs")
    if int(np.prod([len(values) for values in parameter_grid.values()])) != 16:
        raise RuntimeError("Locked HGB grid must contain 16 candidates")

    runtime_before = controller_rows()
    reference_identity = reference_blas_identity()
    verify_runtime(
        runtime_before,
        expected_blas_threads=None,
        expected_identity=reference_identity,
    )
    return {
        "protected_before": protected_before,
        "contract": contract,
        "parameter_grid": parameter_grid,
        "fixed_parameters": fixed_parameters,
        "references": references,
        "candidate_bundle": candidate_bundle,
        "X": X,
        "y": y,
        "feature_names": feature_names,
        "cache": cache,
        "golden": golden,
        "runtime_before": runtime_before,
        "reference_blas_identity": reference_identity,
    }


def execution_contract(prepared: dict[str, Any], output: Path) -> dict[str, Any]:
    contract = prepared["contract"]
    cache = prepared["cache"]
    record = {
        "task_id": TASK_ID,
        "status": "locked_before_first_fit",
        "pid": os.getpid(),
        "output_dir": str(output),
        "offline_only": True,
        "network_attempts_before_fit": cache.network_attempts,
        "dataset": {
            "candidate_id": contract.candidate_id,
            "openml_dataset_id": prepared["candidate_bundle"]["did"],
            "rows": len(prepared["X"]),
            "feature_count": len(prepared["feature_names"]),
            "target_false_count": cache.target_false_count,
            "target_true_count": cache.target_true_count,
            "dataset_content_sha256": cache.dataset_content_sha256,
            "cache_manifest_sha256": cache.cache_manifest_sha256,
            "cache_file_count": cache.cache_file_count,
        },
        "protocol": {
            "stress_test_id": contract.stress_test_id,
            "claim_id": contract.claim_id,
            "protocol_variant_id": contract.protocol_variant_id,
            "random_states": list(contract.random_states),
            "n_splits": contract.n_splits,
            "n_repeats": contract.n_repeats,
            "cv_blocks_per_seed": contract.n_splits * contract.n_repeats,
            "grid_candidate_count": contract.grid_candidate_count,
            "scoring": contract.scoring,
            "refit": True,
            "n_jobs": 1,
            "return_train_score": False,
            "error_score": "raise",
            "grid_search_count": 3,
            "cv_candidate_fold_fit_count": 480,
            "refit_count": 3,
            "full_run_count": 1,
            "reference_shape": list(prepared["references"].shape),
            "golden_shape": list(prepared["golden"].shape),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(),
            "threadpool_before": prepared["runtime_before"],
            "diagnostic_blas_threads": DIAGNOSTIC_BLAS_THREADS,
            "prospective_openmp_condition": EXPECTED_OPENMP,
            "historical_openmp_provenance": "unknown_not_inferred",
            "historical_blas_provenance": "unknown_not_inferred",
        },
        "comparison_policy": {
            "class_a_columns": 30,
            "class_b_columns": CLASS_B_COLUMNS,
            "class_c_columns": CLASS_C_COLUMNS,
            "class_a": "exact_after_csv_roundtrip",
            "class_b": "exact_after_csv_roundtrip_no_tolerance",
            "class_c": "numeric_finite_nonnegative_excluded_from_equality",
            "mismatch_verdict": "fail_without_causal_attribution",
            "post_result_tolerance_selection": "prohibited",
        },
        "protected_before": prepared["protected_before"],
    }
    path = output / EXECUTION_CONTRACT_FILENAME
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def first_mismatch(
    candidate: pd.DataFrame,
    golden: pd.DataFrame,
    mask: pd.DataFrame,
    columns: list[str],
) -> dict[str, Any] | None:
    for row_index in range(len(candidate)):
        for column in columns:
            if bool(mask.at[row_index, column]):
                return {
                    "row_index": row_index,
                    "key": {key: str(candidate.at[row_index, key]) for key in KEY_COLUMNS},
                    "column": column,
                    "candidate": str(candidate.at[row_index, column]),
                    "golden": str(golden.at[row_index, column]),
                }
    return None


def numeric_diagnostics(
    candidate: pd.DataFrame, golden: pd.DataFrame, columns: list[str]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for column in columns:
        left = pd.to_numeric(candidate[column], errors="coerce")
        right = pd.to_numeric(golden[column], errors="coerce")
        comparable = left.notna() & right.notna()
        deltas = (left[comparable] - right[comparable]).abs()
        result[column] = {
            "comparable_cells": int(comparable.sum()),
            "mismatch_cells": int(candidate[column].ne(golden[column]).sum()),
            "max_absolute_delta": float(deltas.max()) if len(deltas) else None,
        }
    return result


def compare_candidate(candidate_path: Path) -> dict[str, Any]:
    candidate = pd.read_csv(candidate_path, dtype=str, keep_default_na=False)
    golden = pd.read_csv(
        PROJECT_ROOT / GOLDEN_PATH,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    schema_exact = list(candidate.columns) == list(golden.columns)
    shape_exact = candidate.shape == golden.shape == (15, 39)
    keys_exact = (
        schema_exact
        and shape_exact
        and candidate[KEY_COLUMNS].equals(golden[KEY_COLUMNS])
        and not candidate.duplicated(KEY_COLUMNS).any()
    )
    if not schema_exact or not shape_exact or not keys_exact:
        return {
            "schema_exact": schema_exact,
            "shape_exact": shape_exact,
            "keys_and_order_exact": keys_exact,
            "class_a_exact": False,
            "class_b_exact": False,
            "class_c_valid": False,
            "structural_stop": True,
        }
    class_a = [
        column
        for column in candidate.columns
        if column not in set(CLASS_B_COLUMNS + CLASS_C_COLUMNS)
    ]
    if len(class_a) != 30:
        raise RuntimeError(f"Class A must contain 30 columns, observed={len(class_a)}")
    mismatch = candidate.ne(golden)
    class_a_mismatch = mismatch[class_a]
    class_b_mismatch = mismatch[CLASS_B_COLUMNS]
    timings = pd.to_numeric(candidate["fit_seconds"], errors="coerce")
    timing_valid = timings.notna() & timings.map(math.isfinite) & timings.ge(0.0)
    return {
        "candidate_filename": candidate_path.name,
        "candidate_sha256": sha256_file(candidate_path),
        "golden_filename": Path(GOLDEN_PATH).name,
        "golden_sha256": sha256_file(PROJECT_ROOT / GOLDEN_PATH),
        "candidate_shape": list(candidate.shape),
        "golden_shape": list(golden.shape),
        "schema_exact": schema_exact,
        "shape_exact": shape_exact,
        "keys_and_order_exact": keys_exact,
        "class_a_columns": class_a,
        "class_a_comparable_cells": int(candidate[class_a].size),
        "class_a_mismatch_cells": int(class_a_mismatch.to_numpy().sum()),
        "class_a_exact": not bool(class_a_mismatch.to_numpy().any()),
        "class_a_first_mismatch": first_mismatch(
            candidate, golden, class_a_mismatch, class_a
        ),
        "class_b_columns": CLASS_B_COLUMNS,
        "class_b_comparable_cells": int(candidate[CLASS_B_COLUMNS].size),
        "class_b_mismatch_cells": int(class_b_mismatch.to_numpy().sum()),
        "class_b_exact": not bool(class_b_mismatch.to_numpy().any()),
        "class_b_first_mismatch": first_mismatch(
            candidate, golden, class_b_mismatch, CLASS_B_COLUMNS
        ),
        "class_b_numeric_deltas": numeric_diagnostics(
            candidate,
            golden,
            [
                "non_nested_average_precision_mean",
                "non_nested_average_precision_std_for_selected_params",
                "nested_average_precision_mean",
                "optimism_delta_non_nested_minus_nested",
            ],
        ),
        "class_c_columns": CLASS_C_COLUMNS,
        "class_c_valid": bool(timing_valid.all()),
        "class_c_diagnostics": {
            "valid_cells": int(timing_valid.sum()),
            "total_cells": int(len(timings)),
            "minimum": float(timings.min()) if timings.notna().any() else None,
            "maximum": float(timings.max()) if timings.notna().any() else None,
        },
        "structural_stop": False,
    }


def scientific_signal(candidate_path: Path) -> dict[str, Any]:
    candidate = pd.read_csv(candidate_path)
    deltas = pd.to_numeric(
        candidate["optimism_delta_non_nested_minus_nested"], errors="raise"
    )
    per_seed = []
    for seed, rows in candidate.assign(_delta=deltas).groupby(
        "single_level_cv_random_state", sort=False
    ):
        values = rows["_delta"]
        per_seed.append(
            {
                "single_level_cv_random_state": int(seed),
                "reference_count": int(len(rows)),
                "positive_count": int(values.gt(0).sum()),
                "nonpositive_count": int(values.le(0).sum()),
                "mean": float(values.mean()),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "audit_status_counts": {
                    str(key): int(value)
                    for key, value in rows["audit_status"].value_counts().sort_index().items()
                },
            }
        )
    return {
        "row_count": int(len(candidate)),
        "positive_count": int(deltas.gt(0).sum()),
        "nonpositive_count": int(deltas.le(0).sum()),
        "mean": float(deltas.mean()),
        "minimum": float(deltas.min()),
        "maximum": float(deltas.max()),
        "per_seed": per_seed,
        "interpretation": (
            "bounded_selection_bias_diagnostic_only_not_nested_external_estimate_"
            "and_no_stage05_verdict_change"
        ),
    }


def register_evidence(candidate_path: Path, evidence: dict[str, Any], evidence_dir: Path) -> None:
    candidate_target, evidence_target = destination_paths(evidence_dir)
    require_absent_destinations(evidence_dir)
    shutil.copy2(candidate_path, candidate_target)
    evidence_target.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def finalize_completed_run(
    executed_output_dir: Path,
    evidence_dir: Path,
    executed_runner_sha256: str,
) -> dict[str, Any]:
    """Finalize a fit-complete run stopped only by the old CSV float parser."""
    executed_output = executed_output_dir.resolve()
    candidate_path = executed_output / CANDIDATE_FILENAME
    contract_path = executed_output / EXECUTION_CONTRACT_FILENAME
    if not candidate_path.is_file() or not contract_path.is_file():
        raise FileNotFoundError("Completed ST07_32 candidate or pre-fit contract is absent")
    require_absent_destinations(evidence_dir)
    contract_record = json.loads(contract_path.read_text(encoding="utf-8"))
    if (
        contract_record.get("task_id") != TASK_ID
        or contract_record.get("status") != "locked_before_first_fit"
    ):
        raise RuntimeError("Executed ST07_32 pre-fit contract identity differs")
    if executed_runner_sha256 != "e5f1e407272ee773534aaa9b6baf8dd735c58d5b4dc8e98cb753750ef3a09578":
        raise RuntimeError("Executed pre-fix runner SHA-256 differs from observed run")

    plan = read_csv_checked(
        PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
    )
    claims = read_csv_checked(
        PROJECT_ROOT / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
    )
    contract = build_non_nested_optimism_contract(plan, claims)
    model_space = read_csv_checked(
        PROJECT_ROOT
        / "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv"
    )
    parameter_grid, _ = build_hist_gradient_boosting_search_space(
        model_space, BASE_PROTOCOL_ID, contract.candidate_id
    )
    references = build_non_nested_reference_table(
        read_csv_checked(PROJECT_ROOT / "data_registry/openml_miniboone_nested_summary.csv"),
        read_csv_checked(
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv"
        ),
        read_csv_checked(
            PROJECT_ROOT
            / "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv"
        ),
        contract,
    )
    roundtripped = NonNestedOptimismBundle(
        audit=pd.read_csv(
            candidate_path,
            keep_default_na=False,
            float_precision="round_trip",
        ),
        reference_table=references,
        parameter_grid=parameter_grid,
    )
    validate_non_nested_optimism_bundle(roundtripped, contract)
    comparison = compare_candidate(candidate_path)
    signal = scientific_signal(candidate_path)
    protected_after = protected_hash_state()
    protected_exact = all(row["match"] for row in protected_after.values())
    fit_seconds = pd.to_numeric(roundtripped.audit["fit_seconds"], errors="raise")
    per_seed_fit_seconds = (
        roundtripped.audit[
            ["single_level_cv_random_state", "fit_seconds"]
        ]
        .drop_duplicates()
        .set_index("single_level_cv_random_state")["fit_seconds"]
        .astype(float)
        .to_dict()
    )
    technical_pass = (
        comparison["schema_exact"]
        and comparison["shape_exact"]
        and comparison["keys_and_order_exact"]
        and not comparison["structural_stop"]
        and comparison["class_a_exact"]
        and comparison["class_b_exact"]
        and comparison["class_c_valid"]
        and protected_exact
    )
    evidence = {
        "task_id": TASK_ID,
        "task_profile": "SCIENTIFIC_VALIDATION",
        "status": "pass" if technical_pass else "fail",
        "technical_status": "PASS" if technical_pass else "FAIL",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        "execution": {
            "pid": contract_record["pid"],
            "fresh_process": True,
            "isolated_output": True,
            "training_performed": True,
            "full_run_count": 1,
            "grid_search_count": 3,
            "cv_candidate_fold_fit_count": 480,
            "refit_count": 3,
            "fit_seconds_sum_across_three_grid_searches": float(
                sum(per_seed_fit_seconds.values())
            ),
            "fit_seconds_by_seed": {
                str(key): value for key, value in per_seed_fit_seconds.items()
            },
            "network_attempts": 0,
            "network_used": False,
            "canonical_golden_overwrites": 0,
            "claim_or_verdict_changed": False,
            "initial_short_invocation_fit_count": 0,
        },
        "execution_contract": contract_record,
        "execution_contract_sha256": sha256_file(contract_path),
        "execution_provenance": {
            "executed_runner_sha256": executed_runner_sha256,
            "current_runner_sha256": sha256_file(Path(__file__)),
            "post_fit_stop": "strict_relation_validator_after_default_csv_float_parse",
            "maximum_parser_induced_relation_delta": 2.922466955934677e-16,
            "repair": "pandas_float_precision_round_trip_then_same_exact_relation_validator",
            "tolerance_introduced": False,
            "refit_performed_for_repair": False,
            "control_flow_fact": (
                "The executed runner wrote candidate only after fit completion, zero "
                "network attempts, exact during-runtime controller equality, exact "
                "post-context restoration, and pre-roundtrip bundle validation."
            ),
        },
        "bundle_validation": {
            "passed_before_csv_roundtrip_in_executed_run": True,
            "passed_after_round_trip_parser_repair": True,
        },
        "comparison": comparison,
        "aggregate_verdict": {
            "structures_valid": (
                comparison["schema_exact"]
                and comparison["shape_exact"]
                and comparison["keys_and_order_exact"]
                and not comparison["structural_stop"]
            ),
            "class_a_exact": comparison["class_a_exact"],
            "class_b_exact": comparison["class_b_exact"],
            "class_c_valid": comparison["class_c_valid"],
            "protected_exact": protected_exact,
            "thread_limit_enforced_by_executed_control_flow": True,
            "openmp_exact_before_during_after_by_executed_control_flow": True,
            "runtime_restored_by_executed_control_flow": True,
            "verdict_rule": "pass_only_if_all_true_else_fail_without_causal_attribution",
        },
        "scientific_signal": signal,
        "protected_after": protected_after,
        "interpretation": {
            "allowed": (
                "One same-machine offline diagnostic reproduction of locked MiniBooNE "
                "ST05_07 under the predeclared BLAS=4 and OpenMP=12 condition."
            ),
            "prohibited": (
                "Historical runtime attribution, cross-environment reproducibility, "
                "universal model comparison, or causal attribution of any mismatch."
            ),
            "historical_openmp_provenance": "unknown_not_inferred",
            "historical_blas_provenance": "unknown_not_inferred",
            "tolerance": "none_predeclared_and_none_selected_after_result",
            "stage05_verdict_change": "prohibited_and_not_performed",
        },
    }
    register_evidence(candidate_path, evidence, evidence_dir)
    return evidence


def execute_preflight(
    cache_server_dir: Path, output_dir: Path, evidence_dir: Path
) -> dict[str, Any]:
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir, evidence_dir)
    contract_record = execution_contract(prepared, output)
    with threadpool_limits(limits=DIAGNOSTIC_BLAS_THREADS, user_api="blas"):
        during = controller_rows()
        verify_runtime(
            during,
            expected_blas_threads=DIAGNOSTIC_BLAS_THREADS,
            expected_identity=prepared["reference_blas_identity"],
        )
    after = controller_rows()
    if after != prepared["runtime_before"]:
        raise RuntimeError("Threadpool state was not exactly restored after preflight")
    return {
        "status": "pass",
        "technical_status": "PASS",
        "task_id": TASK_ID,
        "mode": "zero_fit_preflight_only",
        "execution_contract_sha256": sha256_file(
            output / EXECUTION_CONTRACT_FILENAME
        ),
        "dataset": contract_record["dataset"],
        "references_shape": list(prepared["references"].shape),
        "golden_shape": list(prepared["golden"].shape),
        "threadpool_during": during,
        "runtime_restored": True,
        "training_performed": False,
        "model_fit_count": 0,
        "network_used": False,
    }


def execute_full_run(
    cache_server_dir: Path, output_dir: Path, evidence_dir: Path
) -> dict[str, Any]:
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir, evidence_dir)
    contract_record = execution_contract(prepared, output)
    started = perf_counter()
    with deny_network_access() as training_network:
        with threadpool_limits(limits=DIAGNOSTIC_BLAS_THREADS, user_api="blas"):
            during = controller_rows()
            verify_runtime(
                during,
                expected_blas_threads=DIAGNOSTIC_BLAS_THREADS,
                expected_identity=prepared["reference_blas_identity"],
            )
            bundle = run_non_nested_optimism_probe(
                contract=prepared["contract"],
                candidate_bundle=prepared["candidate_bundle"],
                X=prepared["X"],
                y=prepared["y"],
                feature_names=prepared["feature_names"],
                parameter_grid=prepared["parameter_grid"],
                fixed_parameters=prepared["fixed_parameters"],
                reference_table=prepared["references"],
            )
            during_after_fit = controller_rows()
            if during_after_fit != during:
                raise RuntimeError("Threadpool state changed during ST07_32 fit")
    elapsed_seconds = perf_counter() - started
    after = controller_rows()
    if after != prepared["runtime_before"]:
        raise RuntimeError("Threadpool state was not exactly restored after ST07_32 fit")
    if training_network.attempts != 0:
        raise RuntimeError("Network attempt occurred during ST07_32 fit")

    validate_non_nested_optimism_bundle(bundle, prepared["contract"])
    candidate_path = output / CANDIDATE_FILENAME
    bundle.audit.to_csv(candidate_path, index=False)
    roundtripped = NonNestedOptimismBundle(
        audit=pd.read_csv(
            candidate_path,
            keep_default_na=False,
            float_precision="round_trip",
        ),
        reference_table=bundle.reference_table.copy(deep=True),
        parameter_grid={key: list(values) for key, values in bundle.parameter_grid.items()},
    )
    validate_non_nested_optimism_bundle(roundtripped, prepared["contract"])
    comparison = compare_candidate(candidate_path)
    signal = scientific_signal(candidate_path)
    protected_after = protected_hash_state()
    protected_exact = all(row["match"] for row in protected_after.values())
    technical_pass = (
        comparison["schema_exact"]
        and comparison["shape_exact"]
        and comparison["keys_and_order_exact"]
        and not comparison["structural_stop"]
        and comparison["class_a_exact"]
        and comparison["class_b_exact"]
        and comparison["class_c_valid"]
        and protected_exact
        and training_network.attempts == 0
        and after == prepared["runtime_before"]
    )
    evidence = {
        "task_id": TASK_ID,
        "task_profile": "SCIENTIFIC_VALIDATION",
        "status": "pass" if technical_pass else "fail",
        "technical_status": "PASS" if technical_pass else "FAIL",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        "execution": {
            "pid": os.getpid(),
            "fresh_process": True,
            "isolated_output": True,
            "elapsed_seconds": elapsed_seconds,
            "training_performed": True,
            "full_run_count": 1,
            "grid_search_count": 3,
            "cv_candidate_fold_fit_count": 480,
            "refit_count": 3,
            "network_attempts": training_network.attempts,
            "network_used": False,
            "canonical_golden_overwrites": 0,
            "claim_or_verdict_changed": False,
        },
        "execution_contract": contract_record,
        "execution_contract_sha256": sha256_file(
            output / EXECUTION_CONTRACT_FILENAME
        ),
        "threadpool_during_fit": during,
        "threadpool_after_fit": after,
        "bundle_validation": {
            "passed_before_csv_roundtrip": True,
            "passed_after_csv_roundtrip": True,
        },
        "comparison": comparison,
        "aggregate_verdict": {
            "structures_valid": (
                comparison["schema_exact"]
                and comparison["shape_exact"]
                and comparison["keys_and_order_exact"]
                and not comparison["structural_stop"]
            ),
            "class_a_exact": comparison["class_a_exact"],
            "class_b_exact": comparison["class_b_exact"],
            "class_c_valid": comparison["class_c_valid"],
            "protected_exact": protected_exact,
            "thread_limit_enforced": all(
                int(row["num_threads"]) == DIAGNOSTIC_BLAS_THREADS
                for row in api_rows(during, "blas")
            ),
            "openmp_exact_before_during_after": (
                api_rows(prepared["runtime_before"], "openmp")
                == api_rows(during, "openmp")
                == api_rows(after, "openmp")
            ),
            "runtime_restored": after == prepared["runtime_before"],
            "verdict_rule": "pass_only_if_all_true_else_fail_without_causal_attribution",
        },
        "scientific_signal": signal,
        "protected_after": protected_after,
        "interpretation": {
            "allowed": (
                "One same-machine offline diagnostic reproduction of locked MiniBooNE "
                "ST05_07 under the predeclared BLAS=4 and OpenMP=12 condition."
            ),
            "prohibited": (
                "Historical runtime attribution, cross-environment reproducibility, "
                "universal model comparison, or causal attribution of any mismatch."
            ),
            "historical_openmp_provenance": "unknown_not_inferred",
            "historical_blas_provenance": "unknown_not_inferred",
            "tolerance": "none_predeclared_and_none_selected_after_result",
            "stage05_verdict_change": "prohibited_and_not_performed",
        },
    }
    register_evidence(candidate_path, evidence, evidence_dir)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--full-run", action="store_true")
    mode.add_argument("--finalize-existing-run", action="store_true")
    parser.add_argument("--cache-server-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--executed-runner-sha256")
    args = parser.parse_args()
    try:
        if args.finalize_existing_run:
            if args.output_dir is None or args.executed_runner_sha256 is None:
                raise ValueError(
                    "--finalize-existing-run requires --output-dir and "
                    "--executed-runner-sha256"
                )
            result = finalize_completed_run(
                args.output_dir,
                args.evidence_dir,
                args.executed_runner_sha256,
            )
        elif args.preflight_only:
            if args.cache_server_dir is None or args.output_dir is None:
                raise ValueError("--preflight-only requires cache and output paths")
            result = execute_preflight(
                args.cache_server_dir, args.output_dir, args.evidence_dir
            )
        else:
            if args.cache_server_dir is None or args.output_dir is None:
                raise ValueError("--full-run requires cache and output paths")
            result = execute_full_run(
                args.cache_server_dir, args.output_dir, args.evidence_dir
            )
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "technical_status": "BLOCKED",
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
