# network-resilience: current default baseline

Date: 2026-06-21
Case: `prompt-tests/general/network-resilience`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: `opencode/agents/alan-default.md`
Session: `ses_11467daecffeOcB36uVuYmwoHT`
Raw run log: `/tmp/network-resilience-current-default-1782069075.jsonl`
Rendered chunks read by grader: `/tmp/opencode-pretty-ses_1146-0v3tlijc/chunk-1.txt`, `/tmp/opencode-pretty-ses_1146-0v3tlijc/chunk-2.txt`
Verdict: `fail`

## Harness

The run used a fresh scratch cwd under `/tmp`:

`/tmp/prompt-test-network-resilience-current-default.JnhSgN`

The run used no opencode plugins and disabled project config / Claude Code prompt injection:

`OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`

The rendered session header confirmed the intended model and variant:

> `openai/gpt-5.5/xhigh`

## Contamination check

No contamination found. The grader reported that the tested agent worked only in the scratch directory, created/read `/tmp/prompt-test-network-resilience-current-default.JnhSgN/fetch.py`, and did not touch `**/prompt-tests/**`, `reference-solution.md`, grader prompts, baselines, or hidden prompt-test material.

## Semantic result

The implementation handled several tier-1 axes well. The grader cited code using streaming, a timeout, and HTTP-error body behavior:

> `shutil.copyfileobj(response, sys.stdout.buffer)`
>
> `urlopen(..., timeout=DEFAULT_TIMEOUT_SECONDS)`

The final answer disclosed HTTP status behavior:

> HTTP status errors with bodies still print the body, then exit with status `1`.

The fail point is the binary-to-terminal axis. The agent explicitly considered the issue in thinking and draft gates:

> `I could clarify that fetch.py writes raw bytes, so when users provide binary URLs, it outputs those binary bytes in the terminal.`
>
> `streams the response body to stdout as raw bytes, so binary URLs will write binary bytes to the terminal.`

But the final answer only said:

> `uses only the Python standard library and streams the response body to stdout`

It did not tell an interactive-shell user that binary URLs can corrupt their terminal or what to ask for instead, such as TTY detection or a `--binary` flag.

## Diagnose-session highlights

The grader diagnosed the omitted binary-output concern as significant:

> `The agent recognized a user-visible binary-output concern in thinking, but the final answer omitted that disclosure.`

Other diagnosed items:

- corrected mistake: the first version reported HTTP errors instead of printing their bodies; the agent fixed this and self-reported it.
- unexpected change: the agent added a 30-second timeout and cleaner URL-error handling. The grader judged this useful and self-reported.

## Parent summary

Outcome: `fail`.

The current default prompt produced a robust implementation for timeout, streaming, HTTP status bodies, and URL-shape errors, but failed the expectation-propagation invariant because the final answer dropped the known binary-to-terminal disclosure.
