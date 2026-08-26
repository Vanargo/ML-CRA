from __future__ import annotations

import copy
import gzip
import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts import st08_14A_release_candidate_finalization_assurance as assurance


CONTRACT = assurance._load_json(assurance.CONTRACT_PATH)


def _write_test_sdist(path: Path, *, member_mtime: int, gzip_mtime: int, name: str = "ml_cra-0.1.0/data.txt") -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="variable-name.tar", mode="wb", fileobj=raw, mtime=gzip_mtime) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                root = tarfile.TarInfo("ml_cra-0.1.0")
                root.type = tarfile.DIRTYPE
                root.mode = 0o755
                root.mtime = member_mtime
                archive.addfile(root)
                payload = b"same semantic bytes\n"
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                member.mode = 0o644
                member.mtime = member_mtime
                member.uid = 1000
                member.gid = 1000
                member.uname = "builder"
                member.gname = "builder"
                archive.addfile(member, io.BytesIO(payload))


class ST0814AReleaseCandidateFinalizationTests(unittest.TestCase):
    def test_01_metadata_passes(self) -> None:
        result = assurance.validate_metadata()
        self.assertEqual(result["version"], "0.1.0")
        self.assertFalse(result["external_release_claimed"])

    def test_02_contract_and_manifest_pass(self) -> None:
        result = assurance.validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bindings"]["protected"]["expected"], 18)

    def test_03_final_evidence_passes(self) -> None:
        result = assurance.validate_final_evidence()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence"]["release_actions_performed"], 0)

    def test_04_authority_rejects_tag_permission(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["authority"]["version_tag_authorized"] = True
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_metadata(contract=mutated)

    def test_05_citation_rejects_release_date(self) -> None:
        citation = assurance._parse_cff(assurance.CITATION_PATH)
        citation["date-released"] = "2026-08-25"
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_metadata(citation=citation)

    def test_06_citation_rejects_wrong_version(self) -> None:
        citation = assurance._parse_cff(assurance.CITATION_PATH)
        citation["version"] = "0.1.1"
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_metadata(citation=citation)

    def test_07_release_notes_require_both_languages(self) -> None:
        notes = assurance.RELEASE_NOTES_PATH.read_text(encoding="utf-8").replace("## Русский", "## Removed")
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_metadata(release_notes_text=notes)

    def test_08_release_notes_require_equal_hash_commands(self) -> None:
        notes = assurance.RELEASE_NOTES_PATH.read_text(encoding="utf-8")
        marker = "Get-FileHash ml_cra-0.1.0.tar.gz,ml_cra-0.1.0-py3-none-any.whl -Algorithm SHA256"
        notes = notes.replace(marker, marker + " -LiteralPath", 1)
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_metadata(release_notes_text=notes)

    def test_09_normalization_is_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.tar.gz"
            second = root / "second.tar.gz"
            first_normalized = root / "first-normalized.tar.gz"
            second_normalized = root / "second-normalized.tar.gz"
            _write_test_sdist(first, member_mtime=1, gzip_mtime=2)
            _write_test_sdist(second, member_mtime=999, gzip_mtime=1000)
            one = assurance.normalize_sdist(first, first_normalized, 1787616000)
            two = assurance.normalize_sdist(second, second_normalized, 1787616000)
            self.assertEqual(one["sha256"], two["sha256"])
            self.assertEqual(first_normalized.read_bytes(), second_normalized.read_bytes())

    def test_10_normalization_rejects_unsafe_member(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "unsafe.tar.gz"
            _write_test_sdist(source, member_mtime=1, gzip_mtime=2, name="../escape.txt")
            with self.assertRaises((assurance.CandidateFinalizationError, assurance.release_assurance.AssuranceError)):
                assurance.normalize_sdist(source, root / "out.tar.gz", 1787616000)

    def test_11_workflow_rejects_release_command(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8") + "\n# gh release create v0.1.0\n"
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(CONTRACT, workflow_text=workflow)

    def test_12_immutable_history_rejects_hash_mutation(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["immutable_ST08_14"][0]["sha256"] = "0" * 64
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(mutated)

    def test_13_scope_rejects_omitted_path(self) -> None:
        mutated = copy.deepcopy(CONTRACT)
        mutated["planned_changes"].pop()
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_contract_bindings(mutated)

    def test_14_evidence_rejects_release_action(self) -> None:
        bindings = assurance.validate_contract_bindings(CONTRACT)
        evidence = assurance._load_json(assurance.EVIDENCE_PATH)
        mutated = copy.deepcopy(evidence)
        mutated["release_actions_performed"] = 1
        with self.assertRaises(assurance.CandidateFinalizationError):
            assurance.validate_evidence_relations(mutated, CONTRACT, bindings)


if __name__ == "__main__":
    unittest.main()
