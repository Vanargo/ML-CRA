from __future__ import annotations

import copy
import unittest

from scripts import (
    st08_15_v0_1_0_post_release_review_and_v0_1_1_corrective_contract_assurance
    as assurance,
)


class TestSt0815CorrectiveContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = assurance._load_json(assurance.CONTRACT_PATH)
        cls.evidence = assurance._load_json(assurance.EVIDENCE_PATH)

    def test_contract_passes(self) -> None:
        result = assurance.validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["bindings"]["corrective_release"]["target_version"], "0.1.1"
        )
        self.assertEqual(result["bindings"]["release_actions_performed"], 0)

    def test_final_evidence_passes(self) -> None:
        result = assurance.validate_final_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence"]["selected_option"], "O04")

    def test_decision_matrix_recomputes_unique_winner(self) -> None:
        result = assurance.validate_decision_matrix(self.contract["decision_matrix"])
        self.assertEqual(result["selected"], "O04")
        self.assertEqual(result["scores"]["O04"], 4.9)

    def test_registered_negative_mutations_are_rejected(self) -> None:
        result = assurance.run_mutations()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["mutations_rejected"], 10)

    def test_matrix_rejects_weight_drift(self) -> None:
        mutated = copy.deepcopy(self.contract["decision_matrix"])
        mutated["criteria"][0]["weight"] = 0.20
        with self.assertRaises(assurance.CorrectiveContractError):
            assurance.validate_decision_matrix(mutated)

    def test_contract_rejects_direct_pypi_selection(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["decision_matrix"]["selected_option"] = "O01"
        with self.assertRaises(assurance.CorrectiveContractError):
            assurance.validate_contract_bindings(mutated)

    def test_contract_rejects_future_phase_authorization(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["phase_sequence"][1]["status"] = "authorized"
        with self.assertRaises(assurance.CorrectiveContractError):
            assurance.validate_contract_bindings(mutated)

    def test_contract_rejects_release_write_workflow(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8")
        with self.assertRaises(assurance.CorrectiveContractError):
            assurance.validate_contract_bindings(
                self.contract,
                workflow_text=workflow + "\npermissions:\n  contents: write\n",
            )

    def test_evidence_rejects_product_version_change(self) -> None:
        bindings = assurance.validate_contract()["bindings"]
        mutated = copy.deepcopy(self.evidence)
        mutated["product_version_changed"] = True
        with self.assertRaises(assurance.CorrectiveContractError):
            assurance.validate_evidence_relations(mutated, self.contract, bindings)

    def test_evidence_rejects_premature_ready_state(self) -> None:
        bindings = assurance.validate_contract()["bindings"]
        mutated = copy.deepcopy(self.evidence)
        mutated["readiness"] = "READY_FOR_JOHN_ACCEPTANCE"
        with self.assertRaises(assurance.CorrectiveContractError):
            assurance.validate_evidence_relations(mutated, self.contract, bindings)


if __name__ == "__main__":
    unittest.main()
