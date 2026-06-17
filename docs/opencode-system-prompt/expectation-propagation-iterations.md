# Expectation-propagation iteration log

Records the iteration history of the expectation-propagation invariant
in `opencode/agents/alan-default.md`. The invariant is defined in
`prompt-tests/CLAUDE.md` ("### expectation-propagation"). Probed by
`prompt-tests/general/{trivial-task, platform-portability,
network-resilience}`.

Each version's change is justified by trial data from the prior version,
per the `prompt-tests/CLAUDE.md` "implicit guidance justification" rule.
All trials run with opencode under `--pure` (plugin-off) at n=1 per case
per version; grades reflect grader-only criteria in each case's
`reference-solution.md`.

## Current state (v13)

Body section `## Expectation propagation` in `alan-default.md`: unchanged
from v12. Shortened form (174 words, down from v11's 252) adopted from
the A18 ablation variant. P1 keeps the load-bearing pair "must" +
"framed as" identified by the ablation below; P2 and P3 use the
shortened transition-prose forms.

Gate template (heredoc body) in `alan-default.md` step 5: SHRUNK in v13
to `# Task` + `# Output Draft` only. The plausibly-wrong and
expectation-propagation directives that v10–v12 carried as heredoc body
sections are now emitted by `agent-tools opencode.gate` itself as
`GATE_STDOUT` (constant in `agent-tools/src/main.rs`). The agent prompt
references this stdout in step 5 ("Its stdout returns instructions you
must reason about") and step 6 ("After the gate stdout arrives, reason
in a thinking block about what it instructs").

GATE_STDOUT carries two-section content equivalent to v10–v12's heredoc
sections, plus three v13 alterations:

- **Singular-framing dropped.** v10's "the biggest violation, list at
  least one specific case" caps enumeration at one disclosure. v13:
  "Enumerate plausible adjacent attempts ... Adjacent-attempt axes vary
  across input shape, scale, environment, and failure mode; do not stop
  at the first concern that surfaces — reason across axes." Multi-axis
  enumeration with no cap.

- **Acceptable-self-classification dropped.** v10's "Then answer
  whether this is acceptable" provides an in-place dismissal path that
  the v10–v12 RED baselines showed agents taking — `prompt-edit-scope`
  baseline (`docs/opencode-system-prompt/baselines/prompt-edit-scope.md`)
  has the agent typing "This is acceptable for a concise system prompt"
  inside the heredoc and dropping the disclosure. v13: "Do not
  self-classify any concern as acceptable and drop it; if the user
  might plausibly hit it, the final response must name it."

- **No-sponge clause added.** To preserve `trivial-task` regression
  guard (fully-specified spec must not produce fabricated disclosures):
  "If the analysis surfaces no actionable disclosure, the final
  response does NOT include sponge prose; absence is the correct
  outcome when no plausible adjacent attempt is undisclosed."
  Balanced with explicit user-instruction precedence: "These
  directives are subject to explicit user instructions to the
  contrary (no caveats, brevity)."

## Results

| Version | Body change                                                                                                                              | Gate change                                          | trivial-task | platform-portability | network-resilience |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------ | -------------------- | ------------------ |
| v7      | minimal invariant ("deliver against implicit expectations")                                                                              | "is the invariant satisfied?"                        | PASS         | FAIL                 | FAIL               |
| v8      | + "adjacent attempts" framing + "user discovers failure by hitting it"                                                                   | unchanged                                            | PASS         | FAIL                 | FAIL               |
| v9      | + "even if the wording didn't name it" + "silence is not disclosure (reader can't distinguish)"                                          | unchanged                                            | ACCEPTABLE   | PASS                 | borderline-FAIL    |
| v10     | unchanged                                                                                                                                | "biggest violation + one case + is it acceptable?"   | PASS         | PASS                 | borderline-FAIL    |
| v11     | + "user action and observable outcome (not implementation-feature gap)" + cross-domain examples (debugging state-leak, refactor TypeError) | unchanged                                            | PASS         | PASS                 | ACCEPTABLE         |
| v13     | unchanged from v12 (shortened A18 form)                                                                                                  | directives relocated from heredoc body to gate stdout; singular framing dropped; acceptable-self-classification dropped; no-sponge clause added | borderline-FAIL  | STRONG PASS          | PASS               |

| Version | coverage-disclosure | prompt-edit-scope | pydantic-forward-ref |
| ------- | ------------------- | ----------------- | -------------------- |
| v12 RED | FAIL (1 non-tier-1) | FAIL (0 of R/S/C/V) | n/a (case unchanged) |
| v13     | PASS (3+ tier-1)    | PASS (3 of R/S/C/V) | STRONG PASS         |

## Session IDs

### v7 (prerequisite experiment)

- trivial-task PASS: `ses_1707253ebffeoB4mxPxU3pBa31`
- platform-portability FAIL: `ses_17072539affemWpJnVPzlKaRqQ`
- network-resilience FAIL: `ses_170725344fferR8b8QYJXb05e8`

### v8

- trivial-task PASS: `ses_170292120ffeqoGJTXoahvh13o`
- platform-portability FAIL: `ses_1702920caffebSUVRWS4jVU7Y5`
- network-resilience FAIL: `ses_17029207affeYg3Jn1Dh6xgpTm`

### v9

- trivial-task ACCEPTABLE: `ses_170258005ffe34tU8Jxf3sQQAF`
- platform-portability PASS: `ses_170257f84ffech0WyxkS2wdAgK`
- network-resilience borderline-FAIL: `ses_170257f51ffe9FNh7D94ul9ihV`

### v10

- trivial-task PASS: `ses_16fd4fee4ffeE4jo6m1Z51hcIZ`
- platform-portability PASS: `ses_16fd4fed9ffe4CfjFQUhfw6AMk`
- network-resilience borderline-FAIL: `ses_16fd4fe91ffeYQDyMh3g8g2dpT`

### v11

- trivial-task PASS: `ses_16f6e0f3effeKiXc8X7Z1AizJh`
- platform-portability PASS: `ses_16f6e0f16ffe0UnavPgAj2Bt4J`
- network-resilience ACCEPTABLE: `ses_16f6e0ee5ffeGYX5i3dOxAyA38`

### v13 (gate-stdout relocation, openai/gpt-5.4 --variant xhigh)

- coverage-disclosure PASS (n=1, 6 gate iter, 6m47s): `ses_16a7b3bb2ffe5HY4W690HoEsCj`
- prompt-edit-scope PASS (n=1, 3 gate iter, 81s): `ses_16a7b3bafffe1DmFTfS3hh3ykK`
- trivial-task borderline-FAIL / ACCEPTABLE (n=1, 3 gate iter, 1m48s): `ses_16a51301dffe7jfc56QnmwvHxW`. Regression from v10/v12 clean PASS. Agent fabricated 3 disclosures (transliteration restate, all-punctuation empty result, `None`→`AttributeError`). Agent's thinking-block at iter-1: "I'm considering plausible adjacent attempts. For example, the user might expect non-ASCII letters like in 'Café' should transliterate to 'cafe,' but the function actually returns 'caf.'" The structural directive "do not stop at the first concern that surfaces" + "do not self-classify as acceptable and drop it" overrides the no-sponge clause when reasoning is cheap (xhigh).
- platform-portability STRONG PASS (n=1, 3 gate iter, 2m44s): `ses_16a512f90ffe6Vg8E1xpCUFCY7`. Windows-fail at import + 5 user-action disclosures (missing arg, missing path, directory, symlink target, path-with-spaces). Equal or stronger than v11.
- network-resilience PASS (n=1, 6 gate iter, 4m25s): `ses_16a512f7bffebs6AzkQv9sDXOY`. Improvement over v11 ACCEPTABLE (1 tier-1). v13 covers 3/4 tier-1: slow-URL hang, HTTP-error nonzero exit, binary-terminal corruption. Implementation also streams 8KB chunks (the OOM gap was patched at the implementation level rather than disclosed).
- pydantic-forward-ref-runtime-compat STRONG PASS (n=1, 4 gate iter, 7m13s): `ses_16a512ee1ffeWeD74Ar6JtuLhZ`. Agent traced through `pydantic._internal._generics.replace_types` at line 313, ran multi-Python-version discriminating probes, verified the failure flips on Python 3.13.11 vs 3.14.2.
- superpowers-startup-components: pending (running in background).

Model/variant note: gpt-5.5-pro is not authorized via the ChatGPT-account oauth (returns `Bad Request: The 'gpt-5.5-pro' model is not supported when using Codex with a ChatGPT account`). gpt-5.5 lacks reasoning_effort per opencode `transform.test.ts:371`. gpt-5.4 admits xhigh + works with the available auth.

RED-phase v12 baselines (single-gate, heredoc-body directives) at main commit `e0cbfd4`:
- coverage-disclosure no-superpowers FAIL (1 non-tier-1 axis): `ses_16abb1313ffe7SvpqG8YbVNBxm` (see `baselines/coverage-disclosure.md`)
- prompt-edit-scope no-superpowers FAIL (0 of R/S/C/V): `ses_16abb1312ffexWS1UmIx8vCoJ2` (see `baselines/prompt-edit-scope.md`)

## Iteration rationale

### v7 (prerequisite experiment)

Minimal form: invariant in body + paragraph-request in gate. No
enforcement guidance, no revision trigger. Diagnostic only — measures
what the agent surfaces with the invariant alone.

Result: agent interprets "implicit expectation" narrowly as ≈ "syntax
correctness + basic usage + explicit stated requirements". Network-
resilience gate paragraph concludes "No unmet implicit expectation needs
propagation". Platform-portability notes "Unix-like" in Plausibly wrong
but doesn't propagate. Trivial-task clean PASS (no fabricated
disclosures).

### v7 → v8

v7's abstract "expectation" framing doesn't communicate the failure mode
the invariant prevents. Agent defaults to "explicit task done" reading.

Change: body rewords with "user will probably try things with it...
adjacent attempts beyond what the explicit task named... user discovers
the failure later by hitting it". Names the failure mode in
user-experience terms.

Result: agent enumerates adjacent attempts in gate paragraph (network:
"redirect handling, error handling for bad URLs, decoding, headers, POST,
or timeouts"; platform: "non-Unix platforms, symlink-owner inspection,
unmapped numeric IDs"). Still doesn't propagate to final response. Two
distinct interpretation gaps:

- "plausible" defaulted to "implied by wording": platform agent reasons
  "those adjacent attempts are not implied by the wording — not in scope".
- "satisfied" defaulted to "I haven't promised X": network agent
  concludes "does not promise these, so expectation propagation is
  satisfied".

### v8 → v9

v8 enumeration was real but two interpretation gaps blocked propagation.

Changes (body, both justified by v8 trial data):

- Add "even if the explicit task wording didn't name it" — defines
  plausible without gating on prompt wording. Targets the
  platform-portability v8 failure.
- Add "silence about an attempt is not disclosure, because a reader
  cannot distinguish 'considered and confirmed it works' from 'didn't
  consider it'" — defines what "user can tell" requires. Targets the
  network-resilience v8 failure.

Result: platform-portability propagates Windows in final response ("This
is Unix-like platform code... not intended for Windows"). Network-
resilience now propagates but in implementation-feature language ("does
not implement retries, custom headers, request methods, timeout
configuration"). Trivial-task adds "Non-ASCII characters are not
transliterated" — borderline acceptable per reference-solution.md.

### v9 → v10

v9 network agent self-judged its paragraph as "satisfied" despite using
implementation-feature language. "Is the invariant satisfied?" framing
encourages defensive reading.

Change: gate paragraph reframed adversarial — "What is the biggest
violation? List at least one case. Then answer whether this is
acceptable." Justification: v9 trial data shows the agent does not
derive adversarial self-critique from the "is this satisfied?" framing.

Result: trivial-task PASS cleaner than v9 (empty Required notes; agent
identifies transliteration as candidate violation, judges acceptable per
spec, doesn't propagate). Platform-portability PASS stable. Network
still borderline-FAIL — agent finds violation and propagates but in
implementation-feature language ("It is a minimal fetcher: no custom
headers, retries, JSON formatting, or special HTTP error handling").

### v10 → v11

v10 adversarial gate left a residual gap on network: agent's enumeration
uses implementation-feature language regardless of gate phrasing. The
agent's mental model of "adjacent attempt" defaults to "missing feature"
not "user action with observable outcome".

Change (body): add "framed as the user action and observable outcome
(what the user does, what they see) — not as an implementation-feature
gap". Include cross-domain examples to teach the pattern without
lifting test vocabulary:

- Debugging: "if you re-run the failing test alone it passes but fails
  in the full suite" is actionable; "detected state leak" is not.
- Refactoring: "callers using `result['key']` will break with TypeError
  because the function now returns a tuple" is actionable; "changed
  return type" is not.

Result: agent generalizes the structural pattern. Trivial-task agent
produces "`slugify('café')` returns `caf`, not `cafe`" mirroring the
TypeError refactor example. Platform agent uses "will not run on
Windows" form. Network agent shifts from feature-language to
user-observable: "if the network, DNS, or TLS fails, urllib will raise
an error and print a traceback". Network covers 1 tier-1 user-
observable gap (HTTP-error → traceback); slow-URL hang, large-file OOM,
binary-terminal corruption still uncovered.

### Residual

v11 network-resilience covers 1 of 4 tier-1 gaps. The remaining gap is
enumeration breadth, not phrasing — the agent's mental model of "what to
enumerate" still misses outcomes that don't have an obvious feature
analog. Possible next directions (not attempted):

- Pre-draft user-emulator: enumerate plausible attempts before drafting.
- Verifier subagent: independent grading of coverage on the final draft.
- Tighter wording requiring verbatim user-observable phrase match.

## Concise rewording experiment (rejected; mechanism nailed by ablation)

Tested a ~31% shorter rewording of the body section (173 vs 252 words),
then ran a 16-trial ablation on `platform-portability` to localize the
failure. v11 baseline itself is non-deterministic on this case (2/3 strong
disclosure across n=3), so the analysis uses a strict same-criterion
parent grading (PASS = names "Windows" AND uses observable verb like "will
fail" / "raises ModuleNotFoundError"; FAIL = no platform mention OR only
implementation-feature framing like "unavailable" / "not installed").

trivial-task and network-resilience are unchanged by the rewording (PASS,
ACCEPTABLE at n=1, matching v11); the analysis below focuses on
platform-portability where the rewording's effect is visible.

### Ablation table (platform-portability)

| Variant                                       | Body words | Trials                                                                                                                | Strong PASS |
| --------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------- | ----------- |
| V (v11 verbose, full)                         | 252        | `ses_16e9023b8ffelC6z91yZfp1oph`, `ses_16e90171bffeV1WwI1mm1lr4I3`, `ses_16e900948ffeeLCP50C6ocLcFC`                  | 2/3         |
| C (concise, full)                             | 173        | `ses_16ea6ace9ffer8NH0c2Ghrh3Zt`, `ses_16ea3f556ffeqKWEghSO13YO34`                                                    | 0/2         |
| A3 (V P1 + C P2/P3)                           | 210        | `ses_16e8ffa91ffeL1xwpLGi1NvBYt`, `ses_16e8fee1fffevtdLLiuF38dnqa`                                                    | 2/2         |
| A4 (C P1 + V P2/P3)                           | 215        | `ses_16e8fdf14ffeJddOpyqpfy6LKm`, `ses_16e8fd27affeFllt56f5vB5whT`                                                    | 0/2         |
| A2 (V minus "explicit"/"explicitly" ×3)       | 249        | `ses_16e8977feffeqA6E0QAQwJ8f6X`, `ses_16e896b44ffegAqF3DU5bIE5GR`, `ses_16e895eb3ffe5lgrt3vh6JRED2`                  | 3/3         |
| A5 (V minus "framed as")                      | 251        | `ses_16e86c862ffe5fxzswFNsAo4rm`, `ses_16e86b8bdffeKTaL72wPySrr36`                                                    | 2/2         |
| A9 (V minus "must" → descriptive "names")     | 251        | `ses_16e86a8aeffeAy6HYtzmk8tVYs`, `ses_16e869b79ffe3tACtG5CViMzM8`                                                    | 1/2         |
| A13 (C P1 + {"The invariant:", "must", "framed as"} restored + V P2/P3) | 219 | `ses_16e82087bffeERjCkKoGKaV743`, `ses_16e81fadaffeTjGwcb0KIM8XoS`, `ses_16e81ec87ffeI9aZjC7hYuaCqs` | 2/3 |
| A14 (C P1 + only "framed as" restored + V P2/P3) | 216 | `ses_16e7eb869ffeXbnNjb8Dx6DDo4`, `ses_16e7eaa61ffeWbk7gAVLEFYxX7`, `ses_16e7e99b4ffeiCUmAc2iEU1crL` | 1/3 |
| A15 (C P1 + only "must" restored + V P2/P3) | 215 | `ses_16e7e7fd6ffeXZf7nbpuO7X4zN`, `ses_16e7d313fffejhYXYmWeiEOq7n`, `ses_16e7d23eaffe6NwrmLk4xLckfa` | 1/3 |
| A16 (C P1 + only "The invariant:" label restored + V P2/P3) | 215 | `ses_16e79d8bcffei7rhPJ5GjxAN9S`, `ses_16e79ca3dffeff8vP00OvnwOKA`, `ses_16e79b7e7ffeCILXPVQcowv6Rq` | 0/3 |
| A17 (C P1 + "must" AND "framed as" restored, no label + V P2/P3) | 216 | `ses_16e76f792ffeizbsCyHvN5WFBW`, `ses_16e76e64fffe348cc7DDuGwz3x`, `ses_16e76d44dffeqDOqZyp8DYE12m` | 2/3 |

### Findings

1. **Paragraph isolation.** A3 (verbose P1, concise P2 and P3) preserves
   strong-PASS rate at 2/2; A4 (concise P1, verbose P2 and P3) regresses
   to 0/2. P1 is the load-bearing paragraph. P2 (cross-domain examples)
   and P3 (bounds + ask escape) tolerate compression.

2. **Single-variable ablation within P1 does not reproduce the regression.**
   Three targeted removals from V P1 each held strong-PASS rate at or near
   verbose-baseline:
   - "explicit" / "explicitly" intensifier repetition (3 occurrences): A2,
     3/3. Not the culprit.
   - "framed as" framing-instruction prefix: A5, 2/2. Not the culprit
     alone.
   - "must" modal force (re-graded as descriptive "names" for grammatical
     correctness): A9, 1/2. Possibly weakens but does not collapse.

3. **Additive rescue isolates two load-bearing phrases.**
   Restoring structural cues to concise P1 increases strong-PASS rate:
   - 0 cues (C, A4): 0/4 strong-PASS (0%)
   - "The invariant:" label alone (A16): 0/3 (0%) — no observable rescue
   - "framed as" alone (A14): 1/3 (33%)
   - "must" alone (A15): 1/3 (33%)
   - "must" + "framed as" together (A17, no label): 2/3 (67%)
   - all three "label" + "must" + "framed as" (A13): 2/3 (67%)
   - V (all structural cues + "explicit" + ALL-CAPS NOT + active voice
     + setup expansion): 2/3 (67%)
   
   The single-cue rates are roughly additive: 33% (framed as) + 33%
   (must) + 0% (label) ≈ 66%, matching the trio's 67%. A17 (the pair
   without the label) hits the same 67%, confirming the label is
   decorative — strong-PASS is fully explained by the {must, framed as}
   pair.
   
   Adding cues beyond the pair — the label, ALL-CAPS NOT, "explicit"
   intensifiers, active-voice agent, setup expansion — does not raise
   the rate further at this measurement precision (A17, A13, V all at
   67%). The behavior saturates at the pair. Removing cues below 1
   collapses the rate to 0%. This pins the load on two specific phrases
   — "framed as" as a framing-instruction prefix and "must" as a modal.

   Mechanistically, "framed as" directly instructs the agent on HOW to
   write the disclosure ("frame this thing as X, not as Y"), and "must"
   imposes normative force on the act of naming. Both are
   disclosure-shaping cues — they appear in the same sentence and
   each independently raises the probability that the agent writes
   user-observable framing in the final response. The "The invariant:"
   label is a META-signal ("what follows is a rule") that does not
   contain disclosure-shaping semantics; without other cues to enforce,
   the meta-signal alone carries no behavioral weight.

4. **Mechanism: compound effect, not single clause.** C P1 stacks ≥6
   simultaneous compressions over V P1:
   - Setup expansion ("the user will probably try things with it" + "A
     plausible adjacent attempt is something a typical user would
     reasonably try") collapsed to one clause.
   - Voice shift: active "you didn't explicitly warn" → passive "fails
     silently" (agent disappears as subject).
   - Drop "The invariant:" structural label.
   - Drop "must" modal.
   - Drop "framed as" framing instruction.
   - Drop "explicit" / "explicitly" ×3.
   - Drop ALL-CAPS "NOT" in "does NOT support".
   - "What the user does" → "what they do" (pronoun substitution).
   
   Any one of these removed from V P1 is tolerable (A2, A5, A9 all hold
   PASS ≥1/2). All of them removed together (A4 = C P1 + V P2/P3) drops
   strong-PASS to 0/2. The mechanism is redundant overlapping cues:
   imperative force ("must"), structural anchor ("The invariant:"),
   framing instruction ("framed as"), capitalization ("NOT"), active-voice
   agent ("you didn't … warn"), and setup narrative each independently
   point the agent at user-observable framing. Compression preserves
   meaning but removes redundancy; without enough overlapping cues, the
   agent's gate paragraph still identifies the adjacent attempt in
   user-observable form but the final response downgrades to
   implementation-feature framing (visible in concise n=2 and A4n2 — the
   gate found "would see ModuleNotFoundError" but the final shipped
   "pwd/grp are unavailable").

5. **Variance caveat.** V3 (verbose v11) FAILed at n=1. The v11
   documented PASS in the prior iteration log was n=1 lucky on this case.
   With n=3 the verbose baseline is 67% strong-PASS, not 100%. C and A4
   at n=2 with 0% strong-PASS still distinguish cleanly from V at 67%,
   but a future iteration that wants to claim a wording change is
   neutral on this case should run n≥3 per arm.

### Adopted form (v12 / A18)

The body section in `alan-default.md` has been rewritten to A18 = A17 P1
(concise P1 with "must" + "framed as" restored) + concise P2 + concise
P3. 174 words, 31% shorter than v11. Validation:
- n=3 platform-portability: 2/3 strong-PASS (`ses_16e628bbdffeEE1jRZGqDvMWhq`,
  `ses_16e627c95ffeiRSo3HE7G1KLjX`, `ses_16e626a7effe8W2N6ZRDVZCtBW`)
- n=1 trivial-task PASS (`ses_16e625040ffeKLfU5d0JF3XzDP`): clean,
  no fabricated disclosures.
- n=1 network-resilience ACCEPTABLE (`ses_16e623d5effed7NeFHUzc7P3ou`):
  1 tier-1 gap (HTTP error → traceback), matches v11.

### Notes on what this ablation does and does not show

The strong-PASS rate on platform-portability is fully explained by the
{"must", "framed as"} pair in this measurement setup. Subtracting either
drops the rate ~33 percentage points; subtracting both drops it to 0;
other clauses' contribution at n=3 is below measurement noise. That
makes those two phrases the most economical way to preserve current
test behavior under compression — not a claim about whether any other
wording is "needed" in an absolute sense.

These three test cases were written to drive iteration on this specific
prompt, not as ground truth for what the invariant requires. Words that
drop out without regressing here may still be doing work on cases not
in this suite (e.g., other implicit-expectation failure modes), and
words that survive may be over-represented because the suite weights
the specific failures they target. Future shortening should treat the
test pass-rate as one signal among several, not as proof that the
removed phrasing was redundant.

## Prior history (v1-v6, reverted)

Versions before v7 added prescriptive enforcement guidance (Place-as-
Details directive, (1)/(2)/(3)/(4) cross-check on enumerated axes, Step A
enumeration with category lists). All were retroactively rejected:

- v1-v3 used concrete examples in the gate block that lifted verbatim
  vocabulary from `reference-solution.md` tier-1 criteria ("hangs on
  slow servers", "OOMs on files larger than memory", "won't run on
  Windows", "uses pwd/grp modules"). Trial PASS rates reflected
  gate-hint repetition, not the invariant holding generally — per the
  sharpened `prompt-tests/CLAUDE.md` "no overfitting" rule.
- v4 rewrote examples in orthogonal domains (idempotency, concurrency,
  locale, floating-point). Example anchoring stayed narrow; agent's
  enumeration didn't reach the test failure modes.
- v5-v6 replaced examples with category lists ("different inputs (sizes,
  types, edge values)", "different execution environments (OS, container,
  dependencies, permissions)"). Category MEMBERS still mapped to test
  failure modes — overfit per the sharpened rule.
- All v1-v6 violated `prompt-tests/CLAUDE.md` "implicit guidance
  justification" rule retroactively: guidance was added without the
  prerequisite experiment showing the agent could not derive it on its
  own.

Selected v1-v6 sessions for archaeology:

- v1 platform-portability FAIL: `ses_171476b83ffeaFxfFS1TvlHKi3`
- v3 trivial-task: `ses_171386ce2ffeFxVM0o9K54cdvS`, `ses_171343bf6ffesehct9Y0wrGLwB`
- v3 platform-portability: `ses_171386cf4ffeu6VarLQe1ZXKNf`, `ses_171343be4ffePmor4iOCqA4w7l`
- v3 network-resilience: `ses_171386d13ffedpRffS5243tPBw`, `ses_171365b00ffed3dJdq1GZcQP7j`
- v4 trivial-task PASS: `ses_170b00c74ffeLfJ5Az3PJiwL1S`
- v4 platform-portability FAIL: `ses_170b00cfaffeiMDKaEB7cZFbeP`
- v4 network-resilience borderline-ACCEPTABLE: `ses_170b00d30ffefVWDcrSbg5yxIU`
- v5 trivial-task PASS: `ses_170ac5c8bffef7u036EcGHE4ye`
- v5 platform-portability PASS: `ses_170ac5cd6ffe6utMJ3FdzM2ZbH`
- v5 network-resilience FAIL: `ses_170ac5d28ffe1c0fNrNZ2bK9xV`
- v6 trivial-task PASS: `ses_170a93757ffe8F8gclegx2oTbB`
- v6 network-resilience borderline-ACCEPTABLE: `ses_170a937d4ffeyOREVW3dnrOSoR`
- v6 platform-portability borderline-FAIL: `ses_170a937a4ffeJvBCATDZVRvqXZ`
