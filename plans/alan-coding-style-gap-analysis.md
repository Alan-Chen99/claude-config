# alan-coding-style Gap Analysis vs leon_writing_style

Comparative analysis of script output only (internal implementation out of scope).

## Confirmed Gaps (ranked by impact)

### 1. No Loop-Back Mechanism — CRITICAL

Leon Step 9 has explicit binary stopping criteria ("ALL must be true") and continue
criteria ("ANY triggers re-refinement"). Alan Step 8 (lines 633-637) actively undermines
its own checklist: "If any checkbox would be [ ] instead of [x]: Note remaining issues
in your delivery." The verification pipeline becomes advisory rather than enforcing.

**Fix:** Add Step 9 with stopping criteria. If HIGH-confidence violations remain or
positive markers are WEAK/MINIMAL, loop back to Step 8.

### 2. Cargo-Culted Step-Back Principles — HIGH

Leon Step 3 has genuine meta-cognitive priming: "What makes Leon's voice distinctive?"
and "What would make this AI-generated?" Alan Step 2 has a `<step_back_principles>` tag
containing purely procedural content ("The applicable style guide sections are embedded
below..."). The tag name was borrowed without the substance.

**Fix:** Add real step-back questions: "What makes Alan's coding style distinctive from
generic clean code?" and "What would make this obviously LLM-generated code?"

### 3. Advisory Thresholds Instead of Gates — HIGH

Leon uses binding language: "≥3 markers required" → PASS/FAIL. Alan Step 6 (line 459)
labels its thresholds "advisory, not hard gates" with "~" prefixes. The LOC-based
thresholds themselves are good, but the advisory language tells the agent it's okay to
proceed regardless. Combined with gap #1, a WEAK assessment has zero consequences.

**Fix:** Remove "advisory, not hard gates". Use "≥" instead of "~". WEAK/MINIMAL must
trigger mandatory re-work.

### 4. No Style-Context Alignment Step — MEDIUM

Leon Step 6 verifies voice matches content type per section. Alan applies uniform style
checks regardless of code context. Code has different contexts: production library vs
test code vs CLI scripts vs API handlers. Each warrants different style rigor.

**Fix:** Add a verification sub-check validating style-to-context alignment. Extend
Step 1 classification with a code-context field.

### 5. No Consumer/Purpose Analysis — MEDIUM (partial)

Leon Step 2 asks: WHO reads this? WHY does it exist? Alan classifies task type but not
code consumers. The code equivalent: who calls this code? (teammates via internal module,
external users via public API, CI via test suite). Hook drafting and reference register
are prose-specific acceptable omissions.

**Fix:** Add to Step 1 classification: `| Consumers | internal / public-API / CLI / test |`
and `| Purpose | one-sentence description |`.

### 6. No Content-Type-Driven Verification Exemptions — LOW-MEDIUM

Leon exempts instructional/reference sections from positive marker checks. Alan applies
all checks uniformly. Test files and config don't need positive pattern assessment the
same way production code does.

**Fix:** Add exemptions to Step 6: "For test code: skip Architecture and Organization.
For config/glue: skip Language Idioms."

## Debunked Gaps (initially suspected, verified as false)

| Suspected Gap | Reality |
|---|---|
| Cross-check lacks false positive re-examination | Has it — Step 7, lines 523-524 |
| No named refinement patterns | Has 5 — Step 8, lines 559-598 |
| Final checklist not granular | 17 checkboxes across 3 sections |
| No quantitative thresholds | Has LOC-based thresholds (but advisory language weakens them) |

## Summary

| Priority | Gap | Fix Effort |
|---|---|---|
| P1 | Add loop-back / quality gate (Step 9) | New step |
| P2 | Add real step-back principles to Step 2/3 | ~5 lines |
| P3 | Remove "advisory" language from thresholds | ~3 lines |
| P4 | Add style-context alignment check | New sub-check or step |
| P5 | Add consumer/purpose to classification | ~3 lines |
| P6 | Add verification exemptions by code type | ~5 lines |

**Key takeaway:** The gap between "having a feature" and "enforcing a feature" is where
alan-coding-style loses the most. It has thresholds, checklists, and verification — but
labels them advisory, tells the agent to deliver anyway, and never loops back. The
`<step_back_principles>` cargo-culting is a textbook example of adapting form without
function.
