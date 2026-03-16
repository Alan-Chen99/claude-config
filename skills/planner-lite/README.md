# planner-lite

Lightweight planning and execution without subagent dispatch.

## Overview

Planner-lite solves the subagent-compatibility constraint: the full planner requires the Task tool for subagent dispatch, making it structurally unusable by subagents themselves. When a subagent needs planning capability, it cannot invoke the full planner because that would require nested Task tool calls.

Planner-lite provides a Bash-tool-compatible alternative. It collapses architect, developer, and technical writer roles into a single agent, emitting plan.md directly without JSON IR translation or multi-agent coordination. This enables any agent, including subagents, to invoke planning workflows via python scripts.

## Architecture

Two independent scripts using the DeepThink pattern:

- **plan.py**: 4-step planning workflow (explore, decompose, draft, self-review)
- **execute.py**: 4-step execution workflow (load, implement, self-review, complete)

State directory contains:

- **context.json**: Task specification, constraints, entry points, assumptions (handover artifact)
- **plan.md**: Human-readable plan output AND state artifact for execution phase

XML stdout protocol: Scripts emit XML blocks with `<step_header>`, `<current_action>` instructions, and `<invoke_after>` continuation commands. The calling LLM reads stdout and follows instructions literally. Scripts never use Task tool or AskUserQuestion; all orchestration happens via XML output parsed by the invoking agent.

## Design Decisions

| Decision | Rationale |
| -------- | --------- |
| **DL-001: DeepThink pattern over mode_main pattern** | Test framework requires WORKFLOW constant for discovery. Mode_main scripts lack WORKFLOW export. DeepThink pattern provides STEPS dict + STEP_HANDLERS dict + format_step_output() + WORKFLOW constant + argparse main() in a single self-contained file. |
| **DL-002: plan.md output over plan.json IR** | Single agent cannot parallelize architect/dev/TW roles. JSON IR adds translation overhead without multi-agent benefit. Markdown is both human-readable output AND state artifact. |
| **DL-003: Inline self-review over independent QR agents** | Subagent-compatible skill cannot dispatch Task tool. Independent QR requires separate agent. Structured checklist with 3-iteration limit partially compensates for confirmation bias. |
| **DL-004: Reuse context.json schema from planner** | Context.json captures task_spec, constraints, entry_points, assumptions. Same categories needed for execute phase handover. Reuse eliminates schema design work and enables familiarity. |
| **DL-005: Independent step numbering per script** | Convention is independent numbering per script (1-4 each). Continuous 1-8 numbering couples plan.py and execute.py. Independent numbering matches deepthink and planner patterns, allows script evolution without coupling. |
| **DL-006: No diagram generation in planner-lite** | Diagrams require architect+TW separation for quality. Single agent collapsing all roles cannot produce good diagrams. Skip diagrams in lite version to avoid low-quality output. |
| **DL-007: prompt-engineer as recommended not mandatory** | Full planner constraint requires prompt-engineer at sub-agent steps. Planner-lite has no sub-agents (single-agent design per DL-002, DL-003). Constraint is structurally inapplicable: "sub-agent steps" prerequisite does not exist. Prompt-engineer downgraded to recommended guidance in XML output prompts. If planner-lite gains sub-agent dispatch, re-elevate to mandatory. |

## Invariants

- Scripts emit XML to stdout; calling agent reads and follows instructions
- No Task tool usage (subagent-compatibility requirement)
- No AskUserQuestion in step scripts (orchestration is XML-mediated)
- WORKFLOW constant must be exported for test framework discovery
- State directory contains all artifacts (context.json, plan.md)
- plan.md is both human-readable output AND state artifact for execution

## Tradeoffs

### Quality vs Compatibility

Single agent produces lower quality than multi-agent separation. Planner uses independent architect, developer, technical writer, and quality review agents with role-specific prompts and iterative refinement. Planner-lite collapses these into one agent.

Accepted because subagent-compatibility requires Bash-tool-only operation. Planner-lite is explicitly the lite version: reduced quality in exchange for broader invocability.

### Self-Review vs Independent QR

Self-review suffers from confirmation bias. Independent QR agents in full planner provide objective assessment. Planner-lite uses inline self-review with structured checklists.

Structured checklists with specific pass/fail items partially compensate. 3-iteration limit prevents infinite loops while allowing convergence. Accepted as necessary compromise for single-agent operation.

### Simplicity vs Completeness

Planner-lite omits:

- JSON IR with CAS versioning (unnecessary without multi-agent state mutation)
- Separate QR state files (inline review needs no file mediation)
- Independent TW pass (single agent documents inline)
- Diagram generation (quality requires role separation)

These omissions reduce overhead and complexity. Planner-lite targets straightforward planning scenarios where subagent invocability matters more than exhaustive rigor.
