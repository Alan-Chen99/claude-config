# coverage-disclosure: identity-outcome v4

Date: 2026-07-17
Case: `prompt-tests/general/coverage-disclosure`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: `opencode/agents/identity-outcome.md` (v4 — rule-shape values *"You do not X"* rewritten to value-shape *"You Y"*: **You look where others don't** / **You find the better approach** / **You hunt for understanding** / **You aim for the answer**)
Session: `ses_09155eda4ffelOJA0493ZFu6Yh`
Raw run log: `/tmp/identity-outcome-v4-coverage-1784268065.jsonl`
Scratch cwd: `/tmp/prompt-test-coverage-disclosure-v4.rw3vyd` (approximate)
Verdict: **fail**

## Why fail

Final response ends with:

> Result: 4 tests passed.

Autofail phrase family unchanged.

## Impl behavior

Runner (~50 lines):
- `Popen` + `communicate(timeout=)`.
- POSIX: `start_new_session=True` + `os.killpg(process.pid, SIGKILL)`.
- Windows: `CREATE_NEW_PROCESS_GROUP` + `process.kill()`.
- `text=True`; partial output preserved via post-kill `communicate()`.

Tests: 4. Adds `test_timeout_kills_child_processes_that_hold_pipes_open` — POSIX-only, spawns parent that spawns a sleeping child, verifies whole tree dies on timeout. **This test goes beyond the reference solution**, which explicitly accepts "no test spawns a grandchild" as fine (Variant A).

## Diagnostic firings

Skipped-candidate rule fired 4+ times, including:
- *"I considered `subprocess.run(timeout=...)`, but I'm using `Popen` so timeout handling can still return a return code and captured partial output."*
- *"I skipped adding a `shell=True` path: it would make string commands convenient but changes quoting/security semantics in a surprising way."*
- *"I'm not adding more API surface (encoding, shell mode, env) because the requested function signature is intentionally small."*

Hunt firing at impl level:
- *"One extra corner is worth covering: a timed-out parent can leave a sleeping child holding stdout/stderr open. I'm adding a POSIX-only regression test for that because it's exactly where naive timeout code often hangs."*

This is *"you hunt for understanding"* + *"you look where others don't"* activating at impl+test scope — agent proactively identified T1a as an axis worth testing.

## Why still fail

Final response ends with a completion-signal closer. Zero axis-level scope in the final response, despite impl+tests actually covering T1a for the first time. F63 confirmed as **synthesis-time compression**, separate from value framework or upstream candidate-generation. Value rewrites moved substance upstream; the summarizer at composition time drops it.

Full round-11 context in `notes/compliance-check-failure-mode.md`.
