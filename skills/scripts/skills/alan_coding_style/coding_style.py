#!/usr/bin/env python3
"""
Alan Coding Style - Multi-turn prompt injection for coding style compliance.

Grounded in:
- Plan-and-Solve (Wang et al., 2023) - task classification before coding
- Step-Back Prompting (Zheng et al., 2023) - principle retrieval before applying
- RE2 Re-Reading (Xu et al., 2023) - re-read before verification
- Chain-of-Verification (Dhuliawala et al., 2023) - factored style checking
- Factor+Revise (Dhuliawala et al., 2023) - extract-then-judge per pattern
- Self-Refine (Madaan et al., 2023) - iterative improvement with checklist
- Metacognitive Prompting (Wang & Zhao, 2024) - sufficiency thresholds
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


TOTAL_STEPS = 9  # 9 steps: 8 workflow steps + quality gate (ref: DL-001)

# Injected at step 1 only; instructs executing agents to follow XML protocol.
# Content is agent-facing instruction text, not code metadata.
XML_FORMAT_MANDATE = """<xml_format_mandate>
CRITICAL: All script outputs use XML format. You MUST:
1. Execute the action in <current_action>
2. When complete, invoke the exact command in <invoke_after>
3. DO NOT modify commands. DO NOT skip steps.
</xml_format_mandate>"""

SECTION_TO_FILE = {
    "philosophy": "philosophy.md",
    "naming": "naming.md",
    "structure": "structure.md",
    "types": "types.md",
    "error-handling": "error-handling.md",
    "comments": "comments.md",
    "functions": "functions.md",
    "architecture": "architecture.md",
    "idioms": "idioms.md",
    "testing": "testing.md",
    "anti-patterns": "anti-patterns.md",
    "thresholds": "thresholds.md",
    "examples": "examples.md",
    "ai-voice-removal": "ai-voice-removal.md",
}


def get_references_dir() -> Path:
    # scripts/skills/alan_coding_style/ -> scripts/skills/ -> scripts/ -> skills/
    return Path(__file__).parent.parent.parent.parent / "alan-coding-style" / "references"


def load_section_files(sections: list[str]) -> list[tuple[str, str]]:
    """Load reference markdown files for the given section names.

    Isolated from format_output so file I/O stays separate from output
    formatting. Returns (section_name, file_content) pairs. Exits on
    unknown section name or missing file. (ref: DL-003, DL-005)
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


def format_section_block(name: str, content: str) -> str:
    """Format a section as a labeled plain-text block for embedding in current_action.

    Output: "=== name ===\ncontent" - visible to executing agents without file paths. (ref: DL-003)
    """
    return f"=== {name} ===\n{content.strip()}"


# Sentinel replaced with step-specific content in get_step_guidance.
_HISTORY_SENTINEL = "_HISTORY_"


def history_template(step: int) -> str:
    """Progressive context accumulation — shows only sections complete at this step."""
    parts = [
        "",
        "CONTEXT ACCUMULATION: Your --thoughts MUST include:",
        "",
        "  ## Classification (from Step 1)",
        "  | Aspect | Value |",
        "  | Task Type | generate/review/refactor/fix |",
        "  | Language(s) | ... |",
        "  | Scope | file/function/module |",
    ]
    if step >= 2:
        parts += [
            "",
            "  ## Applicable Rules (from Step 2)",
            "  | Category | Rule | Source Section |",
        ]
    if step >= 3:
        parts += [
            "",
            "  ## Draft Output (from Step 3)",
            "  Code or analysis notes produced in Step 3.",
        ]
    if step >= 4:
        parts += [
            "",
            "  ## Violations (from Steps 4-5)",
            "  | Location | Pattern | Code | Confidence |",
        ]
    if step >= 5:
        parts += [
            "",
            "  ## AI Voice Issues (from Step 5)",
            "  | Location | Tell Type | Code | Confidence |",
        ]
    if step >= 6:
        parts += [
            "",
            "  ## Positive Markers (from Step 6)",
            "  | Category | Count | Examples |",
            "  Assessment: STRONG/MODERATE/WEAK/MINIMAL",
        ]
    if step >= 7:
        parts += [
            "",
            "  ## Refinement Plan (from Step 7)",
            "  Ordered list of fixes to apply in Step 8.",
        ]
    parts.append("")
    return "\n".join(parts)

# Changes confined to STEPS dict text; get_step_guidance handler not refactored to avoid unnecessary diff. (ref: DL-006)
STEPS = {
    # Step 1: classification includes Consumers, Purpose, Code Context fields; Step 6 exempts test/config/CLI from some categories. (ref: DL-004, DL-005)
    1: {
        "id": "context_analysis",
        "phase": "UNDERSTANDING",
        "step_title": "Context Analysis",
        "actions": [
            "Before coding, classify your task. Style rules depend on this.",
            "",
            "<task_types>",
            "GENERATE - Write new code from requirements",
            "  Focus: naming, structure, patterns, error handling",
            "  Input: requirements description",
            "",
            "REVIEW - Assess existing code against style",
            "  Focus: identify violations, suggest fixes",
            "  Input: existing code to review",
            "",
            "REFACTOR - Restructure code to match style",
            "  Focus: architecture patterns, function design, naming",
            "  Input: existing code to refactor",
            "",
            "FIX - Debug while maintaining style",
            "  Focus: minimal change, preserve conventions",
            "  Input: buggy code + problem description",
            "</task_types>",
            "",
            "<classification_output>",
            "Map your task:",
            "",
            "  | Aspect | Value |",
            "  |--------|-------|",
            "  | Task Type | generate / review / refactor / fix |",
            "  | Language(s) | e.g. Python, C#, TypeScript |",
            "  | Scope | file / function / module / project |",
            "  | Consumers | internal / public-API / CLI / test |",
            "  | Purpose | one-sentence what this code does |",
            "  | Code Context | production / test / config / CLI / glue |",
            "",
            "This table guides section selection below and informs context-appropriate style checking.",
            "</classification_output>",
            "",
            "<section_selection>",
            "Select applicable reference sections for your task.",
            "",
            "  ALWAYS INCLUDE:",
            "    philosophy -- Core design instincts",
            "",
            "  SELECT BY TASK TYPE (defaults, adjust as needed):",
            "    GENERATE: naming, structure, types, functions, idioms, anti-patterns",
            "    REVIEW:   naming, anti-patterns, thresholds, examples",
            "    REFACTOR: structure, architecture, functions, naming",
            "    FIX:      error-handling, naming",
            "",
            "  ALL AVAILABLE:",
            "    philosophy, naming, structure, types, error-handling, comments,",
            "    functions, architecture, idioms, testing, anti-patterns,",
            "    thresholds, examples, ai-voice-removal",
            "",
            "OUTPUT: Write your selected sections as a comma-separated list (no spaces).",
            "Example: SECTIONS: philosophy,naming,structure,types,functions,idioms,anti-patterns",
            "Use this exact list to replace <SELECTED_SECTIONS> in the next command.",
            "</section_selection>",
        ],
        "next_desc": "Load applicable style rules.",
    },
    # Step 2: step_back_principles primes meta-cognitive framing; procedural rule lists defeat the technique by answering the question before it is asked. (ref: DL-002)
    2: {
        "id": "style_rule_retrieval",
        "phase": "UNDERSTANDING",
        "step_title": "Style Rule Retrieval",
        "actions": [
            "<purpose_gate>",
            "If you cannot state in one sentence what this code must accomplish and who",
            "consumes it, stop and request clarification before proceeding.",
            "</purpose_gate>",
            "",
            "Read the style sections below for your task type and language.",
            "Then use <rule_selection> to surface the applicable rules as a concrete list.",
            "",
            "<rule_selection>",
            "For your task type and language, surface:",
            "  1. NAMING rules that apply to this language",
            "  2. STRUCTURE patterns for this scope level",
            "  3. ERROR HANDLING conventions",
            "  4. IDIOMS specific to this language",
            "  5. ANTI-PATTERNS most likely for this task type",
            "",
            "Present each as a concrete, actionable rule.",
            "</rule_selection>",
            "",
            "<rule_priority>",
            "When two rules conflict or you must triage, resolve by this priority order.",
            "Higher-priority categories take precedence:",
            "  GENERATE: naming > structure > idioms > error handling",
            "  REVIEW:   anti-patterns > naming > structure > error handling",
            "  REFACTOR: structure > architecture > naming > idioms",
            "  FIX:      error handling > naming (changed code only)",
            "</rule_priority>",
            "",
            "OUTPUT: Write your <rule_selection> as a table:",
            "  | Category | Rule | Source Section |",
            "One row per applicable rule (5-10 rows). Then state your rule_priority order.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Apply style rules to code.",
    },
    3: {
        "id": "apply_style_rules",
        "phase": "GENERATION",
        "step_title": "Apply Style Rules",
        "actions": [
            # Step 3 is IF/ELSE dispatch with no identity context without this block; stakes block establishes Alan identity before rule application so output is owned, not just compliant. (ref: DL-002)
            "<stakes>",
            "This code represents Alan's coding identity.",
            "The output produced here directly reflects Alan's engineering standards.",
            "Generate code that Alan would recognize as his own -- not code that happens",
            "to pass a style check.",
            "</stakes>",
            "",
            # Brief reminder of four signature patterns — full rules are in Step 2 and --thoughts. (ref: DL-002)
            "Apply rules from Step 2, prioritized by task type (see <rule_priority>).",
            "Four signature patterns: terse naming (ans/ctx/fn), assert-driven invariants,",
            "data-driven dispatch (registry dicts), minimal abstraction (no speculative wrappers).",
            "",
            "<naming_reminders>",
            "Common LLM naming mistakes to avoid NOW (cheaper than fixing in Step 4):",
            "  WRONG: configuration, authentication_service, result_value, transaction_log",
            "  RIGHT: cfg, auth_svc, ans, txn_log",
            "  WRONG: DataManager, UserHandler, BaseProcessor",
            "  RIGHT: Cache, dispatch_user, (no base class needed)",
            "</naming_reminders>",
            "",
            "IMPORTANT: Focus ONLY on your classified task type from Step 1.",
            "Ignore instructions for other task types.",
            "",
            "<apply_rules>",
            "Using the classification from Step 1 and rules from Step 2:",
            "",
            "IF GENERATE:",
            "  Module structure (top to bottom):",
            "    1. Imports (formatter-managed)",
            "    2. Constants and registries (SCREAMING_SNAKE_CASE)",
            "    3. Core data types (frozen dataclasses for value types)",
            "    4. Internal helpers (prefixed `_`)",
            "    5. Public API functions",
            "    6. Entry point (if CLI: `if __name__ == '__main__': sys.exit(main())`)",
            "  Generation steps:",
            "  1. Write module-level layout first (imports, constants, section separators).",
            "  2. Name all types and functions before filling bodies — verify abbreviations",
            "     match naming rules (cfg not config, auth_svc not authentication_service).",
            "  3. Fill function bodies using ans pattern, walrus operator, early return.",
            "  4. Convert any if/elif dispatch chains to registry dicts.",
            "  5. Add assert guards for preconditions; use assert False for unreachable branches.",
            "",
            "IF REVIEW:",
            "  Read the code under review function by function.",
            "  For each function, note:",
            "    - Does naming match conventions? (terse, abbreviated, ans/ctx/fn)",
            "    - Is structure data-driven or procedural? (registry vs if/elif)",
            "    - Are invariants asserted or defensively checked?",
            "    - Are there LLM tells? (verbose names, narrating comments, gratuitous types)",
            "  Draft a violation list with quoted code and rule references.",
            "  Steps 4-5 will verify systematically; your draft seeds them.",
            "",
            "IF REFACTOR:",
            "  Read the code to refactor.",
            "  Apply structure and naming rules to produce improved version.",
            "  Preserve existing behavior.",
            "",
            "IF FIX:",
            "  Identify and fix the bug.",
            "  Apply style rules to the changed code only.",
            "  Minimize changes outside the fix.",
            "</apply_rules>",
            "",
            # Repeats Step 2 meta-cognitive questions at generation time — supplements, does not replace, Step 2 step-back. (ref: DL-002)
            "<step_back_at_generation>",
            "Before producing output, ask yourself:",
            "1. What makes Alan's coding style distinctive from generic clean code?",
            "   (Terse names, assert guards, registry dispatch, no speculative abstractions)",
            "2. What would make this code obviously LLM-generated?",
            "   (Over-engineered names, excessive comments, defensive internal validation)",
            "Write code that passes both tests.",
            "</step_back_at_generation>",
            "",
            "<output_expectations>",
            "GENERATE / REFACTOR / FIX: Output your draft code.",
            "REVIEW: Output your analysis notes with code references.",
            "",
            "Verification follows in Steps 4-5.",
            "</output_expectations>",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Check for anti-patterns.",
    },
    4: {
        "id": "anti_pattern_detection",
        "phase": "VERIFICATION",
        "step_title": "Anti-Pattern Detection",
        "actions": [
            "<re_read>",
            "Before checking, re-read the anti-patterns section from your Step 2 rules.",
            "With those WRONG/RIGHT pairs fresh, read your code function by function.",
            "</re_read>",
            "",
            "VERIFICATION METHOD: Extract first, then judge.",
            "For each pattern: (1) extract candidates, (2) assess each.",
            "PROCESS: Complete each pattern fully before moving to the next.",
            "After each pattern, record a running tally:",
            "  Patterns completed: N/5 | Violations found: M",
            "",
            "<pattern_1_naming>",
            "NAMING VIOLATIONS",
            "",
            "  EXTRACT: List all identifiers (variables, functions, classes, files).",
            "  Group by naming convention expected (from Step 2 rules).",
            "",
            "  JUDGE each: Does it follow the convention?",
            "    Check: Case style (camelCase, snake_case, PascalCase)",
            "    Check: Verbosity (WRONG if full-word where abbreviation is domain standard)",
            "    Note: Register consistency (terse vs verbose mixing) is checked in Step 5.",
            "",
            "  The principle: if the domain says it daily, the code says it abbreviated.",
            "",
            "  For each violation, record:",
            "    | Identifier | Expected | Actual | Confidence (HIGH/MED/LOW) |",
            "</pattern_1_naming>",
            "",
            "<pattern_2_overengineering>",
            "OVER-ENGINEERING (LLM code smell)",
            "",
            "  EXTRACT: List all abstractions (interfaces, base classes, wrappers,",
            "  utility functions, config objects).",
            "",
            "  JUDGE each by observable structural excess:",
            "    WRONG: Abstraction with only one implementation",
            "    WRONG: Config class for 2 settings (use constants)",
            "    WRONG: Wrapper that delegates every method",
            "    WRONG: Generic type parameters used once",
            "    RIGHT: Direct implementation without speculative abstraction",
            "  The principle: add abstraction only when the third use case arrives.",
            "",
            "  For each violation, record:",
            "    | Abstraction | Why Unnecessary | Confidence (HIGH/MED/LOW) |",
            "</pattern_2_overengineering>",
            "",
            "<pattern_3_error_handling>",
            "ERROR HANDLING VIOLATIONS",
            "",
            "  EXTRACT: List all try/catch, error checks, validation logic.",
            "",
            "  JUDGE each against style conventions (boundary errors only;",
            "  defensive internal checks are covered by Step 5 pattern_13):",
            "    WRONG: Catching Exception/BaseException without re-raising",
            "    WRONG: Silent failure (empty catch block)",
            "    WRONG: Error info swallowed (catch-and-log without re-raise)",
            "    RIGHT: Validate at system boundaries, trust internal code",
            "  The principle: trust internal code; validate only at system boundaries.",
            "",
            "  For each violation, record:",
            "    | Location | Issue | Convention Violated | Confidence (HIGH/MED/LOW) |",
            "</pattern_3_error_handling>",
            "",
            "<pattern_4_comments>",
            "COMMENT VIOLATIONS",
            "",
            "  EXTRACT: List all comments in the code.",
            "",
            "  JUDGE each (narrating docstrings are checked in Step 5 pattern_10;",
            "  focus here on commented-out code and TODO violations):",
            "    WRONG: Commented-out code left in",
            "    WRONG: TODO without context or owner",
            "    WRONG: Docstrings on trivial functions",
            "    RIGHT: Comment explains WHY, not WHAT",
            "    RIGHT: No comment when code is self-documenting",
            "  The principle: if the name and type tell the story, the comment is noise.",
            "",
            "  For each violation, record:",
            "    | Comment Text | Issue | Confidence (HIGH/MED/LOW) |",
            "</pattern_4_comments>",
            "",
            "<pattern_5_structure>",
            "STRUCTURAL VIOLATIONS",
            "",
            "  EXTRACT: List function/method sizes, nesting depths, file organization.",
            "",
            "  JUDGE against structure conventions:",
            "    Check: Function length within bounds",
            "    Check: Nesting depth acceptable",
            "    Check: Does function do both I/O and computation? (separate them)",
            "  Record as: | Function | Lines | Nesting | Compliance |",
            "  Step 5 reuses this table for variance analysis.",
            "  The principle: split at concerns, not at line counts.",
            "",
            "  For each violation, record:",
            "    | Location | Issue | Convention | Confidence (HIGH/MED/LOW) |",
            "</pattern_5_structure>",
            "",
            # LLM code tells (verbose names, defensive checks, gratuitous types) are covered by Step 5 AI voice removal patterns 6, 9, 11 and the ai-voice-removal reference. Removed to avoid duplicate findings.
            "OUTPUT: Violation table with quoted code and confidence per pattern.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Check for AI voice in code.",
    },
    5: {
        "id": "ai_voice_removal",
        "phase": "VERIFICATION",
        "step_title": "AI Voice Removal",
        "actions": [
            "Apply the AI voice removal patterns below to your code/review output.",
            "The reference (13 checks with extract-then-judge methodology) is",
            "injected inline in this step.",
            "",
            "The patterns below are already adapted to code context.",
            "Follow every pattern exactly as written.",
            # Prose-to-code adaptation mapping (reference only; patterns already incorporate these):
            #   sentences -> lines of code, comments, docstrings
            #   paragraphs -> functions, classes, modules
            #   structural monotony -> cookie-cutter function/class shapes
            #   formula following -> cookie-cutter function shapes
            #   structural variance -> function-shape variance
            #   sentence rhythm -> line-complexity mix
            "",
            "OUTPUT: AI voice violation table with quoted code and confidence per pattern.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Check for positive coding patterns.",
    },
    # Step 6: thresholds are binding gates (>= not ~); WEAK/MINIMAL verdict is a FAIL. (ref: DL-003)
    6: {
        "id": "positive_pattern_check",
        "phase": "VERIFICATION",
        "step_title": "Positive Pattern Check",
        "actions": [
            "<positive_patterns>",
            "VERIFICATION METHOD: Extract first, then assess sufficiency.",
            "Steps 4-5 check for ABSENCE of bad patterns.",
            "This step checks for PRESENCE of Alan's signature coding patterns.",
            "",
            "CATEGORY 1: NAMING IDIOMS",
            # Step 6 receives no reference file injection (Step 2 is the only injection point), so category patterns must be self-contained. (ref: DL-004)
            "  EXTRACT: Identifiers following these specific patterns:",
            "    - `ans` for return-value variables",
            "    - `ctx` for context parameters",
            "    - single-letter vars in tight scopes (f, b, v, r, n, k)",
            "    - trailing underscore for shadowed builtins (break_, else_)",
            "    - terse class names (Cfg, AuthSvc, TxnLog)",
            "  COUNT: How many found? Quote each identifier.",
            "",
            "CATEGORY 2: ARCHITECTURE PATTERNS",
            # Step 6 receives no reference file injection; detection targets are embedded inline so the agent does not depend on re-injected .md content. (ref: DL-004)
            "  EXTRACT: Structural patterns matching these specifics:",
            "    - registry dicts (FRAG_OPTS, ROUTES, HANDLERS) for dispatch",
            "    - frozen dataclasses for value types",
            "    - `assert` as invariant checks, not defensive validation",
            "    - `with` blocks for resource/state scoping",
            "    - ordered function lists for pipelines",
            "  COUNT: How many found? Quote each pattern.",
            "",
            "CATEGORY 3: ERROR HANDLING PATTERNS",
            # Same rationale as Category 2 anchor (CC-M-002-003): inline patterns are required because Step 6 receives no reference file injection. (ref: DL-004)
            "  EXTRACT: Error handling matching these specifics:",
            "    - `assert` for preconditions/postconditions",
            "    - `assert False` for unreachable branches",
            "    - terse lowercase error messages without trailing period",
            "    - `raise ... from None` to suppress exception chains",
            "    - validation at boundaries only (not in internal helpers)",
            "  COUNT: How many found? Quote each.",
            "",
            "CATEGORY 4: LANGUAGE IDIOMS",
            # Same rationale as Category 2 anchor (CC-M-002-003): inline patterns are required because Step 6 receives no reference file injection. (ref: DL-004)
            "  EXTRACT: Language-specific patterns matching these specifics:",
            "    - walrus operator in conditionals (`if i := x.check():`)",
            "    - comprehensions for single-expression transforms",
            "    - f-strings exclusively (no .format or % formatting)",
            "    - match/case for AST dispatch",
            "    - pathlib.Path for file handling, contextlib.contextmanager usage",
            "  COUNT: How many found? Quote each.",
            "",
            "CATEGORY 5: CODE ORGANIZATION",
            # Same rationale as Category 2 anchor (CC-M-002-003): inline patterns are required because Step 6 receives no reference file injection. (ref: DL-004)
            "  EXTRACT: Organization patterns matching these specifics:",
            "    - constants at module top in SCREAMING_SNAKE_CASE",
            "    - imports grouped: standard / third-party / local",
            "    - leading underscore for internal modules (_core.py, _api.py)",
            "    - section separators (####...####) in large files",
            "    - re-export facade using `as` aliases (no __all__)",
            "  COUNT: How many found? Quote each.",
            "</positive_patterns>",
            "",
            "<sufficiency_check>",
            "REFERENCE THRESHOLDS:",
            "  - Code <50 lines: >= 2 markers from any category",
            "  - Code 50-200 lines: >= 4 markers across 2+ categories",
            "  - Code >200 lines: >= 6 markers across 3+ categories",
            "",
            "TALLY:",
            "  | Category | Count | Examples |",
            "  |----------|-------|----------|",
            "  | Naming Idioms | ? | '...' |",
            "  | Architecture | ? | '...' |",
            "  | Error Handling | ? | '...' |",
            "  | Language Idioms | ? | '...' |",
            "  | Organization | ? | '...' |",
            "  | TOTAL | ? | |",
            "",
            "ASSESSMENT (based on evidence strength):",
            "  STRONG:   6+ markers across 3+ categories",
            "  MODERATE: 4-5 markers across 2+ categories",
            "  WEAK:     2-3 markers",
            "  MINIMAL:  0-1 markers",
            "",
            "VERDICT: Both checks must pass:",
            "  1. Marker count meets REFERENCE THRESHOLDS for code size.",
            "  2. Assessment is STRONG or MODERATE.",
            "If either check fails -> FAIL (record as HIGH priority violation for Step 7).",
            "",
            "EXEMPTIONS by code context (from Step 1):",
            "  test code: skip Architecture and Organization categories.",
            "  config/glue code: skip Language Idioms category.",
            "  CLI scripts <30 lines with no dispatch logic: skip Architecture category.",
            "When categories are exempted, reduce the 'across N+ categories' requirement",
            "by 1 per exempted category. Marker count threshold stays the same.",
            "",
            "Carry your assessment and verdict to Step 7.",
            "</sufficiency_check>",
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
            "Include anti-pattern violations, AI voice issues, AND positive pattern assessment.",
            "",
            "<consolidation>",
            "Create a single violation table:",
            "",
            "  | # | Location | Pattern | Code/Description | Confidence | Priority |",
            "  |---|----------|---------|------------------|------------|----------|",
            "  | 1 | Global   | Positive | assessment: WEAK | HIGH       | P1      |",
            "  | 2 | line 12  | AI Voice | 'getData()'     | HIGH       | P2      |",
            "  | 3 | line 30  | Naming   | 'get the data'  | MED        | P3      |",
            "",
            "PRIORITY ORDER (category first, then HIGH before MED/LOW within each):",
            "  P1. Missing positive patterns (most impactful -- drives the most rework)",
            "  P2. AI voice / LLM tells (most revealing of non-human authorship)",
            "  P3. Naming violations (most visible to readers)",
            "  P4. Over-engineering / unnecessary abstraction (hardest to add back once shipped)",
            "  P5. Structural and comment issues (lowest reader impact)",
            "</consolidation>",
            "",
            "<cross_check>",
            "Review the consolidated list:",
            "",
            "  1. Are any violations duplicates? (Same code, different patterns)",
            "     -> Merge into single entry, note both patterns.",
            "",
            "  2. Do any violations conflict? (Fixing one creates another)",
            "     -> Higher-priority category (per P1-P5) takes precedence.",
            "     -> Accept the lower-priority regression and note it.",
            "",
            "  3. Are any LOW confidence violations actually false positives?",
            "     -> Remove if you cannot quote a specific code token that violates the pattern.",
            "     -> Keep if you can quote the token, even at LOW confidence.",
            "",
            "  4. Are any areas violation-free? (Confirm explicitly)",
            "     -> Note: 'Lines X-Y: No violations found.'",
            "</cross_check>",
            "",
            "<refinement_plan>",
            "Create a refinement order:",
            "",
            "  Fix #1: [violation] -> [planned fix approach]",
            "  Fix #2: [violation] -> [planned fix approach]",
            "  ...",
            "",
            "This plan guides Step 8.",
            "</refinement_plan>",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Apply refinements and deliver.",
    },
    # Step 8: final_checklist triggers Step 9 quality gate instead of silently noting issues; loop prevents silent delivery of violations. (ref: DL-007)
    8: {
        "id": "refine_deliver",
        "phase": "REFINEMENT",
        "step_title": "Refine & Deliver",
        "actions": [
            "Apply refinements from your Step 7 plan.",
            "",
            "<refinement_process>",
            "FOR EACH VIOLATION in priority order:",
            "  1. Quote the original code",
            "  2. State the pattern violated",
            "  3. Write the revised code",
            "  4. Verify the fix doesn't introduce new violations",
            "</refinement_process>",
            "",
            "<naming_fix>",
            "NAMING FIX:",
            "  BEFORE: getData() or user_input_validation_result",
            "  AFTER:  get_data() or ans",
            "  BEFORE: configuration, authentication_service",
            "  AFTER:  cfg, auth_svc",
            "</naming_fix>",
            "",
            "<overengineering_fix>",
            "OVER-ENGINEERING FIX:",
            "  BEFORE: AbstractFactory + Interface + Implementation for one use case",
            "  AFTER:  Single function or class with no inheritance",
            "  BEFORE: Config class for 2 settings",
            "  AFTER:  Two module-level constants",
            "</overengineering_fix>",
            "",
            "<comment_fix>",
            "COMMENT FIX:",
            "  BEFORE: # increment the counter\\n  counter += 1",
            "  AFTER:  counter += 1",
            "</comment_fix>",
            "",
            "<llm_authorship_fix>",
            "LLM AUTHORSHIP FIX (covers both LLM tells and AI voice):",
            "  Verbose names:    user_input_string -> ipt",
            "  Gratuitous types (locals only): x: str = get_input() -> x = get_input()",
            "    Note: function parameter and return annotations are required -- do not remove.",
            "  Cliche names:     DataManager -> Cache, UserHandler -> dispatch_user",
            "  Narrating comments: # First validate the input -> (delete)",
            "  Formulaic structure: vary function shapes by purpose",
            "  Completionist features: delete unrequested configurability",
            "</llm_authorship_fix>",
            "",
            "<refinement_log>",
            "Record each change:",
            "",
            "  | # | Original | Revised | Pattern Fixed |",
            "  |---|----------|---------|---------------|",
            "",
            "This log goes in your --thoughts.",
            "</refinement_log>",
            "",
            "OUTPUT: Revised code/review with refinement log. Step 9 runs final verification.",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "Run quality gate.",
    },
    9: {
        "id": "quality_gate",
        "phase": "REFINEMENT",
        "step_title": "Quality Gate",
        "actions": [
            "FINAL VERIFICATION. Re-read your refined code before checking.",
            "Do not rely on earlier assessments -- verify each item fresh.",
            "",
            "<final_checklist>",
            "Check each box ONLY if the condition is met. Leave unchecked if not.",
            "",
            "ANTI-PATTERNS ABSENT:",
            "  [ ] No naming convention violations",
            "  [ ] No over-engineering (speculative abstraction)",
            "  [ ] No error handling violations",
            "  [ ] No comment violations (restating code, commented-out code)",
            "  [ ] No structural violations (function length, nesting)",
            "",
            "AI VOICE ABSENT:",
            "  [ ] No formulaic function signatures (cookie-cutter structure)",
            "  [ ] No didactic or narrative comments (lecturing, step-by-step narration)",
            "  [ ] No cliche naming (Manager, Handler, Service, Helper, Util)",
            "  [ ] No gratuitous type hints on obvious locals",
            "",
            "POSITIVE PATTERNS PRESENT:",
            "  [ ] Naming follows conventions (terse, abbreviated, ans/ctx/fn)",
            "  [ ] Architecture patterns present (registry dicts, frozen dataclasses)",
            "  [ ] Error handling follows conventions (assert guards, boundary validation)",
            "  [ ] Language idioms used (walrus operator, comprehensions, f-strings)",
            "  [ ] Code organization matches conventions (section separators, imports)",
            "",
            "If any checkbox is [ ] instead of [x]:",
            "  Re-invoke Step 8 (include your --sections from the current invocation).",
            "",
            "Otherwise: all boxes checked. Deliver final code.",
            "</final_checklist>",
            "",
            _HISTORY_SENTINEL,
        ],
        "next_desc": "WORKFLOW COMPLETE - deliver final code.",
    },
}


def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
    """Return step-specific guidance dict for the given step.

    When sections is provided, loads the corresponding reference files and
    prepends them as labeled plain-text blocks into the actions list.
    Step 5 always appends the ai-voice-removal section regardless of sections.
    (ref: DL-004, DL-003)
    """
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
    next_text = f"Step {next_step}: {step_data['next_desc']}" if next_step else step_data["next_desc"]
    actions = list(step_data["actions"])

    # Replace history sentinel with step-specific progressive template
    actions = [history_template(step) if item == _HISTORY_SENTINEL else item for item in actions]

    # Reference sections inject at Step 2 only; Steps 3-9 carry rules via --thoughts accumulation. Step 5 ai-voice injection (step == 5, below) operates on a separate path. (ref: DL-001, DL-006)
    if sections and step == 2:
        loaded = load_section_files(sections)
        section_blocks = [format_section_block(name, content) for name, content in loaded]
        actions = section_blocks + actions

    if step == 5:
        ai_voice_sections = load_section_files(["ai-voice-removal"])
        section_blocks = [format_section_block(name, content) for name, content in ai_voice_sections]
        actions = actions + section_blocks

    return {
        "phase": phase,
        "step_title": step_data["step_title"],
        "actions": actions,
        "next": next_text,
    }


def format_output(
    step: int,
    guidance: dict,
    thoughts: str,
) -> str:
    """Render step output as XML using the AST builder API.

    Reads sections_arg from guidance dict (set by main) to propagate
    --sections through invoke_after without leaking it into the function
    signature. (ref: DL-001, DL-005)
    """
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

    parts.append(render_current_action(CurrentActionNode(guidance["actions"])))
    parts.append("")

    next_text = guidance.get("next", "")
    if is_complete or "COMPLETE" in next_text.upper():
        parts.append("WORKFLOW COMPLETE - Deliver final code.")
    else:
        # sections_arg passed via guidance dict so format_output stays at 3 params (ref: DL-001)
        if step == 1:
            sections_part = guidance.get("sections_arg", "<SELECTED_SECTIONS>")
        else:
            sections_part = guidance.get("sections_arg", "")
        if sections_part:
            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --sections {sections_part} --thoughts \\"<accumulated>\\"'
        else:
            next_cmd = f'python3 -m skills.alan_coding_style.coding_style --step {step + 1} --thoughts \\"<accumulated>\\"'
        parts.append(render_invoke_after(InvokeAfterNode(cmd=next_cmd)))

    return "\n".join(parts)


# Workflow definition — derived from STEPS to avoid dual maintenance.
WORKFLOW = Workflow(
    "alan-coding-style",
    *[
        StepDef(
            id=s["id"],
            title=s["step_title"],
            actions=s["actions"],
        )
        for s in (STEPS[i] for i in sorted(STEPS))
    ],
    description="Multi-turn coding style compliance workflow",
    validate=False,
)


def main():
    """Entry point with parameter annotations for testing framework.

    Note: Uses --step-number for backward compatibility.
    Parameters have defaults because actual values come from argparse.
    """
    parser = argparse.ArgumentParser(
        description="Alan Coding Style - Multi-turn coding style compliance workflow",
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
        help="Your thinking, draft code, classification, and findings",
    )
    parser.add_argument(
        "--sections",
        type=str,
        default=None,
        help="Comma-separated style guide sections to inject",
    )

    args = parser.parse_args()

    if args.step_number < 1:
        print("ERROR: step-number must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.step_number > TOTAL_STEPS:
        print(f"ERROR: step-number cannot exceed {TOTAL_STEPS}", file=sys.stderr)
        sys.exit(1)

    sec_list = [s.strip() for s in args.sections.split(",") if s.strip()] if args.sections else None
    guidance = get_step_guidance(args.step_number, sections=sec_list)
    if args.sections:
        # Propagate sections string through guidance dict so format_output can
        # emit it in invoke_after without an extra parameter. (ref: DL-001, DL-004)
        guidance["sections_arg"] = args.sections
    print(format_output(args.step_number, guidance, args.thoughts))


if __name__ == "__main__":
    main()
