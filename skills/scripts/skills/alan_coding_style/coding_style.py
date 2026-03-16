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


# Context accumulation template shared by Steps 2-7 and 9.
# Single template prevents duplicate Classification tables across steps; Step 9 excluded from contiguous range because Step 8 does not use it. (ref: DL-009)
HISTORY_TEMPLATE = """
CONTEXT ACCUMULATION: Your --thoughts MUST include:

  ## Classification (from Step 1)
  | Aspect | Value |
  | Task Type | generate/review/refactor/fix |
  | Language(s) | ... |
  | Scope | file/function/module |

  ## Applicable Rules (from Step 2)
  | Category | Rule | Source Section |

  ## Draft Output (from Step 3)
  Code or analysis notes produced in Step 3.

  ## Violations (from Steps 4-5)
  | Location | Pattern | Code | Confidence |

  ## AI Voice Issues (from Step 5)
  | Location | Tell Type | Code | Confidence |

  ## Positive Markers (from Step 6)
  | Category | Count | Examples |
  Assessment: STRONG/MODERATE/WEAK/MINIMAL

  ## Refinement Plan (from Step 7)
  Ordered list of fixes to apply in Step 8.
"""

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
            "<step_back_principles>",
            "1. What makes Alan's coding style distinctive from generic clean code?",
            "   (Concrete decision thresholds, contrastive WRONG/RIGHT pairs, minimal abstraction)",
            "2. What would make this code obviously LLM-generated?",
            "   (Over-engineering, verbose names, excessive comments, defensive validation of internal state)",
            "Keep these answers in mind as you apply rules.",
            "</step_back_principles>",
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
            "Skip sections with no content (placeholder-only).",
            "</rule_selection>",
            "",
            "<rule_priority>",
            "PRIORITY by task type:",
            "  GENERATE: naming > structure > idioms > error handling",
            "  REVIEW:   anti-patterns > naming > structure > error handling",
            "  REFACTOR: structure > architecture > naming > idioms",
            "  FIX:      error handling > naming (changed code only)",
            "</rule_priority>",
            "",
            HISTORY_TEMPLATE,
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
            # Four patterns distilled from reference sections — embedded here so Step 3 carries them without reference re-injection. (ref: DL-002)
            "<core_coding_voice>",
            "Four patterns that make Alan's code immediately recognizable:",
            "",
            "1. TERSE NAMING",
            "   Return values: `ans`. Context params: `ctx`. Bound function: `fn`.",
            "   Tight loop vars: f, b, v, r, n, k/v.",
            "   Class names: Cfg, AuthSvc, TxnLog.",
            "",
            "2. ASSERT-DRIVEN INVARIANTS",
            "   `assert isinstance(x, int)` guards preconditions.",
            "   `assert False, 'unreachable'` marks dead branches.",
            "   No defensive try/except around internal state.",
            "",
            "3. DATA-DRIVEN DISPATCH",
            "   FRAG_OPTS = {'json': fmt_json, 'csv': fmt_csv}",
            "   ROUTES = {'get': handle_get, 'post': handle_post}",
            "   Registry dict + lookup instead of if/elif chains.",
            "",
            "4. MINIMAL ABSTRACTION",
            "   Implement directly. No speculative wrappers or base classes.",
            "   If the same logic appears twice, extract. Once: keep inline.",
            "</core_coding_voice>",
            "",
            "IMPORTANT: Focus ONLY on your classified task type from Step 1.",
            "Ignore instructions for other task types.",
            "",
            "<apply_rules>",
            "Using the classification from Step 1 and rules from Step 2:",
            "",
            "IF GENERATE:",
            "  Write code following every applicable rule.",
            "  Name things according to naming conventions.",
            "  Structure according to architecture patterns.",
            "  Handle errors per error handling conventions.",
            "  Use language-specific idioms.",
            "",
            "IF REVIEW:",
            "  Read the code under review carefully.",
            "  For each applicable rule, check compliance.",
            "  Note areas of concern -- defer full analysis to Steps 4-5.",
            "  Draft initial observations.",
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
            HISTORY_TEMPLATE,
        ],
        "next_desc": "Check for anti-patterns.",
    },
    4: {
        "id": "anti_pattern_detection",
        "phase": "VERIFICATION",
        "step_title": "Anti-Pattern Detection",
        "actions": [
            "<re_read>",
            "Read your code/review again, function by function.",
            "Then check for anti-patterns.",
            "</re_read>",
            "",
            "VERIFICATION METHOD: Extract first, then judge.",
            "For each pattern: (1) extract candidates, (2) assess each.",
            "PROCESS: Complete each pattern fully before moving to the next.",
            "After each pattern, record a running tally:",
            "  Patterns completed: N/6 | Violations found: M",
            "",
            "<pattern_1_naming>",
            "NAMING VIOLATIONS",
            "",
            "  EXTRACT: List all identifiers (variables, functions, classes, files).",
            "  Group by naming convention expected (from Step 2 rules).",
            "",
            "  JUDGE each: Does it follow the convention?",
            "    Check: Case style (camelCase, snake_case, PascalCase)",
            "    Check: Descriptiveness (not too generic, not too verbose)",
            "    Check: Consistency within scope",
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
            "  JUDGE each: Is it necessary for the current requirements?",
            "    WRONG: Abstract factory for one implementation",
            "    WRONG: Config class for 2 settings",
            "    WRONG: Wrapper that delegates every method",
            "    WRONG: Generic type parameters used once",
            "    RIGHT: Direct implementation without speculative abstraction",
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
            "  JUDGE each against style conventions:",
            "    Check: Are errors handled at the right level?",
            "    Check: Is error information preserved or swallowed?",
            "    Check: Is validation appropriate (not defensive against impossible states)?",
            "    WRONG: Catching Exception/BaseException without re-raising",
            "    WRONG: Validating internal function parameters already validated upstream",
            "    WRONG: Silent failure (empty catch block)",
            "    RIGHT: Validate at system boundaries, trust internal code",
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
            "  JUDGE each: Does it follow comment style conventions?",
            "    WRONG: Comment restates what code does ('# increment counter')",
            "    WRONG: Commented-out code left in",
            "    WRONG: TODO without context or owner",
            "    WRONG: Docstrings on trivial functions",
            "    RIGHT: Comment explains WHY, not WHAT",
            "    RIGHT: No comment when code is self-documenting",
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
            "    Check: Single responsibility per function",
            "    Check: Dependencies flow in correct direction",
            "    Check: No circular imports or dependencies",
            "",
            "  For each violation, record:",
            "    | Location | Issue | Convention | Confidence (HIGH/MED/LOW) |",
            "</pattern_5_structure>",
            "",
            "<pattern_6_llm_tells>",
            "LLM CODE TELLS",
            "",
            "  EXTRACT: Scan for patterns typical of LLM-generated code:",
            "    - Excessive inline comments explaining obvious logic",
            "    - Over-verbose variable names ('userInputValidationResult')",
            "    - Unnecessary type annotations on obvious types",
            "    - Defensive checks for impossible states",
            "    - 'Helper' or 'Util' classes/functions",
            "    - Unused imports",
            "    - Docstrings on every function regardless of complexity",
            "    - Over-parameterized functions (flags for every variation)",
            "",
            "  JUDGE each: Is this genuinely needed or an LLM tell?",
            "",
            "  For each violation, record:",
            "    | Code | LLM Tell Type | Confidence (HIGH/MED/LOW) |",
            "</pattern_6_llm_tells>",
            "",
            "OUTPUT: Violation table with quoted code and confidence per pattern.",
            "",
            HISTORY_TEMPLATE,
        ],
        "next_desc": "Check for AI voice in code.",
    },
    5: {
        "id": "ai_voice_removal",
        "phase": "VERIFICATION",
        "step_title": "AI Voice Removal",
        "actions": [
            "Apply the AI voice removal patterns from the loaded ai-voice-removal",
            "reference to your code/review output. The reference contains the exact",
            "detection patterns (13 checks with extract-then-judge methodology).",
            "",
            "Adapt each pattern to CODE context:",
            "  - 'sentences' -> lines of code, comments, docstrings",
            "  - 'paragraphs' -> functions, classes, modules",
            "  - 'quotes/references' -> imports, dependencies, naming patterns",
            "  - 'structural monotony' -> cookie-cutter function/class shapes",
            "  - 'meta-commentary openers' -> meta-docstrings describing what follows",
            # Prose-specific patterns (formula following, structural variance, sentence rhythm) have no code equivalent; entries map prose pattern names to their code-domain analogs so Step 5 adaptation guidance stays current.
            "  - 'formula following' -> cookie-cutter function shapes (docstring->validate->process->return)",
            "  - 'structural variance' -> function-shape variance (line count, nesting depth, param count)",
            "  - 'sentence rhythm' -> line-complexity mix (assignments vs expressions vs comprehensions)",
            "",
            "The ai-voice-removal reference is injected above.",
            "Follow every pattern exactly as written, substituting code artifacts",
            "for prose artifacts.",
            "",
            "OUTPUT: AI voice violation table with quoted code and confidence per pattern.",
            "",
            HISTORY_TEMPLATE,
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
            "    - single-letter vars in tight scopes (f, b, v, r, n, k, v)",
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
            "VERDICT: STRONG/MODERATE -> PASS.",
            "WEAK/MINIMAL -> FAIL (record as HIGH priority violation for Step 7).",
            "",
            "EXEMPTIONS by code context (from Step 1):",
            "  test code: skip Architecture and Organization categories.",
            "  config/glue code: skip Language Idioms category.",
            "  CLI scripts: skip Architecture category.",
            "",
            "Carry your assessment and verdict to Step 7.",
            "</sufficiency_check>",
            "",
            HISTORY_TEMPLATE,
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
            "  | 1 | line 12  | Naming  | 'getData()'      | HIGH       | P2      |",
            "  | 2 | line 30  | LLM Tell| '# get the data' | HIGH       | P5      |",
            "  | 3 | Global   | Weak positive patterns | assessment: WEAK | HIGH | P1 |",
            "",
            "PRIORITY ORDER (numbered, apply in this order):",
            "  P1. Missing positive patterns (most impactful)",
            "  P2. AI voice patterns (most revealing of LLM authorship)",
            "  P3. Naming violations (most visible)",
            "  P4. Over-engineering",
            "  P5. HIGH confidence before MED/LOW",
            "  P6. LLM tells",
            "  P7. Minor structural issues",
            "</consolidation>",
            "",
            "<cross_check>",
            "Review the consolidated list:",
            "",
            "  1. Are any violations duplicates? (Same code, different patterns)",
            "     -> Merge into single entry, note both patterns.",
            "",
            "  2. Do any violations conflict? (Fixing one creates another)",
            "     -> Note the conflict, decide which takes precedence.",
            "",
            "  3. Are any LOW confidence violations actually false positives?",
            "     -> Re-examine the code. Remove if not a real violation.",
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
            HISTORY_TEMPLATE,
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
            "  Apply naming conventions from the style guide.",
            "  BEFORE: getData() or user_input_validation_result",
            "  AFTER:  [name following conventions for detected language]",
            "</naming_fix>",
            "",
            "<overengineering_fix>",
            "OVER-ENGINEERING FIX:",
            "  Remove speculative abstraction. Use direct implementation.",
            "  BEFORE: AbstractFactory + Interface + Implementation",
            "  AFTER:  Single concrete implementation",
            "</overengineering_fix>",
            "",
            "<comment_fix>",
            "COMMENT FIX:",
            "  Remove restating comments. Keep WHY comments.",
            "  BEFORE: # increment the counter\\n  counter += 1",
            "  AFTER:  counter += 1",
            "</comment_fix>",
            "",
            "<llm_tell_fix>",
            "LLM TELL FIX:",
            "  Remove excessive annotations, verbose names, defensive checks.",
            "  BEFORE: user_input_string: str = get_user_input_string()  # get input",
            "  AFTER:  user_input = get_input()",
            "</llm_tell_fix>",
            "",
            "<ai_voice_fix>",
            "AI VOICE FIX:",
            "  Remove patterns that reveal LLM authorship.",
            "  BEFORE: class DataManager: / def process_data(self): / # First validate",
            "  AFTER:  class Cache: / def invalidate(self): / (no narration comment)",
            "",
            "  Formulaic structure: vary function shapes by purpose.",
            "  Didactic comments: delete narration, keep only WHY.",
            "  Cliche names: replace Manager/Handler/Service with concrete nouns.",
            "  Gratuitous types: remove obvious local annotations.",
            "  Completionist features: delete unrequested configurability.",
            "</ai_voice_fix>",
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
            "<final_checklist>",
            "ANTI-PATTERNS ABSENT (must all be true):",
            "  [x] No naming convention violations",
            "  [x] No over-engineering (speculative abstraction)",
            "  [x] No error handling violations",
            "  [x] No comment violations (restating code, commented-out code)",
            "  [x] No structural violations (function length, nesting)",
            "  [x] No LLM code tells (excessive comments, over-verbose names)",
            "",
            "AI VOICE ABSENT (must all be true):",
            "  [x] No formulaic function signatures (cookie-cutter structure)",
            "  [x] No didactic or narrative comments (lecturing, step-by-step narration)",
            "  [x] No cliche naming (Manager, Handler, Service, Helper, Util)",
            "  [x] No hollow annotations (IMPORTANT/NOTE without substance)",
            "  [x] No gratuitous type hints on obvious locals",
            "  [x] No completionist features (unrequested configurability)",
            "",
            "POSITIVE PATTERNS PRESENT (must all be true):",
            "  [x] Naming follows conventions for detected language",
            "  [x] Architecture patterns match expectations",
            "  [x] Error handling follows conventions",
            "  [x] Language idioms used appropriately",
            "  [x] Code organization matches conventions",
            "",
            "If any checkbox would be [ ] instead of [x]:",
            "  increase total_steps.",
            "",
            "Otherwise: code complete. Deliver final output.",
            "</final_checklist>",
        ],
        "next_desc": "Run quality gate.",
    },
    9: {
        "id": "quality_gate",
        "phase": "REFINEMENT",
        "step_title": "Quality Gate",
        "actions": [
            HISTORY_TEMPLATE,
            "",
            "<stopping_criteria>",
            "STOP when ALL of the following are true:",
            "  - Zero HIGH-confidence violations remain",
            "  - Positive markers >= threshold (STRONG or MODERATE verdict from Step 6)",
            "  - No cargo-culted step-back principles appear in output",
            "",
            "CONTINUE (increase total_steps) when ANY of the following are true:",
            "  - A HIGH-confidence violation remains unresolved",
            "  - Positive markers assessment is WEAK or MINIMAL",
            "  - Style-context mismatch detected (wrong rules applied for code context)",
            "</stopping_criteria>",
            "",
            "Evaluate each condition above against your accumulated context.",
            "If STOP conditions are all met: proceed to deliver final code below.",
            "If any CONTINUE condition is true: increase total_steps and loop back to Step 8.",
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
