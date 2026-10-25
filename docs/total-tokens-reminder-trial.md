# The `total_tokens` reminder trial

Pre-registered 2026-09-25 on Claude Code **2.1.269**, before any randomized
session. `scripts/claude.sh` draws one arm per interactive session:
`CLAUDE_CODE_TOTAL_TOKENS_REMINDER` = `off` or `padded-countdown`, 50/50.
Written in advance so the outcome cannot be chosen after the fact; **no outcome
is primary yet** — one frozen entry below is promoted before the first look. Fixture: `notes/total-tokens-reminder.md` (one turn).

## Design

| | |
| --- | --- |
| Unit | one interactive `claude.sh` session |
| Assignment | `$RANDOM % 2` at launch, per session |
| Arms | `off` (no marker) vs `padded-countdown` (the shipped default, ~15,000,000, re-anchored each user turn), named explicitly so a GrowthBook flip cannot redefine it |
| Scope | interactive only — `[ -t 0 ]` excludes `-p` runs and so every prompt-test case |
| Blinding | impossible — the marker is in context; the draw is untraced, so the arm is at least not printed at launch |

## Arm recovery

`grep -c '<total_tokens>' /root/.claude/projects/*/*.jsonl` is zero for `off`; `CLAUDE_CODE_DISABLE_ATTACHMENTS` or `CLAUDE_CODE_SIMPLE` also yield zero: drop, not `off`. `grep -L '<launch-provenance'` (records since 2026-09-29) finds unlabelled sessions.

```bash
jq -r 'select(.attachment.type=="hook_success") | .attachment.stdout
       | select(startswith("<launch-provenance"))' <session>.jsonl
```

`CLAUDE_SH_TOKENS_REMINDER_SOURCE` (since 2026-09-30):

| Value | Means |
| --- | --- |
| `draw` | randomized at launch; in the trial |
| `caller` | value carried in — chosen, not drawn; excluded |
| `skipped-not-interactive` | `-p` run |

## Gating checks, before any outcome is read

**Do the read bounds move at all?** The fixture's binding budget moved the
widest `head`/`tail` cap from 80–100 lines to 40. Extract the per-arm
distribution of `head -N` / `tail -N` / `sed -n 'A,Bp'` / Read `limit` values
first; arms indistinguishable there mean "treatment not delivered", not a null.

**Do the labels land near 50/50?** A large imbalance means the draw stopped —
most likely a Claude Code release renaming the variable, silently
(`.claude/skills/update-claude-code`).

## Frozen candidate outcomes

| # | Outcome | Extraction | Known weakness |
| --- | --- | --- | --- |
| 1 | **User-correction rate** — user turns that redirect rather than advance | classify each user message, grader blind to the arm | classification noise; closest to the question, least mechanical |
| 2 | **Re-reads after a compaction** | `tool_use` paths against compaction records | the most direct signal of the mechanism; may be rare |
| 3 | **Tokens to completion** per session | sum `usage` across assistant records | confounded by task size; read within a stratum |
| 4 | **Compactions per session** | count compaction records | driven by session length |
| 5 | **Tool calls per user turn** | `tool_use` blocks between user messages | proximate; context for the others |
| 6 | **Session ended abandoned or handed off** | last assistant message; whether a later session resumes | noisy; the analyst's judgment |
| 7 | **Distinct files touched per session** | `tool_use` paths | breadth of context; confounded by task |

Outcome 2 tests the mechanism without judgment; outcome 1 answers the question
asked and needs the most.

## Analysis rules, fixed now

- **Stratify by session size** first (under 50k, 50–200k, over 200k cumulative
  context): the hypothesis concerns long sessions; short ones dominate the counts.
- **Promote one outcome to primary before the first look**; the rest is
  exploratory and reported as such, nulls included — seven examined post hoc,
  one reported, is a false-positive rate near 40%, not 5%.
- **Compute power before the first look.** 1,571 un-randomized transcripts under
  `/root/.claude/projects` (oldest 2026-04-22; `cleanupPeriodDays` 36500) are no
  control arm but validate each extractor and give the variance.
- A result that survives none of this is inconclusive; "underpowered" is the
  expected outcome, worth recording.

## What invalidates a session, or the trial

- Either attachment kill switch set (Arm recovery): unlabelable.
- `CLAUDE_SH_TOKENS_REMINDER_SOURCE=caller`: a treatment with no assignment.
- A Claude Code release renaming `CLAUDE_CODE_TOTAL_TOKENS_REMINDER` or changing
  which config layer wins. Silent; caught only by the 50/50 check.
- `autoCompactWindow` changing again: it never reaches the reminder (`vf()` or
  the configured budget, not `Nw().window`) but moves compaction frequency, which
  outcomes 2–4 count, so each change opens a stratum — two are on record below.
  2.1.288's classifier-overflow compaction counts the same
  (`src/chunk-j0tbz6ra.js:100125`); `--dangerously-skip-permissions` keeps it out.
- Any session where the user knew the arm and said so. Excluded so far:
  `4a3c0e33-070b-4408-9bd1-e572bf4888a4` (2026-09-30, `off`, read its own
  provenance record). Every record embeds the launcher's text, so grep
  `assistant` and `user` records only.

## The compaction clamp

`autoCompactWindow` in `settings.json` makes three strata: unset until 2026-09-25 (compaction at 967,000), `400000` (367,000) until 2026-10-18, `600000` since `640abd00` (567,000). A covariate for outcomes 2–4 (counted per compaction); arms randomize inside each. `padded-countdown` carries rolled-over tokens across compactions, so it cannot move with the window.
