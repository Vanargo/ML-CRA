from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts import st08_15C_v0_1_1_GitHub_execution_assurance as assurance


CONTRACT = assurance._load_json(assurance.CONTRACT_PATH)
EVIDENCE = assurance._load_json(assurance.EVIDENCE_PATH)


class TestSt0815CGitHubExecution(unittest.TestCase):
    def test_contract_and_release_state_pass(self) -> None:
        result = assurance.validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["release_state"]["version"], "0.1.1")
        self.assertEqual(result["planned_change_paths"], 18)
        self.assertEqual(result["protected"]["expected"], 18)

    def test_current_evidence_is_fail_closed(self) -> None:
        result = assurance.validate_final_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertIn(
            result["evidence"]["lifecycle_state"],
            (assurance.PREPARED, assurance.RELEASED_PENDING, assurance.RELEASED_CLOSED),
        )
        expected_readiness = (
            "READY_FOR_JOHN_ACCEPTANCE"
            if result["evidence"]["lifecycle_state"] == assurance.RELEASED_CLOSED
            else "NOT_READY"
        )
        self.assertEqual(result["evidence"]["readiness"], expected_readiness)
        self.assertEqual(
            EVIDENCE["release_performed"],
            EVIDENCE["lifecycle_state"] != assurance.PREPARED,
        )

    def test_all_registered_mutations_are_rejected(self) -> None:
        result = assurance.run_mutations()
        self.assertEqual(result["mutations_rejected"], 12)
        self.assertEqual(len(set(result["labels"])), 12)

    def test_authority_rejects_PyPI_permission(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["PyPI_publication_authorized"] = True
        with self.assertRaises(assurance.GitHubExecutionError):
            assurance._assert_authority(mutated)

    def test_authority_requires_separate_merge_confirmation(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["protected_main_merge_requires_separate_John_confirmation"] = False
        with self.assertRaises(assurance.GitHubExecutionError):
            assurance._assert_authority(mutated)

    def test_release_state_rejects_guessed_citation_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ["README.md", "README_RU.md", "RELEASE_NOTES_0.1.1.md", "SECURITY.md", "CITATION.cff", "pyproject.toml"]:
                (root / relative).write_text(
                    (assurance.PROJECT_ROOT / relative).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            with (root / "CITATION.cff").open("a", encoding="utf-8") as stream:
                stream.write("\ndate-released: 2026-10-13\n")
            with self.assertRaises(assurance.GitHubExecutionError):
                assurance.validate_release_state(root)

    def test_workflow_rejects_release_write_authority(self) -> None:
        text = assurance.WORKFLOW_PATH.read_text(encoding="utf-8") + "\ngh release create v0.1.1\n"
        with self.assertRaises(assurance.GitHubExecutionError):
            assurance.validate_workflow_text(text)

    def test_current_evidence_rejects_release_state_contradiction(self) -> None:
        bindings = assurance.validate_contract_bindings(CONTRACT)
        mutated = copy.deepcopy(EVIDENCE)
        mutated["release_performed"] = not EVIDENCE["release_performed"]
        with self.assertRaises(assurance.GitHubExecutionError):
            assurance.validate_evidence(mutated, CONTRACT, bindings)

    def test_release_body_is_deterministic_and_binds_exact_identity(self) -> None:
        assets = assurance._validate_asset_contract(CONTRACT)
        first = assurance.render_release_body("1" * 40, "2" * 40, assets)
        second = assurance.render_release_body("1" * 40, "2" * 40, assets)
        self.assertEqual(first, second)
        self.assertIn("`" + "1" * 40 + "`", first)
        self.assertIn("`" + "2" * 40 + "`", first)
        for name in assurance.ASSET_NAMES:
            self.assertIn(name, first)

    def test_asset_contract_rejects_zero_size(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["release_assets"]["assets"][assurance.ASSET_NAMES[0]]["size_bytes"] = 0
        with self.assertRaises(assurance.GitHubExecutionError):
            assurance._validate_asset_contract(mutated)


if __name__ == "__main__":
    unittest.main()
