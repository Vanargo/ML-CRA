# ML Claim Reliability Auditor (ML-CRA)

[Русская версия](README_RU.md)

<!-- ST08-10:status -->
## Status and scope

ML-CRA audits whether experimental evidence supports a **bounded**
machine-learning claim. It does not choose a universally best model and does not
turn one dataset result into a general recommendation.

This public repository is a development snapshot, version `0.1.0.dev0`.
It is not an authorized release. Repository publication, hosted CI, and
repository-security observations are bounded by the
[ST08_13B evidence record](data_registry/st08_13B_public_repository_hosted_CI_and_security_evidence_v01.json).
The subsequent [ST08_13C prospective v02 re-audit](data_registry/st08_13C_prospective_release_candidate_v02_reaudit_evidence_v01.json)
applies all 24 registered project requirements to an exact hash-bound candidate.
Project completion passes only within that registered boundary. External release
remains blocked until John separately authorizes it; no version tag, GitHub
Release, or package-index publication is implied.
The supported user workflows are local binary tabular classification
and bounded exchangeable-row tabular regression on Windows x64 with CPython
3.12, plus generation of a local static English/Russian dashboard from a
verified evidence bundle. Multiclass classification, time-series or grouped
regression, arbitrary model imports, pickle/joblib inputs, URLs, automatic
hyperparameter search, an interactive or hosted dashboard, and a hosted service
are not supported.

The English and Russian guides describe the same commands. User-facing CLI
diagnostics are currently emitted in Russian; diagnostic localization is not a
supported feature yet.

<!-- ST08-10:purpose -->
## What the tool does

`mlcra audit` validates a task-specific versioned JSON claim and a local UTF-8
CSV, compares two fixed allowlisted implementations over registered paired
folds, and writes an eight-file evidence bundle. Binary classification uses
stratified folds; regression uses K-fold only under the declared
`exchangeable_rows` assumption. `mlcra verify` checks that bundle's exact
inventory, hashes, provenance relations, and verdict without fitting models.
`mlcra doctor` reports whether the installed environment matches the declared
cell and lists unresolved release gates.

A successful audit can return `supported`, `fragile`, or `not_supported`.
All three are valid bounded findings, not software failures. See the
[Stage 8 product contract](configs/project_readiness/stage08_public_product_scope_and_release_train_contract_v01.json)
the [binary claim JSON Schema](src/mlcra/schemas/binary_classification_claim_v01.schema.json),
and the [regression claim JSON Schema](src/mlcra/schemas/tabular_regression_claim_v01.schema.json).

<!-- ST08-10:prerequisites -->
## Prerequisites

- Windows x64;
- CPython `>=3.12,<3.13`;
- a source checkout of this repository;
- network access to the configured Python package index during the installation
  commands below. The supported `audit`, `verify`, and `doctor` operations do
  not use the network.

The locally observed cell is CPython 3.12.0 on Windows Server 2019 AMD64. A
GitHub Actions cell using CPython 3.12.10 on `windows-2022` is configured; its
observed outcome is recorded, rather than inferred from configuration, in the
ST08_13B evidence record. Linux, macOS, ARM64, PyPy, and other Python versions
are not claimed as validated.

<!-- ST08-10:installation -->
## Reconstructible source installation

Run these commands from the repository root in PowerShell. The first two
installations use exact versions and SHA-256 hashes. The project installation
then reuses the already installed, fixed build backend and does not resolve new
dependencies.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements/locks/st08_09-assurance-tools-py312-windows-x86_64.txt
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements/locks/st08_07-py312-windows-x86_64.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps .
.\.venv\Scripts\mlcra.exe doctor --format json
```

Expected result: `doctor` exits with code `0` and reports
`"environment_pass": true`. It intentionally reports `"release_ready": false`
with the sole blocker `John_release_authorization_not_granted`. The v02
project-completion audit has passed, but a successful audit is evidence about
the candidate, not permission to perform a release.

<!-- ST08-10:quickstart -->
## Quick start

The following source-checkout walkthrough uses a small synthetic fixture. It
does not modify the registered MiniBooNE evidence and does not use the network.
It writes a new uniquely named bundle under the operating-system temporary
directory.

```powershell
$ClassRunDir = Join-Path ([System.IO.Path]::GetTempPath()) ("mlcra-classification-demo-" + [guid]::NewGuid().ToString("N"))
$RegressionRunDir = Join-Path ([System.IO.Path]::GetTempPath()) ("mlcra-regression-demo-" + [guid]::NewGuid().ToString("N"))
$DashboardDir = Join-Path ([System.IO.Path]::GetTempPath()) ("mlcra-dashboard-demo-" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\mlcra.exe audit --spec tests/fixtures/st08_08/binary_claim_v01.json --data tests/fixtures/st08_08/binary_data_v01.csv --output-dir $ClassRunDir --format json
.\.venv\Scripts\mlcra.exe verify --bundle $ClassRunDir --format json
.\.venv\Scripts\mlcra.exe audit --spec tests/fixtures/st08_11/regression_claim_v01.json --data tests/fixtures/st08_11/regression_data_v01.csv --output-dir $RegressionRunDir --format json
.\.venv\Scripts\mlcra.exe verify --bundle $RegressionRunDir --format json
.\.venv\Scripts\mlcra.exe dashboard --bundle $RegressionRunDir --output-dir $DashboardDir --format json
```

Expected result for each audit: exit code `0`, a bounded `supported` fixture
verdict, and exactly these files in its output directory:

`run_manifest.json`, `input_validation.json`, `environment.json`,
`provenance.json`, `audit_summary.json`, `verdict.json`, `warnings.json`, and
`artifact_index.json`.

Expected verification result: exit code `0`, `"status": "PASS"`,
`"verified_artifacts": 8`, and `"model_fit_performed": false`. You may delete
the temporary bundles after inspection. These synthetic results verify software
behavior; they are not registered scientific findings for a real dataset.
The dashboard command first verifies the bundle and then writes
`dashboard_view.json`, `dashboard_en.html`, `dashboard_ru.html`, and
`dashboard_manifest.json`. It performs no fit and no network access; both HTML
pages are exact renderings of the same verified JSON view.

<!-- ST08-10:inputs -->
## Input boundary

The claim must validate against its supplied task schema. Every CSV needs a
header, one explicit target, and at least one complete finite numeric feature.
Binary classification additionally requires exactly two labels and enough rows
of each class for all folds. Regression requires a complete finite numeric,
nonconstant target, at least twice as many rows as folds, and the explicit
`exchangeable_rows` assumption. That assumption is not machine-verifiable:
time-ordered, grouped, repeated-measure, or spatially dependent observations
need a separately registered split protocol.

Classification allowlists `hist_gradient_boosting_v01` versus
`logistic_regression_v01` with `average_precision`. Regression allowlists
`hist_gradient_boosting_regressor_v01` versus `ridge_regression_v01` with
`root_mean_squared_error`; positive delta means baseline RMSE minus candidate
RMSE. Models and hyperparameters are fixed before execution. A new output
directory is mandatory; overwriting is rejected.

<!-- ST08-10:exit-codes -->
## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Contract-valid execution completed, including any valid verdict category |
| `2` | Command-line usage error |
| `3` | Input or specification contract error |
| `4` | Evidence is insufficient for a valid verdict |
| `5` | Controlled environment or model-execution failure |
| `6` | Internal invariant or bundle-integrity failure |

Errors are fail-closed: a failed operation does not publish a successful bundle
and normal user mode does not expose an uncaught traceback.

<!-- ST08-10:troubleshooting -->
## Troubleshooting

- `environment_pass=false`: use CPython 3.12 on Windows x64, install both lock
  files exactly, then reinstall the project with `--no-build-isolation`.
- `MLCRA_OUTPUT_ALREADY_EXISTS`: choose a new output directory; automatic
  overwrite is forbidden.
- `MLCRA_EVIDENCE_CLASS_COUNT_INSUFFICIENT`: reduce `n_splits` or provide enough
  rows for both classes.
- `MLCRA_UNSUPPORTED_TARGET_CARDINALITY`: a binary-classification claim requires
  exactly two labels; use the regression schema for a numeric regression target.
- `MLCRA_NONNUMERIC_TARGET` or `MLCRA_NONFINITE_TARGET`: convert the regression
  target to complete finite numeric values.
- `MLCRA_EVIDENCE_ROW_COUNT_INSUFFICIENT`: provide at least twice as many
  regression rows as folds.
- bundle hash or file-set error: do not repair the bundle manually; repeat
  `audit` from the original inputs.
- security issue: follow [SECURITY.md](SECURITY.md). Do not place raw datasets,
  caches, credentials, private keys, or local environments in the repository.

<!-- ST08-10:verification -->
## Maintainer verification

The deterministic baseline can be run from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts/agent_verify.py --mode baseline
```

The broader cumulative pilot intentionally retains historical checkpoint gates;
its nonzero exit code must be interpreted through the current Stage 8 evidence,
not silently treated as a new regression. Current CI and security controls are
documented in [SECURITY.md](SECURITY.md) and the
[ST08_09 evidence](data_registry/st08_09_CI_security_and_release_candidate_assurance_evidence_v01.json).

<!-- ST08-10:scientific-boundary -->
## Scientific evidence boundary

The registered MiniBooNE claim is a separate scientific evidence record. Within
its fixed dataset, protocols, models, metrics, and verdict policy it is recorded
as `strongly_supported`, with high computational cost disclosed. It does not
establish universal superiority of histogram gradient boosting over logistic
regression, and running the public CLI does not change that registered verdict.
See [Stage 5](docs/stages/stage_05_claim_audit_protocol.md),
[Stage 6](docs/stages/stage_06_packaging_and_publication.md), and
[dataset attribution](DATASET_ATTRIBUTION.md).

The ST08_11 regression fixture is synthetic and validates software and protocol
invariants only. ST08_11A separately registers the UCI Wine Quality red dataset,
its provenance and license, an exchangeable-row claim, and the resulting
scope-limited scientific verdict. That result does not validate temporal or
grouped regression candidates, which require separate prospective protocols.

<!-- ST08-10:project-status -->
## Remaining project gates

The historical 2026-08-24 v01 re-audit remains unchanged at 19 `PASS`, two
`FAIL`, three `BLOCKED`, and `not_ready`. The prospective ST08_13C audit applies
the owner-approved v02 rules without rewriting that history: all 24 current
requirements and all eight dimensions pass, so project completion is `PASS`.
The cumulative pilot still executes and must reproduce exactly its eight
registered historical FAIL rows with no new failure. External release readiness
is independently `BLOCKED` solely because John has not authorized a release.
Real-dataset regression validation and the local static dashboard remain valid
bounded results; neither authorizes broader scientific claims or a release.

<!-- ST08-10:legal-help -->
## License, citation, and help

Original ML-CRA code and documentation are licensed under the [MIT License](LICENSE).
Third-party dataset terms remain separate; see [DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md).
Citation metadata is in [CITATION.cff](CITATION.cff). The project is maintained
by Ivan Polishchuk (Иван Полищук), ORCID
[0009-0005-6596-0605](https://orcid.org/0009-0005-6596-0605).

For usage problems, retain the complete diagnostic envelope and the exact
command. For suspected vulnerabilities, use the private reporting process in
[SECURITY.md](SECURITY.md).
