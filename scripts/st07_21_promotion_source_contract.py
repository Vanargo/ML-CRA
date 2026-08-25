from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.io import read_csv_checked, write_csv_checked  # noqa: E402
from mlcra.nested_artifacts import (  # noqa: E402
    ARTIFACT_IDS,
    read_v02_artifacts,
    validate_v02_schema,
)


TASK_ID = (
    "ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract"
)
AUTHORITY = f"NEXT_BLOCK_AUTHORIZED: {TASK_ID}"
PROTOCOL_ID = "miniboone_nested_cv_v02"
MANIFEST_ID = "miniboone_nested_v02_promotion_source_manifest_v01"
SELECTED_SOURCE_LABEL = "run_a"
SOURCE_SELECTION_POLICY = (
    "first_complete_validation_run_in_registered_execution_order"
)
BUNDLE_ATOMICITY = "all_7_artifacts_from_one_run"
TIMING_POLICY = (
    "preserve_selected_run_class_C_exact_no_average_no_minimum_selection"
)
ARTIFACT_CONTEXT = "miniboone_v02_scientific_candidate"
SOURCE_LOCATOR_KIND = "temporary_validation_bundle_relative_locator"
DECISION_STATUS = "selected_source_contract_only_noncanonical_not_promoted"

PROTOCOL_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "openml_miniboone_nested_cv_v02_protocol_lock.csv"
)
SCHEMA_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
)
VALIDATION_EVIDENCE_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "st07_20_nested_cv_v02_provenance_corrected_dual_run_"
    "revalidation_evidence_v01.json"
)
MANIFEST_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "openml_miniboone_nested_v02_promotion_source_manifest_v01.csv"
)
EVIDENCE_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "st07_21_nested_cv_v02_promotion_source_and_timing_"
    "provenance_contract_evidence_v01.json"
)
VALIDATION_EVIDENCE_SHA256 = (
    "abb7b31036ea0c44a48590d3cb260be8a9c7d02196fa5f1a78ca32d6fa7e04f9"
)
PROTECTED_CONTRACT_HASHES = {
    "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
        "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
    ),
    "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
        "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
    ),
    (
        "data_registry/st07_20_nested_cv_v02_provenance_corrected_dual_run_"
        "revalidation_evidence_v01.json"
    ): VALIDATION_EVIDENCE_SHA256,
}

MANIFEST_COLUMNS = [
    "promotion_source_manifest_id",
    "protocol_id",
    "validation_task_id",
    "validation_evidence_path",
    "validation_evidence_sha256",
    "source_selection_policy",
    "selected_source_label",
    "selected_source_pid",
    "execution_order_position",
    "bundle_atomicity",
    "selected_bundle_sha256",
    "artifact_context",
    "timing_policy",
    "artifact_id",
    "source_locator_kind",
    "source_relative_locator",
    "source_filename",
    "source_sha256",
    "source_rows",
    "source_columns",
    "canonical_path",
    "source_available_at_contract_creation",
    "canonical_target_absent_at_contract_creation",
    "decision_status",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bundle_sha256(records: dict[str, dict[str, Any]]) -> str:
    payload = "\n".join(
        f"{artifact_id}:{records[artifact_id]['sha256']}"
        for artifact_id in ARTIFACT_IDS
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_validation_evidence() -> dict[str, Any]:
    if sha256_file(VALIDATION_EVIDENCE_PATH) != VALIDATION_EVIDENCE_SHA256:
        raise ValueError("SHA-256 evidence ST07_20 не совпадает с зарегистрированным")
    evidence = json.loads(VALIDATION_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if evidence.get("task_id") != (
        "ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation"
    ):
        raise ValueError("Неверный task_id evidence ST07_20")
    if evidence.get("technical_status") != "PASS":
        raise ValueError("Evidence ST07_20 не имеет technical_status=PASS")
    if evidence.get("validation_run_count") != 2:
        raise ValueError("Evidence ST07_20 должен содержать ровно два run")
    if evidence.get("candidate_artifacts_promoted") != 0:
        raise ValueError("Evidence ST07_20 сообщает о promotion")
    if not evidence.get("canonical_outputs_absent_after"):
        raise ValueError("Evidence ST07_20 не подтверждает отсутствие canonical outputs")
    if not all(evidence.get("checks", {}).values()):
        raise ValueError("Не все checks ST07_20 имеют PASS")
    if tuple(evidence.get("artifact_records", {})) != ("run_a", "run_b"):
        raise ValueError("Порядок run_a/run_b в evidence ST07_20 нарушен")
    processes = evidence.get("process_records", [])
    if [record.get("label") for record in processes] != ["run_a", "run_b"]:
        raise ValueError("Порядок process records ST07_20 нарушен")
    for record in processes:
        result = record.get("runner_result", {})
        if record.get("return_code") != 0 or result.get("status") != "pass":
            raise ValueError("Один из процессов ST07_20 не завершился успешно")
        if result.get("artifact_context") != ARTIFACT_CONTEXT:
            raise ValueError("Неверный artifact_context процесса ST07_20")
        if result.get("promotion_performed") or result.get("network_used"):
            raise ValueError("ST07_20 нарушил no-promotion/offline boundary")
    return evidence


def canonical_paths(schema: pd.DataFrame) -> dict[str, str]:
    result: dict[str, str] = {}
    for artifact_id in ARTIFACT_IDS:
        values = schema.loc[
            schema["artifact_id"].eq(artifact_id), "canonical_path"
        ].drop_duplicates()
        if len(values) != 1:
            raise ValueError(f"Неоднозначный canonical_path для {artifact_id}")
        result[artifact_id] = str(values.iloc[0])
    return result


def require_canonical_outputs_absent(schema: pd.DataFrame) -> None:
    present = [
        relative
        for relative in canonical_paths(schema).values()
        if (PROJECT_ROOT / relative).exists()
    ]
    if present:
        raise ValueError(f"Canonical v02 outputs уже существуют: {present}")


def observe_bundle(
    work_root: Path,
    label: str,
    schema: pd.DataFrame,
    expected_records: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    source_dir = work_root / label
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Временный source bundle не найден: {label}")
    artifacts = read_v02_artifacts(source_dir, schema)
    expected_names = {
        str(expected_records[artifact_id]["filename"])
        for artifact_id in ARTIFACT_IDS
    }
    actual_names = {path.name for path in source_dir.iterdir() if path.is_file()}
    if actual_names != expected_names:
        raise ValueError(
            f"Набор файлов {label} не равен зарегистрированным 7 artifacts"
        )
    observed: dict[str, dict[str, Any]] = {}
    for artifact_id, frame in artifacts.as_dict().items():
        expected = expected_records[artifact_id]
        source_path = source_dir / str(expected["filename"])
        record = {
            "filename": source_path.name,
            "sha256": sha256_file(source_path),
            "rows": len(frame),
            "columns": len(frame.columns),
        }
        if record != expected:
            raise ValueError(
                f"Observed record {label}/{artifact_id} не совпадает с ST07_20"
            )
        observed[artifact_id] = record
    return observed


def build_manifest(
    evidence: dict[str, Any], schema: pd.DataFrame
) -> pd.DataFrame:
    selected_records = evidence["artifact_records"][SELECTED_SOURCE_LABEL]
    selected_process = evidence["process_records"][0]
    selected_pid = selected_process["runner_result"]["pid"]
    bundle_hash = bundle_sha256(selected_records)
    targets = canonical_paths(schema)
    rows = []
    for artifact_id in ARTIFACT_IDS:
        record = selected_records[artifact_id]
        rows.append(
            {
                "promotion_source_manifest_id": MANIFEST_ID,
                "protocol_id": PROTOCOL_ID,
                "validation_task_id": evidence["task_id"],
                "validation_evidence_path": VALIDATION_EVIDENCE_PATH.relative_to(
                    PROJECT_ROOT
                ).as_posix(),
                "validation_evidence_sha256": VALIDATION_EVIDENCE_SHA256,
                "source_selection_policy": SOURCE_SELECTION_POLICY,
                "selected_source_label": SELECTED_SOURCE_LABEL,
                "selected_source_pid": str(selected_pid),
                "execution_order_position": "1",
                "bundle_atomicity": BUNDLE_ATOMICITY,
                "selected_bundle_sha256": bundle_hash,
                "artifact_context": ARTIFACT_CONTEXT,
                "timing_policy": TIMING_POLICY,
                "artifact_id": artifact_id,
                "source_locator_kind": SOURCE_LOCATOR_KIND,
                "source_relative_locator": f"{SELECTED_SOURCE_LABEL}/{record['filename']}",
                "source_filename": record["filename"],
                "source_sha256": record["sha256"],
                "source_rows": str(record["rows"]),
                "source_columns": str(record["columns"]),
                "canonical_path": targets[artifact_id],
                "source_available_at_contract_creation": "yes",
                "canonical_target_absent_at_contract_creation": "yes",
                "decision_status": DECISION_STATUS,
            }
        )
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)


def _require_constant(frame: pd.DataFrame, column: str, value: str) -> None:
    if not frame[column].eq(value).all():
        raise ValueError(f"Нарушено постоянное поле {column}")


def validate_manifest(
    frame: pd.DataFrame,
    evidence: dict[str, Any],
    schema: pd.DataFrame,
) -> dict[str, Any]:
    validate_v02_schema(schema)
    if list(frame.columns) != MANIFEST_COLUMNS:
        raise ValueError("Столбцы source manifest не совпадают с контрактом")
    if len(frame) != len(ARTIFACT_IDS):
        raise ValueError("Source manifest должен иметь ровно 7 строк")
    if tuple(frame["artifact_id"]) != ARTIFACT_IDS:
        raise ValueError("Порядок или множество artifact_id нарушены")
    if frame["artifact_id"].duplicated().any():
        raise ValueError("Source manifest содержит duplicate artifact_id")

    constants = {
        "promotion_source_manifest_id": MANIFEST_ID,
        "protocol_id": PROTOCOL_ID,
        "validation_task_id": evidence["task_id"],
        "validation_evidence_path": VALIDATION_EVIDENCE_PATH.relative_to(
            PROJECT_ROOT
        ).as_posix(),
        "validation_evidence_sha256": VALIDATION_EVIDENCE_SHA256,
        "source_selection_policy": SOURCE_SELECTION_POLICY,
        "selected_source_label": SELECTED_SOURCE_LABEL,
        "selected_source_pid": str(
            evidence["process_records"][0]["runner_result"]["pid"]
        ),
        "execution_order_position": "1",
        "bundle_atomicity": BUNDLE_ATOMICITY,
        "selected_bundle_sha256": bundle_sha256(
            evidence["artifact_records"][SELECTED_SOURCE_LABEL]
        ),
        "artifact_context": ARTIFACT_CONTEXT,
        "timing_policy": TIMING_POLICY,
        "source_locator_kind": SOURCE_LOCATOR_KIND,
        "source_available_at_contract_creation": "yes",
        "canonical_target_absent_at_contract_creation": "yes",
        "decision_status": DECISION_STATUS,
    }
    for column, value in constants.items():
        _require_constant(frame, column, value)

    selected = evidence["artifact_records"][SELECTED_SOURCE_LABEL]
    targets = canonical_paths(schema)
    for row in frame.to_dict(orient="records"):
        artifact_id = row["artifact_id"]
        record = selected[artifact_id]
        exact = {
            "source_relative_locator": (
                f"{SELECTED_SOURCE_LABEL}/{record['filename']}"
            ),
            "source_filename": str(record["filename"]),
            "source_sha256": str(record["sha256"]),
            "source_rows": str(record["rows"]),
            "source_columns": str(record["columns"]),
            "canonical_path": targets[artifact_id],
        }
        for column, value in exact.items():
            if str(row[column]) != value:
                raise ValueError(f"Неверное поле {column} для {artifact_id}")
    return {
        "row_count": len(frame),
        "artifact_count": len(ARTIFACT_IDS),
        "selected_source_label": SELECTED_SOURCE_LABEL,
        "selected_bundle_sha256": constants["selected_bundle_sha256"],
        "class_C_column_count": int(schema["comparison_class"].eq("C").sum()),
        "status": "pass",
    }


def run_negative_tests(
    valid: pd.DataFrame,
    evidence: dict[str, Any],
    schema: pd.DataFrame,
) -> dict[str, bool]:
    mutations: dict[str, Callable[[pd.DataFrame], None]] = {
        "missing_artifact_row": lambda frame: frame.drop(frame.index[-1], inplace=True),
        "duplicate_artifact_id": lambda frame: frame.__setitem__(
            "artifact_id",
            list(frame["artifact_id"][:-1]) + [frame["artifact_id"].iloc[0]],
        ),
        "mixed_source_hash": lambda frame: frame.__setitem__(
            "source_sha256",
            frame["source_sha256"].where(
                ~frame["artifact_id"].eq("outer_scores"),
                evidence["artifact_records"]["run_b"]["outer_scores"]["sha256"],
            ),
        ),
        "wrong_source_label": lambda frame: frame.__setitem__(
            "selected_source_label", "run_b"
        ),
        "wrong_source_pid": lambda frame: frame.__setitem__(
            "selected_source_pid", "12556"
        ),
        "wrong_execution_order": lambda frame: frame.__setitem__(
            "execution_order_position", "2"
        ),
        "result_driven_timing_policy": lambda frame: frame.__setitem__(
            "timing_policy", "minimum_observed_timing"
        ),
        "wrong_canonical_target": lambda frame: frame.__setitem__(
            "canonical_path",
            frame["canonical_path"].where(
                ~frame["artifact_id"].eq("summary"),
                "data_registry/wrong.csv",
            ),
        ),
        "wrong_validation_evidence_sha": lambda frame: frame.__setitem__(
            "validation_evidence_sha256", "0" * 64
        ),
        "source_not_observed": lambda frame: frame.__setitem__(
            "source_available_at_contract_creation", "no"
        ),
    }
    results: dict[str, bool] = {}
    for name, mutate in mutations.items():
        candidate = valid.copy(deep=True)
        mutate(candidate)
        try:
            validate_manifest(candidate, evidence, schema)
        except (KeyError, TypeError, ValueError):
            results[name] = True
        else:
            results[name] = False
    if not all(results.values()):
        raise ValueError(f"Не все negative tests fail-closed: {results}")
    return results


def protected_hashes_exact() -> bool:
    return all(
        sha256_file(PROJECT_ROOT / relative_path) == expected
        for relative_path, expected in PROTECTED_CONTRACT_HASHES.items()
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register the ST07_21 atomic promotion-source contract."
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        required=True,
        help="Existing ST07_20 temporary root containing run_a and run_b.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    work_root = args.work_root.resolve()
    if MANIFEST_PATH.exists() or EVIDENCE_PATH.exists():
        raise FileExistsError("ST07_21 outputs already exist; overwrite is forbidden")
    if not protected_hashes_exact():
        raise ValueError("Protected protocol/schema/ST07_20 evidence hash mismatch")

    evidence = load_validation_evidence()
    schema = read_csv_checked(SCHEMA_PATH)
    validate_v02_schema(schema)
    require_canonical_outputs_absent(schema)

    observed = {
        label: observe_bundle(
            work_root,
            label,
            schema,
            evidence["artifact_records"][label],
        )
        for label in ("run_a", "run_b")
    }
    manifest = build_manifest(evidence, schema)
    manifest_validation = validate_manifest(manifest, evidence, schema)
    negative_tests = run_negative_tests(manifest, evidence, schema)
    require_canonical_outputs_absent(schema)

    write_csv_checked(manifest, MANIFEST_PATH)
    manifest_sha = sha256_file(MANIFEST_PATH)
    evidence_record = {
        "evidence_schema_version": "st07_21_evidence_v01",
        "task_id": TASK_ID,
        "task_profile": "CHANGE",
        "authority": AUTHORITY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_id": PROTOCOL_ID,
        "validation_evidence_path": VALIDATION_EVIDENCE_PATH.relative_to(
            PROJECT_ROOT
        ).as_posix(),
        "validation_evidence_sha256": VALIDATION_EVIDENCE_SHA256,
        "source_selection_policy": SOURCE_SELECTION_POLICY,
        "selected_source_label": SELECTED_SOURCE_LABEL,
        "selected_source_pid": int(
            evidence["process_records"][0]["runner_result"]["pid"]
        ),
        "execution_order_position": 1,
        "bundle_atomicity": BUNDLE_ATOMICITY,
        "selected_bundle_sha256": manifest_validation["selected_bundle_sha256"],
        "artifact_context": ARTIFACT_CONTEXT,
        "timing_policy": TIMING_POLICY,
        "timing_class_C_column_count": manifest_validation[
            "class_C_column_count"
        ],
        "promotion_source_manifest_path": MANIFEST_PATH.relative_to(
            PROJECT_ROOT
        ).as_posix(),
        "promotion_source_manifest_sha256": manifest_sha,
        "promotion_source_manifest_rows": len(manifest),
        "source_locator_base": "<temporary_work_root>",
        "temporary_source_persisted_in_checkpoint": False,
        "observed_artifact_records": observed,
        "canonical_output_count": len(ARTIFACT_IDS),
        "canonical_outputs_absent_before": True,
        "canonical_outputs_absent_after": True,
        "candidate_artifacts_copied": 0,
        "candidate_artifacts_promoted": 0,
        "training_performed": False,
        "network_used": False,
        "stage05_claim_or_verdict_changed": False,
        "protected_contract_hashes": PROTECTED_CONTRACT_HASHES,
        "checks": {
            "st07_20_evidence_pass_and_exact_hash": True,
            "both_temporary_bundles_available_and_14_hashes_exact": True,
            "both_bundles_schema_and_row_policies_valid": True,
            "source_selected_by_registered_order_not_results": True,
            "selected_source_is_atomic_run_a_7_of_7": True,
            "class_C_timing_preserved_exact_from_selected_source": True,
            "no_average_or_minimum_timing_selection": True,
            "canonical_v02_outputs_absent": True,
            "promotion_and_copy_not_performed": True,
            "training_and_network_not_performed": True,
            "protected_contract_hashes_exact": True,
            "negative_mutations_fail_closed": True,
            "claim_or_verdict_change_none": True,
        },
        "negative_tests": negative_tests,
        "planned_change_set": [
            "docs/agent/st07_21_nested_cv_v02_promotion_source_and_timing_provenance_change_scope_v01.csv",
            "scripts/st07_21_promotion_source_contract.py",
            "data_registry/openml_miniboone_nested_v02_promotion_source_manifest_v01.csv",
            "data_registry/st07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ],
        "scientific_interpretation": (
            "promotion_source_and_timing_provenance_contract_only; "
            "not_promotion; not_new_training; not_cross_environment_reproducibility; "
            "not_universal_model_superiority; not_stage05_claim_support"
        ),
        "technical_status": "PASS",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
    }
    EVIDENCE_PATH.write_text(
        json.dumps(evidence_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    persisted = read_csv_checked(MANIFEST_PATH)
    validate_manifest(persisted, evidence, schema)
    if not all(evidence_record["checks"].values()):
        raise ValueError("Evidence ST07_21 содержит непрошедший check")
    if not protected_hashes_exact():
        raise ValueError("Protected files изменились во время ST07_21")
    require_canonical_outputs_absent(schema)

    print(
        json.dumps(
            {
                "status": "pass",
                "task_id": TASK_ID,
                "selected_source_label": SELECTED_SOURCE_LABEL,
                "artifact_count": len(manifest),
                "negative_tests_passed": sum(negative_tests.values()),
                "canonical_outputs_created": 0,
                "candidate_artifacts_promoted": 0,
                "training_performed": False,
                "network_used": False,
                "manifest_sha256": manifest_sha,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
