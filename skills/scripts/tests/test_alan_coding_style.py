"""Tests for alan_coding_style skill.

Covers: WORKFLOW construction, format_output for all steps, section loading,
CLI invocation, and regression for the phase= removal.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from skills.alan_coding_style.coding_style import (
    STEPS,
    TOTAL_STEPS,
    WORKFLOW,
    _HISTORY_SENTINEL,
    history_template,
    format_output,
    get_references_dir,
    get_step_guidance,
    load_section_files,
)
from skills.lib.workflow.core import Workflow


SCRIPTS_DIR = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# WORKFLOW construction
# ---------------------------------------------------------------------------


def test_workflow_is_workflow_instance():
    assert isinstance(WORKFLOW, Workflow)


def test_workflow_name():
    assert WORKFLOW.name == "alan-coding-style"


def test_workflow_step_count_matches_total():
    assert WORKFLOW.total_steps == TOTAL_STEPS


def test_workflow_step_ids_match_steps_dict():
    expected_ids = [STEPS[i]["id"] for i in sorted(STEPS)]
    assert list(WORKFLOW._step_order) == expected_ids


def test_stepdef_has_no_phase_field():
    """Regression: StepDef lost its phase field during rebase."""
    for step_def in WORKFLOW.steps.values():
        assert not hasattr(step_def, "phase"), (
            f"StepDef '{step_def.id}' should not have phase attribute"
        )


# ---------------------------------------------------------------------------
# get_step_guidance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step", range(1, TOTAL_STEPS + 1))
def test_get_step_guidance_returns_required_keys(step):
    guidance = get_step_guidance(step)
    assert "phase" in guidance
    assert "step_title" in guidance
    assert "actions" in guidance
    assert isinstance(guidance["actions"], list)
    assert len(guidance["actions"]) > 0


@pytest.mark.parametrize("step", range(1, TOTAL_STEPS + 1))
def test_get_step_guidance_phase_is_valid(step):
    guidance = get_step_guidance(step)
    valid_phases = {"UNDERSTANDING", "GENERATION", "VERIFICATION", "REFINEMENT"}
    assert guidance["phase"] in valid_phases


# ---------------------------------------------------------------------------
# format_output
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step", range(1, TOTAL_STEPS + 1))
def test_format_output_produces_step_header(step):
    guidance = get_step_guidance(step)
    output = format_output(step, guidance, "test thoughts")
    assert "<step_header" in output
    assert guidance["phase"] in output
    assert guidance["step_title"] in output


def test_format_output_step1_includes_xml_mandate():
    guidance = get_step_guidance(1)
    output = format_output(1, guidance, "")
    assert "<xml_format_mandate>" in output


def test_format_output_step1_includes_invoke_with_sections_placeholder():
    guidance = get_step_guidance(1)
    output = format_output(1, guidance, "")
    assert "<SELECTED_SECTIONS>" in output


def test_format_output_last_step_shows_complete():
    guidance = get_step_guidance(TOTAL_STEPS)
    output = format_output(TOTAL_STEPS, guidance, "final")
    assert "WORKFLOW COMPLETE" in output


# Asserts TOTAL_STEPS == 9 explicitly; last_step test uses TOTAL_STEPS dynamically. (ref: DL-001)
def test_format_output_step9_shows_complete():
    assert TOTAL_STEPS == 9
    guidance = get_step_guidance(9)
    output = format_output(9, guidance, "final")
    assert "WORKFLOW COMPLETE" in output


def test_format_output_middle_step_includes_invoke_after():
    guidance = get_step_guidance(3)
    # sections_arg stored in guidance dict; format_output reads it from there (ref: DL-001)
    guidance["sections_arg"] = "philosophy,naming"
    output = format_output(3, guidance, "ctx")
    assert "<invoke_after>" in output
    assert "--step 4" in output
    assert "--sections philosophy,naming" in output


def test_format_output_includes_accumulated_thoughts():
    guidance = get_step_guidance(2)
    output = format_output(2, guidance, "my accumulated context")
    assert "<accumulated_thoughts>" in output
    assert "my accumulated context" in output


def test_format_output_empty_thoughts_omits_block():
    guidance = get_step_guidance(2)
    output = format_output(2, guidance, "")
    assert "<accumulated_thoughts>" not in output


# ---------------------------------------------------------------------------
# Section loading
# ---------------------------------------------------------------------------


def test_references_dir_exists():
    assert get_references_dir().is_dir()


def test_load_section_files_returns_tuples():
    nodes = load_section_files(["philosophy"])
    assert len(nodes) == 1
    name, content = nodes[0]
    assert name == "philosophy"
    assert len(content) > 0


def test_load_section_files_multiple():
    nodes = load_section_files(["philosophy", "naming", "types"])
    assert len(nodes) == 3


def test_format_output_with_file_nodes():
    guidance2 = get_step_guidance(2, sections=["philosophy"])
    output = format_output(2, guidance2, "ctx")
    assert "<style_references>" not in output
    assert "<![CDATA[" not in output
    assert "=== philosophy ===" in output
    assert "<current_action>" in output


def test_get_step_guidance_with_sections():
    guidance = get_step_guidance(2, sections=["philosophy"])
    actions_text = "\n".join(str(a) for a in guidance["actions"])
    assert "=== philosophy ===" in actions_text


def test_step2_sections_after_instruction_before_rules():
    """Reference content must appear between opening instruction and rule_selection."""
    guidance = get_step_guidance(2, sections=["philosophy", "naming"])
    actions_text = "\n".join(str(a) for a in guidance["actions"])
    instruction_pos = actions_text.index("Read the style sections below")
    first_section_pos = actions_text.index("=== philosophy ===")
    last_section_pos = actions_text.index("=== naming ===")
    rule_sel_pos = actions_text.index("<rule_selection>")
    assert instruction_pos < first_section_pos < rule_sel_pos
    assert instruction_pos < last_section_pos < rule_sel_pos


def test_history_sentinel_referenced_by_steps():
    # Step 8 excluded: final_checklist step does not accumulate history. (ref: DL-009)
    # Step 9 excluded: quality gate omits context template (leon pattern — LLM has seen it 7x). (ref: iter-8)
    for step_num in [2, 3, 4, 5, 6, 7]:
        actions = STEPS[step_num]["actions"]
        assert _HISTORY_SENTINEL in actions, f"Step {step_num} missing _HISTORY_SENTINEL"


def test_history_template_progressive():
    # Step 2 should NOT contain future-step sections
    t2 = history_template(2)
    assert "Classification" in t2
    assert "Applicable Rules" in t2
    assert "Draft Output" not in t2
    assert "Violations" not in t2

    # Step 5 should contain Structural Metrics (AI voice merged into Violations)
    t5 = history_template(5)
    assert "Structural Metrics" in t5
    assert "AI Voice Issues" not in t5  # merged into Violations section
    assert "Positive Markers" not in t5

    # Step 7 produces Refinements (merged Plan + Log), so it should appear at step 7+
    t7 = history_template(7)
    assert "Refinements" in t7

    # Step 9 should contain everything
    t9 = history_template(9)
    assert "Refinements" in t9


# ---------------------------------------------------------------------------
# Behavioral contracts for quality gate, loop-back, and binding thresholds
# ---------------------------------------------------------------------------
# Step 8 is refinement only; no quality gate. Gate moved to Step 9. (ref: DL-007)
def test_step8_is_refinement_only():
    actions = STEPS[8]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "<refinement_process>" in actions_text
    assert "<final_checklist>" not in actions_text


def test_step8_fix_patterns_cover_step4_detection_patterns():
    """Step 8 must have a fix block for every step 4 detection pattern."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<naming_fix>" in actions_text
    assert "<overengineering_fix>" in actions_text
    assert "<error_handling_fix>" in actions_text
    assert "<comment_fix>" in actions_text
    assert "<structure_fix>" in actions_text


def test_step8_fix_patterns_cover_step5_detection_patterns():
    """Step 8 must have fix blocks for step 5 patterns that need explicit guidance."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    # structural_variance_fix covers pattern_9_structural_variance
    assert "<structural_variance_fix>" in actions_text
    assert "cookie-cutter shape" in actions_text
    # copy_paste_fix covers pattern_12_copy_paste
    assert "<copy_paste_fix>" in actions_text
    assert "extract shared logic" in actions_text


def test_step9_has_code_conventions_section():
    """Step 9 must verify output-level structural conventions (leon STRUCTURE analog)."""
    actions_text = "\n".join(str(a) for a in STEPS[9]["actions"])
    assert "CODE CONVENTIONS" in actions_text
    assert "Module layout follows top-to-bottom convention" in actions_text
    assert "Data-driven dispatch" in actions_text
    assert "Boundary validation only" in actions_text


def test_step4_re_read_references_own_patterns():
    """Step 4 re_read must reference its own WRONG/RIGHT pairs, not Step 2 rules."""
    actions_text = "\n".join(str(a) for a in STEPS[4]["actions"])
    assert "WRONG/RIGHT pairs in each pattern below" in actions_text
    # re_read block itself must not misdirect to Step 2 anti-patterns section
    re_read_start = actions_text.index("<re_read>")
    re_read_end = actions_text.index("</re_read>")
    re_read_block = actions_text[re_read_start:re_read_end]
    assert "Step 2" not in re_read_block


# Step 9 is the full re-verification gate with checklist. (ref: DL-001, DL-008)
def test_step9_has_full_checklist():
    actions = STEPS[9]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "<final_checklist>" in actions_text
    assert "<stopping_criteria>" in actions_text
    assert "ANTI-PATTERNS ABSENT" in actions_text
    assert "POSITIVE PATTERNS PRESENT" in actions_text


def test_step9_checklist_uses_prechecked_boxes():
    """Step 9 uses [x] pre-checked boxes (exception-finding framing)."""
    actions_text = "\n".join(str(a) for a in STEPS[9]["actions"])
    assert "[x] No naming convention violations" in actions_text
    assert "[ ] No naming convention violations" not in actions_text
    assert "All items below are pre-checked [x]" in actions_text


# Step 2 has action framing before rules; step_back moved to Step 3 only to avoid duplication. (ref: DL-002)
def test_step2_has_action_framing():
    actions = STEPS[2]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "Read the style sections below" in actions_text
    assert "<rule_selection>" in actions_text
    assert "<rule_priority>" in actions_text


# Creative priming in Step 3 — step_back_at_generation is the sole meta-cognitive check. (ref: DL-002)
def test_step3_has_creative_priming():
    actions = STEPS[3]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "<stakes>" in actions_text
    assert "<step_back_at_generation>" in actions_text
    assert "terse naming" in actions_text


# Advisory language + advisory Step 8 produces zero consequences for WEAK assessment; test prevents regression to advisory form. (ref: DL-003)
def test_step6_thresholds_are_binding():
    actions = STEPS[6]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "advisory" not in actions_text
    # Verdict requires both checks to pass; FAIL on either
    assert "FAIL" in actions_text
    assert "Both checks must pass" in actions_text


# Step 6 categories carry specific grep-able patterns because Step 6 receives no reference file injection; detection cannot depend on re-injected .md content. (ref: DL-004)
def test_step6_has_specific_marker_patterns():
    actions = STEPS[6]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "ans" in actions_text
    assert "ctx" in actions_text
    assert ("FRAG_OPTS" in actions_text or "registry" in actions_text)
    assert "assert False" in actions_text
    assert "walrus" in actions_text
    assert ("SCREAMING_SNAKE_CASE" in actions_text or "module top" in actions_text)


# Consumer, Purpose, and Code Context feed later steps; omitting them collapses context-appropriate style checking to uniform rules. (ref: DL-004, DL-005)
def test_step1_has_consumer_purpose_context_fields():
    actions = STEPS[1]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "Consumers" in actions_text
    assert "Purpose" in actions_text
    assert "Code Context" in actions_text


# ---------------------------------------------------------------------------
# CLI invocation (subprocess, matches test_workflow_steps pattern)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step", range(1, TOTAL_STEPS + 1))
def test_cli_invocation_succeeds(step):
    """Each step is invocable via CLI without error."""
    cmd = [
        sys.executable, "-m", "skills.alan_coding_style.coding_style",
        "--step", str(step),
        "--thoughts", "test",
    ]
    if step >= 2:
        cmd.extend(["--sections", "philosophy,naming"])
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode == 0, f"Step {step} failed: {result.stderr[:300]}"
    assert "<step_header" in result.stdout
    # Output must not expose implementation details (file paths, CDATA) to agents (ref: DL-003, DL-005)
    assert "<style_references>" not in result.stdout
    assert "<![CDATA[" not in result.stdout
    if step == 2:
        assert "=== philosophy ===" in result.stdout or "=== naming ===" in result.stdout
    # Steps > 2 must not receive section content — inject-once behavior; section presence indicates regression. (ref: DL-001)
    if step > 2:
        assert "=== philosophy ===" not in result.stdout
        assert "=== naming ===" not in result.stdout


def test_cli_rejects_step_zero():
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_coding_style.coding_style",
         "--step", "0", "--thoughts", "x"],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode != 0


def test_cli_overflow_step_produces_additional_refinement():
    """Steps beyond TOTAL_STEPS produce overflow refinement output."""
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_coding_style.coding_style",
         "--step", str(TOTAL_STEPS + 1), "--thoughts", "x"],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode == 0
    assert "Additional Refinement" in result.stdout
    assert "WORKFLOW COMPLETE" in result.stdout


def test_overflow_step_focus_varies_by_step():
    """First overflow step focuses on HIGH; second on MED; third+ on diminishing returns."""
    from skills.alan_coding_style.coding_style import _overflow_step
    first = _overflow_step(TOTAL_STEPS + 1)
    first_text = "\n".join(str(a) for a in first["actions"])
    assert "Focus on HIGH-confidence" in first_text
    assert "Re-run the Step 9 checklist" in first_text

    second = _overflow_step(TOTAL_STEPS + 2)
    second_text = "\n".join(str(a) for a in second["actions"])
    assert "MED-confidence" in second_text
    assert "Focus on HIGH-confidence" not in second_text

    third = _overflow_step(TOTAL_STEPS + 3)
    third_text = "\n".join(str(a) for a in third["actions"])
    assert "diminishing returns" in third_text
    assert "MED-confidence" not in third_text


def test_step9_checklist_cross_references_patterns():
    """Step 9 checklist items reference their source detection patterns."""
    step9 = STEPS[9]
    text = "\n".join(str(a) for a in step9["actions"])
    # Anti-patterns reference Step 4 patterns
    assert "pattern_1_naming" in text
    assert "pattern_2_overengineering" in text
    assert "pattern_3_error_handling" in text
    assert "pattern_5_structure" in text
    # AI voice references Step 5 patterns
    assert "pattern_6_formula" in text
    assert "pattern_7_naming_register" in text
    assert "pattern_10_narrating_docstrings" in text
    # Positive patterns reference Step 6 categories
    assert "Step 6 category 1" in text
    assert "Step 6 category 2" in text


def test_history_template_includes_structural_metrics():
    """Context accumulation includes structural metrics from step 5 onward."""
    # Step 4: no structural metrics yet
    h4 = history_template(4)
    assert "Structural Metrics" not in h4
    # Step 5: structural metrics available (compact form — header only)
    h5 = history_template(5)
    assert "Structural Metrics" in h5


def test_cli_step1_includes_selected_sections_placeholder():
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_coding_style.coding_style",
         "--step", "1", "--thoughts", ""],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode == 0
    assert "<SELECTED_SECTIONS>" in result.stdout
    assert "<style_references>" not in result.stdout


def test_step9_checklist_covers_all_step5_patterns():
    """Step 9 checklist must reference all 13 step 5 AI voice patterns."""
    step9 = STEPS[9]
    text = "\n".join(str(a) for a in step9["actions"])
    # Code-structural patterns (individual items)
    for pat in ["pattern_6", "pattern_7", "pattern_9", "pattern_10", "pattern_13"]:
        assert pat in text, f"missing individual checklist item for {pat}"
    # Text-level AI tells (grouped item covering patterns 1-5, 8)
    assert "patterns 1-5, 8" in text, "missing grouped text-level AI tells item"
    # Code-level uniformity (grouped item covering patterns 11, 12)
    assert "patterns 11, 12" in text, "missing grouped code-level uniformity item"


def test_step2_has_forward_context_schema():
    """Step 2 shows full context schema preview for all future steps."""
    step2 = STEPS[2]
    text = "\n".join(str(a) for a in step2["actions"])
    assert "context_schema_preview" in text
    # Preview must include all major sections from future steps
    for section in ["Violations", "Structural Metrics",
                     "Positive Markers", "Refinements"]:
        assert section in text, f"forward schema missing '{section}'"
    # AI Voice Issues merged into Violations — should NOT appear separately
    assert "AI Voice Issues" not in text


def test_history_template_includes_refinements():
    """Context accumulation includes merged Refinements section from step 7 onward."""
    h6 = history_template(6)
    assert "Refinements" not in h6
    # Step 7: Refinements section (merged Plan + Log) available
    h7 = history_template(7)
    assert "Refinements" in h7
    assert "Pattern Fixed" in h7


def test_step8_has_defensive_code_fix():
    """Step 8 must have fix guidance for step 5 pattern_13 (defensive code)."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<defensive_code_fix>" in actions_text
    assert "trust the caller" in actions_text


def test_step8_has_vague_message_fix():
    """Step 8 must have fix guidance for step 5 pattern_8 (vague error messages)."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<vague_message_fix>" in actions_text
    assert "expected int" in actions_text


def test_context_template_no_separate_ai_voice_section():
    """AI voice issues must be merged into Violations, not a separate section."""
    for step in range(1, 16):
        template = history_template(step)
        assert "AI Voice Issues" not in template, f"Step {step} still has separate AI Voice Issues"


def test_step9_omits_context_accumulation():
    """Step 9 quality gate has no context template — LLM has seen it 7 times already."""
    actions = STEPS[9]["actions"]
    assert _HISTORY_SENTINEL not in actions
    actions_text = "\n".join(str(a) for a in actions)
    assert "CONTEXT ACCUMULATION" not in actions_text


def test_step1_section_selection_compact():
    """Step 1 section_selection uses compact format without redundant ALL AVAILABLE list."""
    actions_text = "\n".join(str(a) for a in STEPS[1]["actions"])
    assert "section_selection" in actions_text
    assert "GENERATE:" in actions_text
    assert "REVIEW:" in actions_text
    # Compact: no separate ALWAYS INCLUDE heading or ALL AVAILABLE section
    assert "ALWAYS INCLUDE:" not in actions_text
    assert "ALL AVAILABLE:" not in actions_text


def test_history_template_compact_format():
    """Context template uses compact section headers without table examples for already-created sections."""
    h8 = history_template(8)
    # Classification should NOT have example value rows (LLM created it in step 1)
    assert "generate/review/refactor/fix" not in h8
    assert "Language(s)" not in h8
    # Draft Output should NOT have description text
    assert "Code or analysis notes" not in h8
    # Refinements merged (no separate Plan/Log)
    assert "Refinement Plan" not in h8
    assert "Refinement Log" not in h8
    assert "Refinements" in h8


def test_step3_step_back_before_apply_rules():
    """step_back_at_generation must appear before apply_rules in step 3 actions."""
    actions = STEPS[3]["actions"]
    actions_text = [str(a) for a in actions]
    step_back_idx = None
    apply_rules_idx = None
    for i, a in enumerate(actions_text):
        if "<step_back_at_generation>" in a and step_back_idx is None:
            step_back_idx = i
        if "<apply_rules>" in a and apply_rules_idx is None:
            apply_rules_idx = i
    assert step_back_idx is not None, "step_back_at_generation missing from step 3"
    assert apply_rules_idx is not None, "apply_rules missing from step 3"
    assert step_back_idx < apply_rules_idx, (
        f"step_back_at_generation (index {step_back_idx}) must come before "
        f"apply_rules (index {apply_rules_idx})"
    )


def test_step5_has_pattern_tally():
    """Step 5 must include running tally instruction matching step 4's format."""
    actions_text = "\n".join(str(a) for a in STEPS[5]["actions"])
    assert "Patterns completed: N/13" in actions_text
    assert "Violations found: M" in actions_text


def test_step2_context_schema_has_field_templates():
    """Step 2 context_schema_preview must include field templates, not just section names."""
    actions_text = "\n".join(str(a) for a in STEPS[2]["actions"])
    # Field templates should show expected table formats
    assert "| Aspect | Value |" in actions_text
    assert "| Category | Rule | Source Section |" in actions_text
    assert "| Location | Pattern | Code | Confidence |" in actions_text
    assert "| Category | Count | Examples |" in actions_text


def test_step8_has_positive_pattern_fix():
    """Step 8 must have fix guidance for adding missing positive patterns (leon marker_fix equivalent)."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<positive_pattern_fix>" in actions_text
    # Must show concrete BEFORE/AFTER for key positive patterns
    assert "ans = compute" in actions_text
    assert "HANDLERS" in actions_text
    assert "assert items" in actions_text


def test_step8_has_code_prose_fix():
    """Step 8 must have fix guidance for text-level AI tells in code (patterns 1-5)."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<code_prose_fix>" in actions_text
    # Covers tricolons, dead metaphors, hollow emphasis, contrarian openers in code context
    assert "Tricolons in docstrings" in actions_text
    assert "Dead metaphors in comments" in actions_text
    assert "Hollow emphasis in error messages" in actions_text


def test_step6_has_category_tally():
    """Step 6 must include running tally instruction matching steps 4-5 format."""
    actions_text = "\n".join(str(a) for a in STEPS[6]["actions"])
    assert "Categories completed: N/5" in actions_text
    assert "Markers found: M" in actions_text


def test_step8_has_line_complexity_fix():
    """Step 8 must have fix guidance for pattern_11 (line complexity variance)."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<line_complexity_fix>" in actions_text
    # Must show BEFORE/AFTER for inlining pipelines and simplifying conditionals
    assert "return format(process(get_a()))" in actions_text
    assert "x = cond" in actions_text


def test_step7_cross_check_has_task_output_alignment():
    """Step 7 cross_check must verify output format matches task type from Step 1."""
    actions_text = "\n".join(str(a) for a in STEPS[7]["actions"])
    assert "output format match the task type" in actions_text
    # Must list all 4 task types with expected output format
    assert "GENERATE:" in actions_text
    assert "REVIEW:" in actions_text
    assert "REFACTOR:" in actions_text
    assert "FIX:" in actions_text
