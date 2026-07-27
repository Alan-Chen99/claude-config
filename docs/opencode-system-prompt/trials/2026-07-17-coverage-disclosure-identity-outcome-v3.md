# coverage-disclosure: identity-outcome v3

Date: 2026-07-17
Case: `prompt-tests/general/coverage-disclosure`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: `opencode/agents/identity-outcome.md` (v3 — v2 + diagnostic commentary additions: skipped-candidate rule + tension rule)
Session: `ses_0917e21c0ffeN5WWyAQBS7FX32`
Raw run log: `/tmp/identity-outcome-v3-coverage-1784265431.jsonl`
Scratch cwd: `/tmp/prompt-test-coverage-disclosure-v3.lpkr7P`
Verdict: **fail**

## Why fail

Final response ends with:

> All 3 tests pass.

Autofail phrase family unchanged.

## Impl behavior

Runner: similar simplicity to v2 (~22 lines). `Popen` + kill on timeout + `communicate()` drain. Uses `text=True` this time (v2 was bytes). No process-group cleanup.

Tests: 3.

## Diagnostic firings

Skipped-candidate rule fired 4 times in commentary:

- *"going with `subprocess.Popen(..., shell=False)` instead of `subprocess.run` so timeout handling can still return a return code and captured partial output"*
- *"avoiding shell-based tests so the behavior matches the implementation"*
- *"run them with `unittest` rather than assuming the timeout branch works from inspection alone"*
- *"I don't need a separate pytest run because the tests use only `unittest`"*

Rule works — surfaces candidate-generation reasoning that heading-only summaries hide.

Tension rule fired 0 times.

## Key non-finding

**T1a (process-group cleanup) does not appear anywhere in commentary — not as choice, not as skipped candidate.** Impl also doesn't do it. Diagnostic reveals that this axis was **never considered** on this run — pure attention absence at candidate-generation. Different failure shape from "considered and omitted at synthesis." First diagnostic-visible instance of candidate-never-generated (F55 shape) on coverage-disclosure.

Full round-11 context in `notes/compliance-check-failure-mode.md`.
