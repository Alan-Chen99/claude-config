# Plan

## Overview

alan-coding-style workflow has 6 gaps identified in gap analysis vs leon_writing_style: advisory-only quality gate, cargo-culted step-back principles, advisory thresholds, no style-context alignment, no consumer/purpose analysis, no verification exemptions by code type.

**Approach**: Text-level changes to STEPS dict entries for gaps 2-6, plus new STEPS[9] quality gate for gap 1. TOTAL_STEPS updated from 8 to 9. Tests updated to cover all new behavior and maintain existing parametrized coverage.

## Planning Context

### Decision Log

| ID | Decision | Reasoning Chain |
|---|---|---|
| DL-001 | Add Step 9 quality gate modeled on leon_writing_style Step 9 | Gap analysis shows Step 8 final checklist is advisory (says note remaining issues) -> without enforcement the verification pipeline becomes decorative -> Step 9 with stopping/continue criteria creates a hard gate that loops back when violations remain |
| DL-002 | Replace cargo-culted step_back_principles with genuine meta-cognitive priming | Leon Step 3 uses real meta-cognitive questions (What makes voice distinctive? What would make this AI-generated?) -> Alan Step 2 has the XML tag but content is purely procedural -> replacing with coding-domain equivalents restores the Step-Back Prompting technique the docstring claims |
| DL-003 | Change advisory threshold language to binding gates | Leon uses binding language (at least N markers, PASS/FAIL verdict) -> Alan Step 6 uses advisory not hard gates with ~ prefixes -> combined with advisory Step 8 checklist this means WEAK assessment has zero consequences -> removing advisory language and using >= creates enforceable gates |
| DL-004 | Add consumer/purpose fields to Step 1 classification table | Leon Step 2 asks WHO reads this and WHY it exists -> code equivalent is who calls this code and what purpose it serves -> these fields inform context-appropriate style checking in later steps |
| DL-005 | Add code-context field and verification exemptions to Steps 1 and 6 | Different code contexts (production/test/config/CLI) warrant different style rigor -> test files dont need positive pattern checks for Architecture and Organization -> adding context field to classification and exemptions to Step 6 prevents false violations on non-production code |
| DL-006 | Keep existing STEPS dict pattern instead of refactoring to handler functions | alan_coding_style uses a simpler pattern than leon_writing_style (STEPS dict directly, no per-step handler functions) -> all 6 gaps map to text-level changes in the STEPS dict plus one new entry -> refactoring to handlers would be a large unnecessary diff with regression risk |
| DL-007 | Step 8 final_checklist changes from advisory to loop-back trigger | Step 8 currently says If any checkbox would be [ ] note remaining issues in your delivery -> this must change to increase total_steps to trigger Step 9 quality gate -> Step 9 then has the actual stop/continue decision |
| DL-008 | Step 9 uses increase total_steps prompt-level pattern from leon for continuation; format_output needs no changes | Leon Step 9 says CONTINUE increase total_steps if ANY are true -> this is a prompt-level instruction to the LLM agent, not a code-level change -> format_output is_complete = step >= WORKFLOW.total_steps means step 9 always outputs WORKFLOW COMPLETE, which is correct because the agent re-runs step 9 on continuation -> same pattern as leon_writing_style -> no format_output changes needed |
| DL-009 | HISTORY_TEMPLATE coverage in tests must list explicit step numbers, not a contiguous range | Steps 2-7 and 9 use HISTORY_TEMPLATE but Step 8 does not -> a range like 2-9 would falsely require Step 8 to have it -> test must enumerate [2, 3, 4, 5, 6, 7, 9] explicitly to match actual usage |

### Rejected Alternatives

| Alternative | Why Rejected |
|---|---|
| Refactor STEPS dict to per-step handler functions like leon_writing_style | All 6 gaps map to text-level changes in the STEPS dict plus one new entry -> refactoring to handlers would create a large unnecessary diff with regression risk for no functional benefit (ref: DL-006) |

### Constraints

- MUST: All 6 problems from gap analysis are fixed
- MUST: No regression in script behavior (existing tests must pass)
- MUST: No regression in implementation maintainability or code quality
- SHOULD: Follow existing DL-xxx design decision patterns
- MUST-NOT: Change externally observable behavior of other skills

### Known Risks

- **Consumer/purpose table fit assumption is M-confidence: if fields dont map cleanly to coding contexts, classification output may need restructuring**: Fields are additive rows (not columns) in a markdown table -> low structural risk. Review during implementation.
- **Exemption text scope assumption is M-confidence: edge cases like test utilities that should follow production patterns may exist**: Exemptions are phrased as defaults (skip category) not absolutes -> LLM agent can override when context warrants.

## Invisible Knowledge

### System

Design decisions DL-001 through DL-005 are documented as inline code comments with (ref: DL-NNN) notation. New decisions DL-006 through DL-008 follow the same convention where they touch code.

### Invariants

- WORKFLOW is constructed from STEPS dict with validate=False; total_steps derives from len(STEPS). Adding STEPS[9] automatically updates WORKFLOW.total_steps to 9.
- HISTORY_TEMPLATE is shared across Steps 2-7 (and will be shared across Steps 2-7 plus new Step 9) for context accumulation. Step 4 also uses it. Step 8 does not.
- StepDef has no phase attribute. A regression test exists for this (test_stepdef_has_no_phase_attribute). Code must not add phase to StepDef.
- XML_FORMAT_MANDATE is injected only at Step 1 via get_step_guidance. Other steps must not duplicate it.

### Tradeoffs

- Step 9 format_output always shows WORKFLOW COMPLETE because is_complete = step >= WORKFLOW.total_steps evaluates True for the final step. The CONTINUE (increase total_steps) instruction is prompt-level: the LLM agent re-invokes step 9, which re-evaluates stopping criteria. This matches leon_writing_style exactly.

## Milestones

### Milestone 1: Fix 6 gaps in alan-coding-style workflow

**Files**: skills/scripts/skills/alan_coding_style/coding_style.py, skills/scripts/tests/test_alan_coding_style.py

**Requirements**:

- Gap #1 (CRITICAL): Add Step 9 quality gate with stopping/continue criteria and update Step 8 to trigger loop-back
- Gap #2 (HIGH): Replace cargo-culted step_back_principles in Step 2 with genuine meta-cognitive priming questions
- Gap #3 (HIGH): Replace advisory threshold language in Step 6 with binding PASS/FAIL gates
- Gap #4 (MEDIUM): Add style-context alignment via Code Context field in Step 1 classification
- Gap #5 (MEDIUM): Add consumer/purpose analysis fields to Step 1 classification table
- Gap #6 (LOW-MEDIUM): Add content-type-driven verification exemptions to Step 6

**Acceptance Criteria**:

- STEPS dict has 9 entries (keys 1-9) and TOTAL_STEPS equals 9
- STEPS[9] contains stopping_criteria tag with STOP and CONTINUE conditions
- STEPS[8] final_checklist says increase total_steps instead of Note remaining issues
- STEPS[2] step_back_principles contains meta-cognitive priming questions, not procedural content
- STEPS[6] sufficiency_check has no advisory language, uses >= thresholds, and has PASS/FAIL verdict
- STEPS[1] classification_output contains Consumers, Purpose, and Code Context rows
- STEPS[6] sufficiency_check contains verification exemptions by code context
- All existing tests pass without modification (no regressions)
- New tests cover all 6 gap fixes

#### Code Intent

- **CI-M-001-001** `skills/scripts/skills/alan_coding_style/coding_style.py::TOTAL_STEPS`: Update TOTAL_STEPS from 8 to 9 (refs: DL-001)
- **CI-M-001-002** `skills/scripts/skills/alan_coding_style/coding_style.py::STEPS`: Add STEPS[9] quality gate step with stopping_criteria (STOP when ALL true: zero HIGH-confidence violations, positive markers >= threshold, no cargo-culted step-back in output) and continue criteria (CONTINUE increase total_steps if ANY true: HIGH-confidence violation remains, positive markers WEAK/MINIMAL, style-context mismatch). Phase is REFINEMENT, step_title is Quality Gate, id is quality_gate. Actions list includes HISTORY_TEMPLATE. next_desc is WORKFLOW COMPLETE - deliver final code. (refs: DL-001, DL-008)
- **CI-M-001-003** `skills/scripts/skills/alan_coding_style/coding_style.py::STEPS`: In STEPS[8] final_checklist, replace the advisory If any checkbox would be [ ] instead of [x]: Note remaining issues in your delivery. Otherwise: code complete. Deliver final output. with If any checkbox would be [ ] instead of [x]: increase total_steps. Otherwise: code complete. Deliver final output. (refs: DL-007)
- **CI-M-001-004** `skills/scripts/skills/alan_coding_style/coding_style.py::STEPS`: In STEPS[2] step_back_principles tag, replace purely procedural content with genuine meta-cognitive priming questions: 1. What makes Alans coding style distinctive from generic clean code? (Concrete decision thresholds, contrastive WRONG/RIGHT pairs, minimal abstraction) 2. What would make this code obviously LLM-generated? (Over-engineering, verbose names, excessive comments, defensive validation of internal state). Keep these answers in mind as you apply rules. (refs: DL-002)
- **CI-M-001-005** `skills/scripts/skills/alan_coding_style/coding_style.py::STEPS`: In STEPS[6] sufficiency_check, remove advisory, not hard gates text from REFERENCE THRESHOLDS line. Replace ~ prefix with >= on the threshold numbers. Add binding verdict after assessment: VERDICT: STRONG/MODERATE -> PASS. WEAK/MINIMAL -> FAIL (record as HIGH priority violation for Step 7). (refs: DL-003)
- **CI-M-001-006** `skills/scripts/skills/alan_coding_style/coding_style.py::STEPS`: In STEPS[1] classification_output, add two new rows to the classification table: | Consumers | internal / public-API / CLI / test | and | Purpose | one-sentence what this code does |. Update the This table guides text to mention these inform context-appropriate style checking. (refs: DL-004)
- **CI-M-001-007** `skills/scripts/skills/alan_coding_style/coding_style.py::STEPS`: In STEPS[1] classification_output, add a Code Context row: | Code Context | production / test / config / CLI / glue |. In STEPS[6] sufficiency_check, add verification exemptions after the thresholds: EXEMPTIONS by code context (from Step 1): test code: skip Architecture and Organization categories. config/glue code: skip Language Idioms category. CLI scripts: skip Architecture category. (refs: DL-005)
- **CI-M-001-008** `skills/scripts/tests/test_alan_coding_style.py::test_history_template_referenced_by_steps`: Update test_history_template_referenced_by_steps to check steps 2, 3, 4, 5, 6, 7, and 9 (was 2-7). Step 8 does not use HISTORY_TEMPLATE. New Step 9 uses HISTORY_TEMPLATE per CI-M-001-002. (refs: DL-001)
- **CI-M-001-009** `skills/scripts/tests/test_alan_coding_style.py::test_format_output_step9_shows_complete`: Add test_format_output_step9_shows_complete to verify TOTAL_STEPS=9 step shows WORKFLOW COMPLETE text. This replaces the coverage of the old step 8 terminal test since step 8 is no longer the last step. (refs: DL-001)
- **CI-M-001-010** `skills/scripts/tests/test_alan_coding_style.py::test_step8_triggers_loopback`: Add test_step8_triggers_loopback to verify Step 8 final_checklist contains increase total_steps instead of Note remaining issues. (refs: DL-007)
- **CI-M-001-011** `skills/scripts/tests/test_alan_coding_style.py::test_step9_has_stopping_criteria`: Add test_step9_has_stopping_criteria to verify Step 9 actions contain stopping_criteria tag with STOP and CONTINUE conditions. (refs: DL-001)
- **CI-M-001-012** `skills/scripts/tests/test_alan_coding_style.py::test_step2_step_back_has_meta_cognitive_questions`: Add test_step2_step_back_has_meta_cognitive_questions to verify Step 2 step_back_principles contains the two priming questions (What makes Alans coding style distinctive and What would make this obviously LLM-generated) rather than procedural text. (refs: DL-002)
- **CI-M-001-013** `skills/scripts/tests/test_alan_coding_style.py::test_step6_thresholds_are_binding`: Add test_step6_thresholds_are_binding to verify Step 6 sufficiency_check does not contain advisory and uses PASS/FAIL verdict language. (refs: DL-003)
- **CI-M-001-014** `skills/scripts/tests/test_alan_coding_style.py::test_step1_has_consumer_purpose_context_fields`: Add test_step1_has_consumer_purpose_context_fields to verify Step 1 classification_output actions contain Consumers, Purpose, and Code Context rows. (refs: DL-004, DL-005)

#### Code Changes

**CC-M-001-001** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-001

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -32,7 +32,7 @@ from skills.lib.workflow.ast.renderer import (
 
 
-TOTAL_STEPS = 8
+TOTAL_STEPS = 9
 
 # Injected at step 1 only; instructs executing agents to follow XML protocol.
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -32,7 +32,7 @@ from skills.lib.workflow.ast.renderer import (
 
 
-TOTAL_STEPS = 9
+TOTAL_STEPS = 9  # 9 steps: 8 workflow steps + quality gate (ref: DL-001)

```


**CC-M-001-002** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-003

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -633,8 +633,7 @@ STEPS = {
             "[x] Code organization matches conventions",
             "",
             "If any checkbox would be [ ] instead of [x]:",
-            "  Note remaining issues in your delivery.",
-            "  Explain what was not addressed and why.",
+            "  increase total_steps.",
             "",
             "Otherwise: code complete. Deliver final output.",
             "</final_checklist>",

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -544,6 +544,7 @@ STEPS = {
         "next_desc": "Apply refinements and deliver.",
     },
+    # Step 8: final_checklist triggers Step 9 quality gate instead of silently noting issues; loop prevents silent delivery of violations. (ref: DL-007)
     8: {
         "id": "refine_deliver",

```


**CC-M-001-003** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-004

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -194,12 +194,14 @@ STEPS = {
         "actions": [
             "<step_back_principles>",
-            "The applicable style guide sections are embedded below.",
-            "These were selected based on your Step 1 classification.",
-            "",
-            "Based on the embedded sections, identify which rules apply.",
-            "Not all rules within a section are relevant to every task.",
+            "1. What makes Alan's coding style distinctive from generic clean code?",
+            "   (Concrete decision thresholds, contrastive WRONG/RIGHT pairs, minimal abstraction)",
+            "2. What would make this code obviously LLM-generated?",
+            "   (Over-engineering, verbose names, excessive comments, defensive validation of internal state)",
+            "Keep these answers in mind as you apply rules.",
             "</step_back_principles>",
             "",
             "<rule_selection>",

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -189,6 +189,7 @@ STEPS = {
         "next_desc": "Load applicable style rules.",
     },
+    # Step 2: step_back_principles primes meta-cognitive framing; procedural rule lists defeat the technique by answering the question before it is asked. (ref: DL-002)
     2: {
         "id": "style_rule_retrieval",

```


**CC-M-001-004** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-005

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -459,9 +459,13 @@ STEPS = {
             "",
             "<sufficiency_check>",
-            "REFERENCE THRESHOLDS (advisory, not hard gates):",
-            "  - Code <50 lines: ~2 markers from any category",
-            "  - Code 50-200 lines: ~4 markers across 2+ categories",
-            "  - Code >200 lines: ~6 markers across 3+ categories",
+            "REFERENCE THRESHOLDS:",
+            "  - Code <50 lines: >= 2 markers from any category",
+            "  - Code 50-200 lines: >= 4 markers across 2+ categories",
+            "  - Code >200 lines: >= 6 markers across 3+ categories",
             "",
             "TALLY:",
             "  | Category | Count | Examples |",
@@ -480,7 +480,12 @@ STEPS = {
             "  WEAK:     2-3 markers",
             "  MINIMAL:  0-1 markers",
             "",
-            "Record your assessment level and carry it to Step 7.",
+            "VERDICT: STRONG/MODERATE -> PASS.",
+            "WEAK/MINIMAL -> FAIL (record as HIGH priority violation for Step 7).",
+            "",
+            "Carry your assessment and verdict to Step 7.",
             "</sufficiency_check>",

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -422,6 +422,7 @@ STEPS = {
         "next_desc": "Check for positive coding patterns.",
     },
+    # Step 6: thresholds are binding gates (>= not ~); WEAK/MINIMAL verdict is a FAIL. (ref: DL-003)
     6: {
         "id": "positive_pattern_check",

```


**CC-M-001-005** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-006

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -156,8 +156,12 @@ STEPS = {
             "  | Aspect | Value |",
             "  |--------|-------|",
             "  | Task Type | generate / review / refactor / fix |",
             "  | Language(s) | e.g. Python, C#, TypeScript |",
             "  | Scope | file / function / module / project |",
+            "  | Consumers | internal / public-API / CLI / test |",
+            "  | Purpose | one-sentence what this code does |",
             "",
-            "This table guides section selection below.",
+            "This table guides section selection below and informs context-appropriate style checking.",
             "</classification_output>",

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -128,6 +128,8 @@ HISTORY_TEMPLATE = """

+# All gaps addressed as text-level changes to this dict; no handler function refactor to avoid unnecessary diff. (ref: DL-006)
 STEPS = {
+    # Step 1: classification includes Consumers, Purpose fields for context-appropriate style checking. (ref: DL-004)
     1: {
         "id": "context_analysis",

```


**CC-M-001-006** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-007

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -156,6 +156,7 @@ STEPS = {
             "  | Task Type | generate / review / refactor / fix |",
             "  | Language(s) | e.g. Python, C#, TypeScript |",
             "  | Scope | file / function / module / project |",
             "  | Consumers | internal / public-API / CLI / test |",
             "  | Purpose | one-sentence what this code does |",
+            "  | Code Context | production / test / config / CLI / glue |",
             "",
             "This table guides section selection below and informs context-appropriate style checking.",
@@ -480,6 +480,12 @@ STEPS = {
             "VERDICT: STRONG/MODERATE -> PASS.",
             "WEAK/MINIMAL -> FAIL (record as HIGH priority violation for Step 7).",
             "",
+            "EXEMPTIONS by code context (from Step 1):",
+            "  test code: skip Architecture and Organization categories.",
+            "  config/glue code: skip Language Idioms category.",
+            "  CLI scripts: skip Architecture category.",
+            "",
             "Carry your assessment and verdict to Step 7.",
             "</sufficiency_check>",

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -128,7 +128,7 @@ HISTORY_TEMPLATE = """
 
 STEPS = {
-    # Step 1: classification includes Consumers, Purpose fields for context-appropriate style checking. (ref: DL-004)
+    # Step 1: classification includes Consumers, Purpose, Code Context fields; Step 6 exempts test/config/CLI from some categories. (ref: DL-004, DL-005)
     1: {
         "id": "context_analysis",

```


**CC-M-001-007** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-002

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -639,7 +639,36 @@ STEPS = {
             "</final_checklist>",
         ],
-        "next_desc": "WORKFLOW COMPLETE - deliver final code.",
+        "next_desc": "Run quality gate.",
     },
+    9: {
+        "id": "quality_gate",
+        "phase": "REFINEMENT",
+        "step_title": "Quality Gate",
+        "actions": [
+            HISTORY_TEMPLATE,
+            "",
+            "<stopping_criteria>",
+            "STOP when ALL of the following are true:",
+            "  - Zero HIGH-confidence violations remain",
+            "  - Positive markers >= threshold (STRONG or MODERATE verdict from Step 6)",
+            "  - No cargo-culted step-back principles appear in output",
+            "",
+            "CONTINUE (increase total_steps) when ANY of the following are true:",
+            "  - A HIGH-confidence violation remains unresolved",
+            "  - Positive markers assessment is WEAK or MINIMAL",
+            "  - Style-context mismatch detected (wrong rules applied for code context)",
+            "</stopping_criteria>",
+            "",
+            "Evaluate each condition above against your accumulated context.",
+            "If STOP conditions are all met: proceed to deliver final code below.",
+            "If any CONTINUE condition is true: increase total_steps and loop back to Step 8.",
+        ],
+        "next_desc": "WORKFLOW COMPLETE - deliver final code.",
+    },
 }

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -94,7 +94,7 @@ XML_FORMAT_MANDATE = """<xml_format_mandate>

-# Context accumulation template shared by all steps.
-# Single template prevents duplicate Classification tables across steps.
+# Context accumulation template shared by Steps 2-7 and 9.
+# Single template prevents duplicate Classification tables across steps; Step 9 excluded from contiguous range because Step 8 does not use it. (ref: DL-009)
 HISTORY_TEMPLATE = """

```


**CC-M-001-008** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-008

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -174,7 +174,7 @@ def test_format_output_with_file_nodes():
 
 def test_history_template_referenced_by_steps():
-    for step_num in [2, 3, 4, 5, 6, 7]:
+    for step_num in [2, 3, 4, 5, 6, 7, 9]:
         actions = STEPS[step_num]["actions"]
         assert HISTORY_TEMPLATE in actions, f"Step {step_num} missing HISTORY_TEMPLATE"

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -173,6 +173,7 @@ def test_format_output_with_file_nodes():
 
 def test_history_template_referenced_by_steps():
+    # Step 8 excluded: final_checklist step does not accumulate history. (ref: DL-009)
     for step_num in [2, 3, 4, 5, 6, 7, 9]:
         actions = STEPS[step_num]["actions"]
         assert HISTORY_TEMPLATE in actions, f"Step {step_num} missing HISTORY_TEMPLATE"

```


**CC-M-001-009** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-009

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -111,6 +111,13 @@ def test_format_output_last_step_shows_complete():
     output = format_output(TOTAL_STEPS, guidance, "final")
     assert "WORKFLOW COMPLETE" in output
 
+
+def test_format_output_step9_shows_complete():
+    assert TOTAL_STEPS == 9
+    guidance = get_step_guidance(9)
+    output = format_output(9, guidance, "final")
+    assert "WORKFLOW COMPLETE" in output
+
 
 def test_format_output_middle_step_includes_invoke_after():

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -111,6 +111,7 @@ def test_format_output_last_step_shows_complete():
     assert "WORKFLOW COMPLETE" in output
 
 
+# Asserts TOTAL_STEPS == 9 explicitly; last_step test uses TOTAL_STEPS dynamically. (ref: DL-001)
 def test_format_output_step9_shows_complete():
     assert TOTAL_STEPS == 9
     guidance = get_step_guidance(9)

```


**CC-M-001-010** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-010

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -177,6 +177,13 @@ def test_history_template_referenced_by_steps():
         assert HISTORY_TEMPLATE in actions, f"Step {step_num} missing HISTORY_TEMPLATE"
 
 
+def test_step8_triggers_loopback():
+    actions = STEPS[8]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "increase total_steps" in actions_text
+    assert "Note remaining issues" not in actions_text
+
+
 # ---------------------------------------------------------------------------
 # CLI invocation (subprocess, matches test_workflow_steps pattern)
 # ---------------------------------------------------------------------------

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -177,6 +177,8 @@ def test_history_template_referenced_by_steps():
         assert HISTORY_TEMPLATE in actions, f"Step {step_num} missing HISTORY_TEMPLATE"


+# ---------------------------------------------------------------------------
+# Behavioral contracts for quality gate, loop-back, and binding thresholds
+# ---------------------------------------------------------------------------
 def test_step8_triggers_loopback():
     actions = STEPS[8]["actions"]
     actions_text = "\n".join(str(a) for a in actions)

```


**CC-M-001-011** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-011

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -184,6 +184,13 @@ def test_step8_triggers_loopback():
     assert "Note remaining issues" not in actions_text
 
 
+def test_step9_has_stopping_criteria():
+    actions = STEPS[9]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "<stopping_criteria>" in actions_text
+    assert "STOP" in actions_text
+    assert "CONTINUE" in actions_text
+
+
 # ---------------------------------------------------------------------------
 # CLI invocation (subprocess, matches test_workflow_steps pattern)
 # ---------------------------------------------------------------------------

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -184,6 +184,7 @@ def test_step8_triggers_loopback():
     assert "Note remaining issues" not in actions_text


+# Step 9 must contain both conditions so the gate enforces a real decision, not a checklist acknowledgment. (ref: DL-001, DL-008)
 def test_step9_has_stopping_criteria():
     actions = STEPS[9]["actions"]
     actions_text = "\n".join(str(a) for a in actions)

```


**CC-M-001-012** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-012

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -191,6 +191,14 @@ def test_step9_has_stopping_criteria():
     assert "CONTINUE" in actions_text
 
 
+def test_step2_step_back_has_meta_cognitive_questions():
+    actions = STEPS[2]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "What makes Alan" in actions_text
+    assert "LLM-generated" in actions_text
+    assert "The applicable style guide sections are embedded below" not in actions_text
+
+
 # ---------------------------------------------------------------------------
 # CLI invocation (subprocess, matches test_workflow_steps pattern)
 # ---------------------------------------------------------------------------

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -191,6 +191,7 @@ def test_step9_has_stopping_criteria():
     assert "CONTINUE" in actions_text


+# Procedural list answers the question before it is asked, defeating meta-cognitive priming; test locks this invariant. (ref: DL-002)
 def test_step2_step_back_has_meta_cognitive_questions():
     actions = STEPS[2]["actions"]
     actions_text = "\n".join(str(a) for a in actions)

```


**CC-M-001-013** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-013

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -199,6 +199,14 @@ def test_step2_step_back_has_meta_cognitive_questions():
     assert "The applicable style guide sections are embedded below" not in actions_text
 
 
+def test_step6_thresholds_are_binding():
+    actions = STEPS[6]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "advisory" not in actions_text
+    assert "PASS" in actions_text
+    assert "FAIL" in actions_text
+
+
 # ---------------------------------------------------------------------------
 # CLI invocation (subprocess, matches test_workflow_steps pattern)
 # ---------------------------------------------------------------------------

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -199,6 +199,7 @@ def test_step2_step_back_has_meta_cognitive_questions():
     assert "The applicable style guide sections are embedded below" not in actions_text


+# Advisory language + advisory Step 8 produces zero consequences for WEAK assessment; test prevents regression to advisory form. (ref: DL-003)
 def test_step6_thresholds_are_binding():
     actions = STEPS[6]["actions"]
     actions_text = "\n".join(str(a) for a in actions)

```


**CC-M-001-014** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-014

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -207,6 +207,15 @@ def test_step6_thresholds_are_binding():
     assert "FAIL" in actions_text
 
 
+def test_step1_has_consumer_purpose_context_fields():
+    actions = STEPS[1]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "Consumers" in actions_text
+    assert "Purpose" in actions_text
+    assert "Code Context" in actions_text
+
+
 # ---------------------------------------------------------------------------
 # CLI invocation (subprocess, matches test_workflow_steps pattern)
 # ---------------------------------------------------------------------------

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -207,6 +207,7 @@ def test_step6_thresholds_are_binding():
     assert "FAIL" in actions_text


+# Consumer, Purpose, and Code Context feed later steps; omitting them collapses context-appropriate style checking to uniform rules. (ref: DL-004, DL-005)
 def test_step1_has_consumer_purpose_context_fields():
     actions = STEPS[1]["actions"]
     actions_text = "\n".join(str(a) for a in actions)

```


**CC-M-001-015** (skills/alan-coding-style/README.md)

**Documentation:**

```diff
--- a/skills/alan-coding-style/README.md
+++ b/skills/alan-coding-style/README.md
@@ -1,7 +1,8 @@
 # Alan Coding Style
 
-Style-matched code generation and review. The skill orchestrates an 8-step
-workflow (classify -> retrieve rules -> apply -> detect anti-patterns -> AI voice
-removal -> check positive patterns -> consolidate -> refine) driven by
+Style-matched code generation and review. The skill orchestrates a 9-step
+workflow (classify -> retrieve rules -> apply -> detect anti-patterns -> AI voice
+removal -> check positive patterns -> consolidate -> refine -> quality gate) driven by
 `coding_style.py`. Style guide sections in `references/*.md` are loaded at
 runtime and injected as labeled plain text into step guidance.

```

