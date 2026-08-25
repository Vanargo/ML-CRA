from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import yaml

from scripts import st08_09_release_assurance as assurance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(assurance.DEFAULT_CONTRACT.read_text(encoding="utf-8"))
PUBLICATION_CONTRACT = json.loads(
    assurance.PUBLICATION_CONTRACT.read_text(encoding="utf-8")
)


def write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


class TestSt0809ReleaseAssurance(unittest.TestCase):
    def test_publication_manifest_binds_canonical_git_index_blob(self) -> None:
        with assurance.PUBLICATION_TREE_MANIFEST.open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        row = next(
            item
            for item in rows
            if item["relative_path"]
            == ".agents/skills/ml-cra-stage-gate/SKILL.md"
        )
        payload = assurance.git_index_blob_bytes(row["relative_path"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), row["sha256"])
        self.assertEqual(str(len(payload)), row["size_bytes"])

    def test_published_protected_binding_rejects_mutated_git_hash(self) -> None:
        bindings = copy.deepcopy(
            PUBLICATION_CONTRACT["protected_git_blob_bindings"]
        )
        bindings[0]["canonical_git_blob_sha256"] = "0" * 64
        with self.assertRaises(assurance.AssuranceError):
            assurance.validate_protected_hashes(
                inventory="published", canonical_bindings=bindings
            )

    def test_doctor_reports_only_current_post_st08_13C_release_blocker(self) -> None:
        source = (PROJECT_ROOT / "src/mlcra/application.py").read_text(encoding="utf-8")
        self.assertNotIn('"prospective_release_candidate_reaudit_v02_not_passed"', source)
        self.assertIn('"John_release_authorization_not_granted"', source)
        self.assertNotIn('"hosted_CI_run_not_observed"', source)
        self.assertNotIn('"external_GitHub_secret_scanning_not_enabled"', source)

    def test_source_contract_passes(self) -> None:
        result = assurance.validate_source()
        self.assertEqual(result["status"], "PASS")
        expected_representation = (
            "canonical_git_blob"
            if result["inventory"] == "published"
            else "historical_worktree_bytes"
        )
        self.assertEqual(
            result["protected"],
            {
                "expected": 18,
                "mismatches": 0,
                "representation": expected_representation,
            },
        )

    def test_published_source_contract_passes(self) -> None:
        result = assurance.validate_source(inventory="published")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["inventory"], "published")

    def test_published_tree_rejects_unregistered_tracked_path(self) -> None:
        tracked = assurance.tracked_repository_paths()
        with mock.patch.object(assurance, "tracked_repository_paths", return_value=tracked + ["unregistered.txt"]):
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_publication_tree()

    def test_workflow_rejects_mutable_action_reference(self) -> None:
        workflow = yaml.load(assurance.WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        mutated = copy.deepcopy(workflow)
        mutated["jobs"]["assurance"]["steps"][0]["uses"] = "actions/checkout@v7.0.1"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            write_yaml(path, mutated)
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_workflow_rejects_write_permission(self) -> None:
        workflow = yaml.load(assurance.WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        workflow["permissions"]["contents"] = "write"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            write_yaml(path, workflow)
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_workflow_rejects_implicit_working_inventory(self) -> None:
        workflow = yaml.load(
            assurance.WORKFLOW.read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
        workflow["jobs"]["assurance"].pop("env")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            write_yaml(path, workflow)
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_workflow_rejects_privileged_pull_request_target(self) -> None:
        workflow = yaml.load(assurance.WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        workflow["on"]["pull_request_target"] = {}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            write_yaml(path, workflow)
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_workflow_rejects_missing_native_exit_guard(self) -> None:
        mutated = assurance.WORKFLOW.read_text(encoding="utf-8").replace(
            "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }", "# removed native exit guard", 1
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            path.write_text(mutated, encoding="utf-8")
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_workflow_rejects_detached_pip_requirement_argument(self) -> None:
        mutated = assurance.WORKFLOW.read_text(encoding="utf-8").replace(
            "--only-binary=:all: -r requirements/locks/",
            "--only-binary=:all:\n          -r requirements/locks/",
            1,
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            path.write_text(mutated, encoding="utf-8")
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_workflow_requires_regular_local_project_install(self) -> None:
        mutated = assurance.WORKFLOW.read_text(encoding="utf-8").replace(
            "python -m pip install --no-deps --no-build-isolation .",
            "# removed regular local project install",
            1,
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ci.yml"
            path.write_text(mutated, encoding="utf-8")
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_workflow(path, CONTRACT)

    def test_publication_manifest_digest_uses_canonical_git_blob(self) -> None:
        result = assurance.validate_publication_tree()
        payload = assurance.git_index_blob_bytes(
            assurance.PUBLICATION_TREE_MANIFEST.relative_to(
                assurance.PROJECT_ROOT
            ).as_posix()
        )
        self.assertEqual(result["manifest_sha256"], hashlib.sha256(payload).hexdigest())

    def test_lock_rejects_missing_hash(self) -> None:
        original = assurance.RUNTIME_LOCK.read_text(encoding="utf-8")
        mutated = original.replace("    --hash=sha256:", "    # removed-hash=sha256:", 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "lock.txt"
            path.write_text(mutated, encoding="utf-8")
            with self.assertRaises(assurance.AssuranceError):
                assurance.validate_lock(path, 15)

    def test_wheel_inventory_passes_and_rejects_bytecode(self) -> None:
        required = [
            "mlcra/application.py",
            "mlcra/cli.py",
            "mlcra/dashboard.py",
            "mlcra/schemas/binary_classification_claim_v01.schema.json",
            "mlcra/schemas/tabular_regression_claim_v01.schema.json",
            "ml_cra-0.1.0.dev0.dist-info/entry_points.txt",
            "ml_cra-0.1.0.dev0.dist-info/licenses/LICENSE",
            "ml_cra-0.1.0.dev0.dist-info/licenses/DATASET_ATTRIBUTION.md",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            good = Path(temporary) / "good.whl"
            with zipfile.ZipFile(good, "w") as archive:
                for name in required:
                    content = "[console_scripts]\nmlcra = mlcra.cli:main\n" if name.endswith("entry_points.txt") else "fixture"
                    archive.writestr(name, content)
            self.assertEqual(assurance.verify_wheel(good, CONTRACT)["file_entries"], len(required))
            bad = Path(temporary) / "bad.whl"
            with zipfile.ZipFile(bad, "w") as archive:
                for name in required:
                    content = "[console_scripts]\nmlcra = mlcra.cli:main\n" if name.endswith("entry_points.txt") else "fixture"
                    archive.writestr(name, content)
                archive.writestr("mlcra/__pycache__/cli.pyc", b"bad")
            with self.assertRaises(assurance.AssuranceError):
                assurance.verify_wheel(bad, CONTRACT)

    def test_sdist_inventory_passes_and_rejects_symlink(self) -> None:
        root = "ml_cra-0.1.0.dev0"
        required = CONTRACT["archive_assurance"]["sdist_must_include"]
        with tempfile.TemporaryDirectory() as temporary:
            good = Path(temporary) / "good.tar.gz"
            with tarfile.open(good, "w:gz") as archive:
                for name in required:
                    payload = b"fixture"
                    info = tarfile.TarInfo(f"{root}/{name}")
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))
            self.assertEqual(assurance.verify_sdist(good, CONTRACT)["file_entries"], len(required))
            bad = Path(temporary) / "bad.tar.gz"
            with tarfile.open(bad, "w:gz") as archive:
                for name in required:
                    payload = b"fixture"
                    info = tarfile.TarInfo(f"{root}/{name}")
                    info.size = len(payload)
                    archive.addfile(info, io.BytesIO(payload))
                link = tarfile.TarInfo(f"{root}/unsafe-link")
                link.type = tarfile.SYMTYPE
                link.linkname = "../../outside"
                archive.addfile(link)
            with self.assertRaises(assurance.AssuranceError):
                assurance.verify_sdist(bad, CONTRACT)

    def test_archive_path_rejects_parent_traversal(self) -> None:
        with self.assertRaises(assurance.AssuranceError):
            assurance._validate_archive_path("package/../../secret.txt")

    def test_secret_scanner_rejects_private_key_pattern(self) -> None:
        try:
            from detect_secrets import SecretsCollection
            from detect_secrets.settings import transient_settings
        except ImportError as error:
            self.skipTest(str(error))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "secret.pem"
            begin = "-----BEGIN " + "RSA PRIVATE KEY-----"
            end = "-----END " + "RSA PRIVATE KEY-----"
            path.write_text(
                f"{begin}\nMIIBOgIBAAJBALongFakeFixtureForDetectionOnly\n{end}\n",
                encoding="utf-8",
            )
            with transient_settings({"plugins_used": [{"name": "PrivateKeyDetector"}]}):
                secrets = SecretsCollection()
                secrets.scan_file(str(path))
            self.assertTrue(secrets.json())

    def test_public_manifest_is_exact_and_unmapped_zero(self) -> None:
        if os.environ.get("MLCRA_ASSURANCE_INVENTORY") == "published":
            result = assurance.validate_publication_tree()
            self.assertEqual(result["paths"], 326)
        else:
            result = assurance.validate_public_manifest()
            self.assertGreater(result["paths"], 0)
            self.assertEqual(sum(result["counts"].values()), result["paths"])


if __name__ == "__main__":
    unittest.main()
