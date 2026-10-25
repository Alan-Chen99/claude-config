# The `total_tokens` reminder trial

Pre-registered 2026-09-25 on Claude Code **2.1.269**, before any randomized
session. `scripts/claude.sh` draws one arm per interactive session:
`CLAUDE_CODE_TOTAL_TOKENS_REMINDER` = `off` or `padded-countdown`, 50/50.

Written in advance so the outcome cannot be chosen after the fact; **no outcome
is primary yet** — one entry of the frozen list below is promoted before the
first look at randomized data.

## What it tests, and why the fixture cannot

`notes/total-tokens-reminder.md` measured the marker's *proximate* effect on one
turn: a binding budget cut reading by two thirds and got the answer wrong; at the
shipped value `off` and 15M were indistinguishable — a null that cannot transfer,
since every run reached the cause (a ceiling) and one turn cannot show a per-turn
economy compounding across turns and compactions into missing context and
rework. The fixture measures the response, this trial the consequence.

## Design

| | |
| --- | --- |
| Unit | one interactive `claude.sh` session |
| Assignment | `$RANDOM % 2` at launch, per session |
| Arms | `off` (no marker) vs `padded-countdown` (the shipped default, ~15,000,000, re-anchored each user turn), named explicitly so a GrowthBook flip cannot redefine it |
| Scope | interactive only — `[ -t 0 ]` excludes `-p` runs and so every prompt-test case |
| Blinding | impossible — the marker is in context; the draw is untraced, so the arm is at least not printed at launch |

## Arm recovery

**What was delivered.** Claude Code writes the marker into the transcript as
`attachment` records, so `grep -c '<total_tokens>' /root/.claude/projects/*/*.jsonl`
separates the arms: zero is `off`.

**One confound.** No markers is also what `CLAUDE_CODE_DISABLE_ATTACHMENTS` or
`CLAUDE_CODE_SIMPLE` produce; neither is set here today, and sessions from a
period where one is are unlabelable — dropped, not `off`.

**What was configured.** `agent-tools hook-provenance` writes the launch
configuration into the same JSONL, out of the model's context: the launcher
chain verbatim, every `CLAUDE_CODE_*` variable in force, every settings file
readable:

```bash
jq -r 'select(.attachment.type=="hook_success") | .attachment.stdout
       | select(startswith("<launch-provenance"))' <session>.jsonl
```

The count says which arm ran, not which arm *set* the draw was over; with a
third arm only the launcher's text, embedded here, tells the treatments apart.
`grep -L '<launch-provenance'` also checks the draw still happens — no record
and no marker is unlabelled, not `off`. Records begin 2026-09-29.

**Whether the launcher drew it.** After `exec` a drawn value and a
caller-exported one are the same variable, so `scripts/claude.sh` labels the
path it took, in the same block:

| `CLAUDE_SH_TOKENS_REMINDER_SOURCE` | Means |
| --- | --- |
| `draw` | randomized at launch; the session is in the trial |
| `caller` | the environment already carried a value — chosen, not drawn; excluded |
| `skipped-not-interactive` | no tty, no draw, variable unset: a `-p` run, which Claude Code configures for itself |

Absent before 2026-09-30, when the embedded launcher text answers instead.

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

`settings.json` sets `autoCompactWindow: 600000` since 2026-10-18 (`640abd00`),
and `400000` from 2026-09-25 — after the draw went live — until then, so the
sessions fall in three strata; it reaches a session through the
`~/.claude/settings.json` symlink into the canonical checkout.

Auto-compaction then fires at **567,000** context tokens (367,000 at `400000`)
against 967,000 before — the window less `min(maxOutputTokens, 20000)` less a flat 13,000 (`SK` →
`MJ` → `GQ`, `src/chunk-j0tbz6ra.js:64535`, `:64468`, `:64109`; Opus 5's window
1e6 at `src/chunk-dvghjmtr.js:668-676`), compared live off
`n.options.autoCompactWindow` (`chunk-j0tbz6ra.js:101421`, `:101483`). Re-derived on 2.1.289 and
again on 2.1.310, unmoved. The clamp only lowers — `TS()` returns `Math.min(modelWindow, n)`
(`:64296`) — and 2.1.288's server-supplied window is read only after the
settings key (`:64318` before `:64336`), so it does not displace this one.

**A covariate, not a second treatment.** Outcomes 2–4 are counted per
compaction, so the clamp moves their denominator: one stratum before, another
after, arms randomized inside each. The treatment cannot move:
`padded-countdown` emits `JZ() − cumulativeUsed`, which carries rolled-over
tokens across every compaction (`chunk-j0tbz6ra.js:137421`, `:90151`; rollover
`src/chunk-f0m66zs2.js:95`, unconditional since 2.1.310), so it reads the same at either window; `countdown`,
whose subtrahend is the current message list, would move — no arm draws it.
The split buys yield and dates itself: at 367,000 a long session compacts about
2.6× as often (at 567,000, 1.7×), so each session supplies more of the events outcomes 2–4 count,
and a first compaction near 367k or 567k rather than 967k recovers the stratum
without the commit date.
