from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from mlcra.validation import require_columns


def resolve_project_path(root: Path, relative_path: str | Path) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return root / path


def read_csv_checked(path: str | Path, required_columns: Iterable[str] | None = None) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV-файл не найден: {csv_path}")
    try:
        df = pd.read_csv(
            csv_path,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
            sep=None,
            engine="python",
        )
    except pd.errors.ParserError as error:
        raise pd.errors.ParserError(
            f"Не удалось прочитать CSV-файл {csv_path}. "
            "Проверь разделитель, кавычки и количество полей в строках. "
            f"Исходная ошибка pandas: {error}"
        ) from error

    if required_columns is not None:
        require_columns(df, required_columns, str(csv_path))
    return df


def write_csv_checked(df: pd.DataFrame, path: str | Path, index: bool = False) -> None:
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=index, encoding="utf-8-sig")