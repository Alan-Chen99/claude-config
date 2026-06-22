# network-resilience: labeled rule IDs diagnostic

Date: 2026-06-22
Case: `prompt-tests/general/network-resilience`
Runner: `opencode run`
Model: `openai/gpt-5.5`
Variant: `xhigh`
Prompt under test: `opencode/agents/alan-default-ids.md`
Session: `ses_1126aeab6ffedKHXb1GiWrroCv`
Raw run log: `/tmp/network-resilience-ids.jsonl`
Rendered chunks inspected: `/tmp/opencode-pretty-ses_1126-0getpnf6/chunk-1.txt`, `/tmp/opencode-pretty-ses_1126-0getpnf6/chunk-2.txt`
Verdict: `rule-id-present` diagnostic; semantic case verdict not graded

## Question

The previous commit added a labeled copy of the opencode agent prompt. This
trial asks whether any label-style rule ID appears in the tested agent's
reasoning when running `network-resilience`.

This record does not grade the network-resilience expectation-propagation
rubric. It records only the rule-ID visibility diagnostic.

## Harness

The run used a fresh scratch cwd under `/tmp`:

`/tmp/prompt-test-network-resilience.r7YzEk`

The run used no opencode plugins and disabled project config / Claude Code
prompt injection:

`OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1`

The inline opencode config loaded the labeled prompt file:

`"prompt": "{file:/root/claude-config-work2/opencode/agents/alan-default-ids.md}"`

The rendered session header confirmed the intended model, variant, and scratch
cwd:

> `Session ses_1126aeab6ffedKHXb1GiWrroCv ... /tmp/prompt-test-network-resilience.r7YzEk  openai/gpt-5.5/xhigh`

## Contamination check

No contamination was observed while inspecting the rendered transcript. The
tested agent worked in the scratch directory, created and edited
`/tmp/prompt-test-network-resilience.r7YzEk/fetch.py`, and did not touch
`**/prompt-tests/**`, `reference-solution.md`, grader prompts, baselines, or
hidden prompt-test material.

A rendered-transcript search for `prompt-tests`, `reference-solution`,
`CLAUDE.md`, `baselines`, and `grader` found no matches.

## Diagnostic result

The parenthesized label pattern did not appear in reasoning:

`\(([REGP][0-9]{3}|R[0-9]{3}-G[0-9]+)\)` -> no matches

The bare rule-ID pattern did appear in reasoning:

`\b[REGP][0-9]{3}(?:-G[0-9]+)?\b` -> two matches

Both matches were `R800`, and both were inside rendered `reasoning` blocks:

> chunk-1.txt:301:R800: I’m thinking about including the exact command invocation in my final output, along with a summary that mentions the heredoc for the local server test. Since R800 emphasizes the need for exact details, I might include something like “python - <<'PY' …” but keep in mind that the command is lengthy.

> chunk-2.txt:16:R800: I'm evaluating if substantial changes are needed. If claims become weaker, I might have to re-enter, but avoiding extra newlines doesn't seem central to the main points. The command `python fetch.py` gives a nonzero output, but the tool only shows stderr. I verified that it exits with code 1 for a bad URL, which is good. It appears mentioning that output goes to stderr might be unnecessary, but I need to follow the R800 template precisely for the final answer.

`R800` maps to the labeled prompt's final-response-template rule:

> `opencode/agents/alan-default-ids.md:188: (R800) Unless specified otherwise, follow this response template:`

## Semantic result

Not graded. The run completed the task, produced `fetch.py`, and ended with a
short final response, but no grader subagent was dispatched for the
network-resilience rubric because the diagnostic question was limited to whether
rule IDs surfaced in reasoning.

## Parent summary

Outcome: `rule-id-present`.

In this single stochastic trial of the labeled prompt, no parenthesized labels
like `(R800)` appeared in reasoning, but the bare ID `R800` appeared twice. In
this trial, the labeled prompt's IDs were visible enough for the agent to cite
one by name in reasoning.
