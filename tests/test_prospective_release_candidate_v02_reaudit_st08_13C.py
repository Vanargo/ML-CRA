from __future__ import annotations

import copy
import hashlib
import unittest

from scripts import st08_13C_prospective_release_candidate_v02_reaudit as reaudit


CONTRACT = reaudit._load_json(reaudit.CONTRACT_PATH)


def final_evidence_fixture() -> dict:
    requirement_results = []
    dimension_results = []
    for index in range(1, 25):
        dimension = f"D{((index - 1) // 3) + 1:02d}"
        requirement_results.append(
            {
                "requirement_id": f"ST08-REQ-{index:02d}",
                "dimension_id": dimension,
                "status": "PASS",
                "observed_evidence": "fixture evidence",
                "evidence_paths": ["fixture/path"],
                "verification_command_or_method": "fixture_method",
                "finding_ids": [],
            }
        )
    for index in range(1, 9):
        dimension_results.append({"dimension_id": f"D{index:02d}", "name": "fixture", "status": "PASS"})
    return {
        "schema_version": "st08_13C_prospective_release_candidate_v02_reaudit_evidence_v01",
        "task_id": CONTRACT["task_id"],
        "profile": "SCIENTIFIC_VALIDATION",
        "status": "prospective_v02_reaudit_complete_release_not_authorized",
        "candidate_manifest": {"fixture": True},
        "candidate_hosted_CI": {
            "run_id": 1,
            "head_sha": "a" * 40,
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/Vanargo/ML-CRA/actions/runs/1",
            "job_name": "assurance",
            "job_conclusion": "success",
        },
        "requirement_results": requirement_results,
        "dimension_results": dimension_results,
        "aggregate_verdict": {
            "requirement_status_counts": {"PASS": 24, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0},
            "dimension_status_counts": {"PASS": 8, "FAIL": 0, "BLOCKED": 0},
            "project_completion_verdict": "PASS",
            "external_release_readiness": "BLOCKED",
            "release_class": "not_ready",
            "release_blockers": ["John_release_authorization_not_granted"],
            "John_release_decision_required": True,
        },
        "open_findings": [],
        "historical_disposition": {
            "ST08_v01_project_completion": "FAIL_PRESERVED",
            "ST08_v01_external_release": "FAIL_PRESERVED",
            "ST08_v01_REQ08": "FAIL_PRESERVED",
            "ST08_v01_REQ12": "BLOCKED_PRESERVED",
            "ST08_13A_migration": "PASS_PRESERVED",
            "ST08_13B_external_controls": "PASS_PRESERVED",
        },
        "training_runs": 0,
        "scientific_artifact_changes": 0,
        "release_actions_performed": 0,
        "technical_status": "PASS",
        "readiness": "READY_FOR_JOHN_ACCEPTANCE",
    }


_, REQUIREMENTS = reaudit._load_csv(reaudit.REQUIREMENTS_PATH)


class ST0813CProspectiveReleaseCandidateReauditTests(unittest.TestCase):
    def validate(self, evidence: dict) -> dict:
        return reaudit.validate_evidence_relations(evidence, CONTRACT, REQUIREMENTS)

    def test_candidate_tree_and_contract_pass(self) -> None:
        result = reaudit.validate_candidate_tree()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bindings"]["requirements"]["requirements"], 24)
        self.assertEqual(result["bindings"]["protected"]["expected"], 18)

    def test_contract_hashes_use_canonical_git_blobs(self) -> None:
        requirements_payload = reaudit.release_assurance.git_index_blob_bytes(
            CONTRACT["assessment"]["requirements_path"]
        )
        self.assertEqual(
            CONTRACT["assessment"]["requirements_representation"],
            "SHA-256 over canonical Git index blob bytes",
        )
        self.assertEqual(
            hashlib.sha256(requirements_payload).hexdigest(),
            CONTRACT["assessment"]["requirements_sha256"],
        )
        self.assertEqual(
            CONTRACT["immutable_history_representation"],
            "SHA-256 over canonical Git index blob bytes",
        )
        for item in CONTRACT["immutable_history"]:
            payload = reaudit.release_assurance.git_index_blob_bytes(item["path"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), item["sha256"])

    def test_final_fixture_passes(self) -> None:
        result = self.validate(final_evidence_fixture())
        self.assertEqual(result["project_completion_verdict"], "PASS")
        self.assertEqual(result["external_release_readiness"], "BLOCKED")

    def test_duplicate_requirement_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["requirement_results"][-1]["requirement_id"] = "ST08-REQ-23"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_mandatory_skip_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["requirement_results"][0]["status"] = "SKIPPED"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_silent_non_pass_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["requirement_results"][0]["status"] = "FAIL"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_dimension_overstatement_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["requirement_results"][0]["status"] = "BLOCKED"
        mutated["requirement_results"][0]["finding_ids"] = ["F-1"]
        mutated["open_findings"] = [{"finding_id": "F-1"}]
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_project_completion_overstatement_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["aggregate_verdict"]["project_completion_verdict"] = "BLOCKED"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_release_authorization_is_not_inferred(self) -> None:
        mutated = final_evidence_fixture()
        mutated["aggregate_verdict"]["external_release_readiness"] = "PASS"
        mutated["aggregate_verdict"]["release_blockers"] = []
        mutated["aggregate_verdict"]["release_class"] = "source_release"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_failed_hosted_CI_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["candidate_hosted_CI"]["conclusion"] = "failure"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_historical_rewrite_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["historical_disposition"]["ST08_v01_REQ08"] = "PASS"
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_release_action_is_rejected(self) -> None:
        mutated = final_evidence_fixture()
        mutated["release_actions_performed"] = 1
        with self.assertRaises(reaudit.ProspectiveReauditError):
            self.validate(mutated)

    def test_workflow_omission_is_rejected(self) -> None:
        workflow = reaudit.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "scripts/st08_13C_prospective_release_candidate_v02_reaudit.py candidate-tree",
            "removed-validator",
        )
        with self.assertRaises(reaudit.ProspectiveReauditError):
            reaudit.validate_candidate_bindings(CONTRACT, workflow_text=workflow)


if __name__ == "__main__":
    unittest.main()
