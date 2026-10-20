from __future__ import annotations

import copy
import json
import unittest

from scripts import st08_16_v1_0_0_exit_contract_assurance as assurance


CONTRACT = json.loads(assurance.CONTRACT_PATH.read_text(encoding="utf-8"))


class TestSt0816ExitContract(unittest.TestCase):
    def test_contract_and_successor_manifest_pass(self) -> None:
        result = assurance.validate_contract_bindings(CONTRACT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["terminal"]["future_blocks"], 3)
        self.assertEqual(result["future_blocks_authorized"], 0)

    def test_registered_baseline_metadata_remains_bound_after_successor(self) -> None:
        assurance._validate_baseline(CONTRACT, assurance.PROJECT_ROOT)

    def test_registered_mutations_are_all_rejected(self) -> None:
        result = assurance.run_registered_mutations()
        self.assertEqual(result["registered"], 8)
        self.assertEqual(result["rejected"], 8)

    def test_final_evidence_is_hosted_closed_pending_John_acceptance(self) -> None:
        result = assurance.validate_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["lifecycle_state"],
            "CONTRACT_DESIGNED_HOSTED_ASSURANCE_CLOSED_PENDING_JOHN_ACCEPTANCE",
        )
        self.assertEqual(result["readiness"], "READY_FOR_JOHN_ACCEPTANCE")
        self.assertEqual(result["future_blocks_authorized"], 0)

    def test_future_authority_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["future_block_authorized"] = True
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(mutated)

    def test_fourth_ordinary_future_block_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["finite_exit_plan"]["blocks"].append(
            {
                "order": 4,
                "task_id": "ST08_16D_more_release_work",
                "purpose": "unbounded continuation",
                "status": "proposed_not_authorized",
            }
        )
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(mutated)

    def test_routine_additional_zero_release_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["finite_exit_plan"]["additional_0_x_policy"] = "permitted"
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(mutated)

    def test_version_update_backlog_cannot_be_relabelled_security_alerts(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        feedback = mutated["post_release_observations"]["feedback_and_security"]
        feedback["open_Dependabot_security_alerts"] = feedback["open_Dependabot_version_update_PRs"]
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(mutated)

    def test_zero_downloads_cannot_prove_adoption(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["post_release_observations"]["feedback_and_security"]["operational_adoption_evidence"] = "PROVEN"
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(mutated)

    def test_public_command_removal_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["public_contract_freeze"]["commands"].remove("mlcra dashboard")
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(mutated)

    def test_workflow_must_include_final_evidence_gate(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "python scripts/st08_16_v1_0_0_exit_contract_assurance.py final-evidence",
            "# removed ST08_16 final-evidence gate",
        )
        with self.assertRaises(assurance.ExitContractError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)


if __name__ == "__main__":
    unittest.main()
