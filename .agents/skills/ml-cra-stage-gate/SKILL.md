---
name: ml-cra-stage-gate
description: Execute one bounded, John-authorized ML-CRA task through task profiling, MAPE-K analysis, a traceable planned change set, in-scope implementation, verification or scientific validation, evidence recording, checkpointing when applicable, and a mandatory stop for John acceptance. Use for ML-CRA project-governance changes, any changing task, a new stage or Stage 7 continuation, claim/protocol/evidence/verdict work, canonical-state reconciliation, scientific validation, checkpoint creation, or stage closure. Do not use to authorize or begin a merely proposed next task.
---

# ML-CRA stage gate

## Purpose

Turn exactly one John-authorized ML-CRA task into a traceable result without
silently changing the scientific claim, protocol, evidence, stage boundary, or
task boundary.

Follow the root `AGENTS.md`. Read
`docs/agent/ml_cra_agent_working_contract_v01.md`,
`docs/agent/task_templates/task_core_v01.md`, and exactly one applicable
profile template before executing a governed task.

## Gate 0 — Confirm authority and profile

Identify:

- chat/task name and task identifier;
- one measurable outcome;
- task profile: `ANALYSIS_ONLY`, `CHANGE`, `SCIENTIFIC_VALIDATION`, or
  `CHECKPOINT`;
- technical completion criteria;
- source baseline and sources of truth;
- permitted and prohibited scope;
- protected artifacts;
- required checks and evidence;
- decisions reserved for John;
- mandatory stop conditions.

If the profile is omitted but unambiguous, select it and state the selection. If
the choice materially changes permitted actions, ask John. If no bounded task
has been authorized, propose a task and stop. Never infer authority to start a
neighboring stage or proposed next block.

## Gate 1 — Monitor

Read every necessary current file completely. Inventory relevant code, configs,
notebooks, evidence tables, active documentation, and exact paths.

Report immediately if a required file is missing, empty, undecodable,
truncated, inaccessible, structurally invalid, or too large to process
completely. Do not replace missing local evidence with external sources.

Capture the pre-change state with hashes or an equivalent reproducible manifest
for a significant change, checkpoint, or baseline reconciliation.

## Gate 2 — Analyze

Build the traceability chain:

```text
John decision
→ task contract
→ claim and active stage, when applicable
→ protocol/config
→ implementation
→ evidence
→ verdict
→ roadmap/stage record, only when canonical state changes
```

Classify every material statement as local file evidence, observed execution
evidence, authoritative external support, analytical inference, or unresolved
uncertainty.

Check applicable homeostatic invariants: registered scope, seeds, splits,
metric direction, schema, key uniqueness, rounding, verdict semantics,
artifact paths, current task boundary, and current stage status.

When sources conflict, verify observable behavior and record the conflict. Do
not canonically close it without John acceptance.

## Gate 3 — Plan and continue

Define the smallest planned change set that reaches the authorized outcome. For
each item specify:

- target file and contract;
- traceability to the task;
- expected effect and prohibited side effects;
- verification method;
- risk and recovery or checkpoint strategy.

State the protected and out-of-scope files. Use applicable authoritative
scientific, standards, or official documentation and recognized professional
methods for important decisions.

Continue directly to execution; do not wait for separate approval of the
planned change set.

If an initially unplanned file becomes necessary, add it to the planned change
set before creation when practicable and continue only if it is necessary for
the already authorized goal, does not expand scope, is not protected, has a
recorded reason, appears in the final change log, and can be verified.
Otherwise stop for John.

## Gate 4 — Execute

Apply only the authorized plan. Preserve unrelated user work and historical
records.

For computational refactoring, keep reusable deterministic logic under
`src/mlcra/` and keep notebooks as orchestration. Do not change canonical
numeric results unless the task explicitly changes the registered scientific
process.

On an in-scope defect, repair and re-run checks without asking John. Stop when a
repair would change the task outcome, scientific meaning, protected artifact,
or authorized boundary.

## Gate 5 — Verify, validate, and review

Label evidence correctly:

- **software verification**: syntax, schemas, deterministic behavior, exact
  regression equality, paths, and contracts;
- **scientific validation**: rerun or independent assessment of the experiment
  supporting a claim;
- **documentary consistency**: current documents name actual artifacts and
  status;
- **checkpoint integrity**: inventory, exclusions, hashes, and reproducible
  archive structure.

Never use refactoring equality as new scientific confirmation. Run focused
checks first, then relevant regressions. Record command, environment, exit
status, expected result, actual result, and
`PASS | FAIL | BLOCKED | SKIPPED`.

Perform a final self-review against the task, planned change set, actual diff,
protected artifacts, and completion criteria. Use an independent reviewer only
for a high-risk block and only when John pre-authorized it.

## Gate 6 — Knowledge, evidence, and checkpoint

Update the active stage document and `roadmap.md` only when the authorized task
changes canonical state. Do not rewrite archives to remove historical
inconsistency.

Create an evidence record containing:

- task identity, profile, authority, and scope;
- planned change set and actual change log;
- reasons for deviations;
- source-to-decision traceability;
- checks and results;
- scientific interpretation limits;
- remaining risks and uncertainty;
- next proposed task, explicitly marked not authorized.

Create a checkpoint ZIP and SHA-256 only for a completed stage, an explicit
request from John, a high-risk or hard-to-reverse change without equivalent
verified recovery, or a portable accepted reproducible state. For an ordinary
reversible task, use the evidence record, exact change log, applicable checks,
and a state manifest; record checkpoint creation as `SKIPPED` with a reason.
Browser handoff is not part of the current Codex-only workflow. Exclude caches,
virtual environments, temporary files, and analysis-only artifacts.

## Gate 7 — Stop for John

Deliver:

1. outcome first;
2. changed-file list;
3. evidence and check table;
4. evidence of material source or notebook changes when applicable;
5. uncertainties and deferred items;
6. checkpoint filename and SHA-256 when applicable;
7. technical status and readiness;
8. a plain-Russian interpretation immediately after every material
   machine-readable status block, explaining meaning, basis, practical
   consequence, and any decision required from John; when a choice is requested,
   include viable alternatives and the evidence-based recommendation;
9. a separate `Задачи John` section.

Assign only:

```text
TECHNICAL_STATUS: PASS | FAIL | BLOCKED
READINESS: READY_FOR_JOHN_ACCEPTANCE | NOT_READY
```

Stop. Only John may assign `ACCEPTED_BY_JOHN`, `TASK_CLOSED`, or
`NEXT_BLOCK_AUTHORIZED`.
