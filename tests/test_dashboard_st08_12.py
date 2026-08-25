from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mlcra import application
from mlcra.dashboard import render_html, run_dashboard, verify_dashboard_output


ROOT = Path(__file__).resolve().parents[1]


class ST0812DashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="mlcra-st08-12-")
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _bundle(self, kind: str) -> Path:
        fixture = ROOT / "tests/fixtures" / ("st08_08" if kind == "classification" else "st08_11")
        claim = fixture / ("binary_claim_v01.json" if kind == "classification" else "regression_claim_v01.json")
        data = fixture / ("binary_data_v01.csv" if kind == "classification" else "regression_data_v01.csv")
        bundle = self.root / f"{kind}-bundle"
        application.run_audit(claim, data, bundle)
        return bundle

    def test_classification_dashboard_exact_files_and_golden_equivalence(self) -> None:
        bundle = self._bundle("classification")
        output = self.root / "dashboard"
        result = run_dashboard(bundle, output)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(verify_dashboard_output(bundle, output)["files"], 4)
        view = json.loads((output / "dashboard_view.json").read_text(encoding="utf-8"))
        self.assertEqual(view, application.build_dashboard_view(bundle))

    def test_regression_dashboard_preserves_negative_verdict(self) -> None:
        fixture = ROOT / "tests/fixtures/st08_11"
        claim = json.loads((fixture / "regression_claim_v01.json").read_text(encoding="utf-8"))
        claim["minimum_mean_delta"] = 100.0
        claim_path = self.root / "negative-regression-claim.json"
        claim_path.write_text(json.dumps(claim), encoding="utf-8")
        bundle = self.root / "regression-bundle"
        application.run_audit(claim_path, fixture / "regression_data_v01.csv", bundle)
        output = self.root / "dashboard"
        run_dashboard(bundle, output)
        view = json.loads((output / "dashboard_view.json").read_text(encoding="utf-8"))
        verdict = json.loads((bundle / "verdict.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["category"], "not_supported")
        self.assertEqual(view["verdict"], verdict["category"])
        self.assertEqual(view["mean_primary_delta"], verdict["mean_primary_delta"])

    def test_dashboard_verification_never_fits(self) -> None:
        bundle = self._bundle("classification")
        output = self.root / "dashboard"
        run_dashboard(bundle, output)
        with mock.patch.object(application, "execute_binary_audit", side_effect=AssertionError("fit forbidden")):
            self.assertEqual(verify_dashboard_output(bundle, output)["status"], "PASS")

    def test_html_renderer_escapes_untrusted_bundle_text(self) -> None:
        view = application.build_dashboard_view(self._bundle("classification"))
        mutated = copy.deepcopy(view)
        mutated["claim_id"] = '<script>alert("x")</script>'
        rendered = render_html(mutated, "en")
        self.assertNotIn('<script>alert("x")</script>', rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_tampered_view_is_rejected_even_if_json_remains_valid(self) -> None:
        bundle = self._bundle("classification")
        output = self.root / "dashboard"
        run_dashboard(bundle, output)
        view_path = output / "dashboard_view.json"
        value = json.loads(view_path.read_text(encoding="utf-8"))
        value["verdict"] = "tampered"
        view_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(Exception, "MLCRA_DASHBOARD_INTEGRITY_GOLDEN_MISMATCH"):
            verify_dashboard_output(bundle, output)

    def test_existing_output_is_rejected(self) -> None:
        bundle = self._bundle("classification")
        output = self.root / "dashboard"
        output.mkdir()
        with self.assertRaisesRegex(Exception, "MLCRA_DASHBOARD_OUTPUT_EXISTS"):
            run_dashboard(bundle, output)


if __name__ == "__main__":
    unittest.main()
