# alan-coding-style Gap Analysis v2: DeepThink Evaluation

Comparative analysis of script **output only** (internal implementation out of scope).
Evaluates current state of alan-coding-style vs leon_writing_style after prior v1 fixes.

## Prior Gap Status

The v1 gap analysis identified 6 gaps. Current status:

| v1 Gap | Status | Evidence |
|--------|--------|----------|
| P1: No loop-back / quality gate | FIXED | Step 9 exists with STOP/CONTINUE criteria |
| P2: Cargo-culted step-back principles | FIXED | Step 2 has genuine meta-cognitive questions |
| P3: Advisory thresholds | FIXED | Step 6 uses `>=` and PASS/FAIL verdicts |
| P4: No style-context alignment | PARTIAL | Exemptions exist but no dedicated alignment check step |
| P5: No consumer/purpose analysis | FIXED | Step 1 classification includes Consumers and Purpose |
| P6: No verification exemptions | FIXED | Step 6 has test/config/CLI exemptions |

Gap P4 remains partially open: alan has exemptions by code context in Step 6 but no
dedicated step verifying that style rules match code context. Leon has a full Step 6
(Voice-Content Alignment) that cross-checks voice against content type per section.

---

## New Findings (ranked by impact)

### 1. Reference Flooding — CRITICAL (NEW)

alan injects the full text of selected reference `.md` files into every step's
`<current_action>` from Step 2 onward. The same philosophy.md and naming.md content
appears byte-identically 8 times across a workflow run.

**Quantitative measurement (--sections philosophy,naming):**

| Step | Total Lines | Ref Lines | Step-Specific Lines | Ref % (by chars) |
|------|-------------|-----------|---------------------|------------------|
| 2    | 138         | 73        | 65                  | 64.3%            |
| 3    | 147         | 73        | 74                  | 64.5%            |
| 4    | 225         | 73        | 152                 | 43.5%            |
| 5    | 439         | 97        | 342                 | 30.0%            |
| 6    | 174         | 73        | 101                 | 54.4%            |
| 7    | 158         | 73        | 85                  | 59.1%            |
| 8    | 171         | 73        | 98                  | 53.8%            |
| 9    | 124         | 74        | 50                  | 70.5%            |
| **TOTAL** | **1,576** | **609** | **967**          | **50.4%**        |

**Scaling to realistic usage (7 sections, typical GENERATE task):**

| Metric                          | alan (2 sections) | alan (7 sections) | leon |
|---------------------------------|-------------------|-------------------|------|
| Reference material per step     | 64% of output     | 84% of output     | 0%   |
| Wasted tokens per full run      | ~6,800            | ~19,900           | 0    |
| Step-specific guidance per step | 36% of output     | 16% of output     | 100% |

Leon inlines relevant guidance directly into each step's prompt at authoring time.
Zero file injection, zero duplication.

**Why this matters:**
1. Input token cost: billed 8x for content that could be read once
2. Context window pressure: displaces useful step-specific content
3. Attention dilution: agent re-reads unchanged reference material on every step

The injection may serve a re-grounding purpose (refreshing agent awareness of style
rules per step). This benefit is vastly outweighed by the token cost. Better approach:
inject fully in Step 2, carry key rules via `--thoughts`, inject in later steps only
where a specific section is needed (e.g., `ai-voice-removal` in Step 5 only).

**Fix:** Architectural change to injection strategy. Load references once in Step 2
("Style Rule Retrieval"), then rely on `--thoughts` accumulation to carry forward.
Re-inject selectively where step-specific sections are needed.

---

### 2. Generation Step Lacks Creative Priming — HIGH (NEW)

alan Step 3 is a procedural dispatcher:

```
IF GENERATE:
  Write code following every applicable rule.
  Name things according to naming conventions.
  Structure according to architecture patterns.
  Handle errors per error handling conventions.
  Use language-specific idioms.
```

leon Step 3 has 5 priming elements alan entirely lacks:

| Element                        | leon Step 3                                                        | alan Step 3 |
|--------------------------------|--------------------------------------------------------------------|-------------|
| Stakes statement               | "This represents Leon's public voice. Quality matters."            | Missing     |
| Core voice summary             | 4 patterns: confident authority, first-person, sardonic, pragmatic | Missing     |
| Structure template             | 6-step progression (hook -> context -> deep dive -> ...)           | Missing     |
| Transition guidance            | Specific phrases to use/avoid                                      | Missing     |
| Step-back at generation time   | "What would make this sound AI-generated?"                         | Only at Step 2 (one step too early) |

The cascade effect: a weakly-primed first draft means all 5 subsequent verification
steps are checking suboptimal work. The agent has the rules available (via reference
injection) but is not primed with identity, voice, or stakes before generating.

Having rules available is not the same as being primed to generate in character.

**Fix:** Add a `<core_coding_voice>` block to Step 3 with Alan's distilled identity:
- Terse naming, domain abbreviations expected
- Assert-driven invariants, not defensive validation
- Data-driven dispatch over if/elif chains
- Minimal abstraction, direct implementation

Add a stakes statement. Move step-back principles to Step 3 in addition to Step 2.
Effort: ~20 lines of step-specific content.

---

### 3. AI Voice Domain Adaptation Is Surface-Level — HIGH (PERSISTS)

alan Step 5 imports leon's 13 prose AI-tell patterns verbatim, then adapts with a
5-line term substitution table:

```
Adapt each pattern to CODE context:
  - 'sentences' -> lines of code, comments, docstrings
  - 'paragraphs' -> functions, classes, modules
  - 'quotes/references' -> imports, dependencies, naming patterns
  - 'structural monotony' -> cookie-cutter function/class shapes
  - 'meta-commentary openers' -> meta-docstrings describing what follows
```

The `<scope>` block (listing 7 code artifact types to examine) is well-done.
The gap is showing **what violations look like**, not where to look.

**Pattern-by-pattern assessment:**

| Category | Patterns (count) | Current Status |
|----------|-----------------|----------------|
| Applicable to code prose (comments, docstrings, error msgs, log stmts) | ~9-10: tricolons, contrarian openers, dead metaphors, hollow emphasis, callbacks, euphemism, grounded openers, repetition, overjustification | Detection logic works but needs supplementary code-domain WRONG/RIGHT examples |
| Fundamentally prose-specific | ~3: structural variance (sentence count per paragraph), sentence rhythm (word count per sentence), formula following (paragraph structure) | Need complete restructuring — prose metrics don't map to code artifacts |
| Edge-case | ~1: mixed register | Theoretically applicable but extremely rare in code comments |

The 3 prose-specific patterns rely on metrics like "count sentences per paragraph"
and "<8 words = SHORT sentence" which have no code-domain equivalent. These need
replacement with code-native equivalents:
- Structural variance -> function-shape variance (not all functions same length/structure)
- Sentence rhythm -> nesting-depth variance, line-length mix
- Formula following -> cookie-cutter class/method structure detection

**Fix:** Two-part:
1. Add code-domain WRONG/RIGHT examples for the ~10 applicable patterns
   (e.g., tricolon in a docstring, hollow emphasis in an error message)
2. Replace 3 prose-specific patterns with code-native equivalents

---

### 4. Positive Marker Categories Are Abstract — MEDIUM (PARTIALLY NEW)

alan Step 6 categories vs leon Step 5 categories:

| alan Step 6 (code)                                 | leon Step 5 (prose)                             |
|----------------------------------------------------|-------------------------------------------------|
| "Identifiers following Alan's naming conventions"  | "Sentences opening with: 'So,' or 'So '"        |
| "Structural patterns matching Alan's preferences"  | "Any 'X? Well,' or 'X? Y:' constructions"       |
| "Error handling matching Alan's conventions"       | "'Sigh.', 'of course!'"                          |
| "Language-specific patterns matching Alan's style" | "'The astute reader will notice...'"             |

Leon's categories are grep-able literal strings an agent can mechanically search for.
Alan's categories describe what "good" looks like at a meta-level without naming
specific extractable patterns.

**What specific markers COULD look like:**

| Category | Abstract (current) | Specific (proposed) |
|----------|--------------------|---------------------|
| Naming Idioms | "Identifiers following conventions" | "Uses of `ans` for return values, `ctx` for context, single-letter vars in tight scopes, trailing underscore for shadowed builtins" |
| Architecture | "Structural patterns matching preferences" | "Registry dicts (`FRAG_OPTS` pattern), frozen dataclasses for value types, `assert` as invariant checks, `with` blocks for scope" |
| Language Idioms | "Language-specific patterns" | "Walrus operator in conditionals, comprehensions over short transforms, f-strings over `.format()`" |
| Error Handling | "Error handling conventions" | "`assert` for preconditions/postconditions, `assert False` for unreachable, validate at boundaries only" |
| Organization | "Code organization conventions" | "Constants at module top, imports grouped standard/third-party/local, `_` prefix for internal" |

**Ironic interaction with Finding #1:** Reference flooding partially compensates for
this gap. The agent sees specific patterns in the injected reference sections even
though the extract instructions are abstract. If flooding is fixed (Finding #1),
marker specificity becomes critical because the agent will no longer have the raw
reference material available at Step 6. **Findings #1 and #4 must be fixed together.**

**Fix:** Surface specific extractable patterns from the reference sections into the
Step 6 extract instructions. Effort: ~15 lines.

---

## What alan Does Well (Appropriate Adaptations)

These are features where alan correctly adapts for code domain or innovates beyond leon:

| Feature | Detail |
|---------|--------|
| Running tally (Step 4) | "Patterns completed: N/6 \| Violations found: M" -- leon lacks this |
| Numbered priority system (Step 7) | P1-P7 ordering is more deterministic than leon's unnumbered rules |
| Richer classification table (Step 1) | 6 fields (task type, language, scope, consumers, purpose, code context) vs leon's 3 |
| Context accumulation template | Tracks 7 sections (more than leon's 6), separates AI voice from standard violations |
| Verification exemptions by code context | test/config/CLI exemptions in Step 6 -- leon has no equivalent |
| Invoke parameterization (--sections) | Justified design choice for 14-section reference library |
| Task-type dispatch (Step 3) | GENERATE/REVIEW/REFACTOR/FIX routing is appropriate for code (leon has no equivalent) |

---

## Fix Priority and Coupling

| Priority | Finding | Severity | Fix Effort | Dependencies |
|----------|---------|----------|------------|--------------|
| P1 | Reference flooding | CRITICAL | Architectural change | Must fix with P4 |
| P2 | Generation step priming | HIGH | ~20 lines new content | Independent |
| P3 | AI voice domain adaptation | HIGH | ~3 patterns restructure + ~10 need examples | Independent |
| P4 | Positive marker abstraction | MEDIUM | ~15 lines | Must fix with P1 |

**Critical coupling:** P1 and P4 must be fixed together. Removing reference flooding
without making markers specific will degrade positive pattern detection (the agent
will no longer have raw reference material to self-extract from at Step 6).

**Recommended fix order:** P2 (independent, quick win) -> P1+P4 (coupled, architectural)
-> P3 (independent, medium effort).

---

## Methodology

- Captured full 9-step output from both skills via direct script invocation
- Quantitative token measurement: line counts, character ratios, per-step breakdowns
- Three-perspective analysis: token economy, verification rigor, prompt engineering quality
- Two rounds of self-critique with independent verification questions
- All findings evidence-grounded in captured script output

**Limitation:** Analysis evaluates output quality by inspection, not by measuring actual
agent compliance rates. Real-world impact ranking is inferred from prompt engineering
principles, not empirical measurement.
