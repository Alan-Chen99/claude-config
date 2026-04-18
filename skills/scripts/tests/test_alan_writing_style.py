"""Tests for alan_writing_style skill.

Covers: WORKFLOW construction, format_output for all steps, CLI invocation,
history template progression, and behavioral contracts for the quality gate.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from skills.alan_writing_style.writing_style import (
    STEPS,
    TOTAL_STEPS,
    WORKFLOW,
    _HISTORY_SENTINEL,
    history_template,
    format_output,
    get_step_guidance,
)
from skills.lib.workflow.core import Workflow


SCRIPTS_DIR = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# WORKFLOW construction
# ---------------------------------------------------------------------------


def test_workflow_is_workflow_instance():
    assert isinstance(WORKFLOW, Workflow)


def test_workflow_name():
    assert WORKFLOW.name == "alan-writing-style"


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
    valid_phases = {"UNDERSTANDING", "DRAFTING", "VERIFICATION", "REFINEMENT"}
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


def test_format_output_last_step_shows_complete():
    guidance = get_step_guidance(TOTAL_STEPS)
    output = format_output(TOTAL_STEPS, guidance, "final")
    assert "WORKFLOW COMPLETE" in output


def test_format_output_step9_shows_complete():
    assert TOTAL_STEPS == 9
    guidance = get_step_guidance(9)
    output = format_output(9, guidance, "final")
    assert "WORKFLOW COMPLETE" in output


def test_format_output_middle_step_includes_invoke_after():
    guidance = get_step_guidance(3)
    output = format_output(3, guidance, "ctx")
    assert "<invoke_after>" in output
    assert "--step 4" in output


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
# History template
# ---------------------------------------------------------------------------


def test_history_sentinel_referenced_by_steps():
    # Steps 2-8 use sentinel; step 1 and 9 do not
    for step_num in [2, 3, 4, 5, 6, 7, 8]:
        actions = STEPS[step_num]["actions"]
        assert _HISTORY_SENTINEL in actions, f"Step {step_num} missing _HISTORY_SENTINEL"


def test_step1_omits_history_sentinel():
    actions = STEPS[1]["actions"]
    assert _HISTORY_SENTINEL not in actions


def test_history_template_progressive():
    # Step 2: Classification and Purpose, but not later sections
    t2 = history_template(2)
    assert "Classification" in t2
    assert "Purpose" in t2
    assert "Draft" not in t2
    assert "Violations" not in t2

    # Step 3: adds Draft
    t3 = history_template(3)
    assert "Draft" in t3
    assert "Violations" not in t3

    # Step 4: adds Violations and Structural Metrics
    t4 = history_template(4)
    assert "Violations" in t4
    assert "Structural Metrics" in t4
    assert "Positive Markers" not in t4

    # Step 5: adds Positive Markers
    t5 = history_template(5)
    assert "Positive Markers" in t5
    assert "Refinements" not in t5

    # Step 8: adds Refinements
    t8 = history_template(8)
    assert "Refinements" in t8


def test_step9_omits_context_accumulation():
    """Step 9 quality gate has no context template -- LLM has seen it enough times."""
    actions = STEPS[9]["actions"]
    assert _HISTORY_SENTINEL not in actions
    actions_text = "\n".join(str(a) for a in actions)
    assert "CONTEXT ACCUMULATION" not in actions_text


# ---------------------------------------------------------------------------
# Behavioral contracts
# ---------------------------------------------------------------------------


def test_step3_has_creative_priming():
    actions_text = "\n".join(str(a) for a in STEPS[3]["actions"])
    assert "<stakes>" in actions_text
    assert "<step_back_principles>" in actions_text


def test_step4_has_ai_tells_patterns():
    actions_text = "\n".join(str(a) for a in STEPS[4]["actions"])
    assert "<pattern_1_tricolons>" in actions_text
    assert "<pattern_2_contrarian>" in actions_text
    assert "<pattern_3_metaphors>" in actions_text
    assert "<pattern_4_emphasis>" in actions_text
    assert "<pattern_5_callbacks>" in actions_text
    assert "<pattern_6_formula>" in actions_text
    assert "<pattern_7_mixed_register>" in actions_text
    assert "<pattern_8_euphemism>" in actions_text
    assert "<pattern_9_structural_variance>" in actions_text
    assert "<pattern_10_grounded_openers>" in actions_text
    assert "<pattern_11_sentence_rhythm>" in actions_text
    assert "<pattern_12_repetition>" in actions_text
    assert "<pattern_13_overjustification>" in actions_text


def test_step5_has_positive_markers():
    actions_text = "\n".join(str(a) for a in STEPS[5]["actions"])
    assert "<positive_markers>" in actions_text
    assert "<sufficiency_check>" in actions_text
    assert "VERDICT" in actions_text


def test_step6_has_voice_checks():
    actions_text = "\n".join(str(a) for a in STEPS[6]["actions"])
    assert "<narrative_check>" in actions_text
    assert "<instructional_check>" in actions_text
    assert "<reference_check>" in actions_text
    assert "<hybrid_boundary_check>" in actions_text


def test_step7_has_consolidation():
    actions_text = "\n".join(str(a) for a in STEPS[7]["actions"])
    assert "<consolidation>" in actions_text
    assert "<cross_check>" in actions_text
    assert "<refinement_plan>" in actions_text


def test_step8_has_refinement_fixes():
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<tricolon_fix>" in actions_text
    assert "<metaphor_fix>" in actions_text
    assert "<emphasis_fix>" in actions_text
    assert "<voice_fix>" in actions_text
    assert "<rhythm_fix>" in actions_text
    assert "<marker_fix>" in actions_text
    assert "<opener_fix>" in actions_text
    assert "<variance_fix>" in actions_text


def test_step8_is_refinement_only():
    """Step 8 is refinement; quality gate is in step 9."""
    actions_text = "\n".join(str(a) for a in STEPS[8]["actions"])
    assert "<refinement_process>" in actions_text
    assert "<final_checklist>" not in actions_text


def test_step9_has_full_checklist():
    actions_text = "\n".join(str(a) for a in STEPS[9]["actions"])
    assert "<final_checklist>" in actions_text
    assert "<stopping_criteria>" in actions_text
    assert "AI TELLS ABSENT" in actions_text
    assert "ALAN'S VOICE PRESENT" in actions_text
    assert "VOICE" in actions_text
    assert "STRUCTURE" in actions_text


def test_step9_checklist_uses_prechecked_boxes():
    """Step 9 uses [x] pre-checked boxes (exception-finding framing)."""
    actions_text = "\n".join(str(a) for a in STEPS[9]["actions"])
    assert "[x] No tricolons" in actions_text
    assert "All items below are pre-checked [x]" in actions_text


# ---------------------------------------------------------------------------
# CLI invocation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("step", range(1, TOTAL_STEPS + 1))
def test_cli_invocation_succeeds(step):
    """Each step is invocable via CLI without error."""
    cmd = [
        sys.executable, "-m", "skills.alan_writing_style.writing_style",
        "--step", str(step),
        "--thoughts", "test",
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode == 0, f"Step {step} failed: {result.stderr[:300]}"
    assert "<step_header" in result.stdout


def test_cli_rejects_step_zero():
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_writing_style.writing_style",
         "--step", "0", "--thoughts", "x"],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode != 0


def test_cli_overflow_step_produces_additional_refinement():
    """Steps beyond TOTAL_STEPS produce overflow refinement output."""
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_writing_style.writing_style",
         "--step", str(TOTAL_STEPS + 1), "--thoughts", "x"],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode == 0
    assert "Additional Refinement" in result.stdout
    assert "WORKFLOW COMPLETE" in result.stdout


def test_overflow_step_focus_varies_by_step():
    """First overflow step focuses on HIGH; second on MED; third+ on diminishing returns."""
    from skills.alan_writing_style.writing_style import _overflow_step
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
