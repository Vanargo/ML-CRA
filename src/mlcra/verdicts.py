from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from mlcra.metrics import METRIC_DIRECTIONS, metric_delta
from mlcra.validation import require_columns, require_non_empty, require_unique_key


STAGE05_CURRENT_READOUT_ID = "ST05_01_current_nested_readout"
STAGE05_CURRENT_READOUT_CLAIM_ID = "miniboone_hgb_vs_logreg_average_precision_v01"
STAGE05_CURRENT_READOUT_CANDIDATE_ID = "openml_miniboone_41150"
STAGE05_CURRENT_READOUT_PROTOCOL_ID = "miniboone_nested_cv_v01"
STAGE05_CURRENT_READOUT_CANDIDATE_MODEL_ID = "hist_gradient_boosting"
STAGE05_CURRENT_READOUT_SOURCE_FILE = (
    "data_registry/openml_miniboone_nested_outer_scores.csv"
)
STAGE05_CURRENT_READOUT_METRICS = [
    "average_precision",
    "roc_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
]
STAGE05_CURRENT_READOUT_COMPARISONS = [
    ("logistic_regression", "primary_baseline"),
    ("dummy_prior", "lower_bound_model"),
]
STAGE05_CURRENT_READOUT_KEY_COLUMNS = [
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
]
STAGE05_CURRENT_READOUT_REQUIRED_COLUMNS = [
    "protocol_id",
    "candidate_id",
    "dataset_name",
    *STAGE05_CURRENT_READOUT_KEY_COLUMNS,
    "model_id",
    *STAGE05_CURRENT_READOUT_METRICS,
    "row_status",
]
STAGE05_CURRENT_READOUT_COLUMNS = [
    "readout_id",
    "claim_id",
    "source_protocol_id",
    "candidate_id",
    "dataset_name",
    "comparison_role",
    "candidate_model_id",
    "comparison_model_id",
    "metric_name",
    "metric_direction",
    "row_type",
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
    "candidate_metric_value",
    "comparison_metric_value",
    "raw_delta_candidate_minus_comparison",
    "advantage_for_candidate",
    "candidate_better",
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
    "source_file",
]


def _require_current_readout_values(
    df: pd.DataFrame,
    column: str,
    expected_values: set[str],
) -> None:
    actual_values = set(df[column].astype(str).str.strip().unique())
    if actual_values != expected_values:
        raise ValueError(
            f"ST07_07: столбец {column} исходных внешних оценок "
            "не совпадает с ожидаемым набором значений. "
            f"Ожидалось: {sorted(expected_values)}, "
            f"получено: {sorted(actual_values)}"
        )


def _prepare_current_readout_input(
    outer_scores_df: pd.DataFrame,
) -> pd.DataFrame:
    artifact_name = "ST05_01 nested outer scores"
    require_non_empty(outer_scores_df, artifact_name)
    require_columns(
        outer_scores_df,
        STAGE05_CURRENT_READOUT_REQUIRED_COLUMNS,
        artifact_name,
    )

    prepared = outer_scores_df.copy()
    for column, expected_values in [
        ("protocol_id", {STAGE05_CURRENT_READOUT_PROTOCOL_ID}),
        ("candidate_id", {STAGE05_CURRENT_READOUT_CANDIDATE_ID}),
        (
            "model_id",
            {
                STAGE05_CURRENT_READOUT_CANDIDATE_MODEL_ID,
                *(
                    comparison_model_id
                    for comparison_model_id, _ in STAGE05_CURRENT_READOUT_COMPARISONS
                ),
            },
        ),
        ("row_status", {"nested_research_draft"}),
    ]:
        _require_current_readout_values(
            prepared,
            column,
            expected_values,
        )

    blank_key_counts = {
        column: int(prepared[column].astype(str).str.strip().eq("").sum())
        for column in STAGE05_CURRENT_READOUT_KEY_COLUMNS
    }
    blank_key_counts = {
        column: count
        for column, count in blank_key_counts.items()
        if count > 0
    }
    if blank_key_counts:
        raise ValueError(
            "ST07_07: в исходных внешних оценках обнаружены пустые "
            f"значения парного ключа: {blank_key_counts}"
        )

    require_unique_key(
        prepared,
        [*STAGE05_CURRENT_READOUT_KEY_COLUMNS, "model_id"],
        artifact_name,
    )

    block_counts = prepared.groupby(
        STAGE05_CURRENT_READOUT_KEY_COLUMNS,
        dropna=False,
    )["model_id"].nunique()
    if len(block_counts) != 10:
        raise ValueError(
            "ST07_07: ожидалось 10 внешних блоков, "
            f"получено {len(block_counts)}"
        )
    if not block_counts.eq(3).all():
        raise ValueError(
            "ST07_07: в каждом внешнем блоке должны присутствовать "
            "ровно три зарегистрированные модели"
        )

    for metric_name in STAGE05_CURRENT_READOUT_METRICS:
        raw_values = prepared[metric_name].astype(str).str.strip()
        try:
            numeric_values = raw_values.map(float)
        except ValueError as error:
            raise ValueError(
                f"ST07_07: столбец {metric_name} содержит значение, "
                "которое нельзя преобразовать в float"
            ) from error
        invalid_mask = raw_values.eq("") | ~np.isfinite(numeric_values)
        if invalid_mask.any():
            raise ValueError(
                f"ST07_07: столбец {metric_name} содержит пустые, "
                "нечисловые или бесконечные значения. "
                f"Число нарушений: {int(invalid_mask.sum())}; "
                f"примеры: {raw_values[invalid_mask].head(5).tolist()}"
            )
        prepared[metric_name] = numeric_values.astype(float)

    return prepared


def _build_current_readout_pair_rows(
    outer_scores_df: pd.DataFrame,
    comparison_model_id: str,
    comparison_role: str,
) -> list[dict[str, Any]]:
    candidate_rows = outer_scores_df[
        outer_scores_df["model_id"].eq(
            STAGE05_CURRENT_READOUT_CANDIDATE_MODEL_ID
        )
    ].copy()
    comparison_rows = outer_scores_df[
        outer_scores_df["model_id"].eq(comparison_model_id)
    ].copy()

    try:
        paired = candidate_rows.merge(
            comparison_rows,
            on=STAGE05_CURRENT_READOUT_KEY_COLUMNS,
            suffixes=("_candidate", "_comparison"),
            validate="one_to_one",
        )
    except pd.errors.MergeError as error:
        raise ValueError(
            "ST07_07: нарушена однозначность парного соединения "
            f"HGB/{comparison_model_id}"
        ) from error

    if len(paired) != 10:
        raise ValueError(
            "ST07_07: нарушена полнота парного соединения "
            f"HGB/{comparison_model_id}: ожидалось 10 пар, "
            f"получено {len(paired)}"
        )

    rows: list[dict[str, Any]] = []
    for _, row in paired.sort_values(
        STAGE05_CURRENT_READOUT_KEY_COLUMNS,
        kind="mergesort",
    ).iterrows():
        for metric_name in STAGE05_CURRENT_READOUT_METRICS:
            metric_direction = METRIC_DIRECTIONS[metric_name]
            candidate_value = float(row[f"{metric_name}_candidate"])
            comparison_value = float(row[f"{metric_name}_comparison"])
            raw_delta = candidate_value - comparison_value
            advantage_for_candidate = metric_delta(
                candidate_value,
                comparison_value,
                metric_name,
            )

            rows.append({
                "readout_id": STAGE05_CURRENT_READOUT_ID,
                "claim_id": STAGE05_CURRENT_READOUT_CLAIM_ID,
                "source_protocol_id": row["protocol_id_candidate"],
                "candidate_id": row["candidate_id_candidate"],
                "dataset_name": row["dataset_name_candidate"],
                "comparison_role": comparison_role,
                "candidate_model_id": STAGE05_CURRENT_READOUT_CANDIDATE_MODEL_ID,
                "comparison_model_id": comparison_model_id,
                "metric_name": metric_name,
                "metric_direction": metric_direction,
                "row_type": "paired_outer_block",
                "outer_split_number": int(row["outer_split_number"]),
                "outer_repeat_number": int(row["outer_repeat_number"]),
                "outer_fold_number": int(row["outer_fold_number"]),
                "candidate_metric_value": candidate_value,
                "comparison_metric_value": comparison_value,
                "raw_delta_candidate_minus_comparison": raw_delta,
                "advantage_for_candidate": advantage_for_candidate,
                "candidate_better": bool(advantage_for_candidate > 0),
                "n_blocks": "",
                "advantage_mean": "",
                "advantage_std_population": "",
                "advantage_min": "",
                "advantage_max": "",
                "candidate_positive_blocks": "",
                "candidate_negative_blocks": "",
                "candidate_zero_blocks": "",
                "row_status": "stage05_current_readout",
                "interpretation_allowed_ru": (
                    "Только первичный срез текущего вложенного результата; "
                    "не является итоговым вердиктом этапа 5."
                ),
                "source_file": STAGE05_CURRENT_READOUT_SOURCE_FILE,
            })

    return rows


def build_current_effect_readout(
    outer_scores_df: pd.DataFrame,
) -> pd.DataFrame:
    prepared = _prepare_current_readout_input(outer_scores_df)

    paired_rows: list[dict[str, Any]] = []
    for comparison_model_id, comparison_role in (
        STAGE05_CURRENT_READOUT_COMPARISONS
    ):
        paired_rows.extend(
            _build_current_readout_pair_rows(
                prepared,
                comparison_model_id,
                comparison_role,
            )
        )

    paired_df = pd.DataFrame(
        paired_rows,
        columns=STAGE05_CURRENT_READOUT_COLUMNS,
    )
    if len(paired_df) != 120:
        raise ValueError(
            "ST07_07: ожидалось 120 строк paired_outer_block, "
            f"получено {len(paired_df)}"
        )

    summary_rows: list[dict[str, Any]] = []
    for keys, group in paired_df.groupby(
        [
            "claim_id",
            "source_protocol_id",
            "candidate_id",
            "comparison_role",
            "candidate_model_id",
            "comparison_model_id",
            "metric_name",
            "metric_direction",
        ],
        dropna=False,
    ):
        (
            claim_id,
            source_protocol_id,
            candidate_id,
            comparison_role,
            candidate_model_id,
            comparison_model_id,
            metric_name,
            metric_direction,
        ) = keys
        advantages = group["advantage_for_candidate"].astype(float)

        summary_rows.append({
            "readout_id": STAGE05_CURRENT_READOUT_ID,
            "claim_id": claim_id,
            "source_protocol_id": source_protocol_id,
            "candidate_id": candidate_id,
            "dataset_name": group["dataset_name"].iloc[0],
            "comparison_role": comparison_role,
            "candidate_model_id": candidate_model_id,
            "comparison_model_id": comparison_model_id,
            "metric_name": metric_name,
            "metric_direction": metric_direction,
            "row_type": "metric_summary",
            "outer_split_number": "",
            "outer_repeat_number": "",
            "outer_fold_number": "",
            "candidate_metric_value": "",
            "comparison_metric_value": "",
            "raw_delta_candidate_minus_comparison": "",
            "advantage_for_candidate": "",
            "candidate_better": "",
            "n_blocks": int(len(group)),
            "advantage_mean": float(advantages.mean()),
            "advantage_std_population": float(advantages.std(ddof=0)),
            "advantage_min": float(advantages.min()),
            "advantage_max": float(advantages.max()),
            "candidate_positive_blocks": int(advantages.gt(0).sum()),
            "candidate_negative_blocks": int(advantages.lt(0).sum()),
            "candidate_zero_blocks": int(advantages.eq(0).sum()),
            "row_status": "stage05_current_readout",
            "interpretation_allowed_ru": (
                "Сводка текущего вложенного результата; использовать как вход "
                "этапа 5, а не как финальный вердикт."
            ),
            "source_file": STAGE05_CURRENT_READOUT_SOURCE_FILE,
        })

    result = pd.concat(
        [
            paired_df,
            pd.DataFrame(
                summary_rows,
                columns=STAGE05_CURRENT_READOUT_COLUMNS,
            ),
        ],
        ignore_index=True,
    )

    row_type_counts = result["row_type"].value_counts().to_dict()
    if row_type_counts != {
        "paired_outer_block": 120,
        "metric_summary": 12,
    }:
        raise ValueError(
            "ST07_07: нарушено ожидаемое число строк по row_type: "
            f"{row_type_counts}"
        )
    if result.shape != (132, 30):
        raise ValueError(
            "ST07_07: ожидалась форма результата (132, 30), "
            f"получено {result.shape}"
        )

    require_unique_key(
        result[result["row_type"].eq("paired_outer_block")],
        [
            "comparison_model_id",
            "metric_name",
            *STAGE05_CURRENT_READOUT_KEY_COLUMNS,
        ],
        "ST05_01 paired_outer_block result",
    )
    require_unique_key(
        result[result["row_type"].eq("metric_summary")],
        ["comparison_model_id", "metric_name"],
        "ST05_01 metric_summary result",
    )

    return result


STAGE05_METRIC_CONFLICT_ID = "ST05_04_metric_conflict_audit"
STAGE05_METRIC_CONFLICT_CLAIM_ID = "miniboone_hgb_vs_logreg_average_precision_v01"
STAGE05_METRIC_CONFLICT_CANDIDATE_ID = "openml_miniboone_41150"
STAGE05_METRIC_CONFLICT_CANDIDATE_MODEL_ID = "hist_gradient_boosting"
STAGE05_METRIC_CONFLICT_COMPARISON_MODEL_ID = "logistic_regression"
STAGE05_METRIC_CONFLICT_SUMMARY_SCOPE = "all_outer_random_states"

STAGE05_METRIC_CONFLICT_METRICS = [
    "average_precision",
    "roc_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
]

STAGE05_METRIC_CONFLICT_PROTOCOLS = {
    "nested_5x2_seed_grid_v01",
    "nested_10x1_seed_grid_v01",
}

STAGE05_METRIC_SUMMARY_REQUIRED_COLUMNS = [
    "stress_test_id",
    "claim_id",
    "protocol_variant_id",
    "summary_scope",
    "candidate_model_id",
    "comparison_model_id",
    "metric_name",
    "metric_direction",
    "n_blocks",
    "advantage_mean",
    "advantage_min",
    "advantage_max",
    "candidate_positive_blocks",
    "candidate_negative_blocks",
    "candidate_zero_blocks",
]


def _metric_role(metric_name: str) -> str:
    return "primary" if metric_name == "average_precision" else "secondary"


def _classify_metric_conflict_row(
    n_blocks: int,
    positive_blocks: int,
    negative_blocks: int,
    zero_blocks: int,
    advantage_mean: float,
    advantage_min: float,
) -> tuple[str, str, str]:
    supports_candidate = (
        n_blocks > 0
        and positive_blocks == n_blocks
        and negative_blocks == 0
        and zero_blocks == 0
        and advantage_mean > 0
        and advantage_min > 0
    )

    if supports_candidate:
        return "no_conflict", "конфликт метрик не обнаружен", "none"
    if negative_blocks > 0 or advantage_mean < 0 or advantage_min < 0:
        return "conflict_detected", "обнаружен конфликт метрик", "review_claim_reliability"
    return "requires_review", "требуется ручная проверка", "manual_review"


def _classify_metric_conflict_group(group: pd.DataFrame) -> tuple[str, str, str]:
    conflict_count = int(group["metric_conflict_status"].eq("conflict_detected").sum())
    review_count = int(group["metric_conflict_status"].eq("requires_review").sum())

    if conflict_count == 0 and review_count == 0:
        return "no_conflict", "конфликт метрики между протоколами не обнаружен", "none"
    if conflict_count > 0:
        return (
            "conflict_detected",
            "обнаружен конфликт метрики хотя бы в одном протоколе",
            "review_claim_reliability",
        )
    return "requires_review", "требуется ручная проверка метрики", "manual_review"


def _classify_overall_metric_conflict(rows_df: pd.DataFrame) -> tuple[str, str, str]:
    conflict_count = int(rows_df["metric_conflict_status"].eq("conflict_detected").sum())
    review_count = int(rows_df["metric_conflict_status"].eq("requires_review").sum())

    if conflict_count == 0 and review_count == 0:
        return (
            "no_metric_conflict_detected",
            "конфликт интерпретации между метриками не обнаружен",
            "none",
        )
    if conflict_count > 0:
        return (
            "metric_conflict_detected",
            "обнаружен конфликт интерпретации между метриками",
            "review_claim_reliability",
        )
    return "requires_review", "требуется ручная проверка согласованности метрик", "manual_review"


def build_metric_conflict_audit(
    seed_summary_df: pd.DataFrame,
    split_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    for summary_name, summary_df in [
        ("ST05_02", seed_summary_df),
        ("ST05_03a", split_summary_df),
    ]:
        require_non_empty(summary_df, summary_name)
        require_columns(summary_df, STAGE05_METRIC_SUMMARY_REQUIRED_COLUMNS, summary_name)

    input_summary = pd.concat(
        [
            seed_summary_df.assign(source_stage="ST05_02_seed_stability_grid"),
            split_summary_df.assign(source_stage="ST05_03a_split_protocol_10x1"),
        ],
        ignore_index=True,
    )

    input_summary = input_summary[
        input_summary["claim_id"].eq(STAGE05_METRIC_CONFLICT_CLAIM_ID)
        & input_summary["comparison_model_id"].eq(STAGE05_METRIC_CONFLICT_COMPARISON_MODEL_ID)
        & input_summary["summary_scope"].eq(STAGE05_METRIC_CONFLICT_SUMMARY_SCOPE)
    ].copy()

    expected_protocols = STAGE05_METRIC_CONFLICT_PROTOCOLS
    actual_protocols = set(input_summary["protocol_variant_id"].unique())
    if actual_protocols != expected_protocols:
        raise ValueError(
            "Набор protocol_variant_id для ST05_04 не совпадает с ожидаемым. "
            f"Ожидалось: {sorted(expected_protocols)}, "
            f"получено: {sorted(actual_protocols)}"
        )

    expected_metric_set = set(STAGE05_METRIC_CONFLICT_METRICS)
    actual_metric_set = set(input_summary["metric_name"].unique())
    if actual_metric_set != expected_metric_set:
        raise ValueError(
            "Набор метрик для ST05_04 не совпадает с ожидаемым. "
            f"Ожидалось: {sorted(expected_metric_set)}, "
            f"получено: {sorted(actual_metric_set)}"
        )

    unknown_metric_directions = [
        metric_name
        for metric_name in sorted(actual_metric_set)
        if metric_name not in METRIC_DIRECTIONS
    ]
    if unknown_metric_directions:
        raise ValueError(f"Для ST05_04 обнаружены неизвестные метрики: {unknown_metric_directions}")

    expected_rows = len(expected_protocols) * len(STAGE05_METRIC_CONFLICT_METRICS)
    if len(input_summary) != expected_rows:
        raise ValueError(
            f"Неожиданное число строк входной сводки ST05_04: "
            f"ожидалось {expected_rows}, получено {len(input_summary)}"
        )

    audit_rows: list[dict[str, Any]] = []

    for _, row in input_summary.sort_values(
        ["protocol_variant_id", "metric_name"],
        kind="mergesort",
    ).iterrows():
        n_blocks = int(row["n_blocks"])
        positive_blocks = int(row["candidate_positive_blocks"])
        negative_blocks = int(row["candidate_negative_blocks"])
        zero_blocks = int(row["candidate_zero_blocks"])
        advantage_mean = float(row["advantage_mean"])
        advantage_min = float(row["advantage_min"])
        advantage_max = float(row["advantage_max"])

        metric_conflict_status, metric_conflict_status_ru, action_required = _classify_metric_conflict_row(
            n_blocks=n_blocks,
            positive_blocks=positive_blocks,
            negative_blocks=negative_blocks,
            zero_blocks=zero_blocks,
            advantage_mean=advantage_mean,
            advantage_min=advantage_min,
        )

        audit_rows.append({
            "stress_test_id": STAGE05_METRIC_CONFLICT_ID,
            "claim_id": STAGE05_METRIC_CONFLICT_CLAIM_ID,
            "candidate_id": STAGE05_METRIC_CONFLICT_CANDIDATE_ID,
            "audit_level": "protocol_metric",
            "source_stage": row["source_stage"],
            "protocol_variant_id": row["protocol_variant_id"],
            "summary_scope": row["summary_scope"],
            "candidate_model_id": row["candidate_model_id"],
            "comparison_model_id": row["comparison_model_id"],
            "metric_name": row["metric_name"],
            "metric_role": _metric_role(row["metric_name"]),
            "metric_direction": row["metric_direction"],
            "n_blocks": n_blocks,
            "advantage_mean": advantage_mean,
            "advantage_min": advantage_min,
            "advantage_max": advantage_max,
            "candidate_positive_blocks": positive_blocks,
            "candidate_negative_blocks": negative_blocks,
            "candidate_zero_blocks": zero_blocks,
            "metric_conflict_status": metric_conflict_status,
            "metric_conflict_status_ru": metric_conflict_status_ru,
            "action_required": action_required,
            "row_status": "stage05_metric_conflict_protocol_metric",
            "interpretation_allowed_ru": (
                "Строка проверяет согласованность одной метрики внутри одного протокола; "
                "не является итоговым вердиктом этапа 5."
            ),
        })

    protocol_metric_df = pd.DataFrame(audit_rows)

    for metric_name, group in protocol_metric_df.groupby("metric_name", dropna=False):
        metric_conflict_status, metric_conflict_status_ru, action_required = _classify_metric_conflict_group(group)

        audit_rows.append({
            "stress_test_id": STAGE05_METRIC_CONFLICT_ID,
            "claim_id": STAGE05_METRIC_CONFLICT_CLAIM_ID,
            "candidate_id": STAGE05_METRIC_CONFLICT_CANDIDATE_ID,
            "audit_level": "all_protocols_metric",
            "source_stage": "ST05_02_and_ST05_03a",
            "protocol_variant_id": "all_completed_preregistered_variants",
            "summary_scope": STAGE05_METRIC_CONFLICT_SUMMARY_SCOPE,
            "candidate_model_id": STAGE05_METRIC_CONFLICT_CANDIDATE_MODEL_ID,
            "comparison_model_id": STAGE05_METRIC_CONFLICT_COMPARISON_MODEL_ID,
            "metric_name": metric_name,
            "metric_role": _metric_role(metric_name),
            "metric_direction": group["metric_direction"].iloc[0],
            "n_blocks": int(group["n_blocks"].astype(int).sum()),
            "advantage_mean": float(group["advantage_mean"].astype(float).mean()),
            "advantage_min": float(group["advantage_min"].astype(float).min()),
            "advantage_max": float(group["advantage_max"].astype(float).max()),
            "candidate_positive_blocks": int(group["candidate_positive_blocks"].astype(int).sum()),
            "candidate_negative_blocks": int(group["candidate_negative_blocks"].astype(int).sum()),
            "candidate_zero_blocks": int(group["candidate_zero_blocks"].astype(int).sum()),
            "metric_conflict_status": metric_conflict_status,
            "metric_conflict_status_ru": metric_conflict_status_ru,
            "action_required": action_required,
            "row_status": "stage05_metric_conflict_all_protocols_metric",
            "interpretation_allowed_ru": (
                "Строка агрегирует проверку одной метрики по завершенным протоколам ST05_02 и ST05_03a; "
                "не является итоговым вердиктом этапа 5."
            ),
        })

    pre_overall_df = pd.DataFrame(audit_rows)

    secondary_metric_rows = pre_overall_df[
        pre_overall_df["audit_level"].eq("all_protocols_metric")
        & pre_overall_df["metric_role"].eq("secondary")
    ].copy()

    if secondary_metric_rows.empty:
        raise ValueError("Для ST05_04 не найдены агрегированные строки вторичных метрик")

    primary_metric_rows = pre_overall_df[
        pre_overall_df["audit_level"].eq("all_protocols_metric")
        & pre_overall_df["metric_role"].eq("primary")
    ].copy()

    overall_status, overall_status_ru, action_required = _classify_overall_metric_conflict(pre_overall_df)

    audit_rows.append({
        "stress_test_id": STAGE05_METRIC_CONFLICT_ID,
        "claim_id": STAGE05_METRIC_CONFLICT_CLAIM_ID,
        "candidate_id": STAGE05_METRIC_CONFLICT_CANDIDATE_ID,
        "audit_level": "overall_metric_conflict_audit",
        "source_stage": "ST05_02_and_ST05_03a",
        "protocol_variant_id": "all_completed_preregistered_variants",
        "summary_scope": STAGE05_METRIC_CONFLICT_SUMMARY_SCOPE,
        "candidate_model_id": STAGE05_METRIC_CONFLICT_CANDIDATE_MODEL_ID,
        "comparison_model_id": STAGE05_METRIC_CONFLICT_COMPARISON_MODEL_ID,
        "metric_name": "all_primary_and_secondary_metrics",
        "metric_role": "overall",
        "metric_direction": "mixed",
        "n_blocks": int(primary_metric_rows["n_blocks"].astype(int).sum()) if len(primary_metric_rows) else 0,
        "advantage_mean": "",
        "advantage_min": "",
        "advantage_max": "",
        "candidate_positive_blocks": int(primary_metric_rows["candidate_positive_blocks"].astype(int).sum()) if len(primary_metric_rows) else 0,
        "candidate_negative_blocks": int(primary_metric_rows["candidate_negative_blocks"].astype(int).sum()) if len(primary_metric_rows) else 0,
        "candidate_zero_blocks": int(primary_metric_rows["candidate_zero_blocks"].astype(int).sum()) if len(primary_metric_rows) else 0,
        "metric_conflict_status": overall_status,
        "metric_conflict_status_ru": overall_status_ru,
        "action_required": action_required,
        "row_status": "stage05_metric_conflict_overall",
        "interpretation_allowed_ru": (
            "Итоговая строка ST05_04 проверяет наличие конфликта между основной и вторичными метриками "
            "по уже завершенным протоколам; не является финальным вердиктом этапа 5."
        ),
    })

    audit_df = pd.DataFrame(audit_rows).sort_values(
        [
            "audit_level",
            "protocol_variant_id",
            "metric_name",
        ],
        kind="mergesort",
    )

    expected_audit_rows = 19
    if len(audit_df) != expected_audit_rows:
        raise ValueError(
            f"Неожиданное число строк ST05_04: "
            f"ожидалось {expected_audit_rows}, получено {len(audit_df)}"
        )

    return audit_df

STAGE05_PARAMETER_STABILITY_ID = "ST05_05_parameter_selection_stability"
STAGE05_PARAMETER_STABILITY_CLAIM_ID = "miniboone_hgb_vs_logreg_average_precision_v01"
STAGE05_PARAMETER_STABILITY_CANDIDATE_ID = "openml_miniboone_41150"
STAGE05_PARAMETER_STABILITY_MODEL_ID = "hist_gradient_boosting"
STAGE05_PARAMETER_STABILITY_MODEL_ROLE = "tuned_candidate"
STAGE05_PARAMETER_STABILITY_EXPECTED_ROWS = 80
STAGE05_PARAMETER_STABILITY_EXPECTED_AUDIT_ROWS = 22

STAGE05_PARAMETER_STABILITY_PROTOCOLS = {
    "nested_5x2_seed_grid_v01",
    "nested_10x1_seed_grid_v01",
}

STAGE05_PARAMETER_STABILITY_PARAMETER_NAMES = [
    "l2_regularization",
    "learning_rate",
    "max_iter",
    "max_leaf_nodes",
]

STAGE05_PARAMETER_STABILITY_REQUIRED_COLUMNS = [
    "stress_test_id",
    "claim_id",
    "protocol_variant_id",
    "candidate_id",
    "model_id",
    "model_role",
    "outer_random_state",
    "outer_split_number",
    "selected_parameter_set_id",
    "selected_params_json",
    "inner_best_average_precision",
    "average_precision",
]

STAGE05_PARAMETER_STABILITY_UNIQUE_KEY = [
    "stress_test_id",
    "protocol_variant_id",
    "outer_random_state",
    "outer_split_number",
    "model_id",
]


def _parse_selected_params_json(selected_params_json: str) -> dict[str, Any]:
    if pd.isna(selected_params_json) or str(selected_params_json).strip() == "":
        raise ValueError("Пустой selected_params_json для tuned_candidate")

    try:
        parsed = json.loads(str(selected_params_json))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"selected_params_json содержит некорректный JSON: {selected_params_json}"
        ) from error

    if not isinstance(parsed, dict):
        raise ValueError(
            "selected_params_json должен быть JSON-объектом, "
            f"получено: {type(parsed)}"
        )

    return parsed


def _normalize_parameter_value(value: Any) -> str:
    if isinstance(value, float):
        return repr(float(value))
    return str(value)


def _classify_parameter_stability(
    top_share: float,
    unique_count: int,
    stable_parameter_count: int | None = None,
    total_parameter_count: int | None = None,
) -> tuple[str, str, str]:
    if unique_count == 1:
        return "stable", "выбор стабилен", "none"

    if stable_parameter_count is not None and total_parameter_count is not None:
        if stable_parameter_count >= max(total_parameter_count - 1, 1):
            return (
                "partially_stable",
                "выбор частично стабилен: меняется не более одного параметра",
                "document_instability",
            )

    if top_share >= 0.75:
        return (
            "dominant_configuration",
            "есть доминирующая конфигурация параметров",
            "document_instability",
        )

    if top_share >= 0.50:
        return (
            "partially_stable",
            "выбор частично стабилен",
            "document_instability",
        )

    return (
        "unstable",
        "выбор параметров нестабилен",
        "review_claim_reliability",
    )


def _classify_parameter_value(
    unique_value_count: int,
    top_value_share: float,
) -> tuple[str, str, str]:
    if unique_value_count == 1:
        return "stable", "значение параметра стабильно", "none"

    if top_value_share >= 0.75:
        return (
            "dominant_value",
            "есть доминирующее значение параметра",
            "document_instability",
        )

    return (
        "variable",
        "значение параметра изменяется между блоками",
        "document_instability",
    )


def _parameter_stability_row(**values: Any) -> dict[str, Any]:
    row = {
        "stress_test_id": STAGE05_PARAMETER_STABILITY_ID,
        "claim_id": STAGE05_PARAMETER_STABILITY_CLAIM_ID,
        "candidate_id": STAGE05_PARAMETER_STABILITY_CANDIDATE_ID,
        "audit_level": "",
        "source_stage": "",
        "protocol_variant_id": "",
        "model_id": STAGE05_PARAMETER_STABILITY_MODEL_ID,
        "parameter_name": "",
        "parameter_value": "",
        "selected_parameter_set_id": "",
        "n_blocks": 0,
        "selection_count": 0,
        "selection_share": 0.0,
        "unique_parameter_set_count": 0,
        "top_selection_count": 0,
        "top_selection_share": 0.0,
        "inner_best_average_precision_mean": 0.0,
        "outer_average_precision_mean": 0.0,
        "stability_status": "",
        "stability_status_ru": "",
        "action_required": "",
        "row_status": "",
        "interpretation_allowed_ru": "",
    }
    row.update(values)
    return row


def _build_parameter_scope_rows(
    group: pd.DataFrame,
    audit_scope: str,
    source_stage: str,
    protocol_variant_id: str,
    include_overall_row: bool,
) -> list[dict[str, Any]]:
    n_blocks = int(len(group))
    inner_best_mean = float(
        group["inner_best_average_precision"].astype(float).mean()
    )
    outer_average_precision_mean = float(
        group["average_precision"].astype(float).mean()
    )

    common_values = {
        "source_stage": source_stage,
        "protocol_variant_id": protocol_variant_id,
        "n_blocks": n_blocks,
        "inner_best_average_precision_mean": inner_best_mean,
        "outer_average_precision_mean": outer_average_precision_mean,
    }

    parameter_set_counts = (
        group
        .groupby(
            [
                "selected_parameter_set_id",
                "selected_params_canonical_json",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="selection_count")
        .sort_values(
            [
                "selection_count",
                "selected_parameter_set_id",
            ],
            ascending=[False, True],
            kind="mergesort",
        )
    )

    unique_set_count = int(len(parameter_set_counts))
    top_set_count = int(parameter_set_counts["selection_count"].max())
    top_set_share = float(top_set_count / n_blocks)

    if audit_scope == "protocol":
        set_level = "protocol_parameter_set"
        value_level = "protocol_parameter_value"
        set_interpretation = (
            "Строка описывает частоту выбора одного набора гиперпараметров "
            "внутри одного протокола; "
            "не является итоговым вердиктом этапа 5."
        )
        value_interpretation = (
            "Строка описывает частоту выбора одного значения гиперпараметра "
            "внутри одного протокола; "
            "не является итоговым вердиктом этапа 5."
        )
    else:
        set_level = "all_protocols_parameter_set"
        value_level = "all_protocols_parameter_value"
        set_interpretation = (
            "Строка описывает частоту выбора одного набора гиперпараметров "
            "по всем завершенным протоколам; "
            "не является итоговым вердиктом этапа 5."
        )
        value_interpretation = (
            "Строка описывает частоту выбора одного значения гиперпараметра "
            "по всем завершенным протоколам; "
            "не является итоговым вердиктом этапа 5."
        )

    rows: list[dict[str, Any]] = []

    for _, count_row in parameter_set_counts.iterrows():
        selection_count = int(count_row["selection_count"])

        rows.append(
            _parameter_stability_row(
                **common_values,
                audit_level=set_level,
                parameter_name="all_parameters",
                parameter_value=count_row[
                    "selected_params_canonical_json"
                ],
                selected_parameter_set_id=count_row[
                    "selected_parameter_set_id"
                ],
                selection_count=selection_count,
                selection_share=float(selection_count / n_blocks),
                unique_parameter_set_count=unique_set_count,
                top_selection_count=top_set_count,
                top_selection_share=top_set_share,
                row_status="stage05_parameter_set_frequency",
                interpretation_allowed_ru=set_interpretation,
            )
        )

    stable_parameter_count = 0
    variable_parameter_names: list[str] = []

    for parameter_name in STAGE05_PARAMETER_STABILITY_PARAMETER_NAMES:
        parameter_values = group["selected_params_dict"].apply(
            lambda selected_params: _normalize_parameter_value(
                selected_params[parameter_name]
            )
        )

        value_counts = (
            parameter_values
            .value_counts(dropna=False)
            .rename_axis("parameter_value")
            .reset_index(name="selection_count")
            .sort_values(
                [
                    "selection_count",
                    "parameter_value",
                ],
                ascending=[False, True],
                kind="mergesort",
            )
        )

        unique_value_count = int(len(value_counts))
        top_value_count = int(value_counts["selection_count"].max())
        top_value_share = float(top_value_count / n_blocks)

        if unique_value_count == 1:
            stable_parameter_count += 1
        else:
            variable_parameter_names.append(parameter_name)

        stability_status, stability_status_ru, action_required = (
            _classify_parameter_value(
                unique_value_count,
                top_value_share,
            )
        )

        for _, value_row in value_counts.iterrows():
            selection_count = int(value_row["selection_count"])

            rows.append(
                _parameter_stability_row(
                    **common_values,
                    audit_level=value_level,
                    parameter_name=parameter_name,
                    parameter_value=value_row["parameter_value"],
                    selected_parameter_set_id="not_applicable",
                    selection_count=selection_count,
                    selection_share=float(selection_count / n_blocks),
                    unique_parameter_set_count=unique_value_count,
                    top_selection_count=top_value_count,
                    top_selection_share=top_value_share,
                    stability_status=stability_status,
                    stability_status_ru=stability_status_ru,
                    action_required=action_required,
                    row_status="stage05_parameter_value_frequency",
                    interpretation_allowed_ru=value_interpretation,
                )
            )

    if include_overall_row:
        overall_status, overall_status_ru, overall_action_required = (
            _classify_parameter_stability(
                top_share=top_set_share,
                unique_count=unique_set_count,
                stable_parameter_count=stable_parameter_count,
                total_parameter_count=len(
                    STAGE05_PARAMETER_STABILITY_PARAMETER_NAMES
                ),
            )
        )

        rows.append(
            _parameter_stability_row(
                **common_values,
                audit_level="overall_parameter_selection_stability",
                parameter_name="all_parameters",
                parameter_value=(
                    ";".join(variable_parameter_names)
                    if variable_parameter_names
                    else "all_parameters_stable"
                ),
                selected_parameter_set_id="overall",
                selection_count=top_set_count,
                selection_share=top_set_share,
                unique_parameter_set_count=unique_set_count,
                top_selection_count=top_set_count,
                top_selection_share=top_set_share,
                stability_status=overall_status,
                stability_status_ru=overall_status_ru,
                action_required=overall_action_required,
                row_status=(
                    "stage05_parameter_selection_stability_overall"
                ),
                interpretation_allowed_ru=(
                    "Итоговая строка ST05_05 описывает устойчивость "
                    "выбора гиперпараметров HGB по завершенным протоколам; "
                    "не является финальным вердиктом этапа 5."
                ),
            )
        )

    return rows


def build_parameter_selection_stability_audit(
    seed_outer_scores_df: pd.DataFrame,
    split_outer_scores_df: pd.DataFrame,
) -> pd.DataFrame:
    input_specs = [
        (
            "ST05_02",
            seed_outer_scores_df,
            "ST05_02_seed_stability_grid",
            "ST05_02_seed_stability_grid",
        ),
        (
            "ST05_03a",
            split_outer_scores_df,
            "ST05_03a_split_protocol_10x1",
            "ST05_03a_split_protocol_10x1",
        ),
    ]

    prepared_inputs: list[pd.DataFrame] = []

    for (
        artifact_name,
        scores_df,
        expected_stress_test_id,
        source_stage,
    ) in input_specs:
        require_non_empty(scores_df, artifact_name)
        require_columns(
            scores_df,
            STAGE05_PARAMETER_STABILITY_REQUIRED_COLUMNS,
            artifact_name,
        )

        actual_stress_test_ids = set(
            scores_df["stress_test_id"].unique()
        )

        if actual_stress_test_ids != {expected_stress_test_id}:
            raise ValueError(
                f"Набор stress_test_id для {artifact_name} "
                "не совпадает с ожидаемым. "
                f"Ожидалось: {[expected_stress_test_id]}, "
                f"получено: {sorted(actual_stress_test_ids)}"
            )

        prepared_inputs.append(
            scores_df.assign(source_stage=source_stage)
        )

    input_scores = pd.concat(
        prepared_inputs,
        ignore_index=True,
    )

    hgb_scores = input_scores[
        input_scores["claim_id"].eq(
            STAGE05_PARAMETER_STABILITY_CLAIM_ID
        )
        & input_scores["candidate_id"].eq(
            STAGE05_PARAMETER_STABILITY_CANDIDATE_ID
        )
        & input_scores["model_id"].eq(
            STAGE05_PARAMETER_STABILITY_MODEL_ID
        )
        & input_scores["model_role"].eq(
            STAGE05_PARAMETER_STABILITY_MODEL_ROLE
        )
    ].copy()

    require_non_empty(
        hgb_scores,
        "ST05_05 filtered HGB rows",
    )

    require_unique_key(
        hgb_scores,
        STAGE05_PARAMETER_STABILITY_UNIQUE_KEY,
        "ST05_05 filtered HGB rows",
    )

    actual_protocols = set(
        hgb_scores["protocol_variant_id"].unique()
    )

    if actual_protocols != STAGE05_PARAMETER_STABILITY_PROTOCOLS:
        raise ValueError(
            "Набор protocol_variant_id для ST05_05 "
            "не совпадает с ожидаемым. "
            f"Ожидалось: "
            f"{sorted(STAGE05_PARAMETER_STABILITY_PROTOCOLS)}, "
            f"получено: {sorted(actual_protocols)}"
        )

    if len(hgb_scores) != STAGE05_PARAMETER_STABILITY_EXPECTED_ROWS:
        raise ValueError(
            "Неожиданное число строк HGB для ST05_05: "
            f"ожидалось {STAGE05_PARAMETER_STABILITY_EXPECTED_ROWS}, "
            f"получено {len(hgb_scores)}"
        )

    hgb_scores["selected_params_dict"] = (
        hgb_scores["selected_params_json"]
        .apply(_parse_selected_params_json)
    )

    hgb_scores["selected_params_canonical_json"] = (
        hgb_scores["selected_params_dict"]
        .apply(
            lambda value: json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    )

    actual_parameter_names = sorted({
        parameter_name
        for selected_params in hgb_scores["selected_params_dict"]
        for parameter_name in selected_params.keys()
    })

    if (
        actual_parameter_names
        != STAGE05_PARAMETER_STABILITY_PARAMETER_NAMES
    ):
        raise ValueError(
            "Набор анализируемых параметров HGB "
            "не совпадает с ожидаемым. "
            f"Ожидалось: "
            f"{STAGE05_PARAMETER_STABILITY_PARAMETER_NAMES}, "
            f"получено: {actual_parameter_names}"
        )

    audit_rows: list[dict[str, Any]] = []

    for protocol_variant_id, group in hgb_scores.groupby(
        "protocol_variant_id",
        dropna=False,
    ):
        source_stages = group["source_stage"].unique()

        if len(source_stages) != 1:
            raise ValueError(
                f"Для протокола {protocol_variant_id} "
                "ожидался один source_stage, "
                f"получено: {sorted(source_stages)}"
            )

        audit_rows.extend(
            _build_parameter_scope_rows(
                group=group.copy(),
                audit_scope="protocol",
                source_stage=source_stages[0],
                protocol_variant_id=protocol_variant_id,
                include_overall_row=False,
            )
        )

    audit_rows.extend(
        _build_parameter_scope_rows(
            group=hgb_scores.copy(),
            audit_scope="all_protocols",
            source_stage="ST05_02_and_ST05_03a",
            protocol_variant_id=(
                "all_completed_preregistered_variants"
            ),
            include_overall_row=True,
        )
    )

    audit_df = pd.DataFrame(audit_rows).sort_values(
        [
            "audit_level",
            "protocol_variant_id",
            "parameter_name",
            "selection_count",
            "parameter_value",
        ],
        ascending=[True, True, True, False, True],
        kind="mergesort",
    )

    if (
        len(audit_df)
        != STAGE05_PARAMETER_STABILITY_EXPECTED_AUDIT_ROWS
    ):
        raise ValueError(
            "Неожиданное число строк ST05_05: "
            f"ожидалось "
            f"{STAGE05_PARAMETER_STABILITY_EXPECTED_AUDIT_ROWS}, "
            f"получено {len(audit_df)}"
        )

    return audit_df


STAGE05_COST_QUALITY_ID = "ST05_06_cost_quality_audit"
STAGE05_COST_QUALITY_CLAIM_ID = "miniboone_hgb_vs_logreg_average_precision_v01"
STAGE05_COST_QUALITY_CANDIDATE_ID = "openml_miniboone_41150"
STAGE05_COST_QUALITY_CANDIDATE_MODEL_ID = "hist_gradient_boosting"
STAGE05_COST_QUALITY_BASELINE_MODEL_ID = "logistic_regression"
STAGE05_COST_QUALITY_METRICS = [
    "average_precision",
    "roc_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
]
STAGE05_COST_QUALITY_KEY_COLUMNS = [
    "stress_test_id",
    "protocol_variant_id",
    "outer_random_state",
    "outer_split_number",
    "outer_repeat_number",
    "outer_fold_number",
]
STAGE05_COST_QUALITY_REQUIRED_COLUMNS = [
    *STAGE05_COST_QUALITY_KEY_COLUMNS,
    "claim_id",
    "candidate_id",
    "model_id",
    "model_role",
    "fit_seconds",
    "predict_seconds",
    *STAGE05_COST_QUALITY_METRICS,
]
STAGE05_COST_QUALITY_EXPECTED_PAIR_COUNTS = {
    "ST05_02_seed_stability_grid": 50,
    "ST05_03a_split_protocol_10x1": 30,
    "all_completed_preregistered_variants": 80,
}


def _require_exact_values(
    df: pd.DataFrame,
    column: str,
    expected_values: set[str],
    artifact_name: str,
) -> None:
    actual_values = set(df[column].astype(str).str.strip().unique())
    if actual_values != expected_values:
        raise ValueError(
            f"ST07_06: в артефакте {artifact_name} столбец {column} "
            "не совпадает с ожидаемым набором значений. "
            f"Ожидалось: {sorted(expected_values)}, "
            f"получено: {sorted(actual_values)}"
        )


def _prepare_cost_quality_input(
    scores_df: pd.DataFrame,
    artifact_name: str,
    expected_stress_test_id: str,
    expected_protocol_variant_id: str,
    expected_baseline_role: str,
    expected_pair_count: int,
) -> pd.DataFrame:
    require_non_empty(scores_df, artifact_name)
    require_columns(
        scores_df,
        STAGE05_COST_QUALITY_REQUIRED_COLUMNS,
        artifact_name,
    )

    for column, expected_values in [
        ("stress_test_id", {expected_stress_test_id}),
        ("claim_id", {STAGE05_COST_QUALITY_CLAIM_ID}),
        ("candidate_id", {STAGE05_COST_QUALITY_CANDIDATE_ID}),
        ("protocol_variant_id", {expected_protocol_variant_id}),
    ]:
        _require_exact_values(
            scores_df,
            column,
            expected_values,
            artifact_name,
        )

    pair_input_df = scores_df[
        scores_df["model_id"].isin(
            [
                STAGE05_COST_QUALITY_CANDIDATE_MODEL_ID,
                STAGE05_COST_QUALITY_BASELINE_MODEL_ID,
            ]
        )
    ].copy()
    require_non_empty(pair_input_df, f"{artifact_name} HGB/LR rows")
    _require_exact_values(
        pair_input_df,
        "model_id",
        {
            STAGE05_COST_QUALITY_CANDIDATE_MODEL_ID,
            STAGE05_COST_QUALITY_BASELINE_MODEL_ID,
        },
        f"{artifact_name} HGB/LR rows",
    )

    candidate_mask = pair_input_df["model_id"].eq(
        STAGE05_COST_QUALITY_CANDIDATE_MODEL_ID
    )
    baseline_mask = pair_input_df["model_id"].eq(
        STAGE05_COST_QUALITY_BASELINE_MODEL_ID
    )
    _require_exact_values(
        pair_input_df[candidate_mask],
        "model_role",
        {"tuned_candidate"},
        f"{artifact_name} HGB rows",
    )
    _require_exact_values(
        pair_input_df[baseline_mask],
        "model_role",
        {expected_baseline_role},
        f"{artifact_name} LR rows",
    )

    candidate_count = int(candidate_mask.sum())
    baseline_count = int(baseline_mask.sum())
    if candidate_count != expected_pair_count or baseline_count != expected_pair_count:
        raise ValueError(
            f"ST07_06: для {artifact_name} ожидалось по "
            f"{expected_pair_count} строк HGB и LR, получено "
            f"HGB={candidate_count}, LR={baseline_count}."
        )

    blank_key_counts = {
        column: int(pair_input_df[column].astype(str).str.strip().eq("").sum())
        for column in STAGE05_COST_QUALITY_KEY_COLUMNS
    }
    blank_key_counts = {
        column: count
        for column, count in blank_key_counts.items()
        if count > 0
    }
    if blank_key_counts:
        raise ValueError(
            f"ST07_06: в артефакте {artifact_name} обнаружены пустые "
            f"значения парного ключа: {blank_key_counts}"
        )

    require_unique_key(
        pair_input_df,
        [*STAGE05_COST_QUALITY_KEY_COLUMNS, "model_id"],
        f"{artifact_name} HGB/LR rows",
    )

    for column in [
        "fit_seconds",
        "predict_seconds",
        *STAGE05_COST_QUALITY_METRICS,
    ]:
        raw_values = pair_input_df[column].astype(str).str.strip()
        numeric_values = pd.to_numeric(raw_values, errors="coerce")
        invalid_mask = (
            raw_values.eq("")
            | numeric_values.isna()
            | ~np.isfinite(numeric_values)
        )
        if invalid_mask.any():
            raise ValueError(
                f"ST07_06: в артефакте {artifact_name} столбец {column} "
                "содержит пустые, нечисловые или бесконечные значения. "
                f"Число нарушений: {int(invalid_mask.sum())}; "
                f"примеры: {raw_values[invalid_mask].head(5).tolist()}"
            )
        pair_input_df[column] = numeric_values.astype(float)

    return pair_input_df


def _build_cost_quality_pairs(
    source_df: pd.DataFrame,
    protocol_scope_id: str,
) -> pd.DataFrame:
    candidate_rows = source_df[
        source_df["model_id"].eq(
            STAGE05_COST_QUALITY_CANDIDATE_MODEL_ID
        )
    ].copy()
    baseline_rows = source_df[
        source_df["model_id"].eq(
            STAGE05_COST_QUALITY_BASELINE_MODEL_ID
        )
    ].copy()

    try:
        pairs_df = candidate_rows.merge(
            baseline_rows,
            on=STAGE05_COST_QUALITY_KEY_COLUMNS,
            suffixes=("_candidate", "_baseline"),
            validate="one_to_one",
        )
    except pd.errors.MergeError as error:
        raise ValueError(
            "ST07_06: нарушена однозначность парного соединения HGB/LR "
            f"для области {protocol_scope_id}."
        ) from error

    if len(pairs_df) != len(candidate_rows) or len(pairs_df) != len(baseline_rows):
        raise ValueError(
            "ST07_06: нарушена полнота парного соединения HGB/LR "
            f"для области {protocol_scope_id}: "
            f"candidate_rows={len(candidate_rows)}, "
            f"baseline_rows={len(baseline_rows)}, pairs={len(pairs_df)}"
        )

    return pairs_df


def _safe_cost_quality_ratio(
    numerator: pd.Series,
    denominator: pd.Series,
    ratio_name: str,
    protocol_scope_id: str,
) -> pd.Series:
    if denominator.le(0).any():
        raise ValueError(
            f"ST07_06: для расчета {ratio_name} в области "
            f"{protocol_scope_id} обнаружено нулевое или отрицательное "
            "значение времени; расчет остановлен."
        )
    return numerator / denominator


def _summarize_cost_quality_scope(
    protocol_scope_id: str,
    pairs_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidate_fit = pairs_df["fit_seconds_candidate"]
    baseline_fit = pairs_df["fit_seconds_baseline"]
    candidate_predict = pairs_df["predict_seconds_candidate"]
    baseline_predict = pairs_df["predict_seconds_baseline"]
    candidate_total = candidate_fit + candidate_predict
    baseline_total = baseline_fit + baseline_predict
    fit_delta = candidate_fit - baseline_fit
    predict_delta = candidate_predict - baseline_predict
    total_delta = candidate_total - baseline_total
    fit_ratio = _safe_cost_quality_ratio(
        candidate_fit,
        baseline_fit,
        "отношения времени обучения",
        protocol_scope_id,
    )
    predict_ratio = _safe_cost_quality_ratio(
        candidate_predict,
        baseline_predict,
        "отношения времени предсказания",
        protocol_scope_id,
    )
    total_ratio = _safe_cost_quality_ratio(
        candidate_total,
        baseline_total,
        "отношения полного времени",
        protocol_scope_id,
    )

    for metric_name in STAGE05_COST_QUALITY_METRICS:
        metric_direction = METRIC_DIRECTIONS[metric_name]
        candidate_quality = pairs_df[f"{metric_name}_candidate"]
        baseline_quality = pairs_df[f"{metric_name}_baseline"]
        if metric_direction == "higher_is_better":
            quality_delta = candidate_quality - baseline_quality
        elif metric_direction == "lower_is_better":
            quality_delta = baseline_quality - candidate_quality
        else:
            raise ValueError(
                f"ST07_06: неизвестное направление метрики "
                f"{metric_name}: {metric_direction}"
            )

        mean_quality_delta = float(quality_delta.mean())
        mean_fit_delta = float(fit_delta.mean())
        mean_total_delta = float(total_delta.mean())
        if np.isclose(mean_quality_delta, 0.0):
            fit_cost_per_quality = np.nan
            total_cost_per_quality = np.nan
        else:
            fit_cost_per_quality = mean_fit_delta / mean_quality_delta
            total_cost_per_quality = mean_total_delta / mean_quality_delta

        all_quality_deltas_positive = bool(quality_delta.gt(0).all())
        fit_ratio_of_means = float(candidate_fit.mean() / baseline_fit.mean())
        if all_quality_deltas_positive and fit_ratio_of_means > 10.0:
            audit_status = "quality_advantage_with_high_training_cost_disclosed"
            audit_status_ru = (
                "Преимущество качества положительно во всех парных блоках, "
                "но стоимость обучения HGB существенно выше LR и должна быть явно раскрыта."
            )
        elif all_quality_deltas_positive:
            audit_status = "quality_advantage_cost_disclosed"
            audit_status_ru = (
                "Преимущество качества положительно во всех парных блоках; "
                "стоимость раскрыта в audit-файле."
            )
        else:
            audit_status = "requires_review"
            audit_status_ru = (
                "Преимущество качества не является положительным во всех парных блоках; "
                "требуется дополнительная проверка."
            )

        rows.append({
            "cost_quality_audit_id": STAGE05_COST_QUALITY_ID,
            "claim_id": STAGE05_COST_QUALITY_CLAIM_ID,
            "candidate_id": STAGE05_COST_QUALITY_CANDIDATE_ID,
            "candidate_model_id": STAGE05_COST_QUALITY_CANDIDATE_MODEL_ID,
            "baseline_model_id": STAGE05_COST_QUALITY_BASELINE_MODEL_ID,
            "protocol_scope_id": protocol_scope_id,
            "source_stress_test_ids": ";".join(sorted(pairs_df["stress_test_id"].unique())),
            "paired_outer_blocks": int(len(pairs_df)),
            "quality_metric": metric_name,
            "metric_direction": metric_direction,
            "candidate_quality_mean": round(float(candidate_quality.mean()), 6),
            "baseline_quality_mean": round(float(baseline_quality.mean()), 6),
            "quality_delta_directional_mean": round(mean_quality_delta, 6),
            "quality_delta_directional_median": round(float(quality_delta.median()), 6),
            "quality_delta_directional_min": round(float(quality_delta.min()), 6),
            "quality_delta_directional_max": round(float(quality_delta.max()), 6),
            "quality_delta_positive_blocks": int(quality_delta.gt(0).sum()),
            "quality_delta_negative_blocks": int(quality_delta.lt(0).sum()),
            "quality_delta_zero_blocks": int(quality_delta.eq(0).sum()),
            "candidate_fit_seconds_mean": round(float(candidate_fit.mean()), 6),
            "baseline_fit_seconds_mean": round(float(baseline_fit.mean()), 6),
            "fit_seconds_delta_mean": round(mean_fit_delta, 6),
            "fit_seconds_ratio_mean_of_pairs": round(float(fit_ratio.mean()), 6),
            "fit_seconds_ratio_of_means": round(fit_ratio_of_means, 6),
            "candidate_predict_seconds_mean": round(float(candidate_predict.mean()), 6),
            "baseline_predict_seconds_mean": round(float(baseline_predict.mean()), 6),
            "predict_seconds_delta_mean": round(float(predict_delta.mean()), 6),
            "predict_seconds_ratio_mean_of_pairs": round(float(predict_ratio.mean()), 6),
            "predict_seconds_ratio_of_means": round(
                float(candidate_predict.mean() / baseline_predict.mean()),
                6,
            ),
            "candidate_total_seconds_mean": round(float(candidate_total.mean()), 6),
            "baseline_total_seconds_mean": round(float(baseline_total.mean()), 6),
            "total_seconds_delta_mean": round(mean_total_delta, 6),
            "total_seconds_ratio_mean_of_pairs": round(float(total_ratio.mean()), 6),
            "total_seconds_ratio_of_means": round(
                float(candidate_total.mean() / baseline_total.mean()),
                6,
            ),
            "fit_seconds_delta_per_quality_delta_mean": round(
                float(fit_cost_per_quality),
                6,
            ),
            "total_seconds_delta_per_quality_delta_mean": round(
                float(total_cost_per_quality),
                6,
            ),
            "audit_status": audit_status,
            "audit_status_ru": audit_status_ru,
            "row_status": "stage05_cost_quality_audit_derived",
            "interpretation_allowed_ru": (
                "Разрешен только аудит соотношения качества и вычислительной стоимости; "
                "строка не является самостоятельным итоговым вердиктом этапа 5."
            ),
        })

    return rows


def build_cost_quality_audit(
    seed_outer_scores_df: pd.DataFrame,
    split_outer_scores_df: pd.DataFrame,
) -> pd.DataFrame:
    input_specs = [
        (
            seed_outer_scores_df,
            "ST05_02",
            "ST05_02_seed_stability_grid",
            "nested_5x2_seed_grid_v01",
            "control",
            50,
        ),
        (
            split_outer_scores_df,
            "ST05_03a",
            "ST05_03a_split_protocol_10x1",
            "nested_10x1_seed_grid_v01",
            "baseline",
            30,
        ),
    ]
    prepared_inputs: dict[str, pd.DataFrame] = {}

    for (
        scores_df,
        artifact_name,
        stress_test_id,
        protocol_variant_id,
        baseline_role,
        expected_pair_count,
    ) in input_specs:
        prepared_inputs[stress_test_id] = _prepare_cost_quality_input(
            scores_df=scores_df,
            artifact_name=artifact_name,
            expected_stress_test_id=stress_test_id,
            expected_protocol_variant_id=protocol_variant_id,
            expected_baseline_role=baseline_role,
            expected_pair_count=expected_pair_count,
        )

    all_pair_input_df = pd.concat(
        list(prepared_inputs.values()),
        ignore_index=True,
    )
    pairs_by_scope = {
        scope_id: _build_cost_quality_pairs(source_df, scope_id)
        for scope_id, source_df in prepared_inputs.items()
    }
    pairs_by_scope["all_completed_preregistered_variants"] = (
        _build_cost_quality_pairs(
            all_pair_input_df,
            "all_completed_preregistered_variants",
        )
    )

    for scope_id, expected_pair_count in (
        STAGE05_COST_QUALITY_EXPECTED_PAIR_COUNTS.items()
    ):
        actual_pair_count = len(pairs_by_scope[scope_id])
        if actual_pair_count != expected_pair_count:
            raise ValueError(
                f"ST07_06: для области {scope_id} ожидалось "
                f"{expected_pair_count} пар, получено {actual_pair_count}."
            )

    audit_rows: list[dict[str, Any]] = []
    for scope_id, pairs_df in pairs_by_scope.items():
        audit_rows.extend(_summarize_cost_quality_scope(scope_id, pairs_df))

    audit_df = pd.DataFrame(audit_rows).sort_values(
        ["protocol_scope_id", "quality_metric"],
        kind="mergesort",
    )
    expected_rows = (
        len(STAGE05_COST_QUALITY_EXPECTED_PAIR_COUNTS)
        * len(STAGE05_COST_QUALITY_METRICS)
    )
    if len(audit_df) != expected_rows:
        raise ValueError(
            f"ST07_06: ожидалось {expected_rows} строк результата, "
            f"получено {len(audit_df)}."
        )
    if len(audit_df.columns) != 40:
        raise ValueError(
            "ST07_06: ожидалось 40 столбцов результата, "
            f"получено {len(audit_df.columns)}."
        )

    require_unique_key(
        audit_df,
        ["protocol_scope_id", "quality_metric"],
        "ST05_06 cost-quality audit result",
    )
    missing_values = audit_df.isna().sum()
    missing_values = missing_values[missing_values.gt(0)]
    if not missing_values.empty:
        raise ValueError(
            f"ST07_06: результат содержит пропуски: {missing_values.to_dict()}"
        )

    return audit_df


VERDICT_POLICY_ID = "miniboone_verdict_policy_v01"
VERDICT_CLAIM_ID = "miniboone_hgb_vs_logreg_average_precision_v01"
VERDICT_CANDIDATE_ID = "openml_miniboone_41150"
VERDICT_CANDIDATE_MODEL_ID = "hist_gradient_boosting"
VERDICT_BASELINE_MODEL_ID = "logistic_regression"
VERDICT_PRIMARY_METRIC = "average_precision"
VERDICT_EVALUATOR_CONTRACT_ID = "miniboone_verdict_policy_evaluators_v01"
VERDICT_EVALUATOR_VERSION = "v01"
VERDICT_CATEGORY_ORDER = (
    "strongly_supported",
    "moderately_supported",
    "weakly_supported",
    "fragile",
    "unsupported",
    "contradicted",
)
VERDICT_CLAUSE_IDS = (
    "quality_gate",
    "primary_metric",
    "secondary_metric",
    "stability",
    "cost",
)
VERDICT_POLICY_COLUMNS = (
    "policy_id",
    "claim_id",
    "category_id",
    "category_ru",
    "decision_rank",
    "quality_gate_ru",
    "primary_metric_condition_ru",
    "secondary_metric_condition_ru",
    "stability_condition_ru",
    "cost_condition_ru",
    "allowed_language_ru",
    "forbidden_language_ru",
    "decision_status",
    "internal_source",
    "external_source_url",
    "notes_ru",
)
VERDICT_SECONDARY_METRICS = (
    "roc_auc",
    "f1",
    "balanced_accuracy",
    "log_loss",
    "brier_score",
)
VERDICT_REQUIRED_FAMILY_IDS = (
    "current_evidence_readout",
    "random_seed_stability",
    "metric_conflict",
)
VERDICT_REQUIRED_SOURCE_PATHS = (
    "configs/claims/miniboone_hgb_vs_logreg_claim_v01.csv",
    "data_registry/openml_miniboone_nested_quality_checks.csv",
    "data_registry/openml_miniboone_stage05_current_effect_readout.csv",
    "data_registry/openml_miniboone_stage05_seed_stability_outer_scores.csv",
    "data_registry/openml_miniboone_stage05_split_10x1_outer_scores.csv",
    "data_registry/openml_miniboone_stage05_metric_conflict_audit.csv",
    "data_registry/openml_miniboone_stage05_parameter_selection_stability.csv",
    "data_registry/openml_miniboone_stage05_cost_quality_audit.csv",
    "data_registry/openml_miniboone_stage05_non_nested_optimism_probe.csv",
)
VERDICT_EVALUATION_OUTCOMES = {
    "PASS",
    "FAIL",
    "INDETERMINATE",
    "NOT_EVALUATED_AFTER_MATCH",
}
VERDICT_APPLICATION_STATUSES = {
    "APPLIED",
    "INDETERMINATE_FAIL_CLOSED",
    "NO_CATEGORY_MATCH_FAIL_CLOSED",
}


@dataclass(frozen=True)
class VerdictEvidenceRecordV01:
    policy_id: str
    claim_id: str
    candidate_id: str
    candidate_model_id: str
    baseline_model_id: str
    primary_metric: str
    required_check_count: int
    passed_check_count: int
    error_count: int
    fatal_warning_count: int
    paired_block_count: int
    candidate_positive_blocks: int
    positive_share: float
    directional_delta_mean: float
    directional_delta_q05_linear: float
    metric_names: tuple[str, ...]
    paired_blocks_per_metric: int
    support_share_by_metric: tuple[tuple[str, float], ...]
    systematic_conflict_metric_count: int
    required_family_ids: tuple[str, ...]
    positive_current_readout: bool
    positive_seed_family: bool
    metric_conflict_status: str
    parameter_stability_status: str
    fit_seconds_ratio_of_means: float
    total_seconds_ratio_of_means: float
    high_training_cost: bool
    non_nested_comparison_count: int
    non_nested_delta_mean: float
    non_nested_audit_scope: str
    source_sha256: tuple[tuple[str, str], ...]
    evaluator_contract_id: str


@dataclass(frozen=True)
class VerdictConditionEvaluationV01:
    policy_id: str
    claim_id: str
    category_id: str
    clause_id: str
    decision_rank: int
    evaluator_id: str
    evaluator_version: str
    outcome: str
    observed_fact_ids: tuple[str, ...]
    reason_code: str


@dataclass(frozen=True)
class VerdictPolicyApplicationResultV01:
    application_id: str
    policy_id: str
    claim_id: str
    application_status: str
    selected_category_id: str | None
    selected_decision_rank: int | None
    selected_category_ru: str | None
    quality_gate_outcome: str
    primary_metric_outcome: str
    secondary_metric_outcome: str
    stability_outcome: str
    cost_outcome: str
    required_disclosures: tuple[str, ...]
    allowed_language_ru: str | None
    forbidden_language_ru: str | None
    evidence_record_sha256: str
    policy_sha256: str
    row_status: str
    interpretation_limit_ru: str


def _require_nonblank_value(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"ST07_35: поле {field_name} не может быть пустым")
    return normalized


def _require_sha256(value: Any, field_name: str) -> str:
    normalized = _require_nonblank_value(value, field_name).lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"ST07_35: поле {field_name} не является SHA-256")
    return normalized


def _require_finite(value: Any, field_name: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"ST07_35: поле {field_name} нельзя преобразовать в float"
        ) from error
    if not np.isfinite(normalized):
        raise ValueError(f"ST07_35: поле {field_name} должно быть конечным")
    return normalized


def _require_exact_column_values(
    frame: pd.DataFrame,
    column: str,
    expected: set[str],
    artifact_name: str,
) -> None:
    require_columns(frame, [column], artifact_name)
    actual = set(frame[column].astype(str).str.strip().unique())
    if actual != expected:
        raise ValueError(
            f"ST07_35: {artifact_name}.{column}: ожидалось "
            f"{sorted(expected)}, получено {sorted(actual)}"
        )


def _validate_registered_verdict_policy(policy_df: pd.DataFrame) -> pd.DataFrame:
    require_non_empty(policy_df, "ST07_35 registered verdict policy")
    if tuple(policy_df.columns) != VERDICT_POLICY_COLUMNS:
        raise ValueError(
            "ST07_35: схема verdict policy должна точно совпадать с v01"
        )
    if policy_df.shape != (6, 16):
        raise ValueError(
            f"ST07_35: ожидалась policy 6x16, получено {policy_df.shape}"
        )
    prepared = policy_df.copy()
    _require_exact_column_values(
        prepared, "policy_id", {VERDICT_POLICY_ID}, "verdict policy"
    )
    _require_exact_column_values(
        prepared, "claim_id", {VERDICT_CLAIM_ID}, "verdict policy"
    )
    _require_exact_column_values(
        prepared, "decision_status", {"locked_before_stage05_runs"}, "verdict policy"
    )
    if not prepared["category_id"].is_unique:
        raise ValueError("ST07_35: category_id verdict policy не уникален")
    ranks = pd.to_numeric(prepared["decision_rank"], errors="raise")
    if not ranks.is_unique or set(ranks.astype(int)) != set(range(1, 7)):
        raise ValueError("ST07_35: decision_rank должен быть уникальным набором 1..6")
    prepared["decision_rank"] = ranks.astype(int)
    prepared = prepared.sort_values(
        "decision_rank", ascending=False, kind="mergesort"
    ).reset_index(drop=True)
    if tuple(prepared["category_id"]) != VERDICT_CATEGORY_ORDER:
        raise ValueError("ST07_35: категории policy не совпадают с v01")
    for column in (
        "category_ru",
        "quality_gate_ru",
        "primary_metric_condition_ru",
        "secondary_metric_condition_ru",
        "stability_condition_ru",
        "cost_condition_ru",
        "allowed_language_ru",
        "forbidden_language_ru",
    ):
        if prepared[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"ST07_35: policy содержит пустое поле {column}")
    return prepared


def _paired_primary_deltas(
    scores_df: pd.DataFrame,
    artifact_name: str,
    expected_stress_test_id: str,
    expected_rows_per_model: int,
) -> pd.DataFrame:
    required = [
        "stress_test_id",
        "claim_id",
        "candidate_id",
        "outer_random_state",
        "outer_split_number",
        "model_id",
        VERDICT_PRIMARY_METRIC,
    ]
    require_non_empty(scores_df, artifact_name)
    require_columns(scores_df, required, artifact_name)
    _require_exact_column_values(
        scores_df, "stress_test_id", {expected_stress_test_id}, artifact_name
    )
    _require_exact_column_values(
        scores_df, "claim_id", {VERDICT_CLAIM_ID}, artifact_name
    )
    _require_exact_column_values(
        scores_df, "candidate_id", {VERDICT_CANDIDATE_ID}, artifact_name
    )
    selected = scores_df[
        scores_df["model_id"].isin(
            [VERDICT_CANDIDATE_MODEL_ID, VERDICT_BASELINE_MODEL_ID]
        )
    ].copy()
    _require_exact_column_values(
        selected,
        "model_id",
        {VERDICT_CANDIDATE_MODEL_ID, VERDICT_BASELINE_MODEL_ID},
        artifact_name,
    )
    key = ["outer_random_state", "outer_split_number"]
    require_unique_key(selected, [*key, "model_id"], artifact_name)
    candidate = selected[selected["model_id"].eq(VERDICT_CANDIDATE_MODEL_ID)]
    baseline = selected[selected["model_id"].eq(VERDICT_BASELINE_MODEL_ID)]
    if len(candidate) != expected_rows_per_model or len(baseline) != expected_rows_per_model:
        raise ValueError(
            f"ST07_35: {artifact_name} должен содержать по "
            f"{expected_rows_per_model} строк HGB/LR"
        )
    try:
        paired = candidate.merge(
            baseline,
            on=key,
            suffixes=("_candidate", "_baseline"),
            validate="one_to_one",
        )
    except pd.errors.MergeError as error:
        raise ValueError(f"ST07_35: нарушено парное соединение {artifact_name}") from error
    candidate_values = pd.to_numeric(
        paired[f"{VERDICT_PRIMARY_METRIC}_candidate"], errors="raise"
    ).astype(float)
    baseline_values = pd.to_numeric(
        paired[f"{VERDICT_PRIMARY_METRIC}_baseline"], errors="raise"
    ).astype(float)
    if not np.isfinite(candidate_values).all() or not np.isfinite(baseline_values).all():
        raise ValueError(f"ST07_35: {artifact_name} содержит неконечную метрику")
    return pd.DataFrame({
        "outer_random_state": paired["outer_random_state"].astype(str),
        "directional_delta": candidate_values - baseline_values,
    })


def build_verdict_evidence_record(
    claim_df: pd.DataFrame,
    quality_checks_df: pd.DataFrame,
    current_effect_readout_df: pd.DataFrame,
    seed_outer_scores_df: pd.DataFrame,
    split_outer_scores_df: pd.DataFrame,
    metric_conflict_df: pd.DataFrame,
    parameter_stability_df: pd.DataFrame,
    cost_quality_df: pd.DataFrame,
    non_nested_df: pd.DataFrame,
    *,
    source_sha256: Mapping[str, str],
    policy_id: str = VERDICT_POLICY_ID,
    evaluator_contract_id: str = VERDICT_EVALUATOR_CONTRACT_ID,
) -> VerdictEvidenceRecordV01:
    require_non_empty(claim_df, "ST07_35 registered claim")
    if len(claim_df) != 1:
        raise ValueError("ST07_35: зарегистрированный claim должен иметь одну строку")
    claim = claim_df.iloc[0]
    claim_identity = {
        "claim_id": VERDICT_CLAIM_ID,
        "candidate_id": VERDICT_CANDIDATE_ID,
        "candidate_model_id": VERDICT_CANDIDATE_MODEL_ID,
        "baseline_model_id": VERDICT_BASELINE_MODEL_ID,
        "primary_metric": VERDICT_PRIMARY_METRIC,
    }
    require_columns(claim_df, list(claim_identity), "ST07_35 registered claim")
    for field_name, expected in claim_identity.items():
        if str(claim[field_name]).strip() != expected:
            raise ValueError(
                f"ST07_35: claim.{field_name}: ожидалось {expected}, "
                f"получено {claim[field_name]}"
            )
    if _require_nonblank_value(policy_id, "policy_id") != VERDICT_POLICY_ID:
        raise ValueError("ST07_35: неизвестный policy_id")
    if evaluator_contract_id != VERDICT_EVALUATOR_CONTRACT_ID:
        raise ValueError("ST07_35: неизвестный evaluator_contract_id")

    require_non_empty(quality_checks_df, "ST07_35 quality checks")
    require_columns(
        quality_checks_df,
        ["protocol_id", "check_id", "check_result"],
        "ST07_35 quality checks",
    )
    _require_exact_column_values(
        quality_checks_df,
        "protocol_id",
        {"miniboone_nested_cv_v01"},
        "quality checks",
    )
    require_unique_key(quality_checks_df, ["check_id"], "ST07_35 quality checks")
    allowed_quality = {"pass", "error", "fatal_warning"}
    actual_quality = set(quality_checks_df["check_result"].astype(str).str.strip())
    if not actual_quality.issubset(allowed_quality):
        raise ValueError("ST07_35: неизвестный check_result quality gate")
    required_check_count = int(len(quality_checks_df))
    passed_check_count = int(quality_checks_df["check_result"].eq("pass").sum())
    error_count = int(quality_checks_df["check_result"].eq("error").sum())
    fatal_warning_count = int(
        quality_checks_df["check_result"].eq("fatal_warning").sum()
    )

    require_non_empty(current_effect_readout_df, "ST07_35 current effect readout")
    require_columns(
        current_effect_readout_df,
        [
            "claim_id",
            "candidate_id",
            "comparison_role",
            "candidate_model_id",
            "comparison_model_id",
            "metric_name",
            "row_type",
            "n_blocks",
            "candidate_positive_blocks",
            "candidate_negative_blocks",
            "candidate_zero_blocks",
        ],
        "ST07_35 current effect readout",
    )
    for column, expected in (
        ("claim_id", {VERDICT_CLAIM_ID}),
        ("candidate_id", {VERDICT_CANDIDATE_ID}),
        ("candidate_model_id", {VERDICT_CANDIDATE_MODEL_ID}),
    ):
        _require_exact_column_values(
            current_effect_readout_df, column, expected, "current effect readout"
        )
    current_summary = current_effect_readout_df[
        current_effect_readout_df["comparison_role"].eq("primary_baseline")
        & current_effect_readout_df["comparison_model_id"].eq(
            VERDICT_BASELINE_MODEL_ID
        )
        & current_effect_readout_df["metric_name"].eq(VERDICT_PRIMARY_METRIC)
        & current_effect_readout_df["row_type"].eq("metric_summary")
    ]
    if len(current_summary) != 1:
        raise ValueError("ST07_35: нужна одна ST05_01 primary metric summary")
    current_positive = int(current_summary.iloc[0]["candidate_positive_blocks"])
    current_total = int(current_summary.iloc[0]["n_blocks"])
    current_negative = int(current_summary.iloc[0]["candidate_negative_blocks"])
    current_zero = int(current_summary.iloc[0]["candidate_zero_blocks"])
    if (
        current_total <= 0
        or current_positive + current_negative + current_zero != current_total
        or not (0 <= current_positive <= current_total)
    ):
        raise ValueError("ST07_35: ST05_01 current readout counts несогласованы")
    if (
        int(claim["current_positive_blocks_hgb_minus_logreg"]) != current_positive
        or int(claim["current_total_blocks"]) != current_total
    ):
        raise ValueError("ST07_35: claim и ST05_01 current readout расходятся")

    seed_deltas = _paired_primary_deltas(
        seed_outer_scores_df,
        "ST05_02 seed outer scores",
        "ST05_02_seed_stability_grid",
        50,
    )
    split_deltas = _paired_primary_deltas(
        split_outer_scores_df,
        "ST05_03a split outer scores",
        "ST05_03a_split_protocol_10x1",
        30,
    )
    primary = pd.concat(
        [seed_deltas["directional_delta"], split_deltas["directional_delta"]],
        ignore_index=True,
    ).astype(float)
    positive_blocks = int(primary.gt(0).sum())
    paired_block_count = int(len(primary))
    seed_means = seed_deltas.groupby("outer_random_state")[
        "directional_delta"
    ].mean()
    if len(seed_means) != 5:
        raise ValueError("ST07_35: ожидалось пять seed-family состояний")

    require_non_empty(metric_conflict_df, "ST07_35 metric conflict audit")
    for column, expected in (
        ("claim_id", {VERDICT_CLAIM_ID}),
        ("candidate_id", {VERDICT_CANDIDATE_ID}),
        ("candidate_model_id", {VERDICT_CANDIDATE_MODEL_ID}),
        ("comparison_model_id", {VERDICT_BASELINE_MODEL_ID}),
    ):
        _require_exact_column_values(metric_conflict_df, column, expected, "metric audit")
    require_columns(
        metric_conflict_df,
        [
            "audit_level",
            "metric_name",
            "metric_role",
            "n_blocks",
            "candidate_positive_blocks",
            "metric_conflict_status",
        ],
        "ST07_35 metric conflict audit",
    )
    all_metric = metric_conflict_df[
        metric_conflict_df["audit_level"].eq("all_protocols_metric")
    ].copy()
    secondary = all_metric[all_metric["metric_role"].eq("secondary")].copy()
    if set(secondary["metric_name"]) != set(VERDICT_SECONDARY_METRICS) or len(secondary) != 5:
        raise ValueError("ST07_35: набор вторичных метрик не совпадает с v01")
    require_unique_key(secondary, ["metric_name"], "ST07_35 secondary metrics")
    secondary["n_blocks"] = pd.to_numeric(secondary["n_blocks"], errors="raise").astype(int)
    secondary["candidate_positive_blocks"] = pd.to_numeric(
        secondary["candidate_positive_blocks"], errors="raise"
    ).astype(int)
    if not secondary["n_blocks"].eq(80).all():
        raise ValueError("ST07_35: каждая вторичная метрика должна иметь 80 блоков")
    support_share = tuple(
        (
            metric_name,
            float(
                secondary.loc[secondary["metric_name"].eq(metric_name), "candidate_positive_blocks"].iloc[0]
                / secondary.loc[secondary["metric_name"].eq(metric_name), "n_blocks"].iloc[0]
            ),
        )
        for metric_name in VERDICT_SECONDARY_METRICS
    )
    overall_metric = metric_conflict_df[
        metric_conflict_df["audit_level"].eq("overall_metric_conflict_audit")
    ]
    if len(overall_metric) != 1:
        raise ValueError("ST07_35: нужна одна overall metric-conflict строка")
    metric_conflict_status = _require_nonblank_value(
        overall_metric.iloc[0]["metric_conflict_status"], "metric_conflict_status"
    )
    systematic_conflict_count = int(
        secondary["metric_conflict_status"].ne("no_conflict").sum()
    )

    require_non_empty(parameter_stability_df, "ST07_35 parameter stability")
    _require_exact_column_values(
        parameter_stability_df,
        "claim_id",
        {VERDICT_CLAIM_ID},
        "parameter stability",
    )
    parameter_overall = parameter_stability_df[
        parameter_stability_df["audit_level"].eq(
            "overall_parameter_selection_stability"
        )
    ]
    if len(parameter_overall) != 1:
        raise ValueError("ST07_35: нужна одна overall parameter-stability строка")
    parameter_stability_status = _require_nonblank_value(
        parameter_overall.iloc[0]["stability_status"],
        "parameter_stability_status",
    )

    require_non_empty(cost_quality_df, "ST07_35 cost-quality audit")
    for column, expected in (
        ("claim_id", {VERDICT_CLAIM_ID}),
        ("candidate_id", {VERDICT_CANDIDATE_ID}),
        ("candidate_model_id", {VERDICT_CANDIDATE_MODEL_ID}),
        ("baseline_model_id", {VERDICT_BASELINE_MODEL_ID}),
    ):
        _require_exact_column_values(cost_quality_df, column, expected, "cost-quality audit")
    cost_primary = cost_quality_df[
        cost_quality_df["protocol_scope_id"].eq(
            "all_completed_preregistered_variants"
        )
        & cost_quality_df["quality_metric"].eq(VERDICT_PRIMARY_METRIC)
    ]
    if len(cost_primary) != 1:
        raise ValueError("ST07_35: нужна одна all-protocol primary cost строка")
    fit_ratio = _require_finite(
        cost_primary.iloc[0]["fit_seconds_ratio_of_means"],
        "fit_seconds_ratio_of_means",
    )
    total_ratio = _require_finite(
        cost_primary.iloc[0]["total_seconds_ratio_of_means"],
        "total_seconds_ratio_of_means",
    )
    if fit_ratio < 0 or total_ratio < 0:
        raise ValueError("ST07_35: отношения стоимости не могут быть отрицательными")

    require_non_empty(non_nested_df, "ST07_35 non-nested audit")
    _require_exact_column_values(
        non_nested_df, "claim_id", {VERDICT_CLAIM_ID}, "non-nested audit"
    )
    non_nested_delta = pd.to_numeric(
        non_nested_df["optimism_delta_non_nested_minus_nested"], errors="raise"
    ).astype(float)
    if not np.isfinite(non_nested_delta).all():
        raise ValueError("ST07_35: non-nested delta должен быть конечным")

    actual_source_paths = set(source_sha256)
    if actual_source_paths != set(VERDICT_REQUIRED_SOURCE_PATHS):
        raise ValueError(
            "ST07_35: source_sha256 должен точно покрывать восемь входных источников"
        )
    normalized_hashes = tuple(
        (path, _require_sha256(source_sha256[path], f"source_sha256[{path}]"))
        for path in VERDICT_REQUIRED_SOURCE_PATHS
    )

    record = VerdictEvidenceRecordV01(
        policy_id=VERDICT_POLICY_ID,
        claim_id=VERDICT_CLAIM_ID,
        candidate_id=VERDICT_CANDIDATE_ID,
        candidate_model_id=VERDICT_CANDIDATE_MODEL_ID,
        baseline_model_id=VERDICT_BASELINE_MODEL_ID,
        primary_metric=VERDICT_PRIMARY_METRIC,
        required_check_count=required_check_count,
        passed_check_count=passed_check_count,
        error_count=error_count,
        fatal_warning_count=fatal_warning_count,
        paired_block_count=paired_block_count,
        candidate_positive_blocks=positive_blocks,
        positive_share=float(positive_blocks / paired_block_count),
        directional_delta_mean=float(primary.mean()),
        directional_delta_q05_linear=float(
            primary.quantile(0.05, interpolation="linear")
        ),
        metric_names=VERDICT_SECONDARY_METRICS,
        paired_blocks_per_metric=80,
        support_share_by_metric=support_share,
        systematic_conflict_metric_count=systematic_conflict_count,
        required_family_ids=VERDICT_REQUIRED_FAMILY_IDS,
        positive_current_readout=current_positive == current_total,
        positive_seed_family=bool(seed_means.gt(0).all()),
        metric_conflict_status=metric_conflict_status,
        parameter_stability_status=parameter_stability_status,
        fit_seconds_ratio_of_means=fit_ratio,
        total_seconds_ratio_of_means=total_ratio,
        high_training_cost=fit_ratio > 10.0,
        non_nested_comparison_count=int(len(non_nested_delta)),
        non_nested_delta_mean=float(non_nested_delta.mean()),
        non_nested_audit_scope="diagnostic_only_not_external_performance_evidence",
        source_sha256=normalized_hashes,
        evaluator_contract_id=evaluator_contract_id,
    )
    _validate_verdict_evidence_record(record)
    return record


def _validate_verdict_evidence_record(record: VerdictEvidenceRecordV01) -> None:
    expected_identity = {
        "policy_id": VERDICT_POLICY_ID,
        "claim_id": VERDICT_CLAIM_ID,
        "candidate_id": VERDICT_CANDIDATE_ID,
        "candidate_model_id": VERDICT_CANDIDATE_MODEL_ID,
        "baseline_model_id": VERDICT_BASELINE_MODEL_ID,
        "primary_metric": VERDICT_PRIMARY_METRIC,
    }
    for field_name, expected in expected_identity.items():
        if _require_nonblank_value(getattr(record, field_name), field_name) != expected:
            raise ValueError(f"ST07_35: evidence identity {field_name} не совпадает")
    if record.evaluator_contract_id != VERDICT_EVALUATOR_CONTRACT_ID:
        raise ValueError("ST07_35: evaluator_contract_id evidence неизвестен")
    counts = (
        record.required_check_count,
        record.passed_check_count,
        record.error_count,
        record.fatal_warning_count,
        record.paired_block_count,
        record.candidate_positive_blocks,
        record.paired_blocks_per_metric,
        record.systematic_conflict_metric_count,
        record.non_nested_comparison_count,
    )
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in counts):
        raise ValueError("ST07_35: evidence counts должны быть целыми неотрицательными")
    if (
        record.passed_check_count + record.error_count + record.fatal_warning_count
        != record.required_check_count
    ):
        raise ValueError("ST07_35: quality counts несогласованы")
    if record.paired_block_count <= 0 or not (
        0 <= record.candidate_positive_blocks <= record.paired_block_count
    ):
        raise ValueError("ST07_35: primary paired counts несогласованы")
    expected_share = record.candidate_positive_blocks / record.paired_block_count
    if not math.isclose(record.positive_share, expected_share, rel_tol=0, abs_tol=1e-15):
        raise ValueError("ST07_35: primary positive_share не согласован со счётчиками")
    for field_name in (
        "positive_share",
        "directional_delta_mean",
        "directional_delta_q05_linear",
        "fit_seconds_ratio_of_means",
        "total_seconds_ratio_of_means",
        "non_nested_delta_mean",
    ):
        _require_finite(getattr(record, field_name), field_name)
    if not 0.0 <= record.positive_share <= 1.0:
        raise ValueError("ST07_35: positive_share вне диапазона [0, 1]")
    if record.metric_names != VERDICT_SECONDARY_METRICS:
        raise ValueError("ST07_35: evidence metric_names не совпадает с v01")
    if record.paired_blocks_per_metric <= 0:
        raise ValueError("ST07_35: paired_blocks_per_metric должен быть положительным")
    if tuple(name for name, _ in record.support_share_by_metric) != VERDICT_SECONDARY_METRICS:
        raise ValueError("ST07_35: support_share_by_metric имеет неверный порядок")
    for metric_name, value in record.support_share_by_metric:
        share = _require_finite(value, f"support_share_by_metric[{metric_name}]")
        if not 0.0 <= share <= 1.0:
            raise ValueError("ST07_35: secondary support share вне диапазона [0, 1]")
    if record.required_family_ids != VERDICT_REQUIRED_FAMILY_IDS:
        raise ValueError("ST07_35: required_family_ids не совпадает с v01")
    if record.high_training_cost != (record.fit_seconds_ratio_of_means > 10.0):
        raise ValueError("ST07_35: high_training_cost не согласован с fit ratio")
    if record.non_nested_comparison_count <= 0:
        raise ValueError("ST07_35: non_nested_comparison_count должен быть положительным")
    source_paths = tuple(path for path, _ in record.source_sha256)
    if source_paths != VERDICT_REQUIRED_SOURCE_PATHS:
        raise ValueError("ST07_35: evidence source hashes неполны или не упорядочены")
    for path, digest in record.source_sha256:
        _require_sha256(digest, f"source_sha256[{path}]")


def _condition_evaluation(
    *,
    category_id: str,
    clause_id: str,
    decision_rank: int,
    outcome: str,
    facts: Sequence[str],
    reason_code: str,
) -> VerdictConditionEvaluationV01:
    return VerdictConditionEvaluationV01(
        policy_id=VERDICT_POLICY_ID,
        claim_id=VERDICT_CLAIM_ID,
        category_id=category_id,
        clause_id=clause_id,
        decision_rank=decision_rank,
        evaluator_id=f"{VERDICT_EVALUATOR_CONTRACT_ID}:{category_id}:{clause_id}",
        evaluator_version=VERDICT_EVALUATOR_VERSION,
        outcome=outcome,
        observed_fact_ids=tuple(facts),
        reason_code=reason_code,
    )


def _evaluate_strongly_supported(
    record: VerdictEvidenceRecordV01,
) -> tuple[VerdictConditionEvaluationV01, ...]:
    clauses = (
        (
            "quality_gate",
            record.required_check_count == record.passed_check_count
            and record.error_count == 0
            and record.fatal_warning_count == 0,
            ("required_check_count", "passed_check_count", "error_count", "fatal_warning_count"),
        ),
        (
            "primary_metric",
            record.positive_share >= 0.95
            and record.directional_delta_mean >= 0.03
            and record.directional_delta_q05_linear > 0.01,
            ("positive_share", "directional_delta_mean", "directional_delta_q05_linear"),
        ),
        (
            "secondary_metric",
            all(share >= 0.90 for _, share in record.support_share_by_metric)
            and record.systematic_conflict_metric_count == 0,
            ("support_share_by_metric", "systematic_conflict_metric_count"),
        ),
        (
            "stability",
            record.positive_current_readout
            and record.positive_seed_family
            and record.metric_conflict_status == "no_metric_conflict_detected",
            (
                "positive_current_readout",
                "positive_seed_family",
                "metric_conflict_status",
                "parameter_stability_status",
            ),
        ),
        (
            "cost",
            record.fit_seconds_ratio_of_means >= 0
            and record.total_seconds_ratio_of_means >= 0
            and record.high_training_cost
            == (record.fit_seconds_ratio_of_means > 10.0),
            (
                "fit_seconds_ratio_of_means",
                "total_seconds_ratio_of_means",
                "high_training_cost",
            ),
        ),
    )
    return tuple(
        _condition_evaluation(
            category_id="strongly_supported",
            clause_id=clause_id,
            decision_rank=6,
            outcome="PASS" if passed else "FAIL",
            facts=facts,
            reason_code=(
                "registered_strong_thresholds_satisfied_v01"
                if passed
                else "registered_strong_thresholds_not_satisfied_v01"
            ),
        )
        for clause_id, passed, facts in clauses
    )


def evaluate_registered_verdict_conditions(
    policy_df: pd.DataFrame,
    evidence_record: VerdictEvidenceRecordV01,
) -> tuple[VerdictConditionEvaluationV01, ...]:
    policy = _validate_registered_verdict_policy(policy_df)
    _validate_verdict_evidence_record(evidence_record)
    evaluations: list[VerdictConditionEvaluationV01] = []
    evaluation_stopped = False
    for row in policy.itertuples(index=False):
        if evaluation_stopped:
            evaluations.extend(
                _condition_evaluation(
                    category_id=row.category_id,
                    clause_id=clause_id,
                    decision_rank=int(row.decision_rank),
                    outcome="NOT_EVALUATED_AFTER_MATCH",
                    facts=(),
                    reason_code="not_evaluated_after_ranked_stop_v01",
                )
                for clause_id in VERDICT_CLAUSE_IDS
            )
            continue
        if row.category_id == "strongly_supported":
            category_evaluations = _evaluate_strongly_supported(evidence_record)
        else:
            category_evaluations = tuple(
                _condition_evaluation(
                    category_id=row.category_id,
                    clause_id=clause_id,
                    decision_rank=int(row.decision_rank),
                    outcome="INDETERMINATE",
                    facts=(),
                    reason_code="qualitative_policy_term_not_operationalized_v01",
                )
                for clause_id in VERDICT_CLAUSE_IDS
            )
        evaluations.extend(category_evaluations)
        outcomes = {item.outcome for item in category_evaluations}
        if outcomes == {"PASS"} or "INDETERMINATE" in outcomes:
            evaluation_stopped = True
    result = tuple(evaluations)
    _validate_condition_evaluations(policy, result)
    return result


def _validate_condition_evaluations(
    policy: pd.DataFrame,
    evaluations: Sequence[VerdictConditionEvaluationV01],
) -> None:
    expected_keys = {
        (row.category_id, clause_id)
        for row in policy.itertuples(index=False)
        for clause_id in VERDICT_CLAUSE_IDS
    }
    actual_keys: list[tuple[str, str]] = []
    rank_by_category = dict(zip(policy["category_id"], policy["decision_rank"]))
    for evaluation in evaluations:
        if not isinstance(evaluation, VerdictConditionEvaluationV01):
            raise ValueError("ST07_35: неизвестный тип condition evaluation")
        if evaluation.policy_id != VERDICT_POLICY_ID or evaluation.claim_id != VERDICT_CLAIM_ID:
            raise ValueError("ST07_35: condition evaluation identity не совпадает")
        key = (evaluation.category_id, evaluation.clause_id)
        actual_keys.append(key)
        if key not in expected_keys:
            raise ValueError("ST07_35: неизвестный ключ condition evaluation")
        if evaluation.decision_rank != int(rank_by_category[evaluation.category_id]):
            raise ValueError("ST07_35: condition evaluation rank не совпадает")
        if evaluation.outcome not in VERDICT_EVALUATION_OUTCOMES:
            raise ValueError("ST07_35: неизвестный outcome condition evaluation")
        _require_nonblank_value(evaluation.evaluator_id, "evaluator_id")
        if evaluation.evaluator_version != VERDICT_EVALUATOR_VERSION:
            raise ValueError("ST07_35: неизвестная версия evaluator")
        _require_nonblank_value(evaluation.reason_code, "reason_code")
    if len(actual_keys) != 30 or len(set(actual_keys)) != 30 or set(actual_keys) != expected_keys:
        raise ValueError("ST07_35: требуется ровно 30 уникальных condition evaluations")


def _evidence_record_sha256(record: VerdictEvidenceRecordV01) -> str:
    payload = json.dumps(
        asdict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _required_disclosures(record: VerdictEvidenceRecordV01) -> tuple[str, ...]:
    disclosures: list[str] = []
    if record.high_training_cost:
        disclosures.append("high_training_cost")
    disclosures.append("miniboone_and_registered_protocol_scope")
    if record.parameter_stability_status == "partially_stable":
        disclosures.append("partial_l2_selection_instability")
    if record.non_nested_comparison_count > 0:
        disclosures.append("non_nested_probe_is_diagnostic_only")
    return tuple(disclosures)


def _derive_verdict_policy_application_result(
    policy: pd.DataFrame,
    evidence_record: VerdictEvidenceRecordV01,
    evaluations: Sequence[VerdictConditionEvaluationV01],
    policy_sha256: str,
) -> VerdictPolicyApplicationResultV01:
    evidence_digest = _evidence_record_sha256(evidence_record)
    disclosure_values = _required_disclosures(evidence_record)
    result_values: dict[str, Any] | None = None
    for row in policy.itertuples(index=False):
        category_evaluations = {
            evaluation.clause_id: evaluation
            for evaluation in evaluations
            if evaluation.category_id == row.category_id
        }
        outcomes = tuple(
            category_evaluations[clause_id].outcome for clause_id in VERDICT_CLAUSE_IDS
        )
        if "INDETERMINATE" in outcomes:
            result_values = {
                "application_status": "INDETERMINATE_FAIL_CLOSED",
                "selected_category_id": None,
                "selected_decision_rank": None,
                "selected_category_ru": None,
                "outcomes": outcomes,
                "allowed_language_ru": None,
                "forbidden_language_ru": None,
                "row_status": "verdict_policy_application_indeterminate_fail_closed",
            }
            break
        if outcomes == ("PASS",) * len(VERDICT_CLAUSE_IDS):
            result_values = {
                "application_status": "APPLIED",
                "selected_category_id": row.category_id,
                "selected_decision_rank": int(row.decision_rank),
                "selected_category_ru": row.category_ru,
                "outcomes": outcomes,
                "allowed_language_ru": row.allowed_language_ru,
                "forbidden_language_ru": row.forbidden_language_ru,
                "row_status": "verdict_policy_application_applied_v01",
            }
            break
        if "NOT_EVALUATED_AFTER_MATCH" in outcomes:
            raise ValueError("ST07_35: ranked application остановлено до причины")
    if result_values is None:
        result_values = {
            "application_status": "NO_CATEGORY_MATCH_FAIL_CLOSED",
            "selected_category_id": None,
            "selected_decision_rank": None,
            "selected_category_ru": None,
            "outcomes": ("FAIL",) * len(VERDICT_CLAUSE_IDS),
            "allowed_language_ru": None,
            "forbidden_language_ru": None,
            "row_status": "verdict_policy_application_no_match_fail_closed",
        }
    outcomes = result_values.pop("outcomes")
    return VerdictPolicyApplicationResultV01(
        application_id=(
            f"miniboone_verdict_application_v01_{evidence_digest[:16]}_"
            f"{policy_sha256[:16]}"
        ),
        policy_id=VERDICT_POLICY_ID,
        claim_id=VERDICT_CLAIM_ID,
        quality_gate_outcome=outcomes[0],
        primary_metric_outcome=outcomes[1],
        secondary_metric_outcome=outcomes[2],
        stability_outcome=outcomes[3],
        cost_outcome=outcomes[4],
        required_disclosures=disclosure_values,
        evidence_record_sha256=evidence_digest,
        policy_sha256=policy_sha256,
        interpretation_limit_ru=(
            "Результат ограничен MiniBooNE, зарегистрированными протоколами и "
            "каноническими evidence ST05_01-ST05_07; универсальное превосходство "
            "модели не утверждается."
        ),
        **result_values,
    )


def apply_registered_verdict_policy(
    policy_df: pd.DataFrame,
    evidence_record: VerdictEvidenceRecordV01,
    condition_evaluations: Sequence[VerdictConditionEvaluationV01],
    *,
    policy_sha256: str,
) -> VerdictPolicyApplicationResultV01:
    policy = _validate_registered_verdict_policy(policy_df)
    _validate_verdict_evidence_record(evidence_record)
    normalized_policy_digest = _require_sha256(policy_sha256, "policy_sha256")
    _validate_condition_evaluations(policy, condition_evaluations)
    expected_evaluations = evaluate_registered_verdict_conditions(
        policy_df, evidence_record
    )
    if tuple(condition_evaluations) != expected_evaluations:
        raise ValueError("ST07_35: condition evaluations не воспроизводятся из evidence")
    return _derive_verdict_policy_application_result(
        policy,
        evidence_record,
        condition_evaluations,
        normalized_policy_digest,
    )


def validate_verdict_policy_application_bundle(
    policy_df: pd.DataFrame,
    evidence_record: VerdictEvidenceRecordV01,
    condition_evaluations: Sequence[VerdictConditionEvaluationV01],
    result: VerdictPolicyApplicationResultV01,
) -> None:
    policy = _validate_registered_verdict_policy(policy_df)
    _validate_verdict_evidence_record(evidence_record)
    _validate_condition_evaluations(policy, condition_evaluations)
    if not isinstance(result, VerdictPolicyApplicationResultV01):
        raise ValueError("ST07_35: неизвестный тип application result")
    if result.application_status not in VERDICT_APPLICATION_STATUSES:
        raise ValueError("ST07_35: неизвестный application_status")
    expected_evaluations = evaluate_registered_verdict_conditions(
        policy_df, evidence_record
    )
    if tuple(condition_evaluations) != expected_evaluations:
        raise ValueError("ST07_35: condition evaluations не воспроизводятся из evidence")
    expected = _derive_verdict_policy_application_result(
        policy,
        evidence_record,
        condition_evaluations,
        _require_sha256(result.policy_sha256, "result.policy_sha256"),
    )
    if result != expected:
        raise ValueError("ST07_35: application result не воспроизводится из bundle")
    selected = result.selected_category_id is not None
    if selected != (result.application_status == "APPLIED"):
        raise ValueError("ST07_35: selected category не согласована со статусом")
