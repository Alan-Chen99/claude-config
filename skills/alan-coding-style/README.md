# Alan Coding Style

Style-matched code generation and review. The skill orchestrates a 9-step
workflow (classify -> retrieve rules -> apply -> detect anti-patterns -> AI voice
removal -> check positive patterns -> consolidate -> refine -> quality gate) driven by
`coding_style.py`. Style guide sections in `references/*.md` are loaded at
runtime and injected as labeled plain text into step guidance.

## Invisible Knowledge

### Why "Always Apply, Never Fall Back to Generic"

The style guide must produce Alan-style code even in domains far from the
compiler reference (web APIs, data pipelines, CLI tools). Every rule needs
enough context and multi-domain examples that an agent can extrapolate
confidently. If a situation isn't covered, the agent should adapt the nearest
principle — not revert to PEP-8 defaults or generic LLM style.

This matters because LLMs have strong priors toward verbose, PEP-8-compliant
code. Without explicit reinforcement and multi-domain examples, agents silently
fall back to generic style the moment they leave the compiler domain. The
Portability Guide section classifies rules as ALWAYS/PYTHON-SPECIFIC/ADAPT/REFERENCE
so agents know which to apply verbatim vs. adapt to new contexts.

### Why Prompt-Engineering Friendly (Concrete Decision Procedures)

Rules are written as concrete decision procedures, not vague preferences.
Contrastive pairs (WRONG/RIGHT) anchor each pattern. Decision Thresholds give
numeric/structural criteria (e.g. ">=3 call sites -> extract") so agents don't
have to guess.

This matters because vague rules ("keep functions small", "use good names")
produce inconsistent results across agent invocations. Concrete thresholds and
contrastive examples reduce variance — agents can pattern-match rather than
interpret.

### Why Section-Based Loading

Style guide content lives in `references/*.md` (one file per `## Section`) and is
loaded selectively via `--sections`. Step 1 prompts the LLM to select sections
based on task type; the selected sections are passed to `get_step_guidance`, which
loads the files and injects them as labeled plain text blocks into the step's
`current_action` output. Implementation details (file paths, CDATA markers) remain
invisible to executing agents. This keeps context windows focused — a naming
review doesn't need architecture patterns. Adding a section requires a new `.md`
file and an entry in `SECTION_TO_FILE` in `coding_style.py`.

### Why a Quality Gate at Step 9 Instead of Advisory Step 8 Checklist

Without a hard gate, verification becomes decorative: Step 8 previously said "note
remaining issues in your delivery," which means a WEAK assessment had zero
consequences. Step 9 introduces stopping/continue criteria (STOP when zero
HIGH-confidence violations remain and positive markers >= threshold; CONTINUE by
increasing `total_steps` when any violation remains). The `format_output`
`is_complete` check (`step >= WORKFLOW.total_steps`) always shows WORKFLOW COMPLETE
at Step 9 because the loop operates at the prompt level: the agent re-invokes
Step 9 on continuation, re-evaluating stopping criteria each time. (ref: DL-001,
DL-007, DL-008)

### Why Step-Back Principles Use Meta-Cognitive Questions Not Procedural Lists

Step 2 uses Step-Back Prompting (Zheng et al., 2023). A procedural list ("identify
which rules apply based on sections below") answers the question before it is
asked, collapsing the technique to a no-op. The two questions ("What makes Alan's
coding style distinctive?" and "What would make this code obviously LLM-generated?")
prime the agent to retrieve first principles before applying rules. (ref: DL-002)

### Why HISTORY_TEMPLATE Skips Step 8

Steps 2-7 and 9 accumulate context via `HISTORY_TEMPLATE`. Step 8 (`refine_deliver`)
does not because it is a final checklist that operates on the fully accumulated
context, not an intermediate accumulation step. Including `HISTORY_TEMPLATE` in
Step 8 would duplicate context already present and confuse the loop-back trigger.
(ref: DL-009)

### Why Thresholds Use >= Not ~

Advisory thresholds with `~` prefix combined with an advisory Step 8 checklist
mean a WEAK positive-pattern assessment produces no enforcement action. Replacing
`~` with `>=` and adding a PASS/FAIL verdict (`WEAK/MINIMAL -> FAIL, record as HIGH
priority violation for Step 7`) ensures WEAK assessments are treated as violations
that trigger the Step 9 quality gate. (ref: DL-003)

### Why Step 1 Classification Includes Consumers, Purpose, and Code Context

These fields inform context-appropriate style checking in Steps 6 and later. Without
them, every code artifact is checked against the same rules: test files get
penalized for missing Architecture patterns they deliberately omit; CLI scripts get
penalized for lacking organization structures irrelevant to scripts. The Code Context
field drives Step 6 exemptions (test code skips Architecture and Organization;
config/glue code skips Language Idioms; CLI scripts skip Architecture). (ref: DL-004,
DL-005)

### Why Reference Injection Is Restricted to Step 2

`get_step_guidance` injects `--sections` reference files at Step 2 only. Steps
3-9 rely on `--thoughts` accumulation to carry style rules forward (M-confidence assumption; not empirically validated -- see R-001, R-002 in `plans/alan-coding-style-v2-fixes.md` Decision Log). Injecting the same
files at every step doubles context length without adding new information (8x duplication
across a 9-step run). The condition is `step == 2` rather than per-step injection mapping
because any handler-level change beyond a single condition change would constitute a
refactoring of `get_step_guidance`, violating the constraint that fixes target STEPS dict text.
Step 5 retains a separate `if step == 5:` block that unconditionally injects
`ai-voice-removal.md` -- this path is independent of `--sections` and runs unconditionally at Step 5.

### Why P1 (Reference Flooding) and P4 (Abstract Positive Markers) Are Coupled

Step 6 category descriptions require self-contained grep-able patterns because Step 6
receives no reference file injection. Categories 2-5 embed specific patterns inline
so the agent can detect positive markers without depending on reference material
injected at Step 2. The two behaviors -- restricting injection to Step 2 and embedding
specific patterns in Step 6 categories -- are coupled: removing injection without updating category descriptions degrades positive pattern detection, and vice versa.
