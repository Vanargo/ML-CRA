from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mlcra.datasets import (  # noqa: E402
    MINIBOONE_CANDIDATE_ID,
    MINIBOONE_FEATURE_NAMES,
    build_miniboone_control_estimators,
    prepare_miniboone_candidate,
)
from mlcra.io import read_csv_checked  # noqa: E402
from mlcra.nested_artifacts import (  # noqa: E402
    ARTIFACT_IDS,
    V02_PROTOCOL_ID,
    assemble_v02_artifacts,
    write_v02_artifacts,
)
from mlcra.nested_cv import (  # noqa: E402
    V02ArtifactContext,
    run_nested_cv_rows,
)
from mlcra.numeric_runtime import (  # noqa: E402
    RUNTIME_CONTRACT_ID,
    build_numeric_runtime_contract,
)


RANDOM_STATE = 20260507
ROW_STATUS = "st07_16_software_fixture_not_scientific_evidence"
INTERPRETATION_ALLOWED = "no_scientific_interpretation"


def build_fixture() -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(RANDOM_STATE)
    values = rng.normal(size=(120, len(MINIBOONE_FEATURE_NAMES)))
    score = values[:, 0] + 0.5 * values[:, 1] - 0.25 * values[:, 2]
    threshold = float(np.median(score))
    target = (score > threshold).astype(np.int64)
    return pd.DataFrame(values, columns=MINIBOONE_FEATURE_NAMES), target


def execute_fixture(output_dir: Path) -> dict[str, object]:
    schema_path = (
        PROJECT_ROOT
        / "data_registry"
        / "openml_miniboone_nested_cv_v02_expected_output_schema.csv"
    )
    runtime_path = (
        PROJECT_ROOT
        / "configs"
        / "runtime"
        / "miniboone_nested_numeric_runtime_v01.csv"
    )
    schema = read_csv_checked(schema_path)
    runtime_df = read_csv_checked(runtime_path)
    runtime_contract = build_numeric_runtime_contract(
        runtime_df,
        RUNTIME_CONTRACT_ID,
        V02_PROTOCOL_ID,
    )

    X_raw, y_raw = build_fixture()
    bundle, X, y, feature_names = prepare_miniboone_candidate(X_raw, y_raw)
    parameter_grid = {
        "learning_rate": [0.05, 0.10],
        "max_iter": [2, 3],
        "max_leaf_nodes": [3, 5],
        "l2_regularization": [0.0, 0.01],
    }
    fixed_parameters = {
        "random_state": RANDOM_STATE,
        "early_stopping": "auto",
    }
    rows = run_nested_cv_rows(
        candidate_bundle=bundle,
        X=X,
        y=y,
        feature_names=feature_names,
        parameter_grid=parameter_grid,
        fixed_parameters=fixed_parameters,
        control_estimators=build_miniboone_control_estimators(RANDOM_STATE),
        protocol_id=V02_PROTOCOL_ID,
        candidate_id=MINIBOONE_CANDIDATE_ID,
        outer_n_splits=5,
        outer_n_repeats=2,
        inner_n_splits=3,
        base_random_state=RANDOM_STATE,
        feature_policy_id="numeric_particleid_0_49_locked",
        row_status=ROW_STATUS,
        interpretation_allowed=INTERPRETATION_ALLOWED,
        numeric_runtime_contract=runtime_contract,
        artifact_context=V02ArtifactContext.ST07_16_SOFTWARE_FIXTURE,
    )
    artifacts = assemble_v02_artifacts(
        rows,
        schema,
        parameter_grid,
        runtime_contract,
        outer_n_splits=5,
        outer_n_repeats=2,
        inner_n_splits=3,
        random_state=RANDOM_STATE,
        artifact_context=V02ArtifactContext.ST07_16_SOFTWARE_FIXTURE,
    )
    write_v02_artifacts(
        artifacts,
        schema,
        output_dir,
        project_root=PROJECT_ROOT,
    )
    return {
        "status": "pass",
        "pid": os.getpid(),
        "output_dir": str(output_dir.resolve()),
        "protocol_id": V02_PROTOCOL_ID,
        "artifact_context": (
            V02ArtifactContext.ST07_16_SOFTWARE_FIXTURE.value
        ),
        "artifact_count": len(ARTIFACT_IDS),
        "scientific_validation": "skipped_software_fixture_only",
        "network_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = execute_fixture(args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
