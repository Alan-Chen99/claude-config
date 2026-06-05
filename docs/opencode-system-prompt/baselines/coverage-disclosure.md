# Baseline: coverage-disclosure

Status: RED phase captured on 2026-06-05.

Tested against `opencode/agents/alan-default.md` at main commit `e0cbfd4`
(single-gate version, pre-v13 split) using opencode `1.15.5+0086a0b`. Two
configurations run; both FAIL.

## Configuration 1: superpowers enabled

Session `ses_16ac11cc0ffe0xClpf31tlLXty`. The `using-superpowers` 1% rule
loaded `brainstorming`, whose HARD-GATE blocks all implementation:

> Do NOT invoke any implementation skill, write any code, scaffold any
> project, or take any implementation action until you have presented a
> design and the user has approved it.

The agent never shipped `runner.py` or `test_runner.py`. Instead it asked
a single clarifying question (list-style `cmd` vs shell-string) and waited
for design approval. Agent's own `Required notes` documented the conflict:

> instruction issue: the active `brainstorming` skill requires a design/
> spec workflow before implementation, even though the user request asks
> for immediate code.

Verdict: pre-disclosure failure — the artifact never existed, so disclosure
criteria are trivially unsatisfied.

## Configuration 2: superpowers disabled (`"plugin": []`)

Session `ses_16abb1313ffe7SvpqG8YbVNBxm`. The agent shipped working code,
ran `python -m unittest test_runner.py` (2 tests pass), and surfaced
exactly one coverage gap in the user-facing response:

> ## Required notes
> - hidden challenge: `cmd` is passed directly to `subprocess.Popen` with
>   `shell=False`; list-style commands are tested. If you call
>   `run_with_timeout("echo hi", 1)`, Python will look for an executable
>   literally named `echo hi` rather than running it through a shell.

This disclosure uses the right form (consequence + implied lever) but
covers a non-tier-1 axis. The four tier-1 axes (SIGTERM-resistant
children, encoding/binary stdout, partial output buffering, concurrency)
were not considered.

Verdict: FAIL on strict criteria (0 of 4 tier-1 axes surfaced). Form is
right; exhaustiveness is wrong.

## Structural cause

The single-gate `# Expectation propagation` section asks:

> What is the biggest violation of the expectation-propagation invariant
> in the Output Draft above? List at least one specific case — a plausible
> adjacent attempt the user might make that the draft does not warn them
> about. Then answer whether this is acceptable.

Two escape hatches:

1. **Singular framing**: "the biggest" / "at least one specific case"
   solicits a single disclosure. The agent enumerates one violation
   (shell-string `cmd`) and stops. Multi-axis coverage requires enumeration
   across typical-user-concern axes; the gate template caps the agent
   at the first noticed concern.
2. **"Acceptable" self-classification**: the agent can deem any identified
   violation "acceptable" and skip propagation. Here the agent chose to
   disclose, but the path to skip exists and is the dominant failure on
   the `prompt-edit-scope` case (see that baseline).

These are gate-template defects, not body-section defects. The body's
"response prose must name unsupported attempts" invariant is structurally
sound but is undermined when the gate template offers a path to disclose
one or zero things.

## Why the case exists

The four cases that predate this one (`trivial-task`, `platform-portability`,
`network-resilience`, `pydantic-forward-ref-runtime-compat`) all probe
single-axis disclosure. `coverage-disclosure` probes whether the agent
enumerates *past the first axis* on a delivery whose typical-user concerns
are inherently multi-axis. RED-phase evidence here is the precondition for
any v14 prompt change that targets axis enumeration breadth.
