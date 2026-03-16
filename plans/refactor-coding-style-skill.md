# Plan

## Overview

alan-coding-style script output diverges from leon_writing_style in XML organization: uses <style_references> with CDATA file path blocks, has per-step HISTORY constants causing duplicate content, and format_output has extra parameters leaking implementation details to executing agents

**Approach**: Converge alan output structure to match leon (step_header + xml_mandate + accumulated_thoughts + current_action + invoke_after). Move section content injection from format_output into get_step_guidance. Replace per-step HISTORY constants with single shared template. Remove FileContentNode usage so no file paths or CDATA appear in output

## Planning Context

### Decision Log

| ID | Decision | Reasoning Chain |
|---|---|---|
| DL-001 | Converge format_output signature to leon 3-param pattern (step, guidance, thoughts) | alan format_output takes 5 params (step, guidance, thoughts, file_nodes, sections_arg) vs leon 3 params -> extra params exist only to inject section content into output -> moving section injection into get_step_guidance eliminates the divergence and removes implementation details from the output formatter |
| DL-002 | Replace per-step HISTORY_STEP_N constants with single shared HISTORY_TEMPLATE | alan has 6 separate HISTORY_STEP_N constants each repeating Classification table and accumulating prior-step schemas -> leon uses single HISTORY_TEMPLATE referenced by all steps -> per-step variants cause duplicate content in output when agents carry forward accumulated thoughts -> single template eliminates redundancy and matches leon pattern |
| DL-003 | Embed loaded section content as plain text within current_action, not as <style_references> with <file path=...> CDATA blocks | leon output has no file paths or CDATA in output -> alan <style_references> block exposes implementation details (file paths) to executing agents -> embedding section content as labeled text blocks inside current_action hides implementation while still delivering content -> satisfies MUST: implementation does not leak into runtime behavior |
| DL-004 | Keep --sections CLI arg and load_section_files mechanism but move content injection into get_step_guidance | MUST: implementation remains markdown-file-based -> sections loading is the mechanism that fulfills this -> but format_output should not know about sections -> get_step_guidance receives sections list, loads files, embeds content into actions list before returning -> format_output receives pre-composed guidance dict identical to leon pattern |
| DL-005 | Remove FileContentNode import and usage from coding_style.py | FileContentNode renders as <file path="..."><![CDATA[...]]></file> which leaks file paths into output -> section content embedded as plain text does not need FileContentNode -> removing it eliminates the path-leaking mechanism entirely |
| DL-006 | Keep alan's simpler get_step_guidance pattern; do not adopt leon's STEP_HANDLERS dispatch | leon has per-step handle_step_N functions dispatched through a STEP_HANDLERS dict (9 handlers + dict at line 1017) -> alan uses simpler get_step_guidance that directly indexes STEPS dict without per-step handler functions -> alan's approach is already cleaner and does not need STEP_HANDLERS -> keep alan's pattern, only align output format to match leon |

### Rejected Alternatives

| Alternative | Why Rejected |
|---|---|
| Inline all markdown content directly in Python as string constants | Violates MUST constraint: bulk of style text/instruction must live in committed markdown files, not inline in Python. Would make content harder to review and maintain. (ref: DL-003) |
| Remove --sections arg entirely and hardcode section loading per step | Reduces flexibility - the current mechanism allows step 1 to select relevant sections dynamically. Hardcoding loses the LLM-driven section selection that makes the workflow adaptive. (ref: DL-004) |
| Keep FileContentNode but strip file paths from its output | Treating the symptom not the cause. FileContentNode's purpose is path-labeled CDATA blocks. Better to replace the mechanism entirely with plain text embedding that has no path concept. (ref: DL-005) |

### Constraints

- MUST: script output matches leon_writing_style in organization - XML tags, no file paths in output
- MUST: implementation remains markdown-file-based (references/*.md loaded at runtime)
- MUST: bulk of style text/instruction lives in committed markdown files, not inline in Python
- MUST: implementation details do not leak into runtime behavior experienced by executing agents
- SHOULD: follow skills/README.md file organization ('book pattern', section ordering)
- MUST-NOT: modify leon_writing_style

### Known Risks

- **Breaking existing tests that assert on current format_output signature and output structure**: M-001 includes code_intents (CI-M-001-008 through CI-M-001-010) that explicitly update all test callsites and assertions to match new API
- **Backward compatibility with current agent workflows that depend on --sections flag or <style_references> output format**: --sections CLI arg is preserved (DL-004). Output format changes are intentional per spec. Agent invocations only change in that invoke_after no longer exposes <SELECTED_SECTIONS> mechanism directly.
- **Section content formatting changes may alter how executing agents interpret style guidance**: Content is identical - only the container changes from CDATA blocks to labeled plain text. Acceptance criteria verify content presence in output.
- **WORKFLOW module-level constant or StepDef usage may regress if refactoring touches module structure**: Invariant documented: WORKFLOW constant must remain at module level for test discovery. StepDef has no phase field (regression test exists). Code intents do not modify WORKFLOW or StepDef schema.

## Invisible Knowledge

### System

leon_writing_style is the canonical pattern - alan-coding-style should converge on its output structure. The book pattern from skills/README.md requires specific section ordering in the Python file.

### Invariants

- WORKFLOW constant must exist at module level for test discovery via discover_workflows
- StepDef no longer has a phase field (removed during rebase, regression test exists)

### Tradeoffs

- leon_writing_style is the canonical pattern - alan should converge on its output structure, not the other way around
- The book pattern from skills/README.md requires specific section ordering in the Python file - refactored code must maintain this ordering

## Milestones

### Milestone 1: Refactor coding_style.py output to match leon pattern

**Files**: skills/scripts/skills/alan_coding_style/coding_style.py, skills/scripts/tests/test_alan_coding_style.py

**Requirements**:

- format_output signature matches leon 3-param pattern (step, guidance, thoughts)
- No <style_references>, <file path=...>, or <![CDATA[ markers in any step output
- Section content from references/*.md appears as plain text in <current_action> output
- Single HISTORY_TEMPLATE replaces all per-step HISTORY_STEP_N constants
- WORKFLOW module-level constant preserved for test discovery
- All existing tests updated and passing with new API

**Acceptance Criteria**:

- AC-001: format_output(step, guidance, thoughts) produces output with sections: step_header, xml_mandate (step 1 only), accumulated_thoughts, current_action, invoke_after
- AC-002: No output from any step contains file paths, CDATA markers, or <style_references> tags
- AC-003: Step 2+ output with --sections includes section content as labeled plain text within <current_action>
- AC-004: Step 1 invoke_after contains --sections <SELECTED_SECTIONS> placeholder
- AC-005: All tests in test_alan_coding_style.py pass
- AC-006: python3 -m skills.alan_coding_style.coding_style --step 1 --thoughts '' produces valid output matching leon organization

**Tests**:

- test_format_output 3-param call produces expected XML structure
- test_format_output_with_sections verifies section content as plain text in <current_action> (no CDATA/file paths)
- test_format_output_step1 includes xml_mandate and <SELECTED_SECTIONS> in invoke_after
- test_get_step_guidance_with_sections verifies sections content embedded in guidance actions
- test_history_template single shared template referenced by all steps

#### Code Intent

- **CI-M-001-001** `skills/scripts/skills/alan_coding_style/coding_style.py`: Replace 6 per-step HISTORY_STEP_N constants (HISTORY_STEP_2 through HISTORY_STEP_7) with a single HISTORY_TEMPLATE constant matching leon pattern. The template covers Classification, Applicable Rules, Draft Output, Violations, AI Voice Issues, Positive Markers, and Refinements as a unified schema. Each step action list references HISTORY_TEMPLATE instead of its step-specific constant. (refs: DL-002)
- **CI-M-001-002** `skills/scripts/skills/alan_coding_style/coding_style.py`: Refactor get_step_guidance to accept an optional sections parameter (list of section names). When sections are provided, load the corresponding markdown files via load_section_files, convert their content to labeled text blocks (section name as header, content below, no file paths), and prepend them to the actions list in the returned guidance dict. This moves section injection from format_output into get_step_guidance. For step 5, always append ai-voice-removal content regardless of sections arg. (refs: DL-004, DL-003)
- **CI-M-001-003** `skills/scripts/skills/alan_coding_style/coding_style.py`: Simplify format_output signature to match leon: format_output(step, guidance, thoughts). Remove file_nodes and sections_arg parameters. Remove the <style_references> block rendering. Remove FileContentNode import and usage. The function body becomes: step_header + xml_mandate (step 1) + accumulated_thoughts + current_action + invoke_after, matching leon exactly. (refs: DL-001, DL-005)
- **CI-M-001-004** `skills/scripts/skills/alan_coding_style/coding_style.py`: Simplify invoke_after command construction. Step 1: invoke_after includes --sections <SELECTED_SECTIONS> as a placeholder for the LLM to fill with actual section names. Steps 2+: invoke_after propagates the --sections value received via CLI args (if any). Remove the special-case step-1 code path that currently renders <SELECTED_SECTIONS> differently from other steps; unify the rendering so all steps use the same invoke_after construction logic, differing only in the --sections value passed. (refs: DL-001, DL-004)
- **CI-M-001-005** `skills/scripts/skills/alan_coding_style/coding_style.py`: Update main() to pass sections list to get_step_guidance instead of to format_output. The flow becomes: parse args -> get_step_guidance(step, sections=sec_list) -> format_output(step, guidance, thoughts) -> print. Also store sections_arg for invoke_after construction. (refs: DL-004)
- **CI-M-001-006** `skills/scripts/skills/alan_coding_style/coding_style.py`: Remove read_text_or_exit import from skills.lib.io. The load_section_files function is refactored: it no longer returns FileContentNode list. Instead it returns a list of (section_name, content_string) tuples. A new helper format_section_block(name, content) formats each section as a labeled text block without exposing file paths. (refs: DL-003, DL-005)
- **CI-M-001-007** `skills/scripts/skills/alan_coding_style/coding_style.py`: XML_FORMAT_MANDATE remains as module-level constant. Leon inlines its xml_mandate in format_output; alan keeps it as a named constant for readability. Either approach produces identical output. No functional change needed - this is a keep-as-is decision. (refs: DL-001)
- **CI-M-001-008** `skills/scripts/tests/test_alan_coding_style.py`: Update format_output test calls to use 3-param signature (remove file_nodes and sections_arg params). Update test_format_output_with_file_nodes to verify section content appears as plain text inside <current_action> without <style_references>, <file path=...>, or <![CDATA[ markers. Update test_format_output_step1_includes_invoke_with_sections_placeholder to verify step 1 invoke_after still contains <SELECTED_SECTIONS>. Update test_format_output_middle_step_includes_invoke_after to not pass sections_arg to format_output (sections no longer part of format_output API). Add test_get_step_guidance_with_sections verifying that sections content is embedded in guidance actions when sections parameter is provided. (refs: DL-001, DL-003)
- **CI-M-001-009** `skills/scripts/tests/test_alan_coding_style.py`: Update imports: remove load_section_files if no longer needed in tests (or keep if testing section loading separately). Remove FileContentNode from any test assertions. Add imports for any new functions exposed by the refactored module. (refs: DL-005)
- **CI-M-001-010** `skills/scripts/tests/test_alan_coding_style.py`: Update CLI invocation tests: step 1 CLI test should verify output has no <style_references> or <file path=...>. Steps 2+ with --sections should verify section content appears as plain text in <current_action> output, not in CDATA blocks. (refs: DL-003)

#### Code Changes

**CC-M-001-002** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-006

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -14,7 +14,6 @@ import argparse
 import sys
 from pathlib import Path
 
-from skills.lib.io import read_text_or_exit
 from skills.lib.workflow.core import (
     StepDef,
     Workflow,
@@ -26,7 +26,6 @@ from skills.lib.workflow.ast import W, XMLRenderer, render
 from skills.lib.workflow.ast.nodes import (
-    FileContentNode, TextNode, StepHeaderNode, CurrentActionNode, InvokeAfterNode,
+    TextNode, StepHeaderNode, CurrentActionNode, InvokeAfterNode,
 )
 from skills.lib.workflow.ast.renderer import (
     render_step_header, render_current_action, render_invoke_after,
@@ -65,11 +65,15 @@ def get_references_dir() -> Path:
     return Path(__file__).parent.parent.parent.parent / "alan-coding-style" / "references"
 
 
-def load_section_files(sections: list[str]) -> list[FileContentNode]:
+def load_section_files(sections: list[str]) -> list[tuple[str, str]]:
     refs_dir = get_references_dir()
-    nodes = []
+    result = []
     for sec in sections:
         if sec not in SECTION_TO_FILE:
             valid = ", ".join(sorted(SECTION_TO_FILE.keys()))
             sys.exit(f"ERROR: Unknown section {sec}. Valid: {valid}")
         rel_path = SECTION_TO_FILE[sec]
         full_path = refs_dir / rel_path
-        content = read_text_or_exit(full_path, f"loading section {sec}")
-        nodes.append(FileContentNode(path=f"references/{rel_path}", content=content))
-    return nodes
+        if not full_path.exists():
+            sys.exit(f"ERROR: Section file not found: {full_path}")
+        content = full_path.read_text()
+        result.append((sec, content))
+    return result
+
+
+def format_section_block(name: str, content: str) -> str:
+    return f"=== {name} ===\n{content.strip()}"
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -65,6 +65,11 @@ def get_references_dir() -> Path:
 
 
 def load_section_files(sections: list[str]) -> list[tuple[str, str]]:
+    """Load reference markdown files for the given section names.
+
+    Isolated from format_output so file I/O stays separate from output
+    formatting. Returns (section_name, file_content) pairs. Exits on
+    unknown section name or missing file. (ref: DL-003, DL-005)
+    """
     refs_dir = get_references_dir()
     result = []
     for sec in sections:
@@ -79,4 +83,8 @@ def load_section_files(sections: list[str]) -> list[tuple[str, str]]:
 
 
 def format_section_block(name: str, content: str) -> str:
+    """Format a section as a labeled plain-text block for embedding in current_action.
+
+    Output: "=== name ===\ncontent" - visible to executing agents without file paths. (ref: DL-003)
+    """
     return f"=== {name} ===\n{content.strip()}"

```

> **Developer notes**: Remove read_text_or_exit import per DL-005; load_section_files returns (name, content) tuples instead of FileContentNode list to eliminate CDATA path-leaking mechanism. Labeled text blocks expose section content without file paths.

**CC-M-001-003** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-002

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -705,8 +705,26 @@ def get_references_dir() -> Path:
 
 
-def get_step_guidance(step: int) -> dict:
+def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
     """Return step-specific guidance and actions."""
     next_step = step + 1 if step < TOTAL_STEPS else None
     step_data = STEPS.get(step)
     if not step_data:
         return {
             "phase": "UNKNOWN",
             "step_title": "Unknown Step",
             "actions": ["ERROR: Invalid step number."],
             "next": "COMPLETE",
         }
     phase = step_data["phase"]
-    next_text = f"Step {next_step}: {step_data[next_desc]}" if next_step else step_data["next_desc"]
+    next_text = f"Step {next_step}: {step_data['next_desc']}" if next_step else step_data["next_desc"]
+    actions = list(step_data["actions"])
+
+    if sections:
+        loaded = load_section_files(sections)
+        section_blocks = [format_section_block(name, content) for name, content in loaded]
+        actions = section_blocks + actions
+
+    if step == 5:
+        ai_voice_sections = load_section_files(["ai-voice-removal"])
+        section_blocks = [format_section_block(name, content) for name, content in ai_voice_sections]
+        actions = actions + section_blocks
+
     return {
         "phase": phase,
         "step_title": step_data["step_title"],
-        "actions": step_data["actions"],
+        "actions": actions,
         "next": next_text,
     }
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -705,6 +705,12 @@ def get_references_dir() -> Path:
 
 
 def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
-    """Return step-specific guidance and actions."""
+    """Return step-specific guidance dict for the given step.
+
+    When sections is provided, loads the corresponding reference files and
+    prepends them as labeled plain-text blocks into the actions list.
+    Step 5 always appends the ai-voice-removal section regardless of sections.
+    (ref: DL-004, DL-003)
+    """
     next_step = step + 1 if step < TOTAL_STEPS else None

```

> **Developer notes**: Move section injection from format_output into get_step_guidance per DL-004; get_step_guidance receives sections list, loads files, embeds content as labeled text blocks prepended to actions. format_output remains agnostic to section loading.

**CC-M-001-004** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-003

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -726,54 +726,39 @@ def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
 
 
 def format_output(
     step: int,
     guidance: dict,
     thoughts: str,
-    file_nodes: list[FileContentNode] | None = None,
-    sections_arg: str | None = None,
 ) -> str:
     """Format output using AST builder API."""
     parts = []
     is_complete = step >= WORKFLOW.total_steps
 
     title = f"CODING STYLE - {guidance['phase']} - {guidance['step_title']}" 
     parts.append(render_step_header(StepHeaderNode(
         title=title,
         script="alan_coding_style",
         step=step,
     )))
     parts.append("")
 
     if step == 1:
         parts.append(XML_FORMAT_MANDATE)
         parts.append("")
 
     if thoughts:
         parts.append(render(W.el("accumulated_thoughts", TextNode(thoughts)).build(), XMLRenderer()))
         parts.append("")
 
-    if file_nodes:
-        parts.append("<style_references>")
-        parts.append("Style guide sections loaded based on your section selection:")
-        parts.append("")
-        renderer = XMLRenderer()
-        for node in file_nodes:
-            parts.append(renderer.render_file_content(node))
-            parts.append("")
-        parts.append("</style_references>")
-        parts.append("")
-
     parts.append(render_current_action(CurrentActionNode(guidance["actions"])))
     parts.append("")
 
     next_text = guidance.get("next", "")
     if is_complete or "COMPLETE" in next_text.upper():
         parts.append("WORKFLOW COMPLETE - Deliver final code.")
     else:
-        if step == 1:
-            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step 2 --sections <SELECTED_SECTIONS> --thoughts \\"<accumulated>\\"\'
-        elif sections_arg:
-            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --sections {sections_arg} --thoughts \\"<accumulated>\\"\'
-        else:
-            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --thoughts \\"<accumulated>\\"\'
+        if step == 1:
+            sections_part = guidance.get("sections_arg", "<SELECTED_SECTIONS>")
+        else:
+            sections_part = guidance.get("sections_arg", "")
+        if sections_part:
+            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --sections {sections_part} --thoughts \\"<accumulated>\\"\'
+        else:
+            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --thoughts \\"<accumulated>\\"\'
         parts.append(render_invoke_after(InvokeAfterNode(cmd=next_cmd)))
 
     return "\n".join(parts)
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -726,7 +726,9 @@ def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
 
 
 def format_output(
     step: int,
     guidance: dict,
     thoughts: str,
 ) -> str:
-    """Format output using AST builder API."""
+    """Render step output as XML using the AST builder API.
+
+    Reads sections_arg from guidance dict (set by main) to propagate
+    --sections through invoke_after without leaking it into the function
+    signature. (ref: DL-001, DL-005)
+    """

```

> **Developer notes**: Converge format_output to leon 3-param pattern (step, guidance, thoughts) per DL-001; remove FileContentNode/sections_arg to eliminate path-leaking mechanism per DL-005; unify invoke_after construction via guidance.get(sections_arg) per DL-004. Merges CC-M-001-012 to resolve overlapping region.

**CC-M-001-007** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-001

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -79,107 +79,32 @@ def get_references_dir() -> Path:
 
 
-# Per-step context schemas: each step carries only the sections it needs.
-HISTORY_STEP_2 = """
-CONTEXT ACCUMULATION: Your --thoughts MUST include:
-
-  ## Classification (from Step 1)
-  | Aspect | Value |
-  | Task Type | generate/review/refactor/fix |
-  | Language(s) | ... |
-  | Scope | file/function/module |
-
-  ## Applicable Rules (building)
-  | Category | Rule | Source Section |
-
-  ## Anti-Patterns to Watch (building)
-  | Anti-Pattern | Why Likely |
-"""
-
-HISTORY_STEP_3 = """
-CONTEXT ACCUMULATION: Your --thoughts MUST include:
-
-  ## Classification (from Step 1)
-  | Aspect | Value |
-  | Task Type | generate/review/refactor/fix |
-  | Language(s) | ... |
-  | Scope | file/function/module |
-
-  ## Applicable Rules (from Step 2)
-  | Category | Rule | Source Section |
-
-  ## Draft Output (building)
-  Code or analysis notes produced in this step.
-"""
-
-HISTORY_STEP_4 = """
-CONTEXT ACCUMULATION: Your --thoughts MUST include:
-
-  ## Classification (from Step 1)
-  | Aspect | Value |
-  | Task Type | generate/review/refactor/fix |
-  | Language(s) | ... |
-  | Scope | file/function/module |
-
-  ## Draft Code (from Step 3)
-  The code or analysis produced in Step 3.
-
-  ## Violations (building)
-  | Location | Pattern | Code | Confidence |
-"""
-
-HISTORY_STEP_5 = """
-CONTEXT ACCUMULATION: Your --thoughts MUST include:
-
-  ## Classification (from Step 1)
-  | Aspect | Value |
-  | Task Type | generate/review/refactor/fix |
-  | Language(s) | ... |
-  | Scope | file/function/module |
-
-  ## Draft Code (from Step 3)
-  The code or analysis produced in Step 3.
-
-  ## Violations (from Step 4)
-  | Location | Pattern | Code | Confidence |
-
-  ## AI Voice Issues (building)
-  | Location | Tell Type | Code | Confidence |
-"""
-
-HISTORY_STEP_6 = """
-CONTEXT ACCUMULATION: Your --thoughts MUST include:
-
-  ## Classification (from Step 1)
-  | Aspect | Value |
-  | Task Type | generate/review/refactor/fix |
-  | Language(s) | ... |
-  | Scope | file/function/module |
-
-  ## Draft Code (from Step 3)
-  The code or analysis produced in Step 3.
-
-  ## Violations (from Step 4)
-  | Location | Pattern | Code | Confidence |
-
-  ## AI Voice Issues (from Step 5)
-  | Location | Tell Type | Code | Confidence |
-
-  ## Positive Markers (building)
-  | Category | Count | Examples |
-"""
-
-HISTORY_STEP_7 = """
-CONTEXT ACCUMULATION: Your --thoughts MUST include:
-
-  ## Violations (from Step 4)
-  | Location | Pattern | Code | Confidence |
-
-  ## AI Voice Issues (from Step 5)
-  | Location | Tell Type | Code | Confidence |
-
-  ## Positive Markers (from Step 6)
-  | Category | Count | Examples |
-  Assessment: STRONG/MODERATE/WEAK/MINIMAL
-
-  ## Refinement Plan (building)
-  Ordered list of fixes to apply in Step 8.
-"""
-
-
+# Shared context accumulation schema referenced by all steps.
+HISTORY_TEMPLATE = """
+CONTEXT ACCUMULATION: Your --thoughts MUST include:
+
+  ## Classification (from Step 1)
+  | Aspect | Value |
+  | Task Type | generate/review/refactor/fix |
+  | Language(s) | ... |
+  | Scope | file/function/module |
+
+  ## Applicable Rules (from Step 2)
+  | Category | Rule | Source Section |
+
+  ## Draft Output (from Step 3)
+  Code or analysis notes produced in Step 3.
+
+  ## Violations (from Steps 4-5)
+  | Location | Pattern | Code | Confidence |
+
+  ## AI Voice Issues (from Step 5)
+  | Location | Tell Type | Code | Confidence |
+
+  ## Positive Markers (from Step 6)
+  | Category | Count | Examples |
+  Assessment: STRONG/MODERATE/WEAK/MINIMAL
+
+  ## Refinement Plan (from Step 7)
+  Ordered list of fixes to apply in Step 8.
+"""
+
 STEPS = {
@@ -276,7 +201,7 @@ STEPS = {
             "</rule_priority>",
             "",
-            HISTORY_STEP_2,
+            HISTORY_TEMPLATE,
         ],
         "next_desc": "Apply style rules to code.",
@@ -322,7 +247,7 @@ STEPS = {
             "</output_expectations>",
             "",
-            HISTORY_STEP_3,
+            HISTORY_TEMPLATE,
         ],
         "next_desc": "Check for anti-patterns.",
@@ -445,7 +370,7 @@ STEPS = {
             "OUTPUT: Violation table with quoted code and confidence per pattern.",
             "",
-            HISTORY_STEP_4,
+            HISTORY_TEMPLATE,
         ],
         "next_desc": "Check for AI voice in code.",
@@ -471,7 +396,7 @@ STEPS = {
             "OUTPUT: AI voice violation table with quoted code and confidence per pattern.",
             "",
-            HISTORY_STEP_5,
+            HISTORY_TEMPLATE,
         ],
         "next_desc": "Check for positive coding patterns.",
@@ -536,7 +461,7 @@ STEPS = {
             "Record your assessment level and carry it to Step 7.",
             "</sufficiency_check>",
             "",
-            HISTORY_STEP_6,
+            HISTORY_TEMPLATE,
         ],
         "next_desc": "Consolidate violations for refinement.",
@@ -594,7 +519,7 @@ STEPS = {
             "</refinement_plan>",
             "",
-            HISTORY_STEP_7,
+            HISTORY_TEMPLATE,
         ],
         "next_desc": "Apply refinements and deliver.",

@@ -472,7 +472,7 @@ STEPS = {
             "  - 'meta-commentary openers' -> meta-docstrings describing what follows",
             "",
-            "The reference file is loaded below in <style_references>.",
+            "The ai-voice-removal reference is injected above.",
             "Follow every pattern exactly as written, substituting code artifacts",
             "for prose artifacts.",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -79,6 +79,8 @@ def format_section_block(name: str, content: str) -> str:
 
 
+# Context accumulation template shared by all steps.
+# Single template prevents duplicate Classification tables across steps. (ref: DL-002)
 HISTORY_TEMPLATE = """

```

> **Developer notes**: Replace per-step HISTORY_STEP_N constants with single HISTORY_TEMPLATE per leon pattern; per-step templates accumulated schema redundantly (each repeated prior steps schemas), causing duplicate content; shared template avoids the accumulation. Also updates STEPS[5].actions to remove stale reference to <style_references> block being removed.

**CC-M-001-009** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-008

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -112,7 +112,7 @@ def test_format_output_middle_step_includes_invoke_after():
     guidance = get_step_guidance(3)
-    output = format_output(3, guidance, "ctx", sections_arg="philosophy,naming")
+    guidance["sections_arg"] = "philosophy,naming"
+    output = format_output(3, guidance, "ctx")
     assert "<invoke_after>" in output
     assert "--step 4" in output
     assert "--sections philosophy,naming" in output
@@ -133,21 +133,27 @@ def test_format_output_empty_thoughts_omits_block():
 
 
 # ---------------------------------------------------------------------------
 # Section loading
 # ---------------------------------------------------------------------------
 
 
 def test_references_dir_exists():
     assert get_references_dir().is_dir()
 
 
-def test_load_section_files_returns_file_nodes():
+def test_load_section_files_returns_tuples():
     nodes = load_section_files(["philosophy"])
     assert len(nodes) == 1
-    assert "philosophy" in nodes[0].path
-    assert len(nodes[0].content) > 0
+    name, content = nodes[0]
+    assert name == "philosophy"
+    assert len(content) > 0
 
 
 def test_load_section_files_multiple():
     nodes = load_section_files(["philosophy", "naming", "types"])
     assert len(nodes) == 3
 
 
-def test_format_output_with_file_nodes():
+def test_format_output_with_file_nodes():
     guidance = get_step_guidance(2)
-    nodes = load_section_files(["philosophy"])
-    output = format_output(2, guidance, "ctx", file_nodes=nodes)
-    assert "<style_references>" in output
-    assert "<![CDATA[" in output
+    guidance2 = get_step_guidance(2, sections=["philosophy"])
+    output = format_output(2, guidance2, "ctx")
+    assert "<style_references>" not in output
+    assert "<![CDATA[" not in output
+    assert "=== philosophy ===" in output
+    assert "<current_action>" in output
+
+
+def test_get_step_guidance_with_sections():
+    guidance = get_step_guidance(2, sections=["philosophy"])
+    actions_text = "\n".join(str(a) for a in guidance["actions"])
+    assert "=== philosophy ===" in actions_text
+
+
+def test_history_template_referenced_by_steps():
+    for step_num in [2, 3, 4, 5, 6, 7]:
+        actions = STEPS[step_num]["actions"]
+        assert HISTORY_TEMPLATE in actions, f"Step {step_num} missing HISTORY_TEMPLATE"

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -112,6 +112,7 @@ def test_format_output_middle_step_includes_invoke_after():
     guidance = get_step_guidance(3)
+    # sections_arg stored in guidance dict; format_output reads it from there (ref: DL-001)
     guidance["sections_arg"] = "philosophy,naming"
     output = format_output(3, guidance, "ctx")
     assert "<invoke_after>" in output

```

> **Developer notes**: Update test calls to 3-param format_output signature after DL-001 convergence; sections_arg moved into guidance dict so tests inject it via guidance rather than as a direct parameter.

**CC-M-001-012** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-004

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -762,14 +762,11 @@ def format_output(
     next_text = guidance.get("next", "")
     if is_complete or "COMPLETE" in next_text.upper():
         parts.append("WORKFLOW COMPLETE - Deliver final code.")
     else:
-        if step == 1:
-            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step 2 --sections <SELECTED_SECTIONS> --thoughts \\"<accumulated>\\"'
-        elif sections_arg:
-            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --sections {sections_arg} --thoughts \\"<accumulated>\\"'
-        else:
-            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --thoughts \\"<accumulated>\\"'
+        if step == 1:
+            sections_part = guidance.get("sections_arg", "<SELECTED_SECTIONS>")
+        else:
+            sections_part = guidance.get("sections_arg", "")
+        if sections_part:
+            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --sections {sections_part} --thoughts \\"<accumulated>\\"'
+        else:
+            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --thoughts \\"<accumulated>\\"'
         parts.append(render_invoke_after(InvokeAfterNode(cmd=next_cmd)))
 
     return "\n".join(parts)

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -762,6 +762,8 @@ def format_output(
     next_text = guidance.get("next", "")
     if is_complete or "COMPLETE" in next_text.upper():
         parts.append("WORKFLOW COMPLETE - Deliver final code.")
     else:
+        # sections_arg passed via guidance dict so format_output stays at 3 params (ref: DL-001)
         if step == 1:
             sections_part = guidance.get("sections_arg", "<SELECTED_SECTIONS>")
         else:

```

> **Developer notes**: MERGED INTO CC-M-001-004: invoke_after unification was merged with format_output signature change to avoid overlapping region conflict. CC-M-001-004 now covers both changes.

**CC-M-001-013** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-005

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -840,19 +840,12 @@ def main():
     args = parser.parse_args()
 
     if args.step_number < 1:
         print("ERROR: step-number must be >= 1", file=sys.stderr)
         sys.exit(1)
     if args.step_number > TOTAL_STEPS:
         print(f"ERROR: step-number cannot exceed {TOTAL_STEPS}", file=sys.stderr)
         sys.exit(1)
 
-    file_nodes = None
-    if args.sections:
-        sec_list = [s.strip() for s in args.sections.split(",") if s.strip()]
-        file_nodes = load_section_files(sec_list)
-
-    # Step 5 (AI Voice Removal) always loads its reference file
-    if args.step_number == 5:
-        ai_nodes = load_section_files(["ai-voice-removal"])
-        file_nodes = (file_nodes or []) + ai_nodes
-
-    guidance = get_step_guidance(args.step_number)
-    print(format_output(
-        args.step_number,
-        guidance,
-        args.thoughts,
-        file_nodes=file_nodes,
-        sections_arg=args.sections,
-    ))
+    sec_list = [s.strip() for s in args.sections.split(",") if s.strip()] if args.sections else None
+    guidance = get_step_guidance(args.step_number, sections=sec_list)
+    if args.sections:
+        guidance["sections_arg"] = args.sections
+    print(format_output(args.step_number, guidance, args.thoughts))

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -840,6 +840,8 @@ def main():
     sec_list = [s.strip() for s in args.sections.split(",") if s.strip()] if args.sections else None
     guidance = get_step_guidance(args.step_number, sections=sec_list)
     if args.sections:
+        # Propagate sections string through guidance dict so format_output can
+        # emit it in invoke_after without an extra parameter. (ref: DL-001, DL-004)
         guidance["sections_arg"] = args.sections
     print(format_output(args.step_number, guidance, args.thoughts))

```

> **Developer notes**: Update main() to route sections through get_step_guidance per DL-004; sections are an implementation detail that get_step_guidance consumes, not a parameter that format_output needs. Sections_arg stored separately for invoke_after propagation.

**CC-M-001-014** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-010

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -176,6 +176,22 @@ def test_cli_invocation_succeeds(step):
     assert result.returncode == 0, f"Step {step} failed: {result.stderr[:300]}"
     assert "<step_header" in result.stdout
+    assert "<style_references>" not in result.stdout
+    assert "<![CDATA[" not in result.stdout
+    if step >= 2:
+        assert "=== philosophy ===" in result.stdout or "=== naming ===" in result.stdout
 
 
 def test_cli_rejects_step_zero():
@@ -198,3 +198,16 @@ def test_cli_rejects_step_beyond_max():
     )
     assert result.returncode != 0
+
+
+def test_cli_step1_includes_selected_sections_placeholder():
+    result = subprocess.run(
+        [sys.executable, "-m", "skills.alan_coding_style.coding_style",
+         "--step", "1", "--thoughts", ""],
+        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
+    )
+    assert result.returncode == 0
+    assert "<SELECTED_SECTIONS>" in result.stdout
+    assert "<style_references>" not in result.stdout

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -168,6 +168,8 @@ def test_cli_invocation_succeeds(step):
     assert result.returncode == 0, f"Step {step} failed: {result.stderr[:300]}"
     assert "<step_header" in result.stdout
+    # Output must not expose implementation details (file paths, CDATA) to agents (ref: DL-003, DL-005)
     assert "<style_references>" not in result.stdout
     assert "<![CDATA[" not in result.stdout

```

> **Developer notes**: Add CLI test assertions verifying <style_references> and CDATA blocks are absent from output per DL-005; and that --sections content appears as plain text in <current_action> without file path exposure.

**CC-M-001-015** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-009

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -13,7 +13,8 @@ from skills.alan_coding_style.coding_style import (
     STEPS,
     TOTAL_STEPS,
     WORKFLOW,
+    HISTORY_TEMPLATE,
     format_output,
     get_references_dir,
     get_step_guidance,
     load_section_files,
 )
 from skills.lib.workflow.core import Workflow

```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -13,6 +13,7 @@ from skills.alan_coding_style.coding_style import (
     STEPS,
     TOTAL_STEPS,
     WORKFLOW,
+    HISTORY_TEMPLATE,  # single context accumulation template for all steps (ref: DL-002)
     format_output,
     get_references_dir,
     get_step_guidance,

```

> **Developer notes**: Update test imports to add HISTORY_TEMPLATE (new export) and remove FileContentNode (no longer needed after DL-005 removes FileContentNode usage from coding_style.py).

**CC-M-001-016** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-007

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -35,6 +35,6 @@ XML_FORMAT_MANDATE = """<xml_format_mandate>
 XML_FORMAT_MANDATE = """<xml_format_mandate>
 CRITICAL: All script outputs use XML format. You MUST:
 1. Execute the action in <current_action>
 2. When complete, invoke the exact command in <invoke_after>
 3. DO NOT modify commands. DO NOT skip steps.
 </xml_format_mandate>"""

```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -33,6 +33,8 @@ TOTAL_STEPS = 8
 
 
+# Injected at step 1 only; instructs executing agents to follow XML protocol.
+# Content is agent-facing instruction text, not code metadata.
 XML_FORMAT_MANDATE = """<xml_format_mandate>

```

> **Developer notes**: No functional change: XML_FORMAT_MANDATE stays as module-level constant. Leon inlines it in format_output; alan uses a named constant for readability. Both approaches produce identical output. Verified as keep-as-is per CI-M-001-007.

### Milestone 2: Update alan-coding-style documentation

**Files**: skills/alan-coding-style/SKILL.md, skills/alan-coding-style/README.md

**Requirements**:

- SKILL.md step count reflects actual TOTAL_STEPS (1-8)
- SKILL.md argument table does not expose --sections as user-facing arg
- README.md reflects plain text embedding instead of FileContentNode/CDATA

**Acceptance Criteria**:

- AC-M002-001: SKILL.md states steps 1-8 (not 1-7)
- AC-M002-002: SKILL.md argument table has no --sections row
- AC-M002-003: README.md contains no references to FileContentNode or CDATA
- AC-M002-004: README.md describes section loading as labeled plain text blocks injected into step guidance

**Tests**:

- Manual review: SKILL.md step range matches TOTAL_STEPS constant
- Manual review: README.md accurately describes current implementation approach

#### Code Intent

- **CI-M-002-001** `skills/alan-coding-style/SKILL.md`: Update step count from 1-7 to 1-8 (SKILL.md says 1-7 but TOTAL_STEPS is 8). Remove --sections from the argument table since it is now an internal implementation detail that the LLM fills in automatically based on step 1 output. The invoke command stays the same (--step 1 --thoughts). (refs: DL-003)
- **CI-M-002-002** `skills/alan-coding-style/README.md`: Update the Why Section-Based Loading section to reflect that section content is now embedded as plain text blocks rather than via FileContentNode/CDATA. Remove references to FileContentNode and CDATA-wrapped XML. State that sections are loaded at runtime and injected into step guidance as labeled text blocks, keeping implementation details invisible to executing agents. (refs: DL-003, DL-005)

#### Code Changes

**CC-M-002-001** (skills/alan-coding-style/SKILL.md) - implements CI-M-002-001

**Code:**

```diff
--- a/skills/alan-coding-style/SKILL.md
+++ b/skills/alan-coding-style/SKILL.md
@@ -14,8 +14,7 @@ When this skill activates, IMMEDIATELY invoke the script. The script IS the
 | Argument     | Required | Description                                        |
 | ------------ | -------- | -------------------------------------------------- |
-| `--step`     | Yes      | Current step (1-7)                                 |
+| `--step`     | Yes      | Current step (1-8)                                 |
 | `--thoughts` | No       | Accumulated thinking, draft code, and findings     |
-| `--sections` | No       | Comma-separated style guide sections to inject     |
 
 Do NOT write or draft code first. Run the script and follow its output.

```

**Documentation:**

```diff
--- a/skills/alan-coding-style/SKILL.md
+++ b/skills/alan-coding-style/SKILL.md
@@ -1,4 +1,5 @@ # Alan Coding Style Skill
 # Alan Coding Style Skill

```

> **Developer notes**: Fix step count discrepancy (SKILL.md said 1-7, TOTAL_STEPS=8); remove --sections from SKILL.md argument table since sections selection is now an internal implementation step the LLM performs automatically, not a user-visible parameter.

**CC-M-002-003** (skills/alan-coding-style/README.md) - implements CI-M-002-002

**Code:**

```diff
--- a/skills/alan-coding-style/README.md
+++ b/skills/alan-coding-style/README.md
@@ -1,7 +1,7 @@ # Alan Coding Style
 # Alan Coding Style
 
 Style-matched code generation and review. The skill orchestrates a 7-step
-workflow (classify -> retrieve rules -> apply -> detect anti-patterns -> check
-positive patterns -> consolidate -> refine) driven by `coding_style.py`. The
-style resource `coding-style.md` is loaded section-by-section based on task type.
+workflow (classify -> retrieve rules -> apply -> detect anti-patterns -> AI voice
+removal -> check positive patterns -> consolidate -> refine) driven by
+`coding_style.py`. Style guide sections in `references/*.md` are loaded at
+runtime and injected as labeled plain text into step guidance.
@@ -36,7 +36,8 @@ so agents know which to apply verbatim vs. adapt to new contexts.
 ### Why Section-Based Loading
 
 Style guide content lives in `references/*.md` (one file per `## Section`) and is
-loaded selectively via `--sections` using `FileContentNode`. Step 1 prompts the
-LLM to select sections based on task type; the selected sections are embedded in
-Step 2's output via CDATA-wrapped XML. This keeps context windows focused -- a
-naming review doesn't need architecture patterns. Adding a section requires a new
-`.md` file and an entry in `SECTION_TO_FILE` in `coding_style.py`.
+loaded selectively via `--sections`. Step 1 prompts the LLM to select sections
+based on task type; the selected sections are passed to `get_step_guidance`, which
+loads the files and injects them as labeled plain text blocks into the step's
+`current_action` output. Implementation details (file paths, CDATA markers) remain
+invisible to executing agents. This keeps context windows focused -- a naming
+review doesn't need architecture patterns. Adding a section requires a new `.md`
+file and an entry in `SECTION_TO_FILE` in `coding_style.py`.

```

**Documentation:**

```diff
--- a/skills/alan-coding-style/README.md
+++ b/skills/alan-coding-style/README.md
@@ -1,4 +1,5 @@ # Alan Coding Style
 # Alan Coding Style

```

> **Developer notes**: Update README Why Section-Based Loading to reflect plain text injection replacing FileContentNode/CDATA per DL-004 and DL-005; readers need accurate description of the mechanism to understand future maintenance decisions.
