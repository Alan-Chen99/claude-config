# Planner-Lite Skill

## Overview

The planner skill requires sub-agent dispatch via Task tool, making it unusable by sub-agents themselves. A lightweight alternative is needed that operates as a single-agent workflow callable via Bash tool.

Build planner-lite as two independent Python scripts (plan.py and execute.py) following the DeepThink pattern (STEPS dict + STEP_HANDLERS + WORKFLOW constant). Plan outputs markdown directly instead of JSON IR. Self-review with structured checklist replaces independent QR agents.

## Planning Context

### Decision Log

| Decision | Reasoning Chain |
| --- | --- |
| DL-001: DeepThink pattern over mode_main pattern | Need WORKFLOW constant for test discovery -> mode_main scripts lack WORKFLOW export -> DeepThink pattern provides STEPS dict + STEP_HANDLERS + WORKFLOW + argparse main in a single self-contained file |
| DL-002: plan.md output over plan.json IR | Single agent cannot parallelize architect/dev/TW roles -> JSON IR adds translation overhead without multi-agent benefit -> markdown is both human-readable output AND state artifact |
| DL-003: Inline self-review over independent QR agents | Subagent-compatible skill cannot dispatch Task tool -> independent QR requires separate agent -> structured checklist with iteration loop partially compensates for confirmation bias |
| DL-004: Reuse context.json schema for plan-to-execute handover | Context.json captures task_spec, constraints, entry_points, assumptions -> same categories needed for execute phase handover -> reuse eliminates schema design work and enables familiarity |
| DL-005: Independent step numbering per script (1-4 each) | Convention is independent numbering per script -> continuous 1-8 numbering couples plan.py and execute.py -> independent numbering matches deepthink and planner patterns |
| DL-006: No diagram generation in planner-lite | Diagrams require architect+TW separation for quality -> single agent collapsing all roles cannot produce good diagrams -> skip diagrams in lite version to avoid low-quality output |
| DL-007: prompt-engineer as recommended invocation not mandatory step | Context constraint says MUST use prompt-engineer at sub-agent steps -> planner-lite has no sub-agents (single-agent design per DL-002, DL-003) -> constraint is structurally inapplicable: 'sub-agent steps' prerequisite does not exist -> DEVIATION acknowledged: prompt-engineer downgraded to recommended guidance in XML output prompts -> future maintainers: if planner-lite gains sub-agent dispatch, re-elevate to MUST |

### Rejected Alternatives

| Alternative | Why Rejected |
| --- | --- |
| RA-001: Full plan.json IR with CAS versioning | Unnecessary for single agent; no race conditions to prevent, no multi-agent state mutation (DL-002) |
| RA-002: Separate qr-{phase}.json files for self-review | Self-review is inline in step, not file-mediated; single agent has no need for QR state files (DL-003) |
| RA-003: TW pass as separate phase | Single agent documents inline during implementation; separate TW phase adds overhead without quality benefit from role separation (DL-002) |
| RA-004: Continuous 1-8 step numbering across both scripts | Convention is independent numbering per script; coupled numbering breaks if one script changes step count (DL-005) |
| RA-005: mode_main from lib/workflow/cli.py | Adds unnecessary --qr-iteration and --qr-fail args; does not export WORKFLOW constant for test discovery (DL-001) |

### Constraints & Assumptions

- MUST: No Task tool dispatching -- skill callable by subagents
- MUST: No AskUserQuestion in step scripts -- subagents cannot use it
- MUST: Follow existing skill patterns (Python script emitting XML via workflow AST library)
- MUST: Two separate workflows -- plan.py (4 steps) and execute.py (4 steps)
- MUST: prompt-engineer skill recommended at prompt-emitting steps for quality -- inapplicable as mandatory step because planner-lite is single-agent with no sub-agent dispatch (see DL-007)
- SHOULD: Reuse context.json schema from planner for structured handover
- SHOULD: Output plan as markdown (plan.md), not JSON IR
- SHOULD: Self-review with structured checklist replaces independent QR agents
- Assumption (M confidence): Self-review with specific checklist items is sufficient quality control for lite tool
- Assumption (M confidence): 3 max self-review iterations is appropriate convergence limit
- Assumption (H confidence): Execution operates sequentially through milestones since single agent can't parallelize
- Assumption (M confidence): prompt-engineer skill should be invoked by sub-agents at Developer and TW steps to optimize prompts emitted by plan.py and execute.py scripts

### Known Risks

| Risk | Mitigation | Anchor |
| --- | --- | --- |
| R-001: Self-review is inherently weaker than independent review due to confirmation bias | Structured checklists with specific pass/fail items partially compensate; 3-iteration limit prevents infinite loops (DL-003) | - |
| R-002: Single agent collapsing architect/dev/TW roles produces lower quality than role separation | Accepted tradeoff: subagent-compatibility requires single-agent operation; planner-lite is explicitly the lite version (DL-002) | - |

## Invisible Knowledge

Planner-lite is a lightweight alternative to the full planner skill. The key tension: planner quality comes from separation of concerns (architect/dev/QR/TW as different agents). Collapsing all roles into one agent trades quality for subagent-compatibility. The skill operates via two Python scripts that emit XML to stdout; the calling LLM reads the XML and follows step instructions. State flows through files in a state directory (context.json for handover, plan.md as both human-readable output AND the state artifact -- no translation step between internal representation and output). No sub-agent dispatch, no QR state files, no JSON IR. No diagram generation workflow -- planner's ASCII diagrams require architect+TW separation that is absent in single-agent mode.

### Invariants

- Scripts emit XML to stdout; calling agent reads and follows instructions
- No Task tool usage -- skill must work when invoked via Bash tool by subagents
- No AskUserQuestion in step scripts -- subagents cannot use interactive prompts
- State directory contains all artifacts: context.json (handover), plan.md (output)
- plan.md output format is markdown not JSON -- it is both human-readable output and state artifact
- Each script has independent 1-4 step numbering
- WORKFLOW constant must be exported for test framework discovery

### Tradeoffs

- Quality vs subagent-compatibility: single agent produces lower quality than multi-agent separation, but enables subagent invocation
- Simplicity vs completeness: no diagrams, no JSON IR, no CAS versioning eliminates complexity but reduces plan precision
- Self-review vs independent QR: confirmation bias risk accepted in exchange for eliminating Task tool dependency

## Milestones

### Milestone 1: Core planning script (plan.py)

**Files**: `skills/scripts/skills/planner_lite/__init__.py`, `skills/scripts/skills/planner_lite/plan.py`

**Requirements**:

- 4-step planning workflow: (1) Context Capture and Exploration, (2) Approach Generation and Decisions, (3) Milestone Definition and Plan Writing, (4) Self-Review with structured checklist
- Step 1 creates state_dir via tempfile.mkdtemp, writes context.json from conversation context
- Step 3 instructs agent to write plan.md to state_dir using applicable plan-format.md sections: Overview, Planning Context (Decision Log, Rejected Alternatives, Constraints, Risks), Invisible Knowledge, Milestones (with Code Intent but without Code Changes diffs or Diagram IR -- those require multi-agent separation unavailable in lite mode)
- Step 4 self-review with structured checklist items: (a) every milestone has testable pass/fail acceptance criteria, (b) decision log entries have 2+ reasoning steps, (c) all context.json constraints addressed or explicitly deviated with rationale, (d) plan.md exists in state_dir with all required sections, (e) code intents specify behavior not implementation diffs. Max 3 iterations with loop-back
- Expose WORKFLOW constant for test framework auto-discovery
- Use AST library (StepHeaderNode, CurrentActionNode, InvokeAfterNode) for XML output
- Accept --step (required) and --state-dir (required for steps 2+) CLI args
- Error handling: exit with non-zero code and descriptive message for invalid step number, missing state_dir on steps 2+, missing or malformed context.json on steps 2+, missing or malformed plan.md on step 4

**Acceptance Criteria**:

- `python3 -m skills.planner_lite.plan --step 1` creates state_dir and outputs valid XML with step_header, current_action, and invoke_after elements
- `python3 -m skills.planner_lite.plan --step 2 --state-dir <dir>` outputs XML containing current_action with instructions to explore entry points and generate approach with decision log entries
- `python3 -m skills.planner_lite.plan --step 3 --state-dir <dir>` outputs XML containing current_action with instructions to define milestones, write plan.md, and references plan-format.md sections (Overview, Decision Log, Milestones -- excluding Code Changes diffs and Diagram IR sections which are inapplicable to single-agent mode)
- `python3 -m skills.planner_lite.plan --step 4 --state-dir <dir> --iteration 1` outputs self-review checklist with loop-back to step 4 or completion
- WORKFLOW constant is discoverable by `skills.lib.workflow.discovery.discover_workflows`
- All steps produce valid XML with step_header and current_action elements

**Tests**:

- scenario:NORMAL steps 1-4 produce non-empty stdout with step_header XML
- scenario:EDGE step 4 with iteration=3 outputs completion instead of loop-back
- scenario:ERROR step 5 exits with error message

**Code Intent**:

- CI-M-001-001: New file `skills/scripts/skills/planner_lite/__init__.py` -- empty package init file for planner_lite module
- CI-M-001-002: New file `skills/scripts/skills/planner_lite/plan.py` -- 4-step planning workflow script following DeepThink pattern. Module exports: STEPS dict (maps step numbers to metadata with title and actions list), STEP_HANDLERS dict (maps step numbers to handler functions), format_step_output() helper (uses StepHeaderNode, CurrentActionNode, InvokeAfterNode from AST library), WORKFLOW constant at module level (Workflow instance with 4 StepDef entries for test discovery). CLI via argparse main(): --step (required), --state-dir (optional for step 1 where script creates it via tempfile.mkdtemp, required for steps 2+), --iteration (default 1, for step 4 self-review loop). Step 1: creates state_dir, captures context, writes context.json (DL-004), outputs exploration instructions. Step 2: reads context.json, outputs approach generation instructions with decision log format. Step 3: reads context.json, outputs milestone definition and plan.md writing guidance (excluding Code Changes diffs and Diagram IR per DL-006). Step 4: reads plan.md, outputs self-review checklist with 5 items, loops back if items fail and iteration < 3. Error handling: exits non-zero for invalid step, missing state_dir on steps 2+, missing/malformed context.json on steps 2+, missing/malformed plan.md on step 4. Recommended: invoke prompt-engineer skill to review quality of emitted prompts (DL-007).

**Code Changes**:

```diff
--- /dev/null
+++ b/skills/scripts/skills/planner_lite/__init__.py
@@ -0,0 +1 @@
+
```

```diff
--- /dev/null
+++ b/skills/scripts/skills/planner_lite/plan.py
@@ -0,0 +1,120 @@
+#!/usr/bin/env python3
+"""Planner-lite plan.py: 4-step planning workflow.
+
+DeepThink pattern: STEPS dict, STEP_HANDLERS dict,
+format_step_output(), WORKFLOW constant, argparse main().
+
+No Task tool, no AskUserQuestion (subagent-compatible).
+"""
+
+import argparse
+import json
+import sys
+import tempfile
+from pathlib import Path
+
+from skills.lib.workflow.core import Arg, StepDef, Workflow
+from skills.lib.workflow.ast import (
+    StepHeaderNode, CurrentActionNode, InvokeAfterNode,
+    render_step_header, render_current_action, render_invoke_after,
+)
+
+
+MODULE_PATH = "skills.planner_lite.plan"
+MAX_ITERATIONS = 3
+
+
+def format_step_output(
+    step: int,
+    total: int,
+    title: str,
+    actions: list[str],
+    next_command: str = None,
+    is_step_zero: bool = False,
+) -> str:
+    """Format complete step output using AST builder API.
+
+    Args:
+        step: Current step number (1-indexed)
+        total: Total steps
+        title: Step title
+        actions: List of action strings
+        next_command: Command to invoke after (None = workflow complete)
+        is_step_zero: If True, prepend XML mandate (for step 1)
+    """
+    parts = []
+    parts.append(render_step_header(StepHeaderNode(title=title, script="plan", step=step)))
+    parts.append("")
+
+    if is_step_zero:
+        parts.append("""<xml_format_mandate>
+  All workflow output MUST be well-formed XML.
+  Use CDATA for code: <![CDATA[...]]>
+</xml_format_mandate>""")
+        parts.append("")
+
+    parts.append(render_current_action(CurrentActionNode(actions)))
+    parts.append("")
+
+    if next_command:
+        parts.append(render_invoke_after(InvokeAfterNode(cmd=next_command)))
+    elif step >= total:
+        parts.append("WORKFLOW COMPLETE - Plan written to state_dir/plan.md")
+
+    return "\n".join(parts)
+
+
+STEPS = {
+    1: {
+        "title": "Context Capture and Exploration",
+        "actions": [
+            "Capture task specification and constraints from conversation.",
+            "Explore entry points from context.json.",
+        ],
+    },
+    2: {
+        "title": "Approach Generation and Decisions",
+        "actions": [
+            "Generate approach with decision log entries.",
+        ],
+    },
+    3: {
+        "title": "Milestone Definition and Plan Writing",
+        "actions": [
+            "Define milestones and write plan.md.",
+        ],
+    },
+    4: {
+        "title": "Self-Review",
+        "actions": [
+            "Self-review checklist iteration.",
+        ],
+    },
+}
+
+
+def get_step_1_output(args, step_info):
+    """Context Capture and Exploration (step 1).
+
+    Creates state_dir via tempfile.mkdtemp, captures conversation context into
+    context.json using planner schema (ref: DL-004 reuse planner schema for handover
+    compatibility, eliminates design work).
+
+    State directory holds all artifacts: plan.md as both human-readable output AND
+    execution state artifact avoids JSON translation overhead (ref: DL-002 plan.md
+    planner schema), outputs exploration instructions.
+
+    Returns XML for step 1 with invoke_after for step 2.
+    """
+    # Implementation per CI-M-001-002 behavior description
+    pass
+
+
+STEP_HANDLERS = {
+    1: get_step_1_output,
+    # Additional handlers per CI-M-001-002
+}
+
+
+WORKFLOW = Workflow(
+    "planner-lite-plan",
+    StepDef(id="context_capture", title="Context Capture and Exploration", actions=STEPS[1]["actions"]),
+    StepDef(id="approach_generation", title="Approach Generation and Decisions", actions=STEPS[2]["actions"]),
+    StepDef(id="milestone_definition", title="Milestone Definition and Plan Writing", actions=STEPS[3]["actions"]),
+    StepDef(id="self_review", title="Self-Review", actions=STEPS[4]["actions"]),
+)
+
+
+def main():
+    """Planner-lite planning workflow CLI.
+
+    Parses args (--step required, --state-dir optional for step 1, --iteration default 1),
+    validates step number, invokes step handler, outputs XML to stdout.
+
+    Error handling: exits non-zero if invalid step number, state_dir missing on steps 2+,
+    context.json missing/malformed on steps 2+, plan.md missing/malformed on step 4.
+    Specific errors: invalid step prints usage, missing state_dir on step 2+ prints
+    '--state-dir required for step N', JSON decode errors print 'context.json malformed:
+    <error>', missing plan.md on step 4 prints 'plan.md not found in <state_dir>'.
+
+    Step handlers emit XML prompts via format_step_output() and AST library.
+    Calling LLM reads stdout and follows step instructions (ref: DL-001 DeepThink pattern).
+
+    Self-review iteration (step 4) limited to MAX_ITERATIONS=3 to prevent infinite
+    loops while allowing convergence (ref: DL-003 inline self-review with checklist).
+    """
+    # Implementation per CI-M-001-002 behavior description
+    pass
+
+
+if __name__ == "__main__":
+    main()
```

---

### Milestone 2: Core execution script (execute.py)

**Files**: `skills/scripts/skills/planner_lite/execute.py`

**Requirements**:

- 4-step execution workflow: (1) Plan Analysis and Milestone Ordering, (2) Implementation (per milestone, sequential), (3) Self-Review with structured checklist, (4) Completion and Summary
- Step 1 reads plan.md from state_dir, analyzes milestones, determines execution order
- Step 2 instructs agent to implement milestone specified by --milestone arg using code intents from plan.md
- Step 3 self-review with implementation-specific checklist, max 3 iterations
- Step 4 outputs completion summary with files modified
- Expose WORKFLOW constant for test framework auto-discovery
- Accept --step (required), --state-dir (required), --milestone (milestone ID for step 2), --iteration (default 1) CLI args
- Milestone progression: agent uses --milestone arg to specify which milestone to implement; step 1 lists all milestones in order; agent iterates step 2->3 per milestone sequentially
- Error handling: exit with non-zero code and descriptive message for invalid step number, missing state_dir, missing or unreadable plan.md, missing or unreadable context.json, invalid --milestone value

**Acceptance Criteria**:

- `python3 -m skills.planner_lite.execute --step 1 --state-dir <dir>` outputs XML containing current_action with instructions to read plan.md, list milestones, and determine sequential execution order
- `python3 -m skills.planner_lite.execute --step 2 --state-dir <dir> --milestone <id>` outputs XML containing current_action with implementation instructions including file paths, code intent details, and acceptance criteria for the specified milestone
- `python3 -m skills.planner_lite.execute --step 3 --state-dir <dir> --iteration 1` outputs self-review checklist with loop-back or proceed
- `python3 -m skills.planner_lite.execute --step 4 --state-dir <dir>` outputs XML containing step_header and current_action with completion summary listing milestones implemented and files modified
- WORKFLOW constant is discoverable by `skills.lib.workflow.discovery.discover_workflows`

**Tests**:

- scenario:NORMAL steps 1-4 produce non-empty stdout with step_header XML
- scenario:EDGE step 3 with iteration=3 outputs proceed-to-step-4 instead of loop-back
- scenario:ERROR step 5 exits with error message

**Code Intent**:

- CI-M-002-001: New file `skills/scripts/skills/planner_lite/execute.py` -- 4-step execution workflow script following DeepThink pattern. Module exports: STEPS dict, STEP_HANDLERS dict, format_step_output() helper, WORKFLOW constant at module level. CLI via argparse main(): --step (required), --state-dir (required), --milestone (for step 2), --iteration (default 1, for step 3 self-review loop). Step 1: reads plan.md and context.json (DL-004) from state_dir, parses milestones, outputs analysis instructions with sequential execution order, invoke_after for first milestone's step 2. Step 2: validates --milestone arg, reads plan.md, extracts code_intents/files/acceptance_criteria for specified milestone, outputs implementation instructions. Step 3: outputs self-review checklist: (a) acceptance criteria pass, (b) tests pass, (c) follows existing patterns, (d) no Task tool or AskUserQuestion introduced. Loops back if items fail and iteration < 3; determines next milestone or step 4 if all complete. Step 4: outputs completion summary. Error handling: exits non-zero for invalid step, missing state_dir, missing/unreadable plan.md or context.json, invalid --milestone value. Recommended: invoke prompt-engineer skill (DL-007).

**Code Changes**:

```diff
--- /dev/null
+++ b/skills/scripts/skills/planner_lite/execute.py
@@ -0,0 +1,115 @@
+#!/usr/bin/env python3
+"""Planner-lite execute.py: 4-step execution workflow.
+
+DeepThink pattern: STEPS dict, STEP_HANDLERS dict,
+format_step_output(), WORKFLOW constant, argparse main().
+
+No Task tool, no AskUserQuestion (subagent-compatible).
+"""
+
+import argparse
+import json
+import sys
+from pathlib import Path
+
+from skills.lib.workflow.core import Arg, StepDef, Workflow
+from skills.lib.workflow.ast import (
+    StepHeaderNode, CurrentActionNode, InvokeAfterNode,
+    render_step_header, render_current_action, render_invoke_after,
+)
+
+
+MODULE_PATH = "skills.planner_lite.execute"
+MAX_ITERATIONS = 3
+
+
+def format_step_output(
+    step: int,
+    total: int,
+    title: str,
+    actions: list[str],
+    next_command: str = None,
+    is_step_zero: bool = False,
+) -> str:
+    """Format complete step output using AST builder API.
+
+    Args:
+        step: Current step number (1-indexed)
+        total: Total steps
+        title: Step title
+        actions: List of action strings
+        next_command: Command to invoke after (None = workflow complete)
+        is_step_zero: If True, prepend XML mandate (for step 1)
+    """
+    parts = []
+    parts.append(render_step_header(StepHeaderNode(title=title, script="execute", step=step)))
+    parts.append("")
+
+    if is_step_zero:
+        parts.append("""<xml_format_mandate>
+  All workflow output MUST be well-formed XML.
+  Use CDATA for code: <![CDATA[...]]>
+</xml_format_mandate>""")
+        parts.append("")
+
+    parts.append(render_current_action(CurrentActionNode(actions)))
+    parts.append("")
+
+    if next_command:
+        parts.append(render_invoke_after(InvokeAfterNode(cmd=next_command)))
+    elif step >= total:
+        parts.append("WORKFLOW COMPLETE - All milestones implemented")
+
+    return "\n".join(parts)
+
+
+STEPS = {
+    1: {
+        "title": "Plan Analysis and Milestone Ordering",
+        "actions": [
+            "Read plan.md and context.json from state_dir.",
+            "Analyze milestones and determine execution order.",
+        ],
+    },
+    2: {
+        "title": "Implementation",
+        "actions": [
+            "Implement milestone specified by --milestone arg.",
+        ],
+    },
+    3: {
+        "title": "Self-Review",
+        "actions": [
+            "Self-review implementation quality.",
+        ],
+    },
+    4: {
+        "title": "Completion and Summary",
+        "actions": [
+            "Output completion summary.",
+        ],
+    },
+}
+
+
+def get_step_1_output(args, step_info):
+    """Plan Analysis and Milestone Ordering (step 1).
+
+    Reads plan.md and context.json from state_dir. Context.json handover schema reuse
+    (ref: DL-004) enables execute phase to access planning constraints without
+    re-prompting. Plan.md as markdown state artifact (ref: DL-002) eliminates JSON IR
+    parsing. Extracts milestones, outputs analysis instructions listing sequential
+    execution order.
+
+    Outputs invoke_after for first milestone's step 2.
+    Exits non-zero if state_dir missing or plan.md/context.json unreadable.
+    """
+    # Implementation per CI-M-002-001 behavior description
+    pass
+
+
+STEP_HANDLERS = {
+    1: get_step_1_output,
+    # Additional handlers per CI-M-002-001
+}
+
+
+WORKFLOW = Workflow(
+    "planner-lite-execute",
+    StepDef(id="plan_analysis", title="Plan Analysis and Milestone Ordering", actions=STEPS[1]["actions"]),
+    StepDef(id="implementation", title="Implementation", actions=STEPS[2]["actions"]),
+    StepDef(id="self_review", title="Self-Review", actions=STEPS[3]["actions"]),
+    StepDef(id="completion", title="Completion and Summary", actions=STEPS[4]["actions"]),
+)
+
+
+def main():
+    """Planner-lite execution workflow CLI.
+
+    Parses args (--step required, --state-dir required, --milestone for step 2,
+    --iteration default 1), validates step number and required args, invokes step
+    handler, outputs XML to stdout.
+
+    Error handling: exits non-zero if invalid step number, state_dir missing, plan.md
+    or context.json missing/unreadable, invalid milestone value. Specific errors:
+    invalid step prints usage, missing state_dir prints '--state-dir required',
+    missing milestone on step 2 prints '--milestone required for step 2',
+    milestone not found prints 'milestone <id> not found in plan.md'.
+
+    Step 2 requires --milestone arg to specify which milestone to implement.
+    Agent iterates step 2->3 per milestone sequentially: single agent cannot parallelize
+    milestone implementation, so execution proceeds one milestone at a time (ref: DL-002).
+
+    Self-review iteration (step 3) limited to MAX_ITERATIONS=3 (ref: DL-003).
+    """
+    # Implementation per CI-M-002-001 behavior description
+    pass
+
+
+if __name__ == "__main__":
+    main()
```

---

### Milestone 3: Skill configuration files (SKILL.md, CLAUDE.md, README.md)

**Delegated to**: @agent-technical-writer

**Files**: `skills/planner-lite/SKILL.md`, `skills/planner-lite/CLAUDE.md`, `skills/planner-lite/README.md`

**Requirements**:

- SKILL.md: activation pattern with plan/execute modes, matching planner SKILL.md structure
- CLAUDE.md: tabular navigation index following conventions/documentation.md format
- README.md: invisible knowledge capturing design rationale, tradeoffs vs full planner

**Acceptance Criteria**:

- SKILL.md contains activation table with plan and execute modes and invoke commands
- CLAUDE.md is tabular index only (no prose sections) with Files and Subdirectories tables
- README.md captures invisible knowledge with these required sections: (1) Overview stating subagent-compatibility purpose, (2) Architecture describing two-script + state-directory + XML-stdout protocol, (3) Design Decisions summarizing DL-001 through DL-007 rationale, (4) Invariants listing no-Task-tool / no-AskUserQuestion / WORKFLOW-export rules, (5) Tradeoffs covering quality-vs-compatibility and self-review-vs-independent-QR

**Tests**: skip:documentation-only milestone

**Code Intent**:

- CI-M-003-001: `skills/planner-lite/SKILL.md` -- Skill activation file. Name: planner-lite. Description: Lightweight planning and execution without subagent dispatch. Activation table with two modes: planning ('plan lite', 'design lite', 'lite plan') invoking `python3 -m skills.planner_lite.plan --step 1`, and execution ('execute lite', 'implement lite', 'run lite plan') invoking `python3 -m skills.planner_lite.execute --step 1 --state-dir <dir>`. Triggers intentionally avoid bare 'plan' and 'design' to prevent collision with existing planner skill.
- CI-M-003-002: `skills/planner-lite/CLAUDE.md` -- Navigation index with Files table (SKILL.md, README.md) and reference to Python code location (scripts/skills/planner_lite/). No prose sections.
- CI-M-003-003: `skills/planner-lite/README.md` -- Invisible knowledge document. Overview: what planner-lite solves. Architecture: two scripts, state directory, XML stdout protocol. Design Decisions: DL-001 through DL-007. Invariants: no Task tool, no AskUserQuestion, WORKFLOW export. Tradeoffs: quality vs compatibility.

**Code Changes**: Documentation milestone - no code changes.

**Source Material**: `## Invisible Knowledge` section of this plan

## Milestone Dependencies

```
M-001 ──┐
        ├──> M-003
M-002 ──┘
```

M-001 and M-002 are independent (Wave 1, parallel). M-003 depends on both (Wave 2).
