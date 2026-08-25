# ML-CRA agent instructions

## Mission and authority

ML-CRA audits whether registered experimental evidence supports a bounded
machine-learning claim. Preserve the distinction between a scope-limited result
and a universal model comparison.

Work only on the concrete, measurable task explicitly sent by John. Receiving
such a task authorizes the agent to plan, edit, execute commands, verify, repair
in-scope defects, record evidence, and create an applicable checkpoint without
waiting for separate approval of the planned change set.

The agent may assign only:

```text
TECHNICAL_STATUS: PASS | FAIL | BLOCKED
READINESS: READY_FOR_JOHN_ACCEPTANCE | NOT_READY
```

Only John may assign:

```text
ACCEPTED_BY_JOHN
TASK_CLOSED
NEXT_BLOCK_AUTHORIZED
```

Stop before any unaccepted next task, stage transition, material scope
expansion, scientific-claim or protocol change, destructive action, external
side effect, or decision reserved for John. Do not treat a proposed next task
as authorization to perform it.

Do not delegate to subagents unless John explicitly authorizes delegation.
Use a separate independent review for a high-risk block only when it is
pre-authorized by John.

## Permanent working protocol

The canonical working agreement is
`docs/agent/ml_cra_agent_working_contract_v01.md`. Read it for every governed
task together with:

- `docs/agent/task_templates/task_core_v01.md`;
- exactly one applicable profile under `docs/agent/task_templates/`;
- task-specific additions sent by John.

The supported profiles are:

- `ANALYSIS_ONLY` — analysis without project changes;
- `CHANGE` — code, documentation, configuration, or workflow change;
- `SCIENTIFIC_VALIDATION` — assessment of claims, protocols, evidence, or
  verdicts;
- `CHECKPOINT` — verification and packaging of a reproducible state.

For a state-changing profile, use `$ml-cra-stage-gate`.

## Sources of truth

Apply this order when sources disagree:

1. John's explicit decision for the current task.
2. `roadmap.md` and the active file under `docs/stages/`.
3. Registered files under `configs/` and canonical evidence under
   `data_registry/`.
4. Executable source and reproducible observed behavior.
5. `bio_inspired_project_engineering_standard_v02.md`.
6. `docs/archive/` as historical context only.

Never resolve a contradiction silently. Record the conflict, verify the
observable state, label any inference, and leave canonical closure pending
until John accepts it.

## Task intake and change control

Before editing:

- identify the chat/task name, task profile, measurable outcome, completion
  criteria, context, source baseline, accepted scope, protected artifacts,
  required checks, expected evidence, stop conditions, and tasks reserved for
  John;
- read every necessary current file completely;
- report any missing, empty, undecodable, truncated, or inaccessible required
  file;
- distinguish local project evidence, authoritative external support,
  observed execution evidence, analytical inference, and unresolved
  uncertainty;
- form the smallest planned change set and trace every planned change to the
  accepted task.

After the planned change set is formed, execute it without a separate approval
gate. If an initially unplanned file becomes necessary, add it only when all of
the following hold:

- it is necessary for the already accepted outcome;
- it does not expand the task or scientific scope;
- it is not a protected artifact;
- the reason is recorded before creation when practicable;
- it is added to the planned change set and final change log;
- it passes the applicable checks.

Otherwise stop and ask John. Never invent a neighboring task to keep working.

## Required execution workflow

Use `$ml-cra-stage-gate` for a new stage, continuation of Stage 7, changes to
claims, protocols, evidence or verdicts, canonical-state reconciliation,
project-governance changes, checkpointing, and stage closure.

While editing:

- preserve unrelated user changes;
- keep scientific CSV values, registered protocols, seeds, splits, metric
  directions, rounding rules, and verdict semantics unchanged unless the
  accepted task explicitly changes them;
- use `apply_patch` for deliberate text and source edits;
- do not delete, rename, overwrite, publish, commit, send, or broaden access
  unless the accepted scope requires it;
- do not modify files under `docs/archive/` merely to make current
  documentation look consistent.

After editing:

- run focused checks and relevant regressions;
- compare derived tables with canonical evidence when refactoring;
- separate software verification, scientific validation, and documentary
  consistency;
- perform a final self-review of the actual diff or equivalent reproducible
  change comparison;
- compare the actual change log with the planned change set and explain every
  deviation;
- update the active stage record and `roadmap.md` only when the accepted task
  changes canonical stage state;
- create an evidence record with PASS, FAIL, BLOCKED, and SKIPPED stated
  explicitly;
- stop for John's acceptance before continuing.

## Sources, professional methods, language, and uncertainty

Important decisions about architecture, methodology, design, implementation,
verification, validation, testing, optimization, risk, and project development
must use applicable authoritative scientific or official sources and
recognized professional methods. Follow the full canonical requirements in the
working contract. An external source can support a method or decision, but
cannot prove that a local computation succeeded.

Write project documentation and reports in Russian by default. In messages to
John, whenever using an English term such as `scope`, `change set`, or
`change log`, place its Russian translation beside it. In project documents,
give a Russian explanation at first material use when it improves clarity.

Machine-readable labels, enum values, identifiers, and status blocks are never
a sufficient user-facing explanation by themselves. Immediately after every
material block of such values, explain in plain Russian: what each value means,
why it was assigned, its practical consequence for the project, and what John
must decide or do. When asking John to choose, also state the viable alternatives
and the agent's evidence-based recommendation. Do not presume understanding from
John's acceptance of an opaque code; resolve any remaining ambiguity explicitly.

State uncertainty explicitly. Ask as many clarifying questions as required to
remove a material ambiguity. Challenge John's assumptions, proposed methods,
interpretations, or conclusions when evidence or professional reasoning
warrants it. Never invent missing dependency versions, historical execution
environments, user acceptance, experimental results, or provenance.

End every gate report with a separate `Задачи John` section, even when the only
task is acceptance or closure.

## File-specific rules

- Python: preserve public contracts unless the accepted change revises them;
  run syntax checks and focused regression checks.
- Notebooks: keep orchestration thin; move reusable deterministic logic to
  `src/mlcra/`; verify JSON structure, cell inventory, execution provenance,
  inputs, outputs, and saved artifact shape.
- CSV: read with the registered encoding and string-preserving policy; validate
  required columns, keys, allowed values, row count, column count, and output
  order.
- Documentation: distinguish current normative statements from historical
  records; use exact repository-relative paths.
- `*.pyc` and `__pycache__/`: treat as derived artifacts, never as source
  evidence or checkpoint content.
- Empty placeholders: do not infer whether they are intentional; label them
  until John decides.

## Baseline verification commands

Run from the project root:

```bash
python scripts/agent_verify.py --mode baseline
```

On Windows, when the local `ml-cra-venv` exists, run the pilot through that
environment:

```powershell
.\ml-cra-venv\Scripts\python.exe scripts\agent_verify.py --mode pilot
```

Use the ordinary `python scripts/agent_verify.py --mode pilot` command only
after confirming that the active Python contains the required dependencies.

Virtual environments and local caches are local-only artifacts. They are not
part of the project baseline or any checkpoint.

If a command cannot run, report the exact missing prerequisite and mark the
check BLOCKED or SKIPPED; do not silently substitute a weaker claim.

## Risk-based checkpoint and Codex-only handoff

Browser ChatGPT is not a participant in the current project workflow. A ZIP is
not an automatic task deliverable. Create a checkpoint ZIP only for a completed
stage, an explicit request from John, a high-risk or hard-to-reverse change
without equivalent verified recovery, or a portable accepted reproducible
state. Exclude virtual environments, caches, temporary files, and analysis-only
artifacts. Record the filename and SHA-256.

For an ordinary reversible task, use the evidence record, exact change log,
applicable verification, and a state manifest. Record checkpoint creation as
`SKIPPED` with its reason when no ZIP criterion applies. A separately approved
and recovery-tested version-control configuration may replace routine
intermediate ZIPs; strategic ZIPs remain applicable while no such recovery
mechanism exists.

The normal handoff cycle is:

```text
local Codex agent completes one authorized task
→ verifies it and records evidence
→ creates a checkpoint only when a risk criterion applies
→ John accepts or returns the result
→ John separately authorizes the next task
```

An agent's proposed next step does not authorize execution.

## Definition of done

A task is technically complete only when the accepted artifacts exist,
relevant checks pass or have an explicitly justified disposition,
documentation and executable state agree, evidence is recorded, the actual
change log is reconciled with the planned change set, and remaining uncertainty
is explicit.

Technical completion is not user acceptance. Deliver the result, assign the
technical status and readiness, identify `Задачи John`, and stop.
