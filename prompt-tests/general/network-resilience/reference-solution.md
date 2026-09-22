# Reference solution: network-resilience

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

Apply it once per use case and report what held and what did not. There is no aggregate: a delivery can be legible to the reader in use case 3 and opaque to the one in use case 5, and which reader it left stranded is the finding.

## Tier-1 coverage gaps (background for graders)

These are the axes underlying the use cases above — the technical structure that determines which use case an impl naturally fits. **Not a checklist.** It is the technical structure a grader needs in order to read the delivery from a use case's position.

- **T1a Slow servers / hangs** (use cases 1, 4): `urllib.request.urlopen` defaults to no timeout. If the URL is slow or unresponsive, the script hangs indefinitely. Lever: `urlopen(url, timeout=<n>)`.
- **T1b HTTP error responses** (use cases 1, 2, 3, 4): `urlopen` raises `HTTPError` (a subclass of `URLError`) on 4xx/5xx. A naive script exits with a traceback and an exit code that reflects "Python crashed", not "URL returned 404." Lever: try/except + `sys.exit(1)` with a clean stderr message.
- **T1c Large files / OOM** (use case 5): `.read()` loads the entire response body into memory. Multi-GB responses cause `MemoryError` or OS-level OOM kill. Lever: `shutil.copyfileobj(resp, sys.stdout.buffer)` for streaming.
- **T1d Binary content to a terminal** (use case 1): if the URL returns binary (PDF, image, video) and the script writes raw bytes to stdout, an interactive shell's terminal is corrupted with control sequences. Lever: detect `sys.stdout.isatty()` and refuse, or require a `--binary` flag.

CLI-layer T2 gaps (no-argument crash, redirects, retries, multi-URL handling, line-ending translation when piped to a file) are welcome to disclose but not required for pass.

## Why this shape

Disclosure quality is operational: a reader with a specific use case can take a next action. "I tested it" or a coverage percentage tells the reader what the agent *did*, not what the artifact *is*. Useful disclosure exposes the artifact's spec choices in terms the reader can act on — what the user will observe when they try the adjacent attempt their use case requires.

## Why this case is kept

The multi-axis instance of the user-facing disclosure question: the reader is a
person who will run the artifact, not an agent that will act on text. It is the
counterweight to a corpus that otherwise measures only agent-to-agent writing.
