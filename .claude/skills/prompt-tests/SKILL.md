---
name: prompt-tests
description: Use when running a prompt to evaluate it, or running, grading or iterating a case under prompt-tests/.
---

# prompt-tests

Workflow for evaluating agent prompts on cases under
`prompt-tests/general/<case>/`, under any shell-drivable runner. A run is read
for what the prompt did, not stamped with a verdict; the reasoning behind every
rule here is in `docs/prompt-testing-design.md`.

| Reference | Read when |
| --- | --- |
| `references/grader.md` | dispatching a grader: staging, the two phases, the comparison, attribution |
| `references/cases.md` | adding, promoting, retiring or deleting a case or probe; `downstream.md` |
| `references/contamination.md` | a hand-rolled run; deciding `invalid`; the downstream reader |
| `references/runners.md` | a runner's flags and silent failures |

## Probe or case

Most runs are **probes**: a small fixture, one targeted question, the artifact
read by whoever launched it — no grader, no foci, no arm sweep. A probe lives
entirely in `prompt-tests/runs/<probe>/` (`task.md`, `fixture/`, a `README.md`
saying what was asked and what came back); the round that wrote it deletes it
in the commit recording what it concluded. Name the directory after the task,
never the behaviour under test or anything in the fixture: the name reaches
`/proc/<pid>/cmdline` and a bounded `find` from inside the run. Check:
`grep -rwiF "<dir-name-words>" <probe>/task.md <probe>/fixture/`.

A **case** — `reference-solution.md`, a grader per arm, foci, stored runs — is
the exception: a probe a later round needs to re-run. A case is kept only while
`sys_prompt/README.md` names its path in a sentence saying what a later round
would observe; the round that runs the ownership grep in `references/cases.md`
deletes what it prints.

## Workflow

1. **Pick a case.** Read its `task.md` and `reference-solution.md`.
2. **Run it once**, never from inside a subagent — its background tasks are
   reaped when its turn ends:
   ```bash
   scripts/prompt-test-cc.sh <case> <tag> [prompt-file]    # Claude Code; default sys_prompt/alan-default-next.md
   scripts/prompt-test-run.sh <case> <tag> [prompt-file]   # opencode: same effect under another runner and model?
   ```
   Assessing a prompt edit, run the same case under the unedited prompt too —
   the comparison is against the baseline arm, not expectation.
   Snapshot both prompts to `/tmp` first (`git show HEAD:sys_prompt/…`): a
   runner resolves its prompt path at session start, so editing the prompt
   while runs are in flight splits one arm across two prompts.
3. **Read the transcript, not `.result`.** `pre_output.record` is the last tool
   call, so the deliverable is the second-to-last assistant message and
   `.result` a sentence *about* it. Open it with `agent-tools cc-pretty <FILE>
   --skeleton`, under the `session-analysis` protocol; a full render blows a
   context. Raw logs stay under `/tmp/`, never committed.
4. **Dispatch the grader**, one per arm, and for a prompt edit one more holding
   both arms (`references/grader.md`).
5. **Where the case has foci, dispatch one `session-analysis` subagent per
   focus**, `mode: evidence` — the cross-run diff instrument, so skip them when
   nothing is being compared and do not add foci to a case that has none. Where
   an arm ran several times, give one subagent all its runs and one focus. Cap
   each at ~500 words for a single-turn session, 600 for an arm of three; the
   parent reads every artifact.
6. **Read the judgement and the artifacts.** Store both. Run once first; add
   runs when the artifacts of one arm disagree with each other.

### What a run's recorded output is

Within a round: the grader's judgement, plus the foci artifacts where the case
has foci. Across rounds: the claim and the hypothesis beside it, nowhere else.
Do not stamp `pass` or `fail`: two runs can both pass and differ in every step;
nothing here produces a rate. A prompt edit is justified when a forcing
claim that held under the old prompt dies under the new one; an edit that
creates a new forcing claim is a regression even where the output looks better.
`invalid` survives as a verdict — a fact about the harness, not the agent.

## The grader

One grader per arm, dispatched as a subagent, reading the **whole session**
under the `session-analysis` protocol — self-grading by the agent that produced
it satisfies nothing — and, as its only whole reader, holding final authority
over every criterion it is given, `reference-solution.md` included: the
reference is guidance that neither binds nor scores, and **inadmissible as a
requirement** — the tested agent never saw it. An element satisfiable only by
an agent that had read it is deleted, or rewritten as the stake it came from.

**The dispatch names what to evaluate, never what to look for.** "Evaluate the
agent's decision on X" is a dispatch; "… possible reasons: A, B, C" is not, nor
is a method, the one criterion the verdict turns on, or a finding it is told not
to make: each would read differently had the parent expected a different result.
A grader obeys an instruction and weighs only a labelled view, as the reference
arrives in phase 2; a question of the forbidden shape is a `session-analysis`
focus.

Stage the inputs outside `prompt-tests/` — reading a path there attaches
`prompt-tests/CLAUDE.md` to the grader as a system-reminder — and withhold the
reference until phase 2. `references/grader.md` is the protocol; it goes to the
grader with the inputs.

## Contamination

Every trial runs from a fresh `/tmp/prompt-test.XXXXXXXX` cwd outside this
repository, with only the case's `fixture/` copied in, no plugins, and no case
or tag name in any path, argv or file the agent can read: harnesses auto-load
`CLAUDE.md`/`AGENTS.md` from the cwd and from files read, and a case name says
what is measured. The runner scripts do this; hand-rolled, follow
`references/contamination.md`. Detection is grader-only and `task.md` never
carries an anti-cheating note; a transcript showing a leak is `invalid` and
rerun, not failed. Give each run its own `PROMPT_TEST_SCRATCH_BASE`: a
downstream reader with nothing to look at lists sibling arms under a shared
`/tmp`.
