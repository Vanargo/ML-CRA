from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd
from sklearn.model_selection import ParameterGrid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.datasets import (  # noqa: E402
    MINIBOONE_CANDIDATE_ID,
    MINIBOONE_DATASET_ID,
    MINIBOONE_DATASET_NAME,
    MINIBOONE_EXPECTED_ROWS,
    MINIBOONE_EXPECTED_TARGET_COUNTS,
    MINIBOONE_TARGET_NAME,
    build_miniboone_control_estimators,
    load_miniboone_from_openml_cache,
)
from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.model_spaces import (  # noqa: E402
    build_hist_gradient_boosting_search_space,
)
from mlcra.nested_artifacts import (  # noqa: E402
    ARTIFACT_IDS,
    V02_PROTOCOL_ID,
    assemble_v02_artifacts,
    read_v02_artifacts,
    validate_v02_schema,
    write_v02_artifacts,
)
from mlcra.nested_cv import (  # noqa: E402
    V02ArtifactContext,
    run_nested_cv_rows,
)
from mlcra.numeric_runtime import (  # noqa: E402
    RUNTIME_CONTRACT_ID,
    build_numeric_runtime_contract,
    enforced_numeric_runtime,
)


PREFLIGHT_TASK_ID = (
    "ST07_17_nested_cv_v02_offline_miniboone_runner_and_preflight_contract"
)
FULL_RUN_TASK_ID = "ST07_18_nested_cv_v02_dual_run_reproducibility_validation"
BASE_PROTOCOL_ID = "miniboone_nested_cv_v01"
PREFLIGHT_FILENAME = "st07_17_miniboone_v02_preflight.json"
PROTOCOL_COLUMNS = [
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
CRITICAL_PROTOCOL_VALUES = {
    "base_protocol": BASE_PROTOCOL_ID,
    "candidate_id": MINIBOONE_CANDIDATE_ID,
    "openml_dataset_id": str(MINIBOONE_DATASET_ID),
    "dataset_name": MINIBOONE_DATASET_NAME,
    "features": "ParticleID_0..ParticleID_49",
    "feature_policy_id": "numeric_particleid_0_49_locked",
    "feature_count": "50",
    "target_name": MINIBOONE_TARGET_NAME,
    "target_mapping": "False=0;True=1",
    "positive_class": "True",
    "outer_cv_method": "RepeatedStratifiedKFold",
    "outer_cv_n_splits": "5",
    "outer_cv_n_repeats": "2",
    "outer_random_state": "20260507",
    "inner_cv_method": "StratifiedKFold",
    "inner_cv_n_splits": "3",
    "model_order": "hist_gradient_boosting;dummy_prior;logistic_regression",
    "hgb_model_space": "miniboone_hist_gradient_boosting_nested_space",
    "primary_scoring": "average_precision",
    "numeric_runtime_contract": RUNTIME_CONTRACT_ID,
    "numeric_policy": "prospective_single_thread_exact_same_backend",
    "golden_policy": "preserve_existing_v01_golden",
    "validation_run_count": "2",
    "validation_run_isolation": (
        "fresh_process_and_separate_temporary_directory_per_run"
    ),
    "network_policy": "offline_cache_only_no_force_refresh",
    "artifact_count": "7",
    "claim_policy": "no_claim_or_verdict_change",
}


def validate_preflight_protocol(protocol: pd.DataFrame) -> dict[str, str]:
    if not isinstance(protocol, pd.DataFrame):
        raise TypeError("protocol must be a pandas.DataFrame")
    if list(protocol.columns) != PROTOCOL_COLUMNS:
        raise ValueError("v02 protocol columns must exactly match the contract")
    if len(protocol) != 41:
        raise ValueError("v02 protocol must contain exactly 41 rows")
    if not protocol["protocol_id"].eq(V02_PROTOCOL_ID).all():
        raise ValueError("v02 protocol contains an unexpected protocol_id")
    if not protocol["base_protocol_id"].eq(BASE_PROTOCOL_ID).all():
        raise ValueError("v02 protocol contains an unexpected base_protocol_id")
    if not protocol["locked_before_run"].eq("yes").all():
        raise ValueError("all v02 protocol rows must be locked_before_run=yes")
    if protocol["object"].duplicated(keep=False).any():
        raise ValueError("v02 protocol object values must be unique")
    allowed_statuses = {
        "inherited_exact",
        "prospective_delta",
        "prospective_validation",
    }
    if not set(protocol["decision_status"]).issubset(allowed_statuses):
        raise ValueError("v02 protocol contains an unknown decision_status")
    values = dict(zip(protocol["object"], protocol["value"], strict=True))
    differences = {
        key: (values.get(key), expected)
        for key, expected in CRITICAL_PROTOCOL_VALUES.items()
        if values.get(key) != expected
    }
    if differences:
        raise ValueError(f"critical v02 protocol values differ: {differences}")
    return values


def require_safe_empty_output(output_dir: Path) -> Path:
    output = output_dir.resolve()
    root = PROJECT_ROOT.resolve()
    if output == root or root in output.parents:
        raise ValueError("MiniBooNE v02 output must be outside the project root")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("MiniBooNE v02 output directory must be empty")
    return output


def prepare_run(cache_server_dir: Path) -> dict[str, Any]:
    protocol = read_csv_checked(
        PROJECT_ROOT
        / "data_registry"
        / "openml_miniboone_nested_cv_v02_protocol_lock.csv"
    )
    protocol_values = validate_preflight_protocol(protocol)

    schema = read_csv_checked(
        PROJECT_ROOT
        / "data_registry"
        / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
    )
    validate_v02_schema(schema)
    canonical_outputs = [
        PROJECT_ROOT / path
        for path in schema["canonical_path"].drop_duplicates().tolist()
    ]
    if any(path.exists() for path in canonical_outputs):
        raise FileExistsError(
            "canonical v02 outputs must remain absent before promotion"
        )

    model_space = read_csv_checked(
        PROJECT_ROOT
        / "configs"
        / "model_spaces"
        / "miniboone_hist_gradient_boosting_nested_space.csv"
    )
    parameter_grid, fixed_parameters = build_hist_gradient_boosting_search_space(
        model_space,
        BASE_PROTOCOL_ID,
        MINIBOONE_CANDIDATE_ID,
    )
    parameter_combinations = len(list(ParameterGrid(parameter_grid)))
    if model_space.shape != (6, 10) or parameter_combinations != 16:
        raise ValueError("model space must have shape 6x10 and 16 grid combinations")

    runtime_df = read_csv_checked(
        PROJECT_ROOT
        / "configs"
        / "runtime"
        / "miniboone_nested_numeric_runtime_v01.csv"
    )
    runtime_contract = build_numeric_runtime_contract(
        runtime_df,
        RUNTIME_CONTRACT_ID,
        V02_PROTOCOL_ID,
    )
    with enforced_numeric_runtime(runtime_contract) as runtime_observed:
        observed_threads = sorted(item.num_threads for item in runtime_observed)
    if observed_threads != [1, 1]:
        raise RuntimeError(
            "preflight must observe exactly two BLAS backends with one thread each"
        )

    bundle, X, y, feature_names, cache_evidence = (
        load_miniboone_from_openml_cache(cache_server_dir)
    )
    base_random_state = int(protocol_values["outer_random_state"])
    controls = build_miniboone_control_estimators(base_random_state)
    if sorted(controls) != ["dummy_prior", "logistic_regression"]:
        raise ValueError("control estimator set differs from the registered contract")
    if (
        len(X) != MINIBOONE_EXPECTED_ROWS
        or len(feature_names) != 50
        or cache_evidence.target_false_count
        != MINIBOONE_EXPECTED_TARGET_COUNTS["False"]
        or cache_evidence.target_true_count
        != MINIBOONE_EXPECTED_TARGET_COUNTS["True"]
        or set(y.tolist()) != {0, 1}
    ):
        raise ValueError("MiniBooNE dataset preflight invariants differ")

    return {
        "protocol": protocol,
        "protocol_values": protocol_values,
        "schema": schema,
        "model_space": model_space,
        "parameter_grid": parameter_grid,
        "fixed_parameters": fixed_parameters,
        "parameter_combinations": parameter_combinations,
        "runtime_contract": runtime_contract,
        "runtime_observed": runtime_observed,
        "observed_threads": observed_threads,
        "bundle": bundle,
        "X": X,
        "y": y,
        "feature_names": feature_names,
        "cache_evidence": cache_evidence,
        "controls": controls,
    }


def execute_preflight(cache_server_dir: Path, output_dir: Path) -> dict[str, Any]:
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir)
    cache_evidence = prepared["cache_evidence"]
    result: dict[str, Any] = {
        "status": "pass",
        "task_id": PREFLIGHT_TASK_ID,
        "mode": "preflight_only",
        "pid": os.getpid(),
        "output_dir": str(output),
        "protocol_id": V02_PROTOCOL_ID,
        "protocol_rows": len(prepared["protocol"]),
        "schema_rows": len(prepared["schema"]),
        "artifact_count": len(ARTIFACT_IDS),
        "candidate_id": prepared["bundle"]["candidate_id"],
        "openml_dataset_id": prepared["bundle"]["did"],
        "dataset_name": prepared["bundle"]["dataset_name"],
        "target_name": prepared["bundle"]["target_name"],
        "dataset_rows": len(prepared["X"]),
        "feature_count": len(prepared["feature_names"]),
        "target_false_count": cache_evidence.target_false_count,
        "target_true_count": cache_evidence.target_true_count,
        "dataset_content_sha256": cache_evidence.dataset_content_sha256,
        "cache_manifest_sha256": cache_evidence.cache_manifest_sha256,
        "cache_file_count": cache_evidence.cache_file_count,
        "cache_server_dir": cache_evidence.cache_server_dir,
        "network_attempts": cache_evidence.network_attempts,
        "model_space_rows": len(prepared["model_space"]),
        "parameter_combinations": prepared["parameter_combinations"],
        "parameter_grid_names": sorted(prepared["parameter_grid"]),
        "fixed_parameters": prepared["fixed_parameters"],
        "control_model_ids": sorted(prepared["controls"]),
        "runtime_contract_id": prepared["runtime_contract"].runtime_contract_id,
        "runtime_backend_count": len(prepared["runtime_observed"]),
        "runtime_threads": prepared["observed_threads"],
        "validation_run_count": int(
            prepared["protocol_values"]["validation_run_count"]
        ),
        "model_fit_calls": 0,
        "training_performed": False,
        "scientific_validation": "skipped_preflight_only",
        "canonical_v02_outputs_created": 0,
        "network_used": False,
        "full_run_entrypoint": "authorized_only_by_st07_18",
    }
    (output / PREFLIGHT_FILENAME).write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def execute_full_run(cache_server_dir: Path, output_dir: Path) -> dict[str, Any]:
    """Execute one authorized, noncanonical MiniBooNE v02 candidate run."""
    output = require_safe_empty_output(output_dir)
    prepared = prepare_run(cache_server_dir)
    protocol_values = prepared["protocol_values"]
    started = perf_counter()
    with enforced_numeric_runtime(prepared["runtime_contract"]) as runtime_observed:
        rows = run_nested_cv_rows(
            candidate_bundle=prepared["bundle"],
            X=prepared["X"],
            y=prepared["y"],
            feature_names=prepared["feature_names"],
            parameter_grid=prepared["parameter_grid"],
            fixed_parameters=prepared["fixed_parameters"],
            control_estimators=prepared["controls"],
            protocol_id=V02_PROTOCOL_ID,
            candidate_id=MINIBOONE_CANDIDATE_ID,
            outer_n_splits=int(protocol_values["outer_cv_n_splits"]),
            outer_n_repeats=int(protocol_values["outer_cv_n_repeats"]),
            inner_n_splits=int(protocol_values["inner_cv_n_splits"]),
            base_random_state=int(protocol_values["outer_random_state"]),
            feature_policy_id=protocol_values["feature_policy_id"],
            row_status="nested_research_draft",
            interpretation_allowed="limited_nested_protocol_review_only",
            numeric_runtime_contract=prepared["runtime_contract"],
            artifact_context=(
                V02ArtifactContext.MINIBOONE_SCIENTIFIC_CANDIDATE
            ),
        )
        artifacts = assemble_v02_artifacts(
            rows,
            prepared["schema"],
            prepared["parameter_grid"],
            prepared["runtime_contract"],
            outer_n_splits=int(protocol_values["outer_cv_n_splits"]),
            outer_n_repeats=int(protocol_values["outer_cv_n_repeats"]),
            inner_n_splits=int(protocol_values["inner_cv_n_splits"]),
            random_state=int(protocol_values["outer_random_state"]),
            artifact_context=(
                V02ArtifactContext.MINIBOONE_SCIENTIFIC_CANDIDATE
            ),
        )
    write_v02_artifacts(
        artifacts,
        prepared["schema"],
        output,
        project_root=PROJECT_ROOT,
    )
    roundtripped = read_v02_artifacts(output, prepared["schema"])
    artifact_rows = {
        artifact_id: len(frame)
        for artifact_id, frame in roundtripped.as_dict().items()
    }
    cache_evidence = prepared["cache_evidence"]
    return {
        "status": "pass",
        "task_id": FULL_RUN_TASK_ID,
        "mode": "full_validation_candidate",
        "pid": os.getpid(),
        "protocol_id": V02_PROTOCOL_ID,
        "artifact_context": (
            V02ArtifactContext.MINIBOONE_SCIENTIFIC_CANDIDATE.value
        ),
        "candidate_id": MINIBOONE_CANDIDATE_ID,
        "dataset_rows": len(prepared["X"]),
        "feature_count": len(prepared["feature_names"]),
        "dataset_content_sha256": cache_evidence.dataset_content_sha256,
        "cache_manifest_sha256": cache_evidence.cache_manifest_sha256,
        "cache_file_count": cache_evidence.cache_file_count,
        "network_attempts": cache_evidence.network_attempts,
        "network_used": False,
        "runtime_backend_count": len(runtime_observed),
        "runtime_threads": sorted(item.num_threads for item in runtime_observed),
        "artifact_count": len(artifact_rows),
        "artifact_rows": artifact_rows,
        "quality_pass_count": int(
            roundtripped.quality_checks["check_result"].eq("pass").sum()
        ),
        "training_performed": True,
        "elapsed_seconds": perf_counter() - started,
        "canonical_v02_outputs_created": 0,
        "promotion_performed": False,
        "claim_or_verdict_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--full-run", action="store_true")
    parser.add_argument("--cache-server-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.preflight_only:
            result = execute_preflight(args.cache_server_dir, args.output_dir)
        else:
            result = execute_full_run(args.cache_server_dir, args.output_dir)
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
