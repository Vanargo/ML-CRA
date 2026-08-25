from __future__ import annotations

import importlib
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid

from mlcra.io import read_csv_checked, write_csv_checked
from mlcra.nested_cv import (
    NestedCVRunRows,
    V02ArtifactContext,
    require_v02_artifact_context,
    v02_quality_details_ru,
)
from mlcra.numeric_runtime import (
    NumericRuntimeContract,
    enforced_numeric_runtime,
    numeric_runtime_evidence_rows,
)


V02_PROTOCOL_ID = "miniboone_nested_cv_v02"
ARTIFACT_IDS = (
    "outer_scores",
    "selected_params",
    "summary",
    "quality_checks",
    "warnings",
    "environment",
    "numeric_runtime",
)
SCHEMA_COLUMNS = [
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
METRICS = (
    "roc_auc",
    "average_precision",
    "pr_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
)


@dataclass(frozen=True)
class NestedCVArtifacts:
    outer_scores: pd.DataFrame
    selected_params: pd.DataFrame
    summary: pd.DataFrame
    quality_checks: pd.DataFrame
    warnings: pd.DataFrame
    environment: pd.DataFrame
    numeric_runtime: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {artifact_id: getattr(self, artifact_id) for artifact_id in ARTIFACT_IDS}


def validate_v02_schema(schema: pd.DataFrame) -> None:
    if not isinstance(schema, pd.DataFrame):
        raise TypeError("schema должен быть pandas.DataFrame")
    if list(schema.columns) != SCHEMA_COLUMNS:
        raise ValueError("Столбцы v02 schema не совпадают с контрактом")
    if len(schema) != 118 or not schema["protocol_id"].eq(V02_PROTOCOL_ID).all():
        raise ValueError("v02 schema должна иметь 118 строк одного protocol_id")
    if tuple(schema["artifact_id"].drop_duplicates()) != ARTIFACT_IDS:
        raise ValueError("Порядок семи v02 artifact_id нарушен")
    if not schema["required"].eq("yes").all():
        raise ValueError("Все v02 schema columns должны быть required=yes")
    if not set(schema["comparison_class"]).issubset({"A", "B", "C", "D"}):
        raise ValueError("Неизвестный comparison_class")
    for artifact_id, rows in schema.groupby("artifact_id", sort=False):
        positions = pd.to_numeric(rows["column_position"], errors="raise").tolist()
        if positions != list(range(1, len(rows) + 1)):
            raise ValueError(f"Нарушен column_position для {artifact_id}")
        expected_count = int(rows["expected_column_count"].iloc[0])
        if expected_count != len(rows):
            raise ValueError(f"Нарушен expected_column_count для {artifact_id}")


def _schema_rows(schema: pd.DataFrame, artifact_id: str) -> pd.DataFrame:
    rows = schema[schema["artifact_id"].eq(artifact_id)].copy()
    if rows.empty:
        raise ValueError(f"Schema не содержит artifact_id={artifact_id}")
    return rows


def _ordered_columns(schema: pd.DataFrame, artifact_id: str) -> list[str]:
    return _schema_rows(schema, artifact_id)["column_name"].tolist()


def _expected_rows(policy: str) -> tuple[str, int]:
    if policy.startswith("exact_"):
        return "exact", int(policy.removeprefix("exact_"))
    if policy.startswith("minimum_"):
        return "minimum", int(policy.removeprefix("minimum_"))
    raise ValueError(f"Неизвестная expected_rows_policy: {policy}")


def build_nested_summary(
    outer_scores: pd.DataFrame,
    *,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    random_state: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in outer_scores.groupby(
        ["protocol_id", "candidate_id", "model_id", "model_role"],
        sort=True,
        dropna=False,
    ):
        protocol_id, candidate_id, model_id, model_role = keys
        row: dict[str, Any] = {
            "protocol_id": protocol_id,
            "candidate_id": candidate_id,
            "model_id": model_id,
            "model_role": model_role,
            "n_external_blocks": len(group),
            "outer_cv_n_splits": outer_n_splits,
            "outer_cv_n_repeats": outer_n_repeats,
            "inner_cv_n_splits": inner_n_splits if model_role == "tuned_candidate" else "",
            "random_state": random_state,
            "row_status": group["row_status"].iloc[0],
            "interpretation_allowed": group["interpretation_allowed"].iloc[0],
        }
        for metric in METRICS:
            values = pd.to_numeric(group[metric], errors="raise")
            row[f"{metric}_mean"] = float(values.mean())
            row[f"{metric}_std"] = float(values.std(ddof=0))
            row[f"{metric}_min"] = float(values.min())
            row[f"{metric}_max"] = float(values.max())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["candidate_id", "model_id"], kind="mergesort"
    ).reset_index(drop=True)


def build_environment(protocol_id: str) -> pd.DataFrame:
    rows = []
    for name in ("python", "platform", "openml", "sklearn", "pandas", "numpy", "scipy", "threadpoolctl"):
        if name == "python":
            version = sys.version.replace("\n", " ")
        elif name == "platform":
            version = platform.platform()
        else:
            module = importlib.import_module(name)
            version = getattr(module, "__version__", "unknown")
        rows.append({"name": name, "version": version, "protocol_id": protocol_id})
    return pd.DataFrame(rows)


def build_numeric_runtime(contract: NumericRuntimeContract) -> pd.DataFrame:
    with enforced_numeric_runtime(contract) as observed:
        rows = numeric_runtime_evidence_rows(contract, observed)
    return pd.DataFrame(rows)


def _has_exact_schema(frame: pd.DataFrame, schema: pd.DataFrame, artifact_id: str) -> bool:
    return list(frame.columns) == _ordered_columns(schema, artifact_id)


def _unique_schema_key(frame: pd.DataFrame, schema: pd.DataFrame, artifact_id: str) -> bool:
    rows = _schema_rows(schema, artifact_id)
    keys = rows.loc[rows["key_role"].eq("key"), "column_name"].tolist()
    return not keys or not frame.duplicated(keys, keep=False).any()


def build_quality_checks(
    frames: Mapping[str, pd.DataFrame],
    schema: pd.DataFrame,
    parameter_grid: dict[str, list[Any]],
    *,
    artifact_context: V02ArtifactContext,
) -> pd.DataFrame:
    validated_artifact_context = require_v02_artifact_context(
        artifact_context
    )
    outer = frames["outer_scores"]
    selected = frames["selected_params"]
    allowed = list(ParameterGrid(parameter_grid))
    selected_within_grid = all(
        any(params == candidate for candidate in allowed)
        for params in selected["selected_params_json"].map(json.loads)
    )
    metric_values = outer[list(METRICS)].apply(pd.to_numeric, errors="coerce")
    finite_metrics = bool(np.isfinite(metric_values.to_numpy(dtype=float)).all())
    conditions = [
        ("protocol_id_locked", all(frame["protocol_id"].eq(V02_PROTOCOL_ID).all() for frame in frames.values() if "protocol_id" in frame)),
        ("outer_scores_row_count", len(outer) == 30),
        ("selected_params_row_count", len(selected) == 10),
        ("summary_row_count", len(frames["summary"]) == 3),
        ("warnings_minimum_row_count", len(frames["warnings"]) >= 1),
        ("environment_row_count", len(frames["environment"]) == 8),
        ("numeric_runtime_row_count", len(frames["numeric_runtime"]) == 2),
        ("outer_scores_schema_exact", _has_exact_schema(outer, schema, "outer_scores")),
        ("selected_params_schema_exact", _has_exact_schema(selected, schema, "selected_params")),
        ("summary_schema_exact", _has_exact_schema(frames["summary"], schema, "summary")),
        ("warnings_schema_exact", _has_exact_schema(frames["warnings"], schema, "warnings")),
        ("environment_schema_exact", _has_exact_schema(frames["environment"], schema, "environment")),
        ("numeric_runtime_schema_exact", _has_exact_schema(frames["numeric_runtime"], schema, "numeric_runtime")),
        ("feature_count_locked", outer["feature_count"].eq(50).all()),
        ("selected_params_within_grid", selected_within_grid),
        ("metrics_finite", finite_metrics),
    ]
    return pd.DataFrame(
        [
            {
                "protocol_id": V02_PROTOCOL_ID,
                "check_id": check_id,
                "check_result": "pass" if condition else "fail",
                "details_ru": v02_quality_details_ru(
                    validated_artifact_context,
                    check_id,
                ),
            }
            for check_id, condition in conditions
        ]
    )


def assemble_v02_artifacts(
    rows: NestedCVRunRows,
    schema: pd.DataFrame,
    parameter_grid: dict[str, list[Any]],
    runtime_contract: NumericRuntimeContract,
    *,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    random_state: int,
    artifact_context: V02ArtifactContext,
) -> NestedCVArtifacts:
    validate_v02_schema(schema)
    outer = pd.DataFrame(rows.outer_scores)[_ordered_columns(schema, "outer_scores")]
    selected = pd.DataFrame(rows.selected_params)[_ordered_columns(schema, "selected_params")]
    warnings = pd.DataFrame(rows.warnings)[_ordered_columns(schema, "warnings")]
    row_statuses = outer["row_status"].drop_duplicates().tolist()
    interpretations = outer["interpretation_allowed"].drop_duplicates().tolist()
    if len(row_statuses) != 1 or len(interpretations) != 1:
        raise ValueError(
            "outer_scores должен иметь единый artifact context row policy"
        )
    if not selected["row_status"].eq(row_statuses[0]).all():
        raise ValueError(
            "selected_params row_status несовместим с outer_scores"
        )
    validated_artifact_context = require_v02_artifact_context(
        artifact_context,
        row_status=str(row_statuses[0]),
        interpretation_allowed=str(interpretations[0]),
    )
    summary = build_nested_summary(
        outer,
        outer_n_splits=outer_n_splits,
        outer_n_repeats=outer_n_repeats,
        inner_n_splits=inner_n_splits,
        random_state=random_state,
    )[_ordered_columns(schema, "summary")]
    environment = build_environment(V02_PROTOCOL_ID)[_ordered_columns(schema, "environment")]
    numeric_runtime = build_numeric_runtime(runtime_contract)[_ordered_columns(schema, "numeric_runtime")]
    partial = {
        "outer_scores": outer,
        "selected_params": selected,
        "summary": summary,
        "warnings": warnings,
        "environment": environment,
        "numeric_runtime": numeric_runtime,
    }
    quality = build_quality_checks(
        partial,
        schema,
        parameter_grid,
        artifact_context=validated_artifact_context,
    )[
        _ordered_columns(schema, "quality_checks")
    ]
    artifacts = NestedCVArtifacts(
        outer_scores=outer,
        selected_params=selected,
        summary=summary,
        quality_checks=quality,
        warnings=warnings,
        environment=environment,
        numeric_runtime=numeric_runtime,
    )
    validate_v02_artifacts(artifacts, schema)
    return artifacts


def validate_v02_artifacts(artifacts: NestedCVArtifacts, schema: pd.DataFrame) -> None:
    validate_v02_schema(schema)
    frames = artifacts.as_dict()
    if set(frames) != set(ARTIFACT_IDS):
        raise ValueError("Требуются ровно семь v02 artifacts")
    for artifact_id in ARTIFACT_IDS:
        frame = frames[artifact_id]
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{artifact_id} должен быть pandas.DataFrame")
        expected_columns = _ordered_columns(schema, artifact_id)
        if list(frame.columns) != expected_columns:
            raise ValueError(f"Нарушена точная schema/order для {artifact_id}")
        policy = _schema_rows(schema, artifact_id)["expected_rows_policy"].iloc[0]
        mode, count = _expected_rows(policy)
        if (mode == "exact" and len(frame) != count) or (mode == "minimum" and len(frame) < count):
            raise ValueError(f"Нарушена row policy для {artifact_id}: {policy}")
        if not _unique_schema_key(frame, schema, artifact_id):
            raise ValueError(f"Нарушена уникальность key для {artifact_id}")
        if "protocol_id" in frame and not frame["protocol_id"].eq(V02_PROTOCOL_ID).all():
            raise ValueError(f"Нарушен protocol_id для {artifact_id}")
        class_rows = _schema_rows(schema, artifact_id)
        numeric_columns = class_rows.loc[
            class_rows["comparison_class"].isin(["B", "C"]), "column_name"
        ].tolist()
        if numeric_columns:
            numeric = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
            if not np.isfinite(numeric.to_numpy(dtype=float)).all():
                raise ValueError(f"Нечисловое или бесконечное B/C поле в {artifact_id}")
        c_columns = class_rows.loc[class_rows["comparison_class"].eq("C"), "column_name"].tolist()
        if c_columns and (frame[c_columns].apply(pd.to_numeric, errors="raise") < 0).any().any():
            raise ValueError(f"Отрицательное timing-поле в {artifact_id}")
    if not artifacts.quality_checks["check_result"].eq("pass").all():
        raise ValueError("Все 16 quality checks должны иметь pass")


def _artifact_filename(schema: pd.DataFrame, artifact_id: str) -> str:
    path = _schema_rows(schema, artifact_id)["canonical_path"].iloc[0]
    return Path(path).name


def write_v02_artifacts(
    artifacts: NestedCVArtifacts,
    schema: pd.DataFrame,
    output_dir: Path,
    *,
    project_root: Path,
) -> None:
    validate_v02_artifacts(artifacts, schema)
    root = project_root.resolve()
    output = output_dir.resolve()
    canonical = (root / "data_registry").resolve()
    if output == root or output == canonical or canonical in output.parents:
        raise ValueError("ST07_16 запрещает запись fixture в project root или data_registry")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Fixture output directory должен быть пустым")
    for artifact_id, frame in artifacts.as_dict().items():
        write_csv_checked(frame, output / _artifact_filename(schema, artifact_id))


def read_v02_artifacts(output_dir: Path, schema: pd.DataFrame) -> NestedCVArtifacts:
    frames = {
        artifact_id: read_csv_checked(output_dir / _artifact_filename(schema, artifact_id))
        for artifact_id in ARTIFACT_IDS
    }
    artifacts = NestedCVArtifacts(**frames)
    validate_v02_artifacts(artifacts, schema)
    return artifacts


def compare_v02_runs(
    run_a: NestedCVArtifacts,
    run_b: NestedCVArtifacts,
    schema: pd.DataFrame,
) -> dict[str, Any]:
    validate_v02_artifacts(run_a, schema)
    validate_v02_artifacts(run_b, schema)
    a_frames, b_frames = run_a.as_dict(), run_b.as_dict()
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for artifact_id in ARTIFACT_IDS:
        rows = _schema_rows(schema, artifact_id)
        for comparison_class in counts:
            counts[comparison_class] += int(rows["comparison_class"].eq(comparison_class).sum())
        exact_columns = rows.loc[rows["comparison_class"].isin(["A", "B"]), "column_name"].tolist()
        if exact_columns:
            try:
                pd.testing.assert_frame_equal(
                    a_frames[artifact_id][exact_columns].reset_index(drop=True),
                    b_frames[artifact_id][exact_columns].reset_index(drop=True),
                    check_exact=True,
                    check_dtype=False,
                )
            except AssertionError as error:
                raise ValueError(f"A/B mismatch в {artifact_id}: {error}") from error
        c_columns = rows.loc[rows["comparison_class"].eq("C"), "column_name"].tolist()
        for frame in (a_frames[artifact_id], b_frames[artifact_id]):
            if c_columns:
                timing = frame[c_columns].apply(pd.to_numeric, errors="raise")
                if not np.isfinite(timing.to_numpy(dtype=float)).all() or (timing < 0).any().any():
                    raise ValueError(f"C timing invalid в {artifact_id}")
        d_columns = rows.loc[rows["comparison_class"].eq("D"), "column_name"].tolist()
        if d_columns:
            left = a_frames[artifact_id][d_columns].sort_values(d_columns, kind="mergesort").reset_index(drop=True)
            right = b_frames[artifact_id][d_columns].sort_values(d_columns, kind="mergesort").reset_index(drop=True)
            try:
                pd.testing.assert_frame_equal(left, right, check_exact=True, check_dtype=False)
            except AssertionError as error:
                raise ValueError(f"D warning multiset mismatch: {error}") from error
    return {"status": "pass", "class_column_counts": counts}
