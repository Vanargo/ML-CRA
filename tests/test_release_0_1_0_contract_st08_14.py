from __future__ import annotations

import copy
import unittest

from scripts import st08_14_release_0_1_0_contract_assurance as assurance


CONTRACT = assurance._load_json(assurance.CONTRACT_PATH)


class ST0814Release010ContractTests(unittest.TestCase):
    def test_01_contract_and_successor_manifest_pass(self) -> None:
        result = assurance.validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bindings"]["release_scope"]["target_version"], "0.1.0")
        self.assertEqual(result["bindings"]["protected"]["expected"], 18)

    def test_02_final_evidence_passes(self) -> None:
        result = assurance.validate_final_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence"]["release_actions_performed"], 0)

    def test_03_matrix_rejects_weight_sum_mutation(self) -> None:
        mutated = copy.deepcopy(CONTRACT["decision_matrix"])
        mutated["criteria"][0]["weight"] = 0.24
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_decision_matrix(mutated)

    def test_04_matrix_rejects_score_overstatement(self) -> None:
        mutated = copy.deepcopy(CONTRACT["decision_matrix"])
        mutated["options"][0]["weighted_score"] = 5.0
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_decision_matrix(mutated)

    def test_05_matrix_rejects_direct_release_selection(self) -> None:
        mutated = copy.deepcopy(CONTRACT["decision_matrix"])
        mutated["options"][0]["disposition"] = "selected"
        mutated["options"][2]["disposition"] = "rejected"
        mutated["selected_option"] = "O01"
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_decision_matrix(mutated)

    def test_06_authority_rejects_version_change_permission(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["package_version_change_authorized"] = True
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_release_scope(mutated, assurance.PROJECT_ROOT)

    def test_07_authority_rejects_github_release_permission(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["GitHub_release_authorized"] = True
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_release_scope(mutated, assurance.PROJECT_ROOT)

    def test_08_pypi_must_remain_deferred(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["release_scope_decision"]["PyPI"]["status"] = "authorized"
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_release_scope(mutated, assurance.PROJECT_ROOT)

    def test_09_target_version_cannot_jump_to_1_0_0(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["release_scope_decision"]["first_supported_release_version"] = "1.0.0"
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_release_scope(mutated, assurance.PROJECT_ROOT)

    def test_10_required_release_asset_cannot_be_omitted(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["release_scope_decision"]["required_assets"].pop()
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_release_scope(mutated, assurance.PROJECT_ROOT)

    def test_11_future_phase_cannot_be_authorized(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["phase_sequence"][1]["status"] = "authorized"
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_release_scope(mutated, assurance.PROJECT_ROOT)

    def test_12_workflow_rejects_release_command(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8")
        workflow += "\n# gh release create v0.1.0\n"
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)

    def test_13_immutable_history_rejects_hash_mutation(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["immutable_ST08_13C"][0]["sha256"] = "0" * 64
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_contract_bindings(mutated)

    def test_14_evidence_rejects_release_action(self) -> None:
        bindings = assurance.validate_contract_bindings(CONTRACT)
        evidence = assurance._load_json(assurance.EVIDENCE_PATH)
        mutated = copy.deepcopy(evidence)
        mutated["release_actions_performed"] = 1
        with self.assertRaises(assurance.ReleaseContractError):
            assurance.validate_evidence_relations(mutated, CONTRACT, bindings)


if __name__ == "__main__":
    unittest.main()
