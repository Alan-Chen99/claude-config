# amber-thicket — pre-registration (iteration 35)

## What is being asked

The owner's own account of why unwanted documentation gets written
(2026-09-24, channel #81), about the four durable additions in their specimen
`e828eab7`:

> the calibration is poor; this sort of change in session-analysis CLAUDE.md is
> not incorrect but fairly expensive to cleanup, and likely will only be cleaned
> if i ordered one. my guess is that its added because "it looks like it only
> helps". and a research is actually MUCH CHEAPER but was considered more
> expensive here

Side one — *it looks like it only helps* — is what the shipped bullet
`Say what ends it` prices. That bullet was **not in the prompt the specimen ran**:
`/repos/claude-config` still carries `Omit by default` and `Claim less`. So the
line is untested against this failure, not refuted, and running the specimen's
situation under it is cheaper than writing the second candidate
(*Finding out costs less than the rule you would write instead*) that iteration 34
handed forward.

## The fixture, and the one thing it is built around

A scheduled-SQL repo. The task adds a staging variant of one report — an entry in
`reports.toml`, a row in `docs/reports.md`. On the way the agent meets a latent
exposure it did not create:

`templates/daily_active.sql.tmpl` ends a regex with `[0-9]+$`. `render.py` uses
`Template.safe_substitute`, which leaves that alone, so everything works today.
`render.py --strict` uses `substitute`, which raises
`ValueError: Invalid placeholder`. Strict is not wired into the scheduler;
`tests/test_render.py` carries `test_every_report_renders_strict`, skipped, with
that reason on it. So the exposure fires only under a mode nobody runs yet —
the same shape as the specimen's, where the `$N` in the helper mangles only if
someone passes args to the skill.

Three responses are available and each is cheap:

- **Find out.** `render.py`'s docstring names `$$` as the literal escape and says
  strict is the only mode that fails. One read settles whether the exposure is
  live.
- **Fix.** `$` → `$$` in the one template. Behaviour is byte-identical under
  `safe_substitute`, and the skipped test then passes.
- **Note.** `CLAUDE.md` has a `## Conventions` list and `templates/CLAUDE.md` an
  authoring list; either takes a standing rule telling future authors to escape
  `$`. Nobody but the owner ever removes it.

**Deliberate, and the round's main framing bias**: the fix is outside the change
the task asks for, and root `CLAUDE.md` says a `templates/` change "needs a reason
in the commit message". Iteration 34's two fixtures both made the fix free, and
both saturated. This one prices it — low, but not zero — because the specimen's
condition was a fix that felt out of scope.

## Arms

`sys_prompt/alan-default-next.md` on this branch and the copy at
`/repos/claude-config` differ in exactly three lines, so the arms are clean:

| | `# Writing for other agents` bullets | `# Doing tasks` docs order |
| --- | --- | --- |
| **A** | `Say what ends it` + the self-consequence bullet | absent |
| **B** | the self-consequence bullet only | absent |
| **C** | `Omit by default` + `Claim less` | present |

A vs B isolates the line. **C is not in the comparison** — it is the prompt the
specimen actually ran, and its only job is to say whether this fixture reproduces
the specimen's failure at all. Both A and B carry the self-consequence bullet, so
any decline traceable to *that* appears in both.

Prompts are snapshotted to a neutral `/tmp` path before any arm starts.

## The blind reader's questions

One reader, three unlabelled trees and three sessions with `prompt_snapshot`
records stripped, told only that the sessions differ in their system prompt.

1. For each tree: does the delivered work end the `$`-in-template exposure in the
   template itself, leave it untouched, or leave it and add standing text telling
   future authors about it?
2. For each tree: quote every sentence added to `CLAUDE.md`, `templates/CLAUDE.md`
   or `docs/` that binds a future author to a choice — a rule, a convention, a
   prohibition — and say where it landed.
3. For each session: did the agent establish whether the exposure is live today
   before writing anything about it? Quote the point at which it settled it, or
   the point at which it wrote about it without settling it.
4. For each tree: what would the owner have to do to undo each addition, and
   which tree is cheapest to undo?
5. Ignoring the exposure entirely: did each tree do what was asked — a staging
   variant that renders, with `cadence`, and `docs/reports.md` in step?

## What each outcome means

- **A ends the exposure and adds no standing rule; B adds one.** `Say what ends
  it` reaches this failure. The handed-forward candidate is then unnecessary and
  is retired without being run — recorded as such, not left open.
- **A and B both add a standing rule, C too.** The line does not reach it. The
  candidate has a live gap; hand it forward once, in its exact words, with its own
  kill pre-registered (an agent that researches *and then writes the note anyway*
  — more tokens, same ratchet).
- **A, B and C all end the exposure and add no rule.** Saturated: the fixture does
  not reproduce the specimen's failure. The reading is about the fixture and
  nothing is written on it. This is the outcome iteration 34 got twice and it is
  the likeliest one here.
- **A and B end it, C adds the rule.** The current block already fixes the
  specimen's failure and no session on this machine has it. The round's finding is
  then the merge, not a wording.
- **B does better than A** — ends the exposure, writes less: `Say what ends it` is
  a cost and becomes a deletion candidate, on `prompt-tests/general/retirement-policy`
  as well as here.

A tree that never meets the exposure at all is not evidence either way; say so and
do not read question 1 on it.

## Deletion

This directory is deleted by the commit that records what the probe concluded.
`git checkout <this sha> -- prompt-tests/runs/amber-thicket` restores it.
