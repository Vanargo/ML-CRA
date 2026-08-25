from __future__ import annotations

import copy
import unittest

from scripts import st08_13A_current_canonical_hash_assurance as assurance


CONTRACT = assurance._load_json(assurance.CONTRACT_PATH)
EVIDENCE = assurance._load_json(assurance.EVIDENCE_PATH)
_, REQUIREMENTS_V01 = assurance._load_csv(assurance.REQUIREMENTS_V01_PATH)
_, REQUIREMENTS_V02 = assurance._load_csv(assurance.REQUIREMENTS_V02_PATH)
MANIFEST_FIELDS, MANIFEST_ROWS = assurance._load_csv(assurance.STATE_MANIFEST_PATH)


class ST0813ACurrentCanonicalHashAssuranceTests(unittest.TestCase):
    def test_registered_migration_passes(self) -> None:
        result = assurance.validate_registered_migration()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["bindings"]["migration"]["changed_requirement_ids"], ["ST08-REQ-08", "ST08-REQ-12"])
        self.assertEqual(result["bindings"]["protected"]["expected"], 18)

    def test_non_target_requirement_change_is_rejected(self) -> None:
        mutated = copy.deepcopy(REQUIREMENTS_V02)
        mutated[0]["pass_rule"] += " weakened"
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_requirement_migration(REQUIREMENTS_V01, mutated, CONTRACT)

    def test_target_immutable_field_change_is_rejected(self) -> None:
        mutated = copy.deepcopy(REQUIREMENTS_V02)
        row = next(value for value in mutated if value["requirement_id"] == "ST08-REQ-08")
        row["aggregation_role"] = "conditional"
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_requirement_migration(REQUIREMENTS_V01, mutated, CONTRACT)

    def test_target_missing_authorized_change_is_rejected(self) -> None:
        mutated = copy.deepcopy(REQUIREMENTS_V02)
        before = next(value for value in REQUIREMENTS_V01 if value["requirement_id"] == "ST08-REQ-12")
        row = next(value for value in mutated if value["requirement_id"] == "ST08-REQ-12")
        row["blocked_rule"] = before["blocked_rule"]
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_requirement_migration(REQUIREMENTS_V01, mutated, CONTRACT)

    def test_manifest_missing_path_is_rejected(self) -> None:
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_state_manifest_rows(MANIFEST_FIELDS, MANIFEST_ROWS[:-1], assurance.PROJECT_ROOT, CONTRACT)

    def test_manifest_duplicate_path_is_rejected(self) -> None:
        mutated = copy.deepcopy(MANIFEST_ROWS)
        mutated[-1] = copy.deepcopy(mutated[0])
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_state_manifest_rows(MANIFEST_FIELDS, mutated, assurance.PROJECT_ROOT, CONTRACT)

    def test_manifest_hash_mutation_is_rejected(self) -> None:
        mutated = copy.deepcopy(MANIFEST_ROWS)
        mutated[0]["sha256"] = "0" * 64
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_state_manifest_rows(MANIFEST_FIELDS, mutated, assurance.PROJECT_ROOT, CONTRACT)

    def test_manifest_size_mutation_is_rejected(self) -> None:
        mutated = copy.deepcopy(MANIFEST_ROWS)
        mutated[0]["size_bytes"] = str(int(mutated[0]["size_bytes"]) + 1)
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_state_manifest_rows(MANIFEST_FIELDS, mutated, assurance.PROJECT_ROOT, CONTRACT)

    def test_historical_status_rewrite_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["prospective_disposition"]["historical_ST08_13_REQ08"] = "PASS"
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_repository_bindings(CONTRACT, mutated)

    def test_external_action_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["external_actions_performed"] = 1
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_repository_bindings(CONTRACT, mutated)

    def test_next_block_authorization_is_rejected(self) -> None:
        mutated = copy.deepcopy(EVIDENCE)
        mutated["next_block_reference"]["status"] = "authorized"
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_repository_bindings(CONTRACT, mutated)

    def test_CI_omission_is_rejected(self) -> None:
        workflow = assurance.WORKFLOW_PATH.read_text(encoding="utf-8").replace(
            "scripts/st08_13A_current_canonical_hash_assurance.py", "removed-validator"
        )
        with self.assertRaises(assurance.CanonicalHashAssuranceError):
            assurance.validate_repository_bindings(CONTRACT, EVIDENCE, workflow_text=workflow)


if __name__ == "__main__":
    unittest.main()
