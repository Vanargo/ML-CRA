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
from mlcra.nested_cv import (  # noqa: E402
    build_outer_splitter,
    fit_control_estimator_on_outer_block,
)
from mlcra.numeric_runtime import capture_blas_runtime  # noqa: E402
from mlcra.stress_tests import (  # noqa: E402
    build_seed_stability_contract,
    build_seed_stability_control_estimators,
)


TASK_ID = (
    "ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_"
    "causal_diagnostic_validation"
)
BASE_PROTOCOL_ID = "miniboone_nested_cv_v01"
THREAD_CONDITIONS = (4, 12)
MODEL_ID = "logistic_regression"
ROW_STATUS = "st07_26_same_machine_causal_diagnostic"
INTERPRETATION = (
    "Разрешён только same-machine причинно-диагностический вывод о влиянии "
    "числа BLAS-потоков на расхождение ST05_02 logistic regression."
)
SCORES_FILENAME = (
    "st07_26_stage05_seed_stability_logistic_blas_diagnostic_scores_v01.csv"
)
EVIDENCE_FILENAME = (
    "st07_26_stage05_seed_stability_logistic_blas_diagnostic_evidence_v01.json"
)
EXECUTION_CONTRACT_FILENAME = "st07_26_execution_contract_before_fit_v01.json"
HISTORICAL_REFERENCE = "openml_miniboone_stage05_seed_stability_outer_scores.csv"
ST0725_REFERENCE = "st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv"
METRIC_COLUMNS = (
    "roc_auc",
    "average_precision",
    "pr_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
)
SPLIT_INPUT_COLUMNS = (
    "outer_random_state",
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
    "outer_cv_n_splits",
    "outer_cv_n_repeats",
    "n_train",
    "n_test",
    "train_positive_share",
    "test_positive_share",
)
SCORE_COLUMNS = (
    "task_id",
    "stress_test_id",
    "claim_id",
    "candidate_id",
    "thread_condition",
    "outer_random_state",
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
    "outer_cv_n_splits",
    "outer_cv_n_repeats",
    "model_id",
    "model_role",
    "selected_parameter_set_id",
    "feature_policy_id",
    "n_train",
    "n_test",
    "train_positive_share",
    "test_positive_share",
    *METRIC_COLUMNS,
    "fit_seconds",
    "predict_seconds",
    "reference_artifact",
    "metric_cells_total",
    "exact_reference_metric_cells",
    "exact_after_csv_roundtrip",
    "row_status",
    "interpretation_allowed_ru",
)

PROTECTED_HASHES = {
    "notebooks/04_dataset_smoke_experiments.ipynb": "183fbd39fe84de4f3752d972e7ee003850e98776dc8c0d7b8a276d22f90347d1",
    "src/mlcra/datasets.py": "1a60d860d8073af2e9b9b5143b4817918cc614eb65c0ab17343713cfecfc154b",
    "src/mlcra/metrics.py": "6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3",
    "src/mlcra/nested_cv.py": "97d0630a8f3104472e843730da3e0fc1f6f731053c16cff8d14bb23560c2c7ea",
    "src/mlcra/numeric_runtime.py": "4f09dbe5b16dc42497dd00c29cb70695cdfb802d42a798570f19e08653003086",
    "src/mlcra/stress_tests.py": "3c6bc8d1628712ee3ee6eaf70c5cb0d1efc40647ac3bd7008d1f04ed51bfba0d",
    "configs/stress_tests/miniboone_stress_test_plan_v01.csv": "214661b40941caa8d68ce12b366b971cfdcc166a5a92b2720dfdb1abdf11087d",
    "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv": "d3fb1096c20ac5112d90a42af4dfde30aa30c5db22debdda6b8a5b7f6309bb49",
    "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv": "2a98546d52e1395b6be264d89d90ddb40c49332398d94f275f3633e676045687",
    "data_registry/openml_miniboone_stage05_seed_stability_selected_params.csv": "c9896f843b787c9211269887106713b4a4a8f37b61482773aedd81f55f9fd148",
    "data_registry/openml_miniboone_stage05_seed_stability_summary.csv": "a553816194654b58371687a4760394fa535b0923badfe6c9cf64a5f4e00974b5",
    "data_registry/st07_25_stage05_seed_stability_candidate_outer_scores_v01.csv": "30ae06d3883d478c1815aaeb4a6864fc03cf80c523820cb99b2e423c4bd218af",
    "data_registry/st07_25_stage05_seed_stability_candidate_selected_params_v01.csv": "79174fcc98c45bed58ec7670e420d85b306fc5b9c6035cb3c322e4200e5d651e",
    "data_registry/st07_25_stage05_seed_stability_candidate_summary_v01.csv": "f320b1e6f002123ff0c55a912c8141195e2b377948bf3dfebe5e14fb0fc0d852",
    "data_registry/st07_25_stage05_seed_stability_full_validation_evidence_v01.json": "27cf784078c8d6897c874fa4e55b928f40725610cc57aebb9f3fb4b2335ad09a",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_hash_state() -> dict[str, dict[str, Any]]:
    return {
        path: {
            "expected_sha256": expected,
            "observed_sha256": sha256_file(PROJECT_ROOT / path),
            "match": sha256_file(PROJECT_ROOT / path) == expected,
        }
        for path, expected in PROTECTED_HASHES.items()
    }


def require_safe_empty_output(output_dir: Path) -> Path:
    output = output_dir.resolve()
    root = PROJECT_ROOT.resolve()
    if output == root or root in output.parents:
        raise ValueError("ST07_26 output must be outside the project root")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("ST07_26 output directory must be empty")
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
        (
            PROJECT_ROOT
            / "data_registry/st07_25_stage05_seed_stability_full_validation_evidence_v01.json"
        ).read_text(encoding="utf-8")
    )
    rows = [
        row
        for row in evidence["execution_contract"]["environment"]["threadpools_before_fit"]
        if row["user_api"] == "blas"
    ]
    return runtime_identities(rows)


def package_versions() -> dict[str, str]:
    names = ("numpy", "pandas", "scipy", "scikit-learn", "openml", "threadpoolctl")
    return {name: importlib.metadata.version(name) for name in names}


def prepare_run(cache_server_dir: Path) -> dict[str, Any]:
    protected_before = protected_hash_state()
    if not all(row["match"] for row in protected_before.values()):
        raise RuntimeError("Protected ST07_26 source or scientific input hash differs")
    plan = read_csv_checked(
        PROJECT_ROOT / "configs/stress_tests/miniboone_stress_test_plan_v01.csv"
    )
    claims = read_csv_checked(
        PROJECT_ROOT / "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv"
    )
    contract = build_seed_stability_contract(plan, claims)
    candidate_bundle, X, y, feature_names, cache_evidence = (
        load_miniboone_from_openml_cache(cache_server_dir)
    )
    controls = build_seed_stability_control_estimators()
    if tuple(controls) != ("dummy_prior", "logistic_regression"):
        raise RuntimeError("Registered control estimator order changed")
    observed_runtime = runtime_rows()
    backend_exact = runtime_identities(observed_runtime) == reference_backend_identities()
    if not backend_exact:
        raise RuntimeError("Current BLAS backend identity differs from ST07_25")
    references = {
        4: pd.read_csv(
            PROJECT_ROOT / "data_registry" / HISTORICAL_REFERENCE,
            dtype=str,
            keep_default_na=False,
        ),
        12: pd.read_csv(
            PROJECT_ROOT / "data_registry" / ST0725_REFERENCE,
            dtype=str,
            keep_default_na=False,
        ),
    }
    for condition, frame in references.items():
        selected = frame[frame["model_id"].eq(MODEL_ID)]
        if len(selected) != 50:
            raise RuntimeError(f"Reference for BLAS={condition} must have 50 LR rows")
    return {
        "protected_before": protected_before,
        "contract": contract,
        "candidate_bundle": candidate_bundle,
        "X": X,
        "y": y,
        "feature_names": feature_names,
        "cache_evidence": cache_evidence,
        "estimator": controls[MODEL_ID],
        "runtime_before": observed_runtime,
        "backend_identity_exact": backend_exact,
        "references": references,
    }


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
            "model_id": MODEL_ID,
            "model_fit_count": 100,
            "thread_conditions_in_order": list(THREAD_CONDITIONS),
            "hgb_fit_count": 0,
            "dummy_fit_count": 0,
            "inner_tuning_count": 0,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(),
            "blas_before": prepared["runtime_before"],
            "backend_identity_exact_to_st07_25": prepared["backend_identity_exact"],
        },
        "comparison_policy": {
            "blas_4_reference": HISTORICAL_REFERENCE,
            "blas_12_reference": ST0725_REFERENCE,
            "metrics": list(METRIC_COLUMNS),
            "metric_equality": "exact_after_csv_roundtrip_no_tolerance",
            "timing": "finite_nonnegative_excluded_from_equality",
            "pass_rule": "4_exact_350_of_350_and_12_exact_350_of_350",
            "cross_environment_claim": "prohibited",
            "golden_or_claim_change": "prohibited",
        },
        "protected_before": prepared["protected_before"],
    }
    path = output / EXECUTION_CONTRACT_FILENAME
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def make_score_row(
    raw: dict[str, Any],
    prepared: dict[str, Any],
    condition: int,
    outer_random_state: int,
) -> dict[str, Any]:
    contract = prepared["contract"]
    reference = HISTORICAL_REFERENCE if condition == 4 else ST0725_REFERENCE
    row = {
        "task_id": TASK_ID,
        "stress_test_id": contract.stress_test_id,
        "claim_id": contract.claim_id,
        "candidate_id": contract.candidate_id,
        "thread_condition": condition,
        "outer_random_state": outer_random_state,
        "outer_split_number": raw["outer_split_number"],
        "outer_repeat_number": raw["outer_repeat_number"],
        "outer_fold_number": raw["outer_fold_number"],
        "outer_cv_n_splits": raw["outer_cv_n_splits"],
        "outer_cv_n_repeats": raw["outer_cv_n_repeats"],
        "model_id": raw["model_id"],
        "model_role": raw["model_role"],
        "selected_parameter_set_id": raw["selected_parameter_set_id"],
        "feature_policy_id": raw["feature_policy_id"],
        "n_train": raw["n_train"],
        "n_test": raw["n_test"],
        "train_positive_share": raw["train_positive_share"],
        "test_positive_share": raw["test_positive_share"],
        **{column: raw[column] for column in METRIC_COLUMNS},
        "fit_seconds": raw["fit_seconds"],
        "predict_seconds": raw["predict_seconds"],
        "reference_artifact": reference,
        "metric_cells_total": len(METRIC_COLUMNS),
        "exact_reference_metric_cells": "pending",
        "exact_after_csv_roundtrip": "pending",
        "row_status": ROW_STATUS,
        "interpretation_allowed_ru": INTERPRETATION,
    }
    return row


def reference_lr(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["model_id"].eq(MODEL_ID)].reset_index(drop=True)


def comparison_for_condition(
    scores: pd.DataFrame,
    reference: pd.DataFrame,
    condition: int,
) -> dict[str, Any]:
    candidate = scores[scores["thread_condition"].eq(str(condition))].reset_index(drop=True)
    golden = reference_lr(reference)
    if len(candidate) != 50 or len(golden) != 50:
        raise RuntimeError("Diagnostic/reference LR row count differs from 50")
    split_mask = candidate[list(SPLIT_INPUT_COLUMNS)].ne(golden[list(SPLIT_INPUT_COLUMNS)])
    metric_mask = candidate[list(METRIC_COLUMNS)].ne(golden[list(METRIC_COLUMNS)])
    exact_cells = int(metric_mask.size - metric_mask.to_numpy().sum())
    deltas: dict[str, Any] = {}
    for column in METRIC_COLUMNS:
        left = pd.to_numeric(candidate[column], errors="raise")
        right = pd.to_numeric(golden[column], errors="raise")
        values = (left - right).abs()
        deltas[column] = {
            "mismatch_cells": int(metric_mask[column].sum()),
            "max_absolute_delta": float(values.max()),
        }
    return {
        "thread_condition": condition,
        "reference_artifact": (
            HISTORICAL_REFERENCE if condition == 4 else ST0725_REFERENCE
        ),
        "reference_sha256": sha256_file(
            PROJECT_ROOT
            / "data_registry"
            / (HISTORICAL_REFERENCE if condition == 4 else ST0725_REFERENCE)
        ),
        "rows": len(candidate),
        "split_input_cells": int(split_mask.size),
        "split_input_mismatch_cells": int(split_mask.to_numpy().sum()),
        "split_input_exact": not bool(split_mask.to_numpy().any()),
        "metric_cells": int(metric_mask.size),
        "exact_metric_cells": exact_cells,
        "metric_mismatch_cells": int(metric_mask.to_numpy().sum()),
        "metrics_exact": not bool(metric_mask.to_numpy().any()),
        "metric_deltas": deltas,
    }


def timing_valid(scores: pd.DataFrame) -> tuple[bool, dict[str, Any]]:
    details: dict[str, Any] = {}
    valid_all = True
    for column in ("fit_seconds", "predict_seconds"):
        values = pd.to_numeric(scores[column], errors="coerce")
        valid = values.notna() & values.map(math.isfinite) & values.ge(0.0)
        details[column] = {
            "valid_cells": int(valid.sum()),
            "total_cells": len(values),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        }
        valid_all = valid_all and bool(valid.all())
    return valid_all, details


def register_evidence(
    scores_path: Path,
    evidence: dict[str, Any],
    evidence_dir: Path,
) -> None:
    destination = evidence_dir.resolve()
    if destination != (PROJECT_ROOT / "data_registry").resolve():
        raise ValueError("ST07_26 evidence-dir must be the project data_registry")
    targets = [destination / SCORES_FILENAME, destination / EVIDENCE_FILENAME]
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise FileExistsError(f"ST07_26 evidence targets already exist: {existing}")
    shutil.copy2(scores_path, targets[0])
    targets[1].write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def execute_preflight(cache_server_dir: Path, output_dir: Path) -> dict[str, Any]:
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir)
    contract_record = execution_contract(prepared, output)
    condition_states: dict[str, Any] = {}
    for condition in THREAD_CONDITIONS:
        with threadpool_limits(limits=condition, user_api="blas"):
            condition_states[str(condition)] = verify_thread_condition(condition)
        verify_runtime_restored(prepared["runtime_before"])
    return {
        "status": "pass",
        "technical_status": "PASS",
        "task_id": TASK_ID,
        "mode": "preflight_only",
        "execution_contract_sha256": sha256_file(output / EXECUTION_CONTRACT_FILENAME),
        "condition_states": condition_states,
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
    contract = prepared["contract"]
    score_rows: list[dict[str, Any]] = []
    warning_rows: list[dict[str, Any]] = []
    condition_runtime: dict[str, Any] = {}
    started = perf_counter()
    for condition in THREAD_CONDITIONS:
        with threadpool_limits(limits=condition, user_api="blas"):
            condition_runtime[str(condition)] = verify_thread_condition(condition)
            for outer_random_state in contract.outer_random_states:
                splitter = build_outer_splitter(
                    contract.outer_n_splits,
                    contract.outer_n_repeats,
                    outer_random_state,
                )
                for split_number, (train_index, test_index) in enumerate(
                    splitter.split(prepared["X"], prepared["y"])
                ):
                    raw, captured = fit_control_estimator_on_outer_block(
                        candidate_bundle=prepared["candidate_bundle"],
                        X=prepared["X"],
                        y=prepared["y"],
                        train_index=train_index,
                        test_index=test_index,
                        model_id=MODEL_ID,
                        estimator_template=prepared["estimator"],
                        zero_based_outer_split_number=split_number,
                        feature_names=prepared["feature_names"],
                        protocol_id=contract.nested_protocol_id,
                        candidate_id=contract.candidate_id,
                        outer_n_splits=contract.outer_n_splits,
                        outer_n_repeats=contract.outer_n_repeats,
                        inner_n_splits=contract.inner_n_splits,
                        feature_policy_id=contract.feature_policy_id,
                        row_status=ROW_STATUS,
                        interpretation_allowed=INTERPRETATION,
                        numeric_runtime_contract=None,
                    )
                    score_rows.append(
                        make_score_row(raw, prepared, condition, outer_random_state)
                    )
                    warning_rows.extend(captured)
        verify_runtime_restored(prepared["runtime_before"])
    elapsed_seconds = perf_counter() - started
    scores_path = output / SCORES_FILENAME
    pd.DataFrame(score_rows, columns=SCORE_COLUMNS).to_csv(scores_path, index=False)
    scores = pd.read_csv(scores_path, dtype=str, keep_default_na=False)
    provisional = {
        condition: comparison_for_condition(
            scores, prepared["references"][condition], condition
        )
        for condition in THREAD_CONDITIONS
    }
    for condition, comparison in provisional.items():
        mask = scores["thread_condition"].eq(str(condition))
        reference = reference_lr(prepared["references"][condition])
        candidate = scores[mask].reset_index(drop=True)
        row_exact = candidate[list(METRIC_COLUMNS)].eq(
            reference[list(METRIC_COLUMNS)]
        ).sum(axis=1)
        scores.loc[mask, "exact_reference_metric_cells"] = row_exact.astype(str).tolist()
        scores.loc[mask, "exact_after_csv_roundtrip"] = (
            row_exact.eq(len(METRIC_COLUMNS)).map({True: "true", False: "false"}).tolist()
        )
        if comparison["metric_cells"] != 350:
            raise RuntimeError("Each thread condition must compare 350 metric cells")
    scores.to_csv(scores_path, index=False)
    scores = pd.read_csv(scores_path, dtype=str, keep_default_na=False)
    comparisons = {
        condition: comparison_for_condition(
            scores, prepared["references"][condition], condition
        )
        for condition in THREAD_CONDITIONS
    }
    timing_ok, timing_details = timing_valid(scores)
    protected_after = protected_hash_state()
    protected_exact = all(row["match"] for row in protected_after.values())
    runtime_after = verify_runtime_restored(prepared["runtime_before"])
    thread_enforced = all(
        all(int(row["num_threads"]) == condition for row in condition_runtime[str(condition)])
        for condition in THREAD_CONDITIONS
    )
    causal_support = (
        len(scores) == 100
        and scores["model_id"].eq(MODEL_ID).all()
        and comparisons[4]["metrics_exact"]
        and comparisons[12]["metrics_exact"]
        and comparisons[4]["split_input_exact"]
        and comparisons[12]["split_input_exact"]
        and prepared["backend_identity_exact"]
        and thread_enforced
        and timing_ok
        and not warning_rows
        and prepared["cache_evidence"].network_attempts == 0
        and protected_exact
    )
    evidence = {
        "task_id": TASK_ID,
        "task_profile": "SCIENTIFIC_VALIDATION",
        "status": "pass" if causal_support else "fail",
        "technical_status": "PASS" if causal_support else "FAIL",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        "scientific_verdict": "PASS_CAUSAL_SUPPORT" if causal_support else "FAIL",
        "execution": {
            "pid": os.getpid(),
            "fresh_process": True,
            "isolated_output": True,
            "elapsed_seconds": elapsed_seconds,
            "training_performed": True,
            "logistic_fit_count": len(scores),
            "hgb_fit_count": 0,
            "dummy_fit_count": 0,
            "inner_tuning_count": 0,
            "network_attempts": prepared["cache_evidence"].network_attempts,
            "network_used": False,
            "canonical_golden_overwrites": 0,
            "claim_or_verdict_changed": False,
        },
        "execution_contract": contract_record,
        "execution_contract_sha256": sha256_file(output / EXECUTION_CONTRACT_FILENAME),
        "condition_runtime": condition_runtime,
        "runtime_after": runtime_after,
        "runtime_restored": runtime_after == prepared["runtime_before"],
        "warnings": warning_rows,
        "scores": {
            "filename": SCORES_FILENAME,
            "sha256": sha256_file(scores_path),
            "shape": list(scores.shape),
            "schema": list(scores.columns),
        },
        "comparisons": {str(key): value for key, value in comparisons.items()},
        "timing": {"valid": timing_ok, "details": timing_details},
        "aggregate_verdict": {
            "blas_4_exact_350_of_350": comparisons[4]["exact_metric_cells"] == 350,
            "blas_12_exact_350_of_350": comparisons[12]["exact_metric_cells"] == 350,
            "split_inputs_exact": comparisons[4]["split_input_exact"] and comparisons[12]["split_input_exact"],
            "backend_identity_exact_to_st07_25": prepared["backend_identity_exact"],
            "thread_limits_enforced": thread_enforced,
            "runtime_restored": runtime_after == prepared["runtime_before"],
            "timing_valid": timing_ok,
            "warnings_absent": not warning_rows,
            "protected_exact": protected_exact,
            "verdict_rule": "pass_causal_support_only_if_all_checks_true",
        },
        "protected_after": protected_after,
        "interpretation": {
            "allowed": (
                "BLAS thread count is causally supported as the factor explaining the "
                "current same-machine ST05_02 logistic-regression mismatch."
            ),
            "prohibited": (
                "Retrospective protocol ratification, golden-master change, claim/verdict "
                "change, or cross-environment reproducibility conclusion."
            ),
            "repeatability_scope": "same_machine_same_backend_same_data_same_splits",
            "tolerance": "none_predeclared_and_none_selected_after_result",
        },
    }
    register_evidence(scores_path, evidence, evidence_dir)
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
    print(
        json.dumps(
            {
                "status": result["status"],
                "technical_status": result["technical_status"],
                "task_id": result["task_id"],
                "scientific_verdict": result.get("scientific_verdict"),
                "execution": result.get("execution"),
                "aggregate_verdict": result.get("aggregate_verdict"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
