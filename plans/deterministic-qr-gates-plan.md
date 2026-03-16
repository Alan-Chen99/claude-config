# Plan: Deterministic QR Gates, Constraint Forwarding, Retrospective Honesty

**State dir**: `/tmp/planner-a7wcyl7y`
**Working copy**: `/tmp/claude-config-work` (all edits target this copy, NOT `/other/claude-config`)
**Status**: QR APPROVED — awaiting user review

---

## Decisions

### DL-001: Use has_qr_failures() for executor gate routing instead of --qr-status CLI arg
**Reasoning**: LLM chooses --qr-status at invocation -> can override QR failures -> has_qr_failures() reads qr-{phase}.json directly -> deterministic -> matches planner.py pattern

### DL-002: Add --state-dir as optional CLI arg to executor.py
**Reasoning**: executor.py lacks --state-dir -> required would break existing invocations -> optional with default None preserves backward compat -> gate steps: if state-dir provided, use has_qr_failures(); if absent but --qr-status provided, fall back to --qr-status (backward compat); if neither provided, exit with error explaining that gate steps require --state-dir or --qr-status

### DL-003: Keep --qr-status in verify step output as LLM dispatch guidance
**Reasoning**: Verify step emits --qr-status as guidance for orchestrator LLM -> removing confuses LLM branching -> gate steps ignore it when state-dir available

### DL-004: Forward constraints via STEP_1_ABSORB prompt text not dispatch_step infrastructure
**Reasoning**: dispatch_step already renders context.json -> data available -> missing is absorb instruction -> adding focus lines is minimal -> matches plan_design_qr_decompose.py pattern

### DL-005: Add state-file data sourcing to retrospective via prompt instructions
**Reasoning**: Step 9 is prompt template -> LLM fills content from memory -> unreliable for honest data -> adding explicit Read() instructions for plan.json and qr files grounds retrospective in file state -> programmatic extraction (Python parsing qr-*.json and injecting results) would require executor.py to import/process QR data at prompt-generation time, coupling retrospective to QR internals -> prompt instructions keep retrospective decoupled: LLM reads files itself, cross-references, reports honestly -> tradeoff: LLM may still hallucinate, but file-reading instructions make fabrication detectable (verifier can check whether files were actually read)

## Risks

- **R-001**: Backward incompatibility if --state-dir becomes required
  - Mitigation: Add as optional arg with default None; gate steps fall back to --qr-status when state-dir absent
- **R-002**: Disagreement between --qr-status (LLM says pass) and has_qr_failures() (file says fail)
  - Mitigation: has_qr_failures() takes precedence when state-dir is provided. --qr-status is only dispatch guidance; deterministic file check is authoritative. Log a warning if they disagree but route based on file state.
- **R-003**: Missing qr-{phase}.json at gate step time causes has_qr_failures() to return False, passing the gate when QR decompose never ran
  - Mitigation: Acceptable per INTENT.md QR file lifecycle: file absence means 'QR passed and cleaned up' or 'QR never ran'. In executor workflow, gate steps only execute after verify steps which require qr file existence. If file is missing at gate time, the preceding verify step either passed (file deleted by route) or was skipped (out-of-order invocation, which is a workflow invariant violation, not a gate bug).

## Rejected Alternatives

- **verification-status.md system**: Over-scoped (~100 line spec), LLM-compliance-only enforcement, deferred until deterministic gates prove out and residual failure modes are observed
- **Enforcement gate (Option B) that blocks on QR failures programmatically**: Premature: no data on residual failure modes after deterministic routing; deterministic gates are the prerequisite, enforcement is the follow-up if needed
- **Hardcode project-specific rules (blockquote preservation, script inventory) in general QR prompts**: Wrong abstraction level: context.json constraints mechanism already exists for project-specific rules; hardcoding couples QR prompts to specific projects
- **Remove --qr-status entirely from planner.py verify step guidance (lines 388-389)**: Those lines are dispatch guidance for verify agents telling LLM which branch was taken, not gate routing input; removing confuses LLM branching without improving determinism
- **Remove pre-existing --qr-fail and --qr-iteration argparse definitions (executor.py L890-891)**: Out of scope: these args are kept for backward compatibility in the fallback path (when --state-dir is not provided). CI-M-001-006 replaces their usage in the fail path when state_dir is available, but retains them for non-state-dir invocations. Full removal would require audit of all executor invocation sites to ensure none rely on these flags.

## Execution Waves

- **W-001** (sequential): M-001
- **W-002** (sequential): M-002, M-003

---

## M-001: Deterministic QR gates in executor

**Files**: skills/scripts/skills/planner/orchestrator/executor.py

**Acceptance Criteria**:
- Running executor --step 5 --state-dir DIR produces correct gate output without --qr-status
- Running executor --step 8 --state-dir DIR produces correct gate output without --qr-status
- Running executor --step 5 without --state-dir still works with --qr-status (backward compat)

**Code Intents**:
- **CI-M-001-001**: 
- **CI-M-001-002**: 
- **CI-M-001-003**: 
- **CI-M-001-004**: 
- **CI-M-001-005**: 
- **CI-M-001-006**: 

**Diffs**:

<details><summary>skills/scripts/skills/planner/orchestrator/executor.py — Add --state-dir optional CLI arg to main() argparse</summary>

```diff
--- a/skills/scripts/skills/planner/orchestrator/executor.py
+++ b/skills/scripts/skills/planner/orchestrator/executor.py
@@ -27,6 +27,7 @@
 from skills.planner.shared.qr.cli import add_qr_args
 from skills.planner.shared.qr.types import QRState, QRStatus, GateConfig, LoopState
 from skills.planner.shared.resources import get_mode_script_path
+from skills.planner.shared.qr.utils import has_qr_failures, get_qr_iteration
 
 
 # Module path for -m invocation
@@ -887,6 +888,7 @@ def main():
 
     parser.add_argument("--step", type=int, required=True)
     add_qr_args(parser)
+    parser.add_argument("--state-dir", type=str, default=None)
     parser.add_argument("--qr-iteration", type=int, default=0)
     parser.add_argument("--qr-fail", action="store_true")
     parser.add_argument("--reconciliation-check", action="store_true")
@@ -897,10 +899,6 @@ def main():
     if args.step < 1 or args.step > 9:
         sys.exit("Error: step must be 1-9")
 
-    if args.step == 5 and not args.qr_status:
-        sys.exit("Error: --qr-status required for step 5")
-
-    if args.step == 8 and not args.qr_status:
-        sys.exit("Error: --qr-status required for step 8")
 
     print(format_output(args.step,
                         args.qr_iteration, args.qr_fail, args.qr_status,
-                        args.reconciliation_check, args.milestone_count))
+                        args.reconciliation_check, args.milestone_count,
+                        args.state_dir))
 
 
 if __name__ == "__main__"
```
</details>

<details><summary>skills/scripts/skills/planner/orchestrator/executor.py — Thread state_dir through format_output to STEP_HANDLERS</summary>

```diff
--- a/skills/scripts/skills/planner/orchestrator/executor.py
+++ b/skills/scripts/skills/planner/orchestrator/executor.py
@@ -689,7 +689,7 @@ STEP_HANDLERS = {
 
 def format_output(step: int,
                   qr_iteration: int, qr_fail: bool, qr_status: str,
-                  reconciliation_check: bool, milestone_count: int) -> str:
+                  reconciliation_check: bool, milestone_count: int, state_dir: str = None) -> str:
     """Format output for display using XML format."""
     from skills.planner.shared.constants import EXECUTOR_TOTAL_STEPS
 
@@ -704,7 +704,8 @@ def format_output(step: int,
     handler = STEP_HANDLERS.get(step)
     if handler:
         return handler(qr=qr, total_steps=total_steps, qr_status=qr_status,
-                      milestone_count=milestone_count, reconciliation_check=reconciliation_check)
+                      milestone_count=milestone_count, reconciliation_check=reconciliation_check,
+                      state_dir=state_dir)
 
     # Generic step handling
     info = STEPS.get(step, STEPS[9])
```
</details>

<details><summary>skills/scripts/skills/planner/orchestrator/executor.py — Add --state-dir to format_step_4_code_qr if_pass/if_fail branches</summary>

```diff
--- a/skills/scripts/skills/planner/orchestrator/executor.py
+++ b/skills/scripts/skills/planner/orchestrator/executor.py
@@ -536,7 +536,7 @@ def format_step_1_planning(qr: QRState, total_steps: int, reconciliation_check:
     return "\n".join(parts)
 
 
-def format_step_4_code_qr(qr: QRState, total_steps: int, **kw) -> str:
+def format_step_4_code_qr(qr: QRState, total_steps: int, state_dir: str = None, **kw) -> str:
     """Format step 4 code QR output with branching."""
     info = STEPS[4]
     parts = []
@@ -582,8 +582,14 @@ def format_step_4_code_qr(qr: QRState, total_steps: int, **kw) -> str:
     parts.append(render_current_action(CurrentActionNode(actions)))
     parts.append("")
 
-    if_pass = f"python3 -m {MODULE_PATH} --step 5 --qr-status pass"
-    if_fail = f"python3 -m {MODULE_PATH} --step 5 --qr-status fail"
+    if state_dir:
+        if_pass = f"python3 -m {MODULE_PATH} --step 5 --state-dir {state_dir} --qr-status pass"
+        if_fail = f"python3 -m {MODULE_PATH} --step 5 --state-dir {state_dir} --qr-status fail"
+    else:
+        if_pass = f"python3 -m {MODULE_PATH} --step 5 --qr-status pass"
+        if_fail = f"python3 -m {MODULE_PATH} --step 5 --qr-status fail"
 
     from skills.lib.workflow.ast.nodes import ElementNode
     if_pass_node = ElementNode("if_pass", {}, [TextNode(if_pass)])
```
</details>

<details><summary>skills/scripts/skills/planner/orchestrator/executor.py — Add --state-dir to format_step_7_doc_qr if_pass/if_fail branches</summary>

```diff
--- a/skills/scripts/skills/planner/orchestrator/executor.py
+++ b/skills/scripts/skills/planner/orchestrator/executor.py
@@ -606,7 +606,7 @@ def format_step_4_code_qr(qr: QRState, total_steps: int, state_dir: str = None,
     return "\n".join(parts)
 
 
-def format_step_7_doc_qr(qr: QRState, total_steps: int, **kw) -> str:
+def format_step_7_doc_qr(qr: QRState, total_steps: int, state_dir: str = None, **kw) -> str:
     """Format step 7 doc QR output with branching."""
     info = STEPS[7]
     parts = []
@@ -654,8 +654,14 @@ def format_step_7_doc_qr(qr: QRState, total_steps: int, **kw) -> str:
     parts.append(render_current_action(CurrentActionNode(actions)))
     parts.append("")
 
-    if_pass = f"python3 -m {MODULE_PATH} --step 8 --qr-status pass"
-    if_fail = f"python3 -m {MODULE_PATH} --step 8 --qr-status fail"
+    if state_dir:
+        if_pass = f"python3 -m {MODULE_PATH} --step 8 --state-dir {state_dir} --qr-status pass"
+        if_fail = f"python3 -m {MODULE_PATH} --step 8 --state-dir {state_dir} --qr-status fail"
+    else:
+        if_pass = f"python3 -m {MODULE_PATH} --step 8 --qr-status pass"
+        if_fail = f"python3 -m {MODULE_PATH} --step 8 --qr-status fail"
 
     from skills.lib.workflow.ast.nodes import ElementNode
     if_pass_node = ElementNode("if_pass", {}, [TextNode(if_pass)])
```
</details>

<details><summary>skills/scripts/skills/planner/orchestrator/executor.py — Update format_gate and STEP_HANDLERS to compute QRState from has_qr_failures whe</summary>

```diff
--- a/skills/scripts/skills/planner/orchestrator/executor.py
+++ b/skills/scripts/skills/planner/orchestrator/executor.py
@@ -210,7 +210,7 @@ DOC_QR_GATE = GateConfig(
 
 
-def format_gate(step: int, gate: GateConfig, qr: QRState, total_steps: int) -> str:
+def format_gate(step: int, gate: GateConfig, qr: QRState, total_steps: int, state_dir: str = None) -> str:
     """Format gate step output using W.* API."""
     parts = []
 
@@ -268,7 +268,10 @@ def format_gate(step: int, gate: GateConfig, qr: QRState, total_steps: int) ->
         next_cmd = f"python3 -m {MODULE_PATH} --step {gate.pass_step}"
     else:
         next_iteration = qr.iteration + 1
-        next_cmd = f"python3 -m {MODULE_PATH} --step {gate.work_step} --qr-fail --qr-iteration {next_iteration}"
+        if state_dir:
+            next_cmd = f"python3 -m {MODULE_PATH} --step {gate.work_step} --state-dir {state_dir}"
+        else:
+            next_cmd = f"python3 -m {MODULE_PATH} --step {gate.work_step} --qr-fail --qr-iteration {next_iteration}"
 
     parts.append(render_invoke_after(InvokeAfterNode(cmd=next_cmd)))
     parts.append("")
@@ -680,8 +683,27 @@ def format_step_7_doc_qr(qr: QRState, total_steps: int, state_dir: str = None,
 
 STEP_HANDLERS = {
     1: format_step_1_planning,
     3: lambda qr, total_steps, milestone_count, **kw: format_step_3_implementation(qr, total_steps, milestone_count),
     4: format_step_4_code_qr,
-    5: lambda qr, total_steps, qr_status, **kw: format_gate(5, CODE_QR_GATE, qr, total_steps) if qr_status else "Error: --qr-status required for step 5",
+    5: lambda qr, total_steps, qr_status, state_dir, **kw: (
+        format_gate(
+            5, CODE_QR_GATE,
+            QRState(
+                iteration=get_qr_iteration(state_dir, "impl-code") if state_dir else qr.iteration,
+                state=qr.state,
+                status=QRStatus.PASS if state_dir and not has_qr_failures(state_dir, "impl-code") else (
+                    QRStatus.FAIL if state_dir else (QRStatus(qr_status) if qr_status else None)
+                )
+            ) if state_dir or qr_status else None,
+            total_steps, state_dir
+        ) if state_dir or qr_status else "Error: --state-dir or --qr-status required for step 5"
+    ),
     6: lambda qr, total_steps, **kw: format_step_6_documentation(qr, total_steps),
     7: format_step_7_doc_qr,
-    8: lambda qr, total_steps, qr_status, **kw: format_gate(8, DOC_QR_GATE, qr, total_steps) if qr_status else "Error: --qr-status required for step 8",
+    8: lambda qr, total_steps, qr_status, state_dir, **kw: (
+        format_gate(
+            8, DOC_QR_GATE,
+            QRState(
+                iteration=get_qr_iteration(state_dir, "impl-docs") if state_dir else qr.iteration,
+                state=qr.state,
+                status=QRStatus.PASS if state_dir and not has_qr_failures(state_dir, "impl-docs") else (
+                    QRStatus.FAIL if state_dir else (QRStatus(qr_status) if qr_status else None)
+                )
+            ) if state_dir or qr_status else None,
+            total_steps, state_dir
+        ) if state_dir or qr_status else "Error: --state-dir or --qr-status required for step 8"
+    ),
 }
```
</details>

**Tests**:
- scenario:EDGE run step 5 with state-dir containing qr-impl-code.json with FAIL items -> gate outputs FAIL
- scenario:EDGE run step 5 with state-dir containing qr-impl-code.json all PASS -> gate outputs PASS
- scenario:EDGE run step 5 without state-dir with --qr-status pass -> backward compat pass
- scenario:EDGE run step 5 with state-dir but qr-impl-code.json absent -> gate passes (acceptable: file absence means QR passed and was cleaned up per INTENT.md lifecycle, or verify step was never reached which is a workflow invariant violation not a gate bug)

## M-002: Forward project constraints to impl QR decompose

**Files**: skills/scripts/skills/planner/quality_reviewer/impl_code_qr_decompose.py, skills/scripts/skills/planner/quality_reviewer/impl_docs_qr_decompose.py

**Acceptance Criteria**:
- impl_code_qr_decompose.py STEP_1_ABSORB Focus section contains line referencing 'planning_context.constraints' (mirroring plan_design_qr_decompose.py L33 pattern: 'planning_context.constraints (all documented?)')
- impl_docs_qr_decompose.py STEP_1_ABSORB Focus section contains line referencing 'planning_context.constraints' (mirroring plan_design_qr_decompose.py L33 pattern)
- impl_code_qr_decompose.py STEP_3_ENUMERATION contains line referencing constraints (mirroring plan_design_qr_decompose.py L63 pattern: 'Each constraint in planning_context.constraints (ID, type)')
- impl_docs_qr_decompose.py STEP_3_ENUMERATION contains line referencing constraints (mirroring plan_design_qr_decompose.py L63 pattern)

**Code Intents**:
- **CI-M-002-001**: 
- **CI-M-002-002**: 

**Diffs**:

<details><summary>skills/scripts/skills/planner/quality_reviewer/impl_code_qr_decompose.py — Add constraint references to STEP_1_ABSORB and STEP_3_ENUMERATION</summary>

```diff
--- a/skills/scripts/skills/planner/quality_reviewer/impl_code_qr_decompose.py
+++ b/skills/scripts/skills/planner/quality_reviewer/impl_code_qr_decompose.py
@@ -26,8 +26,9 @@ Also read MODIFIED_FILES from codebase (paths from milestones).
 
 SCOPE: Implemented code quality.
 
 Focus on:
+  - planning_context.constraints (project-specific rules)
   - milestones[].acceptance_criteria (expectations)
   - Actual implemented code in modified files (observations)
   - Code quality (structure, patterns, documentation)
   - Intent markers in implemented code
@@ -58,8 +59,11 @@ FILES:
   - Files modified per milestone (path list)
   - Actual file content (read from codebase)
 
 CROSS-CUTTING:
+  - Each constraint in planning_context.constraints (ID, type)
+
+CODE PATTERNS:
   - Error handling patterns used
   - Logging patterns used
   - Shared state access patterns
```
</details>

<details><summary>skills/scripts/skills/planner/quality_reviewer/impl_docs_qr_decompose.py — Add constraint references to STEP_1_ABSORB and STEP_3_ENUMERATION</summary>

```diff
--- a/skills/scripts/skills/planner/quality_reviewer/impl_docs_qr_decompose.py
+++ b/skills/scripts/skills/planner/quality_reviewer/impl_docs_qr_decompose.py
@@ -29,8 +29,9 @@ Also read documentation files in modified directories:
 
 SCOPE: Post-implementation documentation quality.
 
 Focus on:
+  - planning_context.constraints (project-specific documentation rules)
   - invisible_knowledge section (was it transferred?)
   - Modified directory list (need docs?)
   - CLAUDE.md format compliance
   - README.md presence where required
@@ -58,8 +59,11 @@ DIRECTORIES:
   - CLAUDE.md exists? Format correct?
   - README.md exists where required?
 
 INVISIBLE KNOWLEDGE:
+  - Each constraint in planning_context.constraints (ID, type)
+
+KNOWLEDGE ARTIFACTS:
   - Each invisible_knowledge item (count, topics)
   - Current location vs best location
```
</details>

## M-003: Retrospective data sourcing

**Files**: skills/scripts/skills/planner/orchestrator/executor.py

**Acceptance Criteria**:
- Running executor --step 9 output contains explicit Read() tool call instructions for $STATE_DIR/plan.json before the PRESENT block (e.g., 'Read plan.json: cat $STATE_DIR/plan.json')
- Output contains existence check instructions for qr files: 'If $STATE_DIR/qr-impl-code.json exists, read it; if absent, report QR passed (file deleted on pass)' and same for qr-impl-docs.json
- Output contains cross-reference instruction: 'For each milestone acceptance_criteria in plan.json, verify against actual implementation and report pass/fail per criterion'

**Code Intents**:
- **CI-M-003-001**: 

**Diffs**:

<details><summary>skills/scripts/skills/planner/orchestrator/executor.py — Add data sourcing instructions to STEPS[9] retrospective</summary>

```diff
--- a/skills/scripts/skills/planner/orchestrator/executor.py
+++ b/skills/scripts/skills/planner/orchestrator/executor.py
@@ -171,6 +171,18 @@ STEPS = {
     9: {
         "title": "Retrospective",
         "actions": [
+            "DATA SOURCING (read files before analysis):",
+            "",
+            "Read $STATE_DIR/plan.json for:",
+            "  - Milestone structure and acceptance criteria",
+            "  - Planning decisions and constraints",
+            "",
+            "Check QR file presence:",
+            "  - If $STATE_DIR/qr-impl-code.json exists: read it, report findings",
+            "  - If absent: report QR passed (file deleted on pass per QR lifecycle)",
+            "  - If $STATE_DIR/qr-impl-docs.json exists: read it, report findings",
+            "  - If absent: report QR passed",
+            "",
             "PRESENT retrospective to user (do not write to file):",
             "",
             "EXECUTION RETROSPECTIVE",
@@ -179,6 +191,8 @@ STEPS = {
             "Status: COMPLETED | BLOCKED | ABORTED",
             "",
             "Milestone Outcomes: | Milestone | Status | Notes |",
+            "  For each milestone acceptance_criteria in plan.json:",
+            "    Cross-reference against actual implementation, report pass/fail",
             "Reconciliation Summary: [if run]",
             "Plan Accuracy Issues: [if any]",
             "Deviations from Plan: [if any]",
```
</details>
