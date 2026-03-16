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
    HISTORY_TEMPLATE,
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


def test_history_template_referenced_by_steps():
    # Step 8 excluded: final_checklist step does not accumulate history. (ref: DL-009)
    for step_num in [2, 3, 4, 5, 6, 7, 9]:
        actions = STEPS[step_num]["actions"]
        assert HISTORY_TEMPLATE in actions, f"Step {step_num} missing HISTORY_TEMPLATE"


# ---------------------------------------------------------------------------
# Behavioral contracts for quality gate, loop-back, and binding thresholds
# ---------------------------------------------------------------------------
def test_step8_triggers_loopback():
    actions = STEPS[8]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "increase total_steps" in actions_text
    assert "Note remaining issues" not in actions_text


# Step 9 must contain both conditions so the gate enforces a real decision, not a checklist acknowledgment. (ref: DL-001, DL-008)
def test_step9_has_stopping_criteria():
    actions = STEPS[9]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "<stopping_criteria>" in actions_text
    assert "STOP" in actions_text
    assert "CONTINUE" in actions_text


# Procedural list answers the question before it is asked, defeating meta-cognitive priming; test locks this invariant. (ref: DL-002)
def test_step2_step_back_has_meta_cognitive_questions():
    actions = STEPS[2]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "What makes Alan" in actions_text
    assert "LLM-generated" in actions_text
    assert "The applicable style guide sections are embedded below" not in actions_text


# Creative priming blocks prime the agent with identity and stakes before rule application; absence cascades into weakly-styled generation output. (ref: DL-002)
def test_step3_has_creative_priming():
    actions = STEPS[3]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "<stakes>" in actions_text
    assert "<core_coding_voice>" in actions_text
    assert "<step_back_at_generation>" in actions_text


# Advisory language + advisory Step 8 produces zero consequences for WEAK assessment; test prevents regression to advisory form. (ref: DL-003)
def test_step6_thresholds_are_binding():
    actions = STEPS[6]["actions"]
    actions_text = "\n".join(str(a) for a in actions)
    assert "advisory" not in actions_text
    assert "PASS" in actions_text
    assert "FAIL" in actions_text


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


def test_cli_rejects_step_beyond_max():
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_coding_style.coding_style",
         "--step", str(TOTAL_STEPS + 1), "--thoughts", "x"],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode != 0


def test_cli_step1_includes_selected_sections_placeholder():
    result = subprocess.run(
        [sys.executable, "-m", "skills.alan_coding_style.coding_style",
         "--step", "1", "--thoughts", ""],
        capture_output=True, text=True, timeout=10, cwd=SCRIPTS_DIR,
    )
    assert result.returncode == 0
    assert "<SELECTED_SECTIONS>" in result.stdout
    assert "<style_references>" not in result.stdout
