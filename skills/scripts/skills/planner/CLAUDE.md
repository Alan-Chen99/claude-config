# planner/

Planning and execution workflows with QR gates, TW passes, and Dev execution. State files managed by LLM agents for session continuity. The design, the state files' lifecycles, the workflows and the QR protocol are in the planner skill's `INTENT.md` (`skills/planner/INTENT.md` from the repo root), which this code must conform to; field-level schemas are `shared/schema.py`, and `orchestrator/planner.py` and `orchestrator/executor.py` hold the `STEPS`.

## Shared Files

| File                    | What                                           | When to read                         |
| ----------------------- | ---------------------------------------------- | ------------------------------------ |
| `shared/schema.py`      | Pydantic schemas (context, plan, qr) and       | Understanding state file schemas,    |
|                         | validate_state() function                      | modifying schema definitions         |
| `shared/constraints.py` | Reusable orchestrator constraint strings and builders | Building planner/executor prompts, composing reusable constraint blocks |
| `shared/gates.py`       | Unified gate output builder                    | Understanding QR gate logic,         |
|                         | (`build_gate_output`)                          | modifying gate behavior              |
| `shared/routing.py`     | `route_work_phase()`: the one router behind the five work-phase router scripts | Changing how a phase picks execute or fix mode |
| `shared/resources.py`   | Path helpers, resource provider, context loading | Changing where a state file lives    |
| `shared/qr/`            | QR state loading, phases, types, blocking severities per iteration | QR iteration and severity logic |

## Subdirectories

| Directory           | What                                   | When to read                               |
| ------------------- | -------------------------------------- | ------------------------------------------ |
| `orchestrator/`     | Main workflows (planner, executor)     | Creating/executing plans                   |
| `architect/`        | Plan design sub-agent                  | Understanding planning workflow            |
| `developer/`        | Code filling and implementation        | Dev execution, diff creation               |
| `technical_writer/` | Documentation scrubbing and generation | TW passes, temporal cleanup                |
| `quality_reviewer/` | QR modules for all phases              | QR logic, validation, understanding gates  |
| `cli/`              | `cli.plan` and `cli.qr`: the validated, locked writes to `plan.json` and `qr-{phase}.json` | Changing a state mutation command |
| `shared/`           | Shared resources, schemas, conventions | Accessing conventions, resource management |

## State Files

All plan state lives in plan.json. Context captured separately in context.json. Who writes each and when: `INTENT.md`, "State Files".

| File              | What                                    | Mutability          | When to read                   |
| ----------------- | --------------------------------------- | ------------------- | ------------------------------ |
| `plan.json`       | Complete plan state (milestones, diffs, | mutable -> frozen   | All planning phases            |
|                   | code_intents, code_changes, docs)       |                     |                                |
| `context.json`    | User-provided planning context          | frozen after step 2 | Sub-agent context handover     |
| `qr-{phase}.json` | QA items for specific phase (ephemeral) | ephemeral           | QA decomposition, verification |
