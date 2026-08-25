from __future__ import annotations

import copy
import unittest

from scripts import agent_verify
from scripts import st08_13B_public_repository_assurance as assurance


CONTRACT = assurance._load_json(assurance.CONTRACT_PATH)


class AgentVerifierRepositoryInventoryTests(unittest.TestCase):
    def test_git_administrative_tree_is_derived_local_state(self) -> None:
        self.assertTrue(agent_verify.is_derived(".git/config"))


def final_evidence_fixture() -> dict:
    commit = "a" * 40
    return {
        "schema_version": "st08_13B_public_repository_hosted_CI_and_security_evidence_v01",
        "evidence_id": "st08_13B_public_repository_hosted_CI_and_security_evidence_v01",
        "task_id": CONTRACT["task_id"],
        "recorded_at": "2026-08-24",
        "profile": "CHANGE",
        "status": "external_controls_observed_not_release",
        "publication_tree": {"paths": 1, "path_list_sha256": "b" * 64},
        "external_evidence": {
            "repository": {
                "id": 1,
                "node_id": "R_fixture",
                "owner": "Vanargo",
                "name": "ML-CRA",
                "full_name": "Vanargo/ML-CRA",
                "private": False,
                "visibility": "public",
                "default_branch": "main",
                "html_url": "https://github.com/Vanargo/ML-CRA",
                "archived": False,
                "disabled": False,
            },
            "git": {
                "bootstrap_commit_sha": commit,
                "branch": "main",
                "remote_url": "https://github.com/Vanargo/ML-CRA.git",
            },
            "hosted_ci": {
                "run_id": 1,
                "head_sha": commit,
                "event": "push",
                "status": "completed",
                "conclusion": "success",
                "html_url": "https://github.com/Vanargo/ML-CRA/actions/runs/1",
                "job_name": "assurance",
                "job_conclusion": "success",
            },
            "repository_security": {
                "secret_scanning": "enabled",
                "secret_scanning_push_protection": "enabled",
                "private_vulnerability_reporting": True,
                "vulnerability_alerts": True,
                "main_branch_protection": {
                    "enabled": True,
                    "required_status_check": "assurance",
                    "strict_status_checks": True,
                    "require_pull_request": True,
                    "required_approving_review_count": 0,
                    "required_conversation_resolution": True,
                    "required_linear_history": True,
                    "enforce_admins": True,
                    "allow_force_pushes": False,
                    "allow_deletions": False,
                },
            },
            "remote_recovery": {
                "fresh_clone_verified": True,
                "tracked_paths": 1,
                "path_list_sha256": "b" * 64,
                "content_hash_mismatches": 0,
            },
            "external_actions": {
                "repositories_created": 1,
                "pushes": 1,
                "workflow_runs_observed": 1,
                "tags_created": 0,
                "GitHub_releases_created": 0,
                "packages_published": 0,
            },
        },
        "technical_status": "PASS",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
        "release_performed": False,
    }


class ST0813BPublicRepositoryAssuranceTests(unittest.TestCase):
    def test_publication_tree_and_contract_pass(self) -> None:
        result = assurance.validate_publication_tree()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bindings"]["protected"], {"expected": 18, "mismatches": 0})

    def test_external_evidence_fixture_passes(self) -> None:
        result = assurance.validate_external_evidence(final_evidence_fixture(), CONTRACT)
        self.assertEqual(result["repository"], "Vanargo/ML-CRA")

    def test_private_repository_is_rejected(self) -> None:
        evidence = final_evidence_fixture()
        evidence["external_evidence"]["repository"]["private"] = True
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_external_evidence(evidence, CONTRACT)

    def test_failed_hosted_CI_is_rejected(self) -> None:
        evidence = final_evidence_fixture()
        evidence["external_evidence"]["hosted_ci"]["conclusion"] = "failure"
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_external_evidence(evidence, CONTRACT)

    def test_secret_scanning_disabled_is_rejected(self) -> None:
        evidence = final_evidence_fixture()
        evidence["external_evidence"]["repository_security"]["secret_scanning"] = "disabled"
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_external_evidence(evidence, CONTRACT)

    def test_private_reporting_disabled_is_rejected(self) -> None:
        evidence = final_evidence_fixture()
        evidence["external_evidence"]["repository_security"]["private_vulnerability_reporting"] = False
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_external_evidence(evidence, CONTRACT)

    def test_branch_protection_disabled_is_rejected(self) -> None:
        evidence = final_evidence_fixture()
        evidence["external_evidence"]["repository_security"]["main_branch_protection"]["enabled"] = False
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_external_evidence(evidence, CONTRACT)

    def test_release_action_is_rejected(self) -> None:
        evidence = final_evidence_fixture()
        evidence["external_evidence"]["external_actions"]["GitHub_releases_created"] = 1
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_external_evidence(evidence, CONTRACT)

    def test_authority_overstatement_is_rejected(self) -> None:
        contract = copy.deepcopy(CONTRACT)
        contract["authority"]["GitHub_release_authorized"] = True
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_contract_bindings(contract)

    def test_workflow_omission_is_rejected(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "scripts/st08_13B_public_repository_assurance.py publication-tree", "removed-validator"
        )
        with self.assertRaises(assurance.PublicRepositoryAssuranceError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)


if __name__ == "__main__":
    unittest.main()
