from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd


def _format_columns(columns: Iterable[str]) -> str:
    return ", ".join(str(column) for column in columns)


def require_columns(df: pd.DataFrame, columns: Iterable[str], artifact_name: str) -> None:
    expected_columns = list(columns)
    missing_columns = [column for column in expected_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"В артефакте {artifact_name} отсутствуют обязательные столбцы: "
            f"{_format_columns(missing_columns)}"
        )


def require_non_empty(df: pd.DataFrame, artifact_name: str) -> None:
    if df.empty:
        raise ValueError(f"Артефакт {artifact_name} не должен быть пустым")


def require_allowed_values(
    df: pd.DataFrame,
    column: str,
    allowed_values: Iterable[Any],
    artifact_name: str,
) -> None:
    require_columns(df, [column], artifact_name)
    allowed_value_set = set(allowed_values)
    actual_values = set(df[column].dropna().unique())
    unexpected_values = sorted(actual_values - allowed_value_set)
    if unexpected_values:
        raise ValueError(
            f"В артефакте {artifact_name} столбец {column} содержит недопустимые значения: "
            f"{unexpected_values}. Допустимые значения: {sorted(allowed_value_set)}"
        )


def require_unique_key(df: pd.DataFrame, columns: Iterable[str], artifact_name: str) -> None:
    key_columns = list(columns)
    require_columns(df, key_columns, artifact_name)
    duplicated_rows = df[df.duplicated(subset=key_columns, keep=False)]
    if not duplicated_rows.empty:
        raise ValueError(
            f"В артефакте {artifact_name} нарушена уникальность ключа "
            f"{_format_columns(key_columns)}; повторяющихся строк: {len(duplicated_rows)}"
        )