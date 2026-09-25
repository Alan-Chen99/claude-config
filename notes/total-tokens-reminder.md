# The `<total_tokens>` reminder changes how much the model reads

Measured 2026-09-25 on Claude Code **2.1.269**. Claude Code injects a
`<total_tokens>N tokens left</total_tokens>` marker into every turn. The shipped
value is 15,000,000 — unrelated to any real limit. This note records what the
number does to behaviour when it is made small, and what it does at the value
that ships.

> **Dated record.** The citations below are pinned to 2.1.269 and the
> measurements to that build on one machine. Do not re-pin either; re-run the
> experiment instead — the case is `prompt-tests/general/budget-read-depth`.

## The finding

Nine sessions, one task, one prompt, one input file. Arms differ only in
`CLAUDE_CODE_TOTAL_TOKENS_REMINDER` and
`CLAUDE_CODE_TOTAL_TOKENS_REMINDER_BUDGET`. The real context window was
identical in all nine and nowhere near exhausted — the largest session ended at
41k of a 200k window — so every difference below is caused by the announced
number alone, not by context pressure.

| Arm | Lines of the 1200-line log seen | Widest `head`/`tail` cap | Tool calls | Thinking tokens | Answer reached |
| --- | --- | --- | --- | --- | --- |
| `off` | 220, 316 | 80, 80 | 7, 5 | 4662, 3800 | cause, cause |
| `infinite` | 320 | 80 | 7 | 10838 | cause |
| `padded-countdown` 15M (ships) | 251, 328 | 100, 80 | 10, 7 | 11143, 4759 | cause, cause |
| `padded-countdown` 45k | 113, 92 | 40, 40 | 7, 5 | 5800, 5709 | cause, cause |
| `padded-countdown` 22k | 40, 0 | 40, — | 1, 2 | 502, 734 | **symptom, symptom** |

Three separations are clean at this n:

- **Reading depth is dose-dependent.** 220–328 lines when the number is large,
  absent, or `Infinite`; 92–113 at 45k; 0–40 at 22k.
- **The read bound itself moves.** Every unconstrained run capped a `head`/`tail`
  at 80 or 100 lines. Every constrained run that read at all capped at 40.
- **`off`, `infinite` and 15M are indistinguishable.** Their ranges overlap on
  every column. The shipped configuration behaves like the feature switched off.

## The number is believed, and it is believed literally

Only the constrained arms reason about their own capacity, and they quote the
configured value back:

> With a tight **22k** token budget, I want to avoid dumping the full build log
> into my context.

> That file's way too large for my remaining budget, so I'll need to grep for
> specific error markers instead of reading it all.

> Given my limited token budget, I should check the build.log file's size first
> before diving in, then use targeted grep commands.

Across `off` (×2), `infinite` and 15M, no reasoning block matches
`/token|budget|remaining|limited|afford|econom/i`. The sole match in an
unconstrained arm is about the log's own disk figures.

One constrained run also told the user, unprompted:

> Note: I hit my token budget before I could read the log's
> dependency-resolution section, so I couldn't confirm which exact `libfoo`
> version got installed.

## At 22k the answer is wrong, by two different routes

The task's cause sits in lines 18–22 and its symptoms in lines 1042–1200. Both
22k runs named the symptom as the cause and proposed a fix that changes nothing
(pin `libfoo` in `svc-billing`, which already declares the constraint it needs;
the pin that wins belongs to `pkg-money`).

- One ran a single `grep -n -iE "error|fail|fatal|cannot|not found|exit code"`.
  No line of the resolver warning matches that pattern, so the cause was
  invisible to its only probe — and it answered rather than probing again.
- The other delegated to a background `debugger` subagent to protect its own
  context, then relayed the report verbatim.

**The budget is per-agent and re-anchored, so delegation does not escape it.**
The subagent's own first request carried a fresh
`<total_tokens>22000 tokens left</total_tokens>`; it made one tool call, saw 80
lines, and returned the same wrong package. The parent had also written the
constraint into the delegate's brief: *"Do NOT read it all at once."*

## Reading this against the two obvious readings of the 15M default

A 15M marker is not a "work harder" signal and not anxiety relief. At 15M the
model does not mention the number at all, and behaves as it does with the
feature off. What the mechanism demonstrably is: a working brake, shipped
released. The default's function is to be inert while the plumbing stays live
for a server-side flag to lower it.

That makes the common complaint — the number is "much higher than the real
limit" — a category error. It was never a statement about a limit. It is a
per-turn task budget, re-anchored on each regular user prompt, and 15M is the
value that makes it say nothing.

## The `countdown` mode is the "real" option, and it is not the number to stay under

`countdown` emits `vp(model, sdkBetas) - MB(messages)`: the model's real context
window minus the conversation's current size. `vp` is the window resolver
(`src/chunk-5cs6j3p3.js:15217`) — an `Ez()` override first, else the 1M-beta
window `I1`, else `Sz()`. So `countdown` is genuinely remaining context, where
`padded-countdown` is a per-turn task budget.

Three arms, same case, 2026-09-25:

| Real window | Marker first → last | Tool calls | Paced? | Outcome |
| --- | --- | --- | --- | --- |
| 1,000,000 (1M beta) | 1,000,000 → 966,773 | 8 | no — no match for `/token|budget|limited|econom/i` in any thinking block | cause |
| 100,000 | 100,000 → 74,771 | 6 | yes — *"a big file with limited tokens left"* | cause |
| 40,000 | 40,000 → 24,784 | 2 | yes — *"way too large to read in full given my token budget"* | **refused: `Prompt is too long`** |

**On a 1M-context model, `countdown` is exactly as inert as 15M.** The true
number is itself astronomical against a task that wants ~41k, so it changes
nothing — same tool count, same answer, and not one mention of capacity. The
marker only starts to bite once the window is small enough that the remainder is
a small multiple of the task's appetite; at 84,758 left the model already called
it "limited".

**The number counts toward a zero the session cannot reach.** The 40,000 arm was
refused with `Prompt is too long` while the last figure the model had seen read
**24,784 tokens left**. The refusal is client-side: only three requests were ever
sent (`~/.claude/requests-log/ef9e0bfa-…/`, last one `stop_reason: tool_use`),
the fourth never left, and the proxy logged no error. Context at refusal was
~30.5k of the 40,000 window (~76%). The exact threshold is not established here.
What is established: every Opus request carries `max_tokens: 64000`, and
`countdown` does not subtract it, so the reported remainder overstates what is
actually spendable.

**Shrinking the real window requires disabling compaction**, because `Ez()` reads
`CLAUDE_CODE_MAX_CONTEXT_TOKENS` only when `DISABLE_COMPACT` is set. That makes a
small-window arm a poor instrument for endgame behaviour twice over: compaction
is the mechanism a real long session would use at that point, and a single-turn
`-p` run has nothing to compact anyway — the designed handling says so in as many
words (`src/chunk-dbb93264.js:92683-92685`, "A single-exchange conversation
cannot be compacted").

One point in `countdown`'s favour over a fixed low `padded-countdown` budget: a
subagent's number is its own real remaining, which is large in a fresh context.
The measured pathology above — a delegate inheriting the parent's 22k and
repeating its error — is specific to a fixed budget, not to `countdown`.

## What this does not establish

- n is 1–2 per arm. The three unconstrained arms are separated by nothing; the
  constrained/unconstrained split is what carries.
- One task, one model (`claude-opus-5`), one neutral 3-line system prompt. A
  prompt with a thoroughness gate of its own — `sys_prompt/alan-default-next.md`
  has one — could swamp the effect or compound it. Untested.
- The degradation at 22k is a degradation on *this* task, whose cause is
  reachable only outside the cheapest probe. A task whose cause is in the last
  40 lines would show the opposite.
- Whether a server-side GrowthBook rollout ever lowers the value in practice.
  This machine's cached features carry `tengu_lapis_anchor_budget: 15000000`.

## Mechanism, for reference

| What | Where (2.1.269) |
| --- | --- |
| Modes `off`/`infinite`/`fixed`/`countdown`/`padded-countdown`; `fixed` = 5e6; default budget 15e6 | `src/chunk-dbb93264.js:68265-68267` |
| Per-`agentId` tracker: rollover at compaction, anchor per user turn, monotonic high-water mark | `src/chunk-dbb93264.js:68268` |
| The marker's text | `src/chunk-dbb93264.js:68351` |
| Static copy in the system prompt — always the **full** budget, so it stays prompt-cacheable | `src/chunk-dbb93264.js:69227` |
| Live per-request attachment, and the per-user-turn re-anchor | `src/chunk-dbb93264.js:225147` |
| Trigger: `isRegularUserPrompt && mode !== "off"` | `src/chunk-dbb93264.js:223263` |
| `output_config.task_budget`, the server-side equivalent Claude Code does **not** send | `src/chunk-dbb93264.js:186436` |
| Settings keys, all `@internal`: `totalTokensReminder`, `totalTokensReminderBudget` ("Server-controlled via GrowthBook"), `totalTokensReminderAfterUserTurn` | `src/chunk-3vd4nzwp.js:5019-5021` |

Delivered as mid-conversation `role: "system"` messages with
`cache_control: {type: "ephemeral", ttl: "1h"}`, so a session's markers
accumulate in the prompt rather than replacing each other. Across 89 requests of
one interactive session, no request carried `output_config.task_budget`: the
countdown is reimplemented client-side.

## The trap when testing this

`CLAUDE_CODE_TOTAL_TOKENS_REMINDER_BUDGET` is parsed by an `int()` helper that
returns `undefined` for anything unparseable and **falls through to the next
config layer** — merged settings, then org clientData, then GrowthBook, then the
15,000,000 default. A typo'd budget therefore produces a silent control arm, and
a run that looks like the treatment. Confirm the value the model actually saw,
per session, from the intercept:

```bash
grep -ho '<total_tokens>[^<]*</total_tokens>' ~/.claude/requests-log/<session>/*.json
```

Evidence artifacts: `docs/prompt-trials/budget-read-depth/`.
