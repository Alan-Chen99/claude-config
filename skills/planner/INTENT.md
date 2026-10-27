# Planner Skill Design Intent

Authoritative design specification for the planner skill: the properties its scripts must keep, and why. Implementation MUST conform to this spec. Field-level schemas are the Pydantic v2 models in `shared/schema.py`; step text is in the scripts. Paths are relative to `skills/scripts/skills/planner/`.

## Philosophy

**RESOLVE AMBIGUITY EARLY**: Questions about requirements, architecture or approach are answered during planning, before code is written. Execution is mechanical.

**CAPTURE INVISIBLE KNOWLEDGE**: Decisions, rationale and context live in state files, so a sub-agent picking up work has full context. No information lives only in conversation history.

**QUALITY OVER SPEED**: LLMs make mistakes. QR gates with fix loops catch errors before they propagate; the skill trades execution time for correctness.

## State Files

All live in the state directory and last one planning session, so they carry no schema version.

| File              | Written by                                                                                              | Lifecycle                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `context.json`    | Orchestrator LLM at step 2, the one state file it writes                                                | Frozen after step 2; every later sub-agent, QR included, reads it to check work against user intent |
| `plan.json`       | Scripts only: the orchestrator's skeleton at step 1, then `cli.plan` for architect (step 3), developer (7), technical writer (11) | The plan IR; `plan.md` is rendered from it when step 14 passes              |
| `qr-{phase}.json` | QR decompose creates it; verify agents update items through `cli.qr`; the route step deletes it on PASS | One file per phase (plan-design, plan-code, plan-docs, impl-code, impl-docs) |

Separate QR files per phase keep a fixer's items to its own phase and let each phase's QR pass or fail independently.

plan.json ownership:

- **Architect**: overview, planning_context, milestones with code_intents, diagram_graphs as graph IR (nodes and edges, `ascii_render` left null).
- **Developer**: `code_changes[].diff`, each implementing a code_intent through `intent_ref`.
- **Technical writer**: `code_changes[].doc_diff` (module comments, docstrings, inline comments); doc-only code_changes for cross-cutting README.md files (`intent_ref: null`); each diagram's `ascii_render`.

Waves execute in array order: every milestone in W-001 completes before W-002 begins; milestones within a wave may run in parallel.

Agents change plan.json and qr-{phase}.json only through the CLI. `cli.plan` restricts each role to its commands and versions every entity (Compare-And-Swap): a create omits `--id` and `--version`, an update must pass the current version, and a mismatch prints the current entity for retry, so no agent overwrites changes it has not read. `cli.qr` serializes the parallel verify agents' writes to a shared qr file. A sub-agent's prompt must surface its role's CLI commands with usage examples: it cannot use a command it does not know.

## Workflows

**Planning** (`orchestrator/planner.py`), 14 steps: plan-init (1), context-verify (2), then three QR-able phases: plan-design (architect, steps 3-6), plan-code (developer, 7-10), plan-docs (technical writer, 11-14). The plan is approved when step 14 passes.

**Execution** (`orchestrator/executor.py`), 10 steps: exec-init builds the wave list (1); for each wave, impl-code (developer, up to 4 in parallel, steps 2-5) and impl-docs (technical writer, 6-9); wave-next (10) loops to step 2 until no wave remains.

**Diagrams**: the architect decides what to communicate (graph structure, validated by `validate_refs()`), the technical writer how (rendering). The writer renders each graph to fixed-width ASCII, 80 columns at most: `+` corners, `-` and `|` edges, arrows such as `-->` and `v`. The type defaults to architecture; state, sequence or dataflow only for a state machine, multi-party protocol or data pipeline.

## QR Workflow

Each QR-able phase is a 4-step block:

1. **Work** (1 sub-agent): a router script dispatches the execute or the fix workflow from state.
2. **QR decompose** (1 sub-agent): writes qr-{phase}.json, all items TODO.
3. **QR verify** (N parallel sub-agents): each verifies a batch of related items and must conclude with `PASS` or `FAIL: <reason>`; malformed output counts as FAIL.
4. **QR route** (orchestrator script): reads qr-{phase}.json, and the LLM sees only the routing decision. All pass: delete the file, proceed. Any failure: loop to the work step, whose router dispatches the fix workflow; after the fix, QR verifies again.

Each phase has a router, an execute and a qr_fix script under its agent's directory, and qr_decompose and qr_verify scripts under `quality_reviewer/`.

**Decomposition**, the 8-step workflow in `quality_reviewer/prompts/decompose.py` and the per-phase scripts, works top-down, then bottom-up: holistic concerns first, then an enumeration of what the plan contains, used as the completeness checklist, since enumeration alone misses cross-cutting concerns. Critical concerns get an umbrella item (scope `*`) and specific items; overlap is acceptable, gaps are not. An item's `scope` is one free-form location string (`*`, `file:src/auth.py:L10-L50`, `function:validate_token`, `component:auth-flow`), not a field taxonomy; scripts pass it to verify prompts verbatim.

### QR Iteration

The `iteration` field in qr-{phase}.json is the only record of the QR loop count; the verify step increments it on each retry. The file path is always `{state_dir}/qr-{phase}.json`, computed, never passed.

Decomposition runs once per phase: if the file exists, the decompose step skips to verify. The item set is the verification target; regenerating it each iteration adds failures unrelated to the original ones and the fix-verify loop stops converging. File existence, not the iteration count, signals "decomposed". Delete the file to force a fresh decomposition.

## Question Relay

1. A sub-agent that needs user input saves its state to plan.json, emits `<needs_user_input>` XML and stops.
2. The orchestrator extracts the questions and calls AskUserQuestion.
3. It reinvokes a fresh sub-agent with the accumulated answers in a `<user_response>` block; the new sub-agent reads plan.json and continues.

Sub-agents cannot be resumed: context is restored from state files and the dispatch prompt, which carries the context.json categories, in full at the first handover (step 2 to 3) and tersely after.

## Invariants

**Sub-agents cannot launch sub-agents**. Only the orchestrator dispatches. Maintains audit trail, prevents hidden dependencies.

**Sub-agents cannot invoke AskUserQuestion**. A sub-agent that needs user input yields through the Question Relay; only the orchestrator asks the user.

**Orchestrator LLM never reads/writes state files**, context.json at step 2 excepted. It must not use Read, Write or Edit on plan.json, context.json or qr-{phase}.json; context flows through dispatch prompts. The orchestrator's Python may read them, e.g. `load_qr_state()` to pick items for dispatch: the rule binds the LLM.

**Orchestrator is a dumb dispatcher**. The orchestrator routes based on status flags (pass/fail) and step numbers. It never makes quality judgments ("the plan looks comprehensive"), never decides to "proceed anyway" when protocol requires iteration, and never skips steps based on subjective assessment.

**Sub-agent self-validation**. Every sub-agent that writes plan.json or qr-{phase}.json, in execute and fix workflows alike, loads the file, validates it with `validate_state()`, and fixes it until valid before returning. The orchestrator never sees schema validation errors.

**User authority is absolute**. Agent findings may be wrong. User decisions override everything.

**Always run scripts**. Every step invokes a Python script. No free-form execution. Scripts emit prompts; the LLM performs the work.

**Router dispatch at step 1 only**. Router scripts detect state at step 1 and dispatch to a workflow script. Later steps within a workflow script MUST NOT dispatch to other scripts.

**State detection over flags**. Work scripts detect their mode from qr-{phase}.json: FAIL items mean the fix workflow. The orchestrator dispatches the same step number in either mode.

**No distributed QR state**. All QR state lives in qr-{phase}.json. `--qr-fail` and `--qr-iteration` MUST NOT exist: routers compute the path from state_dir and phase, and the iteration is read from the file. The only QR CLI arguments are `--qr-status` (the orchestrator's aggregated verdict, gate steps) and `--qr-item` (a verify agent's items).

**Adaptive item generation**. Decomposition creates as many items as the content requires. No fixed counts or caps.

**QR decompose output contract**. Decompose writes qr-{phase}.json and dispatches nothing: the verify step (`qr_verify_step()` in `orchestrator/planner.py`) reads that file and builds the verify agents' dispatch.

**QR file lifecycle**. qr-{phase}.json is created by decompose step, updated by verify agents, deleted by route step on PASS. The file's existence signals "QR in progress"; its absence signals "no QR done yet" or "QR passed and cleaned up".

**QR iteration limit**. Maximum 5 iterations per QR phase. The severities that block narrow as the iteration rises: `get_blocking_severities()` in `shared/qr/constants.py`.
