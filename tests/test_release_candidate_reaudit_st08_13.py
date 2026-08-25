from __future__ import annotations

import copy
import unittest

from scripts import st08_13_release_candidate_reaudit as reaudit


CONTRACT = reaudit._load_json(reaudit.CONTRACT_PATH)
EVIDENCE = reaudit._load_json(reaudit.EVIDENCE_PATH)
REQUIREMENTS = reaudit._load_requirements()


class ST0813ReleaseCandidateReauditTests(unittest.TestCase):
    def validate(self, evidence: dict) -> dict:
        return reaudit.validate_evidence_relations(evidence, CONTRACT, REQUIREMENTS)

    def test_registered_evidence_and_repository_bindings_pass(self) -> None:
        result = reaudit.validate_registered_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["relations"]["requirements"], 24)
        self.assertEqual(result["bindings"]["protected"], 18)

    def test_duplicate_requirement_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["requirement_results"][-1]["requirement_id"] = "ST08-REQ-23"
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_missing_requirement_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["requirement_results"].pop()
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_mandatory_requirement_cannot_be_skipped(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["requirement_results"][0]["status"] = "SKIPPED"
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_silent_non_pass_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        row = next(row for row in mutated["requirement_results"] if row["status"] == "FAIL")
        row["finding_ids"] = []
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_dimension_overstatement_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        row = next(row for row in mutated["dimension_results"] if row["dimension_id"] == "D03")
        row["status"] = "PASS"
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_project_completion_overstatement_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["aggregate_verdict"]["project_completion_verdict"] = "PASS"
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_status_count_overstatement_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["aggregate_verdict"]["requirement_status_counts"]["PASS"] += 1
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_external_gate_overstatement_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["external_release_gates"]["hosted_CI"] = "PASS"
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_external_action_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["external_release_gates"]["external_actions_performed"] = 1
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_ST08_14_authorization_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["next_block_reference"]["status"] = "authorized"
        with self.assertRaises(reaudit.ReauditValidationError):
            self.validate(mutated)

    def test_CI_omission_is_rejected(self) -> None:
        without_st08_13 = reaudit.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "scripts/st08_13_release_candidate_reaudit.py", "removed-validator"
        )
        with self.assertRaises(reaudit.ReauditValidationError):
            reaudit.validate_repository_bindings(CONTRACT, EVIDENCE, without_st08_13)


if __name__ == "__main__":
    unittest.main()
