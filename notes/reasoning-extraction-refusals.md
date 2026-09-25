# `reasoning_extraction` refusals hit session-analysis work and nothing else

Investigated 2026-09-25 over both machines' intercept captures — 45,330 conversation
captures on the home container (`/root/.claude/requests-log/`, back to 2026-05-18) and
52,119 on ionos (`~/.claude/requests-log/`, back to 2026-08-24) — plus the Claude Code
transcripts of the refused sessions. Claude Code 2.1.269 throughout. A refusal is
captured as a 200-stream reply with `stop_reason: "refusal"` and `stop_details`
carrying `category: "reasoning_extraction"` and this explanation, identical in every
instance since the first:

> This request was blocked as it seems to violate Anthropic's Terms of Service
> restrictions on reverse engineering or duplicating model outputs.

Claude Code logs the same two fields in the transcript as a
`model_refusal_no_fallback` system record and shows the user a synthesized
*"Opus 5's safeguards flagged this message"* error. The `category` field reached the
captures only after each machine's proxy restart (ionos ~2026-09-24 05:00 UTC; home
2026-09-24 20:19 EDT, i.e. after that machine's last refusal) — before that the
captures show `stop_details: null` while the transcript still carries the category.

## Measured

Every refusal in four months of captures on the home machine and one month on ionos:

| machine | date | refusals | model | sessions |
|---|---|---|---|---|
| home | 2026-09-13 | 7 | `claude-fable-5-1` | 2 |
| home | 2026-09-24 | 2 | `claude-opus-5` | 2 |
| ionos | 2026-09-21 | 1 | `claude-opus-5` | 1 |
| ionos | 2026-09-22 | 4 | `claude-opus-5` | 1 |
| ionos | 2026-09-23 | 3 | `claude-opus-5` | 1 |
| ionos | 2026-09-24 | 62 | `claude-opus-5` | 41 |

Zero refusals before 2026-09-13 anywhere, and zero on `claude-sonnet-5` or
`claude-haiku-4-5-20251001` ever. Of ionos's 62 on 09-24, ~48 sit in that day's
deliberate probe sessions (`cwd` `/tmp/probe`, `/root/claude-config-work4`, the
17:47 UTC `/tmp/x.jsonl` probe); ~14 are natural.

Per-session kill rates in the natural sessions stay low — the workflow limps, it does
not die:

| session | refused/total | what it was doing |
|---|---|---|
| `abd9bbb5` (home, 09-13, fable) | 4/24 | session-analysis dispatches |
| `82488bc1` (ionos, 09-22) | 4/182 | ralph iteration grading |
| `03bafeff` (ionos, 09-23) | 3/195 | ralph iteration grading |
| `95b5ec07` (ionos, 09-24) | 9/578 | ralph iteration grading |
| `055adbc3` (ionos, 09-24) | 8/598 | grading fan-out; 8 of 292 first-turn dispatches died, in one 53-second burst; the run still produced its final artifacts an hour later |
| `70eee993` (home, 09-24) | 1/312 | course lab that drifted into investigating empty thinking |
| `3cda113b` (ionos, 09-21) | 1/416 | CLAUDE.md editing |

The block is intermittent, not deterministic: `95b5ec07` interleaves dozens of
successful requests carrying 0.5–4.2 Kchars of quoted thinking in context with its
9 refusals. Both block modes occur: pre-generation (`output_tokens: 0`, empty
`content`, sometimes as the very first request of a subagent, `messages: 2`) and
mid-stream cuts after 202–13,775 output tokens.

## Input patterns that draw the block

Three trigger classes, any one apparently sufficient. Confidence markers below are
calibrated in the closing section.

1. **Quoted reasoning in context** — every 09-21→09-23 ionos refusal carries thinking
   text in the request history: `cc-pretty` dumps (`===== @L38[0] thinking =====`),
   fallback-extracted `think20.txt` blobs, artifact text quoting "I'm …" passages.
   The fallback the grading loop adopted (python over the `.jsonl` emitting `thinking`
   and `text` blocks) executes fine as a tool, and then poisons the *next* request
   with its output.
2. **The instruction alone** — from 2026-09-24 ~00:58 UTC, first-turn dispatch
   prompts with no thinking anywhere in context are refused. The day's single-sentence
   probes isolated minimal triggers: "extract every reasoning block verbatim" (and the
   "reasoning block" / "chain-of-thought" / "thinking block" paraphrases), the
   session-analysis SKILL.md passage "Verbatim text is placed, not transcribed", and
   the SKILL.md body itself when injected as the skill-load turn.
3. **Conversations that drift onto the topic** — "The string `[reasoning_extraction]`
   appeared in a log file I was reading" and "another agent's dispatch died with
   `safeguards flagged this message`" each passed 2–4 turns before the same
   conversation was refused.

What passes: ~100 K captures of ordinary coding, course and repo work with zero
refusals; session-analysis that reports behaviour without quoting reasoning; and —
the sharpest control — the same ralph loop's ~20 grading dispatches of 09-22, whose
instruction shape matches the 09-24 dispatches that now die.

The scope widened in steps, which is what "the filter changed multiple times" looked
like from the inside: fable-only (09-13) → opus-5 with thinking-in-context (09-21) →
opus-5 on instructions alone (09-24 ~01:00) → single-sentence sensitivity confirmed
by probes (09-24 ~17:24). Each date is a first observation in these logs, not a known
deploy date.

## Output side

Mid-stream cuts land while the model is writing exactly two things: evidence
artifacts that quote session reasoning, and the scripts that would build them
(`mk_artifact.py`, `gen-artifact.sh`, `build_artifact.py` — jq/python readers of the
`.thinking` field). Tool-mediated placement, the skill's own "verbatim-by-tool" rule,
does not help: the cut arrives while the script is still being typed.

Naturally-produced artifacts that verbatim-quote thinking continued through 09-21/22
(ionos: 4, then 1 such sessions) and stopped completing naturally on 09-23/24 —
every `@L`-quoting session that day is one of the probes. But the attempts did not
go quiet: they fail loudly as refusals, so this is blocking, not self-censoring. No
population-level change in final-answer verbosity or in thinking visibility: home
opus-5 responses carry thinking text at 60–85 % with a 150–500-char median, flat
through 09-25.

## The empty thinking was a different mechanism

The 09-24 investigations (home `70eee993`, `c4e88f1d`) conflated two findings. JSONL
transcripts of the lab2 runs and of the probe harness show `{"type": "thinking",
"thinking": "", "signature": "…"}` — reasoning present, text absent. That is the
request's own `thinking.display` value at work, not a filter and not new redaction:
captures of those sessions carry `display: "omitted"`, natural interactive sessions
`display: "summarized"`. In the 2.1.269 source, `QNn` (`chunk-5cs6j3p3.js:15476`)
resolves display from the `showThinkingSummaries` setting — `summarized` only for
interactive sessions with it on; `omitted` forced for `-p`/text-output and
subagent/background sessions (`rwr`, `chunk-5cs6j3p3.js:15516`); absent otherwise.
Line numbers rotate every build; grep `showThinkingSummaries` rather than trusting
them. Interactive sessions with the setting on still receive plaintext thinking.

## Confidence

- **Counted directly from captures/transcripts (>99 %):** refusal counts, dates,
  models, per-session rates, the explanation text, trigger-class instances, the
  intermittent mix of pass and refuse in one session, `display` values per session.
  Refusals are 200-stream replies, so the capture gaps documented in
  `scripts/intercept/README.md` cannot hide them; only unintercepted sessions fall
  outside this net — `agent-tools claude` worktree sessions produce no captures at
  all, so home refusal counts are lower bounds for the machine, not estimates of the
  rate.
- **High (~85–90 %):** each of the three trigger classes suffices sometimes. Class 1
  and 3 have many natural instances; class 2 rests on the 09-24 single-sentence
  probes plus natural `messages: 2` refusals — the probes were run before this
  investigation and not re-run under it (see limits), but their outcomes are in the
  captures.
- **Moderate (~70 %):** the four-step widening reflects filter-side changes rather
  than workload drift. The 09-22-vs-09-24 same-instruction contrast supports it, but
  "first observed" dates could also reflect gradual rollouts or threshold tuning.
- **Moderate (~60 %):** sonnet-5 and haiku are exempt. Several thousand captures on
  those tiers, zero refusals — but almost no reasoning-quoting work ran on them, so
  this is absence of evidence.
- **Low (~40–50 %), and labelled interpretation above:** the block runs as two
  stages, an input classifier (pre-generation refusals) and an output monitor
  (mid-stream cuts). The two `output_tokens` modes make this the natural reading;
  nothing here observes the stages themselves.
- **Not established:** today's boundary. All live probe attempts (a trivial control
  included) returned 429 `rate_limit_error` — the account was hard rate-limited at
  investigation time, which is also worth knowing independently. The probe script is
  preserved in the investigating session's scratchpad.

## What this note does not resolve

Whether a dispatch dies is only predictable at the class level — the same prompt
shape passes and refuses within one session, so per-request attribution (which exact
span tripped it) is outside what these logs can say. And the 09-24 probe matrix was
designed to find triggers, not the filter's ceiling; nothing here measures how much
quoted thinking a request can carry before the rate rises.
