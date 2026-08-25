from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd

from mlcra.validation import require_columns, require_non_empty, require_unique_key


HGB_MODEL_ID = "hist_gradient_boosting"
LOCKED_DECISION_STATUS = "locked_before_run"
MODEL_SPACE_ARTIFACT_NAME = "hist_gradient_boosting model space"

REQUIRED_MODEL_SPACE_COLUMNS = [
    "protocol_id",
    "candidate_id",
    "model_id",
    "search_method",
    "parameter_name",
    "parameter_values",
    "fixed_value",
    "decision_status",
]

EXPECTED_GRID_PARAMETERS = {
    "learning_rate",
    "max_iter",
    "max_leaf_nodes",
    "l2_regularization",
}

EXPECTED_FIXED_PARAMETERS = {
    "random_state",
    "early_stopping",
}


def _parse_parameter_value(raw_value: Any) -> Any:
    if pd.isna(raw_value):
        raise ValueError("Пустое значение параметра недопустимо")

    value = str(raw_value).strip()

    if value == "":
        raise ValueError("Пустое значение параметра недопустимо")

    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    if value.lower() == "none":
        return None

    try:
        integer_value = int(value)
        if str(integer_value) == value:
            return integer_value
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value


def _parse_parameter_values(raw_values: Any) -> list[Any]:
    if pd.isna(raw_values):
        raise ValueError("Пустая сетка значений параметра недопустима")

    return [
        _parse_parameter_value(item)
        for item in str(raw_values).split(";")
        if item.strip()
    ]


def _has_duplicate_values(values: list[Any]) -> bool:
    for index, value in enumerate(values):
        for previous_value in values[:index]:
            both_missing = pd.isna(value) and pd.isna(previous_value)
            if both_missing or value == previous_value:
                return True
    return False


def _require_expected_parameters(
    actual_parameters: set[str],
    expected_parameters: set[str],
    parameter_group: str,
) -> None:
    if actual_parameters != expected_parameters:
        missing_parameters = sorted(expected_parameters - actual_parameters)
        unexpected_parameters = sorted(actual_parameters - expected_parameters)
        raise ValueError(
            f"{parameter_group} параметры hist_gradient_boosting "
            "не совпадают с зарегистрированными. "
            f"Отсутствуют: {missing_parameters}; "
            f"незарегистрированные или ошибочно классифицированные: "
            f"{unexpected_parameters}"
        )


def build_hist_gradient_boosting_search_space(
    model_space_df: pd.DataFrame,
    protocol_id: str,
    candidate_id: str,
) -> tuple[dict[str, list[Any]], dict[str, Any]]:
    require_columns(
        model_space_df,
        REQUIRED_MODEL_SPACE_COLUMNS,
        MODEL_SPACE_ARTIFACT_NAME,
    )

    hgb_rows = model_space_df[
        model_space_df["protocol_id"].eq(protocol_id)
        & model_space_df["candidate_id"].eq(candidate_id)
        & model_space_df["model_id"].eq(HGB_MODEL_ID)
    ].copy()

    require_non_empty(hgb_rows, MODEL_SPACE_ARTIFACT_NAME)

    if not hgb_rows["decision_status"].eq(LOCKED_DECISION_STATUS).all():
        raise ValueError(
            "Все выбранные строки пространства параметров "
            "hist_gradient_boosting должны иметь "
            f"decision_status={LOCKED_DECISION_STATUS}"
        )

    empty_parameter_names = (
        hgb_rows["parameter_name"].isna()
        | hgb_rows["parameter_name"].astype(str).str.strip().eq("")
    )
    if empty_parameter_names.any():
        raise ValueError("Имя параметра hist_gradient_boosting не должно быть пустым")

    require_unique_key(
        hgb_rows,
        ["parameter_name"],
        MODEL_SPACE_ARTIFACT_NAME,
    )

    parameter_grid: dict[str, list[Any]] = {}
    fixed_parameters: dict[str, Any] = {}

    for _, row in hgb_rows.iterrows():
        parameter_name = str(row["parameter_name"])
        search_method = row["search_method"]

        if search_method == "grid":
            values = _parse_parameter_values(row["parameter_values"])
            if not values:
                raise ValueError(
                    f"Пустая сетка значений для параметра: {parameter_name}"
                )
            if _has_duplicate_values(values):
                raise ValueError(
                    f"Сетка параметра {parameter_name} содержит "
                    "повторяющиеся значения"
                )
            parameter_grid[parameter_name] = values
        elif search_method == "fixed":
            fixed_parameters[parameter_name] = _parse_parameter_value(
                row["fixed_value"]
            )
        else:
            raise ValueError(f"Неизвестный search_method: {search_method}")

    _require_expected_parameters(
        set(parameter_grid),
        EXPECTED_GRID_PARAMETERS,
        "Grid",
    )
    _require_expected_parameters(
        set(fixed_parameters),
        EXPECTED_FIXED_PARAMETERS,
        "Fixed",
    )

    return parameter_grid, fixed_parameters


def make_hgb_parameter_set_id(params: dict[str, Any]) -> str:
    canonical = json.dumps(
        params,
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:12]
    return f"hgb_{digest}"
