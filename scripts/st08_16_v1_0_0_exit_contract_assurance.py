from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import subprocess
import sys
import tomllib
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_16_v0_1_1_post_release_review_and_v1_0_0_exit_contract_v01.json"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_16_v0_1_1_post_release_review_and_v1_0_0_exit_contract_evidence_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_16_v1_0_0_exit_contract_manifest_v01.csv"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_16_v0_1_1_post_release_review_and_v1_0_0_exit_contract_change_scope_v01.csv"
ST08_15C_EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_15C_v0_1_1_GitHub_execution_evidence_v01.json"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"


class ExitContractError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExitContractError(f"JSON root must be an object: {path}")
    return value


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not fields or not rows:
        raise ExitContractError(f"CSV is empty or lacks rows: {path}")
    return fields, rows


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _path_list_sha256(paths: Iterable[str]) -> str:
    payload = "".join(f"{path}\n" for path in sorted(paths)).encode("utf-8")
    return _sha256(payload)


def _unique(values: Iterable[str], label: str) -> list[str]:
    values = list(values)
    duplicates = sorted(value for value, count in Counter(values).items() if count != 1)
    if duplicates:
        raise ExitContractError(f"{label} must occur exactly once: {duplicates}")
    return values


def _tracked_paths(root: Path, contract: Mapping[str, Any]) -> list[str]:
    tracked = release_assurance.tracked_repository_paths(root)
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(tracked))
    if missing:
        raise ExitContractError(f"cycle-breaking paths are not tracked: {missing}")
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
        raise ExitContractError(f"successor tree contains policy-excluded paths: {forbidden}")
    return tracked


def build_manifest_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, str]]:
    exclusions = set(contract["successor_manifest"]["cycle_breaking_exclusions"])
    rows: list[dict[str, str]] = []
    for relative in _tracked_paths(root, contract):
        if relative in exclusions:
            continue
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append(
            {
                "relative_path": relative,
                "sha256": _sha256(payload),
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
        "status": "PASS",
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256(path.read_bytes()),
        "cycle_breaking_exclusions": sorted(
            contract["successor_manifest"]["cycle_breaking_exclusions"]
        ),
    }


def validate_manifest(root: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    fields, rows = _load_csv(root / MANIFEST_PATH.relative_to(PROJECT_ROOT))
    if fields != contract["successor_manifest"]["fields"]:
        raise ExitContractError("successor manifest schema mismatch")
    expected = build_manifest_rows(root, contract)
    if rows != expected:
        raise ExitContractError("successor manifest differs from canonical Git index")
    tracked = _tracked_paths(root, contract)
    manifest_payload = release_assurance.git_index_blob_bytes(
        MANIFEST_PATH.relative_to(PROJECT_ROOT).as_posix(), root
    )
    return {
        "status": "PASS",
        "paths": len(tracked),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked),
        "manifest_sha256": _sha256(manifest_payload),
        "cycle_breaking_exclusions": sorted(
            contract["successor_manifest"]["cycle_breaking_exclusions"]
        ),
    }


def _validate_authority(contract: Mapping[str, Any]) -> None:
    authority = contract.get("authority", {})
    if authority.get("authorized_task_label") != (
        "NEXT_BLOCK_AUTHORIZED: "
        "ST08_16_v0_1_1_post_release_review_and_v1_0_0_exit_contract_design"
    ):
        raise ExitContractError("John task authority is missing")
    if authority.get("post_release_review_and_exit_contract_design_authorized") is not True:
        raise ExitContractError("current design authority is missing")
    forbidden = [
        "product_source_or_runtime_change_authorized",
        "package_version_or_classifier_change_authorized",
        "tag_or_GitHub_release_authorized",
        "TestPyPI_or_PyPI_publication_authorized",
        "scientific_claim_protocol_result_or_verdict_change_authorized",
        "future_block_authorized",
    ]
    if any(authority.get(key) is not False for key in forbidden):
        raise ExitContractError("authority boundary is overstated")


def _validate_baseline(contract: Mapping[str, Any], root: Path) -> None:
    baseline = contract.get("source_baseline", {})
    if (
        baseline.get("commit") != "e22d3db4cf4576da8ce12d58ce2cc4f4f28f030b"
        or baseline.get("git_tree") != "9fa92e00835b58fcd2afe1e530bda42ff7b1827b"
        or baseline.get("tracked_paths") != 369
        or baseline.get("protected_artifacts") != 18
        or baseline.get("baseline_status") != "PASS"
    ):
        raise ExitContractError("source baseline mismatch")
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", baseline["commit"], "HEAD"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        raise ExitContractError("registered source baseline is not an ancestor of HEAD")
    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    if project.get("version") != "0.1.1":
        raise ExitContractError("ST08_16 must not change the current package version")
    if "Development Status :: 3 - Alpha" not in project.get("classifiers", []):
        raise ExitContractError("ST08_16 must not pre-apply the 1.0.0 maturity classifier")
    release_assurance.validate_protected_hashes(root, inventory="published")


def _validate_predecessor_and_release(contract: Mapping[str, Any], root: Path) -> None:
    predecessor = contract.get("accepted_predecessor", {})
    if (
        predecessor.get("task_id") != "ST08_15C_v0_1_1_GitHub_execution"
        or predecessor.get("John_decision") != ["ACCEPTED_BY_JOHN", "TASK_CLOSED"]
        or predecessor.get("evidence_closure_PR") != 25
        or predecessor.get("merge_commit") != "e22d3db4cf4576da8ce12d58ce2cc4f4f28f030b"
        or predecessor.get("post_merge_assurance", {}).get("conclusion") != "success"
    ):
        raise ExitContractError("accepted ST08_15C predecessor binding mismatch")
    registered = _load_json(root / ST08_15C_EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    if (
        registered.get("lifecycle_state")
        != "RELEASED_VERIFIED_AND_HOSTED_EVIDENCE_CLOSED"
        or registered.get("technical_status") != "PASS"
    ):
        raise ExitContractError("ST08_15C registered evidence is not technically closed")
    observed = contract.get("post_release_observations", {})
    release = observed.get("GitHub_release", {})
    exact = {
        "repository": "Vanargo/ML-CRA",
        "release_id": 411733338,
        "tag": "v0.1.1",
        "target_commit": "1cfa920ec91d85341525f1ca6ef57a060dcb9cce",
        "git_tree": "180aa516153724643d916f0db615f0adf333e23a",
        "published_at": "2026-10-13T13:57:53Z",
        "draft": False,
        "prerelease": False,
        "immutable": True,
    }
    if any(release.get(key) != value for key, value in exact.items()):
        raise ExitContractError("v0.1.1 release observation mismatch")
    registered_assets = registered.get("release", {}).get("assets", {})
    assets = release.get("assets", [])
    if len(assets) != 3 or sum(item.get("download_count", -1) for item in assets) != 0:
        raise ExitContractError("release assets or observed download counts mismatch")
    for item in assets:
        prior = registered_assets.get(item.get("name"), {})
        if (
            prior.get("sha256") != item.get("sha256")
            or prior.get("size_bytes") != item.get("size_bytes")
        ):
            raise ExitContractError(f"release asset differs from ST08_15C evidence: {item}")
    feedback = observed.get("feedback_and_security", {})
    if (
        feedback.get("user_authored_GitHub_issues") != 0
        or feedback.get("open_Dependabot_security_alerts") != 0
        or feedback.get("open_Dependabot_version_update_PRs") != 9
        or feedback.get("release_asset_downloads_total") != 0
        or feedback.get("operational_adoption_evidence") != "NOT_AVAILABLE"
        or observed.get("review_verdict") != "NO_NAMED_V1_0_0_EXIT_CRITERION_FAILED"
    ):
        raise ExitContractError("post-release feedback, security or uncertainty classification mismatch")


def validate_decision_matrix(matrix: Mapping[str, Any]) -> dict[str, Any]:
    if matrix.get("method") != "weighted_sum_with_ordinal_1_to_5_scores_and_predeclared_criteria":
        raise ExitContractError("unexpected decision-matrix method")
    criteria = matrix.get("criteria", [])
    options = matrix.get("options", [])
    criterion_ids = _unique(
        (str(row.get("criterion_id", "")) for row in criteria), "criterion"
    )
    weights = {row["criterion_id"]: Decimal(str(row["weight"])) for row in criteria}
    if len(criteria) != 4 or sum(weights.values()) != Decimal("1.00"):
        raise ExitContractError("decision-matrix criteria or weights mismatch")
    _unique((str(row.get("option_id", "")) for row in options), "option")
    scores: dict[str, Decimal] = {}
    selected: list[str] = []
    for option in options:
        option_scores = option.get("scores", {})
        if set(option_scores) != set(criterion_ids):
            raise ExitContractError("decision scores are incomplete")
        if any(not isinstance(value, int) or not 1 <= value <= 5 for value in option_scores.values()):
            raise ExitContractError("decision score outside 1..5")
        recomputed = sum(weights[key] * Decimal(str(option_scores[key])) for key in criterion_ids)
        if recomputed.quantize(Decimal("0.01")) != Decimal(str(option["weighted_score"])):
            raise ExitContractError(f"weighted score mismatch: {option.get('option_id')}")
        scores[option["option_id"]] = recomputed
        if option.get("disposition") == "selected":
            selected.append(option["option_id"])
    winner = max(scores, key=scores.get)
    if winner != "O04" or selected != ["O04"] or matrix.get("selected_option") != "O04":
        raise ExitContractError("finite three-block exit plan is not the unique winner")
    return {"criteria": 4, "options": 4, "selected": winner}


def _validate_terminal_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    terminal = contract.get("terminal_product_definition", {})
    if (
        terminal.get("target_version") != "1.0.0"
        or len(terminal.get("required_product_surface", [])) != 8
        or len(terminal.get("explicit_non_goals", [])) != 6
        or "project-development goal is complete" not in terminal.get("completion_semantics", "")
    ):
        raise ExitContractError("terminal product definition mismatch")
    public = contract.get("public_contract_freeze", {})
    if (
        public.get("commands") != ["mlcra audit", "mlcra verify", "mlcra doctor", "mlcra dashboard"]
        or len(public.get("claim_schemas", [])) != 2
        or set(public.get("exit_codes", {})) != {"0", "2", "3", "4", "5", "6"}
        or public.get("maturity_classifier_at_1_0_0")
        != "Development Status :: 5 - Production/Stable"
    ):
        raise ExitContractError("frozen public contract mismatch")
    criteria = contract.get("v1_0_0_exit_criteria", [])
    if len(criteria) != 7 or [row.get("criterion_id") for row in criteria] != [
        f"EXIT-{index:02d}" for index in range(1, 8)
    ]:
        raise ExitContractError("v1.0.0 exit criteria mismatch")
    plan = contract.get("finite_exit_plan", {})
    blocks = plan.get("blocks", [])
    expected_tasks = [
        "ST08_16A_v1_0_0_candidate_finalization",
        "ST08_16B_v1_0_0_final_reaudit_and_security_preflight",
        "ST08_16C_v1_0_0_GitHub_execution",
    ]
    if (
        plan.get("ordinary_blocks_after_ST08_16_acceptance") != 3
        or [row.get("task_id") for row in blocks] != expected_tasks
        or [row.get("status") for row in blocks] != ["proposed_not_authorized"] * 3
        or not str(plan.get("additional_0_x_policy", "")).startswith("forbidden_without_a_named_failed_EXIT_criterion")
        or plan.get("feature_expansion_before_1_0_0") != "forbidden"
        or plan.get("automatic_successor_after_v1_0_0") != "none"
    ):
        raise ExitContractError("finite exit plan was expanded, reordered or authorized")
    policy = contract.get("dependency_and_feedback_policy", {})
    if (
        policy.get("ordinary_version_update_PRs")
        != "maintenance_backlog_not_a_release_blocker_when_exact_locked_audits_and_supported_cell_regressions_pass"
        or len(policy.get("blocking_conditions", [])) != 4
        or "not a prerequisite" not in policy.get("usage_evidence_rule", "")
    ):
        raise ExitContractError("dependency or usage-evidence policy mismatch")
    return {"target": "1.0.0", "exit_criteria": 7, "future_blocks": 3}


def _scope_rows(root: Path) -> list[tuple[str, str]]:
    fields, rows = _load_csv(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if fields != ["change_kind", "relative_path", "reason"]:
        raise ExitContractError("unexpected ST08_16 change-scope schema")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def validate_contract_bindings(
    contract: Mapping[str, Any],
    root: Path = PROJECT_ROOT,
    workflow_text: str | None = None,
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_16_v0_1_1_post_release_review_and_v1_0_0_exit_contract_design":
        raise ExitContractError("unexpected task identifier")
    if contract.get("profile") != "CHANGE":
        raise ExitContractError("profile must be CHANGE")
    _validate_authority(contract)
    _validate_baseline(contract, root)
    _validate_predecessor_and_release(contract, root)
    decision = validate_decision_matrix(contract.get("decision_matrix", {}))
    terminal = _validate_terminal_contract(contract)
    manifest = validate_manifest(root, contract)
    expected_scope = [
        (row["change_kind"], row["relative_path"])
        for row in contract.get("planned_changes", [])
    ]
    observed_scope = _scope_rows(root)
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise ExitContractError("actual change scope differs from planned changes")
    workflow_text = workflow_text if workflow_text is not None else (
        root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)
    ).read_text(encoding="utf-8")
    required_workflow = [
        "st08_16_v1_0_0_exit_contract_assurance.py contract",
        "st08_16_v1_0_0_exit_contract_assurance.py mutations",
        "tests.test_v1_0_0_exit_contract_st08_16",
        "st08_16_v1_0_0_exit_contract_assurance.py final-evidence",
    ]
    missing = [token for token in required_workflow if token not in workflow_text]
    if missing:
        raise ExitContractError(f"workflow omits ST08_16 control: {missing}")
    for forbidden in ["contents: write", "id-token: write", "gh release create", "pypa/gh-action-pypi-publish"]:
        if forbidden in workflow_text:
            raise ExitContractError(f"workflow gained forbidden authority: {forbidden}")
    for relative in [ROADMAP_PATH, STAGE_PATH]:
        text = (root / relative.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
        for token in [
            contract["task_id"],
            "ACCEPTED_BY_JOHN: ST08_15C_v0_1_1_GitHub_execution",
            "ST08_16A_v1_0_0_candidate_finalization",
            "ordinary_blocks_after_ST08_16_acceptance: 3",
        ]:
            if token not in text:
                raise ExitContractError(f"canonical registration missing: {relative}/{token}")
    sources = contract.get("authoritative_support", [])
    if len(sources) != 8:
        raise ExitContractError("authoritative source set mismatch")
    uris = {row.get("uri") for row in sources}
    for uri in {
        "https://semver.org/",
        "https://packaging.python.org/en/latest/specifications/version-specifiers/",
        "https://pypi.org/classifiers/",
        "https://csrc.nist.gov/pubs/sp/800/218/final",
        "https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases",
        "https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-version-updates",
    }:
        if uri not in uris:
            raise ExitContractError(f"authoritative source omitted: {uri}")
    return {
        "status": "PASS",
        "decision": decision,
        "terminal": terminal,
        "manifest": manifest,
        "planned_changes": len(expected_scope),
        "future_blocks_authorized": 0,
    }


def run_registered_mutations(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    workflow = (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    mutation_ids = contract.get("negative_mutations", [])
    rejected: list[str] = []
    for mutation_id in mutation_ids:
        mutated = copy.deepcopy(contract)
        mutated_workflow = workflow
        if mutation_id == "authorize_future_block":
            mutated["authority"]["future_block_authorized"] = True
        elif mutation_id == "change_terminal_version":
            mutated["terminal_product_definition"]["target_version"] = "1.1.0"
        elif mutation_id == "permit_routine_additional_0_x":
            mutated["finite_exit_plan"]["additional_0_x_policy"] = "permitted"
        elif mutation_id == "remove_public_contract_command":
            mutated["public_contract_freeze"]["commands"].pop()
        elif mutation_id == "treat_version_update_PR_as_security_alert":
            mutated["post_release_observations"]["feedback_and_security"]["open_Dependabot_security_alerts"] = 9
        elif mutation_id == "claim_operational_adoption_from_zero_downloads":
            mutated["post_release_observations"]["feedback_and_security"]["operational_adoption_evidence"] = "PROVEN"
        elif mutation_id == "omit_exit_criterion":
            mutated["v1_0_0_exit_criteria"].pop()
        elif mutation_id == "remove_hosted_workflow_gate":
            mutated_workflow = workflow.replace(
                "python scripts/st08_16_v1_0_0_exit_contract_assurance.py final-evidence",
                "# removed ST08_16 final-evidence gate",
            )
        else:
            raise ExitContractError(f"unknown registered mutation: {mutation_id}")
        try:
            validate_contract_bindings(mutated, root, mutated_workflow)
        except ExitContractError:
            rejected.append(mutation_id)
        else:
            raise ExitContractError(f"registered mutation was accepted: {mutation_id}")
    return {"status": "PASS", "registered": len(mutation_ids), "rejected": len(rejected), "mutation_ids": rejected}


def validate_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    contract_result = validate_contract_bindings(contract, root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    if evidence.get("task_id") != contract.get("task_id"):
        raise ExitContractError("evidence task identifier mismatch")
    if evidence.get("lifecycle_state") not in {
        "CONTRACT_DESIGNED_PENDING_HOSTED_ASSURANCE_AND_JOHN_ACCEPTANCE",
        "CONTRACT_DESIGNED_HOSTED_ASSURANCE_CLOSED_PENDING_JOHN_ACCEPTANCE",
    }:
        raise ExitContractError("evidence lifecycle state mismatch")
    if evidence.get("technical_status") != "PASS":
        raise ExitContractError("evidence technical status must be PASS")
    readiness = evidence.get("readiness")
    hosted = evidence.get("hosted_assurance", {})
    if evidence["lifecycle_state"].startswith("CONTRACT_DESIGNED_PENDING"):
        if readiness != "NOT_READY" or hosted.get("status") != "PENDING":
            raise ExitContractError("prepared evidence overstates hosted readiness")
    else:
        if readiness != "READY_FOR_JOHN_ACCEPTANCE" or hosted.get("status") != "PASS":
            raise ExitContractError("closed evidence lacks hosted assurance")
        if (
            not isinstance(hosted.get("run_id"), int)
            or not isinstance(hosted.get("job_id"), int)
            or hosted.get("event") != "pull_request"
            or hosted.get("conclusion") != "success"
            or hosted.get("required_step")
            != "Validate the finite v1.0.0 exit contract"
            or hosted.get("required_step_conclusion") != "success"
            or hosted.get("primary_steps") != 23
            or not isinstance(hosted.get("head_sha"), str)
            or len(hosted["head_sha"]) != 40
            or any(character not in "0123456789abcdef" for character in hosted["head_sha"])
            or hosted.get("run_url")
            != f"https://github.com/Vanargo/ML-CRA/actions/runs/{hosted['run_id']}"
            or hosted.get("job_url")
            != f"{hosted['run_url']}/job/{hosted['job_id']}"
        ):
            raise ExitContractError("closed evidence hosted-run binding mismatch")
    if evidence.get("manifest") != contract_result["manifest"]:
        raise ExitContractError("evidence manifest summary mismatch")
    checks = evidence.get("checks", [])
    if not checks or any(row.get("status") not in {"PASS", "FAIL", "SKIPPED"} for row in checks):
        raise ExitContractError("evidence check disposition mismatch")
    failures = [row for row in checks if row.get("status") == "FAIL"]
    if failures != [
        {
            "check_id": "pilot_full_historical_aggregate",
            "status": "FAIL",
            "result": "current structural and scientific checks pass, but the aggregate command retains accepted historical FAIL gate records and exits 1",
            "disposition": "NON_BLOCKING_HISTORICAL_RECORDS_NOT_REWRITTEN",
        }
    ]:
        raise ExitContractError("evidence contains an unapproved failed check")
    if evidence.get("actions", {}) != {
        "product_source_changes": 0,
        "scientific_artifact_changes": 0,
        "training_runs": 0,
        "tag_or_release_actions": 0,
        "TestPyPI_or_PyPI_uploads": 0,
        "future_blocks_authorized": 0,
    }:
        raise ExitContractError("evidence action boundary mismatch")
    if evidence.get("checkpoint", {}).get("status") != "SKIPPED":
        raise ExitContractError("checkpoint disposition mismatch")
    return {
        "status": "PASS",
        "lifecycle_state": evidence["lifecycle_state"],
        "readiness": readiness,
        "checks": len(checks),
        "future_blocks_authorized": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_16 finite v1.0.0 exit-contract assurance")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ["contract", "mutations", "write-manifest", "final-evidence"]:
        subparsers.add_parser(command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "contract":
            result = validate_contract_bindings(_load_json(CONTRACT_PATH))
        elif args.command == "mutations":
            result = run_registered_mutations()
        elif args.command == "write-manifest":
            result = write_manifest()
        else:
            result = validate_evidence()
    except (ExitContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
