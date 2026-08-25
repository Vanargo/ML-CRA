from __future__ import annotations

import json
import math
import time
import warnings
from contextlib import nullcontext
from dataclasses import dataclass
from enum import Enum
from numbers import Integral, Real
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import (
    GridSearchCV,
    ParameterGrid,
    RepeatedStratifiedKFold,
    StratifiedKFold,
)

from mlcra.metrics import (
    get_positive_class_probability,
    score_binary_classifier,
)
from mlcra.model_spaces import (
    EXPECTED_FIXED_PARAMETERS,
    EXPECTED_GRID_PARAMETERS,
    make_hgb_parameter_set_id,
)
from mlcra.numeric_runtime import (
    NumericRuntimeContract,
    enforced_numeric_runtime,
    require_numeric_runtime_contract,
)


_CONTROL_MODEL_IDS = {"dummy_prior", "logistic_regression"}
_TUNED_MODEL_ID = "hist_gradient_boosting"
_CONTROL_PARAMETER_SET_ID = "not_applicable_control_model"
_MAX_RANDOM_STATE = 2**32 - 1


class V02ArtifactContext(str, Enum):
    ST07_16_SOFTWARE_FIXTURE = "st07_16_software_fixture"
    MINIBOONE_SCIENTIFIC_CANDIDATE = "miniboone_v02_scientific_candidate"


_V02_ARTIFACT_CONTEXT_CONTRACTS = {
    V02ArtifactContext.ST07_16_SOFTWARE_FIXTURE: {
        "row_status": "st07_16_software_fixture_not_scientific_evidence",
        "interpretation_allowed": "no_scientific_interpretation",
        "protocol_boundary_warning_ru": (
            "ST07_16 software fixture validates the execution harness; "
            "it is not MiniBooNE scientific evidence."
        ),
        "quality_details_template": "ST07_16 fixture check {check_id}.",
    },
    V02ArtifactContext.MINIBOONE_SCIENTIFIC_CANDIDATE: {
        "row_status": "nested_research_draft",
        "interpretation_allowed": "limited_nested_protocol_review_only",
        "protocol_boundary_warning_ru": (
            "MiniBooNE v02 scientific-validation candidate artifact; "
            "noncanonical and not promoted."
        ),
        "quality_details_template": (
            "MiniBooNE v02 scientific-candidate check {check_id}; "
            "artifact is noncanonical and not promoted."
        ),
    },
}


def require_v02_artifact_context(
    artifact_context: Any,
    *,
    row_status: str | None = None,
    interpretation_allowed: str | None = None,
) -> V02ArtifactContext:
    """Require one explicit context and optionally its compatible row policy."""
    if not isinstance(artifact_context, V02ArtifactContext):
        raise TypeError("artifact_context должен быть V02ArtifactContext")
    if (row_status is None) != (interpretation_allowed is None):
        raise ValueError(
            "row_status и interpretation_allowed должны проверяться вместе"
        )
    if row_status is not None:
        contract = _V02_ARTIFACT_CONTEXT_CONTRACTS[artifact_context]
        if row_status != contract["row_status"]:
            raise ValueError(
                "row_status несовместим с выбранным artifact_context"
            )
        if interpretation_allowed != contract["interpretation_allowed"]:
            raise ValueError(
                "interpretation_allowed несовместим с выбранным "
                "artifact_context"
            )
    return artifact_context


def v02_protocol_boundary_warning_ru(
    artifact_context: V02ArtifactContext,
) -> str:
    validated = require_v02_artifact_context(artifact_context)
    return str(
        _V02_ARTIFACT_CONTEXT_CONTRACTS[validated][
            "protocol_boundary_warning_ru"
        ]
    )


def v02_quality_details_ru(
    artifact_context: V02ArtifactContext,
    check_id: str,
) -> str:
    validated = require_v02_artifact_context(artifact_context)
    if not isinstance(check_id, str) or not check_id.strip():
        raise ValueError("check_id должен быть непустой строкой")
    return str(
        _V02_ARTIFACT_CONTEXT_CONTRACTS[validated][
            "quality_details_template"
        ]
    ).format(check_id=check_id)


@dataclass(frozen=True)
class NestedCVRunRows:
    outer_scores: tuple[dict[str, Any], ...]
    selected_params: tuple[dict[str, Any], ...]
    warnings: tuple[dict[str, Any], ...]


def _validated_integer(
    value: Any,
    *,
    name: str,
    minimum: int,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} должен быть целым числом")
    normalized = int(value)
    if normalized < minimum:
        raise ValueError(f"{name} должен быть не меньше {minimum}")
    if maximum is not None and normalized > maximum:
        raise ValueError(f"{name} должен быть не больше {maximum}")
    return normalized


def nested_outer_position(
    zero_based_outer_split_number: int,
    outer_n_splits: int,
    outer_n_repeats: int | None = None,
) -> tuple[int, int]:
    """Map a zero-based repeated-CV split to one-based repeat and fold."""
    split_number = _validated_integer(
        zero_based_outer_split_number,
        name="zero_based_outer_split_number",
        minimum=0,
    )
    n_splits = _validated_integer(
        outer_n_splits,
        name="outer_n_splits",
        minimum=2,
    )
    if outer_n_repeats is not None:
        n_repeats = _validated_integer(
            outer_n_repeats,
            name="outer_n_repeats",
            minimum=1,
        )
        if split_number >= n_splits * n_repeats:
            raise ValueError(
                "zero_based_outer_split_number выходит за пределы "
                "зарегистрированного числа внешних разбиений"
            )
    return (split_number // n_splits) + 1, (split_number % n_splits) + 1


def build_outer_splitter(
    n_splits: int,
    n_repeats: int,
    random_state: int,
) -> RepeatedStratifiedKFold:
    """Build the deterministic outer repeated stratified splitter."""
    validated_n_splits = _validated_integer(
        n_splits,
        name="n_splits",
        minimum=2,
    )
    validated_n_repeats = _validated_integer(
        n_repeats,
        name="n_repeats",
        minimum=1,
    )
    validated_random_state = _validated_integer(
        random_state,
        name="random_state",
        minimum=0,
        maximum=_MAX_RANDOM_STATE,
    )
    return RepeatedStratifiedKFold(
        n_splits=validated_n_splits,
        n_repeats=validated_n_repeats,
        random_state=validated_random_state,
    )


def build_inner_splitter(
    n_splits: int,
    base_random_state: int,
    zero_based_outer_split_number: int,
    *,
    add_outer_split_to_random_state: bool = True,
) -> StratifiedKFold:
    """Build the deterministic inner splitter for one outer block."""
    validated_n_splits = _validated_integer(
        n_splits,
        name="n_splits",
        minimum=2,
    )
    validated_base_state = _validated_integer(
        base_random_state,
        name="base_random_state",
        minimum=0,
        maximum=_MAX_RANDOM_STATE,
    )
    split_number = _validated_integer(
        zero_based_outer_split_number,
        name="zero_based_outer_split_number",
        minimum=0,
    )
    if not isinstance(add_outer_split_to_random_state, bool):
        raise TypeError(
            "add_outer_split_to_random_state должен быть логическим значением"
        )
    random_state = validated_base_state + (
        split_number if add_outer_split_to_random_state else 0
    )
    if random_state > _MAX_RANDOM_STATE:
        raise ValueError(
            "base_random_state + zero_based_outer_split_number выходит "
            "за допустимый диапазон random_state"
        )
    return StratifiedKFold(
        n_splits=validated_n_splits,
        shuffle=True,
        random_state=random_state,
    )


def _validated_indices(
    values: Any,
    *,
    name: str,
    row_count: int,
) -> np.ndarray:
    indices = np.asarray(values)
    if indices.ndim != 1 or indices.size == 0:
        raise ValueError(f"{name} должен быть непустым одномерным массивом")
    if indices.dtype.kind not in {"i", "u"}:
        raise TypeError(f"{name} должен содержать только целые индексы")
    indices = indices.astype(np.int64, copy=False)
    if np.any(indices < 0) or np.any(indices >= row_count):
        raise ValueError(f"{name} содержит индекс вне диапазона X")
    if np.unique(indices).size != indices.size:
        raise ValueError(f"{name} содержит повторяющиеся индексы")
    return indices


def _validate_model_contract(
    *,
    model_id: str,
    model_role: str,
    selected_parameter_set_id: str,
    selected_params: dict[str, Any] | None,
) -> None:
    if model_role == "tuned_candidate":
        if model_id != _TUNED_MODEL_ID:
            raise ValueError(
                "Роль tuned_candidate зарегистрирована только для "
                "hist_gradient_boosting"
            )
        if (
            not isinstance(selected_parameter_set_id, str)
            or not selected_parameter_set_id.strip()
            or selected_parameter_set_id == _CONTROL_PARAMETER_SET_ID
        ):
            raise ValueError(
                "Для tuned_candidate требуется непустой идентификатор "
                "выбранного набора параметров"
            )
        if not isinstance(selected_params, dict) or not selected_params:
            raise ValueError(
                "Для tuned_candidate требуется непустой словарь "
                "выбранных параметров"
            )
        if (
            selected_parameter_set_id
            != make_hgb_parameter_set_id(selected_params)
        ):
            raise ValueError(
                "selected_parameter_set_id не соответствует "
                "выбранным параметрам tuned_candidate"
            )
        return

    if model_role == "control":
        if model_id not in _CONTROL_MODEL_IDS:
            raise ValueError(
                "Неизвестная контрольная модель для вложенного протокола"
            )
        if selected_parameter_set_id != _CONTROL_PARAMETER_SET_ID:
            raise ValueError(
                "Контрольная модель должна использовать "
                "not_applicable_control_model"
            )
        if selected_params is not None:
            raise ValueError(
                "Для контрольной модели selected_params должен быть None"
            )
        return

    raise ValueError(f"Неизвестная роль модели: {model_role!r}")


def evaluate_fitted_estimator_on_outer_block(
    estimator: Any,
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    train_index: np.ndarray,
    test_index: np.ndarray,
    model_id: str,
    model_role: str,
    zero_based_outer_split_number: int,
    selected_parameter_set_id: str,
    selected_params: dict[str, Any] | None,
    fit_seconds: float,
    feature_names: list[str],
    *,
    protocol_id: str,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    feature_policy_id: str,
    row_status: str = "nested_research_draft",
    interpretation_allowed: str = "limited_nested_protocol_review_only",
    numeric_runtime_contract: NumericRuntimeContract | None = None,
) -> dict[str, Any]:
    """Evaluate an already fitted estimator on one registered outer block."""
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X должен быть pandas.DataFrame")
    y_array = np.asarray(y)
    if y_array.ndim != 1 or len(y_array) != len(X):
        raise ValueError("y должен быть одномерным и иметь столько же строк, что X")
    if len(X) == 0:
        raise ValueError("X и y не должны быть пустыми")
    if list(X.columns) != feature_names:
        raise ValueError(
            "feature_names должен точно соответствовать порядку столбцов X"
        )
    if not isinstance(candidate_bundle, dict):
        raise TypeError("candidate_bundle должен быть словарём")
    required_candidate_keys = {
        "candidate_id",
        "did",
        "dataset_name",
        "target_name",
        "target_metadata",
    }
    missing_candidate_keys = sorted(required_candidate_keys - candidate_bundle.keys())
    if missing_candidate_keys:
        raise KeyError(
            f"В candidate_bundle отсутствуют поля: {missing_candidate_keys}"
        )
    target_metadata = candidate_bundle["target_metadata"]
    if not isinstance(target_metadata, dict):
        raise TypeError("candidate_bundle['target_metadata'] должен быть словарём")
    required_target_keys = {
        "target_class_0",
        "target_class_1",
        "positive_class_assumption",
    }
    missing_target_keys = sorted(required_target_keys - target_metadata.keys())
    if missing_target_keys:
        raise KeyError(
            f"В target_metadata отсутствуют поля: {missing_target_keys}"
        )
    for value, name in (
        (protocol_id, "protocol_id"),
        (feature_policy_id, "feature_policy_id"),
        (row_status, "row_status"),
        (interpretation_allowed, "interpretation_allowed"),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} должен быть непустой строкой")
    validated_numeric_runtime = require_numeric_runtime_contract(
        protocol_id,
        numeric_runtime_contract,
    )

    split_number = _validated_integer(
        zero_based_outer_split_number,
        name="zero_based_outer_split_number",
        minimum=0,
    )
    n_splits = _validated_integer(
        outer_n_splits,
        name="outer_n_splits",
        minimum=2,
    )
    n_repeats = _validated_integer(
        outer_n_repeats,
        name="outer_n_repeats",
        minimum=1,
    )
    validated_inner_n_splits = _validated_integer(
        inner_n_splits,
        name="inner_n_splits",
        minimum=2,
    )
    outer_repeat_number, outer_fold_number = nested_outer_position(
        split_number,
        n_splits,
        n_repeats,
    )
    train_indices = _validated_indices(
        train_index,
        name="train_index",
        row_count=len(X),
    )
    test_indices = _validated_indices(
        test_index,
        name="test_index",
        row_count=len(X),
    )
    if np.intersect1d(train_indices, test_indices).size:
        raise ValueError("train_index и test_index не должны пересекаться")
    if np.union1d(train_indices, test_indices).size != len(X):
        raise ValueError(
            "train_index и test_index должны вместе покрывать все строки X"
        )
    _validate_model_contract(
        model_id=model_id,
        model_role=model_role,
        selected_parameter_set_id=selected_parameter_set_id,
        selected_params=selected_params,
    )
    if (
        isinstance(fit_seconds, bool)
        or not isinstance(fit_seconds, Real)
        or not math.isfinite(float(fit_seconds))
        or float(fit_seconds) < 0.0
    ):
        raise ValueError("fit_seconds должен быть конечным неотрицательным числом")

    selected_params_json = ""
    if selected_params is not None:
        try:
            selected_params_json = json.dumps(
                selected_params,
                ensure_ascii=False,
                sort_keys=True,
            )
        except (TypeError, ValueError) as error:
            raise ValueError("selected_params должен быть JSON-сериализуемым") from error

    X_test = X.iloc[test_indices].copy()
    y_train = y_array[train_indices]
    y_test = y_array[test_indices]
    runtime_scope = (
        nullcontext()
        if validated_numeric_runtime is None
        else enforced_numeric_runtime(validated_numeric_runtime)
    )
    with runtime_scope:
        predict_start = time.perf_counter()
        y_pred = estimator.predict(X_test)
        y_probability = get_positive_class_probability(estimator, X_test)
        metric_values = score_binary_classifier(y_test, y_pred, y_probability)
        predict_seconds = time.perf_counter() - predict_start

    return {
        "protocol_id": protocol_id,
        "candidate_id": candidate_bundle["candidate_id"],
        "openml_dataset_id": candidate_bundle["did"],
        "dataset_name": candidate_bundle["dataset_name"],
        "target_name": candidate_bundle["target_name"],
        "target_class_0": target_metadata["target_class_0"],
        "target_class_1": target_metadata["target_class_1"],
        "positive_class_assumption": target_metadata[
            "positive_class_assumption"
        ],
        "outer_split_number": split_number + 1,
        "outer_repeat_number": outer_repeat_number,
        "outer_fold_number": outer_fold_number,
        "outer_cv_n_splits": n_splits,
        "outer_cv_n_repeats": n_repeats,
        "inner_cv_n_splits": (
            validated_inner_n_splits
            if model_role == "tuned_candidate"
            else ""
        ),
        "model_id": model_id,
        "model_role": model_role,
        "selected_parameter_set_id": selected_parameter_set_id,
        "selected_params_json": selected_params_json,
        "feature_policy_id": feature_policy_id,
        "feature_count": len(feature_names),
        "feature_names": "; ".join(feature_names),
        "n_train": len(train_indices),
        "n_test": len(test_indices),
        "train_positive_share": float(np.mean(y_train)),
        "test_positive_share": float(np.mean(y_test)),
        "roc_auc": metric_values["roc_auc"],
        "average_precision": metric_values["pr_auc"],
        "pr_auc": metric_values["pr_auc"],
        "f1": metric_values["f1"],
        "balanced_accuracy": metric_values["balanced_accuracy"],
        "log_loss": metric_values["log_loss"],
        "brier_score": metric_values["brier_score"],
        "fit_seconds": round(float(fit_seconds), 6),
        "predict_seconds": round(predict_seconds, 6),
        "row_status": row_status,
        "interpretation_allowed": interpretation_allowed,
    }


def _validated_fit_context(
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    train_index: np.ndarray,
    test_index: np.ndarray,
    zero_based_outer_split_number: int,
    feature_names: list[str],
    *,
    protocol_id: str,
    candidate_id: str,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    feature_policy_id: str,
    row_status: str,
    interpretation_allowed: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int, int]:
    """Validate all metadata and data boundaries before an estimator is fitted."""
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X должен быть pandas.DataFrame")
    y_array = np.asarray(y)
    if y_array.ndim != 1 or len(y_array) != len(X):
        raise ValueError(
            "y должен быть одномерным и иметь столько же строк, что X"
        )
    if len(X) == 0:
        raise ValueError("X и y не должны быть пустыми")
    if not isinstance(feature_names, list) or list(X.columns) != feature_names:
        raise ValueError(
            "feature_names должен точно соответствовать порядку столбцов X"
        )
    if not isinstance(candidate_bundle, dict):
        raise TypeError("candidate_bundle должен быть словарём")
    required_candidate_keys = {
        "candidate_id",
        "did",
        "dataset_name",
        "target_name",
        "target_metadata",
    }
    missing_candidate_keys = sorted(
        required_candidate_keys - candidate_bundle.keys()
    )
    if missing_candidate_keys:
        raise KeyError(
            f"В candidate_bundle отсутствуют поля: {missing_candidate_keys}"
        )
    target_metadata = candidate_bundle["target_metadata"]
    if not isinstance(target_metadata, dict):
        raise TypeError(
            "candidate_bundle['target_metadata'] должен быть словарём"
        )
    required_target_keys = {
        "target_class_0",
        "target_class_1",
        "positive_class_assumption",
    }
    missing_target_keys = sorted(required_target_keys - target_metadata.keys())
    if missing_target_keys:
        raise KeyError(
            f"В target_metadata отсутствуют поля: {missing_target_keys}"
        )
    for value, name in (
        (protocol_id, "protocol_id"),
        (candidate_id, "candidate_id"),
        (feature_policy_id, "feature_policy_id"),
        (row_status, "row_status"),
        (interpretation_allowed, "interpretation_allowed"),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} должен быть непустой строкой")
    if candidate_bundle["candidate_id"] != candidate_id:
        raise ValueError(
            "candidate_id не соответствует candidate_bundle['candidate_id']"
        )

    split_number = _validated_integer(
        zero_based_outer_split_number,
        name="zero_based_outer_split_number",
        minimum=0,
    )
    n_splits = _validated_integer(
        outer_n_splits,
        name="outer_n_splits",
        minimum=2,
    )
    n_repeats = _validated_integer(
        outer_n_repeats,
        name="outer_n_repeats",
        minimum=1,
    )
    _validated_integer(
        inner_n_splits,
        name="inner_n_splits",
        minimum=2,
    )
    outer_repeat_number, outer_fold_number = nested_outer_position(
        split_number,
        n_splits,
        n_repeats,
    )
    train_indices = _validated_indices(
        train_index,
        name="train_index",
        row_count=len(X),
    )
    test_indices = _validated_indices(
        test_index,
        name="test_index",
        row_count=len(X),
    )
    if np.intersect1d(train_indices, test_indices).size:
        raise ValueError("train_index и test_index не должны пересекаться")
    if np.union1d(train_indices, test_indices).size != len(X):
        raise ValueError(
            "train_index и test_index должны вместе покрывать все строки X"
        )
    return (
        y_array,
        train_indices,
        test_indices,
        outer_repeat_number,
        outer_fold_number,
    )


def _warning_rows(
    captured_warnings: list[warnings.WarningMessage],
    *,
    candidate_id: str,
    protocol_id: str,
    zero_based_outer_split_number: int,
    outer_repeat_number: int,
    outer_fold_number: int,
    model_id: str,
) -> list[dict[str, Any]]:
    return [
        {
            "severity": "warning",
            "candidate_id": candidate_id,
            "protocol_id": protocol_id,
            "outer_split_number": zero_based_outer_split_number + 1,
            "outer_repeat_number": outer_repeat_number,
            "outer_fold_number": outer_fold_number,
            "model_id": model_id,
            "object": captured_warning.category.__name__,
            "warning_ru": str(captured_warning.message),
        }
        for captured_warning in captured_warnings
    ]


def fit_control_estimator_on_outer_block(
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    train_index: np.ndarray,
    test_index: np.ndarray,
    model_id: str,
    estimator_template: Any,
    zero_based_outer_split_number: int,
    feature_names: list[str],
    *,
    protocol_id: str,
    candidate_id: str,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    feature_policy_id: str,
    row_status: str = "nested_research_draft",
    interpretation_allowed: str = "limited_nested_protocol_review_only",
    numeric_runtime_contract: NumericRuntimeContract | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Clone, fit, and evaluate one registered control estimator."""
    (
        y_array,
        train_indices,
        test_indices,
        outer_repeat_number,
        outer_fold_number,
    ) = _validated_fit_context(
        candidate_bundle,
        X,
        y,
        train_index,
        test_index,
        zero_based_outer_split_number,
        feature_names,
        protocol_id=protocol_id,
        candidate_id=candidate_id,
        outer_n_splits=outer_n_splits,
        outer_n_repeats=outer_n_repeats,
        inner_n_splits=inner_n_splits,
        feature_policy_id=feature_policy_id,
        row_status=row_status,
        interpretation_allowed=interpretation_allowed,
    )
    _validate_model_contract(
        model_id=model_id,
        model_role="control",
        selected_parameter_set_id=_CONTROL_PARAMETER_SET_ID,
        selected_params=None,
    )
    validated_numeric_runtime = require_numeric_runtime_contract(
        protocol_id,
        numeric_runtime_contract,
    )

    estimator = clone(estimator_template)
    X_train = X.iloc[train_indices].copy()
    y_train = y_array[train_indices]
    runtime_scope = (
        nullcontext()
        if validated_numeric_runtime is None
        else enforced_numeric_runtime(validated_numeric_runtime)
    )
    with runtime_scope:
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            fit_start = time.perf_counter()
            estimator.fit(X_train, y_train)
            fit_seconds = time.perf_counter() - fit_start

    warning_rows = _warning_rows(
        captured_warnings,
        candidate_id=candidate_id,
        protocol_id=protocol_id,
        zero_based_outer_split_number=zero_based_outer_split_number,
        outer_repeat_number=outer_repeat_number,
        outer_fold_number=outer_fold_number,
        model_id=model_id,
    )
    score_row = evaluate_fitted_estimator_on_outer_block(
        estimator=estimator,
        candidate_bundle=candidate_bundle,
        X=X,
        y=y_array,
        train_index=train_indices,
        test_index=test_indices,
        model_id=model_id,
        model_role="control",
        zero_based_outer_split_number=zero_based_outer_split_number,
        selected_parameter_set_id=_CONTROL_PARAMETER_SET_ID,
        selected_params=None,
        fit_seconds=fit_seconds,
        feature_names=feature_names,
        protocol_id=protocol_id,
        outer_n_splits=outer_n_splits,
        outer_n_repeats=outer_n_repeats,
        inner_n_splits=inner_n_splits,
        feature_policy_id=feature_policy_id,
        row_status=row_status,
        interpretation_allowed=interpretation_allowed,
        numeric_runtime_contract=validated_numeric_runtime,
    )
    return score_row, warning_rows


def fit_tuned_hist_gradient_boosting_on_outer_block(
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    train_index: np.ndarray,
    test_index: np.ndarray,
    zero_based_outer_split_number: int,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
    *,
    protocol_id: str,
    candidate_id: str,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    base_random_state: int,
    inner_base_random_state: int | None = None,
    add_outer_split_to_inner_random_state: bool = True,
    feature_policy_id: str,
    scoring: str,
    refit: bool,
    n_jobs: int,
    return_train_score: bool,
    error_score: str,
    row_status: str = "nested_research_draft",
    interpretation_allowed: str = "limited_nested_protocol_review_only",
    numeric_runtime_contract: NumericRuntimeContract | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Tune on the inner folds, then evaluate once on the outer test block."""
    (
        y_array,
        train_indices,
        test_indices,
        outer_repeat_number,
        outer_fold_number,
    ) = _validated_fit_context(
        candidate_bundle,
        X,
        y,
        train_index,
        test_index,
        zero_based_outer_split_number,
        feature_names,
        protocol_id=protocol_id,
        candidate_id=candidate_id,
        outer_n_splits=outer_n_splits,
        outer_n_repeats=outer_n_repeats,
        inner_n_splits=inner_n_splits,
        feature_policy_id=feature_policy_id,
        row_status=row_status,
        interpretation_allowed=interpretation_allowed,
    )
    validated_base_random_state = _validated_integer(
        base_random_state,
        name="base_random_state",
        minimum=0,
        maximum=_MAX_RANDOM_STATE,
    )
    validated_inner_base_random_state = (
        validated_base_random_state
        if inner_base_random_state is None
        else _validated_integer(
            inner_base_random_state,
            name="inner_base_random_state",
            minimum=0,
            maximum=_MAX_RANDOM_STATE,
        )
    )
    if not isinstance(parameter_grid, dict):
        raise TypeError("parameter_grid должен быть словарём")
    if set(parameter_grid) != EXPECTED_GRID_PARAMETERS:
        raise ValueError(
            "parameter_grid должен содержать точный набор параметров "
            "зарегистрированного пространства HGB"
        )
    if any(
        not isinstance(values, list) or not values
        for values in parameter_grid.values()
    ):
        raise ValueError(
            "Каждое значение parameter_grid должно быть непустым списком"
        )
    parameter_grid_copy = {
        name: list(values) for name, values in parameter_grid.items()
    }
    inner_candidate_count = len(list(ParameterGrid(parameter_grid_copy)))
    if inner_candidate_count != 16:
        raise ValueError(
            "parameter_grid должен задавать ровно 16 комбинаций"
        )
    if not isinstance(fixed_parameters, dict):
        raise TypeError("fixed_parameters должен быть словарём")
    if set(fixed_parameters) != EXPECTED_FIXED_PARAMETERS:
        raise ValueError(
            "fixed_parameters должен содержать точный набор фиксированных "
            "параметров зарегистрированного пространства HGB"
        )
    fixed_parameters_copy = dict(fixed_parameters)
    if fixed_parameters_copy["random_state"] != validated_base_random_state:
        raise ValueError(
            "fixed_parameters['random_state'] должен совпадать с "
            "base_random_state"
        )
    if fixed_parameters_copy["early_stopping"] != "auto":
        raise ValueError(
            "fixed_parameters['early_stopping'] должен быть равен 'auto'"
        )
    if scoring != "average_precision":
        raise ValueError("scoring должен быть равен 'average_precision'")
    if refit is not True:
        raise ValueError("refit должен быть True")
    if isinstance(n_jobs, bool) or not isinstance(n_jobs, Integral) or n_jobs != 1:
        raise ValueError("n_jobs должен быть целым числом 1")
    if return_train_score is not False:
        raise ValueError("return_train_score должен быть False")
    if error_score != "raise":
        raise ValueError("error_score должен быть равен 'raise'")
    validated_numeric_runtime = require_numeric_runtime_contract(
        protocol_id,
        numeric_runtime_contract,
    )

    X_train = X.iloc[train_indices].copy()
    y_train = y_array[train_indices]
    inner_cv = build_inner_splitter(
        inner_n_splits,
        validated_inner_base_random_state,
        zero_based_outer_split_number,
        add_outer_split_to_random_state=(
            add_outer_split_to_inner_random_state
        ),
    )
    inner_random_state = inner_cv.random_state
    estimator = HistGradientBoostingClassifier(**fixed_parameters_copy)
    grid_search = GridSearchCV(
        estimator=estimator,
        param_grid=parameter_grid_copy,
        scoring=scoring,
        refit=refit,
        cv=inner_cv,
        n_jobs=int(n_jobs),
        return_train_score=return_train_score,
        error_score=error_score,
    )
    runtime_scope = (
        nullcontext()
        if validated_numeric_runtime is None
        else enforced_numeric_runtime(validated_numeric_runtime)
    )
    with runtime_scope:
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            fit_start = time.perf_counter()
            grid_search.fit(X_train, y_train)
            fit_seconds = time.perf_counter() - fit_start

    warning_rows = _warning_rows(
        captured_warnings,
        candidate_id=candidate_id,
        protocol_id=protocol_id,
        zero_based_outer_split_number=zero_based_outer_split_number,
        outer_repeat_number=outer_repeat_number,
        outer_fold_number=outer_fold_number,
        model_id=_TUNED_MODEL_ID,
    )
    selected_params = dict(grid_search.best_params_)
    selected_parameter_set_id = make_hgb_parameter_set_id(selected_params)
    score_row = evaluate_fitted_estimator_on_outer_block(
        estimator=grid_search,
        candidate_bundle=candidate_bundle,
        X=X,
        y=y_array,
        train_index=train_indices,
        test_index=test_indices,
        model_id=_TUNED_MODEL_ID,
        model_role="tuned_candidate",
        zero_based_outer_split_number=zero_based_outer_split_number,
        selected_parameter_set_id=selected_parameter_set_id,
        selected_params=selected_params,
        fit_seconds=fit_seconds,
        feature_names=feature_names,
        protocol_id=protocol_id,
        outer_n_splits=outer_n_splits,
        outer_n_repeats=outer_n_repeats,
        inner_n_splits=inner_n_splits,
        feature_policy_id=feature_policy_id,
        row_status=row_status,
        interpretation_allowed=interpretation_allowed,
        numeric_runtime_contract=validated_numeric_runtime,
    )
    selected_params_row = {
        "protocol_id": protocol_id,
        "candidate_id": candidate_id,
        "outer_split_number": zero_based_outer_split_number + 1,
        "outer_repeat_number": outer_repeat_number,
        "outer_fold_number": outer_fold_number,
        "model_id": _TUNED_MODEL_ID,
        "selected_parameter_set_id": selected_parameter_set_id,
        "selected_params_json": json.dumps(
            selected_params,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "inner_best_average_precision": float(grid_search.best_score_),
        "inner_cv_n_splits": int(inner_n_splits),
        "inner_cv_random_state": int(inner_random_state),
        "inner_candidate_count": inner_candidate_count,
        "row_status": row_status,
    }
    return score_row, selected_params_row, warning_rows


def run_nested_cv_rows(
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
    control_estimators: dict[str, Any],
    *,
    protocol_id: str,
    candidate_id: str,
    outer_n_splits: int,
    outer_n_repeats: int,
    inner_n_splits: int,
    base_random_state: int,
    feature_policy_id: str,
    row_status: str,
    interpretation_allowed: str,
    numeric_runtime_contract: NumericRuntimeContract,
    artifact_context: V02ArtifactContext,
) -> NestedCVRunRows:
    """Execute the registered model order across all nested outer blocks."""
    if set(control_estimators) != _CONTROL_MODEL_IDS:
        raise ValueError(
            "control_estimators должен содержать dummy_prior и "
            "logistic_regression"
        )
    validated_runtime = require_numeric_runtime_contract(
        protocol_id,
        numeric_runtime_contract,
    )
    if validated_runtime is None:
        raise ValueError("Для standalone v02 harness требуется runtime-контракт")
    validated_artifact_context = require_v02_artifact_context(
        artifact_context,
        row_status=row_status,
        interpretation_allowed=interpretation_allowed,
    )

    outer_scores: list[dict[str, Any]] = []
    selected_params: list[dict[str, Any]] = []
    warning_rows: list[dict[str, Any]] = [
        {
            "severity": "info",
            "candidate_id": candidate_id,
            "protocol_id": protocol_id,
            "outer_split_number": "all",
            "outer_repeat_number": "all",
            "outer_fold_number": "all",
            "model_id": "all",
            "object": "protocol_boundary",
            "warning_ru": v02_protocol_boundary_warning_ru(
                validated_artifact_context
            ),
        }
    ]

    outer_cv = build_outer_splitter(
        outer_n_splits,
        outer_n_repeats,
        base_random_state,
    )
    for split_number, (train_index, test_index) in enumerate(
        outer_cv.split(X, y)
    ):
        tuned_row, selected_row, captured = (
            fit_tuned_hist_gradient_boosting_on_outer_block(
                candidate_bundle=candidate_bundle,
                X=X,
                y=y,
                train_index=train_index,
                test_index=test_index,
                zero_based_outer_split_number=split_number,
                feature_names=feature_names,
                parameter_grid=parameter_grid,
                fixed_parameters=fixed_parameters,
                protocol_id=protocol_id,
                candidate_id=candidate_id,
                outer_n_splits=outer_n_splits,
                outer_n_repeats=outer_n_repeats,
                inner_n_splits=inner_n_splits,
                base_random_state=base_random_state,
                feature_policy_id=feature_policy_id,
                scoring="average_precision",
                refit=True,
                n_jobs=1,
                return_train_score=False,
                error_score="raise",
                row_status=row_status,
                interpretation_allowed=interpretation_allowed,
                numeric_runtime_contract=validated_runtime,
            )
        )
        outer_scores.append(tuned_row)
        selected_params.append(selected_row)
        warning_rows.extend(captured)

        for model_id in ("dummy_prior", "logistic_regression"):
            control_row, captured = fit_control_estimator_on_outer_block(
                candidate_bundle=candidate_bundle,
                X=X,
                y=y,
                train_index=train_index,
                test_index=test_index,
                model_id=model_id,
                estimator_template=control_estimators[model_id],
                zero_based_outer_split_number=split_number,
                feature_names=feature_names,
                protocol_id=protocol_id,
                candidate_id=candidate_id,
                outer_n_splits=outer_n_splits,
                outer_n_repeats=outer_n_repeats,
                inner_n_splits=inner_n_splits,
                feature_policy_id=feature_policy_id,
                row_status=row_status,
                interpretation_allowed=interpretation_allowed,
                numeric_runtime_contract=validated_runtime,
            )
            outer_scores.append(control_row)
            warning_rows.extend(captured)

    return NestedCVRunRows(
        outer_scores=tuple(outer_scores),
        selected_params=tuple(selected_params),
        warnings=tuple(warning_rows),
    )
