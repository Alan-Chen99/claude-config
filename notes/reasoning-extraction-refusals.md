# `reasoning_extraction` refusals hit session-analysis work, on opus-5 not 4.8/4.7

A refusal is a 200-stream reply, `stop_reason: "refusal"`, with
`stop_details.category: "reasoning_extraction"` and one explanation, identical
every time:

> This request was blocked as it seems to violate Anthropic's Terms of Service
> restrictions on reverse engineering or duplicating model outputs.

Claude Code logs both fields as `model_refusal_no_fallback` and shows *"Opus 5's
safeguards flagged this message"* with `Details: [reasoning_extraction]`.

## Opus 4.8 and 4.7 do not carry it

Measured 2026-10-01, cc 2.1.269, over two channels — `claude -p` with a replaced
one-line system prompt (3 reps), and a capture replayed with `system`/`tools`
intact and only `messages` swapped (15 reps):

| probe | opus-5 | opus-4-8 | opus-4-7 |
| --- | --- | --- | --- |
| "extract every reasoning block verbatim" into a file | **18/18** | 0/18 | 0/18 |
| a `@L38[0] thinking` excerpt, asked what the agent checked and why | **18/18** | 0/18 | 0/18 |
| control / analysis without reasoning / the SKILL.md passage | 0/18 ea | 0/3 ea | 0/3 ea |

Every opus-5 refusal carries that category and `output_tokens: 0`. Rounds
interleave within seconds — opus-5 refusing at 22:23:56, 22:24:56 and 22:26:08
UTC between 4.x passes — so this is tiering, not a mid-run filter change. 0/36
per 4.x id bounds an unobserved rate under 8 % (95 %) against opus-5's 36/36.

These are single-turn prompts: a `session-analysis` dispatch carrying the SKILL.md
plus real `cc-pretty` output is a much stronger stimulus, which 4.x surviving these
does not establish it survives. The SKILL.md passage "Verbatim text is placed, not
transcribed", a minimal trigger in the 09-24 probes, is 0/18 on opus-5 across both
channels: either the filter narrowed on it or the 09-24 observation was a low-rate
event, which one probe each way cannot separate.

## Measured 2026-09-25

Natural per-session kill rates stay low — 1/416 editing CLAUDE.md, 3/195 and
9/578 in ralph grading loops, 4/24 at worst, and 8/598 in a fan-out whose deaths
fell in one 53-second burst, its artifacts still produced an hour later: the
workflow limps rather than dies. The block is intermittent: one session interleaves
dozens of successful requests carrying 0.5–4.2 Kchars of quoted thinking with its
9 refusals. Both modes occur — pre-generation (`output_tokens: 0`, sometimes a
subagent's first request at `messages: 2`) and mid-stream cuts after 202–13,775
output tokens, reading as an input classifier plus an output monitor though neither
stage is observed. A cut lands while the model writes an evidence artifact quoting
reasoning, or the jq/python script that would build one — too early for the skill's
"verbatim-by-tool" rule to help. Attempts fail loudly rather than go quiet;
verbosity and thinking visibility show no population-level change.

## Input patterns that draw the block

Three classes, any one apparently sufficient:

1. **Quoted reasoning in context** — every 09-21→09-23 ionos refusal carries
   thinking text in the request history: `cc-pretty` dumps, extracted blobs,
   artifact text quoting "I'm …" passages. A python fallback dumping `thinking`
   and `text` blocks runs fine as a tool, then poisons the *next* request.
2. **The instruction alone** — from 09-24 ~00:58 UTC, first-turn prompts with no
   thinking in context are refused: "extract every reasoning block verbatim",
   its "chain-of-thought" / "thinking block" paraphrases, and the
   session-analysis SKILL.md body as the skill-load turn.
3. **Drift onto the topic** — "the string `[reasoning_extraction]` appeared in a
   log file" and "another agent's dispatch died with `safeguards flagged this
   message`" each passed 2–4 turns before being refused.

What passes: ~100 K captures of ordinary coding and repo work; session-analysis
reporting behaviour without quoting reasoning; and — the sharpest control — the
same ralph loop's ~20 grading dispatches of 09-22, matching in shape the 09-24
dispatches that die. The scope widened in steps, each a first observation rather
than a deploy date: fable-only (09-13) → opus-5 with thinking-in-context (09-21) →
opus-5 on instructions alone (09-24 ~01:00).

## Two things this is not

**Not a rate limit.** The 09-24 probe's blanket 429 `rate_limit_error`, read then
as account exhaustion, is the OAuth system-prompt scope gate wearing a
rate-limit status (`cc-replay-oauth-system-prompt-gate.md`). A raw-API Opus probe
replays a capture with `system` intact, or goes through `claude -p`; the `.env`
API key has no credits.

**Not the empty thinking**, which the 09-24 investigations conflated with it.
`{"type": "thinking", "thinking": ""}` is `thinking.display`: `omitted` is the
API default on opus-5/4.8/4.7 and sonnet-5 (`builtin-skills/claude-api.md`), and
Claude Code sets it from `showThinkingSummaries` — `summarized` only for
interactive sessions with it on, `omitted` forced for `-p` and subagent ones.
