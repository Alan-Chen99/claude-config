# Skills architecture

Script-based agent workflows on a shared orchestration framework. These rules
govern every skill module under `scripts/skills/`; `deepthink/think.py`,
`decision_critic/decision_critic.py` and `codebase_analysis/analyze.py` there
follow them.

## The book pattern

A skill file reads top to bottom like a book: everything is defined above its
first use, so a reader never scrolls up.

### Section order

Group by type, not by step, because functions reference prompts from several
steps. Omit a section with no content. Within each section, order by workflow
step.

1. SHARED PROMPTS: prompts used by 2+ steps (`prompts/shared.py` if large)
2. CONFIGURATION: constants, temperatures, thresholds
3. SYSTEM PROMPTS
4. MESSAGE TEMPLATES: step-delimited (below)
5. PARSING FUNCTIONS
6. MESSAGE BUILDERS: functions that compose templates into messages
7. [DOMAIN] LOGIC
8. STEP DEFINITIONS: the `STATIC_STEPS` and `DYNAMIC_STEPS` dicts
9. OUTPUT FORMATTING: `format_output()`
10. ENTRY POINT: `main()`

A section header is three comment lines, `# ` and 76 `=`, then
`# SECTION NAME`, then the `=` line again, with a blank line before and after.
Inside MESSAGE TEMPLATES, a divider of the same width opens each step,
`# --- STEP 2: SURVEY ---…`. Within a step, the dispatch constants (context,
agents, guidance) come before the instructions.

### Placement

A prompt belongs in the earliest section where it is used. A prompt used in
steps 2, 4 and 6 goes in SHARED PROMPTS. A prompt used only in step 3, or in
steps 3 and 4, goes at step 3's position.

### Naming

Constants are named `[PHASE]_[TYPE]`. PHASE is the workflow phase (`SCOPE`,
`SURVEY`, `DEEPEN`, `SYNTHESIZE`). TYPE is the constant's role
(`INSTRUCTIONS`, `DISPATCH_CONTEXT`, `DISPATCH_AGENTS`, `DISPATCH_GUIDANCE`,
`FORMAT`, `FEEDBACK`). A confidence variant puts the level after the phase
(`SURVEY_LOW_INSTRUCTIONS`). A shared prompt has no phase
(`EVALUATION_CRITERIA`).

### Strings

A multi-line prompt is a parenthesized concatenation and never a
triple-quoted string, which forces its content to column 0. Each line is its
own literal ending in an explicit `\n`. A blank line is `"\n"` on its own line,
and the last line has no `\n`. A composed constant joins as
`+ NAME + "\n"`.

## Step bodies

A step body is a string. There are no action factories and no inversion of
control.

- Static text is a constant in MESSAGE TEMPLATES. Anything that calls
  `roster_dispatch()` and its kin, or takes parameters, is a builder in
  MESSAGE BUILDERS that composes constants defined above it. The prompt text
  then reads at its definition, and dispatch parameters change without
  touching it.
- A mostly static workflow maps each static step to `(title, instructions)` in
  `STATIC_STEPS`, and each parameterized step to a `_format_step_N` function
  in `DYNAMIC_STEPS`. One `format_output()` reads both dicts. A
  `_format_step_N` comes after MESSAGE BUILDERS and before `DYNAMIC_STEPS`.
- A function that returns a prompt fragment is justified only by real
  branching, and it lives in the skill, not in `lib/`. Otherwise compose
  constants with `+`.

## Shared library

`scripts/skills/lib/workflow/prompts/` holds only abstractions that three or
more skills use with the same meaning; anything narrower stays in its skill. A
dispatch step carries two commands: the sub-agent's, inside the dispatch
prompt (`sub_agent_invoke()`), and the parent's, for after the sub-agent
returns, as `format_step`'s `next_cmd`.
