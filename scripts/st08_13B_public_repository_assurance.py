from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from scripts import st08_09_release_assurance as release_assurance
except ModuleNotFoundError:  # direct execution places scripts/ first on sys.path
    import st08_09_release_assurance as release_assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "configs/project_readiness/st08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_contract_v01.json"
EVIDENCE_PATH = PROJECT_ROOT / "data_registry/st08_13B_public_repository_hosted_CI_and_security_evidence_v01.json"
MANIFEST_PATH = PROJECT_ROOT / "data_registry/st08_13B_publication_tree_manifest_v01.csv"
SCOPE_PATH = PROJECT_ROOT / "docs/agent/st08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_change_scope_v01.csv"
WORKFLOW_PATH = PROJECT_ROOT / ".github/workflows/ci.yml"
STAGE_PATH = PROJECT_ROOT / "docs/stages/stage_08_project_completion_and_release_readiness.md"
ROADMAP_PATH = PROJECT_ROOT / "roadmap.md"


class PublicRepositoryAssuranceError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PublicRepositoryAssuranceError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_list_sha256(paths: Sequence[str]) -> str:
    return hashlib.sha256("".join(f"{path}\n" for path in sorted(paths)).encode("utf-8")).hexdigest()


def _load_scope(path: Path) -> list[tuple[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if list(reader.fieldnames or []) != ["change_kind", "relative_path", "reason"]:
            raise PublicRepositoryAssuranceError("unexpected ST08_13B change-scope schema")
        rows = list(reader)
    if not rows:
        raise PublicRepositoryAssuranceError("ST08_13B change scope is empty")
    return [(row["change_kind"], row["relative_path"]) for row in rows]


def write_publication_manifest(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    public_policy = _load_json(root / release_assurance.PUBLIC_MANIFEST.relative_to(PROJECT_ROOT))
    paths = release_assurance.tracked_repository_paths(root)
    included = [
        relative
        for relative in paths
        if release_assurance.classify_public_path(relative, public_policy, root)
        in set(contract["publication_tree"]["allowed_rules"])
    ]
    exclusions = set(contract["publication_tree"]["cycle_breaking_exclusions"])
    missing = sorted(exclusions - set(included))
    if missing:
        raise PublicRepositoryAssuranceError(f"publication cycle-breaking path is not publishable: {missing}")
    rows = []
    for relative in sorted(set(included) - exclusions):
        payload = release_assurance.git_index_blob_bytes(relative, root)
        rows.append(
            {
                "relative_path": relative,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": str(len(payload)),
            }
        )
    path = root / MANIFEST_PATH.relative_to(PROJECT_ROOT)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=contract["publication_tree"]["fields"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    tracked_intent = sorted([row["relative_path"] for row in rows] + sorted(exclusions))
    return {
        "status": "PASS",
        "paths": len(tracked_intent),
        "hashed_paths": len(rows),
        "path_list_sha256": _path_list_sha256(tracked_intent),
        "manifest_sha256": _sha256(path),
    }


def validate_contract_bindings(
    contract: Mapping[str, Any],
    root: Path = PROJECT_ROOT,
    workflow_text: str | None = None,
) -> dict[str, Any]:
    if contract.get("task_id") != "ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence":
        raise PublicRepositoryAssuranceError("unexpected ST08_13B task identifier")
    if contract.get("profile") != "CHANGE":
        raise PublicRepositoryAssuranceError("ST08_13B profile must be CHANGE")
    authority = contract.get("authority")
    if not isinstance(authority, Mapping):
        raise PublicRepositoryAssuranceError("ST08_13B authority is missing")
    for key in (
        "public_repository_creation_authorized",
        "source_publication_authorized",
        "hosted_CI_execution_authorized",
        "repository_security_configuration_authorized",
    ):
        if authority.get(key) is not True:
            raise PublicRepositoryAssuranceError(f"required external authority is absent: {key}")
    for key in ("version_tag_authorized", "GitHub_release_authorized", "PyPI_publication_authorized", "scientific_change_authorized"):
        if authority.get(key) is not False:
            raise PublicRepositoryAssuranceError(f"authority boundary is overstated: {key}")
    for item in contract["immutable_ST08_13A_history"]:
        path = root / item["path"]
        payload = release_assurance.git_index_blob_bytes(item["path"], root)
        if not path.is_file() or hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise PublicRepositoryAssuranceError(f"immutable ST08_13A history changed: {item['path']}")
    protected = release_assurance.validate_protected_hashes(
        root,
        inventory="published",
        canonical_bindings=contract["protected_git_blob_bindings"],
    )
    workflow_text = workflow_text if workflow_text is not None else (root / WORKFLOW_PATH.relative_to(PROJECT_ROOT)).read_text(encoding="utf-8")
    required_workflow_tokens = [
        "st08_09_release_assurance.py source --inventory published",
        "st08_09_release_assurance.py secrets --inventory published",
        "scripts/st08_13_release_candidate_reaudit.py --inventory published",
        "scripts/st08_13B_public_repository_assurance.py publication-tree",
        "tests.test_public_repository_assurance_st08_13B",
    ]
    missing_workflow = [token for token in required_workflow_tokens if token not in workflow_text]
    if missing_workflow:
        raise PublicRepositoryAssuranceError(f"hosted workflow omits ST08_13B control: {missing_workflow}")
    release_assurance.validate_workflow(root / WORKFLOW_PATH.relative_to(PROJECT_ROOT))
    expected_scope = [(row["change_kind"], row["relative_path"]) for row in contract["planned_changes"]]
    observed_scope = _load_scope(root / SCOPE_PATH.relative_to(PROJECT_ROOT))
    if observed_scope != expected_scope or len(observed_scope) != len(set(observed_scope)):
        raise PublicRepositoryAssuranceError("ST08_13B change scope differs from the planned change set")
    for path, tokens in {
        STAGE_PATH.relative_to(PROJECT_ROOT).as_posix(): [contract["task_id"], "hosted_CI_observed"],
        ROADMAP_PATH.relative_to(PROJECT_ROOT).as_posix(): [contract["task_id"], "hosted_CI_observed"],
    }.items():
        text = (root / path).read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in text]
        if missing:
            raise PublicRepositoryAssuranceError(f"canonical document registration missing: {path}/{missing}")
    return {"historical_files": len(contract["immutable_ST08_13A_history"]), "protected": protected, "scope_paths": len(observed_scope)}


def validate_publication_tree(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    bindings = validate_contract_bindings(contract, root)
    tree = release_assurance.validate_publication_tree(root)
    if tree["cycle_breaking_exclusions"] != sorted(contract["publication_tree"]["cycle_breaking_exclusions"]):
        raise PublicRepositoryAssuranceError("publication-tree cycle-breaking exclusions differ from contract")
    return {"status": "PASS", "bindings": bindings, "publication_tree": {key: value for key, value in tree.items() if key != "included_paths"}}


def validate_external_evidence(evidence: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("schema_version") != "st08_13B_public_repository_hosted_CI_and_security_evidence_v01":
        raise PublicRepositoryAssuranceError("unexpected external evidence schema")
    if evidence.get("task_id") != contract.get("task_id") or evidence.get("profile") != "CHANGE":
        raise PublicRepositoryAssuranceError("external evidence task/profile mismatch")
    if evidence.get("status") != "external_controls_observed_not_release":
        raise PublicRepositoryAssuranceError("external evidence is not final")
    external = evidence.get("external_evidence")
    if not isinstance(external, Mapping):
        raise PublicRepositoryAssuranceError("external evidence payload is missing")
    repository = external.get("repository")
    target = contract["target_repository"]
    if not isinstance(repository, Mapping) or any(
        repository.get(key) != value
        for key, value in {
            "owner": target["owner"], "name": target["name"], "full_name": f"{target['owner']}/{target['name']}",
            "private": False, "visibility": "public", "default_branch": "main", "html_url": target["html_url"],
            "archived": False, "disabled": False,
        }.items()
    ):
        raise PublicRepositoryAssuranceError("public repository identity or state mismatch")
    git = external.get("git")
    if not isinstance(git, Mapping) or not re.fullmatch(r"[0-9a-f]{40}", str(git.get("bootstrap_commit_sha", ""))):
        raise PublicRepositoryAssuranceError("bootstrap Git commit is missing or invalid")
    if git.get("branch") != "main" or git.get("remote_url") != target["html_url"] + ".git":
        raise PublicRepositoryAssuranceError("Git remote or branch mismatch")
    hosted = external.get("hosted_ci")
    if not isinstance(hosted, Mapping) or any(
        hosted.get(key) != value
        for key, value in {"head_sha": git["bootstrap_commit_sha"], "event": "push", "status": "completed", "conclusion": "success", "job_name": "assurance", "job_conclusion": "success"}.items()
    ):
        raise PublicRepositoryAssuranceError("hosted CI observation is incomplete or unsuccessful")
    if not isinstance(hosted.get("run_id"), int) or not str(hosted.get("html_url", "")).startswith(target["html_url"] + "/actions/runs/"):
        raise PublicRepositoryAssuranceError("hosted CI run identity is invalid")
    security = external.get("repository_security")
    if not isinstance(security, Mapping):
        raise PublicRepositoryAssuranceError("repository security evidence is missing")
    required_security = {
        "secret_scanning": "enabled",
        "secret_scanning_push_protection": "enabled",
        "private_vulnerability_reporting": True,
        "vulnerability_alerts": True,
    }
    if any(security.get(key) != value for key, value in required_security.items()):
        raise PublicRepositoryAssuranceError("required repository security control is not enabled")
    protection = security.get("main_branch_protection")
    expected_protection = {
        "enabled": True, "required_status_check": "assurance", "strict_status_checks": True,
        "require_pull_request": True, "required_approving_review_count": 0,
        "required_conversation_resolution": True, "required_linear_history": True,
        "enforce_admins": True, "allow_force_pushes": False, "allow_deletions": False,
    }
    if not isinstance(protection, Mapping) or any(protection.get(key) != value for key, value in expected_protection.items()):
        raise PublicRepositoryAssuranceError("main branch protection evidence mismatch")
    recovery = external.get("remote_recovery")
    if not isinstance(recovery, Mapping) or recovery.get("fresh_clone_verified") is not True or recovery.get("content_hash_mismatches") != 0:
        raise PublicRepositoryAssuranceError("remote fresh-clone recovery is not verified")
    if recovery.get("tracked_paths") != evidence.get("publication_tree", {}).get("paths") or recovery.get("path_list_sha256") != evidence.get("publication_tree", {}).get("path_list_sha256"):
        raise PublicRepositoryAssuranceError("remote recovery tree differs from publication evidence")
    actions = external.get("external_actions")
    if not isinstance(actions, Mapping) or actions.get("repositories_created") != 1 or actions.get("pushes") < 1 or actions.get("workflow_runs_observed") < 1:
        raise PublicRepositoryAssuranceError("external action counts are incomplete")
    for key in ("tags_created", "GitHub_releases_created", "packages_published"):
        if actions.get(key) != 0:
            raise PublicRepositoryAssuranceError(f"forbidden release action recorded: {key}")
    if evidence.get("technical_status") != "PASS" or evidence.get("readiness") != "READY_FOR_JOHN_ACCEPTANCE" or evidence.get("release_performed") is not False:
        raise PublicRepositoryAssuranceError("final status or no-release boundary mismatch")
    return {"repository": repository["full_name"], "hosted_run_id": hosted["run_id"], "security_controls": len(required_security) + 1}


def validate_final_evidence(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    contract = _load_json(root / CONTRACT_PATH.relative_to(PROJECT_ROOT))
    tree_result = validate_publication_tree(root)
    evidence = _load_json(root / EVIDENCE_PATH.relative_to(PROJECT_ROOT))
    tree = tree_result["publication_tree"]
    if evidence.get("publication_tree") != {
        "paths": tree["paths"], "hashed_paths": tree["hashed_paths"],
        "path_list_sha256": tree["path_list_sha256"], "manifest_sha256": tree["manifest_sha256"],
        "cycle_breaking_exclusions": tree["cycle_breaking_exclusions"], "status": "PASS",
    }:
        raise PublicRepositoryAssuranceError("external evidence publication-tree binding mismatch")
    return {"status": "PASS", "publication_tree": tree, "external": validate_external_evidence(evidence, contract)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST08_13B public repository and hosted-control assurance")
    parser.add_argument("command", choices=("write-publication-manifest", "publication-tree", "final-evidence"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "write-publication-manifest":
            result = write_publication_manifest()
        elif args.command == "publication-tree":
            result = validate_publication_tree()
        else:
            result = validate_final_evidence()
    except (PublicRepositoryAssuranceError, release_assurance.AssuranceError, csv.Error, json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
