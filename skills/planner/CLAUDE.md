# planner/

Planning and execution skill with quality review gates.

## Files

| File        | What                                                 | When to read                                  |
| ----------- | ---------------------------------------------------- | --------------------------------------------- |
| `SKILL.md`  | Skill activation and invocation                      | Using the planner skill                       |
| `INTENT.md` | Authoritative design specification and invariants    | Before changing any planner script or state file |

## Subdirectories

| Directory    | What                                         | When to read                                 |
| ------------ | -------------------------------------------- | -------------------------------------------- |
| `resources/` | Templates injected into agent prompts        | Changing plan.json fields or a resource      |

Python code: `skills/scripts/skills/planner/` (orchestrator/, architect/, developer/, technical_writer/, quality_reviewer/, cli/, shared/)

## Universal Conventions

Scripts reference these conventions from `.claude/conventions/`:

| Convention          | When to read                                 |
| ------------------- | -------------------------------------------- |
| `documentation.md`  | Understanding CLAUDE.md/README.md format     |
| `structural.md`     | Updating QR RULE 2 or planner decision audit |
| `temporal.md`       | Updating TW/QR temporal contamination logic  |
| `severity.md`       | Understanding QR severity levels             |
| `intent-markers.md` | Understanding :PERF:/:UNSAFE: markers        |
