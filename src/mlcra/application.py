from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import importlib.resources
import json
import math
import os
import platform
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from jsonschema import Draft202012Validator
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlcra.datasets import deny_network_access
from mlcra.metrics import (
    get_positive_class_probability,
    metric_delta,
    score_binary_classifier,
)


CLI_CONTRACT_VERSION = "st08_12_dashboard_shared_core_and_CLI_golden_equivalence_v01"
BINARY_CLAIM_SCHEMA_VERSION = "mlcra_binary_classification_claim_v01"
REGRESSION_CLAIM_SCHEMA_VERSION = "mlcra_tabular_regression_claim_v01"
CLAIM_SCHEMA_RESOURCES = {
    BINARY_CLAIM_SCHEMA_VERSION: "binary_classification_claim_v01.schema.json",
    REGRESSION_CLAIM_SCHEMA_VERSION: "tabular_regression_claim_v01.schema.json",
}
DEVELOPMENT_VERSION = "0.1.0.dev0"
REQUIRED_BUNDLE_FILES = (
    "run_manifest.json",
    "input_validation.json",
    "environment.json",
    "provenance.json",
    "audit_summary.json",
    "verdict.json",
    "warnings.json",
    "artifact_index.json",
)
HASHED_BUNDLE_FILES = tuple(name for name in REQUIRED_BUNDLE_FILES if name != "run_manifest.json")
EXPECTED_RUNTIME_DISTRIBUTIONS = {
    "attrs": "26.1.0",
    "jsonschema": "4.26.0",
    "jsonschema-specifications": "2025.9.1",
    "joblib": "1.5.3",
    "numpy": "2.4.4",
    "pandas": "3.0.2",
    "python-dateutil": "2.9.0.post0",
    "referencing": "0.37.0",
    "rpds-py": "0.30.0",
    "scikit-learn": "1.8.0",
    "scipy": "1.17.1",
    "six": "1.17.0",
    "threadpoolctl": "3.6.0",
    "typing-extensions": "4.16.0",
    "tzdata": "2026.2",
}


class MlcraApplicationError(RuntimeError):
    """Controlled user-facing failure with the registered diagnostic fields."""

    def __init__(
        self,
        *,
        exit_code: int,
        error_code: str,
        phase: str,
        artifact_or_field: str,
        expected: Any,
        actual: Any,
        severity: str,
        action_taken: str,
        user_action: str,
        rule_source: str,
    ) -> None:
        super().__init__(error_code)
        self.exit_code = exit_code
        self.diagnostic = {
            "error_code": error_code,
            "phase": phase,
            "artifact_or_field": artifact_or_field,
            "expected": _json_safe(expected),
            "actual": _json_safe(actual),
            "severity": severity,
            "action_taken": action_taken,
            "user_action": user_action,
            "rule_source": rule_source,
        }


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return str(value)
    return value


def _raise(
    exit_code: int,
    error_code: str,
    phase: str,
    artifact_or_field: str,
    expected: Any,
    actual: Any,
    user_action: str,
    rule_source: str,
    *,
    severity: str = "error",
    action_taken: str = "operation_stopped_without_success_publication",
) -> None:
    raise MlcraApplicationError(
        exit_code=exit_code,
        error_code=error_code,
        phase=phase,
        artifact_or_field=artifact_or_field,
        expected=expected,
        actual=actual,
        severity=severity,
        action_taken=action_taken,
        user_action=user_action,
        rule_source=rule_source,
    )


def software_version() -> str:
    try:
        return importlib.metadata.version("ml-cra")
    except importlib.metadata.PackageNotFoundError:
        return DEVELOPMENT_VERSION


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _local_regular_file(path: str | Path, artifact: str) -> Path:
    raw = str(path)
    if "://" in raw:
        _raise(
            3,
            "MLCRA_INPUT_PATH_NOT_LOCAL",
            "input_validation",
            artifact,
            "existing local regular file without URL scheme",
            raw,
            "Передайте путь к локальному файлу.",
            "ST08_04.cli_contract.input_contract.data.path_policy",
        )
    candidate = Path(path)
    if not candidate.is_file():
        _raise(
            3,
            "MLCRA_INPUT_FILE_MISSING",
            "input_validation",
            artifact,
            "existing local regular file",
            raw,
            "Проверьте путь и права чтения файла.",
            "ST08_04.cli_contract.exit_codes.3",
        )
    return candidate.resolve()


def _read_json_object(path: str | Path, artifact: str) -> tuple[Path, dict[str, Any]]:
    resolved = _local_regular_file(path, artifact)
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _raise(
            3,
            "MLCRA_JSON_PARSE_ERROR",
            "input_validation",
            artifact,
            "UTF-8 JSON object",
            str(error),
            "Сохраните файл как корректный UTF-8 JSON.",
            "ST08_04.cli_contract.input_contract.specification",
        )
    if not isinstance(value, dict):
        _raise(
            3,
            "MLCRA_JSON_ROOT_NOT_OBJECT",
            "input_validation",
            artifact,
            "JSON object",
            type(value).__name__,
            "Используйте объект JSON в корне спецификации.",
            "ST08_04.cli_contract.input_contract.specification",
        )
    return resolved, value


def _claim_schema(schema_version: str) -> dict[str, Any]:
    resource = (
        importlib.resources.files("mlcra")
        .joinpath("schemas")
        .joinpath(CLAIM_SCHEMA_RESOURCES[schema_version])
    )
    schema = json.loads(resource.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_claim_spec(path: str | Path) -> tuple[Path, dict[str, Any]]:
    resolved, spec = _read_json_object(path, "spec")
    schema_version = spec.get("schema_version")
    if not isinstance(schema_version, str) or schema_version not in CLAIM_SCHEMA_RESOURCES:
        _raise(
            3,
            "MLCRA_SPEC_SCHEMA_VERSION_UNSUPPORTED",
            "specification_dispatch",
            "schema_version",
            sorted(CLAIM_SCHEMA_RESOURCES),
            schema_version,
            "Укажите одну из поставляемых версий схемы утверждения.",
            "st08_11.regression_claim_contract.schema_version",
        )
    validator = Draft202012Validator(_claim_schema(schema_version))
    errors = sorted(
        validator.iter_errors(spec),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        field = ".".join(str(part) for part in error.absolute_path) or "<root>"
        _raise(
            3,
            "MLCRA_SPEC_SCHEMA_ERROR",
            "specification_validation",
            field,
            f"instance valid under {schema_version}",
            error.message,
            "Исправьте спецификацию по поставляемой JSON Schema.",
            f"src/mlcra/schemas/{CLAIM_SCHEMA_RESOURCES[schema_version]}",
        )
    return resolved, spec


def _read_csv_header(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, dialect="excel", strict=True)
            header = next(reader, None)
    except (UnicodeDecodeError, csv.Error) as error:
        _raise(
            3,
            "MLCRA_CSV_PARSE_ERROR",
            "input_validation",
            "data",
            "UTF-8 comma-separated CSV compatible with the RFC 4180 profile",
            str(error),
            "Исправьте кодировку, кавычки и число полей CSV.",
            "ST08_04.cli_contract.input_contract.data",
        )
    if not header:
        _raise(
            3,
            "MLCRA_CSV_HEADER_MISSING",
            "input_validation",
            "data.header",
            "one nonempty header row",
            header,
            "Добавьте строку заголовков.",
            "ST08_04.cli_contract.input_contract.data.header",
        )
    if any(not name.strip() for name in header) or len(set(header)) != len(header):
        _raise(
            3,
            "MLCRA_CSV_HEADER_INVALID",
            "input_validation",
            "data.columns",
            "nonempty unique column names",
            header,
            "Исправьте пустые или повторяющиеся имена столбцов.",
            "ST08_04.cli_contract.input_contract.data.columns",
        )
    return header


def load_binary_csv(
    path: str | Path,
    spec: dict[str, Any],
) -> tuple[Path, pd.DataFrame, np.ndarray, dict[str, Any]]:
    resolved = _local_regular_file(path, "data")
    expected_header = _read_csv_header(resolved)
    try:
        frame = pd.read_csv(
            resolved,
            encoding="utf-8-sig",
            dtype=str,
            keep_default_na=False,
            sep=",",
        )
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
        _raise(
            3,
            "MLCRA_CSV_PARSE_ERROR",
            "input_validation",
            "data",
            "UTF-8 comma-separated CSV compatible with the RFC 4180 profile",
            str(error),
            "Исправьте CSV и повторите запуск.",
            "ST08_04.cli_contract.input_contract.data",
        )
    if list(frame.columns) != expected_header:
        _raise(
            3,
            "MLCRA_CSV_HEADER_CHANGED_DURING_PARSE",
            "input_validation",
            "data.columns",
            expected_header,
            list(frame.columns),
            "Исправьте неоднозначный заголовок CSV.",
            "ST08_04.cli_contract.input_contract.data.columns",
        )
    if frame.empty:
        _raise(
            3,
            "MLCRA_CSV_EMPTY",
            "input_validation",
            "data.rows",
            "at least one row",
            0,
            "Добавьте наблюдения в CSV.",
            "ST08_04.cli_contract.input_contract.data.rows",
        )
    target = spec["target"]
    if target not in frame.columns:
        _raise(
            3,
            "MLCRA_TARGET_MISSING",
            "input_validation",
            "spec.target",
            target,
            list(frame.columns),
            "Укажите существующий целевой столбец.",
            "ST08_04.cli_contract.input_contract.data.target",
        )
    feature_names = [column for column in frame.columns if column != target]
    if not feature_names:
        _raise(
            3,
            "MLCRA_FEATURES_MISSING",
            "input_validation",
            "data.features",
            "at least one numeric feature",
            [],
            "Добавьте хотя бы один признак.",
            "st08_08.input_contract.numeric_features",
        )
    try:
        X = frame[feature_names].apply(pd.to_numeric, errors="raise")
    except (ValueError, TypeError) as error:
        _raise(
            3,
            "MLCRA_NONNUMERIC_FEATURE",
            "input_validation",
            "data.features",
            "finite numeric values without empty cells",
            str(error),
            "Преобразуйте все признаки в числа и заполните пропуски заранее.",
            "st08_08.preprocessing_policy.numeric_complete",
        )
    values = X.to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(values).all():
        _raise(
            3,
            "MLCRA_NONFINITE_FEATURE",
            "input_validation",
            "data.features",
            "finite numeric values",
            "NaN_or_infinity_present",
            "Удалите или заранее обработайте нечисловые и бесконечные значения.",
            "st08_08.preprocessing_policy.numeric_complete",
        )
    labels = frame[target].astype(str)
    unique_labels = sorted(labels.unique().tolist())
    if len(unique_labels) != 2:
        _raise(
            3,
            "MLCRA_UNSUPPORTED_TARGET_CARDINALITY",
            "input_validation",
            target,
            "exactly two target labels",
            unique_labels,
            "Используйте бинарную задачу; многоклассовая классификация и регрессия пока не поддерживаются.",
            "ST08_04.problem_support_boundary.release_0_1_0",
        )
    positive_label = spec["positive_label"]
    if positive_label not in unique_labels:
        _raise(
            3,
            "MLCRA_POSITIVE_LABEL_MISSING",
            "input_validation",
            "spec.positive_label",
            unique_labels,
            positive_label,
            "Укажите один из двух фактических классов как положительный.",
            "st08_08.input_contract.explicit_positive_label",
        )
    y = (labels == positive_label).astype(np.int64).to_numpy()
    class_counts = {str(label): int((labels == label).sum()) for label in unique_labels}
    n_splits = int(spec["split_protocol"]["n_splits"])
    if min(class_counts.values()) < n_splits:
        _raise(
            4,
            "MLCRA_EVIDENCE_CLASS_COUNT_INSUFFICIENT",
            "protocol_precondition",
            "data.target_class_counts",
            f"at least {n_splits} rows in each class",
            class_counts,
            "Уменьшите число разбиений либо предоставьте больше наблюдений каждого класса.",
            "sklearn.model_selection.StratifiedKFold",
        )
    validation = {
        "schema_version": "mlcra_input_validation_v01",
        "status": "PASS",
        "rows": int(len(frame)),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "target": target,
        "target_labels": unique_labels,
        "positive_label": positive_label,
        "class_counts": class_counts,
        "missing_or_nonfinite_features": 0,
        "data_sha256": _sha256_file(resolved),
    }
    return resolved, X, y, validation


def load_regression_csv(
    path: str | Path,
    spec: dict[str, Any],
) -> tuple[Path, pd.DataFrame, np.ndarray, dict[str, Any]]:
    resolved = _local_regular_file(path, "data")
    expected_header = _read_csv_header(resolved)
    try:
        frame = pd.read_csv(
            resolved,
            encoding="utf-8-sig",
            dtype=str,
            keep_default_na=False,
            sep=",",
        )
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
        _raise(
            3,
            "MLCRA_CSV_PARSE_ERROR",
            "input_validation",
            "data",
            "UTF-8 comma-separated CSV compatible with the RFC 4180 profile",
            str(error),
            "Исправьте CSV и повторите запуск.",
            "ST08_04.cli_contract.input_contract.data",
        )
    if list(frame.columns) != expected_header:
        _raise(
            3,
            "MLCRA_CSV_HEADER_CHANGED_DURING_PARSE",
            "input_validation",
            "data.columns",
            expected_header,
            list(frame.columns),
            "Исправьте неоднозначный заголовок CSV.",
            "ST08_04.cli_contract.input_contract.data.columns",
        )
    if frame.empty:
        _raise(
            3,
            "MLCRA_CSV_EMPTY",
            "input_validation",
            "data.rows",
            "at least one row",
            0,
            "Добавьте наблюдения в CSV.",
            "ST08_04.cli_contract.input_contract.data.rows",
        )
    target = spec["target"]
    if target not in frame.columns:
        _raise(
            3,
            "MLCRA_TARGET_MISSING",
            "input_validation",
            "spec.target",
            target,
            list(frame.columns),
            "Укажите существующий целевой столбец.",
            "ST08_04.cli_contract.input_contract.data.target",
        )
    feature_names = [column for column in frame.columns if column != target]
    if not feature_names:
        _raise(
            3,
            "MLCRA_FEATURES_MISSING",
            "input_validation",
            "data.features",
            "at least one numeric feature",
            [],
            "Добавьте хотя бы один признак.",
            "st08_11.regression_claim_contract.features",
        )
    try:
        X = frame[feature_names].apply(pd.to_numeric, errors="raise")
    except (ValueError, TypeError) as error:
        _raise(
            3,
            "MLCRA_NONNUMERIC_FEATURE",
            "input_validation",
            "data.features",
            "finite numeric values without empty cells",
            str(error),
            "Преобразуйте все признаки в числа и заполните пропуски заранее.",
            "st08_11.regression_claim_contract.features",
        )
    feature_values = X.to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(feature_values).all():
        _raise(
            3,
            "MLCRA_NONFINITE_FEATURE",
            "input_validation",
            "data.features",
            "finite numeric values",
            "NaN_or_infinity_present",
            "Удалите или заранее обработайте нечисловые и бесконечные значения.",
            "st08_11.regression_claim_contract.features",
        )
    try:
        numeric_target = pd.to_numeric(frame[target], errors="raise")
        y = numeric_target.to_numpy(dtype=np.float64, copy=True)
    except (ValueError, TypeError) as error:
        _raise(
            3,
            "MLCRA_NONNUMERIC_TARGET",
            "input_validation",
            target,
            "complete finite numeric target",
            str(error),
            "Преобразуйте целевой столбец в конечные числа и заполните пропуски заранее.",
            "st08_11.regression_claim_contract.target",
        )
    if not np.isfinite(y).all():
        _raise(
            3,
            "MLCRA_NONFINITE_TARGET",
            "input_validation",
            target,
            "finite numeric target",
            "NaN_or_infinity_present",
            "Удалите или заранее обработайте бесконечные значения цели.",
            "st08_11.regression_claim_contract.target",
        )
    unique_target_values = int(np.unique(y).size)
    if unique_target_values < 2:
        _raise(
            4,
            "MLCRA_EVIDENCE_CONSTANT_REGRESSION_TARGET",
            "protocol_precondition",
            target,
            "at least two distinct numeric target values",
            unique_target_values,
            "Предоставьте данные с изменяющейся целевой величиной.",
            "st08_11.regression_claim_contract.target",
        )
    n_splits = int(spec["split_protocol"]["n_splits"])
    minimum_rows = 2 * n_splits
    if len(frame) < minimum_rows:
        _raise(
            4,
            "MLCRA_EVIDENCE_ROW_COUNT_INSUFFICIENT",
            "protocol_precondition",
            "data.rows",
            f"at least {minimum_rows} rows for {n_splits} folds",
            int(len(frame)),
            "Уменьшите число разбиений либо предоставьте больше наблюдений.",
            "st08_11.evaluation_protocol.minimum_rows",
        )
    validation = {
        "schema_version": "mlcra_input_validation_v01",
        "status": "PASS",
        "rows": int(len(frame)),
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "target": target,
        "target_type": "finite_numeric_single_output",
        "target_distinct_values": unique_target_values,
        "target_min": float(np.min(y)),
        "target_max": float(np.max(y)),
        "sampling_assumption": spec["sampling_assumption"],
        "missing_or_nonfinite_features": 0,
        "missing_or_nonfinite_target": 0,
        "data_sha256": _sha256_file(resolved),
    }
    return resolved, X, y, validation


def _build_models(seed: int) -> tuple[Any, Any]:
    baseline = Pipeline(
        steps=[
            ("standard_scaler", StandardScaler()),
            (
                "logistic_regression",
                LogisticRegression(max_iter=1000, random_state=seed),
            ),
        ]
    )
    candidate = HistGradientBoostingClassifier(
        learning_rate=0.1,
        max_iter=100,
        max_leaf_nodes=15,
        min_samples_leaf=5,
        l2_regularization=0.1,
        random_state=seed,
    )
    return baseline, candidate


def _public_metrics(estimator: Any, X: pd.DataFrame, y: np.ndarray) -> dict[str, float]:
    predicted = estimator.predict(X)
    probability = get_positive_class_probability(estimator, X)
    legacy = score_binary_classifier(y, predicted, probability)
    return {
        "average_precision": legacy["pr_auc"],
        "roc_auc": legacy["roc_auc"],
        "f1": legacy["f1"],
        "balanced_accuracy": legacy["balanced_accuracy"],
        "log_loss": legacy["log_loss"],
        "brier_score": legacy["brier_score"],
    }


def _build_regression_models(seed: int) -> tuple[Any, Any]:
    baseline = Pipeline(
        steps=[
            ("standard_scaler", StandardScaler()),
            ("ridge_regression", Ridge(alpha=1.0, solver="svd")),
        ]
    )
    candidate = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.1,
        max_iter=100,
        max_leaf_nodes=15,
        min_samples_leaf=3,
        l2_regularization=0.1,
        early_stopping=False,
        random_state=seed,
    )
    return baseline, candidate


def _regression_metrics(
    estimator: Any,
    X: pd.DataFrame,
    y: np.ndarray,
) -> dict[str, float]:
    predicted = np.asarray(estimator.predict(X), dtype=np.float64)
    if not np.isfinite(predicted).all():
        raise ValueError("regressor produced a non-finite prediction")
    return {
        "root_mean_squared_error": float(root_mean_squared_error(y, predicted)),
        "mean_absolute_error": float(mean_absolute_error(y, predicted)),
    }


def _primary_metric_delta(
    candidate_value: float,
    baseline_value: float,
    metric_name: str,
) -> float:
    if metric_name in {"root_mean_squared_error", "mean_absolute_error"}:
        return baseline_value - candidate_value
    return metric_delta(candidate_value, baseline_value, metric_name)


def execute_binary_audit(
    X: pd.DataFrame,
    y: np.ndarray,
    spec: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    n_splits = int(spec["split_protocol"]["n_splits"])
    primary_metric = spec["primary_metric"]
    started = time.perf_counter()
    for seed in spec["seeds"]:
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        for fold_index, (train_index, test_index) in enumerate(splitter.split(X, y), 1):
            baseline, candidate = _build_models(seed)
            try:
                baseline.fit(X.iloc[train_index], y[train_index])
                candidate.fit(X.iloc[train_index], y[train_index])
                baseline_metrics = _public_metrics(baseline, X.iloc[test_index], y[test_index])
                candidate_metrics = _public_metrics(candidate, X.iloc[test_index], y[test_index])
            except MlcraApplicationError:
                raise
            except Exception as error:
                _raise(
                    5,
                    "MLCRA_MODEL_EXECUTION_FAILURE",
                    "model_fit_or_score",
                    f"seed={seed};fold={fold_index}",
                    "both allowlisted models fit and score successfully",
                    f"{type(error).__name__}: {error}",
                    "Проверьте ресурсы и числовую корректность входных данных.",
                    "ST08_04.cli_contract.exit_codes.5",
                )
            rows.append(
                {
                    "seed": seed,
                    "fold": fold_index,
                    "train_rows": int(len(train_index)),
                    "test_rows": int(len(test_index)),
                    "baseline_metrics": baseline_metrics,
                    "candidate_metrics": candidate_metrics,
                    "primary_delta": _primary_metric_delta(
                        candidate_metrics[primary_metric],
                        baseline_metrics[primary_metric],
                        primary_metric,
                    ),
                }
            )
    elapsed = time.perf_counter() - started
    deltas = [float(row["primary_delta"]) for row in rows]
    return {
        "schema_version": "mlcra_binary_classification_audit_summary_v01",
        "claim_id": spec["claim_id"],
        "task_type": spec["task_type"],
        "candidate_model": spec["candidate_model"],
        "baseline_model": spec["baseline_model"],
        "primary_metric": primary_metric,
        "split_protocol": spec["split_protocol"],
        "seeds": spec["seeds"],
        "verdict_policy": spec["verdict_policy"],
        "minimum_mean_delta": float(spec["minimum_mean_delta"]),
        "fold_count": len(rows),
        "mean_primary_delta": float(np.mean(deltas)),
        "min_primary_delta": float(np.min(deltas)),
        "max_primary_delta": float(np.max(deltas)),
        "positive_primary_delta_folds": sum(delta > 0.0 for delta in deltas),
        "execution_seconds": float(elapsed),
        "folds": rows,
    }


def execute_regression_audit(
    X: pd.DataFrame,
    y: np.ndarray,
    spec: dict[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    n_splits = int(spec["split_protocol"]["n_splits"])
    primary_metric = spec["primary_metric"]
    started = time.perf_counter()
    for seed in spec["seeds"]:
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
        for fold_index, (train_index, test_index) in enumerate(splitter.split(X), 1):
            baseline, candidate = _build_regression_models(seed)
            try:
                baseline.fit(X.iloc[train_index], y[train_index])
                candidate.fit(X.iloc[train_index], y[train_index])
                baseline_metrics = _regression_metrics(
                    baseline, X.iloc[test_index], y[test_index]
                )
                candidate_metrics = _regression_metrics(
                    candidate, X.iloc[test_index], y[test_index]
                )
            except MlcraApplicationError:
                raise
            except Exception as error:
                _raise(
                    5,
                    "MLCRA_MODEL_EXECUTION_FAILURE",
                    "model_fit_or_score",
                    f"seed={seed};fold={fold_index}",
                    "both allowlisted regressors fit and score successfully",
                    f"{type(error).__name__}: {error}",
                    "Проверьте ресурсы и числовую корректность входных данных.",
                    "ST08_04.cli_contract.exit_codes.5",
                )
            rows.append(
                {
                    "seed": seed,
                    "fold": fold_index,
                    "train_rows": int(len(train_index)),
                    "test_rows": int(len(test_index)),
                    "baseline_metrics": baseline_metrics,
                    "candidate_metrics": candidate_metrics,
                    "primary_delta": _primary_metric_delta(
                        candidate_metrics[primary_metric],
                        baseline_metrics[primary_metric],
                        primary_metric,
                    ),
                }
            )
    elapsed = time.perf_counter() - started
    deltas = [float(row["primary_delta"]) for row in rows]
    return {
        "schema_version": "mlcra_tabular_regression_audit_summary_v01",
        "claim_id": spec["claim_id"],
        "task_type": spec["task_type"],
        "candidate_model": spec["candidate_model"],
        "baseline_model": spec["baseline_model"],
        "primary_metric": primary_metric,
        "split_protocol": spec["split_protocol"],
        "sampling_assumption": spec["sampling_assumption"],
        "seeds": spec["seeds"],
        "verdict_policy": spec["verdict_policy"],
        "minimum_mean_delta": float(spec["minimum_mean_delta"]),
        "fold_count": len(rows),
        "mean_primary_delta": float(np.mean(deltas)),
        "min_primary_delta": float(np.min(deltas)),
        "max_primary_delta": float(np.max(deltas)),
        "positive_primary_delta_folds": sum(delta > 0.0 for delta in deltas),
        "execution_seconds": float(elapsed),
        "folds": rows,
    }


def recompute_verdict(summary: dict[str, Any]) -> dict[str, Any]:
    task_type = summary.get("task_type")
    schema_by_task = {
        "binary_classification": (
            "mlcra_binary_classification_audit_summary_v01",
            "mlcra_binary_classification_verdict_v01",
        ),
        "tabular_regression": (
            "mlcra_tabular_regression_audit_summary_v01",
            "mlcra_tabular_regression_verdict_v01",
        ),
    }
    if task_type not in schema_by_task:
        _raise(
            6,
            "MLCRA_BUNDLE_TASK_TYPE_UNSUPPORTED",
            "bundle_verdict_recompute",
            "audit_summary.task_type",
            sorted(schema_by_task),
            task_type,
            "Используйте bundle поддерживаемого типа задачи.",
            "st08_11.bundle_contract.required_relations",
        )
    expected_summary_schema, verdict_schema = schema_by_task[task_type]
    if summary.get("schema_version") != expected_summary_schema:
        _raise(
            6,
            "MLCRA_BUNDLE_SUMMARY_SCHEMA_MISMATCH",
            "bundle_verdict_recompute",
            "audit_summary.schema_version",
            expected_summary_schema,
            summary.get("schema_version"),
            "Повторите audit с согласованной поставляемой версией.",
            "st08_11.bundle_contract.required_relations",
        )
    try:
        primary_metric = str(summary["primary_metric"])
        rows = summary["folds"]
        deltas = [float(row["primary_delta"]) for row in rows]
    except (KeyError, TypeError, ValueError) as error:
        _raise(
            6,
            "MLCRA_BUNDLE_SUMMARY_STRUCTURE_ERROR",
            "bundle_verdict_recompute",
            "audit_summary",
            "complete fold metrics and finite numeric deltas",
            str(error),
            "Повторите audit из исходных входов.",
            "st08_11.bundle_contract.required_relations",
        )
    if len(deltas) != int(summary.get("fold_count", 0)) or not deltas:
        _raise(
            6,
            "MLCRA_BUNDLE_IMPOSSIBLE_FOLD_COUNT",
            "bundle_verdict_recompute",
            "audit_summary.fold_count",
            "positive count equal to folds length",
            {"fold_count": summary.get("fold_count"), "rows": len(deltas)},
            "Восстановите bundle из неизменённого успешного запуска audit.",
            "ST08_04.cli_contract.exit_codes.6",
        )
    for row_index, row in enumerate(rows, 1):
        try:
            expected_delta = _primary_metric_delta(
                float(row["candidate_metrics"][primary_metric]),
                float(row["baseline_metrics"][primary_metric]),
                primary_metric,
            )
            recorded_delta = float(row["primary_delta"])
        except (KeyError, TypeError, ValueError) as error:
            _raise(
                6,
                "MLCRA_BUNDLE_FOLD_METRIC_RELATION_ERROR",
                "bundle_verdict_recompute",
                f"audit_summary.folds[{row_index}]",
                f"paired metrics containing {primary_metric}",
                str(error),
                "Не исправляйте bundle вручную; повторите audit.",
                "st08_11.bundle_contract.required_relations",
            )
        if not math.isclose(recorded_delta, expected_delta, rel_tol=1e-12, abs_tol=1e-12):
            _raise(
                6,
                "MLCRA_BUNDLE_PRIMARY_DELTA_RELATION_FAILURE",
                "bundle_verdict_recompute",
                f"audit_summary.folds[{row_index}].primary_delta",
                expected_delta,
                recorded_delta,
                "Не исправляйте производные значения вручную; повторите audit.",
                "st08_11.bundle_contract.required_relations",
            )
    mean_delta = float(np.mean(deltas))
    minimum = float(summary["minimum_mean_delta"])
    positive = sum(delta > 0.0 for delta in deltas)
    aggregates = {
        "mean_primary_delta": mean_delta,
        "min_primary_delta": float(np.min(deltas)),
        "max_primary_delta": float(np.max(deltas)),
    }
    for field, expected in aggregates.items():
        try:
            actual = float(summary[field])
        except (KeyError, TypeError, ValueError) as error:
            _raise(
                6,
                "MLCRA_BUNDLE_AGGREGATE_STRUCTURE_ERROR",
                "bundle_verdict_recompute",
                f"audit_summary.{field}",
                expected,
                str(error),
                "Повторите audit из исходных входов.",
                "st08_11.bundle_contract.required_relations",
            )
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            _raise(
                6,
                "MLCRA_BUNDLE_AGGREGATE_RELATION_FAILURE",
                "bundle_verdict_recompute",
                f"audit_summary.{field}",
                expected,
                actual,
                "Не исправляйте производные значения вручную; повторите audit.",
                "st08_11.bundle_contract.required_relations",
            )
    if int(summary.get("positive_primary_delta_folds", -1)) != positive:
        _raise(
            6,
            "MLCRA_BUNDLE_POSITIVE_FOLD_COUNT_RELATION_FAILURE",
            "bundle_verdict_recompute",
            "audit_summary.positive_primary_delta_folds",
            positive,
            summary.get("positive_primary_delta_folds"),
            "Не исправляйте производные значения вручную; повторите audit.",
            "st08_11.bundle_contract.required_relations",
        )
    if mean_delta >= minimum and positive == len(deltas):
        category = "supported"
        explanation = "Среднее улучшение достигло порога и кандидат выиграл на каждом зарегистрированном блоке."
    elif mean_delta >= minimum:
        category = "fragile"
        explanation = "Среднее улучшение достигло порога, но выигрыш не сохраняется на каждом блоке."
    else:
        category = "not_supported"
        explanation = "Среднее улучшение не достигло заранее указанного порога."
    return {
        "schema_version": verdict_schema,
        "claim_id": summary["claim_id"],
        "category": category,
        "primary_metric": summary["primary_metric"],
        "mean_primary_delta": mean_delta,
        "minimum_mean_delta": minimum,
        "positive_primary_delta_folds": positive,
        "fold_count": len(deltas),
        "explanation_ru": explanation,
        "scope_limit": "Вердикт относится только к переданным данным, моделям, метрике, разбиениям и зернам этой спецификации; универсальное превосходство не утверждается.",
    }


def _environment_report() -> dict[str, Any]:
    installed: dict[str, str | None] = {}
    for name in EXPECTED_RUNTIME_DISTRIBUTIONS:
        try:
            installed[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed[name] = None
    return {
        "schema_version": "mlcra_environment_v01",
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.system(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "distribution": "ml-cra",
        "software_version": software_version(),
        "dependencies": installed,
    }


def _artifact_hashes(directory: Path, names: tuple[str, ...]) -> dict[str, str]:
    return {name: _sha256_file(directory / name) for name in names}


def _task_provenance(spec: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if spec["task_type"] == "binary_classification":
        return (
            {
                "baseline": {
                    "id": "logistic_regression_v01",
                    "implementation": "StandardScaler_then_LogisticRegression_max_iter_1000",
                },
                "candidate": {
                    "id": "hist_gradient_boosting_v01",
                    "implementation": "HistGradientBoostingClassifier_lr_0.1_iter_100_leaf_15_min_leaf_5_l2_0.1",
                },
            },
            "ST08_08 сравнивает две фиксированные разрешённые реализации и не подбирает лучшую модель автоматически.",
        )
    return (
        {
            "baseline": {
                "id": "ridge_regression_v01",
                "implementation": "StandardScaler_then_Ridge_alpha_1_solver_svd",
            },
            "candidate": {
                "id": "hist_gradient_boosting_regressor_v01",
                "implementation": "HistGradientBoostingRegressor_squared_error_lr_0.1_iter_100_leaf_15_min_leaf_3_l2_0.1_early_stopping_false",
            },
        },
        "ST08_11 сравнивает две фиксированные разрешённые реализации и не подбирает модель или гиперпараметры автоматически.",
    )


def run_audit(spec_path: str | Path, data_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    if output.exists():
        _raise(
            3,
            "MLCRA_OUTPUT_ALREADY_EXISTS",
            "output_precondition",
            "output_dir",
            "nonexistent path",
            str(output),
            "Выберите новый каталог вывода; перезапись запрещена.",
            "ST08_04.cli_contract.output_contract.overwrite_policy",
        )
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    started_at = _utc_now()
    try:
        spec_file, spec = load_claim_spec(spec_path)
        if spec["task_type"] == "binary_classification":
            data_file, X, y, input_validation = load_binary_csv(data_path, spec)
            executor = execute_binary_audit
        else:
            data_file, X, y, input_validation = load_regression_csv(data_path, spec)
            executor = execute_regression_audit
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir()
        with deny_network_access() as network_evidence:
            summary = executor(X, y, spec)
        if network_evidence.attempts != 0:
            _raise(
                6,
                "MLCRA_NETWORK_ATTEMPT_DURING_AUDIT",
                "execution_integrity",
                "network_attempts",
                0,
                network_evidence.attempts,
                "Удалите сетевую зависимость из поддерживаемого контура.",
                "ST08_04.cli_contract.input_contract.security.network",
            )
        verdict = recompute_verdict(summary)
        environment = _environment_report()
        models, no_selection_warning = _task_provenance(spec)
        provenance = {
            "schema_version": "mlcra_provenance_v01",
            "contract_version": CLI_CONTRACT_VERSION,
            "claim_schema_version": spec["schema_version"],
            "task_type": spec["task_type"],
            "claim_id": spec["claim_id"],
            "data_filename": data_file.name,
            "spec_filename": spec_file.name,
            "data_sha256": input_validation["data_sha256"],
            "spec_sha256": _sha256_file(spec_file),
            "models": models,
            "network_policy": "deny_by_default",
            "network_attempts": network_evidence.attempts,
        }
        warnings = {
            "schema_version": "mlcra_warnings_v01",
            "warnings": [
                {
                    "code": "BOUNDED_CLAIM_ONLY",
                    "message_ru": verdict["scope_limit"],
                },
                {
                    "code": "NO_HYPERPARAMETER_SELECTION",
                    "message_ru": no_selection_warning,
                },
                {
                    "code": "SOFTWARE_OUTPUT_NOT_SCIENTIFIC_REGISTRATION",
                    "message_ru": "Новый bundle является результатом пользовательского запуска и не изменяет зарегистрированный научный вердикт MiniBooNE.",
                },
            ],
        }
        if spec["task_type"] == "tabular_regression":
            warnings["warnings"].append(
                {
                    "code": "EXCHANGEABLE_ROWS_ASSUMPTION_NOT_MACHINE_VERIFIED",
                    "message_ru": "K-fold корректен только в заявленной области обменных строк; временные, групповые, пространственно зависимые и повторные наблюдения требуют отдельного протокола.",
                }
            )
        payloads = {
            "input_validation.json": input_validation,
            "environment.json": environment,
            "provenance.json": provenance,
            "audit_summary.json": summary,
            "verdict.json": verdict,
            "warnings.json": warnings,
        }
        for name, payload in payloads.items():
            _write_json(staging / name, payload)
        first_hashes = _artifact_hashes(staging, tuple(payloads))
        artifact_index = {
            "schema_version": "mlcra_artifact_index_v01",
            "artifacts": [
                {"path": name, "sha256": first_hashes[name]}
                for name in sorted(first_hashes)
            ],
        }
        _write_json(staging / "artifact_index.json", artifact_index)
        hashes = _artifact_hashes(staging, HASHED_BUNDLE_FILES)
        manifest = {
            "schema_version": "mlcra_run_manifest_v01",
            "contract_version": CLI_CONTRACT_VERSION,
            "software_version": software_version(),
            "command": "audit",
            "input_hashes": {
                "data": input_validation["data_sha256"],
                "spec": _sha256_file(spec_file),
            },
            "spec_hash": _sha256_file(spec_file),
            "artifact_hashes": hashes,
            "started_at": started_at,
            "completed_at": _utc_now(),
            "exit_code": 0,
            "network_attempts": network_evidence.attempts,
        }
        _write_json(staging / "run_manifest.json", manifest)
        verify_bundle(staging)
        os.replace(staging, output)
        return {
            "command": "audit",
            "status": "completed",
            "exit_code": 0,
            "claim_id": spec["claim_id"],
            "verdict": verdict["category"],
            "primary_metric": verdict["primary_metric"],
            "mean_primary_delta": verdict["mean_primary_delta"],
            "scope_limit": verdict["scope_limit"],
            "bundle": str(output),
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _load_bundle_json(bundle: Path, name: str) -> dict[str, Any]:
    _, value = _read_json_object(bundle / name, name)
    return value


def verify_bundle(bundle_path: str | Path) -> dict[str, Any]:
    bundle = Path(bundle_path).resolve()
    if not bundle.is_dir():
        _raise(
            4,
            "MLCRA_BUNDLE_MISSING",
            "bundle_precondition",
            "bundle",
            "existing local bundle directory",
            str(bundle),
            "Передайте каталог успешного запуска audit.",
            "ST08_04.cli_contract.exit_codes.4",
        )
    actual_files = sorted(path.name for path in bundle.iterdir())
    expected_files = sorted(REQUIRED_BUNDLE_FILES)
    if actual_files != expected_files:
        _raise(
            6,
            "MLCRA_BUNDLE_FILE_SET_MISMATCH",
            "bundle_integrity",
            "bundle.files",
            expected_files,
            actual_files,
            "Восстановите полный неизменённый bundle.",
            "ST08_04.cli_contract.output_contract.required_artifacts",
        )
    manifest = _load_bundle_json(bundle, "run_manifest.json")
    artifact_index = _load_bundle_json(bundle, "artifact_index.json")
    try:
        indexed = {row["path"]: row["sha256"] for row in artifact_index["artifacts"]}
        declared = manifest["artifact_hashes"]
    except (KeyError, TypeError) as error:
        _raise(
            6,
            "MLCRA_BUNDLE_INDEX_SCHEMA_ERROR",
            "bundle_integrity",
            "artifact_index_or_manifest",
            "hash mapping for every non-manifest artifact",
            str(error),
            "Восстановите bundle из успешного запуска audit.",
            "ST08_04.cli_contract.exit_codes.6",
        )
    observed = _artifact_hashes(bundle, HASHED_BUNDLE_FILES)
    if declared != observed or indexed != {
        name: observed[name] for name in sorted(name for name in observed if name != "artifact_index.json")
    }:
        _raise(
            6,
            "MLCRA_BUNDLE_HASH_MISMATCH",
            "bundle_integrity",
            "artifact_hashes",
            {"manifest": declared, "index_without_self": indexed},
            observed,
            "Не исправляйте bundle вручную; повторите audit из исходных входов.",
            "ST08_04.cli_contract.exit_codes.6",
        )
    if manifest.get("command") != "audit" or manifest.get("exit_code") != 0 or manifest.get("network_attempts") != 0:
        _raise(
            6,
            "MLCRA_BUNDLE_MANIFEST_INVARIANT_FAILURE",
            "bundle_integrity",
            "run_manifest",
            {"command": "audit", "exit_code": 0, "network_attempts": 0},
            manifest,
            "Используйте только полностью опубликованный успешный bundle.",
            "ST08_04.cli_contract.output_contract.manifest_minimum",
        )
    input_validation = _load_bundle_json(bundle, "input_validation.json")
    provenance = _load_bundle_json(bundle, "provenance.json")
    if manifest.get("input_hashes", {}).get("data") != input_validation.get("data_sha256"):
        _raise(
            6,
            "MLCRA_BUNDLE_INPUT_HASH_RELATION_FAILURE",
            "bundle_integrity",
            "data_sha256",
            manifest.get("input_hashes", {}).get("data"),
            input_validation.get("data_sha256"),
            "Повторите audit из исходных входов.",
            "ST08_04.objective_metrics.ST08-MET-07",
        )
    if provenance.get("network_attempts") != 0:
        _raise(
            6,
            "MLCRA_BUNDLE_NETWORK_INVARIANT_FAILURE",
            "bundle_integrity",
            "provenance.network_attempts",
            0,
            provenance.get("network_attempts"),
            "Отклоните bundle и исследуйте сетевую зависимость.",
            "ST08_04.objective_metrics.ST08-MET-09",
        )
    summary = _load_bundle_json(bundle, "audit_summary.json")
    recorded_verdict = _load_bundle_json(bundle, "verdict.json")
    expected_claim_schema = {
        "binary_classification": BINARY_CLAIM_SCHEMA_VERSION,
        "tabular_regression": REGRESSION_CLAIM_SCHEMA_VERSION,
    }.get(summary.get("task_type"))
    observed_relation = {
        "summary_task_type": summary.get("task_type"),
        "provenance_task_type": provenance.get("task_type", "binary_classification"),
        "claim_schema_version": provenance.get("claim_schema_version"),
    }
    expected_relation = {
        "summary_task_type": summary.get("task_type"),
        "provenance_task_type": summary.get("task_type"),
        "claim_schema_version": expected_claim_schema,
    }
    if expected_claim_schema is None or observed_relation != expected_relation:
        _raise(
            6,
            "MLCRA_BUNDLE_TASK_PROVENANCE_RELATION_FAILURE",
            "bundle_integrity",
            "summary_and_provenance_task_schema",
            expected_relation,
            observed_relation,
            "Не исправляйте bundle вручную; повторите audit из исходных входов.",
            "st08_11.bundle_contract.required_relations",
        )
    recomputed = recompute_verdict(summary)
    if recorded_verdict != recomputed:
        _raise(
            6,
            "MLCRA_BUNDLE_VERDICT_RECOMPUTE_MISMATCH",
            "bundle_verdict_recompute",
            "verdict.json",
            recomputed,
            recorded_verdict,
            "Не исправляйте вердикт вручную; повторите audit.",
            "ST08_04.stakeholder_scenarios.ST08-SCN-02",
        )
    return {
        "command": "verify",
        "status": "PASS",
        "exit_code": 0,
        "bundle": str(bundle),
        "claim_id": recorded_verdict["claim_id"],
        "verdict": recorded_verdict["category"],
        "verified_artifacts": len(REQUIRED_BUNDLE_FILES),
        "model_fit_performed": False,
    }


def build_dashboard_view(bundle_path: str | Path) -> dict[str, Any]:
    """Build one deterministic dashboard view from an already verified bundle."""
    bundle = Path(bundle_path).resolve()
    verification = verify_bundle(bundle)
    summary = _load_bundle_json(bundle, "audit_summary.json")
    verdict = _load_bundle_json(bundle, "verdict.json")
    provenance = _load_bundle_json(bundle, "provenance.json")
    validation = _load_bundle_json(bundle, "input_validation.json")
    warnings = _load_bundle_json(bundle, "warnings.json")
    return {
        "schema_version": "mlcra_dashboard_view_v01",
        "contract_version": CLI_CONTRACT_VERSION,
        "verification_status": verification["status"],
        "model_fit_performed": verification["model_fit_performed"],
        "claim_id": verdict["claim_id"],
        "task_type": summary["task_type"],
        "verdict": verdict["category"],
        "verdict_explanation_ru": verdict["explanation_ru"],
        "scope_limit": verdict["scope_limit"],
        "primary_metric": verdict["primary_metric"],
        "mean_primary_delta": verdict["mean_primary_delta"],
        "minimum_mean_delta": verdict["minimum_mean_delta"],
        "positive_primary_delta_folds": verdict["positive_primary_delta_folds"],
        "fold_count": verdict["fold_count"],
        "input_validation": validation,
        "provenance": provenance,
        "warnings": warnings["warnings"],
        "folds": summary["folds"],
    }


def doctor_report() -> dict[str, Any]:
    environment = _environment_report()
    dependency_status = {
        name: {
            "expected": expected,
            "actual": environment["dependencies"][name],
            "pass": environment["dependencies"][name] == expected,
        }
        for name, expected in EXPECTED_RUNTIME_DISTRIBUTIONS.items()
    }
    python_ok = (
        environment["python_implementation"] == "CPython"
        and sys.version_info[:2] == (3, 12)
    )
    platform_ok = (
        environment["operating_system"] == "Windows"
        and environment["architecture"].lower() in {"amd64", "x86_64"}
    )
    try:
        installed_distribution = importlib.metadata.version("ml-cra") == DEVELOPMENT_VERSION
    except importlib.metadata.PackageNotFoundError:
        installed_distribution = False
    environment_pass = python_ok and platform_ok and installed_distribution and all(
        row["pass"] for row in dependency_status.values()
    )
    return {
        "schema_version": "mlcra_doctor_report_v01",
        "contract_version": CLI_CONTRACT_VERSION,
        "environment_id": "ST08-ENV-CORE-PY312-WIN-X86_64",
        "environment_pass": environment_pass,
        "python_pass": python_ok,
        "platform_pass": platform_ok,
        "installed_distribution_pass": installed_distribution,
        "dependency_status": dependency_status,
        "network_access_performed": False,
        "model_fit_performed": False,
        "release_ready": False,
        "release_blockers": [
            "John_release_authorization_not_granted",
        ],
        "environment": environment,
    }
