from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mlcra import application, cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGRESSION_FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "st08_11"
REGRESSION_CLAIM = REGRESSION_FIXTURES / "regression_claim_v01.json"
REGRESSION_DATA = REGRESSION_FIXTURES / "regression_data_v01.csv"
BINARY_FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "st08_08"
BINARY_CLAIM = BINARY_FIXTURES / "binary_claim_v01.json"
BINARY_DATA = BINARY_FIXTURES / "binary_data_v01.csv"
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


def call_cli(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli.main(arguments)
    return code, stdout.getvalue(), stderr.getvalue()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FailingRegressor:
    def fit(self, _X, _y):
        raise RuntimeError("intentional regression test failure")


class TestSt0811TabularRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(prefix="mlcra-st08-11-tests-")
        cls.root = Path(cls._temporary.name)
        cls.bundle = cls.root / "reference-bundle"
        result = application.run_audit(REGRESSION_CLAIM, REGRESSION_DATA, cls.bundle)
        if result["exit_code"] != 0:
            raise AssertionError(result)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def test_regression_audit_creates_specific_supported_bundle(self) -> None:
        self.assertEqual({path.name for path in self.bundle.iterdir()}, EXPECTED_BUNDLE_FILES)
        summary = load_json(self.bundle / "audit_summary.json")
        verdict = load_json(self.bundle / "verdict.json")
        provenance = load_json(self.bundle / "provenance.json")
        self.assertEqual(summary["schema_version"], "mlcra_tabular_regression_audit_summary_v01")
        self.assertEqual(verdict["schema_version"], "mlcra_tabular_regression_verdict_v01")
        self.assertEqual(provenance["claim_schema_version"], "mlcra_tabular_regression_claim_v01")
        self.assertEqual(verdict["category"], "supported")
        self.assertGreaterEqual(summary["mean_primary_delta"], 1.0)
        self.assertEqual(summary["fold_count"], 8)
        for row in summary["folds"]:
            expected = (
                row["baseline_metrics"]["root_mean_squared_error"]
                - row["candidate_metrics"]["root_mean_squared_error"]
            )
            self.assertAlmostEqual(row["primary_delta"], expected, places=12)

    def test_verify_passes_without_any_model_execution(self) -> None:
        with (
            mock.patch.object(application, "execute_binary_audit") as binary_fit,
            mock.patch.object(application, "execute_regression_audit") as regression_fit,
        ):
            result = application.verify_bundle(self.bundle)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["model_fit_performed"])
        binary_fit.assert_not_called()
        regression_fit.assert_not_called()

    def test_same_inputs_have_identical_regression_results_except_timing(self) -> None:
        second = self.root / "determinism-bundle"
        application.run_audit(REGRESSION_CLAIM, REGRESSION_DATA, second)
        first_summary = load_json(self.bundle / "audit_summary.json")
        second_summary = load_json(second / "audit_summary.json")
        first_summary.pop("execution_seconds")
        second_summary.pop("execution_seconds")
        self.assertEqual(first_summary, second_summary)
        self.assertEqual(load_json(self.bundle / "verdict.json"), load_json(second / "verdict.json"))

    def test_schema_rejects_unknown_version_field_and_sampling_assumption(self) -> None:
        base = load_json(REGRESSION_CLAIM)
        mutations = (
            ("unknown-version", {**base, "schema_version": "unknown_v99"}, "MLCRA_SPEC_SCHEMA_VERSION_UNSUPPORTED"),
            ("nonscalar-version", {**base, "schema_version": ["unknown_v99"]}, "MLCRA_SPEC_SCHEMA_VERSION_UNSUPPORTED"),
            ("unknown-field", {**base, "unregistered": True}, "MLCRA_SPEC_SCHEMA_ERROR"),
            ("temporal", {**base, "sampling_assumption": "time_ordered_rows"}, "MLCRA_SPEC_SCHEMA_ERROR"),
        )
        for name, claim, expected_error in mutations:
            with self.subTest(name=name):
                path = self.root / f"{name}.json"
                write_json(path, claim)
                code, _stdout, stderr = call_cli(
                    ["audit", "--spec", str(path), "--data", str(REGRESSION_DATA),
                     "--output-dir", str(self.root / f"{name}-bundle"), "--format", "json"]
                )
                self.assertEqual(code, 3)
                self.assertEqual(json.loads(stderr)["error_code"], expected_error)

    def test_invalid_numeric_targets_fail_closed(self) -> None:
        mutations = (
            ("nonnumeric", "x,target\n0,zero\n1,one\n2,two\n3,three\n4,four\n5,five\n6,six\n7,seven\n", 3, "MLCRA_NONNUMERIC_TARGET"),
            ("nonfinite", "x,target\n0,0\n1,1\n2,2\n3,3\n4,4\n5,5\n6,6\n7,inf\n", 3, "MLCRA_NONFINITE_TARGET"),
            ("constant", "x,target\n0,1\n1,1\n2,1\n3,1\n4,1\n5,1\n6,1\n7,1\n", 4, "MLCRA_EVIDENCE_CONSTANT_REGRESSION_TARGET"),
        )
        for name, csv_text, expected_code, expected_error in mutations:
            with self.subTest(name=name):
                path = self.root / f"{name}.csv"
                path.write_text(csv_text, encoding="utf-8")
                code, _stdout, stderr = call_cli(
                    ["audit", "--spec", str(REGRESSION_CLAIM), "--data", str(path),
                     "--output-dir", str(self.root / f"{name}-target-bundle"), "--format", "json"]
                )
                self.assertEqual(code, expected_code)
                self.assertEqual(json.loads(stderr)["error_code"], expected_error)

    def test_insufficient_rows_for_regression_folds_is_exit_4(self) -> None:
        path = self.root / "insufficient.csv"
        path.write_text("x,target\n0,0\n1,1\n2,4\n3,9\n4,16\n5,25\n6,36\n", encoding="utf-8")
        code, _stdout, stderr = call_cli(
            ["audit", "--spec", str(REGRESSION_CLAIM), "--data", str(path),
             "--output-dir", str(self.root / "insufficient-bundle"), "--format", "json"]
        )
        self.assertEqual(code, 4)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_EVIDENCE_ROW_COUNT_INSUFFICIENT")

    def test_binary_schema_does_not_silently_dispatch_regression_data(self) -> None:
        code, _stdout, stderr = call_cli(
            ["audit", "--spec", str(BINARY_CLAIM), "--data", str(REGRESSION_DATA),
             "--output-dir", str(self.root / "cross-dispatch"), "--format", "json"]
        )
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_UNSUPPORTED_TARGET_CARDINALITY")

    def test_regression_model_failure_is_controlled_exit_5(self) -> None:
        output = self.root / "model-failure"
        with mock.patch.object(
            application,
            "_build_regression_models",
            return_value=(FailingRegressor(), FailingRegressor()),
        ):
            code, _stdout, stderr = call_cli(
                ["audit", "--spec", str(REGRESSION_CLAIM), "--data", str(REGRESSION_DATA),
                 "--output-dir", str(output), "--format", "json"]
            )
        self.assertEqual(code, 5)
        self.assertEqual(json.loads(stderr)["error_code"], "MLCRA_MODEL_EXECUTION_FAILURE")
        self.assertFalse(output.exists())

    def test_verify_rejects_false_delta_even_with_recomputed_hashes(self) -> None:
        mutated = self.root / "relational-tamper"
        shutil.copytree(self.bundle, mutated)
        summary_path = mutated / "audit_summary.json"
        summary = load_json(summary_path)
        summary["folds"][0]["primary_delta"] += 1.0
        write_json(summary_path, summary)

        index_path = mutated / "artifact_index.json"
        index = load_json(index_path)
        for row in index["artifacts"]:
            if row["path"] == "audit_summary.json":
                row["sha256"] = sha256(summary_path)
        write_json(index_path, index)

        manifest_path = mutated / "run_manifest.json"
        manifest = load_json(manifest_path)
        for name in application.HASHED_BUNDLE_FILES:
            manifest["artifact_hashes"][name] = sha256(mutated / name)
        write_json(manifest_path, manifest)

        code, _stdout, stderr = call_cli(
            ["verify", "--bundle", str(mutated), "--format", "json"]
        )
        self.assertEqual(code, 6)
        self.assertEqual(
            json.loads(stderr)["error_code"],
            "MLCRA_BUNDLE_PRIMARY_DELTA_RELATION_FAILURE",
        )

    def test_existing_binary_classification_still_passes(self) -> None:
        output = self.root / "binary-regression-check"
        result = application.run_audit(BINARY_CLAIM, BINARY_DATA, output)
        self.assertEqual(result["verdict"], "supported")
        self.assertEqual(application.verify_bundle(output)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
