# gate thinking and sponge diagnostics

Date: 2026-06-22
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Default prompt under test: `opencode/agents/alan-default.md`

Question: investigate whether the `network-resilience` no-personality trial's
missing post-gate thinking block was one-time, whether the model understands
`reason in your next thinking block`, and what changes when the gate's no-sponge
paragraph is removed.

## Harness notes

All prompt-test case runs used fresh scratch directories under `/tmp`, disabled
project config and Claude Code prompt injection, and loaded no plugins:

`OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`

The worktree `agent-tools` binary was built and put on `PATH` for current-gate
runs. The no-sponge runs used temporary wrapper
`/tmp/opencode/diagnostics/bin/agent-tools`, which delegated all commands except
`opencode.gate` to the worktree binary. It printed the same gate stdout with the
paragraph below removed; due to the wrapper's ASCII-only text, the em dash in
`do not stop at the first concern that surfaces -- reason across axes` was also
rendered as `--` in those no-sponge runs.

> If the analysis surfaces no actionable disclosure, the final response does NOT
> include sponge prose; absence is the correct outcome when no plausible adjacent
> attempt is undisclosed. These directives are subject to explicit user
> instructions to the contrary (no caveats, brevity).

## Runs

### network-resilience current-gate rerun

- Case: `prompt-tests/general/network-resilience`
- Session: `ses_112ea8991ffeVWGz5nEAjUF6fB`
- Raw run log: `/tmp/network-resilience-rerun-1782094065.jsonl`
- Scratch cwd: `/tmp/prompt-test-network-resilience-rerun-1782094065`
- Rendered transcript: `/tmp/opencode-pretty-ses_112e-9fybgwbo/chunk-1.txt`, `/tmp/opencode-pretty-ses_112e-9fybgwbo/chunk-2.txt`

Observation: the missing post-gate thinking block did not reproduce. After the
first gate, the next entry was a reasoning block:

> `**Improving file handling**`
>
> `I'm digging into the idea of handling large file downloads...`

After the final gate, the next entry was also reasoning:

> `**Clarifying file and network usage**`

However, final-synthesis disclosure loss persisted. The final post-gate
reasoning considered binary and timeout behavior:

> `if the user runs commands with missing or no arguments`
>
> `URL to image... write raw bytes`
>
> `slow or hanging URLs without a custom timeout`

The final answer omitted binary-to-terminal and slow-server timeout behavior.

### current-gate direct thinking-block probe

- Task: `Follow your normal completion workflow for this task, then reply with ACK.`
- Session: `ses_112e32fb1ffe1B2itQPhblKl58`
- Scratch cwd: `/tmp/opencode-thinking-block-current-normal-1782094547`

Observation: positive control for the phrase. The gate output was followed by a
visible reasoning block before the final `ACK`:

> `**Analyzing the final response**`
>
> `I need to think through the user's request...`

A prior over-constrained probe, `Reply with exactly ACK`, produced no gate
because the explicit exact-output user instruction overrode the normal workflow;
that run was discarded for this question.

### trivial-task no-sponge gate

- Case: `prompt-tests/general/trivial-task`
- Session: `ses_112e1d75dffe6NmN87L4iU0xls`
- Raw run log: `/tmp/trivial-no-sponge-1782094635.jsonl`
- Scratch cwd: `/tmp/prompt-test-trivial-no-sponge-1782094635`

Observation: no-sponge removal did not produce the exact pattern "no thinking
before response, still put in sponge." The run had post-gate reasoning after
each gate. It did add caveat-like final prose on a case designed to avoid that:

> `It expects a string. Non-ASCII letters are treated as separators, not transliterated, so slugify("Caf\u00e9") returns "caf".`

The final also reported `None -> AttributeError` evidence and included the
non-string behavior in the output draft before final synthesis.

### trivial-task current-gate control

- Case: `prompt-tests/general/trivial-task`
- Session: `ses_112df585affei2Y81AXLHUxJrX`
- Raw run log: `/tmp/trivial-current-gate-1782094799.jsonl`
- Scratch cwd: `/tmp/prompt-test-trivial-current-gate-1782094799`
- Rendered transcript: `/tmp/opencode-pretty-ses_112d-k68hevhg/chunk-1.txt`

Observation: the current no-sponge paragraph did not prevent the same class of
over-disclosure. The final answer included:

> `Non-ASCII letters are treated as separators, not transliterated...`
>
> `Passing a non-string value such as None raises TypeError.`
>
> `Running python slugify.py exits with no output because the file only defines the function.`

The reasoning immediately after the first gate shows the enumerate-across-axes
instruction overpowering the no-sponge guard:

> `I wonder if a user might pass something that isn't a string...`
>
> `Users might expect eclair...`

### network-resilience no-sponge gate

- Case: `prompt-tests/general/network-resilience`
- Session: `ses_112dc02aeffezJFxm3i7o2M2VF`
- Raw run log: `/tmp/network-resilience-no-sponge-1782095017.jsonl`
- Scratch cwd: `/tmp/prompt-test-network-resilience-no-sponge-1782095017`
- Rendered transcript: `/tmp/opencode-pretty-ses_112d-vb17gqbd/chunk-1.txt`

Observation: removing the no-sponge paragraph did not cause a missing
post-gate thinking block. It did make disclosure more active than the current
rerun: the final included HTTP error and binary raw-byte notes. But it still
dropped a material disclosure. The final gate draft contained:

> `There is no custom timeout flag, so a very slow server can make the command wait.`

The final answer omitted that slow-server timeout note and did not disclose the
large-response memory behavior of `.read()`.

## Conclusions

1. The original "no thinking block after gate" observation was not reproduced in
   these runs. The model demonstrably can treat `reason in your next thinking
   block` as an instruction that produces a visible `reasoning` block.
2. The more durable failure is not absence of thinking. It is final-synthesis
   selection: the model thinks about or drafts relevant disclosures, then drops
   one or more of them in the final answer.
3. Removing the no-sponge paragraph did not produce the hypothesized exact shape
   "no thinking before response, still put in sponge" in the observed runs.
4. The no-sponge paragraph is also not strong enough as written. On trivial-task,
   current-gate and no-sponge runs both produced extra caveat-like prose, so the
   enumerate-across-axes directive appears to dominate.

## Follow-up posture

Treat the missing-post-gate-thinking observation as a rare-event hypothesis, not
as a prompt-edit target yet. This diagnostic produced multiple post-gate
thinking blocks across focused reruns, so the next useful step is to collect
real, organic runs and revisit only if more transcripts show the same dropout
pattern. Until then, prioritize the reproducible final-synthesis-loss problem:
the agent can reason about a needed disclosure and still omit it from final
prose.
