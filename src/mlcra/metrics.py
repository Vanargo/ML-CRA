from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)


METRIC_DIRECTIONS: dict[str, str] = {
    "average_precision": "higher_is_better",
    "roc_auc": "higher_is_better",
    "f1": "higher_is_better",
    "balanced_accuracy": "higher_is_better",
    "log_loss": "lower_is_better",
    "brier_score": "lower_is_better",
}


def get_positive_class_probability(
    estimator: Any,
    X: pd.DataFrame,
) -> np.ndarray:
    """Return probabilities for the registered positive class label 1."""
    if not hasattr(estimator, "predict_proba"):
        raise TypeError(f"У модели {type(estimator).__name__} нет predict_proba")
    probabilities = estimator.predict_proba(X)
    classes = getattr(estimator, "classes_", None)
    if classes is None and hasattr(estimator, "named_steps"):
        final_step = list(estimator.named_steps.values())[-1]
        classes = getattr(final_step, "classes_", None)
    if classes is None:
        raise AttributeError("Не удалось получить classes_ у модели")

    class_list = list(classes)
    if 1 not in class_list:
        raise ValueError(f"В classes_ нет положительного кода 1: {class_list}")
    positive_index = class_list.index(1)
    return probabilities[:, positive_index]


def score_binary_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probability: np.ndarray,
) -> dict[str, float]:
    """Return the legacy six-metric binary-classification contract.

    The historical ``pr_auc`` key stores scikit-learn average precision (AP),
    not trapezoidal area under the precision-recall curve. This compatibility
    alias is preserved so that Stage 7 refactoring does not change registered
    Stage 5 values or schemas.
    """
    return {
        "roc_auc": float(roc_auc_score(y_true, y_probability)),
        "pr_auc": float(average_precision_score(y_true, y_probability)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "log_loss": float(
            log_loss(
                y_true,
                np.column_stack([1.0 - y_probability, y_probability]),
                labels=[0, 1],
            )
        ),
        "brier_score": float(
            brier_score_loss(y_true, y_probability, pos_label=1)
        ),
    }


def higher_is_better(metric_name: str) -> bool:
    try:
        return METRIC_DIRECTIONS[metric_name] == "higher_is_better"
    except KeyError as error:
        raise ValueError(f"Неизвестная метрика: {metric_name}") from error


def metric_delta(candidate_value: float, baseline_value: float, metric_name: str) -> float:
    if higher_is_better(metric_name):
        return candidate_value - baseline_value
    return baseline_value - candidate_value
