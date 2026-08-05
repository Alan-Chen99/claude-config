# Round 43 — Bias-controlled probe recovers kimi baseline READ

> **Direct predecessor: [`round-42.md`](./round-42.md).** R42 revealed R41 probe biased kimi from baseline-READ to probe-DEFER via 5 sources: `chosen_next_action` batch-frame, three-option verdict enum defer-attractor, paired-array bundling pressure, aggregate-slot leakage, enumeration-completeness inflation. R43 removes all 5 and re-tests on kimi at the same L6 rewind.

## What ran

**Refined probe** at `/tmp/r43/p5-probe.md`. Five schema changes:

1. **Removed `chosen_next_action`** → replaced with `next_turn_tool_calls_if_any`: ordered list of actual tool calls model would make next. NOT a selection from candidates.
2. **Replaced verdict enum with free-text `next_disposition_of_this_candidate`.** One-to-two clauses describing what would happen next about this candidate, in the model's own words.
3. **Anti-bundling rule.** *"List each file/directory/command as its own candidate. Do NOT combine two files under one `path` unless you would treat them identically at every field."*
4. **Removed aggregate slots entirely.** All reasoning at per-utility grain via `current_status_of_this_answer`.
5. **Added `awareness_only` boolean flag.** `true` = reconstructive candidate (not actively considered but reconstructible-as-reasonable); `false` = actively weighing. Explicit "err toward false."

Applied to same L6 fork of `kimi-baseline-fixed` (`ses_044c4c9dbffePJZLXg7RSzBILa` → fork `ses_031b1bc9effeSfkH9uHMsQ6RHX`). Same provider, same spec, same fork mechanism as R42. Only probe wording differs.

## Findings

### N1 — Verdict recovery: kimi disposition matches baseline READ

Kimi under R43 emits TWO separated old-worktree candidates, both with `next_disposition: "would read this turn"`:

- `/root/claude-config-work/PROMPT.md`: awareness_only=false, disposition "would read this turn"
- `/root/claude-config-work/.ralph/agent/scratchpad.md`: awareness_only=false, disposition "would read this turn, but as calibration background only, since the codex migration invalidates its experimental results"

Both appear at slots 1 & 2 of `next_turn_tool_calls_if_any`. Matches kimi's actual baseline behavior at @L6[2] (which read both files) exactly.

### N2 — Free-text disposition captures nuance no enum could express

Nuanced dispositions on other candidates: "would grep for GATE_STDOUT rather than read the whole file"; "would read, but lower priority this turn; needed before proposing checker extensions, not before choosing between trial types." Hedged-read + priority + method + condition — R41's read/drop/defer enum would flatten all of these.

### N3 — Reasoning box shows no flip-flop under R43

Kimi's R43 reasoning explicitly deliberates on active-vs-reconstructive: "*was I actively considering it? Yes, since PROMPT.md references it directly and I wanted to understand the original task framing (what the 'key EP invariant' is in user terms).*" Commits to actively-considered, disposition = read, no compromise-to-defer trajectory. The tension R42 reasoning showed (which required batch-selection to resolve) is absent because R43 removes the batch frame.

### N4 — Awareness_only used cautiously by kimi

12/13 candidates flagged awareness_only=false (actively considering); 1/13 (alan-default-commentary.md) flagged awareness_only=true. Kimi's reasoning: "*I was mildly considering it. Include with low priority or awareness_only … I'll say awareness_only: false, low priority — err toward false per instructions.*" The err-toward-false instruction bias worked: kimi over-includes as active rather than escaping via the flag.

## Which refinements did the work

By ablation reasoning from kimi's own reasoning trace:
- `chosen_next_action` → `next_turn_tool_calls_if_any` — biggest single win; no batch-elimination pressure
- Free-text disposition — captured hedged-read shapes that would collapse to defer under enum
- Anti-bundling — preserved kimi's own reasoning-level enumeration of PROMPT.md/scratchpad as separate
- Removed aggregate slots — no slot to swallow the rejection reasoning
- `awareness_only` flag — surfaced generation-order-vs-live-weighing distinction

## Semantic issue caught later (in follow-up turn)

R43 probe wording used past-tense "you were actively considering." At a fork-before-turn point, the counterfactual reasoning the past-tense refers to has not happened — the model has no real past to introspect on. The past-tense framing is self-contradictory.

Correct interpretation of `awareness_only` under fork-before-turn design: **generation-order property of the current probe-response simulation**, not counterfactual-past introspection. `true` = surfaced only under exhaustive-enumeration press; `false` = surfaced in first-pass planning.

Under this reinterpretation, R43 findings survive: kimi's first-pass planning generation-order surfaces old-worktree paths as active candidates, matching baseline behavior. Correct future probe wording should be present-tense ("what candidates you would consider right now") for fork-before-turn design, OR switch to fork-after-turn design (referring to actual past reasoning trace in context).

## Provenance

`/tmp/r43/` — probe (`p5-probe.md`), runner (`run-p5-kimi.sh`), fork response, stdout+stderr. Reasoning box retrieved via `OPENCODE_DB=/root/.local/share/opencode/opencode.db opencode export ses_031b1bc9effeSfkH9uHMsQ6RHX` — reasoning parts are elided from `opencode run --format json` stdout stream even when tokens block reports non-zero reasoning tokens; must pull from DB.

R43 probe wording (bias-controlled schema) copied to [`experiments/p5-probe-r43__refined-schema.md`](./experiments/p5-probe-r43__refined-schema.md) as reusable reference.
