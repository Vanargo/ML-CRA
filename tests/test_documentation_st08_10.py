from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import st08_10_documentation_assurance as assurance


CONTRACT = json.loads(assurance.CONTRACT_PATH.read_text(encoding="utf-8"))


class TestSt0810Documentation(unittest.TestCase):
    def test_source_contract_passes(self) -> None:
        result = assurance.validate_source()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["protected"], {"expected": 18, "mismatches": 0})

    def test_published_source_contract_passes(self) -> None:
        result = assurance.validate_source(inventory="published")
        self.assertEqual(result["status"], "PASS")
        self.assertGreater(result["paths"]["policy_excluded_paths"], 0)

    def test_bilingual_commands_are_exact(self) -> None:
        result = assurance.validate_bilingual_documents()
        self.assertTrue(result["command_parity"])
        self.assertEqual(result["powershell_blocks_per_language"], 3)

    def test_missing_section_marker_is_rejected(self) -> None:
        english = assurance.README_EN.read_text(encoding="utf-8").replace(
            "<!-- ST08-10:quickstart -->", "<!-- removed marker -->", 1
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "README.md"
            path.write_text(english, encoding="utf-8")
            with self.assertRaises(assurance.DocumentationAssuranceError):
                assurance.validate_bilingual_documents(path, assurance.README_RU, CONTRACT)

    def test_changed_language_command_is_rejected(self) -> None:
        russian = assurance.README_RU.read_text(encoding="utf-8").replace(
            "--format json", "--format text", 1
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "README_RU.md"
            path.write_text(russian, encoding="utf-8")
            with self.assertRaises(assurance.DocumentationAssuranceError):
                assurance.validate_bilingual_documents(assurance.README_EN, path, CONTRACT)

    def test_broken_local_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=assurance.PROJECT_ROOT) as temporary:
            path = Path(temporary) / "broken.md"
            path.write_text("[missing](definitely-missing.txt)\n", encoding="utf-8")
            with self.assertRaises(assurance.DocumentationAssuranceError):
                assurance.validate_markdown_links([path])

    def test_obsolete_current_path_is_rejected(self) -> None:
        mutated = json.loads(assurance.PATH_CONTRACT_PATH.read_text(encoding="utf-8"))
        mutated["current_path_reconciliation"][0]["forbidden_current_fragments"] = [
            "docs/archive/reports/REPORT_04_project_definition.md"
        ]
        with self.assertRaises(assurance.DocumentationAssuranceError):
            assurance.validate_current_path_reconciliation(mutated)

    def test_metadata_uses_root_readme(self) -> None:
        self.assertEqual(assurance.validate_project_metadata()["readme"], "README.md")

    def test_doctor_has_no_completed_documentation_blocker(self) -> None:
        source = assurance.APPLICATION.read_text(encoding="utf-8")
        self.assertNotIn("RU_and_EN_documentation_deferred_to_ST08_10", source)


if __name__ == "__main__":
    unittest.main()
