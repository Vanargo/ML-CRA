from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.nested_artifacts import (  # noqa: E402
    ARTIFACT_IDS,
    read_v02_artifacts,
    validate_v02_schema,
)
from st07_21_promotion_source_contract import (  # noqa: E402
    SELECTED_SOURCE_LABEL,
    load_validation_evidence,
    observe_bundle,
    validate_manifest,
)


TASK_ID = (
    "ST07_22_nested_cv_v02_transactional_promotion_and_"
    "canonical_artifact_registration"
)
AUTHORITY = f"NEXT_BLOCK_AUTHORIZED: {TASK_ID}"
PROTOCOL_ID = "miniboone_nested_cv_v02"
SOURCE_CHECKPOINT_SHA256 = (
    "ff44a49a11b7c2c2cc395242b8a1c6ccab79bdee29221ccaa0b807ed3d9764cf"
)
DATA_REGISTRY = PROJECT_ROOT / "data_registry"
PROTOCOL_PATH = (
    DATA_REGISTRY / "openml_miniboone_nested_cv_v02_protocol_lock.csv"
)
SCHEMA_PATH = (
    DATA_REGISTRY / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
)
ST07_20_EVIDENCE_PATH = (
    DATA_REGISTRY
    / "st07_20_nested_cv_v02_provenance_corrected_dual_run_"
    "revalidation_evidence_v01.json"
)
SOURCE_MANIFEST_PATH = (
    DATA_REGISTRY / "openml_miniboone_nested_v02_promotion_source_manifest_v01.csv"
)
ST07_21_EVIDENCE_PATH = (
    DATA_REGISTRY
    / "st07_21_nested_cv_v02_promotion_source_and_timing_"
    "provenance_contract_evidence_v01.json"
)
JOURNAL_PATH = (
    DATA_REGISTRY
    / "st07_22_nested_cv_v02_promotion_transaction_journal_v01.json"
)
EVIDENCE_PATH = (
    DATA_REGISTRY
    / "st07_22_nested_cv_v02_transactional_promotion_and_"
    "canonical_artifact_registration_evidence_v01.json"
)
LOCK_PATH = DATA_REGISTRY / ".st07_22_promotion.lock"
PROTECTED_HASHES = {
    PROTOCOL_PATH.relative_to(PROJECT_ROOT).as_posix(): (
        "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
    ),
    SCHEMA_PATH.relative_to(PROJECT_ROOT).as_posix(): (
        "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
    ),
    ST07_20_EVIDENCE_PATH.relative_to(PROJECT_ROOT).as_posix(): (
        "abb7b31036ea0c44a48590d3cb260be8a9c7d02196fa5f1a78ca32d6fa7e04f9"
    ),
    SOURCE_MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(): (
        "aa823a37bb4287d6668489261c7486e3ecd70a0845a7b20f8e59e46e90a4b465"
    ),
    ST07_21_EVIDENCE_PATH.relative_to(PROJECT_ROOT).as_posix(): (
        "baf6ab25138f5acf1f28a6111f4785769f6cd9c65910583b2bf467bf8f7eb9c0"
    ),
}
PLANNED_CHANGE_SET = [
    "docs/agent/st07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration_change_scope_v01.csv",
    "scripts/st07_22_transactional_promotion.py",
    "data_registry/openml_miniboone_nested_v02_outer_scores.csv",
    "data_registry/openml_miniboone_nested_v02_selected_params.csv",
    "data_registry/openml_miniboone_nested_v02_summary.csv",
    "data_registry/openml_miniboone_nested_v02_quality_checks.csv",
    "data_registry/openml_miniboone_nested_v02_warnings.csv",
    "data_registry/openml_miniboone_nested_v02_environment.csv",
    "data_registry/openml_miniboone_nested_v02_numeric_runtime.csv",
    "data_registry/st07_22_nested_cv_v02_promotion_transaction_journal_v01.json",
    "data_registry/st07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration_evidence_v01.json",
    "scripts/agent_verify.py",
    "docs/stages/stage_07_code_modularization.md",
    "roadmap.md",
]


class PromotionError(RuntimeError):
    """Base class for fail-closed ST07_22 errors."""


class PromotionRolledBack(PromotionError):
    """A commit failed and all transaction-created targets were removed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_hashes_exact() -> bool:
    return all(
        (PROJECT_ROOT / relative).is_file()
        and sha256_file(PROJECT_ROOT / relative) == expected
        for relative, expected in PROTECTED_HASHES.items()
    )


def write_bytes_fsync(path: Path, payload: bytes, *, exclusive: bool) -> None:
    mode = "xb" if exclusive else "wb"
    with path.open(mode) as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json_new(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"Overwrite запрещён: {path}")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"Временный JSON уже существует: {temporary}")
    try:
        write_bytes_fsync(temporary, _json_bytes(payload), exclusive=True)
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def replace_json_owned(path: Path, payload: dict[str, Any]) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Собственный journal отсутствует: {path}")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"Временный journal уже существует: {temporary}")
    try:
        write_bytes_fsync(temporary, _json_bytes(payload), exclusive=True)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def exclusive_lock(lock_path: Path, transaction_id: str) -> Iterator[None]:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        )
        payload = (
            json.dumps(
                {
                    "task_id": TASK_ID,
                    "transaction_id": transaction_id,
                    "pid": os.getpid(),
                    "acquired_at_utc": utc_now(),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        os.write(descriptor, payload)
        os.fsync(descriptor)
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
            if lock_path.exists():
                lock_path.unlink()


def canonical_records(manifest: pd.DataFrame) -> list[dict[str, str]]:
    records = manifest.to_dict(orient="records")
    if [record["artifact_id"] for record in records] != list(ARTIFACT_IDS):
        raise ValueError("Manifest artifact order не совпадает с ARTIFACT_IDS")
    return records


def require_targets_absent(
    records: Sequence[dict[str, str]],
    *,
    project_root: Path,
) -> None:
    present = [
        record["canonical_path"]
        for record in records
        if (project_root / record["canonical_path"]).exists()
    ]
    if present:
        raise FileExistsError(f"Canonical targets уже существуют: {present}")


def validate_file_records(
    root: Path,
    records: Sequence[dict[str, str]],
    *,
    relative_field: str,
    hash_field: str,
) -> dict[str, str]:
    observed: dict[str, str] = {}
    for record in records:
        path = root / record[relative_field]
        if not path.is_file():
            raise FileNotFoundError(f"Обязательный файл отсутствует: {path}")
        digest = sha256_file(path)
        if digest != record[hash_field]:
            raise ValueError(f"SHA-256 mismatch: {path}")
        observed[record["artifact_id"]] = digest
    return observed


def validate_st07_21_evidence(
    evidence: dict[str, Any], manifest_sha256: str
) -> None:
    if evidence.get("task_id") != (
        "ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract"
    ):
        raise ValueError("Неверный task_id evidence ST07_21")
    if evidence.get("technical_status") != "PASS":
        raise ValueError("Evidence ST07_21 не имеет technical_status=PASS")
    if evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE":
        raise ValueError("Evidence ST07_21 не готово к принятию")
    if evidence.get("selected_source_label") != SELECTED_SOURCE_LABEL:
        raise ValueError("Evidence ST07_21 выбрало не run_a")
    if evidence.get("promotion_source_manifest_rows") != len(ARTIFACT_IDS):
        raise ValueError("Evidence ST07_21 сообщает неверное число manifest rows")
    if evidence.get("promotion_source_manifest_sha256") != manifest_sha256:
        raise ValueError("Evidence ST07_21 не связано с точным source manifest")
    if evidence.get("candidate_artifacts_copied") != 0:
        raise ValueError("Evidence ST07_21 сообщает о преждевременном copy")
    if evidence.get("candidate_artifacts_promoted") != 0:
        raise ValueError("Evidence ST07_21 сообщает о преждевременном promotion")
    if not evidence.get("canonical_outputs_absent_after"):
        raise ValueError("Evidence ST07_21 не подтверждает canonical absence")
    if not all(evidence.get("checks", {}).values()):
        raise ValueError("Evidence ST07_21 содержит непрошедший check")


def load_registered_inputs(
    source_root: Path,
    source_checkpoint: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, str]], dict[str, Any]]:
    if not source_checkpoint.is_file():
        raise FileNotFoundError(f"Source checkpoint не найден: {source_checkpoint}")
    if sha256_file(source_checkpoint) != SOURCE_CHECKPOINT_SHA256:
        raise ValueError("SHA-256 source checkpoint v34 не совпадает")
    if not protected_hashes_exact():
        raise ValueError("Один или несколько защищённых SHA-256 изменились")

    schema = read_csv_checked(SCHEMA_PATH)
    validate_v02_schema(schema)
    validation_evidence = load_validation_evidence()
    manifest = read_csv_checked(SOURCE_MANIFEST_PATH)
    validate_manifest(manifest, validation_evidence, schema)
    manifest_sha = sha256_file(SOURCE_MANIFEST_PATH)
    st07_21_evidence = json.loads(
        ST07_21_EVIDENCE_PATH.read_text(encoding="utf-8")
    )
    validate_st07_21_evidence(st07_21_evidence, manifest_sha)
    records = canonical_records(manifest)
    require_targets_absent(records, project_root=PROJECT_ROOT)

    observed = observe_bundle(
        source_root,
        SELECTED_SOURCE_LABEL,
        schema,
        validation_evidence["artifact_records"][SELECTED_SOURCE_LABEL],
    )
    source_dir = source_root / SELECTED_SOURCE_LABEL
    validate_file_records(
        source_dir,
        records,
        relative_field="source_filename",
        hash_field="source_sha256",
    )
    return schema, manifest, records, observed


def copy_file_fsync(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(f"Staging overwrite запрещён: {target}")
    with source.open("rb") as input_stream, target.open("xb") as output_stream:
        shutil.copyfileobj(input_stream, output_stream, length=1024 * 1024)
        output_stream.flush()
        os.fsync(output_stream.fileno())


def prepare_staging(
    source_root: Path,
    staging_dir: Path,
    records: Sequence[dict[str, str]],
    schema: pd.DataFrame,
) -> dict[str, str]:
    if staging_dir.exists():
        raise FileExistsError(f"Staging directory уже существует: {staging_dir}")
    staging_dir.mkdir()
    if os.stat(staging_dir).st_dev != os.stat(DATA_REGISTRY).st_dev:
        raise OSError("Staging и canonical directory находятся не на одном device")
    source_dir = source_root / SELECTED_SOURCE_LABEL
    for record in records:
        copy_file_fsync(
            source_dir / record["source_filename"],
            staging_dir / record["source_filename"],
        )
    observed = validate_file_records(
        staging_dir,
        records,
        relative_field="source_filename",
        hash_field="source_sha256",
    )
    read_v02_artifacts(staging_dir, schema)
    return observed


def rollback_created_targets(
    created: Sequence[tuple[Path, str]],
) -> list[str]:
    errors: list[str] = []
    for target, expected_hash in reversed(created):
        try:
            if not target.exists():
                continue
            if not target.is_file() or sha256_file(target) != expected_hash:
                errors.append(f"refused_to_delete_changed_target:{target}")
                continue
            target.unlink()
        except OSError as error:
            errors.append(f"{type(error).__name__}:{target}:{error}")
    return errors


def commit_staged_links(
    staging_dir: Path,
    records: Sequence[dict[str, str]],
    *,
    project_root: Path,
    on_progress: Callable[[list[str]], None] | None = None,
    inject_failure_after: int | None = None,
) -> list[tuple[Path, str]]:
    created: list[tuple[Path, str]] = []
    try:
        for record in records:
            staged = staging_dir / record["source_filename"]
            target = project_root / record["canonical_path"]
            if target.exists():
                raise FileExistsError(f"Canonical overwrite запрещён: {target}")
            os.link(staged, target)
            expected_hash = record["source_sha256"]
            created.append((target, expected_hash))
            if sha256_file(target) != expected_hash:
                raise ValueError(f"Post-link SHA-256 mismatch: {target}")
            if on_progress is not None:
                on_progress(
                    [path.relative_to(project_root).as_posix() for path, _ in created]
                )
            if inject_failure_after == len(created):
                raise RuntimeError("injected_commit_failure")
        return created
    except Exception as error:
        rollback_errors = rollback_created_targets(created)
        if rollback_errors:
            raise PromotionError(
                f"Commit failed and rollback is incomplete: {rollback_errors}"
            ) from error
        raise PromotionRolledBack(
            f"Commit failed; transaction-created targets rolled back: {error}"
        ) from error


def cleanup_staging(staging_dir: Path) -> None:
    if not staging_dir.exists():
        return
    for path in staging_dir.iterdir():
        if not path.is_file():
            raise PromotionError(f"Unexpected non-file in staging: {path}")
        path.unlink()
    staging_dir.rmdir()


def _expect_failure(action: Callable[[], Any]) -> bool:
    try:
        action()
    except (FileExistsError, FileNotFoundError, PromotionError, ValueError):
        return True
    return False


def _fixture_records(payloads: dict[str, bytes]) -> list[dict[str, str]]:
    return [
        {
            "artifact_id": name,
            "source_filename": f"{name}.csv",
            "source_sha256": hashlib.sha256(payload).hexdigest(),
            "canonical_path": f"targets/{name}.csv",
        }
        for name, payload in payloads.items()
    ]


def run_negative_tests() -> dict[str, bool]:
    results: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(
        prefix=".st07_22_negative_", dir=PROJECT_ROOT
    ) as temporary_name:
        root = Path(temporary_name)
        source = root / "source"
        staging = root / "staging"
        targets = root / "targets"
        source.mkdir()
        staging.mkdir()
        targets.mkdir()
        payloads = {"a": b"a,b\n1,2\n", "b": b"a,b\n3,4\n"}
        records = _fixture_records(payloads)
        for name, payload in payloads.items():
            (source / f"{name}.csv").write_bytes(payload)
            (staging / f"{name}.csv").write_bytes(payload)

        missing_root = root / "missing"
        missing_root.mkdir()
        (missing_root / "a.csv").write_bytes(payloads["a"])
        results["missing_source"] = _expect_failure(
            lambda: validate_file_records(
                missing_root,
                records,
                relative_field="source_filename",
                hash_field="source_sha256",
            )
        )

        mismatch_root = root / "hash_mismatch"
        mismatch_root.mkdir()
        (mismatch_root / "a.csv").write_bytes(payloads["a"])
        (mismatch_root / "b.csv").write_bytes(b"changed")
        results["source_hash_mismatch"] = _expect_failure(
            lambda: validate_file_records(
                mismatch_root,
                records,
                relative_field="source_filename",
                hash_field="source_sha256",
            )
        )

        mixed_root = root / "mixed_bundle"
        mixed_root.mkdir()
        (mixed_root / "a.csv").write_bytes(payloads["a"])
        (mixed_root / "b.csv").write_bytes(payloads["a"])
        results["mixed_bundle"] = _expect_failure(
            lambda: validate_file_records(
                mixed_root,
                records,
                relative_field="source_filename",
                hash_field="source_sha256",
            )
        )

        (targets / "a.csv").write_bytes(b"preexisting")
        results["preexisting_target"] = _expect_failure(
            lambda: commit_staged_links(staging, records, project_root=root)
        ) and (targets / "a.csv").read_bytes() == b"preexisting"
        (targets / "a.csv").unlink()

        (staging / "b.csv").write_bytes(b"staging_changed")
        results["staging_hash_mismatch"] = _expect_failure(
            lambda: validate_file_records(
                staging,
                records,
                relative_field="source_filename",
                hash_field="source_sha256",
            )
        )
        (staging / "b.csv").write_bytes(payloads["b"])

        lock = root / "promotion.lock"
        with exclusive_lock(lock, "negative_outer"):
            results["concurrent_lock"] = _expect_failure(
                lambda: exclusive_lock(lock, "negative_inner").__enter__()
            )

        results["injected_partial_commit_rollback"] = _expect_failure(
            lambda: commit_staged_links(
                staging,
                records,
                project_root=root,
                inject_failure_after=1,
            )
        ) and not any(targets.iterdir())

        (targets / "b.csv").write_bytes(b"foreign_partial")
        results["partial_canonical_state"] = _expect_failure(
            lambda: commit_staged_links(staging, records, project_root=root)
        ) and not (targets / "a.csv").exists()
        (targets / "b.csv").unlink()

        valid_evidence = json.loads(
            ST07_21_EVIDENCE_PATH.read_text(encoding="utf-8")
        )
        invalid_evidence = dict(valid_evidence)
        invalid_evidence["promotion_source_manifest_sha256"] = "0" * 64
        results["evidence_manifest_mismatch"] = _expect_failure(
            lambda: validate_st07_21_evidence(
                invalid_evidence, sha256_file(SOURCE_MANIFEST_PATH)
            )
        )

        results["lock_cleanup"] = not lock.exists()

    if not all(results.values()):
        raise PromotionError(f"Negative tests failed: {results}")
    return results


def build_journal(
    transaction_id: str,
    staging_dir: Path,
    records: Sequence[dict[str, str]],
) -> dict[str, Any]:
    return {
        "journal_schema_version": "st07_22_transaction_journal_v01",
        "task_id": TASK_ID,
        "authority": AUTHORITY,
        "transaction_id": transaction_id,
        "protocol_id": PROTOCOL_ID,
        "selected_source_label": SELECTED_SOURCE_LABEL,
        "commit_method": "os.link_no_overwrite_same_filesystem",
        "commit_protocol": "prepare_validate_lock_commit_verify_or_rollback",
        "state": "prepare",
        "terminal": False,
        "created_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
        "staging_locator": f"<data_registry>/{staging_dir.name}",
        "canonical_paths": [record["canonical_path"] for record in records],
        "committed_paths": [],
        "rollback_errors": [],
        "evidence_path": EVIDENCE_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "evidence_sha256": None,
        "events": [{"phase": "prepare", "at_utc": utc_now()}],
    }


def update_journal(
    journal: dict[str, Any],
    state: str,
    *,
    committed_paths: list[str] | None = None,
    terminal: bool = False,
    details: dict[str, Any] | None = None,
) -> None:
    journal["state"] = state
    journal["terminal"] = terminal
    journal["updated_at_utc"] = utc_now()
    if committed_paths is not None:
        journal["committed_paths"] = list(committed_paths)
    event: dict[str, Any] = {"phase": state, "at_utc": utc_now()}
    if details:
        event.update(details)
    journal["events"].append(event)
    replace_json_owned(JOURNAL_PATH, journal)


def canonical_hashes_exact(
    records: Sequence[dict[str, str]],
) -> dict[str, str]:
    return validate_file_records(
        PROJECT_ROOT,
        records,
        relative_field="canonical_path",
        hash_field="source_sha256",
    )


def build_evidence(
    *,
    source_checkpoint: Path,
    transaction_id: str,
    records: Sequence[dict[str, str]],
    source_observed: dict[str, Any],
    staging_observed: dict[str, str],
    canonical_observed: dict[str, str],
    negative_tests: dict[str, bool],
) -> dict[str, Any]:
    return {
        "evidence_schema_version": "st07_22_evidence_v01",
        "task_id": TASK_ID,
        "task_profile": "CHANGE",
        "authority": AUTHORITY,
        "created_at_utc": utc_now(),
        "technical_status": "PASS",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        "source_checkpoint": source_checkpoint.name,
        "source_checkpoint_sha256": SOURCE_CHECKPOINT_SHA256,
        "protocol_id": PROTOCOL_ID,
        "transaction_id": transaction_id,
        "selected_source_label": SELECTED_SOURCE_LABEL,
        "selected_bundle_sha256": records[0]["selected_bundle_sha256"],
        "source_manifest_path": SOURCE_MANIFEST_PATH.relative_to(
            PROJECT_ROOT
        ).as_posix(),
        "source_manifest_sha256": sha256_file(SOURCE_MANIFEST_PATH),
        "transaction_journal_path": JOURNAL_PATH.relative_to(
            PROJECT_ROOT
        ).as_posix(),
        "commit_method": "os.link_no_overwrite_same_filesystem",
        "commit_protocol": "prepare_validate_lock_commit_verify_or_rollback",
        "bundle_atomicity_claim": (
            "transactional_7_file_bundle_not_single_filesystem_atomic_operation"
        ),
        "file_fsync_used_for_staging_and_json": True,
        "directory_fsync_claimed": False,
        "source_locator_base": "<temporary_work_root>/run_a",
        "source_artifact_records": source_observed,
        "staging_hashes": staging_observed,
        "canonical_hashes": canonical_observed,
        "canonical_paths": [record["canonical_path"] for record in records],
        "canonical_output_count": len(records),
        "candidate_artifacts_promoted": len(records),
        "training_performed": False,
        "network_used": False,
        "stage05_claim_or_verdict_changed": False,
        "protected_hashes": PROTECTED_HASHES,
        "negative_tests": negative_tests,
        "checks": {
            "source_checkpoint_v34_exact": True,
            "st07_21_evidence_and_manifest_exact": True,
            "protected_hashes_exact_before_and_after": True,
            "selected_run_a_source_7_of_7_hash_and_schema_exact": True,
            "canonical_targets_absent_before": True,
            "same_filesystem_staging_validated_7_of_7": True,
            "exclusive_lock_acquired": True,
            "no_overwrite_hard_link_commit_7_of_7": True,
            "canonical_hash_and_schema_exact_7_of_7": True,
            "transaction_journal_terminal_commit_planned": True,
            "negative_tests_fail_closed": True,
            "training_and_network_zero": True,
            "stage05_claim_or_verdict_unchanged": True,
        },
        "planned_change_set": PLANNED_CHANGE_SET,
        "actual_change_log": PLANNED_CHANGE_SET,
        "change_set_deviations": [],
        "scientific_interpretation": (
            "canonical_registration_of_prevalidated_run_a_only; "
            "not_new_training; not_new_scientific_validation; "
            "not_cross_environment_reproducibility; "
            "not_universal_model_superiority; not_stage05_claim_change"
        ),
        "remaining_risks": [
            (
                "A process-terminating crash is fail-closed through the durable "
                "journal but may require manual recovery before rerun."
            ),
            (
                "File fsync is used; no unsupported cross-platform claim of "
                "directory-entry durability or seven-file filesystem atomicity is made."
            ),
        ],
    }


def execute_promotion(
    source_root: Path,
    source_checkpoint: Path,
) -> dict[str, Any]:
    if JOURNAL_PATH.exists() or EVIDENCE_PATH.exists():
        raise FileExistsError("ST07_22 journal/evidence already exists")
    if LOCK_PATH.exists():
        raise FileExistsError("ST07_22 lock already exists")

    schema, _manifest, records, source_observed = load_registered_inputs(
        source_root, source_checkpoint
    )
    negative_tests = run_negative_tests()
    transaction_id = (
        f"st07_22_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_"
        f"{records[0]['selected_bundle_sha256'][:12]}"
    )
    staging_dir = DATA_REGISTRY / f".st07_22_staging_{transaction_id}"
    journal = build_journal(transaction_id, staging_dir, records)
    write_json_new(JOURNAL_PATH, journal)

    created: list[tuple[Path, str]] = []
    evidence_created = False
    committed = False
    try:
        with exclusive_lock(LOCK_PATH, transaction_id):
            staging_observed = prepare_staging(
                source_root, staging_dir, records, schema
            )
            update_journal(
                journal,
                "validated",
                details={"staged_file_count": len(staging_observed)},
            )
            update_journal(journal, "commit_started")

            def record_progress(paths: list[str]) -> None:
                update_journal(
                    journal,
                    "commit_started",
                    committed_paths=paths,
                    details={"committed_file_count": len(paths)},
                )

            created = commit_staged_links(
                staging_dir,
                records,
                project_root=PROJECT_ROOT,
                on_progress=record_progress,
            )
            canonical_observed = canonical_hashes_exact(records)
            read_v02_artifacts(DATA_REGISTRY, schema)
            update_journal(
                journal,
                "verified",
                committed_paths=[
                    path.relative_to(PROJECT_ROOT).as_posix()
                    for path, _ in created
                ],
                details={"verified_file_count": len(canonical_observed)},
            )
            cleanup_staging(staging_dir)
            if not protected_hashes_exact():
                raise PromotionError("Protected hashes changed during promotion")
            source_dir = source_root / SELECTED_SOURCE_LABEL
            validate_file_records(
                source_dir,
                records,
                relative_field="source_filename",
                hash_field="source_sha256",
            )

            evidence = build_evidence(
                source_checkpoint=source_checkpoint,
                transaction_id=transaction_id,
                records=records,
                source_observed=source_observed,
                staging_observed=staging_observed,
                canonical_observed=canonical_observed,
                negative_tests=negative_tests,
            )
            write_json_new(EVIDENCE_PATH, evidence)
            evidence_created = True
            evidence_sha = sha256_file(EVIDENCE_PATH)
            journal["evidence_sha256"] = evidence_sha
            update_journal(
                journal,
                "committed",
                committed_paths=evidence["canonical_paths"],
                terminal=True,
                details={
                    "canonical_file_count": len(canonical_observed),
                    "evidence_sha256": evidence_sha,
                },
            )
            persisted_journal = json.loads(
                JOURNAL_PATH.read_text(encoding="utf-8")
            )
            if (
                persisted_journal.get("state") != "committed"
                or persisted_journal.get("terminal") is not True
                or persisted_journal.get("evidence_sha256") != evidence_sha
            ):
                raise PromotionError("Terminal journal verification failed")
            canonical_hashes_exact(records)
            read_v02_artifacts(DATA_REGISTRY, schema)
            committed = True
        if LOCK_PATH.exists():
            raise PromotionError("Exclusive lock was not released")
        return {
            "status": "pass",
            "task_id": TASK_ID,
            "transaction_id": transaction_id,
            "canonical_artifacts": len(records),
            "negative_tests_passed": sum(negative_tests.values()),
            "journal_state": "committed",
            "evidence_sha256": sha256_file(EVIDENCE_PATH),
            "training_performed": False,
            "network_used": False,
        }
    except Exception as error:
        if committed:
            raise
        rollback_errors = rollback_created_targets(created)
        if evidence_created and EVIDENCE_PATH.exists():
            try:
                EVIDENCE_PATH.unlink()
            except OSError as evidence_error:
                rollback_errors.append(
                    f"evidence_cleanup:{type(evidence_error).__name__}:{evidence_error}"
                )
        try:
            cleanup_staging(staging_dir)
        except Exception as staging_error:
            rollback_errors.append(
                f"staging_cleanup:{type(staging_error).__name__}:{staging_error}"
            )
        journal["rollback_errors"] = rollback_errors
        try:
            update_journal(
                journal,
                "rolled_back" if not rollback_errors else "rollback_required",
                committed_paths=[],
                terminal=not rollback_errors,
                details={"error": f"{type(error).__name__}: {error}"},
            )
        except Exception:
            pass
        raise


def preflight(source_root: Path, source_checkpoint: Path) -> dict[str, Any]:
    schema, _manifest, records, _observed = load_registered_inputs(
        source_root, source_checkpoint
    )
    negative_tests = run_negative_tests()
    return {
        "status": "pass",
        "task_id": TASK_ID,
        "mode": "preflight",
        "source_artifacts": len(records),
        "canonical_targets_absent": True,
        "schema_rows": len(schema),
        "negative_tests_passed": sum(negative_tests.values()),
        "protected_hashes_exact": protected_hashes_exact(),
        "training_performed": False,
        "network_used": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transactional ST07_22 promotion of registered run_a 7/7."
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument(
        "--mode", choices=("preflight", "execute"), required=True
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    source_checkpoint = args.source_checkpoint.resolve()
    result = (
        preflight(source_root, source_checkpoint)
        if args.mode == "preflight"
        else execute_promotion(source_root, source_checkpoint)
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
