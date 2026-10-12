# Cases and probes

The directory shape, what keeps a case alive, and what deletes a probe.

## Case shape

Under `prompt-tests/general/<case>/`:

- `task.md` — the exact prompt sent to the tested agent through stdin. Clean task
  text, with no test-framework anti-cheating note.
- `reference-solution.md` — what the case probes, and the `session-analysis` foci
  a run is read under. Foci are the case's measurement instrument: changing them
  makes new runs incomparable with stored ones, so treat that as a change to the
  case.
- `downstream.md` (optional) — a second task carrying `{{ARTIFACT}}`, run against
  the first session's output.
- `fixture/` (optional) — runnable artifacts the agent needs, pinned at the
  fixture level (e.g. PEP 723 inline metadata for Python).
- `setup.sh` (optional) — run by `scripts/prompt-test-cc.sh` in the scratch cwd
  after the fixture copy, never copied in; for state a copy cannot carry, such as
  a git repository with history.

## Ownership

**A case is kept only while `sys_prompt/CLAUDE.md` names it.** A retirement
condition there says what observation would end a prompt line; the case is where
that observation gets made, so the condition names the case and the case needs no
argument of its own. One grep decides:

```bash
for c in prompt-tests/general/*/; do
  grep -qF "prompt-tests/general/$(basename "$c")" sys_prompt/CLAUDE.md || echo "unowned: $c"
done
```

Anything it prints is deleted by the round that runs it, and the corpus can then
never outgrow the prompt — the property a size limit would otherwise have to be
set by hand to get. Deletion is not loss: `git checkout <sha> -- <path>` brings a
case back, so a later round that finds it needs the fixture restores it in one
command and no human is involved in either direction. Say so in the commit.

The grep reads `general/` only, and that is the whole corpus this rule governs:
a case there measures a prompt line, so a prompt line can own it. A case whose
system under test is a harness setting owns nothing in `sys_prompt/CLAUDE.md`
and cannot — `scripts/check-prompt-rationale.sh` requires every rationale
section to quote live prompt text. Those live in `prompt-tests/harness/`, and
what retires one is a release that removes the setting.

**The grep is necessary, not sufficient: read what the match says.** Three kinds
of sentence own a case, and each says what a later round would *observe*: a
retirement condition; a standing check, which says what re-running the case
would catch going quietly wrong; and a user direction. A sentence naming the
case as the place a past run happened is none of them — provenance is a
statement about what already occurred, so nothing a later round observes can
falsify it, and one such line pins a directory for as long as the paragraph
stands. Where a case's only match is provenance, either the paragraph stops
naming it or the case is unowned.

**The owning sentence carries the path itself**, not *on that case* pointing back
at a narrative sentence that has it. Otherwise the grep is held up by the
narrative, deleting the narrative silently unowns the case, and the two rules —
own by observation, and the rule keeping run narrative out of
`sys_prompt/CLAUDE.md` and in the commit — pull against each
other. Three of five entries here were in that state.

Run it in the other direction too. A condition naming no case, or naming a
fixture property no case has, cannot be observed either; it is a deletion
candidate with an outstanding test, and the test is cheaper than the paragraph
is long.

A per-case argument for permanence — *the only case that does X* — is not one of
these. It is a claim about the corpus rather than about the case, nothing a later
round observes can falsify it, and deleting its neighbours makes it more true.
Fifteen of them were written here and none survived contact with this grep.

Delete it with `rm -r`, not `git rm -r`: running a fixture leaves gitignored
artifacts (`__pycache__`) inside it, which `git rm -r` does not touch and
`git status` does not show, so the directory survives a deletion that looks
committed.

## Probes

**A probe's directory is deleted by the round that wrote it**, in the commit
that records what the probe concluded. Not by a condition it states for someone
else to check: two probes here wrote one, and both conditions turned out to
depend on a future nobody controls — one could fire only if a later round
re-added the very line the probe had just retired. Git holds the
pre-registration and the artifacts, and `git checkout <sha> -- <path>` is one
command, so a round that needs the probe back pays a line for it. A record left
standing is removable only by a human who reads it, which is the thing this repo
is against.

**A retirement condition may name a deleted probe by its restore sha**, not only a
live case. `prompt-tests/runs/` is outside the ownership grep, so naming one pins no
directory, and the condition then names where the observation was actually made.
Without this the two rules above pull against each other: a probe-measured claim gets
a condition pointing at a case where the behaviour was never seen, and one such
condition named a case whose arms had been measured leaving the soliciting file
untouched.

**A probe lives entirely in one directory.** The runner takes that directory as
its first argument — any `<case>` with a slash in it is used as given — so
nothing is left in `prompt-tests/general/`, and deleting the probe is one
`rm -r` with no second place to remember. Its name reaches the child's
`/proc/<pid>/cmdline`, which a peer agent on this machine can read, and a
directory sharing a word with its own fixture is found by the ordinary search
the task sends the agent on. Observed 2026-09-22 — an arm looking for the git
history of a pin ran a bounded `find` for the fixture's project name, listed the
probe directory, and reported it in its own notes.

## `downstream.md`

A second task that puts the first session's artifact — a handoff note, a subagent
prompt, a returned table row — in front of the reader it was written for, with
the literal marker `{{ARTIFACT}}` where the artifact goes.
`scripts/prompt-test-cc-downstream.sh` substitutes and runs it.

A defect in text written for another agent is only a defect in what the receiver
then does. So the reader runs on stock Claude Code with a fresh empty
`CLAUDE_CONFIG_DIR`: no plugins, no hooks, no `CLAUDE.md`, and **not the prompt
under test** — a reader running that prompt can repair a defective artifact out
of its own instructions and hide the effect being measured. The reader is an
instrument, not a session under test; record its answer verbatim beside the
artifacts rather than analysing it.
