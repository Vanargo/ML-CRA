from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/st08_11A_wine_quality_scientific_validation.py"
SPEC = importlib.util.spec_from_file_location("st08_11A_validation", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ST0811AScientificValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_json(MODULE.CONTRACT_PATH)
        self.rows = MODULE.read_fold_csv(MODULE.FOLD_PATH)

    def test_registered_evidence_relations(self) -> None:
        result = MODULE.validate_registered()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["fold_count"], 25)

    def test_false_delta_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.rows)
        mutated[0]["primary_delta"] = str(float(mutated[0]["primary_delta"]) + 0.1)
        with self.assertRaisesRegex(ValueError, "primary delta relation"):
            MODULE.validate_rows(mutated, self.contract)

    def test_duplicate_fold_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.rows)
        mutated[-1] = copy.deepcopy(mutated[0])
        with self.assertRaisesRegex(ValueError, "fold key set"):
            MODULE.validate_rows(mutated, self.contract)

    def test_post_result_threshold_change_alters_verdict_or_contract(self) -> None:
        mutated = copy.deepcopy(self.contract)
        mutated["prospective_claim"]["minimum_mean_delta"] = 100.0
        result = MODULE.validate_rows(self.rows, mutated)
        self.assertEqual(result["verdict"], "not_supported")


if __name__ == "__main__":
    unittest.main()
