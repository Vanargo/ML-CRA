from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, ParameterGrid, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mlcra.metrics import METRIC_DIRECTIONS
from mlcra.model_spaces import (
    EXPECTED_FIXED_PARAMETERS,
    EXPECTED_GRID_PARAMETERS,
    make_hgb_parameter_set_id,
)
from mlcra.nested_cv import (
    build_outer_splitter,
    fit_control_estimator_on_outer_block,
    fit_tuned_hist_gradient_boosting_on_outer_block,
)
from mlcra.validation import (
    require_columns,
    require_non_empty,
    require_unique_key,
)


STAGE05_SEED_STABILITY_ID = "ST05_02_seed_stability_grid"
STAGE05_SEED_CLAIM_ID = "miniboone_hgb_vs_logreg_average_precision_v01"
STAGE05_SEED_RUN_GROUP = "nested_seed_stability_v01"
STAGE05_SEED_PROTOCOL_VARIANT_ID = "nested_5x2_seed_grid_v01"
STAGE05_SEED_NESTED_PROTOCOL_ID = "miniboone_nested_cv_v01"
STAGE05_SEED_CANDIDATE_ID = "openml_miniboone_41150"
STAGE05_SEED_FEATURE_POLICY_ID = "numeric_particleid_0_49_locked"
STAGE05_SEED_ROW_STATUS = "stage05_seed_stability_draft"
STAGE05_SEED_INTERPRETATION_RU = (
    "Разрешен только аудит устойчивости к зернам случайности; "
    "строка не является самостоятельным итоговым выводом."
)
STAGE05_SEED_SUMMARY_ROW_STATUS = "stage05_seed_stability_summary"
STAGE05_SEED_ALL_INTERPRETATION_RU = (
    "Сводка по всем зафиксированным зернам случайности; "
    "не объединять с другими протоколами без отдельной проверки."
)
STAGE05_SEED_SINGLE_INTERPRETATION_RU = (
    "Сводка по одному зерну случайности внешнего разбиения; "
    "используется только внутри этапа 5."
)

STAGE05_SEED_RANDOM_STATES = (
    20260507,
    20260517,
    20260527,
    20260606,
    20260616,
)
STAGE05_SEED_OUTER_N_SPLITS = 5
STAGE05_SEED_OUTER_N_REPEATS = 2
STAGE05_SEED_INNER_N_SPLITS = 3
STAGE05_SEED_HGB_RANDOM_STATE = 20260507
STAGE05_SEED_FEATURE_NAMES = tuple(f"ParticleID_{index}" for index in range(50))
STAGE05_SEED_MODEL_ORDER = (
    "hist_gradient_boosting",
    "dummy_prior",
    "logistic_regression",
)
STAGE05_SEED_COMPARISON_ORDER = (
    "dummy_prior",
    "logistic_regression",
)
STAGE05_SEED_METRIC_ORDER = (
    "average_precision",
    "balanced_accuracy",
    "brier_score",
    "f1",
    "log_loss",
    "roc_auc",
)

STAGE05_SEED_OUTER_COLUMNS = (
    "stress_test_id",
    "claim_id",
    "run_group",
    "protocol_variant_id",
    "candidate_id",
    "openml_dataset_id",
    "dataset_name",
    "target_name",
    "target_class_0",
    "target_class_1",
    "positive_class_assumption",
    "outer_random_state",
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
    "outer_cv_n_splits",
    "outer_cv_n_repeats",
    "inner_cv_n_splits",
    "inner_random_state",
    "model_id",
    "model_role",
    "selected_parameter_set_id",
    "selected_params_json",
    "inner_best_average_precision",
    "inner_candidate_count",
    "feature_policy_id",
    "feature_count",
    "feature_names",
    "n_train",
    "n_test",
    "train_positive_share",
    "test_positive_share",
    "roc_auc",
    "average_precision",
    "pr_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
    "fit_seconds",
    "predict_seconds",
    "row_status",
    "interpretation_allowed_ru",
)

STAGE05_SEED_SELECTED_COLUMNS = (
    "stress_test_id",
    "claim_id",
    "run_group",
    "protocol_variant_id",
    "candidate_id",
    "outer_random_state",
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
    "model_id",
    "selected_parameter_set_id",
    "selected_params_json",
    "inner_best_average_precision",
    "inner_cv_n_splits",
    "inner_random_state",
    "inner_candidate_count",
    "row_status",
)

STAGE05_SEED_SUMMARY_COLUMNS = (
    "stress_test_id",
    "claim_id",
    "run_group",
    "protocol_variant_id",
    "summary_scope",
    "outer_random_state",
    "candidate_id",
    "comparison_role",
    "candidate_model_id",
    "comparison_model_id",
    "metric_name",
    "metric_direction",
    "n_blocks",
    "advantage_mean",
    "advantage_std_population",
    "advantage_min",
    "advantage_max",
    "candidate_positive_blocks",
    "candidate_negative_blocks",
    "candidate_zero_blocks",
    "row_status",
    "interpretation_allowed_ru",
)

_PLAN_REQUIRED_COLUMNS = (
    "stress_test_id",
    "claim_id",
    "requires_new_model_run",
    "run_group",
    "protocol_variant_id",
    "outer_cv_method",
    "outer_cv_n_splits",
    "outer_cv_n_repeats",
    "outer_random_states",
    "inner_cv_method",
    "inner_cv_n_splits",
    "models",
    "primary_metric",
    "parameter_space_policy",
    "priority",
    "execution_order",
    "decision_status",
)

_CLAIM_REQUIRED_COLUMNS = (
    "claim_id",
    "candidate_id",
    "current_protocol_id",
    "decision_status",
)


@dataclass(frozen=True)
class SeedStabilityContract:
    stress_test_id: str
    claim_id: str
    run_group: str
    protocol_variant_id: str
    nested_protocol_id: str
    candidate_id: str
    outer_random_states: tuple[int, ...]
    outer_n_splits: int
    outer_n_repeats: int
    inner_n_splits: int
    hgb_random_state: int
    feature_policy_id: str
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class SeedStabilityBundle:
    outer_scores: pd.DataFrame
    selected_params: pd.DataFrame
    summary: pd.DataFrame


TunedFit = Callable[..., tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]]
ControlFit = Callable[..., tuple[dict[str, Any], list[dict[str, Any]]]]


def _require_exact_text(actual: Any, expected: str, name: str) -> None:
    if str(actual) != expected:
        raise ValueError(f"{name} должен быть равен {expected!r}")


def _require_exact_integer(actual: Any, expected: int, name: str) -> None:
    try:
        normalized = int(str(actual))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} должен быть целым числом {expected}") from error
    if normalized != expected:
        raise ValueError(f"{name} должен быть равен {expected}")


def build_seed_stability_contract(
    stress_test_plan: pd.DataFrame,
    claim_registry: pd.DataFrame,
) -> SeedStabilityContract:
    """Validate the preregistered ST05_02 row and return its locked contract."""
    if not isinstance(stress_test_plan, pd.DataFrame):
        raise TypeError("stress_test_plan должен быть pandas.DataFrame")
    if not isinstance(claim_registry, pd.DataFrame):
        raise TypeError("claim_registry должен быть pandas.DataFrame")
    require_columns(
        stress_test_plan,
        _PLAN_REQUIRED_COLUMNS,
        "ST05_02 stress-test plan",
    )
    require_columns(
        claim_registry,
        _CLAIM_REQUIRED_COLUMNS,
        "ST05_02 claim registry",
    )

    plan_rows = stress_test_plan[
        stress_test_plan["stress_test_id"].eq(STAGE05_SEED_STABILITY_ID)
    ].copy()
    if len(plan_rows) != 1:
        raise ValueError("Для ST05_02 требуется ровно одна строка stress-test plan")
    plan = plan_rows.iloc[0]
    expected_text = {
        "claim_id": STAGE05_SEED_CLAIM_ID,
        "requires_new_model_run": "yes",
        "run_group": STAGE05_SEED_RUN_GROUP,
        "protocol_variant_id": STAGE05_SEED_PROTOCOL_VARIANT_ID,
        "outer_cv_method": "RepeatedStratifiedKFold",
        "inner_cv_method": "StratifiedKFold",
        "models": "hist_gradient_boosting;logistic_regression;dummy_prior",
        "primary_metric": "average_precision",
        "parameter_space_policy": "do_not_expand_after_viewing_results",
        "priority": "must_have",
        "execution_order": "2",
        "decision_status": "locked_before_stage05_runs",
    }
    for column, expected in expected_text.items():
        _require_exact_text(plan[column], expected, f"plan.{column}")
    _require_exact_integer(
        plan["outer_cv_n_splits"],
        STAGE05_SEED_OUTER_N_SPLITS,
        "plan.outer_cv_n_splits",
    )
    _require_exact_integer(
        plan["outer_cv_n_repeats"],
        STAGE05_SEED_OUTER_N_REPEATS,
        "plan.outer_cv_n_repeats",
    )
    _require_exact_integer(
        plan["inner_cv_n_splits"],
        STAGE05_SEED_INNER_N_SPLITS,
        "plan.inner_cv_n_splits",
    )
    try:
        seeds = tuple(
            int(value.strip())
            for value in str(plan["outer_random_states"]).split(";")
            if value.strip()
        )
    except ValueError as error:
        raise ValueError("plan.outer_random_states содержит нецелое seed") from error
    if seeds != STAGE05_SEED_RANDOM_STATES:
        raise ValueError("Порядок и значения ST05_02 outer_random_states изменены")

    claim_rows = claim_registry[
        claim_registry["claim_id"].eq(STAGE05_SEED_CLAIM_ID)
    ].copy()
    if len(claim_rows) != 1:
        raise ValueError("Для ST05_02 требуется ровно одна строка claim")
    claim = claim_rows.iloc[0]
    _require_exact_text(
        claim["candidate_id"],
        STAGE05_SEED_CANDIDATE_ID,
        "claim.candidate_id",
    )
    _require_exact_text(
        claim["current_protocol_id"],
        STAGE05_SEED_NESTED_PROTOCOL_ID,
        "claim.current_protocol_id",
    )
    _require_exact_text(
        claim["decision_status"],
        "locked_before_stage05_runs",
        "claim.decision_status",
    )
    return SeedStabilityContract(
        stress_test_id=STAGE05_SEED_STABILITY_ID,
        claim_id=STAGE05_SEED_CLAIM_ID,
        run_group=STAGE05_SEED_RUN_GROUP,
        protocol_variant_id=STAGE05_SEED_PROTOCOL_VARIANT_ID,
        nested_protocol_id=STAGE05_SEED_NESTED_PROTOCOL_ID,
        candidate_id=STAGE05_SEED_CANDIDATE_ID,
        outer_random_states=STAGE05_SEED_RANDOM_STATES,
        outer_n_splits=STAGE05_SEED_OUTER_N_SPLITS,
        outer_n_repeats=STAGE05_SEED_OUTER_N_REPEATS,
        inner_n_splits=STAGE05_SEED_INNER_N_SPLITS,
        hgb_random_state=STAGE05_SEED_HGB_RANDOM_STATE,
        feature_policy_id=STAGE05_SEED_FEATURE_POLICY_ID,
        feature_names=STAGE05_SEED_FEATURE_NAMES,
    )


def build_seed_stability_control_estimators() -> dict[str, Any]:
    """Build the two registered ST05_02 control estimator templates."""
    return {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic_regression": Pipeline(
            steps=[
                ("standard_scaler", StandardScaler()),
                (
                    "logistic_regression",
                    LogisticRegression(
                        max_iter=1000,
                        random_state=STAGE05_SEED_HGB_RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def _validate_execution_inputs(
    contract: SeedStabilityContract,
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
    control_estimators: dict[str, Any],
) -> np.ndarray:
    if not isinstance(contract, SeedStabilityContract):
        raise TypeError("contract должен быть SeedStabilityContract")
    if contract != build_locked_seed_stability_contract():
        raise ValueError("SeedStabilityContract не совпадает с locked ST05_02")
    if not isinstance(candidate_bundle, dict):
        raise TypeError("candidate_bundle должен быть словарём")
    if candidate_bundle.get("candidate_id") != contract.candidate_id:
        raise ValueError("candidate_bundle не соответствует ST05_02 candidate_id")
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X должен быть pandas.DataFrame")
    y_array = np.asarray(y)
    if y_array.ndim != 1 or len(y_array) != len(X) or len(X) == 0:
        raise ValueError("y должен быть непустым одномерным и соответствовать X")
    if feature_names != list(contract.feature_names):
        raise ValueError("feature_names не совпадает с locked ST05_02 feature list")
    if list(X.columns) != feature_names:
        raise ValueError("Порядок столбцов X не совпадает с feature_names")
    if set(parameter_grid) != EXPECTED_GRID_PARAMETERS:
        raise ValueError("parameter_grid имеет неверный набор параметров")
    if len(list(ParameterGrid(parameter_grid))) != 16:
        raise ValueError("parameter_grid должен задавать ровно 16 комбинаций")
    if set(fixed_parameters) != EXPECTED_FIXED_PARAMETERS:
        raise ValueError("fixed_parameters имеет неверный набор параметров")
    if fixed_parameters["random_state"] != contract.hgb_random_state:
        raise ValueError("HGB random_state должен оставаться равен 20260507")
    if fixed_parameters["early_stopping"] != "auto":
        raise ValueError("HGB early_stopping должен оставаться равен 'auto'")
    if tuple(control_estimators) != ("dummy_prior", "logistic_regression"):
        raise ValueError("Нарушен порядок зарегистрированных control estimators")
    return y_array


def build_locked_seed_stability_contract() -> SeedStabilityContract:
    """Return the immutable local representation of the registered contract."""
    return SeedStabilityContract(
        stress_test_id=STAGE05_SEED_STABILITY_ID,
        claim_id=STAGE05_SEED_CLAIM_ID,
        run_group=STAGE05_SEED_RUN_GROUP,
        protocol_variant_id=STAGE05_SEED_PROTOCOL_VARIANT_ID,
        nested_protocol_id=STAGE05_SEED_NESTED_PROTOCOL_ID,
        candidate_id=STAGE05_SEED_CANDIDATE_ID,
        outer_random_states=STAGE05_SEED_RANDOM_STATES,
        outer_n_splits=STAGE05_SEED_OUTER_N_SPLITS,
        outer_n_repeats=STAGE05_SEED_OUTER_N_REPEATS,
        inner_n_splits=STAGE05_SEED_INNER_N_SPLITS,
        hgb_random_state=STAGE05_SEED_HGB_RANDOM_STATE,
        feature_policy_id=STAGE05_SEED_FEATURE_POLICY_ID,
        feature_names=STAGE05_SEED_FEATURE_NAMES,
    )


def _adapt_outer_score_row(
    row: dict[str, Any],
    contract: SeedStabilityContract,
    outer_random_state: int,
    selected_row: dict[str, Any] | None,
) -> dict[str, Any]:
    if row.get("protocol_id") != contract.nested_protocol_id:
        raise ValueError("fit result имеет неверный nested protocol_id")
    tuned = row.get("model_role") == "tuned_candidate"
    if tuned != (selected_row is not None):
        raise ValueError("selected row должен присутствовать только для tuned HGB")
    inner_random_state: Any = ""
    inner_best: Any = ""
    inner_candidate_count: Any = ""
    if selected_row is not None:
        inner_random_state = selected_row["inner_cv_random_state"]
        inner_best = selected_row["inner_best_average_precision"]
        inner_candidate_count = selected_row["inner_candidate_count"]
    return {
        "stress_test_id": contract.stress_test_id,
        "claim_id": contract.claim_id,
        "run_group": contract.run_group,
        "protocol_variant_id": contract.protocol_variant_id,
        "candidate_id": row["candidate_id"],
        "openml_dataset_id": row["openml_dataset_id"],
        "dataset_name": row["dataset_name"],
        "target_name": row["target_name"],
        "target_class_0": row["target_class_0"],
        "target_class_1": row["target_class_1"],
        "positive_class_assumption": row["positive_class_assumption"],
        "outer_random_state": outer_random_state,
        "outer_split_number": row["outer_split_number"],
        "outer_repeat_number": row["outer_repeat_number"],
        "outer_fold_number": row["outer_fold_number"],
        "outer_cv_n_splits": row["outer_cv_n_splits"],
        "outer_cv_n_repeats": row["outer_cv_n_repeats"],
        "inner_cv_n_splits": row["inner_cv_n_splits"],
        "inner_random_state": inner_random_state,
        "model_id": row["model_id"],
        "model_role": row["model_role"],
        "selected_parameter_set_id": row["selected_parameter_set_id"],
        "selected_params_json": row["selected_params_json"],
        "inner_best_average_precision": inner_best,
        "inner_candidate_count": inner_candidate_count,
        "feature_policy_id": row["feature_policy_id"],
        "feature_count": row["feature_count"],
        "feature_names": row["feature_names"],
        "n_train": row["n_train"],
        "n_test": row["n_test"],
        "train_positive_share": row["train_positive_share"],
        "test_positive_share": row["test_positive_share"],
        "roc_auc": row["roc_auc"],
        "average_precision": row["average_precision"],
        "pr_auc": row["pr_auc"],
        "f1": row["f1"],
        "balanced_accuracy": row["balanced_accuracy"],
        "log_loss": row["log_loss"],
        "brier_score": row["brier_score"],
        "fit_seconds": row["fit_seconds"],
        "predict_seconds": row["predict_seconds"],
        "row_status": row["row_status"],
        "interpretation_allowed_ru": row["interpretation_allowed"],
    }


def _adapt_selected_params_row(
    row: dict[str, Any],
    contract: SeedStabilityContract,
    outer_random_state: int,
) -> dict[str, Any]:
    if row.get("protocol_id") != contract.nested_protocol_id:
        raise ValueError("selected params имеет неверный nested protocol_id")
    return {
        "stress_test_id": contract.stress_test_id,
        "claim_id": contract.claim_id,
        "run_group": contract.run_group,
        "protocol_variant_id": contract.protocol_variant_id,
        "candidate_id": row["candidate_id"],
        "outer_random_state": outer_random_state,
        "outer_split_number": row["outer_split_number"],
        "outer_repeat_number": row["outer_repeat_number"],
        "outer_fold_number": row["outer_fold_number"],
        "model_id": row["model_id"],
        "selected_parameter_set_id": row["selected_parameter_set_id"],
        "selected_params_json": row["selected_params_json"],
        "inner_best_average_precision": row["inner_best_average_precision"],
        "inner_cv_n_splits": row["inner_cv_n_splits"],
        "inner_random_state": row["inner_cv_random_state"],
        "inner_candidate_count": row["inner_candidate_count"],
        "row_status": row["row_status"],
    }


def build_seed_stability_summary(
    outer_scores: pd.DataFrame,
    contract: SeedStabilityContract,
) -> pd.DataFrame:
    """Build the registered paired ST05_02 summary in canonical row order."""
    if not isinstance(outer_scores, pd.DataFrame):
        raise TypeError("outer_scores должен быть pandas.DataFrame")
    require_columns(
        outer_scores,
        (
            "outer_random_state",
            "outer_split_number",
            "outer_repeat_number",
            "outer_fold_number",
            "model_id",
            *STAGE05_SEED_METRIC_ORDER,
        ),
        "ST05_02 outer scores",
    )
    key_columns = [
        "outer_random_state",
        "outer_split_number",
        "outer_repeat_number",
        "outer_fold_number",
    ]
    hgb_rows = outer_scores[
        outer_scores["model_id"].eq("hist_gradient_boosting")
    ].copy()
    summary_rows: list[dict[str, Any]] = []
    role_by_model = {
        "dummy_prior": "lower_bound_model",
        "logistic_regression": "primary_baseline",
    }
    for comparison_model_id in STAGE05_SEED_COMPARISON_ORDER:
        comparison_rows = outer_scores[
            outer_scores["model_id"].eq(comparison_model_id)
        ].copy()
        paired = hgb_rows.merge(
            comparison_rows,
            on=key_columns,
            suffixes=("_hgb", "_comparison"),
            validate="one_to_one",
        )
        for metric_name in STAGE05_SEED_METRIC_ORDER:
            candidate_values = pd.to_numeric(
                paired[f"{metric_name}_hgb"], errors="raise"
            )
            comparison_values = pd.to_numeric(
                paired[f"{metric_name}_comparison"], errors="raise"
            )
            raw_delta = candidate_values - comparison_values
            direction = METRIC_DIRECTIONS[metric_name]
            advantages = raw_delta if direction == "higher_is_better" else -raw_delta
            metric_frame = paired[key_columns].copy()
            metric_frame["advantage"] = advantages.astype(float)

            groups: list[tuple[str, Any, pd.DataFrame]] = [
                ("all_outer_random_states", "all", metric_frame)
            ]
            groups.extend(
                (
                    "single_outer_random_state",
                    seed,
                    metric_frame[
                        metric_frame["outer_random_state"].eq(seed)
                    ],
                )
                for seed in contract.outer_random_states
            )
            for summary_scope, seed_value, group in groups:
                group_advantages = group["advantage"].astype(float)
                summary_rows.append(
                    {
                        "stress_test_id": contract.stress_test_id,
                        "claim_id": contract.claim_id,
                        "run_group": contract.run_group,
                        "protocol_variant_id": contract.protocol_variant_id,
                        "summary_scope": summary_scope,
                        "outer_random_state": seed_value,
                        "candidate_id": contract.candidate_id,
                        "comparison_role": role_by_model[comparison_model_id],
                        "candidate_model_id": "hist_gradient_boosting",
                        "comparison_model_id": comparison_model_id,
                        "metric_name": metric_name,
                        "metric_direction": direction,
                        "n_blocks": int(len(group)),
                        "advantage_mean": float(group_advantages.mean()),
                        "advantage_std_population": float(
                            group_advantages.std(ddof=0)
                        ),
                        "advantage_min": float(group_advantages.min()),
                        "advantage_max": float(group_advantages.max()),
                        "candidate_positive_blocks": int(
                            (group_advantages > 0).sum()
                        ),
                        "candidate_negative_blocks": int(
                            (group_advantages < 0).sum()
                        ),
                        "candidate_zero_blocks": int(
                            (group_advantages == 0).sum()
                        ),
                        "row_status": STAGE05_SEED_SUMMARY_ROW_STATUS,
                        "interpretation_allowed_ru": (
                            STAGE05_SEED_ALL_INTERPRETATION_RU
                            if summary_scope == "all_outer_random_states"
                            else STAGE05_SEED_SINGLE_INTERPRETATION_RU
                        ),
                    }
                )
    return pd.DataFrame(summary_rows, columns=STAGE05_SEED_SUMMARY_COLUMNS)


def _require_exact_columns(
    frame: pd.DataFrame,
    expected: tuple[str, ...],
    name: str,
) -> None:
    require_columns(frame, expected, name)
    if tuple(frame.columns) != expected:
        raise ValueError(f"{name}: порядок или набор столбцов не совпадает")


def _require_finite_nonnegative(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for column in columns:
        values = pd.to_numeric(frame[column], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0.0).any():
            raise ValueError(f"{column} должен быть конечным и неотрицательным")


def validate_seed_stability_bundle(
    bundle: SeedStabilityBundle,
    contract: SeedStabilityContract,
) -> None:
    """Fail closed on all registered ST05_02 schemas, keys, order, and pairing."""
    if not isinstance(bundle, SeedStabilityBundle):
        raise TypeError("bundle должен быть SeedStabilityBundle")
    outer = bundle.outer_scores
    selected = bundle.selected_params
    summary = bundle.summary
    for frame, name in (
        (outer, "ST05_02 outer scores"),
        (selected, "ST05_02 selected params"),
        (summary, "ST05_02 summary"),
    ):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name} должен быть pandas.DataFrame")
        require_non_empty(frame, name)
    _require_exact_columns(outer, STAGE05_SEED_OUTER_COLUMNS, "outer scores")
    _require_exact_columns(
        selected, STAGE05_SEED_SELECTED_COLUMNS, "selected params"
    )
    _require_exact_columns(summary, STAGE05_SEED_SUMMARY_COLUMNS, "summary")

    expected_blocks = (
        len(contract.outer_random_states)
        * contract.outer_n_splits
        * contract.outer_n_repeats
    )
    if (len(outer), len(selected), len(summary)) != (
        expected_blocks * 3,
        expected_blocks,
        2 * len(STAGE05_SEED_METRIC_ORDER) * (len(contract.outer_random_states) + 1),
    ):
        raise ValueError("Нарушено зарегистрированное число строк ST05_02")
    require_unique_key(
        outer,
        ["stress_test_id", "outer_random_state", "outer_split_number", "model_id"],
        "outer scores",
    )
    require_unique_key(
        selected,
        ["stress_test_id", "outer_random_state", "outer_split_number", "model_id"],
        "selected params",
    )
    require_unique_key(
        summary,
        [
            "stress_test_id",
            "comparison_model_id",
            "metric_name",
            "summary_scope",
            "outer_random_state",
        ],
        "summary",
    )

    expected_outer_order = [
        (seed, split_number, model_id)
        for seed in contract.outer_random_states
        for split_number in range(1, contract.outer_n_splits * contract.outer_n_repeats + 1)
        for model_id in STAGE05_SEED_MODEL_ORDER
    ]
    actual_outer_order = [
        (int(seed), int(split_number), str(model_id))
        for seed, split_number, model_id in outer[
            ["outer_random_state", "outer_split_number", "model_id"]
        ].itertuples(index=False, name=None)
    ]
    if actual_outer_order != expected_outer_order:
        raise ValueError("Нарушен порядок seed → split → model в outer scores")
    expected_selected_order = [
        (seed, split_number, "hist_gradient_boosting")
        for seed in contract.outer_random_states
        for split_number in range(1, contract.outer_n_splits * contract.outer_n_repeats + 1)
    ]
    actual_selected_order = [
        (int(seed), int(split_number), str(model_id))
        for seed, split_number, model_id in selected[
            ["outer_random_state", "outer_split_number", "model_id"]
        ].itertuples(index=False, name=None)
    ]
    if actual_selected_order != expected_selected_order:
        raise ValueError("Нарушен порядок seed → split в selected params")
    expected_summary_order = [
        (comparison, metric, scope, seed)
        for comparison in STAGE05_SEED_COMPARISON_ORDER
        for metric in STAGE05_SEED_METRIC_ORDER
        for scope, seed in (
            [("all_outer_random_states", "all")]
            + [
                ("single_outer_random_state", state)
                for state in contract.outer_random_states
            ]
        )
    ]
    actual_summary_order = [
        (
            str(comparison),
            str(metric),
            str(scope),
            "all" if str(seed) == "all" else int(seed),
        )
        for comparison, metric, scope, seed in summary[
            [
                "comparison_model_id",
                "metric_name",
                "summary_scope",
                "outer_random_state",
            ]
        ].itertuples(index=False, name=None)
    ]
    if actual_summary_order != expected_summary_order:
        raise ValueError("Нарушен зарегистрированный порядок summary")

    if not outer["stress_test_id"].eq(contract.stress_test_id).all():
        raise ValueError("outer scores содержит неверный stress_test_id")
    if not outer["claim_id"].eq(contract.claim_id).all():
        raise ValueError("outer scores содержит неверный claim_id")
    if not outer["feature_policy_id"].eq(contract.feature_policy_id).all():
        raise ValueError("outer scores содержит неверный feature_policy_id")
    if not outer["feature_count"].astype(int).eq(len(contract.feature_names)).all():
        raise ValueError("outer scores содержит неверный feature_count")
    expected_feature_names = "; ".join(contract.feature_names)
    if not outer["feature_names"].eq(expected_feature_names).all():
        raise ValueError("outer scores содержит неверный feature_names")
    if not outer["row_status"].eq(STAGE05_SEED_ROW_STATUS).all():
        raise ValueError("outer scores содержит неверный row_status")

    role_by_model = {
        "hist_gradient_boosting": "tuned_candidate",
        "dummy_prior": "control",
        "logistic_regression": "control",
    }
    if any(
        role_by_model.get(row.model_id) != row.model_role
        for row in outer[["model_id", "model_role"]].itertuples(index=False)
    ):
        raise ValueError("Нарушено отображение model_id → model_role")
    hgb = outer[outer["model_id"].eq("hist_gradient_boosting")]
    controls = outer[~outer["model_id"].eq("hist_gradient_boosting")]
    if not controls["selected_parameter_set_id"].eq(
        "not_applicable_control_model"
    ).all():
        raise ValueError("Control rows имеют неверный parameter-set ID")
    for row in hgb.itertuples(index=False):
        params = json.loads(row.selected_params_json)
        if row.selected_parameter_set_id != make_hgb_parameter_set_id(params):
            raise ValueError("HGB parameter-set ID не соответствует JSON")
    if not (outer["average_precision"] == outer["pr_auc"]).all():
        raise ValueError("Нарушен historical average_precision/pr_auc alias")
    _require_finite_nonnegative(outer, ("fit_seconds", "predict_seconds"))
    for column in (
        "roc_auc",
        "average_precision",
        "pr_auc",
        "f1",
        "balanced_accuracy",
        "log_loss",
        "brier_score",
    ):
        values = pd.to_numeric(outer[column], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"{column} должен быть конечным")
    for row in summary.itertuples(index=False):
        if METRIC_DIRECTIONS[row.metric_name] != row.metric_direction:
            raise ValueError("Summary содержит неверное направление метрики")
        expected_n = (
            expected_blocks
            if row.summary_scope == "all_outer_random_states"
            else contract.outer_n_splits * contract.outer_n_repeats
        )
        if int(row.n_blocks) != expected_n:
            raise ValueError("Summary содержит неверное n_blocks")


def run_seed_stability_grid(
    contract: SeedStabilityContract,
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
    control_estimators: dict[str, Any],
    *,
    tuned_fit: TunedFit = fit_tuned_hist_gradient_boosting_on_outer_block,
    control_fit: ControlFit = fit_control_estimator_on_outer_block,
) -> SeedStabilityBundle:
    """Execute the locked five-seed ST05_02 grid through shared nested-CV APIs."""
    y_array = _validate_execution_inputs(
        contract,
        candidate_bundle,
        X,
        y,
        feature_names,
        parameter_grid,
        fixed_parameters,
        control_estimators,
    )
    if not callable(tuned_fit) or not callable(control_fit):
        raise TypeError("tuned_fit и control_fit должны быть вызываемыми")

    outer_rows: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for outer_random_state in contract.outer_random_states:
        outer_cv = build_outer_splitter(
            contract.outer_n_splits,
            contract.outer_n_repeats,
            outer_random_state,
        )
        for split_number, (train_index, test_index) in enumerate(
            outer_cv.split(X, y_array)
        ):
            tuned_row, selected_row, tuned_warnings = tuned_fit(
                candidate_bundle=candidate_bundle,
                X=X,
                y=y_array,
                train_index=train_index,
                test_index=test_index,
                zero_based_outer_split_number=split_number,
                feature_names=feature_names,
                parameter_grid=parameter_grid,
                fixed_parameters=fixed_parameters,
                protocol_id=contract.nested_protocol_id,
                candidate_id=contract.candidate_id,
                outer_n_splits=contract.outer_n_splits,
                outer_n_repeats=contract.outer_n_repeats,
                inner_n_splits=contract.inner_n_splits,
                base_random_state=contract.hgb_random_state,
                inner_base_random_state=outer_random_state,
                feature_policy_id=contract.feature_policy_id,
                scoring="average_precision",
                refit=True,
                n_jobs=1,
                return_train_score=False,
                error_score="raise",
                row_status=STAGE05_SEED_ROW_STATUS,
                interpretation_allowed=STAGE05_SEED_INTERPRETATION_RU,
                numeric_runtime_contract=None,
            )
            if not isinstance(tuned_warnings, list):
                raise TypeError("tuned_fit warnings должен быть списком")
            adapted_selected = _adapt_selected_params_row(
                selected_row,
                contract,
                outer_random_state,
            )
            outer_rows.append(
                _adapt_outer_score_row(
                    tuned_row,
                    contract,
                    outer_random_state,
                    selected_row,
                )
            )
            selected_rows.append(adapted_selected)

            for model_id in ("dummy_prior", "logistic_regression"):
                control_row, control_warnings = control_fit(
                    candidate_bundle=candidate_bundle,
                    X=X,
                    y=y_array,
                    train_index=train_index,
                    test_index=test_index,
                    model_id=model_id,
                    estimator_template=control_estimators[model_id],
                    zero_based_outer_split_number=split_number,
                    feature_names=feature_names,
                    protocol_id=contract.nested_protocol_id,
                    candidate_id=contract.candidate_id,
                    outer_n_splits=contract.outer_n_splits,
                    outer_n_repeats=contract.outer_n_repeats,
                    inner_n_splits=contract.inner_n_splits,
                    feature_policy_id=contract.feature_policy_id,
                    row_status=STAGE05_SEED_ROW_STATUS,
                    interpretation_allowed=STAGE05_SEED_INTERPRETATION_RU,
                    numeric_runtime_contract=None,
                )
                if not isinstance(control_warnings, list):
                    raise TypeError("control_fit warnings должен быть списком")
                outer_rows.append(
                    _adapt_outer_score_row(
                        control_row,
                        contract,
                        outer_random_state,
                        None,
                    )
                )

    outer = pd.DataFrame(outer_rows, columns=STAGE05_SEED_OUTER_COLUMNS)
    selected = pd.DataFrame(
        selected_rows,
        columns=STAGE05_SEED_SELECTED_COLUMNS,
    )
    summary = build_seed_stability_summary(outer, contract)
    bundle = SeedStabilityBundle(
        outer_scores=outer,
        selected_params=selected,
        summary=summary,
    )
    validate_seed_stability_bundle(bundle, contract)
    return bundle


STAGE05_SPLIT_10X1_ID = "ST05_03a_split_protocol_10x1"
STAGE05_SPLIT_10X1_RUN_GROUP = "nested_split_sensitivity_v01"
STAGE05_SPLIT_10X1_PROTOCOL_VARIANT_ID = "nested_10x1_seed_grid_v01"
STAGE05_SPLIT_10X1_RANDOM_STATES = (20260507, 20260517, 20260527)
STAGE05_SPLIT_10X1_OUTER_N_SPLITS = 10
STAGE05_SPLIT_10X1_OUTER_N_REPEATS = 1
STAGE05_SPLIT_10X1_INNER_N_SPLITS = 3
STAGE05_SPLIT_10X1_ROW_STATUS = "stage05_split_protocol_sensitivity_score"
STAGE05_SPLIT_10X1_SUMMARY_ROW_STATUS = (
    "stage05_split_protocol_sensitivity_summary"
)
STAGE05_SPLIT_10X1_INTERPRETATION_RU = (
    "Использовать только для проверки чувствительности утверждения к "
    "протоколу 10x1; не объединять с 5x2 без отдельного evidence record."
)
STAGE05_SPLIT_10X1_ALL_INTERPRETATION_RU = (
    "Сводка по всем зафиксированным зернам случайности протокола 10x1; "
    "не объединять с 5x2 без отдельного evidence record."
)
STAGE05_SPLIT_10X1_SINGLE_INTERPRETATION_RU = (
    "Сводка по одному зерну случайности внешнего разбиения 10x1; "
    "используется только внутри ST05_03a."
)
STAGE05_SPLIT_10X1_MODEL_ORDER = STAGE05_SEED_MODEL_ORDER
STAGE05_SPLIT_10X1_COMPARISON_ORDER = STAGE05_SEED_COMPARISON_ORDER
STAGE05_SPLIT_10X1_METRIC_ORDER = STAGE05_SEED_METRIC_ORDER

STAGE05_SPLIT_10X1_OUTER_COLUMNS = (
    "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
    "candidate_id", "openml_dataset_id", "dataset_name", "target_name",
    "target_class_0", "target_class_1", "positive_class_assumption",
    "outer_random_state", "outer_split_number", "outer_repeat_number",
    "outer_fold_number", "outer_cv_method", "outer_cv_n_splits",
    "outer_cv_n_repeats", "inner_cv_method", "inner_cv_n_splits",
    "inner_random_state", "train_size", "test_size",
    "train_positive_share", "test_positive_share", "feature_count",
    "model_id", "model_role", "selected_parameter_set_id",
    "selected_params_json", "inner_best_average_precision",
    "inner_candidate_count", "fit_seconds", "predict_seconds", "roc_auc",
    "average_precision", "pr_auc", "f1", "balanced_accuracy", "log_loss",
    "brier_score", "row_status", "interpretation_allowed_ru",
)
STAGE05_SPLIT_10X1_SUMMARY_COLUMNS = STAGE05_SEED_SUMMARY_COLUMNS


@dataclass(frozen=True)
class Split10x1Contract:
    stress_test_id: str
    claim_id: str
    run_group: str
    protocol_variant_id: str
    nested_protocol_id: str
    candidate_id: str
    outer_random_states: tuple[int, ...]
    outer_n_splits: int
    outer_n_repeats: int
    inner_n_splits: int
    hgb_random_state: int
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class Split10x1Bundle:
    outer_scores: pd.DataFrame
    summary: pd.DataFrame


def build_locked_split_10x1_contract() -> Split10x1Contract:
    """Return the immutable local representation of registered ST05_03a."""
    return Split10x1Contract(
        stress_test_id=STAGE05_SPLIT_10X1_ID,
        claim_id=STAGE05_SEED_CLAIM_ID,
        run_group=STAGE05_SPLIT_10X1_RUN_GROUP,
        protocol_variant_id=STAGE05_SPLIT_10X1_PROTOCOL_VARIANT_ID,
        nested_protocol_id=STAGE05_SEED_NESTED_PROTOCOL_ID,
        candidate_id=STAGE05_SEED_CANDIDATE_ID,
        outer_random_states=STAGE05_SPLIT_10X1_RANDOM_STATES,
        outer_n_splits=STAGE05_SPLIT_10X1_OUTER_N_SPLITS,
        outer_n_repeats=STAGE05_SPLIT_10X1_OUTER_N_REPEATS,
        inner_n_splits=STAGE05_SPLIT_10X1_INNER_N_SPLITS,
        hgb_random_state=STAGE05_SEED_HGB_RANDOM_STATE,
        feature_names=STAGE05_SEED_FEATURE_NAMES,
    )


def build_split_10x1_contract(
    stress_test_plan: pd.DataFrame,
    claim_registry: pd.DataFrame,
) -> Split10x1Contract:
    """Validate the preregistered ST05_03a row and return its locked contract."""
    if not isinstance(stress_test_plan, pd.DataFrame):
        raise TypeError("stress_test_plan должен быть pandas.DataFrame")
    if not isinstance(claim_registry, pd.DataFrame):
        raise TypeError("claim_registry должен быть pandas.DataFrame")
    require_columns(
        stress_test_plan,
        (*_PLAN_REQUIRED_COLUMNS, "planned_outputs"),
        "ST05_03a stress-test plan",
    )
    require_columns(
        claim_registry,
        _CLAIM_REQUIRED_COLUMNS,
        "ST05_03a claim registry",
    )
    rows = stress_test_plan[
        stress_test_plan["stress_test_id"].eq(STAGE05_SPLIT_10X1_ID)
    ]
    if len(rows) != 1:
        raise ValueError("Для ST05_03a требуется ровно одна строка plan")
    row = rows.iloc[0]
    expected_text = {
        "claim_id": STAGE05_SEED_CLAIM_ID,
        "requires_new_model_run": "yes",
        "run_group": STAGE05_SPLIT_10X1_RUN_GROUP,
        "protocol_variant_id": STAGE05_SPLIT_10X1_PROTOCOL_VARIANT_ID,
        "outer_cv_method": "RepeatedStratifiedKFold",
        "inner_cv_method": "StratifiedKFold",
        "models": "hist_gradient_boosting;logistic_regression;dummy_prior",
        "primary_metric": "average_precision",
        "parameter_space_policy": "same_locked_space_as_nested_cv_v01",
        "priority": "should_have",
        "execution_order": "3",
        "decision_status": "locked_before_stage05_runs",
        "planned_outputs": (
            "openml_miniboone_stage05_split_10x1_outer_scores.csv;"
            "openml_miniboone_stage05_split_10x1_summary.csv"
        ),
    }
    for column, expected in expected_text.items():
        _require_exact_text(row[column], expected, f"plan.{column}")
    for column, expected in (
        ("outer_cv_n_splits", STAGE05_SPLIT_10X1_OUTER_N_SPLITS),
        ("outer_cv_n_repeats", STAGE05_SPLIT_10X1_OUTER_N_REPEATS),
        ("inner_cv_n_splits", STAGE05_SPLIT_10X1_INNER_N_SPLITS),
    ):
        _require_exact_integer(row[column], expected, f"plan.{column}")
    try:
        states = tuple(
            int(value.strip())
            for value in str(row["outer_random_states"]).split(";")
            if value.strip()
        )
    except ValueError as error:
        raise ValueError("plan.outer_random_states содержит нецелое seed") from error
    if states != STAGE05_SPLIT_10X1_RANDOM_STATES:
        raise ValueError("Порядок и значения ST05_03a outer seeds изменены")
    claims = claim_registry[
        claim_registry["claim_id"].eq(STAGE05_SEED_CLAIM_ID)
    ]
    if len(claims) != 1:
        raise ValueError("Для ST05_03a требуется ровно одна строка claim")
    claim = claims.iloc[0]
    _require_exact_text(
        claim["candidate_id"], STAGE05_SEED_CANDIDATE_ID, "claim.candidate_id"
    )
    _require_exact_text(
        claim["current_protocol_id"],
        STAGE05_SEED_NESTED_PROTOCOL_ID,
        "claim.current_protocol_id",
    )
    _require_exact_text(
        claim["decision_status"],
        "locked_before_stage05_runs",
        "claim.decision_status",
    )
    return build_locked_split_10x1_contract()


def build_split_10x1_control_estimators() -> dict[str, Any]:
    """Build control templates in the historical ST05_03a order."""
    return build_seed_stability_control_estimators()


def _adapt_split_10x1_outer_row(
    row: dict[str, Any],
    selected_row: dict[str, Any] | None,
    contract: Split10x1Contract,
    outer_random_state: int,
) -> dict[str, Any]:
    if row.get("protocol_id") != contract.nested_protocol_id:
        raise ValueError("fit result имеет неверный nested protocol_id")
    tuned = row.get("model_role") == "tuned_candidate"
    if tuned != (selected_row is not None):
        raise ValueError("selected row должен присутствовать только для HGB")
    if tuned:
        inner_method = "StratifiedKFold"
        inner_n_splits: Any = selected_row["inner_cv_n_splits"]
        inner_random_state: Any = selected_row["inner_cv_random_state"]
        inner_best: Any = selected_row["inner_best_average_precision"]
        inner_count: Any = selected_row["inner_candidate_count"]
        model_role = "tuned_candidate"
        parameter_set_id = row["selected_parameter_set_id"]
        selected_json = row["selected_params_json"]
    else:
        inner_method = "not_applicable"
        inner_n_splits = ""
        inner_random_state = "not_applicable"
        inner_best = "not_applicable"
        inner_count = "not_applicable"
        model_role = (
            "baseline" if row["model_id"] == "logistic_regression"
            else "lower_bound"
        )
        parameter_set_id = "not_applicable"
        selected_json = ""
    return {
        "stress_test_id": contract.stress_test_id,
        "claim_id": contract.claim_id,
        "run_group": contract.run_group,
        "protocol_variant_id": contract.protocol_variant_id,
        "candidate_id": row["candidate_id"],
        "openml_dataset_id": row["openml_dataset_id"],
        "dataset_name": row["dataset_name"],
        "target_name": row["target_name"],
        "target_class_0": row["target_class_0"],
        "target_class_1": row["target_class_1"],
        "positive_class_assumption": row["positive_class_assumption"],
        "outer_random_state": outer_random_state,
        "outer_split_number": row["outer_split_number"],
        "outer_repeat_number": row["outer_repeat_number"],
        "outer_fold_number": row["outer_fold_number"],
        "outer_cv_method": "RepeatedStratifiedKFold",
        "outer_cv_n_splits": row["outer_cv_n_splits"],
        "outer_cv_n_repeats": row["outer_cv_n_repeats"],
        "inner_cv_method": inner_method,
        "inner_cv_n_splits": inner_n_splits,
        "inner_random_state": inner_random_state,
        "train_size": row["n_train"],
        "test_size": row["n_test"],
        "train_positive_share": row["train_positive_share"],
        "test_positive_share": row["test_positive_share"],
        "feature_count": row["feature_count"],
        "model_id": row["model_id"],
        "model_role": model_role,
        "selected_parameter_set_id": parameter_set_id,
        "selected_params_json": selected_json,
        "inner_best_average_precision": inner_best,
        "inner_candidate_count": inner_count,
        "fit_seconds": row["fit_seconds"],
        "predict_seconds": row["predict_seconds"],
        "roc_auc": row["roc_auc"],
        "average_precision": row["average_precision"],
        "pr_auc": row["pr_auc"],
        "f1": row["f1"],
        "balanced_accuracy": row["balanced_accuracy"],
        "log_loss": row["log_loss"],
        "brier_score": row["brier_score"],
        "row_status": STAGE05_SPLIT_10X1_ROW_STATUS,
        "interpretation_allowed_ru": STAGE05_SPLIT_10X1_INTERPRETATION_RU,
    }


def build_split_10x1_summary(
    outer_scores: pd.DataFrame,
    contract: Split10x1Contract,
) -> pd.DataFrame:
    """Build the registered paired ST05_03a summary in canonical row order."""
    if not isinstance(outer_scores, pd.DataFrame):
        raise TypeError("outer_scores должен быть pandas.DataFrame")
    require_columns(
        outer_scores,
        (
            "outer_random_state", "outer_split_number", "outer_repeat_number",
            "outer_fold_number", "model_id", *STAGE05_SPLIT_10X1_METRIC_ORDER,
        ),
        "ST05_03a outer scores",
    )
    key = [
        "outer_random_state", "outer_split_number", "outer_repeat_number",
        "outer_fold_number",
    ]
    hgb = outer_scores[outer_scores["model_id"].eq("hist_gradient_boosting")]
    rows: list[dict[str, Any]] = []
    roles = {
        "dummy_prior": "lower_bound_model",
        "logistic_regression": "primary_baseline",
    }
    for comparison in STAGE05_SPLIT_10X1_COMPARISON_ORDER:
        paired = hgb.merge(
            outer_scores[outer_scores["model_id"].eq(comparison)],
            on=key,
            suffixes=("_hgb", "_comparison"),
            validate="one_to_one",
        )
        for metric in STAGE05_SPLIT_10X1_METRIC_ORDER:
            candidate = pd.to_numeric(paired[f"{metric}_hgb"], errors="raise")
            baseline = pd.to_numeric(
                paired[f"{metric}_comparison"], errors="raise"
            )
            direction = METRIC_DIRECTIONS[metric]
            raw = candidate - baseline
            advantages = raw if direction == "higher_is_better" else -raw
            metric_frame = paired[key].copy()
            metric_frame["advantage"] = advantages.astype(float)
            groups: list[tuple[str, Any, pd.DataFrame]] = [
                ("all_outer_random_states", "all", metric_frame)
            ]
            groups.extend(
                (
                    "single_outer_random_state",
                    seed,
                    metric_frame[
                        metric_frame["outer_random_state"].astype(str).eq(str(seed))
                    ],
                )
                for seed in contract.outer_random_states
            )
            for scope, seed, group in groups:
                values = group["advantage"].astype(float)
                rows.append({
                    "stress_test_id": contract.stress_test_id,
                    "claim_id": contract.claim_id,
                    "run_group": contract.run_group,
                    "protocol_variant_id": contract.protocol_variant_id,
                    "summary_scope": scope,
                    "outer_random_state": seed,
                    "candidate_id": contract.candidate_id,
                    "comparison_role": roles[comparison],
                    "candidate_model_id": "hist_gradient_boosting",
                    "comparison_model_id": comparison,
                    "metric_name": metric,
                    "metric_direction": direction,
                    "n_blocks": int(len(group)),
                    "advantage_mean": float(values.mean()),
                    "advantage_std_population": float(values.std(ddof=0)),
                    "advantage_min": float(values.min()),
                    "advantage_max": float(values.max()),
                    "candidate_positive_blocks": int((values > 0).sum()),
                    "candidate_negative_blocks": int((values < 0).sum()),
                    "candidate_zero_blocks": int((values == 0).sum()),
                    "row_status": STAGE05_SPLIT_10X1_SUMMARY_ROW_STATUS,
                    "interpretation_allowed_ru": (
                        STAGE05_SPLIT_10X1_ALL_INTERPRETATION_RU
                        if scope == "all_outer_random_states"
                        else STAGE05_SPLIT_10X1_SINGLE_INTERPRETATION_RU
                    ),
                })
    return pd.DataFrame(rows, columns=STAGE05_SPLIT_10X1_SUMMARY_COLUMNS)


def validate_split_10x1_bundle(
    bundle: Split10x1Bundle,
    contract: Split10x1Contract,
) -> None:
    """Fail closed on ST05_03a schemas, keys, order, seed policy, and summary."""
    if not isinstance(bundle, Split10x1Bundle):
        raise TypeError("bundle должен быть Split10x1Bundle")
    if contract != build_locked_split_10x1_contract():
        raise ValueError("Split10x1Contract не совпадает с locked ST05_03a")
    outer, summary = bundle.outer_scores, bundle.summary
    for frame, name in ((outer, "outer scores"), (summary, "summary")):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name} должен быть pandas.DataFrame")
        require_non_empty(frame, name)
    _require_exact_columns(
        outer, STAGE05_SPLIT_10X1_OUTER_COLUMNS, "outer scores"
    )
    _require_exact_columns(
        summary, STAGE05_SPLIT_10X1_SUMMARY_COLUMNS, "summary"
    )
    expected_blocks = len(contract.outer_random_states) * contract.outer_n_splits
    if (len(outer), len(summary)) != (expected_blocks * 3, 48):
        raise ValueError("Нарушено зарегистрированное число строк ST05_03a")
    require_unique_key(
        outer,
        ["stress_test_id", "outer_random_state", "outer_split_number", "model_id"],
        "outer scores",
    )
    require_unique_key(
        summary,
        [
            "stress_test_id", "comparison_model_id", "metric_name",
            "summary_scope", "outer_random_state",
        ],
        "summary",
    )
    expected_outer_order = [
        (seed, split, model)
        for seed in contract.outer_random_states
        for split in range(1, contract.outer_n_splits + 1)
        for model in STAGE05_SPLIT_10X1_MODEL_ORDER
    ]
    actual_outer_order = [
        (int(seed), int(split), str(model))
        for seed, split, model in outer[
            ["outer_random_state", "outer_split_number", "model_id"]
        ].itertuples(index=False, name=None)
    ]
    if actual_outer_order != expected_outer_order:
        raise ValueError("Нарушен порядок seed → split → model")
    expected_summary_order = [
        (comparison, metric, scope, seed)
        for comparison in STAGE05_SPLIT_10X1_COMPARISON_ORDER
        for metric in STAGE05_SPLIT_10X1_METRIC_ORDER
        for scope, seed in (
            [("all_outer_random_states", "all")]
            + [("single_outer_random_state", state) for state in contract.outer_random_states]
        )
    ]
    actual_summary_order = [
        (comparison, metric, scope, "all" if str(seed) == "all" else int(seed))
        for comparison, metric, scope, seed in summary[
            ["comparison_model_id", "metric_name", "summary_scope", "outer_random_state"]
        ].itertuples(index=False, name=None)
    ]
    if actual_summary_order != expected_summary_order:
        raise ValueError("Нарушен зарегистрированный порядок summary")
    static_outer = {
        "stress_test_id": contract.stress_test_id,
        "claim_id": contract.claim_id,
        "run_group": contract.run_group,
        "protocol_variant_id": contract.protocol_variant_id,
        "candidate_id": contract.candidate_id,
        "outer_cv_method": "RepeatedStratifiedKFold",
        "outer_cv_n_splits": contract.outer_n_splits,
        "outer_cv_n_repeats": contract.outer_n_repeats,
        "feature_count": len(contract.feature_names),
        "row_status": STAGE05_SPLIT_10X1_ROW_STATUS,
    }
    for column, expected in static_outer.items():
        if not outer[column].astype(str).eq(str(expected)).all():
            raise ValueError(f"outer scores содержит неверный {column}")
    roles = {
        "hist_gradient_boosting": "tuned_candidate",
        "dummy_prior": "lower_bound",
        "logistic_regression": "baseline",
    }
    if any(
        roles.get(row.model_id) != row.model_role
        for row in outer[["model_id", "model_role"]].itertuples(index=False)
    ):
        raise ValueError("Нарушено отображение model_id → model_role")
    hgb = outer[outer["model_id"].eq("hist_gradient_boosting")]
    controls = outer[~outer["model_id"].eq("hist_gradient_boosting")]
    if not (
        hgb["inner_cv_method"].eq("StratifiedKFold").all()
        and hgb["inner_cv_n_splits"].astype(int).eq(contract.inner_n_splits).all()
        and hgb["inner_random_state"].astype(int).eq(
            hgb["outer_random_state"].astype(int)
        ).all()
        and hgb["inner_candidate_count"].astype(int).eq(16).all()
        and controls["inner_cv_method"].eq("not_applicable").all()
        and controls["inner_cv_n_splits"].eq("").all()
        and controls["inner_random_state"].eq("not_applicable").all()
        and controls["selected_parameter_set_id"].eq("not_applicable").all()
        and controls["selected_params_json"].eq("").all()
    ):
        raise ValueError("Нарушен inner-CV или control-row контракт")
    for row in hgb.itertuples(index=False):
        params = json.loads(row.selected_params_json)
        if row.selected_parameter_set_id != make_hgb_parameter_set_id(params):
            raise ValueError("HGB parameter-set ID не соответствует JSON")
    if not outer["average_precision"].eq(outer["pr_auc"]).all():
        raise ValueError("Нарушен historical average_precision/pr_auc alias")
    _require_finite_nonnegative(outer, ("fit_seconds", "predict_seconds"))
    for column in STAGE05_SPLIT_10X1_METRIC_ORDER:
        values = pd.to_numeric(outer[column], errors="raise").to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError(f"{column} должен быть конечным")
    rebuilt = build_split_10x1_summary(outer, contract)
    exact_summary_columns = [
        column
        for column in STAGE05_SPLIT_10X1_SUMMARY_COLUMNS
        if column
        not in {
            "advantage_mean",
            "advantage_std_population",
            "advantage_min",
            "advantage_max",
        }
    ]
    pd.testing.assert_frame_equal(
        summary[exact_summary_columns].reset_index(drop=True).astype(str),
        rebuilt[exact_summary_columns].reset_index(drop=True).astype(str),
        check_exact=True,
    )
    for row in summary.itertuples(index=False):
        values = (
            float(row.advantage_mean),
            float(row.advantage_std_population),
            float(row.advantage_min),
            float(row.advantage_max),
        )
        if not all(np.isfinite(value) for value in values):
            raise ValueError("Summary float-агрегаты должны быть конечными")
        tolerance = 16 * np.finfo(float).eps * max(
            1.0, abs(values[0]), abs(values[2]), abs(values[3])
        )
        if (
            values[1] < 0.0
            or values[0] < values[2] - tolerance
            or values[0] > values[3] + tolerance
        ):
            raise ValueError("Summary float-агрегаты нарушают range/std инвариант")


def run_split_10x1_grid(
    contract: Split10x1Contract,
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
    control_estimators: dict[str, Any],
    *,
    tuned_fit: TunedFit = fit_tuned_hist_gradient_boosting_on_outer_block,
    control_fit: ControlFit = fit_control_estimator_on_outer_block,
) -> Split10x1Bundle:
    """Execute registered ST05_03a while keeping inner seed equal to outer seed."""
    if contract != build_locked_split_10x1_contract():
        raise ValueError("Split10x1Contract не совпадает с locked ST05_03a")
    seed_contract = build_locked_seed_stability_contract()
    y_array = _validate_execution_inputs(
        seed_contract,
        candidate_bundle,
        X,
        y,
        feature_names,
        parameter_grid,
        fixed_parameters,
        control_estimators,
    )
    if not callable(tuned_fit) or not callable(control_fit):
        raise TypeError("tuned_fit и control_fit должны быть вызываемыми")
    rows: list[dict[str, Any]] = []
    for outer_random_state in contract.outer_random_states:
        outer_cv = build_outer_splitter(
            contract.outer_n_splits,
            contract.outer_n_repeats,
            outer_random_state,
        )
        for split_number, (train_index, test_index) in enumerate(
            outer_cv.split(X, y_array)
        ):
            tuned_row, selected_row, tuned_warnings = tuned_fit(
                candidate_bundle=candidate_bundle,
                X=X,
                y=y_array,
                train_index=train_index,
                test_index=test_index,
                zero_based_outer_split_number=split_number,
                feature_names=feature_names,
                parameter_grid=parameter_grid,
                fixed_parameters=fixed_parameters,
                protocol_id=contract.nested_protocol_id,
                candidate_id=contract.candidate_id,
                outer_n_splits=contract.outer_n_splits,
                outer_n_repeats=contract.outer_n_repeats,
                inner_n_splits=contract.inner_n_splits,
                base_random_state=contract.hgb_random_state,
                inner_base_random_state=outer_random_state,
                add_outer_split_to_inner_random_state=False,
                feature_policy_id=STAGE05_SEED_FEATURE_POLICY_ID,
                scoring="average_precision",
                refit=True,
                n_jobs=1,
                return_train_score=False,
                error_score="raise",
                row_status=STAGE05_SPLIT_10X1_ROW_STATUS,
                interpretation_allowed=STAGE05_SPLIT_10X1_INTERPRETATION_RU,
                numeric_runtime_contract=None,
            )
            if not isinstance(tuned_warnings, list):
                raise TypeError("tuned_fit warnings должен быть списком")
            rows.append(
                _adapt_split_10x1_outer_row(
                    tuned_row, selected_row, contract, outer_random_state
                )
            )
            for model_id in ("dummy_prior", "logistic_regression"):
                control_row, control_warnings = control_fit(
                    candidate_bundle=candidate_bundle,
                    X=X,
                    y=y_array,
                    train_index=train_index,
                    test_index=test_index,
                    model_id=model_id,
                    estimator_template=control_estimators[model_id],
                    zero_based_outer_split_number=split_number,
                    feature_names=feature_names,
                    protocol_id=contract.nested_protocol_id,
                    candidate_id=contract.candidate_id,
                    outer_n_splits=contract.outer_n_splits,
                    outer_n_repeats=contract.outer_n_repeats,
                    inner_n_splits=contract.inner_n_splits,
                    feature_policy_id=STAGE05_SEED_FEATURE_POLICY_ID,
                    row_status=STAGE05_SPLIT_10X1_ROW_STATUS,
                    interpretation_allowed=STAGE05_SPLIT_10X1_INTERPRETATION_RU,
                    numeric_runtime_contract=None,
                )
                if not isinstance(control_warnings, list):
                    raise TypeError("control_fit warnings должен быть списком")
                rows.append(
                    _adapt_split_10x1_outer_row(
                        control_row, None, contract, outer_random_state
                    )
                )
    outer = pd.DataFrame(rows, columns=STAGE05_SPLIT_10X1_OUTER_COLUMNS)
    bundle = Split10x1Bundle(
        outer_scores=outer,
        summary=build_split_10x1_summary(outer, contract),
    )
    validate_split_10x1_bundle(bundle, contract)
    return bundle


STAGE05_NON_NESTED_ID = "ST05_07_non_nested_optimism_probe"
STAGE05_NON_NESTED_RUN_GROUP = "non_nested_optimism_probe_v01"
STAGE05_NON_NESTED_PROTOCOL_VARIANT_ID = "non_nested_grid_search_cv_v01"
STAGE05_NON_NESTED_RANDOM_STATES = (20260507, 20260517, 20260527)
STAGE05_NON_NESTED_N_SPLITS = 5
STAGE05_NON_NESTED_N_REPEATS = 2
STAGE05_NON_NESTED_MODEL_ID = "hist_gradient_boosting"
STAGE05_NON_NESTED_FEATURE_POLICY_ID = "numeric_particleid_0_49_locked"
STAGE05_NON_NESTED_ROW_STATUS = "stage05_non_nested_optimism_probe_derived"
STAGE05_NON_NESTED_POSITIVE_STATUS = (
    "non_nested_score_above_nested_reference"
)
STAGE05_NON_NESTED_NONPOSITIVE_STATUS = (
    "non_nested_score_not_above_nested_reference"
)
STAGE05_NON_NESTED_POSITIVE_STATUS_RU = (
    "Невложенная оценка выше выбранной вложенной внешней оценки; "
    "зафиксирован потенциальный оптимистический сдвиг."
)
STAGE05_NON_NESTED_NONPOSITIVE_STATUS_RU = (
    "Невложенная оценка не выше выбранной вложенной внешней оценки; "
    "по данному сравнению оптимистический сдвиг не обнаружен."
)
STAGE05_NON_NESTED_INTERPRETATION_RU = (
    "Разрешено использовать только для диагностики риска оптимистического "
    "смещения невложенной оценки; строка не заменяет вложенную внешнюю "
    "оценку качества."
)
STAGE05_NON_NESTED_OUTPUT_NAME = (
    "openml_miniboone_stage05_non_nested_optimism_probe.csv"
)
STAGE05_NON_NESTED_COLUMNS = (
    "stress_test_id", "claim_id", "run_group", "protocol_variant_id",
    "candidate_id", "openml_dataset_id", "dataset_name", "target_name",
    "target_class_0", "target_class_1", "positive_class_assumption",
    "model_id", "model_role", "feature_policy_id", "feature_count",
    "single_level_cv_method", "single_level_cv_n_splits",
    "single_level_cv_n_repeats", "single_level_cv_random_state",
    "single_level_cv_blocks", "parameter_space_policy",
    "selected_parameter_set_id", "selected_params_json",
    "grid_candidate_count", "non_nested_average_precision_mean",
    "non_nested_average_precision_std_for_selected_params", "fit_seconds",
    "comparison_reference_id", "comparison_reference_source_file",
    "comparison_reference_stress_test_id",
    "comparison_reference_protocol_variant_id",
    "comparison_reference_random_state_scope", "nested_outer_blocks",
    "nested_average_precision_mean",
    "optimism_delta_non_nested_minus_nested", "audit_status",
    "audit_status_ru", "row_status", "interpretation_allowed_ru",
)
STAGE05_NON_NESTED_REFERENCE_COLUMNS = (
    "comparison_reference_id", "comparison_reference_source_file",
    "comparison_reference_stress_test_id",
    "comparison_reference_protocol_variant_id",
    "comparison_reference_random_state_scope", "nested_outer_blocks",
    "nested_average_precision_mean",
)


@dataclass(frozen=True)
class NonNestedOptimismContract:
    stress_test_id: str
    claim_id: str
    run_group: str
    protocol_variant_id: str
    nested_protocol_id: str
    candidate_id: str
    model_id: str
    random_states: tuple[int, ...]
    n_splits: int
    n_repeats: int
    scoring: str
    parameter_space_policy: str
    feature_policy_id: str
    feature_names: tuple[str, ...]
    references_per_seed: int
    output_name: str
    grid_candidate_count: int
    delta_formula: str
    positive_status: str
    nonpositive_status: str
    row_status: str


@dataclass(frozen=True)
class NonNestedReference:
    comparison_reference_id: str
    comparison_reference_source_file: str
    comparison_reference_stress_test_id: str
    comparison_reference_protocol_variant_id: str
    comparison_reference_random_state_scope: str
    nested_outer_blocks: int
    nested_average_precision_mean: float


@dataclass(frozen=True)
class NonNestedOptimismBundle:
    audit: pd.DataFrame
    reference_table: pd.DataFrame
    parameter_grid: dict[str, list[Any]]


def build_locked_non_nested_optimism_contract() -> NonNestedOptimismContract:
    """Return the immutable local representation of the registered ST05_07."""
    return NonNestedOptimismContract(
        stress_test_id=STAGE05_NON_NESTED_ID,
        claim_id=STAGE05_SEED_CLAIM_ID,
        run_group=STAGE05_NON_NESTED_RUN_GROUP,
        protocol_variant_id=STAGE05_NON_NESTED_PROTOCOL_VARIANT_ID,
        nested_protocol_id=STAGE05_SEED_NESTED_PROTOCOL_ID,
        candidate_id=STAGE05_SEED_CANDIDATE_ID,
        model_id=STAGE05_NON_NESTED_MODEL_ID,
        random_states=STAGE05_NON_NESTED_RANDOM_STATES,
        n_splits=STAGE05_NON_NESTED_N_SPLITS,
        n_repeats=STAGE05_NON_NESTED_N_REPEATS,
        scoring="average_precision",
        parameter_space_policy="same_locked_space_as_nested_cv_v01",
        feature_policy_id=STAGE05_NON_NESTED_FEATURE_POLICY_ID,
        feature_names=STAGE05_SEED_FEATURE_NAMES,
        references_per_seed=5,
        output_name=STAGE05_NON_NESTED_OUTPUT_NAME,
        grid_candidate_count=16,
        delta_formula=(
            "non_nested_average_precision_mean-nested_average_precision_mean"
        ),
        positive_status=STAGE05_NON_NESTED_POSITIVE_STATUS,
        nonpositive_status=STAGE05_NON_NESTED_NONPOSITIVE_STATUS,
        row_status=STAGE05_NON_NESTED_ROW_STATUS,
    )


def build_non_nested_optimism_contract(
    stress_test_plan: pd.DataFrame,
    claim_registry: pd.DataFrame,
) -> NonNestedOptimismContract:
    """Validate preregistered ST05_07 plan/claim rows and return the contract."""
    if not isinstance(stress_test_plan, pd.DataFrame):
        raise TypeError("stress_test_plan должен быть pandas.DataFrame")
    if not isinstance(claim_registry, pd.DataFrame):
        raise TypeError("claim_registry должен быть pandas.DataFrame")
    required_plan = (
        "stress_test_id", "claim_id", "family", "requires_new_model_run",
        "run_group", "protocol_variant_id", "outer_cv_method",
        "outer_cv_n_splits", "outer_cv_n_repeats", "outer_random_states",
        "inner_cv_method", "inner_cv_n_splits", "models", "primary_metric",
        "parameter_space_policy", "comparison_unit", "planned_outputs",
        "priority", "execution_order", "decision_status",
    )
    required_claim = (
        "claim_id", "candidate_id", "candidate_model_id", "primary_metric",
        "current_protocol_id", "decision_status",
    )
    require_columns(stress_test_plan, required_plan, "ST05_07 stress-test plan")
    require_columns(claim_registry, required_claim, "ST05_07 claim registry")
    plan_rows = stress_test_plan[
        stress_test_plan["stress_test_id"].eq(STAGE05_NON_NESTED_ID)
    ]
    if len(plan_rows) != 1:
        raise ValueError("Для ST05_07 требуется ровно одна строка stress-test plan")
    plan = plan_rows.iloc[0]
    expected_plan = {
        "claim_id": STAGE05_SEED_CLAIM_ID,
        "family": "selection_bias_probe",
        "requires_new_model_run": "yes",
        "run_group": STAGE05_NON_NESTED_RUN_GROUP,
        "protocol_variant_id": STAGE05_NON_NESTED_PROTOCOL_VARIANT_ID,
        "outer_cv_method": "not_applicable_single_level_cv",
        "inner_cv_method": "GridSearchCV single-level repeated stratified CV",
        "inner_cv_n_splits": "not_applicable",
        "models": STAGE05_NON_NESTED_MODEL_ID,
        "primary_metric": "average_precision",
        "parameter_space_policy": "same_locked_space_as_nested_cv_v01",
        "comparison_unit": "protocol-level score difference",
        "planned_outputs": STAGE05_NON_NESTED_OUTPUT_NAME,
        "priority": "could_have",
        "execution_order": "8",
        "decision_status": "locked_before_stage05_runs",
    }
    for column, expected in expected_plan.items():
        _require_exact_text(plan[column], expected, f"plan.{column}")
    _require_exact_integer(
        plan["outer_cv_n_splits"], STAGE05_NON_NESTED_N_SPLITS,
        "plan.outer_cv_n_splits",
    )
    _require_exact_integer(
        plan["outer_cv_n_repeats"], STAGE05_NON_NESTED_N_REPEATS,
        "plan.outer_cv_n_repeats",
    )
    try:
        states = tuple(
            int(value.strip())
            for value in str(plan["outer_random_states"]).split(";")
            if value.strip()
        )
    except ValueError as error:
        raise ValueError("plan.outer_random_states содержит нецелое seed") from error
    if states != STAGE05_NON_NESTED_RANDOM_STATES:
        raise ValueError("Порядок и значения ST05_07 random_states изменены")
    claim_rows = claim_registry[
        claim_registry["claim_id"].eq(STAGE05_SEED_CLAIM_ID)
    ]
    if len(claim_rows) != 1:
        raise ValueError("Для ST05_07 требуется ровно одна строка claim")
    claim = claim_rows.iloc[0]
    expected_claim = {
        "candidate_id": STAGE05_SEED_CANDIDATE_ID,
        "candidate_model_id": STAGE05_NON_NESTED_MODEL_ID,
        "primary_metric": "average_precision",
        "current_protocol_id": STAGE05_SEED_NESTED_PROTOCOL_ID,
        "decision_status": "locked_before_stage05_runs",
    }
    for column, expected in expected_claim.items():
        _require_exact_text(claim[column], expected, f"claim.{column}")
    return build_locked_non_nested_optimism_contract()


def _require_numeric_series(
    frame: pd.DataFrame,
    column: str,
    context: str,
) -> pd.Series:
    require_columns(frame, (column,), context)
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(float)).all():
        raise ValueError(f"{context}.{column} должен содержать конечные числа")
    return values


def build_non_nested_reference_table(
    nested_summary: pd.DataFrame,
    seed_outer_scores: pd.DataFrame,
    split_10x1_outer_scores: pd.DataFrame,
    contract: NonNestedOptimismContract,
) -> pd.DataFrame:
    """Build the nine registered nested references without model fitting."""
    if contract != build_locked_non_nested_optimism_contract():
        raise ValueError("NonNestedOptimismContract не совпадает с locked ST05_07")
    for frame, name in (
        (nested_summary, "nested summary"),
        (seed_outer_scores, "ST05_02 outer scores"),
        (split_10x1_outer_scores, "ST05_03a outer scores"),
    ):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name} должен быть pandas.DataFrame")
        require_non_empty(frame, name)
        require_columns(frame, ("model_id",), name)
    references: list[NonNestedReference] = []
    original = nested_summary[
        nested_summary["model_id"].eq(contract.model_id)
    ].copy()
    if len(original) != 1:
        raise ValueError("Nested summary должен содержать ровно одну HGB-строку")
    references.append(NonNestedReference(
        "original_nested_5x2_seed_20260507",
        "data_registry/openml_miniboone_nested_summary.csv",
        "original_nested_cv_v01",
        "nested_5x2_seed_20260507_v01",
        "20260507",
        int(_require_numeric_series(original, "n_external_blocks", "nested summary").iloc[0]),
        float(_require_numeric_series(original, "average_precision_mean", "nested summary").iloc[0]),
    ))
    sources = (
        (
            seed_outer_scores, "ST05_02_seed_stability_grid",
            "nested_5x2_seed_grid_v01",
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
            "stage05_02_nested_5x2",
        ),
        (
            split_10x1_outer_scores, "ST05_03a_split_protocol_10x1",
            "nested_10x1_seed_grid_v01",
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
            "stage05_03a_nested_10x1",
        ),
    )
    for frame, stress_id, protocol_id, source_file, prefix in sources:
        require_columns(frame, ("outer_random_state", "average_precision"), source_file)
        hgb = frame[frame["model_id"].eq(contract.model_id)].copy()
        if hgb.empty:
            raise ValueError(f"{source_file} не содержит HGB-строк")
        all_values = _require_numeric_series(hgb, "average_precision", source_file)
        references.append(NonNestedReference(
            f"{prefix}_all_seeds", source_file, stress_id, protocol_id, "all",
            len(hgb), float(all_values.mean()),
        ))
        for state in contract.random_states:
            same_seed = hgb[
                hgb["outer_random_state"].astype(str).eq(str(state))
            ].copy()
            if same_seed.empty:
                raise ValueError(f"{source_file} не содержит HGB seed={state}")
            values = _require_numeric_series(
                same_seed, "average_precision", f"{source_file}/seed={state}"
            )
            references.append(NonNestedReference(
                f"{prefix}_seed_{state}", source_file, stress_id, protocol_id,
                str(state), len(same_seed), float(values.mean()),
            ))
    table = pd.DataFrame(
        [reference.__dict__ for reference in references],
        columns=STAGE05_NON_NESTED_REFERENCE_COLUMNS,
    )
    require_unique_key(table, ["comparison_reference_id"], "ST05_07 references")
    expected_ids = {
        "original_nested_5x2_seed_20260507",
        "stage05_02_nested_5x2_all_seeds",
        "stage05_03a_nested_10x1_all_seeds",
        *(f"stage05_02_nested_5x2_seed_{state}" for state in contract.random_states),
        *(f"stage05_03a_nested_10x1_seed_{state}" for state in contract.random_states),
    }
    if set(table["comparison_reference_id"]) != expected_ids or len(table) != 9:
        raise ValueError("Набор ST05_07 nested references изменён")
    return table


def select_non_nested_reference_rows(
    reference_table: pd.DataFrame,
    random_state: int,
    contract: NonNestedOptimismContract,
) -> pd.DataFrame:
    """Select five references for one seed in canonical output order."""
    if random_state not in contract.random_states:
        raise ValueError("random_state не зарегистрирован для ST05_07")
    expected = [
        "original_nested_5x2_seed_20260507",
        "stage05_02_nested_5x2_all_seeds",
        f"stage05_02_nested_5x2_seed_{random_state}",
        "stage05_03a_nested_10x1_all_seeds",
        f"stage05_03a_nested_10x1_seed_{random_state}",
    ]
    selected = reference_table[
        reference_table["comparison_reference_id"].isin(expected)
    ].copy()
    if len(selected) != contract.references_per_seed:
        raise ValueError("Для seed требуется ровно пять nested references")
    selected["comparison_reference_id"] = pd.Categorical(
        selected["comparison_reference_id"], categories=expected, ordered=True
    )
    return selected.sort_values("comparison_reference_id", kind="mergesort")


def classify_non_nested_optimism_delta(delta: float) -> tuple[str, str]:
    """Return the preregistered bilingual diagnostic status for one delta."""
    if not np.isfinite(float(delta)):
        raise ValueError("optimism delta должен быть конечным")
    if float(delta) > 0.0:
        return STAGE05_NON_NESTED_POSITIVE_STATUS, STAGE05_NON_NESTED_POSITIVE_STATUS_RU
    return (
        STAGE05_NON_NESTED_NONPOSITIVE_STATUS,
        STAGE05_NON_NESTED_NONPOSITIVE_STATUS_RU,
    )


def _validate_non_nested_execution_inputs(
    contract: NonNestedOptimismContract,
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
) -> np.ndarray:
    if contract != build_locked_non_nested_optimism_contract():
        raise ValueError("NonNestedOptimismContract не совпадает с locked ST05_07")
    if not isinstance(candidate_bundle, dict):
        raise TypeError("candidate_bundle должен быть словарём")
    if candidate_bundle.get("candidate_id") != contract.candidate_id:
        raise ValueError("candidate_bundle имеет неверный candidate_id")
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X должен быть pandas.DataFrame")
    if feature_names != list(contract.feature_names) or list(X.columns) != feature_names:
        raise ValueError("Нарушен locked ST05_07 feature contract")
    y_array = np.asarray(y)
    if y_array.ndim != 1 or len(y_array) != len(X) or len(X) == 0:
        raise ValueError("y должен быть непустым одномерным и соответствовать X")
    classes, counts = np.unique(y_array, return_counts=True)
    if len(classes) != 2 or counts.min() < contract.n_splits:
        raise ValueError("ST05_07 требует бинарный target с классами во всех folds")
    if set(parameter_grid) != EXPECTED_GRID_PARAMETERS:
        raise ValueError("parameter_grid имеет неверный набор параметров")
    if len(list(ParameterGrid(parameter_grid))) != 16:
        raise ValueError("parameter_grid должен задавать ровно 16 комбинаций")
    if set(fixed_parameters) != EXPECTED_FIXED_PARAMETERS:
        raise ValueError("fixed_parameters имеет неверный набор параметров")
    if fixed_parameters != {"random_state": 20260507, "early_stopping": "auto"}:
        raise ValueError("fixed_parameters не совпадает с locked HGB contract")
    return y_array


def validate_non_nested_optimism_bundle(
    bundle: NonNestedOptimismBundle,
    contract: NonNestedOptimismContract,
) -> None:
    """Fail closed on ST05_07 schema, keys, order, references, and relations."""
    if not isinstance(bundle, NonNestedOptimismBundle):
        raise TypeError("bundle должен быть NonNestedOptimismBundle")
    if contract != build_locked_non_nested_optimism_contract():
        raise ValueError("NonNestedOptimismContract не совпадает с locked ST05_07")
    audit, references = bundle.audit, bundle.reference_table
    for frame, name in ((audit, "ST05_07 audit"), (references, "references")):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name} должен быть pandas.DataFrame")
        require_non_empty(frame, name)
    _require_exact_columns(audit, STAGE05_NON_NESTED_COLUMNS, "ST05_07 audit")
    _require_exact_columns(
        references, STAGE05_NON_NESTED_REFERENCE_COLUMNS, "ST05_07 references"
    )
    if len(audit) != len(contract.random_states) * contract.references_per_seed:
        raise ValueError("ST05_07 audit должен содержать 15 строк")
    if len(references) != 9:
        raise ValueError("ST05_07 reference table должен содержать 9 строк")
    require_unique_key(
        audit, ["single_level_cv_random_state", "comparison_reference_id"],
        "ST05_07 audit",
    )
    require_unique_key(references, ["comparison_reference_id"], "references")
    expected_reference_metadata = {
        "original_nested_5x2_seed_20260507": (
            "data_registry/openml_miniboone_nested_summary.csv",
            "original_nested_cv_v01", "nested_5x2_seed_20260507_v01",
            "20260507", 10,
        ),
        "stage05_02_nested_5x2_all_seeds": (
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
            "ST05_02_seed_stability_grid", "nested_5x2_seed_grid_v01",
            "all", 50,
        ),
        "stage05_03a_nested_10x1_all_seeds": (
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
            "ST05_03a_split_protocol_10x1", "nested_10x1_seed_grid_v01",
            "all", 30,
        ),
    }
    for state in contract.random_states:
        expected_reference_metadata[f"stage05_02_nested_5x2_seed_{state}"] = (
            "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
            "ST05_02_seed_stability_grid", "nested_5x2_seed_grid_v01",
            str(state), 10,
        )
        expected_reference_metadata[f"stage05_03a_nested_10x1_seed_{state}"] = (
            "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
            "ST05_03a_split_protocol_10x1", "nested_10x1_seed_grid_v01",
            str(state), 10,
        )
    actual_reference_metadata = {
        str(row.comparison_reference_id): (
            str(row.comparison_reference_source_file),
            str(row.comparison_reference_stress_test_id),
            str(row.comparison_reference_protocol_variant_id),
            str(row.comparison_reference_random_state_scope),
            int(row.nested_outer_blocks),
        )
        for row in references.itertuples(index=False)
    }
    if actual_reference_metadata != expected_reference_metadata:
        raise ValueError("ST05_07 reference metadata/source/scope/blocks изменены")
    expected_order = [
        (state, reference_id)
        for state in contract.random_states
        for reference_id in (
            "original_nested_5x2_seed_20260507",
            "stage05_02_nested_5x2_all_seeds",
            f"stage05_02_nested_5x2_seed_{state}",
            "stage05_03a_nested_10x1_all_seeds",
            f"stage05_03a_nested_10x1_seed_{state}",
        )
    ]
    actual_order = [
        (int(state), str(reference_id))
        for state, reference_id in audit[
            ["single_level_cv_random_state", "comparison_reference_id"]
        ].itertuples(index=False, name=None)
    ]
    if actual_order != expected_order:
        raise ValueError("Нарушен порядок ST05_07 seed → reference")
    static = {
        "stress_test_id": contract.stress_test_id,
        "claim_id": contract.claim_id,
        "run_group": contract.run_group,
        "protocol_variant_id": contract.protocol_variant_id,
        "candidate_id": contract.candidate_id,
        "openml_dataset_id": "41150",
        "dataset_name": "MiniBooNE",
        "target_name": "signal",
        "target_class_0": "False",
        "target_class_1": "True",
        "positive_class_assumption": "True",
        "model_id": contract.model_id,
        "model_role": "single_level_tuned_candidate",
        "feature_policy_id": contract.feature_policy_id,
        "feature_count": str(len(contract.feature_names)),
        "single_level_cv_method": "RepeatedStratifiedKFold",
        "single_level_cv_n_splits": str(contract.n_splits),
        "single_level_cv_n_repeats": str(contract.n_repeats),
        "single_level_cv_blocks": str(contract.n_splits * contract.n_repeats),
        "parameter_space_policy": contract.parameter_space_policy,
        "grid_candidate_count": str(contract.grid_candidate_count),
        "row_status": contract.row_status,
        "interpretation_allowed_ru": STAGE05_NON_NESTED_INTERPRETATION_RU,
    }
    for column, expected in static.items():
        if not audit[column].astype(str).eq(expected).all():
            raise ValueError(f"ST05_07 audit содержит неверный {column}")
    if set(bundle.parameter_grid) != EXPECTED_GRID_PARAMETERS:
        raise ValueError("Bundle parameter_grid имеет неверные поля")
    if len(list(ParameterGrid(bundle.parameter_grid))) != contract.grid_candidate_count:
        raise ValueError("Bundle parameter_grid должен иметь 16 комбинаций")
    reference_map = references.set_index("comparison_reference_id")
    for state in contract.random_states:
        seed_rows = audit[
            audit["single_level_cv_random_state"].astype(int).eq(state)
        ]
        if len(seed_rows) != contract.references_per_seed:
            raise ValueError("Каждый seed должен иметь пять audit-строк")
        for column in (
            "selected_parameter_set_id", "selected_params_json",
            "non_nested_average_precision_mean",
            "non_nested_average_precision_std_for_selected_params", "fit_seconds",
        ):
            if seed_rows[column].astype(str).nunique() != 1:
                raise ValueError(f"{column} должен быть постоянным внутри seed")
    for row in audit.itertuples(index=False):
        if row.comparison_reference_id not in reference_map.index:
            raise ValueError("Audit содержит неизвестный reference_id")
        reference = reference_map.loc[row.comparison_reference_id]
        for column in STAGE05_NON_NESTED_REFERENCE_COLUMNS[1:-1]:
            if str(getattr(row, column)) != str(reference[column]):
                raise ValueError(f"Audit/reference расходятся по {column}")
        nested_value = float(row.nested_average_precision_mean)
        expected_nested = float(reference["nested_average_precision_mean"])
        non_nested_value = float(row.non_nested_average_precision_mean)
        delta = float(row.optimism_delta_non_nested_minus_nested)
        if nested_value != expected_nested or non_nested_value - nested_value != delta:
            raise ValueError("Нарушена ST05_07 reference/delta relation")
        expected_status = classify_non_nested_optimism_delta(delta)
        if (row.audit_status, row.audit_status_ru) != expected_status:
            raise ValueError("Audit status не соответствует знаку delta")
        params = json.loads(row.selected_params_json)
        if row.selected_parameter_set_id != make_hgb_parameter_set_id(params):
            raise ValueError("selected_parameter_set_id не соответствует JSON")
        if set(params) != set(bundle.parameter_grid):
            raise ValueError("selected_params_json имеет неверный набор параметров")
        if any(params[name] not in bundle.parameter_grid[name] for name in params):
            raise ValueError("selected_params_json выходит за locked grid")
    _require_finite_nonnegative(audit, ("fit_seconds",))
    for column in (
        "non_nested_average_precision_mean",
        "non_nested_average_precision_std_for_selected_params",
        "nested_average_precision_mean",
        "optimism_delta_non_nested_minus_nested",
    ):
        values = pd.to_numeric(audit[column], errors="raise").to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError(f"{column} должен быть конечным")
    means = pd.to_numeric(audit["non_nested_average_precision_mean"], errors="raise")
    stds = pd.to_numeric(
        audit["non_nested_average_precision_std_for_selected_params"],
        errors="raise",
    )
    if ((means < 0.0) | (means > 1.0)).any() or (stds < 0.0).any():
        raise ValueError("AP mean/std выходят за допустимые границы")


def run_non_nested_optimism_probe(
    contract: NonNestedOptimismContract,
    candidate_bundle: dict[str, Any],
    X: pd.DataFrame,
    y: np.ndarray,
    feature_names: list[str],
    parameter_grid: dict[str, list[Any]],
    fixed_parameters: dict[str, Any],
    reference_table: pd.DataFrame,
) -> NonNestedOptimismBundle:
    """Run locked single-level ST05_07 GridSearchCV and assemble its audit."""
    y_array = _validate_non_nested_execution_inputs(
        contract, candidate_bundle, X, y, feature_names,
        parameter_grid, fixed_parameters,
    )
    rows: list[dict[str, Any]] = []
    for state in contract.random_states:
        cv = RepeatedStratifiedKFold(
            n_splits=contract.n_splits,
            n_repeats=contract.n_repeats,
            random_state=state,
        )
        search = GridSearchCV(
            estimator=HistGradientBoostingClassifier(**fixed_parameters),
            param_grid=parameter_grid,
            scoring=contract.scoring,
            refit=True,
            cv=cv,
            n_jobs=1,
            return_train_score=False,
            error_score="raise",
        )
        started = time.perf_counter()
        search.fit(X, y_array)
        fit_seconds = time.perf_counter() - started
        selected_params = dict(search.best_params_)
        selected_json = json.dumps(
            selected_params, ensure_ascii=False, sort_keys=True
        )
        mean_score = float(search.best_score_)
        std_score = float(
            search.cv_results_["std_test_score"][int(search.best_index_)]
        )
        selected_references = select_non_nested_reference_rows(
            reference_table, state, contract
        )
        for reference in selected_references.itertuples(index=False):
            nested_mean = float(reference.nested_average_precision_mean)
            delta = mean_score - nested_mean
            status, status_ru = classify_non_nested_optimism_delta(delta)
            rows.append({
                "stress_test_id": contract.stress_test_id,
                "claim_id": contract.claim_id,
                "run_group": contract.run_group,
                "protocol_variant_id": contract.protocol_variant_id,
                "candidate_id": candidate_bundle["candidate_id"],
                "openml_dataset_id": candidate_bundle["did"],
                "dataset_name": candidate_bundle["dataset_name"],
                "target_name": candidate_bundle["target_name"],
                "target_class_0": candidate_bundle["target_metadata"]["target_class_0"],
                "target_class_1": candidate_bundle["target_metadata"]["target_class_1"],
                "positive_class_assumption": candidate_bundle["target_metadata"]["positive_class_assumption"],
                "model_id": contract.model_id,
                "model_role": "single_level_tuned_candidate",
                "feature_policy_id": contract.feature_policy_id,
                "feature_count": len(feature_names),
                "single_level_cv_method": "RepeatedStratifiedKFold",
                "single_level_cv_n_splits": contract.n_splits,
                "single_level_cv_n_repeats": contract.n_repeats,
                "single_level_cv_random_state": state,
                "single_level_cv_blocks": contract.n_splits * contract.n_repeats,
                "parameter_space_policy": contract.parameter_space_policy,
                "selected_parameter_set_id": make_hgb_parameter_set_id(selected_params),
                "selected_params_json": selected_json,
                "grid_candidate_count": len(search.cv_results_["params"]),
                "non_nested_average_precision_mean": mean_score,
                "non_nested_average_precision_std_for_selected_params": std_score,
                "fit_seconds": float(fit_seconds),
                "comparison_reference_id": str(reference.comparison_reference_id),
                "comparison_reference_source_file": reference.comparison_reference_source_file,
                "comparison_reference_stress_test_id": reference.comparison_reference_stress_test_id,
                "comparison_reference_protocol_variant_id": reference.comparison_reference_protocol_variant_id,
                "comparison_reference_random_state_scope": str(reference.comparison_reference_random_state_scope),
                "nested_outer_blocks": int(reference.nested_outer_blocks),
                "nested_average_precision_mean": nested_mean,
                "optimism_delta_non_nested_minus_nested": delta,
                "audit_status": status,
                "audit_status_ru": status_ru,
                "row_status": STAGE05_NON_NESTED_ROW_STATUS,
                "interpretation_allowed_ru": STAGE05_NON_NESTED_INTERPRETATION_RU,
            })
    bundle = NonNestedOptimismBundle(
        audit=pd.DataFrame(rows, columns=STAGE05_NON_NESTED_COLUMNS),
        reference_table=reference_table.copy(deep=True),
        parameter_grid={key: list(values) for key, values in parameter_grid.items()},
    )
    validate_non_nested_optimism_bundle(bundle, contract)
    return bundle
