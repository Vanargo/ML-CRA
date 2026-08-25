from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_info


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.datasets import load_miniboone_from_openml_cache  # noqa: E402
from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.model_spaces import (  # noqa: E402
    build_hist_gradient_boosting_search_space,
)
from mlcra.stress_tests import (  # noqa: E402
    SeedStabilityBundle,
    build_seed_stability_contract,
    build_seed_stability_control_estimators,
    run_seed_stability_grid,
    validate_seed_stability_bundle,
)


TASK_ID = (
    "ST07_25_stage05_seed_stability_full_miniboone_and_"
    "golden_diagnostic_validation"
)
BASE_PROTOCOL_ID = "miniboone_nested_cv_v01"
EVIDENCE_FILENAME = (
    "st07_25_stage05_seed_stability_full_validation_evidence_v01.json"
)
EXECUTION_CONTRACT_FILENAME = "st07_25_execution_contract_before_fit_v01.json"

ARTIFACT_SPECS = {
    "outer_scores": {
        "golden": "openml_miniboone_stage05_seed_stability_outer_scores.csv",
        "candidate": "st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv",
        "key": [
            "stress_test_id",
            "outer_random_state",
            "outer_split_number",
            "model_id",
        ],
        "class_b": [
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
        ],
        "class_c": ["fit_seconds", "predict_seconds"],
        "shape": [150, 43],
    },
    "selected_params": {
        "golden": "openml_miniboone_stage05_seed_stability_selected_params.csv",
        "candidate": "st07_25_stage05_seed_stability_candidate_selected_params_v01.csv",
        "key": [
            "stress_test_id",
            "outer_random_state",
            "outer_split_number",
            "model_id",
        ],
        "class_b": ["inner_best_average_precision"],
        "class_c": [],
        "shape": [50, 17],
    },
    "summary": {
        "golden": "openml_miniboone_stage05_seed_stability_summary.csv",
        "candidate": "st07_25_stage05_seed_stability_candidate_summary_v01.csv",
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
        "shape": [72, 22],
    },
}

PROTECTED_HASHES = {
    "notebooks/04_dataset_smoke_experiments.ipynb": "183fbd39fe84de4f3752d972e7ee003850e98776dc8c0d7b8a276d22f90347d1",
    "src/mlcra/nested_cv.py": "97d0630a8f3104472e843730da3e0fc1f6f731053c16cff8d14bb23560c2c7ea",
    "src/mlcra/stress_tests.py": "3c6bc8d1628712ee3ee6eaf70c5cb0d1efc40647ac3bd7008d1f04ed51bfba0d",
    "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
    "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
    "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
    "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
    "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
    "configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv": "88e4cc64f0d9b0ba8697b24db54224a5cdece9cece75d580c2ab6b433a873133",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_hash_state() -> dict[str, dict[str, Any]]:
    return {
        relative_path: {
            "expected_sha256": expected,
            "observed_sha256": sha256_file(PROJECT_ROOT / relative_path),
            "match": sha256_file(PROJECT_ROOT / relative_path) == expected,
        }
        for relative_path, expected in PROTECTED_HASHES.items()
    }


def require_safe_empty_output(output_dir: Path) -> Path:
    output = output_dir.resolve()
    root = PROJECT_ROOT.resolve()
    if output == root or root in output.parents:
        raise ValueError("ST07_25 output must be outside the project root")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("ST07_25 output directory must be empty")
    return output


def sanitized_threadpool_state() -> list[dict[str, Any]]:
    fields = (
        "user_api",
        "internal_api",
        "prefix",
        "version",
        "threading_layer",
        "architecture",
        "num_threads",
    )
    rows = []
    for raw in threadpool_info():
        row = {field: raw.get(field) for field in fields}
        row["library_filename"] = Path(str(raw.get("filepath") or "")).name
        rows.append(row)
    return sorted(
        rows,
        key=lambda row: (
            str(row["user_api"]),
            str(row["internal_api"]),
            str(row["library_filename"]),
        ),
    )


def package_versions() -> dict[str, str]:
    names = ("numpy", "pandas", "scipy", "scikit-learn", "openml", "threadpoolctl")
    return {name: importlib.metadata.version(name) for name in names}


def prepare_run(cache_server_dir: Path) -> dict[str, Any]:
    protected_before = protected_hash_state()
    if not all(row["match"] for row in protected_before.values()):
        raise RuntimeError("Protected ST07_25 source or scientific input hash differs")

    plan = read_csv_checked(
        PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
    )
    claims = read_csv_checked(
        PROJECT_ROOT / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
    )
    contract = build_seed_stability_contract(plan, claims)
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
    controls = build_seed_stability_control_estimators()
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
            "outer_random_states": list(contract.outer_random_states),
            "outer_n_splits": contract.outer_n_splits,
            "outer_n_repeats": contract.outer_n_repeats,
            "inner_n_splits": contract.inner_n_splits,
            "hgb_random_state": contract.hgb_random_state,
            "hgb_parameter_combinations": int(
                np.prod([len(values) for values in prepared["parameter_grid"].values()])
            ),
            "n_jobs": 1,
            "runtime_policy": "observe_current_environment_without_retrospective_enforcement",
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(),
            "threadpools_before_fit": sanitized_threadpool_state(),
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
        "protected_before": prepared["protected_before"],
    }
    path = output / EXECUTION_CONTRACT_FILENAME
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def write_candidate_bundle(bundle: SeedStabilityBundle, output: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for artifact_id, frame in (
        ("outer_scores", bundle.outer_scores),
        ("selected_params", bundle.selected_params),
        ("summary", bundle.summary),
    ):
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
        valid = values.notna() & np.isfinite(values) & values.ge(0.0)
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


def scientific_signal(summary_path: Path) -> dict[str, Any]:
    summary = pd.read_csv(summary_path)
    primary = summary[
        summary["comparison_model_id"].eq("logistic_regression")
        & summary["metric_name"].eq("average_precision")
        & summary["summary_scope"].eq("single_outer_random_state")
    ].copy()
    per_seed = []
    for row in primary.itertuples(index=False):
        per_seed.append(
            {
                "outer_random_state": int(row.outer_random_state),
                "advantage_mean": float(row.advantage_mean),
                "positive_blocks": int(row.candidate_positive_blocks),
                "negative_blocks": int(row.candidate_negative_blocks),
                "majority_positive": int(row.candidate_positive_blocks) > int(row.n_blocks) / 2,
                "mean_positive": float(row.advantage_mean) > 0.0,
            }
        )
    return {
        "registered_primary_signal_pass": len(per_seed) == 5
        and all(row["majority_positive"] and row["mean_positive"] for row in per_seed),
        "per_seed": per_seed,
        "secondary_strong_conflict_threshold": "not_numerically_registered_not_invented",
    }


def register_evidence(
    candidate_paths: dict[str, Path],
    evidence: dict[str, Any],
    evidence_dir: Path,
) -> None:
    destination = evidence_dir.resolve()
    if destination != (PROJECT_ROOT / "data_registry").resolve():
        raise ValueError("ST07_25 evidence-dir must be the project data_registry")
    targets = [destination / path.name for path in candidate_paths.values()]
    targets.append(destination / EVIDENCE_FILENAME)
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise FileExistsError(f"ST07_25 evidence targets already exist: {existing}")
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
    return {
        "status": "pass",
        "task_id": TASK_ID,
        "mode": "preflight_only",
        "execution_contract_sha256": sha256_file(
            output / EXECUTION_CONTRACT_FILENAME
        ),
        "dataset": contract_record["dataset"],
        "training_performed": False,
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
    bundle = run_seed_stability_grid(
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
    validate_seed_stability_bundle(bundle, prepared["contract"])
    candidate_paths = write_candidate_bundle(bundle, output)
    roundtripped = SeedStabilityBundle(
        outer_scores=pd.read_csv(candidate_paths["outer_scores"]),
        selected_params=pd.read_csv(candidate_paths["selected_params"]),
        summary=pd.read_csv(candidate_paths["summary"]),
    )
    validate_seed_stability_bundle(roundtripped, prepared["contract"])
    comparisons = {
        artifact_id: compare_artifact(artifact_id, path)
        for artifact_id, path in candidate_paths.items()
    }
    protected_after = protected_hash_state()
    class_a_exact = all(row["class_a_exact"] for row in comparisons.values())
    class_b_exact = all(row["class_b_exact"] for row in comparisons.values())
    class_c_valid = all(row["class_c_valid"] for row in comparisons.values())
    structures_valid = all(
        row["schema_exact"] and row["shape_exact"] and not row["structural_stop"]
        for row in comparisons.values()
    )
    protected_exact = all(row["match"] for row in protected_after.values())
    signal = scientific_signal(candidate_paths["summary"])
    technical_pass = (
        structures_valid
        and class_a_exact
        and class_b_exact
        and class_c_valid
        and protected_exact
        and signal["registered_primary_signal_pass"]
        and prepared["cache_evidence"].network_attempts == 0
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
            "network_attempts": prepared["cache_evidence"].network_attempts,
            "network_used": False,
            "canonical_golden_overwrites": 0,
            "claim_or_verdict_changed": False,
        },
        "execution_contract": contract_record,
        "execution_contract_sha256": sha256_file(
            output / EXECUTION_CONTRACT_FILENAME
        ),
        "threadpools_after_fit": sanitized_threadpool_state(),
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
            "registered_primary_signal_pass": signal[
                "registered_primary_signal_pass"
            ],
            "verdict_rule": "pass_only_if_all_true_else_fail_without_causal_attribution",
        },
        "scientific_signal": signal,
        "protected_after": protected_after,
        "interpretation": {
            "allowed": "One current-environment offline diagnostic validation of the locked MiniBooNE ST05_02 modular computation.",
            "prohibited": "Cross-environment reproducibility, universal model superiority, or causal attribution of any mismatch without separate evidence.",
            "historical_backend_thread_provenance": "unknown_not_inferred",
            "tolerance": "none_predeclared_and_none_selected_after_result",
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
