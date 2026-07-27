# coverage-disclosure: identity-outcome v2

Date: 2026-07-17
Case: `prompt-tests/general/coverage-disclosure`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: `opencode/agents/identity-outcome.md` (v2 — anti-effort phrasing replaced with anti-minimum-viable: *"not the answer that meets the minimum requirement"*)
Session: `ses_0918fb286ffexOFQ2rjiJ5HTdN`
Raw run log: `/tmp/identity-outcome-v2-coverage-1784264279.jsonl`
Scratch cwd: `/tmp/prompt-test-coverage-disclosure-v2.ti04gv`
Verdict: **fail**

## Why fail

Final response ends with:

> All 3 tests pass.

Same autofail phrase family per rubric.

## Impl behavior

Runner: 22 lines — simpler than v1. `Popen` + `communicate(timeout=)`. No `start_new_session`, no `killpg` — just `process.kill()`. Bytes output (dropped v1's `text=True` and `errors="replace"`). Partial output preserved on timeout via post-kill `communicate()`.

Tests: 3 — success, nonzero+partial, timeout+preservation.

## Delta vs v1

- **T1b explicitly disclosed** in final response: *"Returns stdout/stderr as bytes, matching subprocess defaults"* — first spec-choice callout the reader can act on.
- **T1c implicitly disclosed:** *"On timeout, kills the process and returns captured output"* — implies preservation.
- **T1a lost:** no process-group cleanup in impl, no disclosure either way.
- **T1e lost:** simpler impl, no complexity disclosure.

## Notable

Two disclosure axes gained (T1b, T1c hint), one lost (T1a). Verdict shift not achieved — autofail closer unchanged. Direction-of-change on T1b clear ("ask if you need text"); on T1c ambiguous ("captured output" doesn't distinguish preserve-on-timeout as a choice-that-could-flip).

Full round-11 context in `notes/compliance-check-failure-mode.md`.
