from __future__ import annotations

import copy
import json
import unittest

from scripts import st08_16A_v1_0_0_candidate_finalization_assurance as assurance


CONTRACT = json.loads(assurance.CONTRACT_PATH.read_text(encoding="utf-8"))


class TestSt0816ACandidateFinalization(unittest.TestCase):
    def test_metadata_and_frozen_contract_pass(self) -> None:
        result = assurance.validate_contract_bindings(CONTRACT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["metadata"]["version"], "1.0.0")
        self.assertEqual(result["candidate_asset_builds"], 0)
        self.assertEqual(result["release_actions"], 0)

    def test_registered_mutations_are_rejected(self) -> None:
        result = assurance.run_mutations()
        self.assertEqual(result["registered"], 10)
        self.assertEqual(result["rejected"], 10)

    def test_final_evidence_is_local_pending_hosted_assurance(self) -> None:
        result = assurance.validate_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["readiness"], "NOT_READY")
        self.assertEqual(result["candidate_asset_builds"], 0)

    def test_future_block_authority_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["ST08_16B_authorized"] = True
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(mutated)

    def test_candidate_build_authority_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["candidate_asset_build_authorized"] = True
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(mutated)

    def test_public_command_expansion_is_rejected(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["frozen_public_contract"]["commands"].append("mlcra serve")
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(mutated)

    def test_release_date_is_absent(self) -> None:
        citation = (assurance.PROJECT_ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertNotIn("date-released:", citation)

    def test_version_surfaces_are_consistent(self) -> None:
        result = assurance.validate_metadata()
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["behavior_changes"], 0)

    def test_workflow_must_include_final_evidence_gate(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "python scripts/st08_16A_v1_0_0_candidate_finalization_assurance.py final-evidence",
            "# removed ST08_16A final-evidence gate",
        )
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)


if __name__ == "__main__":
    unittest.main()
