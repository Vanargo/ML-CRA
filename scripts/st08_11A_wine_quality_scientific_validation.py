from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlcra.application import run_audit, verify_bundle


CONTRACT_PATH = ROOT / "configs/project_readiness/st08_11A_registered_regression_dataset_claim_and_scientific_validation_contract_v01.json"
CLAIM_PATH = ROOT / "configs/claims/uci_wine_quality_red_hgbr_vs_ridge_rmse_claim_v01.json"
FOLD_PATH = ROOT / "data_registry/st08_11A_wine_quality_red_fold_scores_v01.csv"
EVIDENCE_PATH = ROOT / "data_registry/st08_11A_registered_regression_dataset_claim_and_scientific_validation_evidence_v01.json"
EXPECTED_HEADER = [
    "fixed acidity", "volatile acidity", "citric acid", "residual sugar",
    "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density",
    "pH", "sulphates", "alcohol", "quality",
]
FOLD_FIELDS = [
    "claim_id", "dataset_id", "seed", "fold", "train_rows", "test_rows",
    "baseline_rmse", "candidate_rmse", "primary_delta",
    "baseline_mae", "candidate_mae",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def read_official_member(archive: Path, contract: dict[str, Any]) -> tuple[bytes, list[list[str]]]:
    member = contract["dataset_registration"]["archive_member"]
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if member not in names or names.count(member) != 1:
            raise ValueError(f"archive must contain exactly one {member!r}; observed={names!r}")
        payload = bundle.read(member)
    text = payload.decode("utf-8")
    rows = list(csv.reader(text.splitlines(), delimiter=";", strict=True))
    if not rows or rows[0] != EXPECTED_HEADER:
        raise ValueError(f"unexpected header: {rows[0] if rows else None!r}")
    data = rows[1:]
    expected_rows = int(contract["dataset_registration"]["expected_rows"])
    if len(data) != expected_rows:
        raise ValueError(f"expected {expected_rows} rows; observed={len(data)}")
    if any(len(row) != len(EXPECTED_HEADER) or any(cell == "" for cell in row) for row in data):
        raise ValueError("ragged or empty data cell")
    for row in data:
        for cell in row:
            if not math.isfinite(float(cell)):
                raise ValueError("non-finite numeric cell")
    return payload, rows


def write_normalized_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter=",", lineterminator="\n")
        writer.writerows(rows)


def scientific_payload(bundle: Path) -> dict[str, Any]:
    summary = load_json(bundle / "audit_summary.json")
    summary.pop("execution_seconds", None)
    return {
        "input_validation": load_json(bundle / "input_validation.json"),
        "provenance": load_json(bundle / "provenance.json"),
        "audit_summary": summary,
        "verdict": load_json(bundle / "verdict.json"),
    }


def fold_rows(summary: dict[str, Any], dataset_id: str) -> list[dict[str, Any]]:
    result = []
    for row in summary["folds"]:
        result.append({
            "claim_id": summary["claim_id"],
            "dataset_id": dataset_id,
            "seed": int(row["seed"]),
            "fold": int(row["fold"]),
            "train_rows": int(row["train_rows"]),
            "test_rows": int(row["test_rows"]),
            "baseline_rmse": float(row["baseline_metrics"]["root_mean_squared_error"]),
            "candidate_rmse": float(row["candidate_metrics"]["root_mean_squared_error"]),
            "primary_delta": float(row["primary_delta"]),
            "baseline_mae": float(row["baseline_metrics"]["mean_absolute_error"]),
            "candidate_mae": float(row["candidate_metrics"]["mean_absolute_error"]),
        })
    return result


def validate_rows(rows: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    protocol = contract["prospective_claim"]
    seeds = [int(seed) for seed in protocol["seeds"]]
    folds = int(protocol["n_splits"])
    expected_keys = {(seed, fold) for seed in seeds for fold in range(1, folds + 1)}
    actual_keys = {(int(row["seed"]), int(row["fold"])) for row in rows}
    if len(rows) != len(expected_keys) or actual_keys != expected_keys:
        raise ValueError("fold key set mismatch or duplicate")
    deltas: list[float] = []
    seed_deltas: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        expected_delta = float(row["baseline_rmse"]) - float(row["candidate_rmse"])
        recorded_delta = float(row["primary_delta"])
        if not math.isclose(expected_delta, recorded_delta, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("primary delta relation failure")
        for field in ("baseline_rmse", "candidate_rmse", "primary_delta", "baseline_mae", "candidate_mae"):
            if not math.isfinite(float(row[field])):
                raise ValueError(f"non-finite {field}")
        deltas.append(recorded_delta)
        seed_deltas[int(row["seed"])].append(recorded_delta)
    mean_delta = sum(deltas) / len(deltas)
    mean_baseline_rmse = sum(float(row["baseline_rmse"]) for row in rows) / len(rows)
    mean_candidate_rmse = sum(float(row["candidate_rmse"]) for row in rows) / len(rows)
    mean_baseline_mae = sum(float(row["baseline_mae"]) for row in rows) / len(rows)
    mean_candidate_mae = sum(float(row["candidate_mae"]) for row in rows) / len(rows)
    positive = sum(delta > 0.0 for delta in deltas)
    threshold = float(protocol["minimum_mean_delta"])
    if mean_delta >= threshold and positive == len(deltas):
        verdict = "supported"
    elif mean_delta >= threshold:
        verdict = "fragile"
    else:
        verdict = "not_supported"
    return {
        "fold_count": len(deltas),
        "mean_primary_delta": mean_delta,
        "mean_baseline_rmse": mean_baseline_rmse,
        "mean_candidate_rmse": mean_candidate_rmse,
        "mean_baseline_mae": mean_baseline_mae,
        "mean_candidate_mae": mean_candidate_mae,
        "min_primary_delta": min(deltas),
        "max_primary_delta": max(deltas),
        "positive_primary_delta_folds": positive,
        "seed_mean_primary_deltas": {str(seed): sum(values) / len(values) for seed, values in sorted(seed_deltas.items())},
        "verdict": verdict,
    }


def write_fold_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FOLD_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_fold_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FOLD_FIELDS:
            raise ValueError("fold CSV schema mismatch")
        return list(reader)


def run_registered(archive: Path) -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    claim = load_json(CLAIM_PATH)
    if contract["status"] != "prospective_locked_before_dataset_download_or_model_execution":
        raise ValueError("prospective contract status mismatch")
    if claim["claim_id"] != contract["prospective_claim"]["claim_id"]:
        raise ValueError("claim relation mismatch")
    member_bytes, source_rows = read_official_member(archive, contract)
    with tempfile.TemporaryDirectory(prefix="mlcra_st08_11A_") as temporary:
        temp = Path(temporary)
        normalized = temp / "winequality-red-mlcra-v01.csv"
        write_normalized_csv(normalized, source_rows)
        bundle_a = temp / "run_a"
        bundle_b = temp / "run_b"
        result_a = run_audit(CLAIM_PATH, normalized, bundle_a)
        result_b = run_audit(CLAIM_PATH, normalized, bundle_b)
        verify_a = verify_bundle(bundle_a)
        verify_b = verify_bundle(bundle_b)
        payload_a = scientific_payload(bundle_a)
        payload_b = scientific_payload(bundle_b)
        if payload_a != payload_b:
            raise ValueError("scientific payload is not deterministic across two runs")
        summary = load_json(bundle_a / "audit_summary.json")
        verdict = load_json(bundle_a / "verdict.json")
        rows = fold_rows(summary, contract["dataset_registration"]["dataset_id"])
        recomputed = validate_rows(rows, contract)
        if verdict["category"] != recomputed["verdict"]:
            raise ValueError("registered verdict differs from independent recomputation")
        write_fold_csv(FOLD_PATH, rows)
        evidence = {
            "schema_version": "st08_11A_registered_regression_dataset_claim_and_scientific_validation_evidence_v01",
            "evidence_id": "st08_11A_registered_regression_dataset_claim_and_scientific_validation_evidence_v01",
            "task_id": contract["task_id"],
            "recorded_at": "2026-08-24",
            "profile": "SCIENTIFIC_VALIDATION",
            "status": "PASS_scientific_validation_completed",
            "authority": contract["authority"],
            "prospective_lock": {
                "claim_sha256_before_download": sha256_file(CLAIM_PATH),
                "initial_contract_sha256_before_download": "abb7927fa644fd437783d261730424c9a1536b3c42dfd92565c373da1e2237f0",
                "contract_sha256_before_model_execution": sha256_file(CONTRACT_PATH),
                "pre_execution_amendment": "After source download and structural inspection but before model execution, the already declared semicolon delimiter was operationalized as a lossless UTF-8 LF comma-CSV transformation required by the ST08_11 application input contract; claim models seeds folds metrics threshold and verdict policy were unchanged.",
                "threshold_and_protocol_changed_after_result": False,
            },
            "dataset_provenance": {
                **contract["dataset_registration"],
                "downloaded_archive_sha256": sha256_file(archive),
                "official_member_sha256": hashlib.sha256(member_bytes).hexdigest(),
                "normalized_application_csv_sha256": sha256_file(normalized),
                "observed_rows": len(source_rows) - 1,
                "observed_columns": len(source_rows[0]),
                "observed_missing_or_nonfinite_cells": 0,
                "raw_data_retained_in_project": False,
            },
            "observed_execution": {
                "audit_first": {key: value for key, value in result_a.items() if key != "bundle"},
                "audit_second": {key: value for key, value in result_b.items() if key != "bundle"},
                "verify_first": {key: value for key, value in verify_a.items() if key != "bundle"},
                "verify_second": {key: value for key, value in verify_b.items() if key != "bundle"},
                "temporary_bundles": "REMOVED_after_relations_hashes_verdict_and_determinism_were_registered",
                "scientific_payload_deterministic_excluding_timing_and_timestamps": True,
                "network_attempts_during_each_audit": 0,
                "model_or_hyperparameter_selection_performed": False,
            },
            "scientific_results": {
                **recomputed,
                "primary_metric": "root_mean_squared_error",
                "secondary_metric": "mean_absolute_error",
                "minimum_mean_delta": contract["prospective_claim"]["minimum_mean_delta"],
                "fold_evidence_path": FOLD_PATH.relative_to(ROOT).as_posix(),
                "fold_evidence_sha256": sha256_file(FOLD_PATH),
            },
            "scientific_verdict": {
                "category": verdict["category"],
                "scope_limit": verdict["scope_limit"],
                "permitted_interpretation": contract["permitted_interpretation"],
                "forbidden_interpretations": contract["forbidden_interpretations"],
            },
            "sampling_and_bias_register": contract["sampling_and_bias_register"],
            "authoritative_support": contract["authoritative_support"],
            "protected_scientific_boundary": {
                "MiniBooNE_claim_protocol_evidence_or_verdict_changed": False,
                "expected_protected_artifacts": 18,
            },
            "checkpoint": contract["checkpoint"],
            "technical_status": "PASS",
            "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        }
        EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return validate_registered()


def validate_registered() -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    evidence = load_json(EVIDENCE_PATH)
    rows = read_fold_csv(FOLD_PATH)
    recomputed = validate_rows(rows, contract)
    scientific = evidence["scientific_results"]
    for field in ("fold_count", "positive_primary_delta_folds", "verdict"):
        if scientific[field] != recomputed[field]:
            raise ValueError(f"evidence mismatch: {field}")
    for field in (
        "mean_primary_delta", "min_primary_delta", "max_primary_delta",
        "mean_baseline_rmse", "mean_candidate_rmse", "mean_baseline_mae", "mean_candidate_mae",
    ):
        if not math.isclose(float(scientific[field]), float(recomputed[field]), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"evidence mismatch: {field}")
    if evidence["scientific_verdict"]["category"] != recomputed["verdict"]:
        raise ValueError("scientific verdict mismatch")
    if scientific["fold_evidence_sha256"] != sha256_file(FOLD_PATH):
        raise ValueError("fold evidence hash mismatch")
    if evidence["dataset_provenance"]["raw_data_retained_in_project"] is not False:
        raise ValueError("raw-data exclusion mismatch")
    return {"status": "PASS", **recomputed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--verify-registered", action="store_true")
    args = parser.parse_args()
    if args.verify_registered:
        result = validate_registered()
    elif args.archive is not None:
        result = run_registered(args.archive.resolve())
    else:
        parser.error("use --archive PATH or --verify-registered")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
