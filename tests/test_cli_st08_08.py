from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mlcra import application, cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "st08_08"
CLAIM = FIXTURE_ROOT / "binary_claim_v01.json"
DATA = FIXTURE_ROOT / "binary_data_v01.csv"
EXPECTED_BUNDLE_FILES = {
    "run_manifest.json",
    "input_validation.json",
    "environment.json",
    "provenance.json",
    "audit_summary.json",
    "verdict.json",
    "warnings.json",
    "artifact_index.json",
}
DIAGNOSTIC_FIELDS = {
    "error_code",
    "phase",
    "artifact_or_field",
    "expected",
    "actual",
    "severity",
    "action_taken",
    "user_action",
    "rule_source",
}


def call_cli(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli.main(arguments)
    return code, stdout.getvalue(), stderr.getvalue()


class FailingEstimator:
    def fit(self, _X, _y):
        raise RuntimeError("intentional test failure")


class TestSt0808UniversalCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(prefix="mlcra-st08-08-tests-")
        cls.root = Path(cls._temporary.name)
        cls.bundle = cls.root / "reference-bundle"
        result = application.run_audit(CLAIM, DATA, cls.bundle)
        if result["exit_code"] != 0:
            raise AssertionError(result)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_audit_creates_exact_bundle_and_supported_verdict(self) -> None:
        self.assertEqual({path.name for path in self.bundle.iterdir()}, EXPECTED_BUNDLE_FILES)
        verdict = json.loads((self.bundle / "verdict.json").read_text(encoding="utf-8"))
        summary = json.loads((self.bundle / "audit_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["category"], "supported")
        self.assertGreaterEqual(summary["mean_primary_delta"], 0.05)
        self.assertEqual(summary["positive_primary_delta_folds"], summary["fold_count"])

    def test_verify_passes_without_model_fit(self) -> None:
        with mock.patch.object(application, "execute_binary_audit") as forbidden_fit:
            code, stdout, stderr = call_cli(
                ["verify", "--bundle", str(self.bundle), "--format", "json"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        payload = json.loads(stdout)
        self.assertFalse(payload["model_fit_performed"])
        forbidden_fit.assert_not_called()

    def test_tampered_bundle_is_integrity_failure_exit_6(self) -> None:
        tampered = self.root / "tampered-bundle"
        shutil.copytree(self.bundle, tampered)
        verdict_path = tampered / "verdict.json"
        verdict_path.write_text(verdict_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        code, _stdout, stderr = call_cli(
            ["verify", "--bundle", str(tampered), "--format", "json"]
        )
        self.assertEqual(code, 6)
        diagnostic = json.loads(stderr)
        self.assertEqual(set(diagnostic), DIAGNOSTIC_FIELDS)
        self.assertEqual(diagnostic["error_code"], "MLCRA_BUNDLE_HASH_MISMATCH")

    def test_schema_rejects_regression_and_unknown_field_exit_3(self) -> None:
        claim = json.loads(CLAIM.read_text(encoding="utf-8"))
        claim["task_type"] = "regression"
        claim["unregistered"] = True
        path = self.root / "regression-claim.json"
        path.write_text(json.dumps(claim), encoding="utf-8")
        code, _stdout, stderr = call_cli(
            ["audit", "--spec", str(path), "--data", str(DATA), "--output-dir", str(self.root / "rejected"), "--format", "json"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(set(json.loads(stderr)), DIAGNOSTIC_FIELDS)
        self.assertFalse((self.root / "rejected").exists())

    def test_multiclass_data_is_rejected_exit_3(self) -> None:
        path = self.root / "multiclass.csv"
        path.write_text(
            "x1,x2,target\n0,0,no\n0,1,yes\n1,0,maybe\n1,1,no\n",
            encoding="utf-8",
        )
        code, _stdout, stderr = call_cli(
            ["audit", "--spec", str(CLAIM), "--data", str(path), "--output-dir", str(self.root / "multiclass-run"), "--format", "json"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_UNSUPPORTED_TARGET_CARDINALITY")

    def test_insufficient_class_count_is_exit_4(self) -> None:
        path = self.root / "insufficient.csv"
        path.write_text(
            "x1,x2,target\n0,0,no\n0,1,no\n1,0,no\n1,1,yes\n2,1,yes\n2,2,yes\n",
            encoding="utf-8",
        )
        code, _stdout, stderr = call_cli(
            ["audit", "--spec", str(CLAIM), "--data", str(path), "--output-dir", str(self.root / "insufficient-run"), "--format", "json"]
        )
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_EVIDENCE_CLASS_COUNT_INSUFFICIENT")

    def test_existing_output_is_rejected_exit_3(self) -> None:
        code, _stdout, stderr = call_cli(
            ["audit", "--spec", str(CLAIM), "--data", str(DATA), "--output-dir", str(self.bundle), "--format", "json"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_OUTPUT_ALREADY_EXISTS")

    def test_usage_error_is_exit_2(self) -> None:
        process = subprocess.run(
            [sys.executable, "-m", "mlcra.cli", "audit", "--format", "json"],
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(process.returncode, 2)
        diagnostic = json.loads(process.stderr)
        self.assertEqual(set(diagnostic), DIAGNOSTIC_FIELDS)
        self.assertEqual(diagnostic["error_code"], "MLCRA_COMMAND_LINE_USAGE_ERROR")
        self.assertNotIn("Traceback", process.stderr)

    def test_model_failure_is_controlled_exit_5(self) -> None:
        output = self.root / "model-failure-run"
        with mock.patch.object(application, "_build_models", return_value=(FailingEstimator(), FailingEstimator())):
            code, _stdout, stderr = call_cli(
                ["audit", "--spec", str(CLAIM), "--data", str(DATA), "--output-dir", str(output), "--format", "json"]
            )
        self.assertEqual(code, 5)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_MODEL_EXECUTION_FAILURE")
        self.assertFalse(output.exists())

    def test_unexpected_failure_is_controlled_exit_6_without_traceback(self) -> None:
        with mock.patch.object(cli, "run_audit", side_effect=RuntimeError("unexpected")):
            code, _stdout, stderr = call_cli(
                ["audit", "--spec", str(CLAIM), "--data", str(DATA), "--output-dir", str(self.root / "unexpected"), "--format", "json"]
            )
        self.assertEqual(code, 6)
        self.assertNotIn("Traceback", stderr)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_INTERNAL_INVARIANT_FAILURE")

    def test_doctor_is_read_only_and_reports_release_blockers(self) -> None:
        code, stdout, stderr = call_cli(["doctor", "--format", "json"])
        self.assertIn(code, {0, 5})
        self.assertEqual(stderr, "")
        report = json.loads(stdout)
        self.assertFalse(report["network_access_performed"])
        self.assertFalse(report["model_fit_performed"])
        self.assertFalse(report["release_ready"])
        self.assertGreater(len(report["release_blockers"]), 0)


if __name__ == "__main__":
    unittest.main()
