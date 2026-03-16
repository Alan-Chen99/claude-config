# Plan

## Overview

The alan-coding-style workflow has 4 gaps: reference files injected 8x per run (50% token waste), Step 3 generation lacks creative priming (no identity/stakes/voice summary), 3 of 13 AI voice patterns use prose metrics inapplicable to code, and Step 6 positive marker categories are abstract instead of grep-able.

**Approach**: Three milestones: M-001 adds creative priming to Step 3 (independent). M-002 restricts reference injection to Step 2 only and surfaces specific patterns into Step 6 (coupled P1+P4). M-003 replaces 3 prose-specific AI voice patterns with code-native equivalents. All changes are text edits to STEPS dict and ai-voice-removal.md, plus one condition change in get_step_guidance.

## Planning Context

### Decision Log

| ID | Decision | Reasoning Chain |
|---|---|---|
| DL-001 | Inject reference sections only at Step 2, not Steps 3-9 | Reference flooding causes 50% token waste across 8 steps -> --thoughts accumulation is assumed to carry rules forward (M-confidence, untested -- logged as R-001, R-002) -> changing condition in get_step_guidance from `if sections` to `if sections and step == 2` eliminates duplication while Step 5 ai-voice-removal injection (separate code path, lines 711-714) remains unaffected -> mitigated by direct pattern embedding in Step 3 (M-001), preserved Step 5 injection, and specific markers in Step 6 (M-002) |
| DL-002 | Add creative priming block to STEPS[3] following leon Step 3 pattern | Leon Step 3 has stakes + core_voice + structure_pattern + transitions that alan lacks -> weakly-primed first draft cascades into 5 verification steps checking suboptimal work -> adding code-domain equivalents (terse naming identity, assert-driven invariants, data-driven dispatch, step-back at generation time) primes the agent before generation |
| DL-003 | Replace 3 prose-specific AI voice patterns in ai-voice-removal.md with code-native equivalents | Patterns 6 (formula following), 9 (structural variance), 11 (sentence rhythm) use prose metrics (sentences per paragraph, word count per sentence) that have no code meaning -> replacing with code-native equivalents (function-shape variance, nesting-depth mix, cookie-cutter class detection) makes the patterns actionable for code review |
| DL-004 | Surface specific grep-able patterns from reference sections into STEPS[6] actions | Current Step 6 categories are abstract meta-descriptions ("Identifiers following conventions") -> reference flooding compensated by giving agent raw reference text -> with flooding removed (DL-001), agent loses reference material at Step 6 -> surfacing specific patterns (ans for return values, FRAG_OPTS registry pattern, assert for preconditions, walrus operator, constants at module top) into Step 6 makes extraction mechanical without needing raw references |
| DL-005 | Fix P1+P4 together as a single milestone, P2 and P3 as separate milestones | P1 removes reference flooding that P4 abstract markers partially depended on -> fixing P1 without P4 degrades positive pattern detection -> coupling them ensures no regression window; P2 and P3 are independent changes that can be verified separately |
| DL-006 | One-line change to get_step_guidance condition rather than per-step injection mapping | DL-006 constrains all fixes to text changes in STEPS dict, no handler function refactor -> a single condition change (step == 2) is the minimal handler touch that achieves inject-once behavior -> a per-step mapping would be a handler refactor violating DL-006 |

### Constraints

- MUST: P1 and P4 fixed together (removing flooding without specific markers degrades detection)
- MUST: All fixes as text changes to STEPS dict entries, no handler function refactor (DL-006)
- MUST: Step 5 always injects ai-voice-removal.md regardless of --sections (existing behavior, Lines 711-714)
- MUST NOT: Change TOTAL_STEPS, step IDs, or phase assignments (DL-001)
- MUST NOT: Expose file paths, CDATA, or implementation details in output (DL-003, DL-005)
- SHOULD: Follow recommended fix order: P2 first (independent), then P1+P4 (coupled), then P3 (independent)

### Known Risks

- **--thoughts accumulation may not reliably carry style rules from Step 2 forward without re-injection (M confidence, untested); Steps 3-9 could lose reference context and generate code ignoring naming/philosophy conventions**: Selective re-injection in Step 5 (ai-voice-removal) and Step 6 (specific markers) compensates for removed general flooding; creative priming in Step 3 embeds distilled patterns directly in the step text
- **Reference sections injected once in Step 2 may be insufficient for Steps 3-9 via thoughts alone (M confidence); quality regression possible in later steps that currently benefit from repeated reference injection**: Step 3 priming embeds core patterns directly; Step 5 retains ai-voice-removal injection; Step 6 surfaces specific grep-able patterns -- the three highest-leverage steps have explicit compensation
- **Selective re-injection in Step 5 and Step 6 may not fully compensate for removed flooding (H confidence); minor degradation in AI voice detection and positive marker extraction possible**: Step 5 ai-voice-removal.md injection is preserved (lines 711-714, unaffected by P1 fix); Step 6 gets specific patterns surfaced directly in STEPS dict text

## Invisible Knowledge

### System

HISTORY_TEMPLATE sections (7 categories) track accumulated context; --thoughts carries this between step invocations

### Invariants

- DL-006: All gap fixes must be text changes to STEPS dict -- no handler refactoring

### Tradeoffs

- Reference flooding partially compensates for abstract markers by giving the agent raw reference material to self-extract from; removing flooding (P1) without surfacing specific markers (P4) would degrade detection quality

## Milestones

### Milestone 1: Add creative priming to Step 3 (P2)

**Files**: skills/scripts/skills/alan_coding_style/coding_style.py, skills/scripts/tests/test_alan_coding_style.py

**Acceptance Criteria**:

- STEPS[3] actions text contains <stakes>, <core_coding_voice>, and <step_back_at_generation> blocks
- <core_coding_voice> lists 4 distilled identity patterns with code examples (terse naming, assert-driven invariants, data-driven dispatch, minimal abstraction)
- test_step3_has_creative_priming passes, asserting presence of the 3 XML blocks in STEPS[3]
- Existing tests continue to pass (no regressions in step content or CLI invocation)

#### Code Intent

- **CI-M-001-001** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[3]["actions"] contains a <stakes> block stating that this code represents Alan's coding identity and that the executing agent's output reflects Alan's engineering standards. Placed before the existing <apply_rules> block. (refs: DL-002)
- **CI-M-001-002** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[3]["actions"] contains a <core_coding_voice> block with 4 distilled identity patterns: (1) TERSE NAMING with code examples (ans, ctx, fn, single-letter vars), (2) ASSERT-DRIVEN INVARIANTS with code examples (assert isinstance, assert False), (3) DATA-DRIVEN DISPATCH with code examples (FRAG_OPTS pattern, ROUTES dict), (4) MINIMAL ABSTRACTION (direct implementation, no speculative wrappers). Placed after <stakes> and before <apply_rules>. (refs: DL-002)
- **CI-M-001-003** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[3]["actions"] contains a <step_back_at_generation> block with the same two meta-cognitive questions from Step 2 ("What makes Alan's coding style distinctive?" and "What would make this code obviously LLM-generated?") rephrased as generation-time reminders. This supplements (not replaces) the Step 2 step-back. (refs: DL-002)
- **CI-M-001-004** `skills/scripts/tests/test_alan_coding_style.py`: A new test test_step3_has_creative_priming asserts that STEPS[3] actions text contains "<stakes>", "<core_coding_voice>", and "<step_back_at_generation>". Follows the existing behavioral contract test pattern (e.g., test_step2_step_back_has_meta_cognitive_questions). (refs: DL-002)

#### Code Changes

**CC-M-001-005** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-001

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -236,6 +236,14 @@ def existing_function(ctx):
     3: {
         "id": "apply_style_rules",
         "phase": "GENERATION",
         "step_title": "Apply Style Rules",
         "actions": [
+            "<stakes>",
+            "This code represents Alan's coding identity.",
+            "The output produced here directly reflects Alan's engineering standards.",
+            "Generate code that Alan would recognize as his own -- not code that happens",
+            "to pass a style check.",
+            "</stakes>",
+            "",
             "IMPORTANT: Focus ONLY on your classified task type from Step 1.",
             "Ignore instructions for other task types.",
             "",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -236,6 +236,7 @@ def existing_function(ctx):
     3: {
         "id": "apply_style_rules",
         "phase": "GENERATION",
         "step_title": "Apply Style Rules",
         "actions": [
+            # Step 3 is IF/ELSE dispatch with no identity context without this block; stakes block establishes Alan identity before rule application so output is owned, not just compliant. (ref: DL-002)
             "<stakes>",

```


**CC-M-001-002** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-002

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -232,14 +232,45 @@ def existing_function(ctx):
     3: {
         "id": "apply_style_rules",
         "phase": "GENERATION",
         "step_title": "Apply Style Rules",
         "actions": [
             "<stakes>",
             "This code represents Alan's coding identity.",
             "The output produced here directly reflects Alan's engineering standards.",
             "Generate code that Alan would recognize as his own -- not code that happens",
             "to pass a style check.",
             "</stakes>",
             "",
+            "<core_coding_voice>",
+            "Four patterns that make Alan's code immediately recognizable:",
+            "",
+            "1. TERSE NAMING",
+            "   Return values: `ans`. Context params: `ctx`. Bound function: `fn`.",
+            "   Tight loop vars: f, b, v, r, n, k/v.",
+            "   Class names: Cfg, AuthSvc, TxnLog.",
+            "",
+            "2. ASSERT-DRIVEN INVARIANTS",
+            "   `assert isinstance(x, int)` guards preconditions.",
+            "   `assert False, 'unreachable'` marks dead branches.",
+            "   No defensive try/except around internal state.",
+            "",
+            "3. DATA-DRIVEN DISPATCH",
+            "   FRAG_OPTS = {'json': fmt_json, 'csv': fmt_csv}",
+            "   ROUTES = {'get': handle_get, 'post': handle_post}",
+            "   Registry dict + lookup instead of if/elif chains.",
+            "",
+            "4. MINIMAL ABSTRACTION",
+            "   Implement directly. No speculative wrappers or base classes.",
+            "   If the same logic appears twice, extract. Once: keep inline.",
+            "</core_coding_voice>",
+            "",
             "IMPORTANT: Focus ONLY on your classified task type from Step 1.",
             "Ignore instructions for other task types.",
             ""
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -244,6 +244,7 @@ def existing_function(ctx):
             "</stakes>",
             "",
+            # Four patterns distilled from reference sections — embedded here so Step 3 carries them without reference re-injection. (ref: DL-002)
             "<core_coding_voice>",

```


**CC-M-001-004** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-001-003

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -264,6 +264,17 @@ def existing_function(ctx):
             "  Minimize changes outside the fix.",
             "</apply_rules>",
             "",
+            "<step_back_at_generation>",
+            "Before producing output, ask yourself:",
+            "1. What makes Alan's coding style distinctive from generic clean code?",
+            "   (Terse names, assert guards, registry dispatch, no speculative abstractions)",
+            "2. What would make this code obviously LLM-generated?",
+            "   (Over-engineered names, excessive comments, defensive internal validation)",
+            "Write code that passes both tests.",
+            "</step_back_at_generation>",
+            "",
             "<output_expectations>",
             "GENERATE / REFACTOR / FIX: Output your draft code.",
             "REVIEW: Output your analysis notes with code references.",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -278,6 +278,7 @@ def existing_function(ctx):
             "  Minimize changes outside the fix.",
             "</apply_rules>",
             "",
+            # Repeats Step 2 meta-cognitive questions at generation time — supplements, does not replace, Step 2 step-back. (ref: DL-002)
             "<step_back_at_generation>",

```


**CC-M-001-007** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-001-004

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -210,6 +210,17 @@ def test_step2_step_back_has_meta_cognitive_questions():
     assert "LLM-generated" in actions_text
     assert "The applicable style guide sections are embedded below" not in actions_text
 
+
+# Step 3 creative priming blocks ensure the agent generates with identity and stakes before applying rules.
+def test_step3_has_creative_priming():
+    actions = STEPS[3]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "<stakes>" in actions_text
+    assert "<core_coding_voice>" in actions_text
+    assert "<step_back_at_generation>" in actions_text
+
+
 # Advisory language + advisory Step 8 produces zero consequences for WEAK assessment; test prevents regression to advisory form. (ref: DL-003)
 def test_step6_thresholds_are_binding():
```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -215,6 +215,7 @@ def test_step2_step_back_has_meta_cognitive_questions():
     assert "The applicable style guide sections are embedded below" not in actions_text


+# Creative priming blocks prime the agent with identity and stakes before rule application; absence cascades into weakly-styled generation output. (ref: DL-002)
 def test_step3_has_creative_priming():

```


### Milestone 2: Fix reference flooding and specific positive markers (P1+P4)

**Files**: skills/scripts/skills/alan_coding_style/coding_style.py, skills/scripts/tests/test_alan_coding_style.py

**Requirements**:

- M-001

**Acceptance Criteria**:

- get_step_guidance() injects section files only when step == 2; steps 3-9 no longer receive section content
- Step 5 ai-voice-removal.md injection (lines 711-714) remains unchanged and functional
- STEPS[6] actions text contains specific grep-able patterns: ans, ctx, FRAG_OPTS or registry, assert False, walrus, SCREAMING_SNAKE_CASE
- Each of the 5 STEPS[6] categories lists concrete code patterns instead of abstract descriptions
- test_step6_has_specific_marker_patterns passes, asserting presence of specific pattern strings
- Existing step 2 tests confirm section content is still injected at step 2

#### Code Intent

- **CI-M-002-001** `skills/scripts/skills/alan_coding_style/coding_style.py`: get_step_guidance() injects section files only when step == 2 (not for steps 3-9). The condition on line 706 changes from `if sections:` to `if sections and step == 2:`. The Step 5 ai-voice-removal injection (lines 711-714, condition `if step == 5:`) remains unchanged. (refs: DL-001, DL-006)
- **CI-M-002-002** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[6]["actions"] CATEGORY 1 (Naming Idioms) EXTRACT instruction lists specific patterns: uses of `ans` for return values, `ctx` for context parameters, single-letter vars in tight scopes (f, b, v, r, n, k/v), trailing underscore for shadowed builtins (break_, else_), terse class names (Cfg, AuthSvc, TxnLog). (refs: DL-004)
- **CI-M-002-003** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[6]["actions"] CATEGORY 2 (Architecture Patterns) EXTRACT instruction lists specific patterns: registry dicts (FRAG_OPTS, ROUTES, HANDLERS pattern), frozen dataclasses for value types, `assert` as invariant checks not defensive validation, `with` blocks for resource/state scoping, ordered function lists for pipelines. (refs: DL-004)
- **CI-M-002-004** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[6]["actions"] CATEGORY 3 (Error Handling) EXTRACT instruction lists specific patterns: `assert` for preconditions/postconditions, `assert False` for unreachable branches, terse lowercase error messages without trailing period, `raise ... from None` to suppress chains, validate at boundaries only. (refs: DL-004)
- **CI-M-002-005** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[6]["actions"] CATEGORY 4 (Language Idioms) EXTRACT instruction lists specific patterns: walrus operator in conditionals (`if i := x.check():`), comprehensions for single-expression transforms, f-strings exclusively (no .format or %), match/case for AST dispatch, pathlib.Path for file handling, contextlib.contextmanager usage. (refs: DL-004)
- **CI-M-002-006** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[6]["actions"] CATEGORY 5 (Code Organization) EXTRACT instruction lists specific patterns: constants at module top in SCREAMING_SNAKE_CASE, imports grouped standard/third-party/local, leading underscore for internal modules (_core.py, _api.py), section separators (####...####) in large files, no __all__, re-export facade with `as` aliases. (refs: DL-004)
- **CI-M-002-007** `skills/scripts/tests/test_alan_coding_style.py`: Existing test_cli_invocation_succeeds for steps >= 2: the assertion that section content (=== philosophy === or === naming ===) appears in stdout applies only to step 2. Steps 3-9 no longer receive injected section content. A new assertion confirms step 2 output contains section markers while step 3+ output does not. (refs: DL-001)
- **CI-M-002-008** `skills/scripts/tests/test_alan_coding_style.py`: A new test test_step6_has_specific_marker_patterns asserts that STEPS[6] actions text contains specific grep-able pattern strings: "ans", "ctx", "FRAG_OPTS" or "registry", "assert False", "walrus", and "SCREAMING_SNAKE_CASE" or "module top". Follows the behavioral contract test pattern. (refs: DL-004)

#### Code Changes

**CC-M-002-001** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-002-001

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -706,7 +706,7 @@ def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
     actions = list(step_data["actions"])
 
-    if sections:
+    if sections and step == 2:
         loaded = load_section_files(sections)
         section_blocks = [format_section_block(name, content) for name, content in loaded]
         actions = section_blocks + actions
 
     if step == 5:
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -706,6 +706,7 @@ def get_step_guidance(step: int, sections: list[str] | None = None) -> dict:
     actions = list(step_data["actions"])

+    # Reference sections inject at Step 2 only; Steps 3-9 carry rules via --thoughts accumulation. Step 5 ai-voice injection (step == 5, below) operates on a separate path. (ref: DL-001, DL-006)
     if sections and step == 2:

```


**CC-M-002-002** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-002-002

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -438,8 +438,14 @@ def existing_function(ctx):
             "CATEGORY 1: NAMING IDIOMS",
-            "  EXTRACT: Identifiers following Alan's naming conventions.",
-            "  COUNT: How many follow the pattern? Quote each.",
+            "  EXTRACT: Identifiers following these specific patterns:",
+            "    - `ans` for return-value variables",
+            "    - `ctx` for context parameters",
+            "    - single-letter vars in tight scopes (f, b, v, r, n, k, v)",
+            "    - trailing underscore for shadowed builtins (break_, else_)",
+            "    - terse class names (Cfg, AuthSvc, TxnLog)",
+            "  COUNT: How many found? Quote each identifier.",
             "",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -433,6 +433,7 @@ def existing_function(ctx):
             "<positive_patterns>",
             "VERIFICATION METHOD: Extract first, then assess sufficiency.",
             "Steps 4-5 check for ABSENCE of bad patterns.",
             "This step checks for PRESENCE of Alan's signature coding patterns.",
             "",
+            # Step 6 receives no reference file injection (Step 2 is the only injection point), so category patterns must be self-contained. (ref: DL-004)
             "CATEGORY 1: NAMING IDIOMS",

```


**CC-M-002-003** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-002-003

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -444,9 +444,14 @@ def existing_function(ctx):
             "CATEGORY 2: ARCHITECTURE PATTERNS",
-            "  EXTRACT: Structural patterns matching Alan's preferences.",
-            "  (module organization, dependency direction, design patterns used)",
-            "  COUNT: How many found? Quote each.",
+            "  EXTRACT: Structural patterns matching these specifics:",
+            "    - registry dicts (FRAG_OPTS, ROUTES, HANDLERS) for dispatch",
+            "    - frozen dataclasses for value types",
+            "    - `assert` as invariant checks, not defensive validation",
+            "    - `with` blocks for resource/state scoping",
+            "    - ordered function lists for pipelines",
+            "  COUNT: How many found? Quote each pattern.",
             "",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -444,6 +444,7 @@ def existing_function(ctx):
             "CATEGORY 2: ARCHITECTURE PATTERNS",
+            # Step 6 receives no reference file injection; detection targets are embedded inline so the agent does not depend on re-injected .md content. (ref: DL-004)
             "  EXTRACT: Structural patterns matching these specifics:",

```


**CC-M-002-004** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-002-004

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -450,9 +450,14 @@ def existing_function(ctx):
             "CATEGORY 3: ERROR HANDLING PATTERNS",
-            "  EXTRACT: Error handling matching Alan's conventions.",
-            "  (error propagation style, validation placement, recovery patterns)",
-            "  COUNT: How many found? Quote each.",
+            "  EXTRACT: Error handling matching these specifics:",
+            "    - `assert` for preconditions/postconditions",
+            "    - `assert False` for unreachable branches",
+            "    - terse lowercase error messages without trailing period",
+            "    - `raise ... from None` to suppress exception chains",
+            "    - validation at boundaries only (not in internal helpers)",
+            "  COUNT: How many found? Quote each.",
             "",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -450,6 +450,7 @@ def existing_function(ctx):
             "CATEGORY 3: ERROR HANDLING PATTERNS",
+            # Same rationale as Category 2 anchor (CC-M-002-003): inline patterns are required because Step 6 receives no reference file injection. (ref: DL-004)
             "  EXTRACT: Error handling matching these specifics:",

```


**CC-M-002-005** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-002-005

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -456,9 +456,14 @@ def existing_function(ctx):
             "CATEGORY 4: LANGUAGE IDIOMS",
-            "  EXTRACT: Language-specific patterns matching Alan's style.",
-            "  (e.g., Python: comprehensions vs loops, f-strings vs format;",
-            "   C#: LINQ patterns, async/await conventions)",
-            "  COUNT: How many found? Quote each.",
+            "  EXTRACT: Language-specific patterns matching these specifics:",
+            "    - walrus operator in conditionals (`if i := x.check():`)",
+            "    - comprehensions for single-expression transforms",
+            "    - f-strings exclusively (no .format or % formatting)",
+            "    - match/case for AST dispatch",
+            "    - pathlib.Path for file handling, contextlib.contextmanager usage",
+            "  COUNT: How many found? Quote each.",
             "",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -456,6 +456,7 @@ def existing_function(ctx):
             "CATEGORY 4: LANGUAGE IDIOMS",
+            # Same rationale as Category 2 anchor (CC-M-002-003): inline patterns are required because Step 6 receives no reference file injection. (ref: DL-004)
             "  EXTRACT: Language-specific patterns matching these specifics:",

```


**CC-M-002-006** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-002-006

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -462,9 +462,14 @@ def existing_function(ctx):
             "CATEGORY 5: CODE ORGANIZATION",
-            "  EXTRACT: File/module organization matching Alan's conventions.",
-            "  (import ordering, section grouping, constant placement)",
-            "  COUNT: How many found? Quote each.",
+            "  EXTRACT: Organization patterns matching these specifics:",
+            "    - constants at module top in SCREAMING_SNAKE_CASE",
+            "    - imports grouped: standard / third-party / local",
+            "    - leading underscore for internal modules (_core.py, _api.py)",
+            "    - section separators (####...####) in large files",
+            "    - re-export facade using `as` aliases (no __all__)",
+            "  COUNT: How many found? Quote each.",
             "</positive_patterns>",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -462,6 +462,7 @@ def existing_function(ctx):
             "CATEGORY 5: CODE ORGANIZATION",
+            # Same rationale as Category 2 anchor (CC-M-002-003): inline patterns are required because Step 6 receives no reference file injection. (ref: DL-004)
             "  EXTRACT: Organization patterns matching these specifics:",

```


**CC-M-002-007** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-002-007

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -254,7 +254,10 @@ def test_cli_invocation_succeeds(step):
     assert result.returncode == 0, f"Step {step} failed: {result.stderr[:300]}"
     assert "<step_header" in result.stdout
     # Output must not expose implementation details (file paths, CDATA) to agents (ref: DL-003, DL-005)
     assert "<style_references>" not in result.stdout
     assert "<\![CDATA[" not in result.stdout
-    if step >= 2:
-        assert "=== philosophy ===" in result.stdout or "=== naming ===" in result.stdout
+    if step == 2:
+        assert "=== philosophy ===" in result.stdout or "=== naming ===" in result.stdout
+    if step > 2:
+        assert "=== philosophy ===" not in result.stdout
+        assert "=== naming ===" not in result.stdout
```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -257,6 +257,7 @@ def test_cli_invocation_succeeds(step):
     assert "<style_references>" not in result.stdout
     assert "<![CDATA[" not in result.stdout
     if step == 2:
         assert "=== philosophy ===" in result.stdout or "=== naming ===" in result.stdout
+    # Steps > 2 must not receive section content — inject-once behavior; section presence indicates regression. (ref: DL-001)
     if step > 2:

```


**CC-M-002-008** (skills/scripts/tests/test_alan_coding_style.py) - implements CI-M-002-008

**Code:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -220,6 +220,18 @@ def test_step6_thresholds_are_binding():
     assert "PASS" in actions_text
     assert "FAIL" in actions_text
 
 
+# Step 6 positive marker categories must be grep-able so the agent can detect patterns
+# without re-injecting reference files (coupling with P1 fix -- DL-004, DL-005).
+def test_step6_has_specific_marker_patterns():
+    actions = STEPS[6]["actions"]
+    actions_text = "\n".join(str(a) for a in actions)
+    assert "ans" in actions_text
+    assert "ctx" in actions_text
+    assert ("FRAG_OPTS" in actions_text or "registry" in actions_text)
+    assert "assert False" in actions_text
+    assert "walrus" in actions_text
+    assert ("SCREAMING_SNAKE_CASE" in actions_text or "module top" in actions_text)
+
+
 # Consumer, Purpose, and Code Context feed later steps; omitting them collapses context-appropriate style checking to uniform rules. (ref: DL-004, DL-005)
 def test_step1_has_consumer_purpose_context_fields():
```

**Documentation:**

```diff
--- a/skills/scripts/tests/test_alan_coding_style.py
+++ b/skills/scripts/tests/test_alan_coding_style.py
@@ -220,6 +220,7 @@ def test_step6_thresholds_are_binding():


+# Step 6 categories carry specific grep-able patterns because Step 6 receives no reference file injection; detection cannot depend on re-injected .md content. (ref: DL-004)
 def test_step6_has_specific_marker_patterns():

```


**CC-M-002-009** (skills/alan-coding-style/README.md)

**Documentation:**

```diff
--- a/skills/alan-coding-style/README.md
+++ b/skills/alan-coding-style/README.md
@@ -93,3 +93,28 @@ These fields inform context-appropriate style checking in Steps 6 and later. Without
 them, every code artifact is checked against the same rules: test files get
 penalized for missing Architecture patterns they deliberately omit; CLI scripts get
 penalized for lacking organization structures irrelevant to scripts. The Code Context
 field drives Step 6 exemptions (test code skips Architecture and Organization;
 config/glue code skips Language Idioms; CLI scripts skip Architecture). (ref: DL-004,
 DL-005)
+
+### Why Reference Injection Is Restricted to Step 2
+
+`get_step_guidance` injects `--sections` reference files at Step 2 only. Steps
+3-9 rely on `--thoughts` accumulation to carry style rules forward. Injecting the same
+files at every step doubles context length without adding new information (8x duplication
+across a 9-step run). The condition is `step == 2` rather than per-step injection mapping
+because any handler-level change beyond a single condition change would constitute a
+refactoring of `get_step_guidance`, violating the constraint that fixes target STEPS dict text.
+Step 5 retains a separate `if step == 5:` block that unconditionally injects
+`ai-voice-removal.md` — this path is independent of `--sections` and runs unconditionally at Step 5.
+
+### Why P1 (Reference Flooding) and P4 (Abstract Positive Markers) Are Fixed Together
+
+Step 6 category descriptions require self-contained grep-able patterns because Step 6
+receives no reference file injection. Categories 2-5 embed specific patterns inline
+so the agent can detect positive markers without depending on reference material
+injected at Step 2. The two fixes — restricting injection to Step 2 and embedding
+specific patterns in Step 6 categories — ship together to prevent a
+state where injection is restricted but category descriptions remain abstract,
+degrading positive pattern detection.

```


### Milestone 3: Replace prose-specific AI voice patterns with code-native equivalents (P3)

**Files**: skills/alan-coding-style/references/ai-voice-removal.md, skills/scripts/skills/alan_coding_style/coding_style.py

**Requirements**:

- M-002

**Acceptance Criteria**:

- ai-voice-removal.md pattern 6 (formula following) uses code-structure analysis (cookie-cutter function shapes) instead of paragraph-structure analysis
- ai-voice-removal.md pattern 9 (structural variance) uses function-shape variance (line count, nesting depth, parameter count) instead of sentence-per-paragraph counting
- ai-voice-removal.md pattern 11 (sentence rhythm) uses line-complexity variance (SHORT/MEDIUM/LONG categorization) instead of word-count-per-sentence
- STEPS[5] adaptation table includes 3 additional entries mapping the replaced prose patterns to their code-native equivalents
- All 13 patterns in ai-voice-removal.md remain present (no deletions, only replacements of 3 patterns)

#### Code Intent

- **CI-M-003-001** `skills/alan-coding-style/references/ai-voice-removal.md`: Pattern 6 (formula following) replaces paragraph-structure analysis with code-structure analysis: detect if all functions follow identical shape (docstring -> validate -> process -> return), cookie-cutter class layouts, and repetitive method signatures. EXTRACT instruction asks for function signatures and body structures rather than paragraph structures. (refs: DL-003)
- **CI-M-003-002** `skills/alan-coding-style/references/ai-voice-removal.md`: Pattern 9 (structural variance) replaces sentence-per-paragraph counting with function-shape variance analysis: count lines per function, nesting depth per function, parameter count per function. FLAG if all functions have similar shape (all 5-10 lines, all flat, all same parameter count). PASS if mix includes short utility functions AND longer complex functions. (refs: DL-003)
- **CI-M-003-003** `skills/alan-coding-style/references/ai-voice-removal.md`: Pattern 11 (sentence rhythm) replaces word-count-per-sentence analysis with line-complexity variance analysis: categorize code lines as SHORT (single assignment, return, assert), MEDIUM (conditional, loop header, function call with args), LONG (complex expression, multi-clause comprehension, long string). FLAG if 90%+ lines are MEDIUM. PASS if mix includes SHORT and LONG. (refs: DL-003)
- **CI-M-003-004** `skills/scripts/skills/alan_coding_style/coding_style.py`: STEPS[5]["actions"] adaptation table (the 5-line substitution list at lines 411-416) adds 3 additional entries mapping the replaced patterns to their code-native equivalents: formula following -> cookie-cutter function shapes, structural variance -> function-shape variance (line count, nesting, params), sentence rhythm -> line-complexity mix (assignments vs expressions vs comprehensions). (refs: DL-003)

#### Code Changes

**CC-M-003-001** (skills/alan-coding-style/references/ai-voice-removal.md) - implements CI-M-003-001

**Code:**

```diff
--- a/skills/alan-coding-style/references/ai-voice-removal.md
+++ b/skills/alan-coding-style/references/ai-voice-removal.md
@@ -120,10 +120,15 @@ def existing_function(ctx):
 <pattern_6_formula>
-FORMULA FOLLOWING
-
-  EXTRACT: What is the structure of each paragraph?
-  (e.g., Statement -> Explanation -> Consequence)
-
-  JUDGE: Are all paragraphs structured identically?
-  Leon's writing varies. Some points just get stated.
-
-  Note if rhythm feels artificial: YES/NO + explanation.
+FORMULA FOLLOWING (CODE)
+
+  EXTRACT: What is the shape of each function?
+  (e.g., docstring -> validate -> process -> return)
+
+  JUDGE: Do all functions follow identical shape?
+  Also check: cookie-cutter class layouts, repetitive method signatures.
+
+  FLAG if: all functions have the same structure template.
+  PASS if: function shapes vary (some are one-liners, some are complex).
+
+  Note if structure feels templated: YES/NO + example.
 </pattern_6_formula>
```

**Documentation:**

```diff
--- a/skills/alan-coding-style/references/ai-voice-removal.md
+++ b/skills/alan-coding-style/references/ai-voice-removal.md
@@ -120,6 +120,7 @@ def existing_function(ctx):
+<!-- Pattern 6: prose paragraph-structure analysis has no code equivalent; function-shape analysis (docstring->validate->process->return) is the code-domain analog. -->
 <pattern_6_formula>

```


**CC-M-003-002** (skills/alan-coding-style/references/ai-voice-removal.md) - implements CI-M-003-002

**Code:**

```diff
--- a/skills/alan-coding-style/references/ai-voice-removal.md
+++ b/skills/alan-coding-style/references/ai-voice-removal.md
@@ -166,17 +166,20 @@ def existing_function(ctx):
 <pattern_9_structural_variance>
-STRUCTURAL MONOTONY
-
-  EXTRACT: Count sentences per paragraph
-    | Para # | Sentence Count |
-    | 1      | ?              |
-    | 2      | ?              |
-    | ...    | ...            |
-
-  JUDGE: What is the variance?
-    - Narrow (all 2-4 sentences): FLAG as monotonous
-    - Wide (includes 1-sentence AND 5+ sentence): PASS
-
-  REQUIRED: At least one paragraph that breaks the pattern
-    - One-liner (<= 1 sentence): 'That's the core idea.'
-    - Long block (>= 5 sentences): deep technical dive
-
-  If no variance, record:
-    | Issue | Range | Confidence |
-    | Structural monotony | 2-4 sentences | HIGH |
+STRUCTURAL MONOTONY (CODE)
+
+  EXTRACT: For each function, measure:
+    | Function | Lines | Nesting Depth | Param Count |
+    | name     | ?     | ?             | ?           |
+
+  JUDGE: What is the variance in function shape?
+    - Narrow (all functions 5-10 lines, all flat, all 1-3 params): FLAG
+    - Wide (includes short utilities AND longer complex functions): PASS
+
+  REQUIRED: Mix of function shapes
+    - Short utility (1-3 lines): pure transform, lookup
+    - Long complex (15+ lines): multi-branch logic, pipeline
+
+  If no variance, record:
+    | Issue | Range | Confidence |
+    | Function shape monotony | 5-10 lines all | HIGH |
 </pattern_9_structural_variance>
```

**Documentation:**

```diff
--- a/skills/alan-coding-style/references/ai-voice-removal.md
+++ b/skills/alan-coding-style/references/ai-voice-removal.md
@@ -166,6 +166,7 @@ def existing_function(ctx):
+<!-- Pattern 9: sentence-per-paragraph counting has no code equivalent; function-shape variance (lines, nesting, params) is the code-domain analog. -->
 <pattern_9_structural_variance>

```


**CC-M-003-003** (skills/alan-coding-style/references/ai-voice-removal.md) - implements CI-M-003-003

**Code:**

```diff
--- a/skills/alan-coding-style/references/ai-voice-removal.md
+++ b/skills/alan-coding-style/references/ai-voice-removal.md
@@ -214,24 +214,27 @@ def existing_function(ctx):
 <pattern_11_sentence_rhythm>
-SENTENCE RHYTHM VARIANCE
-
-  EXTRACT: Categorize sentences by word count
-    SHORT (<8 words): punchy emphasis
-      - 'That's not a good sign.'
-      - 'Sigh.'
-      - 'This is wrong.'
-    MEDIUM (8-20 words): standard prose
-    LONG (>20 words): complex technical explanations
-
-  COUNT per category:
-    | Category | Count | Example Quote |
-    | Short    | ?     | '...'         |
-    | Medium   | ?     | '...'         |
-    | Long     | ?     | '...'         |
-
-  JUDGE: Is there variety?
-    FLAG if: 90%+ sentences in single category (typically medium)
-    PASS if: Mix includes at least one SHORT and one LONG
-
-  BONUS CHECK: Questions and exclamations
-    EXTRACT: Any sentences ending in ? or \!
-    For narrative content: at least one question adds engagement
-      - 'So how do we fix this?'
-      - 'Victory\!'
-
-  If no variance, record:
-    | Issue | Breakdown | Confidence |
-    | Uniform rhythm | 95% medium | HIGH |
+LINE COMPLEXITY VARIANCE (CODE)
+
+  EXTRACT: Categorize code lines by complexity
+    SHORT: single assignment, return, assert
+      - `ans = x + 1`
+      - `return ans`
+      - `assert cond`
+    MEDIUM: conditional, loop header, function call with args
+    LONG: complex expression, multi-clause comprehension, long string
+
+  COUNT per category:
+    | Category | Count | Example |
+    | Short    | ?     | '...'   |
+    | Medium   | ?     | '...'   |
+    | Long     | ?     | '...'   |
+
+  JUDGE: Is there variety in line complexity?
+    FLAG if: 90%+ lines are MEDIUM complexity
+    PASS if: Mix includes SHORT (assignments, returns) and LONG (comprehensions)
+
+  If no variance, record:
+    | Issue | Breakdown | Confidence |
+    | Uniform line complexity | 95% medium | HIGH |
 </pattern_11_sentence_rhythm>
```

**Documentation:**

```diff
--- a/skills/alan-coding-style/references/ai-voice-removal.md
+++ b/skills/alan-coding-style/references/ai-voice-removal.md
@@ -214,6 +214,7 @@ def existing_function(ctx):
+<!-- Pattern 11: word-count-per-sentence has no code equivalent; line-complexity variance (SHORT/MEDIUM/LONG) is the code-domain analog. -->
 <pattern_11_sentence_rhythm>

```


**CC-M-003-004** (skills/scripts/skills/alan_coding_style/coding_style.py) - implements CI-M-003-004

**Code:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -411,7 +411,10 @@ def existing_function(ctx):
             "Adapt each pattern to CODE context:",
             "  - 'sentences' -> lines of code, comments, docstrings",
             "  - 'paragraphs' -> functions, classes, modules",
             "  - 'quotes/references' -> imports, dependencies, naming patterns",
             "  - 'structural monotony' -> cookie-cutter function/class shapes",
             "  - 'meta-commentary openers' -> meta-docstrings describing what follows",
+            "  - 'formula following' -> cookie-cutter function shapes (docstring->validate->process->return)",
+            "  - 'structural variance' -> function-shape variance (line count, nesting depth, param count)",
+            "  - 'sentence rhythm' -> line-complexity mix (assignments vs expressions vs comprehensions)",
             "",
```

**Documentation:**

```diff
--- a/skills/scripts/skills/alan_coding_style/coding_style.py
+++ b/skills/scripts/skills/alan_coding_style/coding_style.py
@@ -411,6 +411,7 @@ def existing_function(ctx):
             "Adapt each pattern to CODE context:",
             "  - 'sentences' -> lines of code, comments, docstrings",
             "  - 'paragraphs' -> functions, classes, modules",
             "  - 'quotes/references' -> imports, dependencies, naming patterns",
             "  - 'structural monotony' -> cookie-cutter function/class shapes",
             "  - 'meta-commentary openers' -> meta-docstrings describing what follows",
+            # Prose-specific patterns (formula following, structural variance, sentence rhythm) have no code equivalent; entries map prose pattern names to their code-domain analogs so Step 5 adaptation guidance stays current.
             "  - 'formula following' -> cookie-cutter function shapes (docstring->validate->process->return)",

```


## Execution Waves

- W-001: M-001
- W-002: M-002
- W-003: M-003
