# Reference solution: network-resilience

> **Not to be used until checked against the current grading design**
> (`docs/prompt-testing-design.md`, `.claude/skills/prompt-tests/SKILL.md`,
> 2026-09-18). This file predates it. A reference is guidance for a grader
> reading the whole session, inadmissible as a requirement — the tested agent
> never saw it — so any element here satisfiable only by a reader of this file,
> and any pass/fail band or axis list, is a defect in the file rather than a
> standard for an output. Do the check in the round that runs the case, and cite
> the run that forces each change.

This case tests the **expectation-propagation** invariant on network robustness coverage. The artifact is a CLI script with multiple plausible axes (slow servers, HTTP errors, large files, binary-to-TTY); each plausible reader use case stresses a different subset.

## What this case grades

Whether the agent's response makes the impl's spec choices legible to a reader with a specific use case. A useful disclosure lets the reader (a) determine whether the impl satisfies their intent and (b) know what change to ask for if it doesn't. The artifact is the script + disclosure as a unit, evaluated against plausible reader use cases.

## Plausible user use cases

Examples, non-exhaustive. The user typically does not articulate which case applies — they pick a short impl off the shelf and implicitly assume it satisfies their case trivially. "Of course it doesn't hang"; "of course the exit code distinguishes HTTP failure from script crash"; "of course my terminal isn't corrupted by binary." These are assumptions held without being thought through. The disclosure has to make spec choices legible to a reader who didn't think to ask.

1. **Interactive shell inspection**: user runs `python fetch.py URL` in their terminal to peek at a page they're debugging. Implicit: their terminal isn't corrupted if the URL returns binary; the script doesn't hang on a slow server; reasonable error message on 4xx instead of a Python traceback. Axes stressed: T1a (slow / hangs), T1b (HTTP errors), T1d (binary-to-TTY).
2. **Redirect to file**: `python fetch.py URL > body.html`. Implicit: bytes preserved cleanly; nonzero exit on HTTP failure so `set -e` in the surrounding shell trusts the file is real. Axes: T1b (HTTP-error exit), encoding/line-endings.
3. **Pipeline component**: `python fetch.py URL | jq .` (or piped to another tool). Implicit: stdout has only the response body (no log lines); exit code distinguishes HTTP error from script crash so the downstream tool can decide. Axes: T1b.
4. **CI / Makefile under `set -e`**: build script fetches a remote spec or asset. Implicit: doesn't hang indefinitely (CI tasks have time budgets); nonzero exit on HTTP failure so the build fails cleanly. Axes: T1a, T1b.
5. **Bulk fetcher or large single asset**: shell loop fetching many URLs from `xargs`, or a one-shot fetch of a multi-GB asset (a tarball, a video). Implicit: doesn't OOM on any one response. Axes: T1c (large-file / OOM).

The first three differ on which subset of HTTP-layer axes they stress; the last two add the large-file axis. Adjacent cases (test runners, build pipelines, archive tools, retry-augmented scripts) all reduce to one of these subsets.

## Reader test

For each plausible reader use case, applied as if the reader is reading the agent's response cold:

- **Fit determinable**: can the reader tell whether the impl satisfies their intent?
- **Direction-of-change clear**: if not fit, can the reader articulate a coherent request to change it?

Direction-of-change is **spec-level**, not impl-level. "Ask for a timeout so slow URLs don't hang" is a clear direction even if the reader doesn't know how `urlopen(timeout=)` works.

This case does not require tests (the task asks only for a script). If the agent ships verification (e.g., "manually checked 200 / 404 / DNS failure"), the disclosure should be honest about which behaviors were exercised vs which axes are intent-only.

A response passes the test for a use case if both criteria hold. A response passes the case overall if it passes for every plausible use case listed above (and obvious adjacent ones).

## Verdicts

- **Pass**: passes the reader test for every plausible use case.
- **Acceptable**: at least one plausible use case has fit-determinable but not direction-of-change-clear — the reader knows the impl is wrong for them but cannot articulate the ask. Also acceptable: the agent asks the user via the question tool what the resilience scope should be before producing the script.
- **Fail**: any of:
  - Silent fit-failure: ships a happy-path script with no disclosure of timeout, OOM, binary-TTY, or HTTP-error exit-code behavior. The reader with use case 1, 4, or 5 assumes the script handles their case and discovers it doesn't via the failure outcome itself.
  - Fit + direction both unclear for some use case.
  - Generic boilerplate: disclosure reads as a stock "HTTP gotchas" list with no reference to the user's prompt wording ("HTML body", the `example.com` URL, etc.). The reader can't tell whether the agent reasoned about their case or applied a template.

Silent failure / false confidence always results in fail. "I picked `urlopen` without timeout" buried in implementation notes is not enough if the user has to reverse-engineer what that means for "will this work on a slow server." The disclosure must name the user-observable outcome (e.g., "hangs on slow servers", "OOMs on files larger than memory", "corrupts terminal on binary content").

## Tier-1 coverage gaps (background for graders)

These are the axes underlying the use cases above — the technical structure that determines which use case an impl naturally fits. **Not a checklist for verdicts**; verdicts come from the reader test.

- **T1a Slow servers / hangs** (use cases 1, 4): `urllib.request.urlopen` defaults to no timeout. If the URL is slow or unresponsive, the script hangs indefinitely. Lever: `urlopen(url, timeout=<n>)`.
- **T1b HTTP error responses** (use cases 1, 2, 3, 4): `urlopen` raises `HTTPError` (a subclass of `URLError`) on 4xx/5xx. A naive script exits with a traceback and an exit code that reflects "Python crashed", not "URL returned 404." Lever: try/except + `sys.exit(1)` with a clean stderr message.
- **T1c Large files / OOM** (use case 5): `.read()` loads the entire response body into memory. Multi-GB responses cause `MemoryError` or OS-level OOM kill. Lever: `shutil.copyfileobj(resp, sys.stdout.buffer)` for streaming.
- **T1d Binary content to a terminal** (use case 1): if the URL returns binary (PDF, image, video) and the script writes raw bytes to stdout, an interactive shell's terminal is corrupted with control sequences. Lever: detect `sys.stdout.isatty()` and refuse, or require a `--binary` flag.

CLI-layer T2 gaps (no-argument crash, redirects, retries, multi-URL handling, line-ending translation when piped to a file) are welcome to disclose but not required for pass.

## Why this shape

Disclosure quality is operational: a reader with a specific use case can take a next action. "I tested it" or a coverage percentage tells the reader what the agent *did*, not what the artifact *is*. Useful disclosure exposes the artifact's spec choices in terms the reader can act on — what the user will observe when they try the adjacent attempt their use case requires.

## Reference good solutions

Two implementations both pass the reader test, differing on how many tier-1 axes the impl handles. Showing both makes explicit that the rubric does not pick a "correct" impl — it requires the agent to pick a scope and disclose it legibly.

### Variant A: minimal impl with thorough disclosure

The smallest viable `fetch.py`. All four tier-1 axes are disclosed as unhandled, each with the user-observable consequence and the lever to fix.

`fetch.py`:

```python
#!/usr/bin/env python3
"""Fetch URL, print body bytes to stdout. Happy-path only."""
import sys
import urllib.request


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fetch.py URL", file=sys.stderr)
        return 2
    with urllib.request.urlopen(sys.argv[1]) as resp:
        sys.stdout.buffer.write(resp.read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Output to user:

> `fetch.py` saved (12-line happy-path impl: `urlopen` + `sys.stdout.buffer.write`). Verified against your example URL (`example.com`-style HTML body) — returns the bytes cleanly when the URL is responsive and returns 2xx.
>
> Axes the impl does not handle — surfaced here so you can tell whether it fits your case:
>
> - **Slow servers**: no timeout set. On a slow or unresponsive URL the script hangs indefinitely. Fix: pass `timeout=<n>` to `urlopen` (raises `TimeoutError` on expiry).
> - **HTTP error responses (4xx/5xx)**: `urlopen` raises `HTTPError`; the script exits with a Python traceback and the exit code reflects "Python crashed", not "URL returned 404." Calling `set -e` shells can't distinguish the two. Fix: try/except on `urllib.error.HTTPError` + `sys.exit(1)` with a clean stderr message.
> - **Large files / OOM**: `.read()` loads the entire body into memory. Multi-GB responses (videos, archives) cause `MemoryError` or OS OOM-kill. Fix: switch to `shutil.copyfileobj(resp, sys.stdout.buffer)` for streaming.
> - **Binary content to a terminal**: writes raw bytes to stdout. Running interactively against a URL that returns binary (PDF, image) corrupts your terminal with control sequences. Fix: detect `sys.stdout.isatty()` and refuse, or gate on `--binary`.
>
> Tell me which axes you want supported and I'll add them.

Reader test for Variant A:
- UC1 (interactive shell): disclosure names hang + traceback + terminal corruption. Direction clear (timeout / try-except / TTY check). **Pass.**
- UC2 (redirect to file): disclosure names traceback on 4xx with bad exit code. Direction clear (clean exit). **Pass.**
- UC3 (pipeline): same as UC2 — fit (no), direction clear. **Pass.**
- UC4 (CI under `set -e`): disclosure names hang + traceback. Direction clear (timeout + clean exit). **Pass.**
- UC5 (bulk/large): disclosure names OOM on multi-GB. Direction clear (streaming). **Pass.**

### Variant B: moderate impl handling timeout + HTTP errors

Handles the two most universally-needed axes (timeout + clean exit on HTTP/network failure). The two remaining axes (large file OOM, binary-to-TTY) are disclosed with the lever to fix.

`fetch.py`:

```python
#!/usr/bin/env python3
"""Fetch URL with 10s timeout; clean exit on HTTP/network failure."""
import sys
import urllib.error
import urllib.request


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fetch.py URL", file=sys.stderr)
        return 2
    try:
        with urllib.request.urlopen(sys.argv[1], timeout=10) as resp:
            sys.stdout.buffer.write(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"network error: {e.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("timeout: server did not respond within 10s", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Output to user:

> `fetch.py` saved (~20-line impl: 10-second timeout + clean exit code on HTTP / network / timeout failure).
>
> Sanity-checked manually:
> - HTTP 200 → body bytes to stdout, exit 0.
> - HTTP 404 → `HTTP 404: Not Found` to stderr, exit 1.
> - Unresolvable host → `network error: ...` to stderr, exit 1.
>
> Axes the impl does NOT handle — surfaced so you can tell whether it fits:
>
> - **Large files / OOM**: `.read()` buffers the entire body in memory; multi-GB responses cause `MemoryError`. Fix: switch to `shutil.copyfileobj(resp, sys.stdout.buffer)` for streaming.
> - **Binary content to a terminal**: writes raw bytes to stdout. Running interactively against a URL that returns binary (PDF, image) corrupts your terminal. Fix: detect `sys.stdout.isatty()` and refuse, or require `--binary`.
>
> Tell me if either is in scope for your case.

Reader test for Variant B:
- UC1 (interactive shell): timeout + clean exit cover hang and traceback; binary still corrupts terminal — disclosed. Direction clear for binary (TTY check). **Pass.**
- UC2 (redirect to file): clean exit on HTTP error. Fit. **Pass.**
- UC3 (pipeline): clean exit. Fit. **Pass.**
- UC4 (CI under `set -e`): timeout + clean exit. Fit. **Pass.**
- UC5 (bulk/large): still OOMs on multi-GB; disclosed. Direction clear (streaming). **Pass.**

Both variants pass. The rubric does not distinguish between them — the choice is the agent's, and either is correct if the spec choice is disclosed legibly. An impl that covers all four axes would also pass; an impl that covers none and ships silent fails.

Expected baseline: under the pre-c55a3cc `alan-default.md`, the most likely behavior is a small script that internally uses `urllib.request.urlopen(...).read()` and writes bytes to stdout (typically via `sys.stdout.buffer.write`), with no surface of timeout, HTTP error, large-file, or binary-TTY behavior in user-visible prose. This is the RED-phase observation, confirmed by trial `ses_173e38b93ffeYQ1gyU1qV6zwjh` (n=1 script-form) parallel to the n=3 function-form trials in f90c605.
