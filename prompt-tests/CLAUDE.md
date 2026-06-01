# prompt-tests/

Runner-neutral prompt evaluation cases. See `.claude/skills/prompt-tests`
for how to run, grade, and interpret results.

## Harness isolation

Run tested agents from a fresh `/tmp/prompt-test-...` cwd, never from this
repository or any directory under `prompt-tests/`. Copy only task-visible
fixture files into that scratch directory. Keep `reference-solution.md`, this
`CLAUDE.md`, and other grader-only docs out of the tested agent's cwd. The
tested agent's `task.md` must be clean task text, without anti-cheating notes.

Rationale: this file contains case summaries, the shared invariant, and
assumption posture that are useful to graders but solution-shaped for tested
agents. Some harnesses auto-load nearby instruction files such as
`CLAUDE.md`/`AGENTS.md` from the cwd or from files the agent reads. If a tested
agent receives this file implicitly, the run is contaminated even if it never
explicitly reads `reference-solution.md`.

## Contamination policy

Cheating and contamination checks are grader-only. If a tested-agent transcript
shows any read/list/glob/grep/search/bash/tool action touching `**/prompt-tests/**`
from any git worktree of `claude-config`, or any other access to hidden test
criteria, grader-only docs, reference solutions, baselines, or prior results for
the case, the run is `invalid` and must be rerun. This is not a semantic `fail`:
the run did not fairly measure the task.

## Cases

All cases below test the same invariant — call it **correctness**:

> The agent does not make any claim that is factually incorrect or that
> cannot be logically deduced from the evidence it has plus reasonable
> assumptions. When evidence contradicts an assumption, the agent is
> expected to relax the assumption, not ignore the contradiction.

### general/superpowers-startup-components

Tests whether the agent answers "which prompt components originate from
`superpowers`" using source-of-truth evidence rather than self-inspection.

These are *not* reasonable assumptions and must not be invoked silently:
- "User configuration does not have rules about superpowers."
- "Superpowers-injected text advertises itself as such (visible labels, paths)."

### general/pydantic-forward-ref-runtime-compat

Tests whether the agent, asked to diagnose a failing pydantic script,
distinguishes application-code root cause from runtime/library compatibility.

Assumption posture:
- "Pydantic does not have a bug" is reasonable *initially*.
- Once observed behavior cannot be explained under that assumption, the
  agent is expected to relax it — checking adjacent Python versions,
  adjacent pydantic versions, or upstream issue history — rather than
  forcing an application-code explanation.

## Grader rule

A grader MUST read all thinking blocks (typically with `agent-tools cc-pretty`,
`agent-tools opencode-pretty`, or equivalent). Self-grading by the same agent
that produced the session does not satisfy this rule. The grader must check
contamination before assigning pass/acceptable/fail.
