# Plan

## Overview

The alan-coding-style skill re-injects full style reference content (~555 lines across 13 section files) into every step output, including verification and refinement steps (4-7) that operate from accumulated --thoughts context rather than raw reference text. This wastes tokens and context window capacity.

**Approach**: Add a per-step needs_references flag to the STEPS dict. Gate load_section_files in main() on this flag so steps 4-7 skip file I/O and CDATA embedding. Replace full reference injection with a brief style_reference_summary reminder for steps 4-7 that names selected sections and directs the LLM to rely on accumulated thoughts.

## Planning Context

### Decision Log

| ID | Decision | Reasoning Chain |
|---|---|---|
| DL-001 | Per-step needs_references flag in STEPS dict controls reference injection | Steps 2-3 actively use reference text (rule retrieval, code generation) -> Steps 4-7 work from accumulated --thoughts context -> Adding a boolean flag per step is minimal change, explicit, and backward-compatible with WORKFLOW construction since StepDef ignores extra keys in STEPS dict |
| DL-002 | Conditional reference loading in main() gated on needs_references | Currently main() loads sections unconditionally when --sections is provided -> Gating on STEPS[step][needs_references] means file I/O and CDATA embedding only happen for steps 2-3 -> Steps 4-7 still receive --sections in invoke_after for chain continuity but do not load/embed the content |
| DL-003 | Steps 4-7 get a brief reminder note instead of full reference text | Completely removing all style context from steps 4-7 risks drift from style rules -> A short TextNode reminder (section names selected, refer to accumulated thoughts) preserves grounding without re-injecting 500+ lines of reference content -> Net token savings ~80% for steps 4-7 |
| DL-004 | Gate reference loading in main() rather than filtering in format_output | Two candidate gate points: main() or format_output. main() is the better gate because it avoids the file I/O cost entirely -- load_section_files reads .md files from disk, so skipping the call saves both I/O and token-embedding cost. format_output would still receive loaded content and discard it, wasting the I/O. Therefore: gate in main(), pass file_nodes=None for non-reference steps. |

### Rejected Alternatives

| Alternative | Why Rejected |
|---|---|
| Lazy-load reference content on demand within format_output | Defers file I/O to formatting layer, mixing concerns. main() is the natural gate for I/O because it already owns the argparse and section loading logic. Lazy-loading also complicates testing since format_output would need filesystem access. (ref: DL-004) |
| Cache loaded reference content across steps (e.g., memoize load_section_files) | Each step runs in a separate process invocation, so in-memory caching provides no cross-step benefit. File-system caching adds complexity for marginal gain since the goal is to avoid loading at all, not to load faster. (ref: DL-002) |
| Use step-number threshold (if step < 4) instead of per-step flag | Hard-codes the boundary between reference-needing and non-reference steps. A per-step flag is more explicit and allows future steps to opt in or out independently without changing threshold logic. (ref: DL-001) |

### Constraints

- MUST: preserve correctness -- steps that need reference text must still get it
- MUST: maintain --thoughts accumulation pattern across steps
- MUST: keep WORKFLOW constant derivable from STEPS for test discovery
- SHOULD: reduce token usage by not re-injecting full reference text in steps 4-7
- SHOULD: maintain backward compatibility with CLI invocation (--step, --sections, --thoughts)
- MUST-NOT: break existing tests in tests/test_alan_coding_style.py

### Known Risks

- **Steps 4-7 may lose access to specific style rule details needed for violation checking**: HISTORY_STEP_4 drops 'Applicable Rules' from accumulation schema. Steps 4-7 reference 'from Step 2 rules' but rules won't be in --thoughts. Mitigation: the style_reference_summary includes section names; step action text already names specific patterns to check (e.g., anti-patterns, positive markers). Monitor for quality degradation.
- **StepDef constructor may reject unknown keys (needs_references) in STEPS dict entries**: WORKFLOW construction uses explicit keyword args (id=, title=, actions=) extracted from STEPS entries, not **kwargs unpacking. Extra keys in the STEPS dict are ignored. Verified at lines 712-716.
- **Existing tests may assert on style_references presence for steps 4-7**: Review test_alan_coding_style.py before implementation to identify any step-specific reference assertions that need updating.

## Invisible Knowledge

### System

DeepThink pattern: STEPS dict + WORKFLOW constant + format_step_output/format_output + argparse main(). WORKFLOW is derived from STEPS at module level for test discovery. StepDef no longer has phase= field (removed in commit 832d7bb). Workflow AST nodes: StepHeaderNode, CurrentActionNode, InvokeAfterNode from skills.lib.workflow.ast.

### Invariants

- WORKFLOW constant must be derivable from STEPS dict at module level -- test discovery depends on this
- Each step invocation is a separate process; no in-memory state persists between steps
- --sections is forwarded unconditionally in invoke_after regardless of needs_references flag
- StepDef constructor takes explicit (id, title, actions) -- extra STEPS dict keys are safely ignored

### Tradeoffs

- Token savings vs. rule accessibility: steps 4-7 lose full reference text but gain ~80% token reduction per step. HISTORY_STEP_4/5/6 schemas drop 'Applicable Rules' from accumulation, so rule content is not carried in --thoughts either. Steps 4-7 rely on action text naming specific patterns rather than referencing raw rules.
- Per-step flag vs. step-number threshold: flag is more verbose (7 entries vs. 1 conditional) but allows independent opt-in/opt-out per step without magic numbers.

## Milestones

### Milestone 1: Add needs_references flag and gate reference injection

**Files**: skills/scripts/skills/alan_coding_style/coding_style.py, skills/scripts/tests/test_alan_coding_style.py

**Acceptance Criteria**:

- AC-001: Every STEPS dict entry (1-7) has a needs_references boolean key
- AC-002: Steps 2-3 have needs_references=True; steps 1,4-7 have needs_references=False
- AC-003: Running --step 2 --sections X loads and embeds full style_references content
- AC-004: Running --step 4 --sections X does NOT load files and does NOT emit style_references block
- AC-005: Running --step 4 --sections X emits a style_reference_summary element with section names
- AC-006: --sections is still forwarded in invoke_after for all steps (chain continuity)
- AC-007: WORKFLOW constant is still derivable from STEPS (module imports without error)
- AC-008: All existing tests in test_alan_coding_style.py pass without modification (unless they assert step 4-7 reference presence)

**Tests**:

- test_needs_references_flag_exists_on_all_steps: STEPS dict has needs_references boolean on every entry with correct values
- test_steps_needing_references_get_file_nodes: format_output for steps 2-3 with file_nodes populated emits style_references and CDATA
- test_steps_not_needing_references_skip_file_nodes: format_output for steps 4-7 with file_nodes=None and sections_arg set emits style_reference_summary but not style_references
- Existing test suite passes (regression check)

#### Code Intent

- **CI-M-001-001** `skills/scripts/skills/alan_coding_style/coding_style.py`: Add needs_references boolean key to each entry in STEPS dict. Steps 2-3 set needs_references=True, Steps 1 and 4-7 set needs_references=False. Step 1 does not load or use reference content (it selects sections); --sections forwarding in invoke_after is independent of this flag (handled by CI-M-001-004). (refs: DL-001)
- **CI-M-001-002** `skills/scripts/skills/alan_coding_style/coding_style.py`: In main(), gate the load_section_files call: only call it when args.sections is provided AND STEPS[args.step_number].get(needs_references, True) is True. When the flag is False, set file_nodes=None so format_output skips the style_references block entirely. (refs: DL-002, DL-004)
- **CI-M-001-003** `skills/scripts/skills/alan_coding_style/coding_style.py`: In format_output, when file_nodes is None/empty AND sections_arg is truthy AND step >= 4, emit a short <style_reference_summary> XML element containing just the selected section names and a note to rely on accumulated thoughts from Steps 2-3. CAVEAT: HISTORY_STEP_4/5/6 schemas drop 'Applicable Rules' from accumulation, so --thoughts may not carry specific rule content. The summary serves as a section-name anchor; step action text already names specific patterns to check. This replaces the full CDATA-wrapped content for verification/refinement steps. (refs: DL-003)
- **CI-M-001-004** `skills/scripts/skills/alan_coding_style/coding_style.py`: The invoke_after command in format_output continues to forward --sections for all steps (no change to lines 697-702). This preserves the chain so a future step that needs references can opt back in. (refs: DL-002)
- **CI-M-001-005** `skills/scripts/tests/test_alan_coding_style.py`: Add test_steps_needing_references_get_file_nodes: call format_output for steps 2-3 with file_nodes populated, assert style_references and CDATA appear. Add test_steps_not_needing_references_skip_file_nodes: call format_output for steps 4-7 with file_nodes=None and sections_arg set, assert style_references does NOT appear but style_reference_summary DOES appear. (refs: DL-001, DL-003)
- **CI-M-001-006** `skills/scripts/tests/test_alan_coding_style.py`: Add test_needs_references_flag_exists_on_all_steps: iterate STEPS dict, assert every entry has a needs_references key with a boolean value. Steps 2-3 are True, steps 1 and 4-7 are False. (refs: DL-001)

#### Code Changes

**CC-M-001-001** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-001

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -161,4 +161,5 @@ STEPS = {
     1: {
         "id": "context_analysis",
         "phase": "UNDERSTANDING",
         "step_title": "Context Analysis",
+        "needs_references": False,
         "actions": [
@@ -223,4 +224,5 @@ STEPS = {
     2: {
         "id": "style_rule_retrieval",
         "phase": "UNDERSTANDING",
         "step_title": "Style Rule Retrieval",
+        "needs_references": True,
         "actions": [
@@ -260,4 +262,5 @@ STEPS = {
     3: {
         "id": "apply_style_rules",
         "phase": "GENERATION",
         "step_title": "Apply Style Rules",
+        "needs_references": True,
         "actions": [
@@ -306,4 +310,5 @@ STEPS = {
     4: {
         "id": "anti_pattern_detection",
         "phase": "VERIFICATION",
         "step_title": "Anti-Pattern Detection",
+        "needs_references": False,
         "actions": [
@@ -430,4 +435,5 @@ STEPS = {
     5: {
         "id": "positive_pattern_check",
         "phase": "VERIFICATION",
         "step_title": "Positive Pattern Check",
+        "needs_references": False,
         "actions": [
@@ -495,4 +501,5 @@ STEPS = {
     6: {
         "id": "cross_check_consolidation",
         "phase": "VERIFICATION",
         "step_title": "Cross-Check Consolidation",
+        "needs_references": False,
         "actions": [
@@ -551,4 +558,5 @@ STEPS = {
     7: {
         "id": "refine_deliver",
         "phase": "REFINEMENT",
         "step_title": "Refine & Deliver",
+        "needs_references": False,
         "actions": [
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -159,6 +159,9 @@ Ordered list of fixes to apply in Step 7.
 """
 
 
+# needs_references controls whether this step loads and injects full style
+# reference text. Steps 2-3 need rule content for retrieval and generation;
+# steps 1 and 4-7 operate from task classification or accumulated --thoughts. (ref: DL-001)
 STEPS = {
     1: {
         "id": "context_analysis",

```


**CC-M-001-002** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-002

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -766,5 +766,6 @@ def main():
 
     file_nodes = None
     if args.sections:
-        sec_list = [s.strip() for s in args.sections.split(",") if s.strip()]
-        file_nodes = load_section_files(sec_list)
+        if STEPS.get(args.step_number, {}).get("needs_references", True):
+            sec_list = [s.strip() for s in args.sections.split(",") if s.strip()]
+            file_nodes = load_section_files(sec_list)
 
     guidance = get_step_guidance(args.step_number)
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -766,6 +766,9 @@ def main():
 
     file_nodes = None
     if args.sections:
+        # Gate file I/O at the call site: load_section_files reads .md files
+        # from disk, so skipping the call avoids both I/O and token-embedding
+        # cost for steps that do not need reference content. (ref: DL-002, DL-004)
         if STEPS.get(args.step_number, {}).get("needs_references", True):
             sec_list = [s.strip() for s in args.sections.split(",") if s.strip()]
             file_nodes = load_section_files(sec_list)

```


**CC-M-001-003** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-003

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -679,6 +679,15 @@ def format_output(
     if file_nodes:
         parts.append("<style_references>")
         parts.append("Style guide sections loaded based on your section selection:")
         parts.append("")
         renderer = XMLRenderer()
         for node in file_nodes:
             parts.append(renderer.render_file_content(node))
             parts.append("")
         parts.append("</style_references>")
         parts.append("")
+    elif sections_arg and step >= 4:
+        section_names = ", ".join(s.strip() for s in sections_arg.split(",") if s.strip())
+        parts.append(
+            f"<style_reference_summary>Selected sections: {section_names}. "
+            "Rely on accumulated thoughts from Steps 2-3 for rule details."
+            "</style_reference_summary>"
+        )
+        parts.append("")
 
     parts.append(render_current_action(CurrentActionNode(guidance["actions"])))
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -688,6 +688,9 @@ def format_output(
         parts.append("")
+    # When reference files are not loaded (steps 4-7), emit a compact summary
+    # with section names so the step retains style grounding without re-injecting
+    # 500+ lines of reference content. Rule details are available in accumulated
+    # --thoughts from Steps 2-3. (ref: DL-003)
     elif sections_arg and step >= 4:
         section_names = ", ".join(s.strip() for s in sections_arg.split(",") if s.strip())
         parts.append(

```


**CC-M-001-004** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-004

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -697,7 +697,7 @@ def format_output(
     if is_complete or "COMPLETE" in next_text.upper():
         parts.append("WORKFLOW COMPLETE - Deliver final code.")
     else:
         if step == 1:
             next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step 2 --sections <SELECTED_SECTIONS> --thoughts \\"<accumulated>\\"'\n         elif sections_arg:\n             next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --sections {sections_arg} --thoughts \\"<accumulated>\\"'\n         else:\n             next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --thoughts \\"<accumulated>\\"'\n         parts.append(render_invoke_after(InvokeAfterNode(cmd=next_cmd)))
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -697,6 +697,8 @@ def format_output(
     if is_complete or "COMPLETE" in next_text.upper():
         parts.append("WORKFLOW COMPLETE - Deliver final code.")
     else:
+        # --sections forwarded unconditionally so downstream steps retain chain
+        # continuity regardless of their needs_references flag. (ref: DL-002)
         if step == 1:
             next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step 2 --sections <SELECTED_SECTIONS> --thoughts \\"<accumulated>\\"'
         elif sections_arg:

```


**CC-M-001-005** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-005

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -200,3 +200,27 @@ def test_cli_rejects_step_beyond_max():
     )
     assert result.returncode \!= 0
+
+
+# ---------------------------------------------------------------------------
+# needs_references flag and reference injection gating
+# ---------------------------------------------------------------------------
+
+
+@pytest.mark.parametrize("step", [2, 3])
+def test_steps_needing_references_get_file_nodes(step):
+    guidance = get_step_guidance(step)
+    nodes = load_section_files(["philosophy"])
+    output = format_output(step, guidance, "ctx", file_nodes=nodes, sections_arg="philosophy")
+    assert "<style_references>" in output
+    assert "<\![CDATA[" in output
+    assert "<style_reference_summary>" not in output
+
+
+@pytest.mark.parametrize("step", [4, 5, 6, 7])
+def test_steps_not_needing_references_skip_file_nodes(step):
+    guidance = get_step_guidance(step)
+    output = format_output(step, guidance, "ctx", file_nodes=None, sections_arg="philosophy,naming")
+    assert "<style_references>" not in output
+    assert "<style_reference_summary>" in output
+    assert "philosophy" in output
+    assert "naming" in output
```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -202,14 +202,20 @@ def test_cli_rejects_step_beyond_max():
 
 
 @pytest.mark.parametrize("step", [2, 3])
+def test_steps_needing_references_get_file_nodes(step):
+    """Steps 2-3 receive file_nodes and emit style_references with CDATA content."""
     guidance = get_step_guidance(step)
     nodes = load_section_files(["philosophy"])
     output = format_output(step, guidance, "ctx", file_nodes=nodes, sections_arg="philosophy")
     assert "<style_references>" in output
     assert "<![CDATA[" in output
     assert "<style_reference_summary>" not in output
 
 
 @pytest.mark.parametrize("step", [4, 5, 6, 7])
+def test_steps_not_needing_references_skip_file_nodes(step):
+    """Steps 4-7 with file_nodes=None emit style_reference_summary, not style_references."""
     guidance = get_step_guidance(step)
     output = format_output(step, guidance, "ctx", file_nodes=None, sections_arg="philosophy,naming")
     assert "<style_references>" not in output

```


**CC-M-001-006** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-006

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -200,3 +200,16 @@ def test_cli_rejects_step_beyond_max():
     )
     assert result.returncode \!= 0
+
+
+def test_needs_references_flag_exists_on_all_steps():
+    for step_num, step_data in STEPS.items():
+        assert "needs_references" in step_data, (
+            f"Step {step_num} missing needs_references key"
+        )
+        assert isinstance(step_data["needs_references"], bool), (
+            f"Step {step_num} needs_references must be bool"
+        )
+    assert STEPS[2]["needs_references"] is True
+    assert STEPS[3]["needs_references"] is True
+    for step_num in [1, 4, 5, 6, 7]:
+        assert STEPS[step_num]["needs_references"] is False
```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -215,5 +215,6 @@ def test_cli_rejects_step_beyond_max():
 
 
 def test_needs_references_flag_exists_on_all_steps():
+    """Every STEPS entry has a needs_references bool; steps 2-3 are True, rest are False."""
     for step_num, step_data in STEPS.items():
         assert "needs_references" in step_data, (

```


**CC-M-001-007** (skills/alan-coding-style/README.md)

**Documentation:**

```diff
--- a/skills/alan-coding-style/README.md
+++ b/skills/alan-coding-style/README.md
@@ -43,3 +43,14 @@ naming review doesn't need architecture patterns. Adding a section requires a new
 `.md` file and an entry in `SECTION_TO_FILE` in `coding_style.py`.
+
+### Why Reference Injection Is Gated Per Step
+
+Steps 2-3 (rule retrieval, code generation) require full reference text because
+they match rules to task context and produce style-compliant code. Steps 4-7
+(anti-pattern detection through refinement) receive accumulated --thoughts from
+Steps 2-3 that already encode the relevant rules and classification.
+
+Re-injecting 500+ lines of reference content into every step wastes tokens without
+adding information the model does not already have in context. The STEPS dict
+carries a `needs_references` boolean per entry; `main()` skips `load_section_files`
+when the flag is False, avoiding both disk I/O and token-embedding cost. Steps 4-7
+emit a compact `<style_reference_summary>` with section names as an anchor.
+(ref: DL-001, DL-002, DL-003, DL-004)

```

