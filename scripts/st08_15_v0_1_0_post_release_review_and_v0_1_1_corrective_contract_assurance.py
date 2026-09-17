from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import tomllib
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_15_v0_1_1_corrective_contract_manifest_v01.csv"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_evidence_v01.json"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
ST08_14C_EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_14C_release_0_1_0_GitHub_execution_evidence_v01.json"


class CorrectiveContractError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CorrectiveContractError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise CorrectiveContractError(f"CSV is empty or lacks rows: {path}")
    return fields, rows


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _path_list_sha256(paths: Iterable[str]) -> str:
    payload = "".join(f"{path}\n" for path in sorted(paths)).encode("utf-8")
    return _sha256_bytes(payload)


def _unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise CorrectiveContractError(f"{label} must occur exactly once: {duplicates}")
    return values


def _tracked_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise CorrectiveContractError(f"cycle-breaking paths are not tracked: {missing}")
    policy = release_assurance._load_json(
        root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT)
    )
    forbidden = [
        path
        for path in tracked
        if release_assurance.classify_public_path(path, policy, root)
        not in {"ST08-06-MANIFEST-06", "ST08-06-MANIFEST-07"}
    ]
    if forbidden:
        raise CorrectiveContractError(
            f"tracked successor tree contains policy-excluded paths: {forbidden}"
        )
    return tracked


def build_manifest_rows(
    root: Path, contract: Mapping[str, Any]
) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    rows: list[dict[str, str]] = []
    for relative in _tracked_paths(root, contract):
        if relative in exclusions:
            continue
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append(
            {
                "relative_path": relative,
                "sha256": _sha256_bytes(payload),
                "size_bytes": str(len(payload)),
            }
        )
    return rows


def write_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    rows = build_manifest_rows(root, contract)
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=contract["successor_manifest"]["fields"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    tracked = sorted(
        [row["relative_path"] for row in rows]
        + list(contract["successor_manifest"]["cycle_breaking_exclusions"])
    )
    return {
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256_bytes(path.read_bytes()),
        "cycle_breaking_exclusions": sorted(
            contract["successor_manifest"]["cycle_breaking_exclusions"]
        ),
        "status": "PASS",
    }


def validate_manifest(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    if fields != contract["successor_manifest"]["fields"]:
        raise CorrectiveContractError("successor manifest schema mismatch")
    expected = build_manifest_rows(root, contract)
    if rows != expected:
        raise CorrectiveContractError("successor manifest differs from canonical Git index")
    tracked = _tracked_paths(root, contract)
    return {
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256_bytes(
            release_assurance.git_index_blob_bytes(
                MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root
            )
        ),
        "cycle_breaking_exclusions": sorted(
            contract["successor_manifest"]["cycle_breaking_exclusions"]
        ),
        "status": "PASS",
    }


def validate_decision_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    if matrix.get("method") != "weighted_sum_with_ordinal_1_to_5_scores_and_predeclared_criteria":
        raise CorrectiveContractError("unexpected decision-matrix method")
    criteria = matrix.get("criteria")
    options = matrix.get("options")
    if not isinstance(criteria, list) or not isinstance(options, list):
        raise CorrectiveContractError("decision matrix rows are missing")
    criterion_ids = _unique(
        (str(row.get("criterion_id", "")) for row in criteria), "criterion"
    )
    weights = {row["criterion_id"]: Decimal(str(row["weight"])) for row in criteria}
    if sum(weights.values()) != Decimal("1.00"):
        raise CorrectiveContractError("decision-matrix weights must sum to one")
    _unique((str(row.get("option_id", "")) for row in options), "option")
    scores: dict[str, Decimal] = {}
    selected: list[str] = []
    for option in options:
        option_scores = option.get("scores")
        if not isinstance(option_scores, Mapping) or set(option_scores) != set(criterion_ids):
            raise CorrectiveContractError(f"decision scores incomplete: {option.get('option_id')}")
        if any(
            not isinstance(value, int) or value < 1 or value > 5
            for value in option_scores.values()
        ):
            raise CorrectiveContractError(f"decision score outside 1..5: {option.get('option_id')}")
        recomputed = sum(weights[key] * Decimal(str(option_scores[key])) for key in criterion_ids)
        if recomputed.quantize(Decimal("0.01")) != Decimal(
            str(option.get("weighted_score"))
        ).quantize(Decimal("0.01")):
            raise CorrectiveContractError(f"weighted score mismatch: {option.get('option_id')}")
        scores[option["option_id"]] = recomputed
        if option.get("disposition") == "selected":
            selected.append(option["option_id"])
    winner = max(scores, key=scores.get)
    if selected != [matrix.get("selected_option")] or winner != "O04":
        raise CorrectiveContractError("phased v0.1.1 correction is not the unique winner")
    return {
        "criteria": len(criteria),
        "options": len(options),
        "selected": winner,
        "scores": {key: float(value) for key, value in scores.items()},
    }


def _validate_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise CorrectiveContractError("authority object missing")
    if authority.get("authorized_task_label") != (
        "NEXT_BLOCK_AUTHORIZED: "
        "ST08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_design"
    ):
        raise CorrectiveContractError("John task authority is missing")
    if authority.get("post_release_review_and_contract_design_authorized") is not True:
        raise CorrectiveContractError("contract-design authority missing")
    forbidden = [
        "source_or_runtime_change_authorized",
        "package_version_change_authorized",
        "tag_or_GitHub_release_authorized",
        "TestPyPI_or_PyPI_publication_authorized",
        "scientific_claim_protocol_result_or_verdict_change_authorized",
    ]
    if any(authority.get(key) is not False for key in forbidden):
        raise CorrectiveContractError("authority boundary is overstated")


def _validate_current_product_unchanged(contract: Mapping[str, Any], root: Path) -> None:
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project.get("version") != "0.1.0" or (
        "Development Status :: 3 - Alpha" not in project.get("classifiers", [])
    ):
        raise CorrectiveContractError("current package metadata changed")
    for item in contract.get("protected_current_artifacts", []):
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise CorrectiveContractError(f"protected current artifact changed: {item['path']}")
    if len(contract.get("protected_current_artifacts", [])) != 8:
        raise CorrectiveContractError("protected current artifact set mismatch")
    for item in contract.get("immutable_ST08_14C_artifacts", []):
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if _sha256_bytes(payload) != item.get("sha256"):
            raise CorrectiveContractError(f"immutable ST08_14C artifact changed: {item['path']}")
    if len(contract.get("immutable_ST08_14C_artifacts", [])) != 4:
        raise CorrectiveContractError("immutable ST08_14C artifact set mismatch")
    application = (root / "src/mlcra/application.py").read_text(encoding="utf-8")
    if '"John_release_authorization_not_granted"' not in application:
        raise CorrectiveContractError("observed doctor limitation is no longer present")


def _validate_release_observation(contract: Mapping[str, Any], root: Path) -> None:
    observed = contract.get("post_release_observations", {})
    release = observed.get("GitHub_release", {})
    exact = {
        "repository": "Vanargo/ML-CRA",
        "release_id": 383873796,
        "tag": "v0.1.0",
        "commit": "9d530b60fd262f21cfe63eb2482722972a24c3d2",
        "git_tree": "d8bda657cc1ee7659ca0a88050c43c54627463a0",
        "draft": False,
        "prerelease": False,
        "immutable": True,
    }
    if any(release.get(key) != value for key, value in exact.items()):
        raise CorrectiveContractError("v0.1.0 release observation mismatch")
    evidence = _load_json(root / ST08_14C_EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    if evidence.get("release", {}).get("assets") is None:
        raise CorrectiveContractError("ST08_14C asset evidence missing")
    expected_assets = {
        name: {"size_bytes": value["size_bytes"], "sha256": value["sha256"]}
        for name, value in evidence["release"]["assets"].items()
    }
    if observed.get("assets") != expected_assets:
        raise CorrectiveContractError("v0.1.0 asset observation differs from ST08_14C evidence")
    limitation = observed.get("known_limitation", {})
    if (
        limitation.get("doctor_release_ready") is not False
        or limitation.get("doctor_release_blockers")
        != ["John_release_authorization_not_granted"]
        or limitation.get("environment_or_scientific_failure") is not False
    ):
        raise CorrectiveContractError("known limitation classification mismatch")


def _validate_corrective_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    corrective = contract.get("corrective_release_contract", {})
    if (
        corrective.get("target_version") != "0.1.1"
        or corrective.get("target_tag") != "v0.1.1"
        or corrective.get("PyPI_disposition")
        != "deferred_until_v0_1_1_is_published_verified_accepted_and_separately_authorized"
    ):
        raise CorrectiveContractError("v0.1.1 corrective identity or PyPI boundary mismatch")
    permitted = corrective.get("permitted_future_product_changes", [])
    required_tokens = [
        "release_ready",
        "release_blockers",
        "release_readiness_scope=packaged_content_only_no_publication_authority",
        "never authorizes",
        "RELEASE_NOTES_0.1.1.md",
    ]
    if any(not any(token in row for row in permitted) for token in required_tokens):
        raise CorrectiveContractError("corrective doctor or documentation semantics incomplete")
    forbidden = corrective.get("forbidden_future_product_changes", [])
    for token in ["v0.1.0", "scientific claims", "TestPyPI or PyPI"]:
        if not any(token in row for row in forbidden):
            raise CorrectiveContractError(f"corrective prohibition omitted: {token}")
    phases = contract.get("phase_sequence", [])
    if len(phases) != 5 or [row.get("order") for row in phases] != list(range(1, 6)):
        raise CorrectiveContractError("corrective phase sequence mismatch")
    if phases[0].get("status") != "authorized_current_task":
        raise CorrectiveContractError("current phase authorization mismatch")
    future = [row.get("status") for row in phases[1:]]
    if future != [
        "proposed_not_authorized",
        "proposed_not_authorized",
        "proposed_not_authorized",
        "optional_proposed_not_authorized",
    ]:
        raise CorrectiveContractError("future phase was authorized or reordered")
    return {"target_version": "0.1.1", "phases": 5, "future_phases_authorized": 0}


def _scope_rows(root: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if fields != ["change_kind", "relative_path", "reason"]:
        raise CorrectiveContractError("unexpected ST08_15 change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_contract_bindings(
    contract: Mapping[str, Any],
    root: Path = PROJECT_ROOT,
    workflow_text: str | None = None,
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_design":
        raise CorrectiveContractError("unexpected task identifier")
    if contract.get("profile") != "CHANGE":
        raise CorrectiveContractError("profile must be CHANGE")
    _validate_authority(contract)
    _validate_current_product_unchanged(contract, root)
    _validate_release_observation(contract, root)
    decision = validate_decision_matrix(contract["decision_matrix"])
    corrective = _validate_corrective_contract(contract)
    manifest = validate_manifest(root, contract)
    protected = release_assurance.validate_protected_hashes(root, inventory="published")

    expected_scope = [
        (row["change_kind"], row["relative_path"])
        for row in contract["planned_changes"]
    ]
    observed_scope = _scope_rows(root)
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise CorrectiveContractError("actual change scope differs from planned changes")

    workflow_text = workflow_text if workflow_text is not None else (
        root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_workflow = [
        "st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_assurance.py contract",
        "st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_assurance.py mutations",
        "tests.test_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_st08_15",
        "st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_assurance.py final-evidence",
        "st08_14C_release_execution_assurance.py build-release",
        "gh release verify v0.1.0 --repo Vanargo/ML-CRA",
    ]
    missing = [token for token in required_workflow if token not in workflow_text]
    if missing:
        raise CorrectiveContractError(f"workflow omits ST08_15 control: {missing}")
    forbidden_workflow = [
        "contents: write",
        "id-token: write",
        "attestations: write",
        "gh release create",
        "gh release edit",
        "pypa/gh-action-pypi-publish",
    ]
    if any(token in workflow_text for token in forbidden_workflow):
        raise CorrectiveContractError("current assurance workflow gained publication authority")

    for relative in [ROADMAP_PATH, STAGE_PATH]:
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [
            contract["task_id"],
            "ACCEPTED_BY_JOHN: ST08_14C_release_0_1_0_GitHub_execution",
            "ST08_15A_v0_1_1_corrective_candidate_implementation",
            "proposed_not_authorized",
        ]:
            if token not in text:
                raise CorrectiveContractError(
                    f"canonical task registration missing: {relative}/{token}"
                )
    sources = contract.get("authoritative_support")
    if not isinstance(sources, list) or len(sources) != 8:
        raise CorrectiveContractError("authoritative source set mismatch")
    uris = {row.get("uri") for row in sources}
    for required_uri in {
        "https://semver.org/",
        "https://packaging.python.org/en/latest/specifications/version-specifiers/",
        "https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases",
        "https://docs.pypi.org/trusted-publishers/",
        "https://csrc.nist.gov/pubs/sp/800/218/final",
    }:
        if required_uri not in uris:
            raise CorrectiveContractError(f"authoritative source omitted: {required_uri}")
    return {
        "decision_matrix": decision,
        "corrective_release": corrective,
        "manifest": manifest,
        "protected_scientific_artifacts": protected,
        "protected_current_artifacts": 8,
        "immutable_ST08_14C_artifacts": 4,
        "change_scope": len(observed_scope),
        "product_files_changed": 0,
        "release_actions_performed": 0,
    }


def validate_evidence_relations(
    evidence: Mapping[str, Any],
    contract: Mapping[str, Any],
    bindings: Mapping[str, Any],
) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_evidence_v01":
        raise CorrectiveContractError("unexpected evidence schema")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "CHANGE":
        raise CorrectiveContractError("evidence task/profile mismatch")
    if evidence.get("status") != "contract_design_complete_future_phases_not_authorized":
        raise CorrectiveContractError("evidence status mismatch")
    baseline = evidence.get("source_baseline", {})
    if (
        baseline.get("git_commit") != contract["source_baseline"]["git_commit"]
        or baseline.get("git_tree") != contract["source_baseline"]["git_tree"]
        or baseline.get("project_version_before") != "0.1.0"
        or baseline.get("project_version_after") != "0.1.0"
        or baseline.get("ST08_14C_acceptance") != "ACCEPTED_BY_JOHN_AND_TASK_CLOSED"
    ):
        raise CorrectiveContractError("source baseline evidence mismatch")
    if evidence.get("mape_k_result") != {
        "selected_option": "O04",
        "weighted_score": 4.9,
        "decision": "preserve_v0_1_0_then_phase_a_compatible_v0_1_1_correction",
    }:
        raise CorrectiveContractError("MAPE-K decision evidence mismatch")
    if evidence.get("successor_manifest") != bindings["manifest"]:
        raise CorrectiveContractError("successor manifest evidence mismatch")
    expected_checks = {
        "contract_assurance": "PASS",
        "mutation_tests": "PASS_10_of_10",
        "focused_unittest": "PASS",
        "working_baseline": "PASS",
        "published_baseline": "PASS",
        "published_source_assurance": "PASS",
        "published_secret_scan": "PASS_zero_findings",
        "documentation_assurance": "PASS",
        "protected_scientific_artifacts": "PASS_18_of_18",
        "product_files_changed": 0,
        "release_actions_performed": 0,
        "training_runs": 0,
        "scientific_artifact_changes": 0,
    }
    if evidence.get("observed_checks") != expected_checks:
        raise CorrectiveContractError("observed checks are incomplete or overstated")
    if evidence.get("change_reconciliation") != {
        "planned_paths": 12,
        "actual_paths": 12,
        "unplanned_paths": [],
        "omitted_paths": [],
        "status": "PASS_exact_planned_path_set",
    }:
        raise CorrectiveContractError("change reconciliation mismatch")
    if any(
        evidence.get(key) not in {False, 0}
        for key in [
            "product_version_changed",
            "release_or_tag_changed",
            "PyPI_or_TestPyPI_action_performed",
            "release_actions_performed",
            "training_runs",
            "scientific_artifact_changes",
        ]
    ):
        raise CorrectiveContractError("forbidden side effect recorded")
    hosted = evidence.get("hosted_assurance", {})
    state = hosted.get("status")
    if state == "PENDING":
        if evidence.get("readiness") != "NOT_READY" or hosted.get("run_id") is not None:
            raise CorrectiveContractError("pending hosted assurance state mismatch")
    elif state == "PASS":
        head_sha = hosted.get("head_sha")
        if (
            evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE"
            or not isinstance(hosted.get("run_id"), int)
            or not isinstance(hosted.get("job_id"), int)
            or hosted.get("conclusion") != "success"
            or not isinstance(hosted.get("pull_request_url"), str)
            or not isinstance(head_sha, str)
            or not re.fullmatch(r"[0-9a-f]{40}", head_sha)
        ):
            raise CorrectiveContractError("successful hosted assurance evidence incomplete")
    else:
        raise CorrectiveContractError("hosted assurance status must be PENDING or PASS")
    if evidence.get("technical_status") != "PASS":
        raise CorrectiveContractError("technical status mismatch")
    return {
        "status": "PASS",
        "selected_option": "O04",
        "target_version": "0.1.1",
        "hosted_assurance": state,
        "future_phases_authorized": 0,
    }


def validate_contract(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    return {"status": "PASS", "bindings": validate_contract_bindings(contract, root)}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    return {
        "status": "PASS",
        "bindings": bindings,
        "evidence": validate_evidence_relations(evidence, contract, bindings),
    }


def _expect_rejection(label: str, action: Any) -> str:
    try:
        action()
    except (CorrectiveContractError, release_assurance.AssuranceError):
        return label
    raise CorrectiveContractError(f"negative mutation accepted: {label}")


def run_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    labels: list[str] = []
    contract_mutations = [
        ("wrong_authority", lambda value: value["authority"].update(authorized_task_label="wrong")),
        ("authorize_source_change", lambda value: value["authority"].update(source_or_runtime_change_authorized=True)),
        ("select_direct_PyPI", lambda value: value["decision_matrix"].update(selected_option="O01")),
        ("retag_v0_1_0", lambda value: value["corrective_release_contract"].update(target_tag="v0.1.0")),
        ("authorize_future_phase", lambda value: value["phase_sequence"][1].update(status="authorized")),
    ]
    for label, mutate in contract_mutations:
        mutated = copy.deepcopy(contract)
        mutate(mutated)
        labels.append(_expect_rejection(label, lambda value=mutated: validate_contract_bindings(value, root)))
    evidence_mutations = [
        ("version_changed", lambda value: value.update(product_version_changed=True)),
        ("release_changed", lambda value: value.update(release_or_tag_changed=True)),
        ("manifest_drift", lambda value: value["successor_manifest"].update(manifest_sha256="0" * 64)),
        ("scientific_change", lambda value: value.update(scientific_artifact_changes=1)),
        ("premature_ready", lambda value: value.update(readiness="READY_FOR_JOHN_ACCEPTANCE")),
    ]
    for label, mutate in evidence_mutations:
        mutated = copy.deepcopy(evidence)
        mutate(mutated)
        labels.append(
            _expect_rejection(
                label,
                lambda value=mutated: validate_evidence_relations(value, contract, bindings),
            )
        )
    return {"status": "PASS", "mutations_rejected": len(labels), "labels": labels}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_15 v0.1.1 corrective contract assurance")
    parser.add_argument(
        "command", choices=("write-manifest", "contract", "mutations", "final-evidence")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "write-manifest":
            result = write_manifest()
        elif args.command == "contract":
            result = validate_contract()
        elif args.command == "mutations":
            result = run_mutations()
        else:
            result = validate_final_evidence()
    except (
        CorrectiveContractError,
        release_assurance.AssuranceError,
        csv.Error,
        json.JSONDecodeError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
