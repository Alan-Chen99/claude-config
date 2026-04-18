#!/usr/bin/env python3
"""
Alan Writing Style - Multi-turn prompt injection for style compliance.

Grounded in:
- Plan-and-Solve (Wang et al., 2023) - classification before writing
- Step-Back Prompting (Zheng et al., 2023) - principle retrieval before drafting
- RE2 Re-Reading (Xu et al., 2023) - re-read before verification
- Chain-of-Verification (Dhuliawala et al., 2023) - factored style checking
- Factor+Revise (Dhuliawala et al., 2023) - explicit cross-check before refinement
- Self-Refine (Madaan et al., 2023) - iterative improvement with contrastive feedback
- Metacognitive Prompting (Wang & Zhao, 2024) - confidence assessment
"""

import argparse
import sys
from pathlib import Path

from skills.lib.workflow.core import (
    StepDef,
    Workflow,
)
from skills.lib.workflow.ast import W, XMLRenderer, render
from skills.lib.workflow.ast.nodes import (
    TextNode, StepHeaderNode, CurrentActionNode, InvokeAfterNode,
)
from skills.lib.workflow.ast.renderer import (
    render_step_header, render_current_action, render_invoke_after,
)


TOTAL_STEPS = 9

# Injected at step 1 only; instructs executing agents to follow XML protocol.
XML_FORMAT_MANDATE = """<xml_format_mandate>
CRITICAL: All script outputs use XML format. You MUST:
1. Execute the action in <current_action>
2. When complete, invoke the exact command in <invoke_after>
3. DO NOT modify commands. DO NOT skip steps.
</xml_format_mandate>"""

SECTION_TO_FILE = {
    "content-types": "content-types.md",
    "voice": "voice.md",
    "ai-tells": "ai-tells.md",
    "ai-tells-examples": "ai-tells-examples.md",
    "positive-markers": "positive-markers.md",
    "voice-alignment": "voice-alignment.md",
    "fixes": "fixes.md",
}


def get_references_dir() -> Path:
    # scripts/skills/alan_writing_style/ -> scripts/skills/ -> scripts/ -> skills/
    return Path(__file__).parent.parent.parent.parent / "alan-writing-style" / "references"


def load_section_files(sections: list[str]) -> list[tuple[str, str]]:
    """Load reference markdown files for the given section names.

    Isolated from format_output so file I/O stays separate from output
    formatting. Returns (section_name, file_content) pairs. Exits on
    unknown section name or missing file.
    """
    refs_dir = get_references_dir()
    result = []
    for sec in sections:
        if sec not in SECTION_TO_FILE:
            valid = ", ".join(sorted(SECTION_TO_FILE.keys()))
            sys.exit(f"ERROR: Unknown section '{sec}'. Valid: {valid}")
        rel_path = SECTION_TO_FILE[sec]
        full_path = refs_dir / rel_path
        if not full_path.exists():
            sys.exit(f"ERROR: Section file not found: {full_path}")
        content = full_path.read_text()
        result.append((sec, content))
    return result


# Sentinel replaced with HISTORY_TEMPLATE in get_step_guidance.
_HISTORY_SENTINEL = "_HISTORY_"

# Sentinel prefix for reference file injection in get_step_guidance.
_SECTION_PREFIX = "_SECTION:"


def _section(name: str) -> str:
    """Sentinel for reference file injection in get_step_guidance."""
    return f"{_SECTION_PREFIX}{name}"


# Flat history template matching leon_writing_style output format.
HISTORY_TEMPLATE = """
CONTEXT ACCUMULATION: Your --thoughts MUST include:

  ## Classification (from Step 1)
  | Section | Content Type | Voice |

  ## Purpose (from Step 2)
  Core message: [one sentence]
  Reference register: [philosophical / pop culture / technical / none]

  ## Violations (from Steps 4-6)
  | Location | Pattern | Quoted Text | Confidence |

  ## Positive Markers (from Step 5)
  | Category | Count | Examples |
  Verdict: PASS/FAIL (found N, required M)

  ## Structural Metrics (from Step 4)
  Paragraph range: X-Y sentences
  Sentence length mix: X% short, Y% medium, Z% long
  Opener type: grounded / meta-commentary

  ## Refinements (from Step 8+)
  | Original | Revised |
"""


STEPS = {
    1: {
        "id": "content_classification",
        "phase": "UNDERSTANDING",
        "step_title": "Content Classification",
        "actions": [
            "Before writing, classify your content. Voice rules depend on this.",
            "",
            _section("content-types"),
            "",
            "<classification_output>",
            "Map your content to types:",
            "",
            "  | Section/Topic | Content Type | Voice |",
            "  |---------------|--------------|-------|",
            "  | Introduction  | narrative    | first-person |",
            "  | Usage         | instructional| imperative |",
            "  | ...           | ...          | ... |",
            "",
            "This table guides voice selection in later steps.",
            "</classification_output>",
        ],
        "next_desc": "Define purpose and audience.",
    },
    2: {
        "id": "purpose_audience",
        "phase": "UNDERSTANDING",
        "step_title": "Purpose & Audience",
        "actions": [
            "Define the content's purpose and target audience.",
            "",
            "<audience_analysis>",
            "WHO is the reader?",
            "  - Technical level: expert / intermediate / beginner",
            "  - What do they already know?",
            "  - What confusion might they bring?",
            "</audience_analysis>",
            "",
            "<purpose_analysis>",
            "WHY does this content exist?",
            "  - What should change after reading? (knowledge, action, belief)",
            "  - What is the SINGLE most important message?",
            "  - What action should the reader take?",
            "",
            "Alan's writing always has a clear throughline.",
            "If you cannot state the core message in one sentence, clarify before drafting.",
            "</purpose_analysis>",
            "",
            "<hook_draft>",
            "Draft your opening hook now:",
            "  - State the problem and why it matters",
            "  - Use first-person if narrative ('I was writing an application that...')",
            "  - Be specific, not abstract (name projects, technologies, constraints)",
            "</hook_draft>",
            "",
            "<reference_register>",
            "OPTIONAL: Will this document use quotes, anecdotes, or cultural references?",
            "",
            "  If YES, choose ONE register and commit:",
            "    - Philosophical (Seneca, military history, wisdom traditions)",
            "    - Pop culture (TV, films, memes, irreverent commentary)",
            "    - Technical (papers, specifications, industry sources)",
            "",
            "  If NO, proceed without references. This is a valid choice.",
            "",
            "  CRITICAL: Do not mix registers. Pick one or none.",
            "</reference_register>",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Draft with style rules.",
    },
    3: {
        "id": "draft_with_style",
        "phase": "DRAFTING",
        "step_title": "Draft with Style Rules",
        "actions": [
            "<step_back_principles>",
            "Before writing, answer these questions:",
            "",
            "  1. What makes Alan's voice distinctive from generic technical writing?",
            "     (First-person authority, specific examples, definitive conclusions)",
            "",
            "  2. What is the ONE thing that would make this sound AI-generated?",
            "     (Tricolons, dead metaphors, hollow emphasis, balanced structure)",
            "",
            "Keep these answers in mind as you draft.",
            "</step_back_principles>",
            "",
            "<stakes>",
            "This content represents Alan's public voice. Quality matters.",
            "Readers will judge Alan's expertise by this writing.",
            "</stakes>",
            "",
            _section("voice"),
            "",
            "Write your draft now. Verification follows in the next steps.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Check for AI tells.",
    },
    4: {
        "id": "ai_tells_detection",
        "phase": "VERIFICATION",
        "step_title": "AI Tells Detection",
        "actions": [
            _section("ai-tells-examples"),
            "",
            "<re_read>",
            "Read your draft again, slowly, sentence by sentence.",
            "Then check for AI-generated patterns.",
            "</re_read>",
            "",
            "VERIFICATION METHOD: Extract first, then judge.",
            "For each pattern: (1) extract candidates, (2) assess each.",
            "",
            _section("ai-tells"),
            "",
            "OUTPUT: Violation table with quoted text and confidence per pattern.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Check for positive voice markers.",
    },
    5: {
        "id": "positive_marker_check",
        "phase": "VERIFICATION",
        "step_title": "Positive Voice Marker Check",
        "actions": [
            _section("positive-markers"),
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Verify voice-content alignment.",
    },
    6: {
        "id": "voice_content_alignment",
        "phase": "VERIFICATION",
        "step_title": "Voice-Content Alignment",
        "actions": [
            "<re_read>",
            "Read your draft again with your Step 1 classification table visible.",
            "For each section, verify voice matches content type.",
            "</re_read>",
            "",
            "VERIFICATION METHOD: Extract voice markers, then compare to expected.",
            "",
            _section("voice-alignment"),
            "",
            "OUTPUT: Section-by-section compliance with violations table.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Consolidate violations for refinement.",
    },
    7: {
        "id": "cross_check_consolidation",
        "phase": "VERIFICATION",
        "step_title": "Cross-Check Consolidation",
        "actions": [
            "Consolidate ALL violations from Steps 4-6 before refinement.",
            "Include both negative pattern violations AND missing positive markers.",
            "",
            "<consolidation>",
            "Create a single violation table:",
            "",
            "  | # | Location | Pattern | Quoted Text | Confidence | Priority |",
            "  |---|----------|---------|-------------|------------|----------|",
            "  | 1 | Para 2   | Tricolon| '...'       | HIGH       | Fix first|",
            "  | 2 | Intro    | Passive | '...'       | HIGH       | Fix first|",
            "  | 3 | Global   | Missing markers | 0 found, 2 required | HIGH | Fix first|",
            "  | 4 | Opener   | Meta-commentary | 'Here is how...' | HIGH | Fix first|",
            "  | 5 | Usage    | 1st-person| '...'     | MED        | Fix after|",
            "",
            "PRIORITY RULES:",
            "  - Missing voice markers: Fix first (most impactful)",
            "  - Meta-commentary openers: Fix first (immediate AI tell)",
            "  - HIGH confidence violations: Fix before MED/LOW",
            "  - Voice mismatches: Fix before minor style issues",
            "  - Structural monotony: Fix by varying paragraph lengths",
            "</consolidation>",
            "",
            "<cross_check>",
            "Review the consolidated list:",
            "",
            "  1. Are any violations duplicates? (Same text, different patterns)",
            "     -> Merge into single entry, note both patterns.",
            "",
            "  2. Do any violations conflict? (Fixing one creates another)",
            "     -> Note the conflict, decide which takes precedence.",
            "",
            "  3. Are any LOW confidence violations actually false positives?",
            "     -> Re-examine the quote. Remove if not a real violation.",
            "",
            "  4. Are any sections violation-free? (Confirm explicitly)",
            "     -> Note: 'Section X: No violations found.'",
            "</cross_check>",
            "",
            "<refinement_plan>",
            "Create a refinement order:",
            "",
            "  Fix #1: [violation] -> [planned fix approach]",
            "  Fix #2: [violation] -> [planned fix approach]",
            "  ...",
            "",
            "This plan guides the next step.",
            "</refinement_plan>",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Apply refinements.",
    },
    8: {
        "id": "self_refine",
        "phase": "REFINEMENT",
        "step_title": "Self-Refine",
        "actions": [
            "Apply refinements from your Step 7 plan.",
            "",
            "<refinement_process>",
            "FOR EACH VIOLATION in priority order:",
            "  1. Quote the original text",
            "  2. State the pattern violated",
            "  3. Write the revised text",
            "  4. Verify the fix doesn't introduce new violations",
            "</refinement_process>",
            "",
            _section("fixes"),
            "",
            "<refinement_log>",
            "Record each change:",
            "",
            "  | # | Original | Revised | Pattern Fixed |",
            "  |---|----------|---------|---------------|",
            "",
            "This log goes in your --thoughts for the next step.",
            "</refinement_log>",
            "",
            "OUTPUT: Revised draft with refinement log.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Final quality check.",
    },
    9: {
        "id": "final_quality_check",
        "phase": "REFINEMENT",
        "step_title": "Final Quality Check",
        "actions": [
            "FINAL VERIFICATION before completion.",
            "",
            "<stopping_criteria>",
            "STOP (workflow complete) when ALL are true:",
            "  - Zero HIGH-confidence violations remain",
            "  - Voice matches content type for every section",
            "  - No tricolons, dead metaphors, or hollow emphasis",
            "  - Positive marker threshold met (Step 5 verdict: PASS)",
            "  - Grounded opener (no meta-commentary)",
            "  - Structural variance present",
            "",
            "CONTINUE (increase total_steps) if ANY are true:",
            "  - Any HIGH-confidence violation remains",
            "  - Voice mismatch in any section",
            "  - Positive markers below threshold",
            "  - Meta-commentary opener still present",
            "  - Rhythm still feels formulaic",
            "</stopping_criteria>",
            "",
            "<final_checklist>",
            "AI TELLS ABSENT (must all be true):",
            "  [x] No tricolons or rhythmic parallelism",
            "  [x] No contrarian openers ('X isn't Y -- it's Z')",
            "  [x] No dead metaphors (flawed foundation, landscape, etc.)",
            "  [x] No hollow emphasis ('This is important')",
            "  [x] No explicit callbacks ('just like', 'as mentioned')",
            "  [x] No mixed register (if references used, all from one category)",
            "  [x] No euphemistic organizational language",
            "  [x] No meta-commentary openers ('Here is how...', 'This section...')",
            "",
            "ALAN'S VOICE PRESENT (must all be true for narrative content):",
            "  [x] At least one signature transition ('So,', 'Now,', 'However,')",
            "  [x] At least one short punchy sentence (<8 words)",
            "  [x] Structural variance (not all paragraphs 2-4 sentences)",
            "  [x] Grounded opener (names project/technology/problem, not meta)",
            "  [x] Mix of sentence lengths (short + medium + long)",
            "  [x] At least one question or parenthetical aside",
            "",
            "VOICE (must all be true):",
            "  [x] Narrative sections use first-person",
            "  [x] Instructional sections use imperative",
            "  [x] Reference sections use third-person",
            "  [x] Voice shifts cleanly at section boundaries",
            "  [x] Uncomfortable truths stated plainly, not hedged",
            "",
            "STRUCTURE (must all be true):",
            "  [x] Conclusions stated first, then supported",
            "  [x] Specific examples, not abstract descriptions",
            "  [x] Natural transitions ('So,', 'However,', 'Now,')",
            "  [x] No 'In conclusion' or 'Moving on to'",
            "  [x] Hook states problem and why it matters",
            "</final_checklist>",
            "",
            "If any checkbox would be [ ] instead of [x]: increase total_steps.",
            "",
            "Otherwise: draft complete. Deliver final content.",
        ],
        "next_desc": "WORKFLOW COMPLETE - deliver final content.",
    },
}


def _overflow_step(step: int) -> dict:
    """Additional refinement for steps beyond TOTAL_STEPS.

    Focus varies by step to prevent re-checking already-fixed items.
    """
    if step == TOTAL_STEPS + 1:
        focus = [
            "Focus on HIGH-confidence violations first.",
            "Re-run the Step 9 checklist after each fix.",
            "When all HIGH-confidence violations are addressed,",
            "deliver final content or invoke step {} for remaining MED-confidence items.".format(step + 1),
        ]
    elif step == TOTAL_STEPS + 2:
        focus = [
            "HIGH-confidence violations should be resolved by now.",
            "Focus on remaining MED-confidence violations and final polish.",
            "Apply voice consistency and positive marker checks.",
            "When satisfied, deliver final content.",
        ]
    else:
        focus = [
            "Refinement has diminishing returns at this point.",
            "Remaining violations are likely LOW-confidence or false positives.",
            "Review critically -- do not make changes unless clearly wrong.",
            "Deliver final content.",
        ]
    return {
        "id": "additional_refinement",
        "phase": "REFINEMENT",
        "step_title": "Additional Refinement",
        "actions": [
            "Continue addressing remaining issues.",
            "",
            "<additional_refinement>",
            "Review your --thoughts for outstanding violations.",
            "Apply refinement rules from Step 8.",
            "",
            *focus,
            "</additional_refinement>",
            "",
            HISTORY_TEMPLATE,
        ],
        "next_desc": "WORKFLOW COMPLETE - deliver final content.",
    }


def get_step_guidance(step: int) -> dict:
    """Return step-specific guidance dict for the given step.

    Expands _HISTORY_SENTINEL to HISTORY_TEMPLATE and _SECTION: sentinels
    to loaded reference file content. Steps beyond TOTAL_STEPS produce
    overflow refinement steps.
    """
    step_data = STEPS.get(step)
    if not step_data:
        if step > TOTAL_STEPS:
            step_data = _overflow_step(step)
        else:
            return {
                "phase": "UNKNOWN",
                "step_title": "Unknown Step",
                "actions": ["ERROR: Invalid step number."],
                "next": "COMPLETE",
            }
    phase = step_data["phase"]
    next_step = step + 1 if step < TOTAL_STEPS else None
    next_text = f"Step {next_step}: {step_data['next_desc']}" if next_step else step_data["next_desc"]
    actions = list(step_data["actions"])

    # Expand sentinels: history template and section references
    expanded = []
    for item in actions:
        if item == _HISTORY_SENTINEL:
            expanded.append(HISTORY_TEMPLATE)
        elif isinstance(item, str) and item.startswith(_SECTION_PREFIX):
            name = item[len(_SECTION_PREFIX):]
            loaded = load_section_files([name])
            content = loaded[0][1].rstrip("\n")
            expanded.extend(content.split("\n"))
        else:
            expanded.append(item)
    actions = expanded

    return {
        "phase": phase,
        "step_title": step_data["step_title"],
        "actions": actions,
        "next": next_text,
    }


def format_output(step: int, guidance: dict, thoughts: str) -> str:
    """Render step output as XML using the AST builder API."""
    parts = []
    is_complete = step >= WORKFLOW.total_steps

    title = f"WRITING STYLE - {guidance['phase']} - {guidance['step_title']}"
    parts.append(render_step_header(StepHeaderNode(
        title=title,
        script="alan_writing_style",
        step=step,
    )))
    parts.append("")

    if step == 1:
        parts.append(XML_FORMAT_MANDATE)
        parts.append("")

    if thoughts:
        parts.append(render(W.el("accumulated_thoughts", TextNode(thoughts)).build(), XMLRenderer()))
        parts.append("")

    parts.append(render_current_action(CurrentActionNode(guidance["actions"])))
    parts.append("")

    next_text = guidance.get("next", "")
    if is_complete or "COMPLETE" in next_text.upper():
        parts.append("WORKFLOW COMPLETE - Deliver final content.")
    else:
        next_cmd = f'python3 -m skills.alan_writing_style.writing_style --step-number {step + 1} --thoughts \\"<accumulated>\\"'
        parts.append(render_invoke_after(InvokeAfterNode(cmd=next_cmd)))

    return "\n".join(parts)


# Workflow definition -- derived from STEPS to avoid dual maintenance.
WORKFLOW = Workflow(
    "alan-writing-style",
    *[
        StepDef(
            id=s["id"],
            title=s["step_title"],
            actions=s["actions"],
        )
        for s in (STEPS[i] for i in sorted(STEPS))
    ],
    description="Multi-turn writing style compliance workflow",
    validate=False,
)


def main():
    """Entry point with parameter annotations for testing framework.

    Note: Uses --step-number for backward compatibility.
    Parameters have defaults because actual values come from argparse.
    """
    parser = argparse.ArgumentParser(
        description="Alan Writing Style - Multi-turn writing style compliance workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="",
    )

    parser.add_argument(
        "--step",
        "--step-number",
        dest="step_number",
        type=int,
        required=True,
        help="Current step number (starts at 1)",
    )
    parser.add_argument(
        "--thoughts",
        type=str,
        default="",
        help="Your thinking, draft content, classification, and findings",
    )

    args = parser.parse_args()

    if args.step_number < 1:
        print("ERROR: step-number must be >= 1", file=sys.stderr)
        sys.exit(1)

    guidance = get_step_guidance(args.step_number)
    print(format_output(args.step_number, guidance, args.thoughts))


if __name__ == "__main__":
    main()
