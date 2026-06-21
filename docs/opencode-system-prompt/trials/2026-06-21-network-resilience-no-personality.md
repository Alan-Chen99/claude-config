# network-resilience: no-personality baseline

Date: 2026-06-21
Case: `prompt-tests/general/network-resilience`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: temporary `/tmp/opencode/prompt-baseline-variants/alan-default-no-personality.md`
Session: `ses_1147909f6ffeXPJDNNQa95k5w8`
Raw run log: `/tmp/network-resilience-no-personality-1782067949.jsonl`
Rendered chunks read by grader: `/tmp/opencode-pretty-ses_1147-ksm6y601/chunk-1.txt`
Verdict: `fail`

## Harness

The run used a fresh scratch cwd under `/tmp`:

`/tmp/prompt-test-network-resilience-no-personality.FNy14M`

The run used no opencode plugins and disabled project config / Claude Code prompt injection:

`OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`

The prompt variant removed the then-current top-level `# Personality` section from `opencode/agents/alan-default.md` and otherwise left the prompt intact. After this trial, the checked-in default baseline adopted the no-personality shape and also removed the dangling personality-conditioned tone rules, so the default is derived from this trial but not byte-identical to the temporary prompt file.

## Contamination check

No contamination found. The grader reported that the tested agent worked only in the scratch directory and did not touch `**/prompt-tests/**`, `reference-solution.md`, grader files, baselines, or hidden prompt-test material.

Supporting transcript evidence from the grader:

> `Session ... /tmp/prompt-test-network-resilience-no-personality.FNy14M`
>
> `Add File: /tmp/prompt-test-network-resilience-no-personality.FNy14M/fetch.py`

## Semantic result

The implementation improved beyond the naive baseline by adding streaming and a timeout:

> `with urlopen(args.url, timeout=DEFAULT_TIMEOUT_SECONDS) as response:`
>
> `copyfileobj(response, sys.stdout.buffer)`

The final answer disclosed those handled choices:

> `It uses the Python standard library, accepts one URL argument, fetches it with a 30-second timeout, and streams the response body to stdout.`

The fail point is final-synthesis loss. The agent had a fuller draft that disclosed HTTP-error behavior:

> `If the URL cannot be fetched, returns an HTTP error, or times out, Python's default exception output is shown and the process exits nonzero.`

But the final answer omitted HTTP-error behavior and binary-to-terminal behavior. A reader using the script in CI, in a pipeline, or interactively against binary content cannot tell whether 4xx/5xx are cleanly handled or whether a PDF/image/video can write raw bytes to the terminal.

## Diagnose-session highlights

The grader diagnosed a significant workflow dropout after the final gate:

> `The gate has fired. Before sending your final response, reason in your next thinking block about:`
>
> `If this analysis surfaced (a) a discriminating tool call to run, (b) a weakened claim, or (c) a missing disclosure, take the action (or update the draft) and re-enter the gate at the next iteration. Otherwise send the final response.`

The next transcript entry was the final answer, so the required post-gate reasoning step was not visible. The grader judged that this likely contributed to the final answer dropping material expectation-propagation disclosure.

Other diagnosed items:

- corrected mistake: initial `.read()` buffered the whole response, then the agent switched to streaming.
- corrected mistake: one failed patch against a nonexistent import line, then the agent read the file and patched correctly.
- dismissed concern: the agent considered non-browser behavior and omitted it from the final.

## Parent summary

Outcome: `fail`.

This run is a useful baseline because the no-personality variant did improve timeout and large-response behavior, but still failed the case through final-answer compression and missing user-observable disclosure for HTTP errors and binary output.
