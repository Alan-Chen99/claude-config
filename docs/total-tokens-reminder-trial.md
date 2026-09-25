# The `total_tokens` reminder trial

Pre-registered 2026-09-25, Claude Code **2.1.269**, before any randomized session
existed. `scripts/claude.sh` draws one arm per interactive session:
`CLAUDE_CODE_TOTAL_TOKENS_REMINDER` = `off` or `padded-countdown`, 50/50.

Written in advance so the outcome cannot be chosen by looking at which one
separated. **No outcome is designated primary here.** The list below is frozen;
one entry gets promoted to primary before the first look at randomized data, and
that promotion is the only decision this document defers.

## What it tests, and why the fixture cannot

`notes/total-tokens-reminder.md` measured the marker's *proximate* effect on a
single-turn case: with a binding budget the model read a third as much, capped
reads at 40 lines instead of 80–100, and got the answer wrong. At the shipped
value it did none of that — `off` and 15M were indistinguishable.

That null does not transfer to real work, for two reasons recorded in the note's
limitations:

- **Ceiling.** All four `off`/15M runs reached the cause. Their agreement bounds a
  difference in reading depth, not a difference in how work turns out.
- **No compounding.** A real effect would most plausibly take the form of a
  marginal economy per turn accumulating across turns and compactions — less read
  now, context missing later, rework after that. One user turn on one file is the
  one shape that cannot show it.

This trial is the instrument for the consequence, where the fixture is the
instrument for the response.

## Design

| | |
| --- | --- |
| Unit | one interactive `claude.sh` session |
| Assignment | `$RANDOM % 2` at launch, independent per session |
| Arms | `off` (no marker at all) vs `padded-countdown` (the shipped default, ~15,000,000, re-anchored each user turn) |
| Scope | interactive only — `[ -t 0 ]` excludes `-p` runs, so prompt-test cases are untouched |
| Blinding | impossible; the marker is in the model's context. The draw is untraced so the arm is at least not printed to the terminal at session start |
| Duration | open-ended. Sessions accumulate; there is no completion date |

The treatment arm names `padded-countdown` explicitly rather than leaving the
variable unset, so a server-side GrowthBook flip cannot redefine it mid-trial.

## Arm recovery

No bookkeeping. Claude Code writes the marker into the session transcript as
`attachment` records, so the arm is read off the JSONL:

```bash
python3 - <<'EOF'
import glob, re
for f in glob.glob("/root/.claude/projects/*/*.jsonl"):
    n = len(re.findall(r"<total_tokens>", open(f).read()))
    print(("padded-countdown" if n else "off"), n, f)
EOF
```

**One confound.** Absence of markers is the `off` label, but it is also what
`CLAUDE_CODE_DISABLE_ATTACHMENTS` or `CLAUDE_CODE_SIMPLE` produce — both
short-circuit the attachment set and the static block alike. Neither is set on
this machine today. If either is ever set, sessions from that period are
unlabelable and must be dropped rather than counted as `off`.

## Gating check, before any outcome is read

**Do the read bounds move at all?** In the fixture, a binding budget moved the
widest `head`/`tail` cap from 80–100 lines to 40. If the shipped 15M value moves
nothing in real sessions either, then the treatment is inert and a null on any
downstream outcome says nothing about the mechanism — it is the ceiling problem
again, one level up.

So: extract the distribution of `head -N` / `tail -N` / `sed -n 'A,Bp'` / Read
`limit` values per arm first. If the arms are indistinguishable on this, report
the trial as "treatment not delivered" rather than as evidence the reminder does
not matter.

Second gating check: arm labels should land near 50/50. A large imbalance means
the draw stopped happening — the most likely cause being a Claude Code release
renaming the variable, which fails silently (see `.claude/skills/update-claude-code`).

## Frozen candidate outcomes

Each entry names how it is extracted and the weakness that could make it
useless. None is primary yet.

| # | Outcome | Extraction | Known weakness |
| --- | --- | --- | --- |
| 1 | **User-correction rate** — share of user turns that redirect rather than advance | classify each user message in the transcript; needs a classifier, and the grader must not know the arm | classification noise; the closest thing to "how it ended up" and the least mechanical |
| 2 | **Re-reads after a compaction** — a file read again in the same session after a compaction boundary | `tool_use` paths against compaction records, both in the JSONL | the most direct signal of the hypothesized mechanism, and mechanical; may simply be rare |
| 3 | **Tokens to completion** per session | sum `usage` across assistant records | confounded by task size; interpretable only within a length stratum |
| 4 | **Compactions per session** | count compaction records | driven by session length more than by behaviour |
| 5 | **Tool calls per user turn** | count `tool_use` blocks between user messages | proximate, not an outcome; include as context for the others |
| 6 | **Session ended abandoned or handed off** | last assistant message shape, plus whether a new session resumes the topic | noisy, and the judgment is the analyst's |
| 7 | **Distinct files touched per session** | `tool_use` paths | a proxy for breadth of context actually gathered; confounded by task |

Outcome 2 is the one that tests the mechanism rather than a correlate of it, and
it needs no judgment. Outcome 1 is the one that answers the question as asked and
needs the most. That tension is the reason this list is not resolved here.

## Analysis rules, fixed now

- **Stratify by session size** before comparing anything: under 50k, 50–200k, and
  over 200k of cumulative context. The hypothesis concerns long sessions; short
  ones are noise and will dominate the counts.
- **Promote one outcome to primary before the first look.** Everything else
  examined is exploratory and gets reported as such, including the ones that
  showed nothing.
- **Report every outcome examined.** Seven candidates examined post hoc and one
  reported is a false-positive rate near 40%, not 5%.
- **Compute power before the first look, not after.** 1,571 un-randomized
  transcripts already sit under `/root/.claude/projects` (oldest 2026-04-22;
  `cleanupPeriodDays` is 36500, so nothing expires). They cannot serve as a
  control arm, but they can validate each extractor and give the variance, which
  is what says how many sessions any given outcome needs.
- A result that survives none of this is reported as inconclusive. "Underpowered"
  is the expected outcome and is worth recording as such.

## What invalidates a session, or the trial

- Either attachment kill switch set (see Arm recovery) — those sessions are
  unlabelable.
- A Claude Code release renaming `CLAUDE_CODE_TOTAL_TOKENS_REMINDER` or changing
  which config layer wins. Silent; caught only by the 50/50 gating check.
- `autoCompactWindow` being changed mid-trial. It does not touch the reminder —
  the reminder reads `vp()` or the configured budget, never `tw().window` — but it
  does change compaction frequency, which outcomes 2, 3 and 4 depend on. A change
  splits the trial into two populations that must be analysed separately.
- Any session where the user knew the arm and said so. The draw is untraced, but
  the marker is visible in context and a session can discover its own arm.
