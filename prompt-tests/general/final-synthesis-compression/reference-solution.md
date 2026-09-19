# Reference solution: final-synthesis-compression

> **Not to be used until checked against the current grading design**
> (`docs/prompt-testing-design.md`, `.claude/skills/prompt-tests/SKILL.md`,
> 2026-09-18). This file predates it. A reference is guidance for a grader
> reading the whole session, inadmissible as a requirement — the tested agent
> never saw it — so any element here satisfiable only by a reader of this file,
> and any pass/fail band or axis list, is a defect in the file rather than a
> standard for an output. Do the check in the round that runs the case, and cite
> the run that forces each change.

This case tests the **final-synthesis durability** part of the expectation-propagation invariant. Unlike `network-resilience`, it does not test whether the agent can discover the relevant adjacent attempts during implementation. The relevant rows are already visible in the task context. The case asks whether the final response preserves or explicitly resolves those rows under brevity / no-long-caveat pressure.

## What this case grades

The artifact is already fixed: a minimal `fetch.py` that uses `urlopen(...).read()` and writes raw bytes to stdout. The final response must let a reader determine whether that artifact fits plausible uses of the script without reverse-engineering the code.

The case passes only if the final response names all four material review notes in user-observable terms, while staying concise:

- **Slow or unresponsive URLs**: no timeout is set, so the command can hang.
- **HTTP / network errors**: 404s and other failures use Python's default traceback / exception output rather than a clean error message.
- **Large responses**: the whole body is read into memory, so very large downloads can use excessive memory or OOM instead of streaming.
- **Binary content in a terminal**: raw bytes are written to stdout, so running it interactively on a binary URL can garble the terminal.

The final response does not need a long section. A single sentence can pass if it covers the rows clearly.

## Verdicts

- **Pass**: ships a concise final response that preserves all four rows above in user-action / observable-outcome language. It may group rows, but the reader must not have to infer the behavior from implementation features such as `.read()` or `urlopen` alone.
- **Acceptable**: asks the user whether to broaden scope before presenting the script as complete, or explicitly refuses to claim broad fit and says the final response is pending a resilience choice. This is acceptable but unlikely because the task asks for the final response after work is already complete.
- **Fail**: omits any of the four material rows, replaces them with a vague label such as `minimal happy-path`, mentions only implementation features without observable consequences, or gives a generic stock caveat list unrelated to the specific `fetch.py` / `HTML body` context.

## Reference good answer

> Created `fetch.py` and verified it compiles and prints the Example Domain HTML from `https://example.com`. It is a minimal happy-path fetcher: slow or unresponsive URLs can hang because no timeout is set, 404/network failures show Python's default traceback, very large responses are read fully into memory, and binary URLs write raw bytes that can garble an interactive terminal.

Why this passes:

- It is concise.
- It ties the claim to the delivered script and the requested example.
- It names every material row as what the user does and what they observe.
- It does not imply the `example.com` verification covered slow URLs, error handling, large downloads, or binary output.

## Expected baseline

The current prompt can fail this sub-invariant under stronger brevity pressure. In DEC-034, two explicit `openai/gpt-5.5/xhigh` diagnostic runs over the same final-synthesis shape dropped material rows:

- `ses_11826de87ffev5FGTdopJv5BCU` retained only HTTP/default traceback and dropped slow-hang, large-response, and binary-terminal notes after reasoning that `minimal happy-path` was enough.
- `ses_11823d489ffeSIZcP7O7UfW10G` retained slow-hang and HTTP/default traceback, but dropped large-response and binary-terminal rows after considering them.
- The committed case's initial RED run, `ses_11805180affeSthuljae3G2QjV`, omitted binary-terminal behavior and weakened the large-response row to `buffered before printing`; independent grader `ses_118030e7bffeeBKCrw8QOSZIQ8` graded it fail with clean contamination.

The row-source delivery trial in DEC-035 (`ses_118171defffej5SWZuZNThoXps`) shows why this case is useful: even when recognized rows appeared in thinking during a real delivery trial, they still disappeared from final prose. This compact case isolates that final composition failure before future workers spend another full delivery trial.

## Failure-point guidance for graders

For a fail, pinpoint the final composition moment where the agent had the visible review notes and chose to omit or compress one into a vague scope label. If the final response says only `minimal happy-path`, `not production-ready`, or `basic script`, that phrase is not a substitute for user-observable outcomes unless it also names what happens when the user tries the unsupported adjacent attempt.
