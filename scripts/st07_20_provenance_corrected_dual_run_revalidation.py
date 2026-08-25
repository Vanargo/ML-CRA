from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.nested_artifacts import (  # noqa: E402
    NestedCVArtifacts,
    compare_v02_runs,
    read_v02_artifacts,
)
from st07_18_dual_run_validation import (  # noqa: E402
    EXPECTED_ARTIFACT_ROWS,
    EXPECTED_CLASS_COLUMN_COUNTS,
    SCHEMA_PATH,
    artifact_inventory,
    build_protected_manifest,
    diagnose_comparison_classes,
    manifest_sha256,
    require_safe_empty_work_root,
    run_one,
    sha256_file,
)


TASK_ID = (
    "ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation"
)
SOURCE_RUNNER_TASK_ID = (
    "ST07_18_nested_cv_v02_dual_run_reproducibility_validation"
)
EVIDENCE_PATH = (
    PROJECT_ROOT
    / "data_registry"
    / "st07_20_nested_cv_v02_provenance_corrected_dual_run_"
    "revalidation_evidence_v01.json"
)
ARTIFACT_CONTEXT = "miniboone_v02_scientific_candidate"
ROW_STATUS = "nested_research_draft"
INTERPRETATION_ALLOWED = "limited_nested_protocol_review_only"
BOUNDARY_WARNING = (
    "MiniBooNE v02 scientific-validation candidate artifact; "
    "noncanonical and not promoted."
)
QUALITY_TEMPLATE = (
    "MiniBooNE v02 scientific-candidate check {check_id}; "
    "artifact is noncanonical and not promoted."
)
REGISTERED_CACHE_MANIFEST_SHA256 = (
    "a6ae3314752c8dce595fb9ef491f27674806e54583bea7d650a3d46878eb7318"
)
PROTECTED_CONTRACT_HASHES = {
    "scripts/st07_17_miniboone_v02_runner.py": (
        "aad089749bd2795651912afb438f547a7feba3ffb5500e52a394c978a6fa68ea"
    ),
    "scripts/st07_18_dual_run_validation.py": (
        "112d1ba0c41af85062711b35c35fddd45136a75c36d49573d34de108cf382d1f"
    ),
    "src/mlcra/nested_cv.py": (
        "804050fbcd8e8a9f10f495ed11de1786677af559c15a4c7f77d955bf24fa6ba9"
    ),
    "src/mlcra/nested_artifacts.py": (
        "19bf4021ef6ee9d556e1bb2f6d03c03901463ce0aa652a81fc80d58b9c246723"
    ),
    "data_registry/openml_miniboone_nested_cv_v02_protocol_lock.csv": (
        "762f02b8b74e3fc5e9f5c75658021f9a384f974316be8d5e6b748478be7dbe9c"
    ),
    "data_registry/openml_miniboone_nested_cv_v02_expected_output_schema.csv": (
        "761b71c9a81438612bed59bc23ac9c382715ab447269fae53daf45f71239f672"
    ),
    (
        "data_registry/st07_18_nested_cv_v02_dual_run_"
        "reproducibility_validation_evidence_v01.json"
    ): "a83620fba7bc84f9e57787f2d93637d9630221be5d9b596b97908dfff435f93c",
    (
        "data_registry/st07_19_nested_cv_v02_artifact_context_and_"
        "provenance_contract_evidence_v01.json"
    ): "8e617d0d3f8d5f471ced7be9985e617b26f3c8c5db624e10ef1fddaa5134602a",
}


def validate_provenance(artifacts: NestedCVArtifacts) -> dict[str, Any]:
    quality = artifacts.quality_checks
    warnings = artifacts.warnings
    outer = artifacts.outer_scores
    selected = artifacts.selected_params

    expected_details = quality["check_id"].map(
        lambda check_id: QUALITY_TEMPLATE.format(check_id=check_id)
    )
    quality_exact = bool(
        len(quality) == 16
        and quality["check_result"].eq("pass").all()
        and quality["details_ru"].equals(expected_details)
    )
    boundary = warnings.loc[warnings["object"].eq("protocol_boundary")]
    boundary_exact = bool(
        len(boundary) == 1
        and boundary["warning_ru"].eq(BOUNDARY_WARNING).all()
    )
    text_values = [
        *quality["details_ru"].astype(str).tolist(),
        *warnings["warning_ru"].astype(str).tolist(),
    ]
    fixture_text_absent = all(
        "st07_16" not in value.casefold()
        and "software fixture" not in value.casefold()
        for value in text_values
    )
    row_policy_exact = bool(
        outer["row_status"].eq(ROW_STATUS).all()
        and outer["interpretation_allowed"].eq(
            INTERPRETATION_ALLOWED
        ).all()
        and selected["row_status"].eq(ROW_STATUS).all()
    )
    checks = {
        "quality_details_exact": quality_exact,
        "protocol_boundary_warning_exact": boundary_exact,
        "fixture_provenance_absent": fixture_text_absent,
        "scientific_candidate_row_policy_exact": row_policy_exact,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "quality_row_count": len(quality),
        "warning_row_count": len(warnings),
        "protocol_boundary_row_count": len(boundary),
        "artifact_context": ARTIFACT_CONTEXT,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-server-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()

    work_root = require_safe_empty_work_root(args.work_root)
    if EVIDENCE_PATH.exists():
        raise FileExistsError("ST07_20 evidence path must not already exist")
    schema = read_csv_checked(SCHEMA_PATH)
    canonical_paths = sorted(
        {(PROJECT_ROOT / path).resolve() for path in schema["canonical_path"]}
    )
    protected_contracts_before = {
        path: sha256_file(PROJECT_ROOT / path)
        for path in PROTECTED_CONTRACT_HASHES
    }
    protected_before = build_protected_manifest()
    canonical_absent_before = all(not path.exists() for path in canonical_paths)

    process_records: list[dict[str, Any]] = []
    for label in ("run_a", "run_b"):
        process_records.append(
            run_one(label, args.cache_server_dir, work_root / label)
        )

    run_artifacts: dict[str, NestedCVArtifacts] = {}
    artifact_records: dict[str, dict[str, Any]] = {}
    provenance_records: dict[str, dict[str, Any]] = {}
    artifact_errors: dict[str, str] = {}
    for record in process_records:
        label = record["label"]
        try:
            artifacts = read_v02_artifacts(work_root / label, schema)
            run_artifacts[label] = artifacts
            artifact_records[label] = artifact_inventory(
                work_root / label, artifacts
            )
            provenance_records[label] = validate_provenance(artifacts)
        except Exception as error:
            artifact_errors[label] = f"{type(error).__name__}: {error}"

    comparison_classes = {
        key: {"status": "not_evaluated", "column_count": count, "errors": []}
        for key, count in EXPECTED_CLASS_COLUMN_COUNTS.items()
    }
    comparator_result: dict[str, Any] | None = None
    comparator_error: str | None = None
    if set(run_artifacts) == {"run_a", "run_b"}:
        comparison_classes = diagnose_comparison_classes(
            run_artifacts["run_a"], run_artifacts["run_b"], schema
        )
        try:
            comparator_result = compare_v02_runs(
                run_artifacts["run_a"], run_artifacts["run_b"], schema
            )
        except Exception as error:
            comparator_error = f"{type(error).__name__}: {error}"

    protected_after = build_protected_manifest()
    protected_contracts_after = {
        path: sha256_file(PROJECT_ROOT / path)
        for path in PROTECTED_CONTRACT_HASHES
    }
    changed_protected = sorted(
        path
        for path in set(protected_before) | set(protected_after)
        if protected_before.get(path) != protected_after.get(path)
    )
    canonical_absent_after = all(not path.exists() for path in canonical_paths)
    runner_results = [record.get("runner_result") for record in process_records]
    process_pass = bool(
        len(process_records) == 2
        and all(record["return_code"] == 0 for record in process_records)
        and all(record["parse_error"] is None for record in process_records)
        and all(
            result is not None
            and result.get("status") == "pass"
            and result.get("task_id") == SOURCE_RUNNER_TASK_ID
            and result.get("artifact_context") == ARTIFACT_CONTEXT
            and result.get("training_performed") is True
            for result in runner_results
        )
        and len({result["pid"] for result in runner_results if result}) == 2
        and all(result["pid"] != os.getpid() for result in runner_results if result)
    )
    offline_pass = all(
        result is not None
        and result.get("network_attempts") == 0
        and result.get("network_used") is False
        and result.get("cache_file_count") == 3
        and result.get("cache_manifest_sha256")
        == REGISTERED_CACHE_MANIFEST_SHA256
        for result in runner_results
    )
    runtime_pass = all(
        result is not None
        and result.get("runtime_backend_count") == 2
        and result.get("runtime_threads") == [1, 1]
        for result in runner_results
    )
    quality_pass = all(
        result is not None and result.get("quality_pass_count") == 16
        for result in runner_results
    )
    artifact_rows_pass = set(artifact_records) == {"run_a", "run_b"} and all(
        inventory[artifact_id]["rows"] >= 1
        if expected is None
        else inventory[artifact_id]["rows"] == expected
        for inventory in artifact_records.values()
        for artifact_id, expected in EXPECTED_ARTIFACT_ROWS.items()
    )
    comparison_pass = bool(
        comparator_result is not None
        and comparator_error is None
        and comparator_result.get("class_column_counts")
        == EXPECTED_CLASS_COLUMN_COUNTS
        and all(
            result["status"] == "pass"
            and result["column_count"] == EXPECTED_CLASS_COLUMN_COUNTS[key]
            for key, result in comparison_classes.items()
        )
    )
    provenance_pass = bool(
        set(provenance_records) == {"run_a", "run_b"}
        and all(
            record["status"] == "pass"
            for record in provenance_records.values()
        )
    )
    protected_contracts_pass = bool(
        protected_contracts_before == PROTECTED_CONTRACT_HASHES
        and protected_contracts_after == PROTECTED_CONTRACT_HASHES
    )
    checks = {
        "exactly_two_fresh_process_full_runs": process_pass,
        "separate_noncanonical_output_directories": bool(
            (work_root / "run_a").is_dir()
            and (work_root / "run_b").is_dir()
            and (work_root / "run_a").resolve()
            != (work_root / "run_b").resolve()
        ),
        "offline_registered_cache_and_zero_network": offline_pass,
        "candidate_artifacts_and_row_policies": artifact_rows_pass,
        "registered_comparison_A_B_D_exact_C_finite_nonnegative": comparison_pass,
        "corrected_scientific_candidate_provenance": provenance_pass,
        "quality_checks_16_of_16_per_run": quality_pass,
        "runtime_two_backends_one_thread_per_run": runtime_pass,
        "protected_project_state_unchanged_during_runs": not changed_protected,
        "protected_scientific_contract_hashes_exact": protected_contracts_pass,
        "canonical_v02_outputs_absent": (
            canonical_absent_before and canonical_absent_after
        ),
        "claim_or_verdict_change_none": True,
        "promotion_not_performed": True,
    }
    technical_status = "PASS" if all(checks.values()) else "FAIL"
    readiness = (
        "READY_FOR_JOHN_ACCEPTANCE"
        if technical_status == "PASS"
        else "NOT_READY"
    )
    evidence = {
        "evidence_schema_version": "st07_20_evidence_v01",
        "task_id": TASK_ID,
        "task_profile": "SCIENTIFIC_VALIDATION",
        "authority": f"NEXT_BLOCK_AUTHORIZED: {TASK_ID}",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "technical_status": technical_status,
        "readiness": readiness,
        "scientific_interpretation": (
            "same_environment_repeatability_of_provenance_corrected_v02_"
            "candidate_artifacts_only; not_cross_environment_reproducibility; "
            "not_universal_model_superiority; not_stage05_claim_support"
        ),
        "protocol_id": "miniboone_nested_cv_v02",
        "validation_run_count": 2,
        "fresh_process_invocations": 2,
        "separate_noncanonical_directories": ["run_a", "run_b"],
        "artifact_context_required": ARTIFACT_CONTEXT,
        "process_records": process_records,
        "artifact_records": artifact_records,
        "artifact_errors": artifact_errors,
        "provenance_records": provenance_records,
        "expected_artifact_rows": EXPECTED_ARTIFACT_ROWS,
        "comparison_classes": comparison_classes,
        "authoritative_comparator_result": comparator_result,
        "authoritative_comparator_error": comparator_error,
        "checks": checks,
        "protected_file_count": len(protected_before),
        "protected_manifest_sha256_before": manifest_sha256(protected_before),
        "protected_manifest_sha256_after": manifest_sha256(protected_after),
        "changed_protected_paths": changed_protected,
        "protected_contract_hashes": protected_contracts_after,
        "canonical_output_count": len(canonical_paths),
        "canonical_outputs_absent_before": canonical_absent_before,
        "canonical_outputs_absent_after": canonical_absent_after,
        "candidate_artifacts_promoted": 0,
        "stage05_claim_or_verdict_changed": False,
        "planned_change_set": [
            "docs/agent/st07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation_change_scope_v01.csv",
            "scripts/st07_20_provenance_corrected_dual_run_revalidation.py",
            "data_registry/st07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation_evidence_v01.json",
            "scripts/agent_verify.py",
            "docs/stages/stage_07_code_modularization.md",
            "roadmap.md",
        ],
    }
    EVIDENCE_PATH.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return 0 if technical_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
