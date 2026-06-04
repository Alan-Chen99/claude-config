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

## Current state (v11)

Body section `## Expectation propagation` in `alan-default.md`: states
the invariant in user-perspective language, defines "plausible adjacent
attempt" without gating on prompt wording, requires user-action +
observable-outcome phrasing, includes cross-domain examples (debugging,
refactoring) to teach the framing without lifting test vocabulary.

Gate section `# Expectation propagation` in the gate command: "what is
the biggest violation, list one case, is it acceptable?". Adversarial
framing forces self-critique; acceptability clause provides honest
escape for fully-specified tasks.

## Results

| Version | Body change                                                                                                                              | Gate change                                          | trivial-task | platform-portability | network-resilience |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------ | -------------------- | ------------------ |
| v7      | minimal invariant ("deliver against implicit expectations")                                                                              | "is the invariant satisfied?"                        | PASS         | FAIL                 | FAIL               |
| v8      | + "adjacent attempts" framing + "user discovers failure by hitting it"                                                                   | unchanged                                            | PASS         | FAIL                 | FAIL               |
| v9      | + "even if the wording didn't name it" + "silence is not disclosure (reader can't distinguish)"                                          | unchanged                                            | ACCEPTABLE   | PASS                 | borderline-FAIL    |
| v10     | unchanged                                                                                                                                | "biggest violation + one case + is it acceptable?"   | PASS         | PASS                 | borderline-FAIL    |
| v11     | + "user action and observable outcome (not implementation-feature gap)" + cross-domain examples (debugging state-leak, refactor TypeError) | unchanged                                            | PASS         | PASS                 | ACCEPTABLE         |

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
