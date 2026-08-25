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
from threadpoolctl import threadpool_limits


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.datasets import load_miniboone_from_openml_cache  # noqa: E402
from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.model_spaces import (  # noqa: E402
    build_hist_gradient_boosting_search_space,
)
from mlcra.numeric_runtime import capture_blas_runtime  # noqa: E402
from mlcra.stress_tests import (  # noqa: E402
    Split10x1Bundle,
    build_split_10x1_contract,
    build_split_10x1_control_estimators,
    run_split_10x1_grid,
    validate_split_10x1_bundle,
)


TASK_ID = (
    "ST07_29_stage05_split_10x1_full_miniboone_and_"
    "golden_diagnostic_validation"
)
BASE_PROTOCOL_ID = "miniboone_nested_cv_v01"
DIAGNOSTIC_BLAS_THREADS = 4
EVIDENCE_FILENAME = (
    "st07_29_stage05_split_10x1_full_validation_evidence_v01.json"
)
EXECUTION_CONTRACT_FILENAME = "st07_29_execution_contract_before_fit_v01.json"
ST0726_EVIDENCE = (
    "data_registry/"
    "st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json"
)

ARTIFACT_SPECS = {
    "outer_scores": {
        "golden": "openml_miniboone_stage05_split_10x1_outer_scores.csv",
        "candidate": "st07_29_stage05_split_10x1_candidate_outer_scores_v01.csv",
        "key": [
            "stress_test_id",
            "outer_random_state",
            "outer_split_number",
            "model_id",
        ],
        "class_b": [
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
        ],
        "class_c": ["fit_seconds", "predict_seconds"],
        "shape": [90, 43],
    },
    "summary": {
        "golden": "openml_miniboone_stage05_split_10x1_summary.csv",
        "candidate": "st07_29_stage05_split_10x1_candidate_summary_v01.csv",
        "key": [
            "stress_test_id",
            "comparison_model_id",
            "metric_name",
            "summary_scope",
            "outer_random_state",
        ],
        "class_b": [
            "advantage_mean",
            "advantage_std_population",
            "advantage_min",
            "advantage_max",
        ],
        "class_c": [],
        "shape": [48, 22],
    },
}

PROTECTED_HASHES = {
    "notebooks/04_dataset_smoke_experiments.ipynb": "dc972ba6dcad6796016aa7714ef207c818166f7f0d24787ac5e5307f3c95ef1a",
    "src/mlcra/datasets.py": "1a60d860d8073af2e9b9b5143b4817918cc614eb65c0ab17343713cfecfc154b",
    "src/mlcra/io.py": "460a4ebe6ad523c2d07650332fe6d03422d4544468ed9d47874edaa590dd4be0",
    "src/mlcra/metrics.py": "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3",
    "src/mlcra/model_spaces.py": "9f726c03394817b0ffb00d11a81ccf2234a1809cab1d41ca0ab118ed9556140b",
    "src/mlcra/nested_cv.py": "86275f03c92475850932169667d2020cc0ff11e97c3d8a57b679c51ff3095727",
    "src/mlcra/numeric_runtime.py": "4f09dbe5b16dc42497dd00c29cb70695cdfb802d42a798570f19e08653003086",
    "src/mlcra/stress_tests.py": "3f07872fc96d44c2cfb166fd811503a4eddce49a9eea01d7ad6d4bebda4c940b",
    "src/mlcra/validation.py": "2bed7566811af6c342b9a70a8e8933479248fc6e7ee4b9983da39d1c0279ffff",
    "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
    "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
    "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
    "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv": "2514b1dc58c40bc162c4858f5fbef3a650efe60f323bd4ac1df4710f13c88970",
    "data_registry/openml_miniboone_stage05_split_10x1_summary.csv": "1e940e50192c37ab3312f9534fd4846a5eedefa23b831e00c032c51bc1103c18",
    ST0726_EVIDENCE: "e07ad5bec329903266eff66436fa9d2e5045de3fa707e14a13da38b89c52bc44",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_hash_state() -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for relative_path, expected in PROTECTED_HASHES.items():
        observed = sha256_file(PROJECT_ROOT / relative_path)
        state[relative_path] = {
            "expected_sha256": expected,
            "observed_sha256": observed,
            "match": observed == expected,
        }
    return state


def require_safe_empty_output(output_dir: Path) -> Path:
    output = output_dir.resolve()
    root = PROJECT_ROOT.resolve()
    if output == root or root in output.parents:
        raise ValueError("ST07_29 output must be outside the project root")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("ST07_29 output directory must be empty")
    return output


def runtime_rows() -> list[dict[str, Any]]:
    return [
        {
            "internal_api": runtime.identity.internal_api,
            "prefix": runtime.identity.prefix,
            "version": runtime.identity.version,
            "threading_layer": runtime.identity.threading_layer,
            "architecture": runtime.identity.architecture,
            "library_filename": runtime.identity.library_filename,
            "num_threads": runtime.num_threads,
        }
        for runtime in capture_blas_runtime()
    ]


def runtime_identities(rows: list[dict[str, Any]]) -> list[tuple[str, ...]]:
    fields = (
        "internal_api",
        "prefix",
        "version",
        "threading_layer",
        "architecture",
        "library_filename",
    )
    return sorted(tuple(str(row[field]) for field in fields) for row in rows)


def reference_backend_identities() -> list[tuple[str, ...]]:
    evidence = json.loads(
        (PROJECT_ROOT / ST0726_EVIDENCE).read_text(encoding="utf-8")
    )
    return runtime_identities(
        evidence["execution_contract"]["environment"]["blas_before"]
    )


def verify_thread_condition(condition: int) -> list[dict[str, Any]]:
    rows = runtime_rows()
    if not rows or any(int(row["num_threads"]) != condition for row in rows):
        raise RuntimeError(
            f"BLAS thread condition not enforced: expected={condition}; observed={rows}"
        )
    return rows


def verify_runtime_restored(before: list[dict[str, Any]]) -> list[dict[str, Any]]:
    after = runtime_rows()
    if after != before:
        raise RuntimeError(f"BLAS runtime not restored: before={before}; after={after}")
    return after


def package_versions() -> dict[str, str]:
    names = ("numpy", "pandas", "scipy", "scikit-learn", "openml", "threadpoolctl")
    return {name: importlib.metadata.version(name) for name in names}


def prepare_run(cache_server_dir: Path) -> dict[str, Any]:
    protected_before = protected_hash_state()
    if not all(row["match"] for row in protected_before.values()):
        raise RuntimeError("Protected ST07_29 source or scientific input hash differs")
    plan = read_csv_checked(
        PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
    )
    claims = read_csv_checked(
        PROJECT_ROOT / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
    )
    contract = build_split_10x1_contract(plan, claims)
    model_space = read_csv_checked(
        PROJECT_ROOT
        / "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv"
    )
    parameter_grid, fixed_parameters = build_hist_gradient_boosting_search_space(
        model_space,
        BASE_PROTOCOL_ID,
        contract.candidate_id,
    )
    candidate_bundle, X, y, feature_names, cache_evidence = (
        load_miniboone_from_openml_cache(cache_server_dir)
    )
    controls = build_split_10x1_control_estimators()
    if tuple(controls) != ("dummy_prior", "logistic_regression"):
        raise RuntimeError("Registered control estimator order changed")
    runtime_before = runtime_rows()
    backend_exact = runtime_identities(runtime_before) == reference_backend_identities()
    if not backend_exact:
        raise RuntimeError("Current BLAS backend identity differs from ST07_26")
    if (
        len(X) != 130064
        or len(feature_names) != 50
        or cache_evidence.target_false_count != 93565
        or cache_evidence.target_true_count != 36499
        or cache_evidence.network_attempts != 0
    ):
        raise RuntimeError("Offline MiniBooNE dataset contract differs")
    return {
        "protected_before": protected_before,
        "contract": contract,
        "parameter_grid": parameter_grid,
        "fixed_parameters": fixed_parameters,
        "candidate_bundle": candidate_bundle,
        "X": X,
        "y": y,
        "feature_names": feature_names,
        "cache_evidence": cache_evidence,
        "controls": controls,
        "runtime_before": runtime_before,
        "backend_identity_exact": backend_exact,
    }


def execution_contract(prepared: dict[str, Any], output: Path) -> dict[str, Any]:
    contract = prepared["contract"]
    cache = prepared["cache_evidence"]
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
            "nested_protocol_id": contract.nested_protocol_id,
            "protocol_variant_id": contract.protocol_variant_id,
            "outer_random_states": list(contract.outer_random_states),
            "outer_n_splits": contract.outer_n_splits,
            "outer_n_repeats": contract.outer_n_repeats,
            "inner_n_splits": contract.inner_n_splits,
            "inner_random_state_policy": "equals_outer_random_state",
            "hgb_random_state": contract.hgb_random_state,
            "models_in_order": [
                "hist_gradient_boosting",
                "dummy_prior",
                "logistic_regression",
            ],
            "hgb_parameter_combinations": int(
                np.prod([len(values) for values in prepared["parameter_grid"].values()])
            ),
            "n_jobs": 1,
            "full_run_count": 1,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(),
            "blas_before": prepared["runtime_before"],
            "backend_identity_exact_to_st07_26": prepared[
                "backend_identity_exact"
            ],
            "diagnostic_blas_threads": DIAGNOSTIC_BLAS_THREADS,
            "historical_backend_thread_provenance": "unknown_not_inferred",
        },
        "comparison_policy": {
            "class_a": "exact_after_csv_roundtrip",
            "class_b": "exact_after_csv_roundtrip_no_tolerance",
            "class_c": "numeric_finite_nonnegative_excluded_from_equality",
            "mismatch_verdict": "fail_without_causal_attribution",
            "cross_environment_reproducibility_claim": "prohibited",
            "post_result_tolerance_selection": "prohibited",
        },
        "bounded_signal_policy": {
            "primary_average_precision_positive_block_fraction_min": 0.95,
            "primary_average_precision_mean_advantage_min": 0.03,
            "primary_average_precision_empirical_q05_min_exclusive": 0.01,
            "per_seed_primary_mean_and_majority_positive": True,
            "secondary_metrics_mean_and_majority_positive": True,
            "effect_on_stage05_verdict": "none_diagnostic_only",
        },
        "protected_before": prepared["protected_before"],
    }
    path = output / EXECUTION_CONTRACT_FILENAME
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def write_candidate_bundle(bundle: Split10x1Bundle, output: Path) -> dict[str, Path]:
    frames = {
        "outer_scores": bundle.outer_scores,
        "summary": bundle.summary,
    }
    paths: dict[str, Path] = {}
    for artifact_id, frame in frames.items():
        path = output / ARTIFACT_SPECS[artifact_id]["candidate"]
        frame.to_csv(path, index=False)
        paths[artifact_id] = path
    return paths


def first_mismatch(
    candidate: pd.DataFrame,
    golden: pd.DataFrame,
    mask: pd.DataFrame,
    columns: list[str],
    key_columns: list[str],
) -> dict[str, Any] | None:
    for row_index in range(len(candidate)):
        for column in columns:
            if bool(mask.at[row_index, column]):
                return {
                    "row_index": row_index,
                    "key": {
                        key: str(candidate.at[row_index, key]) for key in key_columns
                    },
                    "column": column,
                    "candidate": str(candidate.at[row_index, column]),
                    "golden": str(golden.at[row_index, column]),
                }
    return None


def numeric_delta_diagnostics(
    candidate: pd.DataFrame,
    golden: pd.DataFrame,
    columns: list[str],
) -> dict[str, dict[str, Any]]:
    diagnostics: dict[str, dict[str, Any]] = {}
    for column in columns:
        candidate_values = pd.to_numeric(candidate[column], errors="coerce")
        golden_values = pd.to_numeric(golden[column], errors="coerce")
        comparable = candidate_values.notna() & golden_values.notna()
        deltas = (candidate_values[comparable] - golden_values[comparable]).abs()
        diagnostics[column] = {
            "comparable_cells": int(comparable.sum()),
            "non_numeric_or_blank_pairs": int((~comparable).sum()),
            "mismatch_cells": int(candidate[column].ne(golden[column]).sum()),
            "max_absolute_delta": float(deltas.max()) if len(deltas) else None,
        }
    return diagnostics


def compare_artifact(artifact_id: str, candidate_path: Path) -> dict[str, Any]:
    spec = ARTIFACT_SPECS[artifact_id]
    golden_path = PROJECT_ROOT / "data_registry" / spec["golden"]
    candidate = pd.read_csv(candidate_path, dtype=str, keep_default_na=False)
    golden = pd.read_csv(golden_path, dtype=str, keep_default_na=False)
    schema_exact = list(candidate.columns) == list(golden.columns)
    shape_exact = list(candidate.shape) == spec["shape"] == list(golden.shape)
    if not schema_exact or not shape_exact:
        return {
            "artifact_id": artifact_id,
            "schema_exact": schema_exact,
            "shape_exact": shape_exact,
            "candidate_shape": list(candidate.shape),
            "golden_shape": list(golden.shape),
            "class_a_exact": False,
            "class_b_exact": False,
            "class_c_valid": False,
            "structural_stop": True,
        }

    class_b = list(spec["class_b"])
    class_c = list(spec["class_c"])
    class_a = [
        column for column in candidate.columns if column not in set(class_b + class_c)
    ]
    mismatch = candidate.ne(golden)
    class_a_mismatch = mismatch[class_a]
    class_b_mismatch = mismatch[class_b]
    timing_valid = True
    timing_diagnostics: dict[str, dict[str, Any]] = {}
    for column in class_c:
        values = pd.to_numeric(candidate[column], errors="coerce")
        valid = values.notna() & values.map(math.isfinite) & values.ge(0.0)
        timing_diagnostics[column] = {
            "valid_cells": int(valid.sum()),
            "total_cells": int(len(values)),
            "minimum": float(values.min()) if values.notna().any() else None,
            "maximum": float(values.max()) if values.notna().any() else None,
        }
        timing_valid = timing_valid and bool(valid.all())

    return {
        "artifact_id": artifact_id,
        "candidate_filename": candidate_path.name,
        "candidate_sha256": sha256_file(candidate_path),
        "golden_filename": golden_path.name,
        "golden_sha256": sha256_file(golden_path),
        "schema_exact": schema_exact,
        "shape_exact": shape_exact,
        "candidate_shape": list(candidate.shape),
        "golden_shape": list(golden.shape),
        "class_a_columns": class_a,
        "class_a_comparable_cells": int(candidate[class_a].size),
        "class_a_mismatch_cells": int(class_a_mismatch.to_numpy().sum()),
        "class_a_exact": not bool(class_a_mismatch.to_numpy().any()),
        "class_a_first_mismatch": first_mismatch(
            candidate, golden, class_a_mismatch, class_a, spec["key"]
        ),
        "class_b_columns": class_b,
        "class_b_comparable_cells": int(candidate[class_b].size),
        "class_b_mismatch_cells": int(class_b_mismatch.to_numpy().sum()),
        "class_b_exact": not bool(class_b_mismatch.to_numpy().any()),
        "class_b_first_mismatch": first_mismatch(
            candidate, golden, class_b_mismatch, class_b, spec["key"]
        ),
        "class_b_numeric_deltas": numeric_delta_diagnostics(
            candidate, golden, class_b
        ),
        "class_c_columns": class_c,
        "class_c_valid": timing_valid,
        "class_c_diagnostics": timing_diagnostics,
        "structural_stop": False,
    }


def scientific_signal(outer_path: Path, summary_path: Path) -> dict[str, Any]:
    outer = pd.read_csv(outer_path)
    summary = pd.read_csv(summary_path)
    key = [
        "outer_random_state",
        "outer_split_number",
        "outer_repeat_number",
        "outer_fold_number",
    ]
    hgb = outer[outer["model_id"].eq("hist_gradient_boosting")]
    logistic = outer[outer["model_id"].eq("logistic_regression")]
    paired = hgb.merge(logistic, on=key, suffixes=("_hgb", "_lr"), validate="one_to_one")
    primary_advantage = (
        paired["average_precision_hgb"] - paired["average_precision_lr"]
    )
    per_seed = []
    for seed, group in paired.assign(primary_advantage=primary_advantage).groupby(
        "outer_random_state"
    ):
        values = group["primary_advantage"]
        per_seed.append(
            {
                "outer_random_state": int(seed),
                "n_blocks": int(len(values)),
                "advantage_mean": float(values.mean()),
                "positive_blocks": int(values.gt(0.0).sum()),
                "mean_positive": bool(values.mean() > 0.0),
                "majority_positive": bool(values.gt(0.0).sum() > len(values) / 2),
            }
        )
    secondary = summary[
        summary["comparison_model_id"].eq("logistic_regression")
        & summary["summary_scope"].eq("all_outer_random_states")
        & ~summary["metric_name"].eq("average_precision")
    ]
    secondary_rows = [
        {
            "metric_name": str(row.metric_name),
            "advantage_mean": float(row.advantage_mean),
            "positive_blocks": int(row.candidate_positive_blocks),
            "n_blocks": int(row.n_blocks),
            "mean_positive": float(row.advantage_mean) > 0.0,
            "majority_positive": int(row.candidate_positive_blocks)
            > int(row.n_blocks) / 2,
        }
        for row in secondary.itertuples(index=False)
    ]
    q05 = float(np.quantile(primary_advantage.to_numpy(float), 0.05))
    positive_fraction = float(primary_advantage.gt(0.0).mean())
    mean_advantage = float(primary_advantage.mean())
    checks = {
        "primary_rows_30": len(primary_advantage) == 30,
        "primary_positive_fraction_at_least_0_95": positive_fraction >= 0.95,
        "primary_mean_at_least_0_03": mean_advantage >= 0.03,
        "primary_empirical_q05_greater_than_0_01": q05 > 0.01,
        "three_seed_means_and_majorities_positive": len(per_seed) == 3
        and all(row["mean_positive"] and row["majority_positive"] for row in per_seed),
        "five_secondary_means_and_majorities_positive": len(secondary_rows) == 5
        and all(
            row["mean_positive"] and row["majority_positive"]
            for row in secondary_rows
        ),
    }
    return {
        "registered_bounded_signal_pass": all(checks.values()),
        "checks": checks,
        "primary_average_precision": {
            "n_blocks": len(primary_advantage),
            "positive_blocks": int(primary_advantage.gt(0.0).sum()),
            "positive_fraction": positive_fraction,
            "advantage_mean": mean_advantage,
            "empirical_q05": q05,
            "minimum": float(primary_advantage.min()),
            "maximum": float(primary_advantage.max()),
        },
        "per_seed": per_seed,
        "secondary_metrics": secondary_rows,
        "interpretation": "bounded_diagnostic_signal_only_no_stage05_verdict_change",
    }


def register_evidence(
    candidate_paths: dict[str, Path],
    evidence: dict[str, Any],
    evidence_dir: Path,
) -> None:
    destination = evidence_dir.resolve()
    if destination != (PROJECT_ROOT / "data_registry").resolve():
        raise ValueError("ST07_29 evidence-dir must be the project data_registry")
    targets = [destination / path.name for path in candidate_paths.values()]
    targets.append(destination / EVIDENCE_FILENAME)
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise FileExistsError(f"ST07_29 evidence targets already exist: {existing}")
    for source, target in zip(candidate_paths.values(), targets[:-1], strict=True):
        shutil.copy2(source, target)
    targets[-1].write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def execute_preflight(cache_server_dir: Path, output_dir: Path) -> dict[str, Any]:
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir)
    contract_record = execution_contract(prepared, output)
    with threadpool_limits(limits=DIAGNOSTIC_BLAS_THREADS, user_api="blas"):
        during = verify_thread_condition(DIAGNOSTIC_BLAS_THREADS)
    after = verify_runtime_restored(prepared["runtime_before"])
    return {
        "status": "pass",
        "technical_status": "PASS",
        "task_id": TASK_ID,
        "mode": "preflight_only",
        "execution_contract_sha256": sha256_file(
            output / EXECUTION_CONTRACT_FILENAME
        ),
        "dataset": contract_record["dataset"],
        "backend_identity_exact_to_st07_26": prepared["backend_identity_exact"],
        "blas_during": during,
        "runtime_restored": after == prepared["runtime_before"],
        "training_performed": False,
        "model_fit_count": 0,
        "network_used": False,
    }


def execute_full_run(
    cache_server_dir: Path,
    output_dir: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir)
    contract_record = execution_contract(prepared, output)
    started = perf_counter()
    with threadpool_limits(limits=DIAGNOSTIC_BLAS_THREADS, user_api="blas"):
        blas_during = verify_thread_condition(DIAGNOSTIC_BLAS_THREADS)
        bundle = run_split_10x1_grid(
            contract=prepared["contract"],
            candidate_bundle=prepared["candidate_bundle"],
            X=prepared["X"],
            y=prepared["y"],
            feature_names=prepared["feature_names"],
            parameter_grid=prepared["parameter_grid"],
            fixed_parameters=prepared["fixed_parameters"],
            control_estimators=prepared["controls"],
        )
    elapsed_seconds = perf_counter() - started
    runtime_after = verify_runtime_restored(prepared["runtime_before"])
    validate_split_10x1_bundle(bundle, prepared["contract"])
    candidate_paths = write_candidate_bundle(bundle, output)
    roundtripped = Split10x1Bundle(
        outer_scores=pd.read_csv(candidate_paths["outer_scores"], keep_default_na=False),
        summary=pd.read_csv(candidate_paths["summary"], keep_default_na=False),
    )
    validate_split_10x1_bundle(roundtripped, prepared["contract"])
    comparisons = {
        artifact_id: compare_artifact(artifact_id, path)
        for artifact_id, path in candidate_paths.items()
    }
    signal = scientific_signal(
        candidate_paths["outer_scores"], candidate_paths["summary"]
    )
    protected_after = protected_hash_state()
    structures_valid = all(
        row["schema_exact"] and row["shape_exact"] and not row["structural_stop"]
        for row in comparisons.values()
    )
    class_a_exact = all(row["class_a_exact"] for row in comparisons.values())
    class_b_exact = all(row["class_b_exact"] for row in comparisons.values())
    class_c_valid = all(row["class_c_valid"] for row in comparisons.values())
    protected_exact = all(row["match"] for row in protected_after.values())
    runtime_restored = runtime_after == prepared["runtime_before"]
    technical_pass = (
        structures_valid
        and class_a_exact
        and class_b_exact
        and class_c_valid
        and protected_exact
        and signal["registered_bounded_signal_pass"]
        and prepared["cache_evidence"].network_attempts == 0
        and prepared["backend_identity_exact"]
        and runtime_restored
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
            "hgb_outer_tuning_blocks": 30,
            "control_outer_fit_count": 60,
            "outer_model_rows": 90,
            "network_attempts": prepared["cache_evidence"].network_attempts,
            "network_used": False,
            "canonical_golden_overwrites": 0,
            "claim_or_verdict_changed": False,
        },
        "execution_contract": contract_record,
        "execution_contract_sha256": sha256_file(
            output / EXECUTION_CONTRACT_FILENAME
        ),
        "blas_during_fit": blas_during,
        "blas_after_fit": runtime_after,
        "bundle_validation": {
            "passed_before_csv_roundtrip": True,
            "passed_after_csv_roundtrip": True,
        },
        "comparisons": comparisons,
        "aggregate_verdict": {
            "structures_valid": structures_valid,
            "class_a_exact": class_a_exact,
            "class_b_exact": class_b_exact,
            "class_c_valid": class_c_valid,
            "protected_exact": protected_exact,
            "backend_identity_exact_to_st07_26": prepared[
                "backend_identity_exact"
            ],
            "thread_limit_enforced": all(
                int(row["num_threads"]) == DIAGNOSTIC_BLAS_THREADS
                for row in blas_during
            ),
            "runtime_restored": runtime_restored,
            "registered_bounded_signal_pass": signal[
                "registered_bounded_signal_pass"
            ],
            "verdict_rule": "pass_only_if_all_true_else_fail_without_causal_attribution",
        },
        "scientific_signal": signal,
        "protected_after": protected_after,
        "interpretation": {
            "allowed": "One same-machine offline diagnostic reproduction of locked MiniBooNE ST05_03a at predeclared BLAS=4.",
            "prohibited": "Historical BLAS=4 attribution, cross-environment reproducibility, universal model superiority, or causal attribution of any mismatch.",
            "historical_backend_thread_provenance": "unknown_not_inferred",
            "tolerance": "none_predeclared_and_none_selected_after_result",
            "stage05_verdict_change": "prohibited_and_not_performed",
        },
    }
    register_evidence(candidate_paths, evidence, evidence_dir)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--full-run", action="store_true")
    parser.add_argument("--cache-server-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.preflight_only:
            result = execute_preflight(args.cache_server_dir, args.output_dir)
        else:
            if args.evidence_dir is None:
                raise ValueError("--full-run requires --evidence-dir")
            result = execute_full_run(
                args.cache_server_dir,
                args.output_dir,
                args.evidence_dir,
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
