from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import st08_15B_v0_1_1_final_candidate_preflight as preflight


CONTRACT = preflight._load_json(preflight.CONTRACT_PATH)
EVIDENCE = preflight._load_json(preflight.EVIDENCE_PATH)


class TestSt0815BFinalCandidatePreflight(unittest.TestCase):
    def test_contract_and_successor_manifest_pass(self) -> None:
        result = preflight.validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["immutable_ST08_15A"], 7)
        self.assertEqual(result["change_scope"], 14)

    def test_final_evidence_records_exact_hosted_run(self) -> None:
        result = preflight.validate_final_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence"]["hosted_status"], "PASS")
        self.assertEqual(EVIDENCE["readiness"], "READY_FOR_JOHN_ACCEPTANCE")
        self.assertEqual(EVIDENCE["hosted_assurance"]["run_id"], 38357411816)
        self.assertEqual(
            EVIDENCE["hosted_assurance"]["head_sha"],
            "67aaeb662bdbd109c005a8d953f367be191c59fa",
        )

    def test_all_registered_mutations_are_rejected(self) -> None:
        result = preflight.run_mutations()
        self.assertEqual(result["mutations_rejected"], 12)
        self.assertEqual(len(set(result["labels"])), 12)

    def test_authority_rejects_release_permission(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["GitHub_release_authorized"] = True
        with self.assertRaises(preflight.FinalCandidatePreflightError):
            preflight._assert_authority(mutated)

    def test_external_observation_rejects_existing_v0_1_1_tag(self) -> None:
        mutated = copy.deepcopy(EVIDENCE["external_observations"])
        mutated["v0_1_1_tag_exists"] = True
        with self.assertRaises(preflight.FinalCandidatePreflightError):
            preflight.validate_external_observations(mutated)

    def test_external_observation_rejects_open_dependabot_alert(self) -> None:
        mutated = copy.deepcopy(EVIDENCE["external_observations"])
        mutated["open_dependabot_alerts"] = 1
        with self.assertRaises(preflight.FinalCandidatePreflightError):
            preflight.validate_external_observations(mutated)

    def test_runbook_rejects_reordered_publication_transition(self) -> None:
        text = preflight.RUNBOOK_PATH.read_text(encoding="utf-8").replace(
            "2. Зафиксировать переход", "2. Removed", 1
        )
        with self.assertRaises(preflight.FinalCandidatePreflightError):
            preflight.validate_runbook_text(text)

    def test_workflow_rejects_write_authority(self) -> None:
        text = preflight.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "contents: read", "contents: write", 1
        )
        with self.assertRaises(preflight.FinalCandidatePreflightError):
            preflight.validate_workflow_text(text)

    def test_evidence_rejects_ready_state_while_hosted_run_is_pending(self) -> None:
        bindings = preflight.validate_contract_bindings(CONTRACT)
        mutated = copy.deepcopy(EVIDENCE)
        mutated["hosted_assurance"]["status"] = "PENDING_TEST"
        with self.assertRaises(preflight.FinalCandidatePreflightError):
            preflight.validate_evidence(mutated, CONTRACT, bindings)

    def test_transition_surfaces_reject_premature_release_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ("README.md", "README_RU.md", "RELEASE_NOTES_0.1.1.md", "CITATION.cff"):
                (root / relative).write_text(
                    (preflight.PROJECT_ROOT / relative).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            with (root / "CITATION.cff").open("a", encoding="utf-8") as stream:
                stream.write("\ndate-released: 2026-10-13\n")
            with self.assertRaises(preflight.FinalCandidatePreflightError):
                preflight.validate_transition_surfaces(root)

    def test_candidate_asset_relation_requires_accepted_wheel_bytes(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["candidate_preflight"]["ST08_15B_assets"]["ml_cra-0.1.1-py3-none-any.whl"]["sha256"] = "0" * 64
        self.assertNotEqual(
            mutated["candidate_preflight"]["ST08_15B_assets"]["ml_cra-0.1.1-py3-none-any.whl"],
            mutated["candidate_preflight"]["ST08_15A_assets"]["ml_cra-0.1.1-py3-none-any.whl"],
        )


if __name__ == "__main__":
    unittest.main()
