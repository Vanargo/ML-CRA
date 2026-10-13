from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts import st08_15A_v0_1_1_corrective_candidate_assurance as assurance


CONTRACT = assurance._load_json(assurance.CONTRACT_PATH)


class ST0815ACorrectiveCandidateTests(unittest.TestCase):
    def test_01_metadata_passes(self) -> None:
        result = assurance.validate_metadata()
        self.assertEqual(result["version"], "0.1.1")
        self.assertTrue(result["release_ready"])
        self.assertEqual(result["release_blockers"], [])
        self.assertEqual(result["release_readiness_scope"], assurance.READINESS_SCOPE)

    def test_02_contract_and_manifest_pass(self) -> None:
        result = assurance.validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bindings"]["protected"]["expected"], 18)

    def test_03_final_evidence_passes(self) -> None:
        result = assurance.validate_final_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence"]["release_actions_performed"], 0)

    def test_04_registered_mutations_are_rejected(self) -> None:
        result = assurance.run_mutations(CONTRACT)
        self.assertEqual(result, {"status": "PASS", "mutations": 10, "rejected": 10})

    def test_05_authority_rejects_release_permission(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["GitHub_release_authorized"] = True
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_metadata(contract=mutated)

    def test_06_citation_rejects_release_date(self) -> None:
        citation = assurance._parse_cff(assurance.CITATION_PATH)
        citation["date-released"] = "2026-10-09"
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_metadata(citation=citation)

    def test_07_doctor_scope_is_required(self) -> None:
        source = assurance.APPLICATION_PATH.read_text(encoding="utf-8")
        source = source.replace(assurance.READINESS_SCOPE, "removed_scope")
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_metadata(application_text=source)

    def test_08_existing_doctor_keys_remain_registered(self) -> None:
        preserved = set(CONTRACT["corrective_semantics"]["preserved_doctor_keys"])
        self.assertIn("release_ready", preserved)
        self.assertIn("release_blockers", preserved)
        self.assertEqual(CONTRACT["corrective_semantics"]["added_doctor_key"], "release_readiness_scope")

    def test_09_workflow_rejects_release_command(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8") + "\n# gh release create v0.1.1\n"
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)

    def test_10_scope_rejects_omitted_path(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["planned_changes"].pop()
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_contract_bindings(mutated)

    def test_11_asset_validator_rejects_wrong_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ["wrong.tar.gz", "wrong.whl", "SHA256SUMS"]:
                (root / name).write_bytes(b"fixture")
            with self.assertRaises(assurance.CorrectiveCandidateError):
                assurance.validate_candidate_assets(root / "wrong.tar.gz", root / "wrong.whl", root / "SHA256SUMS")

    def test_12_predecessor_notes_are_immutable(self) -> None:
        self.assertEqual(
            assurance._sha256_file(assurance.PROJECT_ROOT / "RELEASE_NOTES_0.1.0.md"),
            CONTRACT["immutable_release_0_1_0"]["release_notes_sha256"],
        )

    def test_13_hosted_pending_cannot_be_ready_for_acceptance(self) -> None:
        evidence = assurance._load_json(assurance.EVIDENCE_PATH)
        evidence["hosted_assurance"]["status"] = "PENDING_TEST"
        evidence["readiness"] = "READY_FOR_JOHN_ACCEPTANCE"
        bindings = assurance.validate_contract_bindings(CONTRACT)
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_evidence(evidence, CONTRACT, bindings)

    def test_14_clean_install_rejects_predecessor_wheel(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "$wheel = Get-ChildItem -LiteralPath dist/st08_15A-ci -Filter *.whl",
            "$wheel = Get-ChildItem -LiteralPath dist/st08_14C-ci -Filter *.whl",
        )
        with self.assertRaises(assurance.CorrectiveCandidateError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)


if __name__ == "__main__":
    unittest.main()
