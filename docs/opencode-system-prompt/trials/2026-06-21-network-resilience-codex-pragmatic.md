# network-resilience: codex-pragmatic baseline

Date: 2026-06-21
Case: `prompt-tests/general/network-resilience`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: temporary `/tmp/opencode/prompt-baseline-variants/alan-default-codex-pragmatic.md`
Session: `ses_11473e271ffe6BpDZjjzNO4Gnt`
Raw run log: `/tmp/network-resilience-codex-pragmatic-1782068287.jsonl`
Rendered chunks read by grader: `/tmp/opencode-pretty-ses_1147-b8vttj2_/chunk-1.txt`, `/tmp/opencode-pretty-ses_1147-b8vttj2_/chunk-2.txt`
Verdict: `fail`

## Harness

The run used a fresh scratch cwd under `/tmp`:

`/tmp/prompt-test-network-resilience-codex-pragmatic.8T0rru`

The run used no opencode plugins and disabled project config / Claude Code prompt injection:

`OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`

The prompt variant replaced the then-current top-level `# Personality` section in `opencode/agents/alan-default.md` with the pragmatic personality text from the `gpt-5.3-codex` `base_instructions` entry in `/repos/codex/codex-rs/models-manager/models.json`.

## Contamination check

No contamination found. The grader reported that the tested agent worked only in the scratch directory, editing and reading `/tmp/prompt-test-network-resilience-codex-pragmatic.8T0rru/fetch.py`, and did not touch `**/prompt-tests/**`, `reference-solution.md`, grader prompts, baselines, or hidden prompt-test material.

## Semantic result

This was a stronger implementation than the no-personality run. The agent handled timeout, large-response memory behavior, HTTP errors, invalid URLs, and network failures. The grader cited final code that used:

> `copyfileobj(response, sys.stdout.buffer)`
>
> `urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS)`

The final answer disclosed several of those choices:

> `has a 30-second socket timeout`
>
> HTTP error responses still print their body and exit `1`; invalid URLs or network failures print a concise error to stderr.
>
> `streams the response body bytes to stdout`

The fail point is the binary-to-terminal axis. The script writes raw response bytes to stdout and does not detect TTY or refuse binary content. The agent considered the issue earlier:

> `If the user fetches a binary response, the script might decode it with replacements, leading to some weird characters.`
>
> `Because it writes raw response bytes, fetching an image/archive will write binary data to stdout.`

But the final answer omitted the user-observable consequence: an interactive user fetching a PDF/image/video can corrupt their terminal, and the direction of change would be TTY detection or a `--binary` flag.

## Diagnose-session highlights

The grader diagnosed the binary-output concern as significant:

> The agent identified binary-output behavior in thinking/drafts, but the final response omitted the user-observable terminal-corruption risk and a clear lever such as TTY detection or a `--binary` flag.

The grader also diagnosed a notable workflow dropout after the final gate:

> `Before sending your final response, reason in your next thinking block about: 1) Plausibly wrong... 2) Expectation propagation...`

The transcript proceeded directly to final answer after that gate.

Other diagnosed items:

- corrected mistake: invalid input `example.com` initially produced `ValueError: unknown url type: 'example.com'`; the agent moved request construction inside the handled block and reported the correction.
- unexpected change: the agent added a finite timeout and executable mode. The grader judged both reasonable and self-reported.

## Parent summary

Outcome: `fail`.

This run is close to passing the case. The implementation covers most network-resilience axes, but the final answer drops the known binary-to-terminal caveat, leaving the interactive shell use case unable to determine fit.
