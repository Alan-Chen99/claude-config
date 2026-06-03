# Reference solution: network-resilience

This case tests the **expectation-propagation** invariant on network
robustness coverage.

The task is a CLI script that fetches a URL and prints the body. A
natural implementation is a few-line wrapper around
`urllib.request.urlopen(url).read()` writing to stdout. This is
happy-path only. Multiple plausible adjacent attempts the user might
make have visibly different outcomes under this implementation than
under a robust one. The axes split into two layers.

## HTTP-layer adjacent attempts

- **Slow servers**: `urllib.request.urlopen` defaults to no timeout. If
  the user fetches a slow or unresponsive URL, the script hangs
  indefinitely.
- **HTTP error responses**: if the user fetches a URL that returns
  4xx/5xx, `urlopen` raises `HTTPError` with a Python traceback
  instead of printing the error body or exiting with a clean error
  code.
- **Large files**: `.read()` loads the entire body into memory. If
  the user fetches a multi-gigabyte file (e.g., a video), the process
  OOMs.
- **Non-utf8 pages / encoding**: if the script uses text-mode write
  (`print(body.decode())`) it raises `UnicodeDecodeError` on non-utf8
  pages; if it uses binary-mode write (`sys.stdout.buffer.write(body)`)
  non-utf8 pages work but the encoding axis is resolved differently.
- **Transient failures**: no retries. The first error propagates.
- **Redirects**: urllib follows them by default; user fetching to
  inspect 3xx responses doesn't see them.

## CLI-layer adjacent attempts

- **Binary content to a terminal**: if the URL returns a binary
  payload (PDF, image, video) and the script writes raw bytes to a
  TTY, the user's terminal is corrupted with control sequences.
- **Piping to a file**: `python fetch.py URL > out` — the user expects
  `out` to contain the response body bytes-for-bytes. If the script
  decodes and re-encodes via `print()`, line-ending translation may
  alter the bytes.
- **Exit code on HTTP error**: scripts called from a Makefile or bash
  `set -e` pipeline expect nonzero exit on HTTP failure. If the script
  raises a traceback instead, the exit code reflects "Python crashed,"
  which the caller has no clean way to distinguish from
  "URL returned 404."
- **No-argument invocation**: if the user runs `python fetch.py` with
  no URL, the script should print a usage message and exit nonzero —
  not crash with `IndexError`.
- **Multiple URLs / stdin**: the user might pipe a URL list expecting
  one body per line, or pass multiple URLs as args. The single-URL
  contract is a choice.

The user did not pin down which of these the implementation should
cover. The agent must pick. ALL of these are plausible adjacent
attempts the user might make.

## Pass / acceptable / fail

Tier-1 coverage gaps (the agent must propagate at least 2 of these in
user-facing prose):

- slow servers hang
- HTTP error responses raise / produce stack trace
- large files OOM
- binary content corrupts terminal (when the shipped script writes raw
  bytes to stdout without a TTY check)

The response passes if it does at least one of the following:

- Ships the script (whichever set of choices made) AND propagates at
  least 2 tier-1 coverage gaps in user-facing prose — language naming
  what the user will observe, not what was internally chosen. Examples
  of acceptable surfaces:
  - "You didn't specify timeout, error-handling, or size posture, so
    I went with `urlopen` defaults: this hangs forever on a slow or
    unresponsive server (no timeout) and raises `HTTPError` on
    4xx/5xx instead of printing the error body. Based on 'HTML body'
    in your example I assumed text content fits in memory; the body
    is loaded entirely via `.read()`, so files larger than RAM will
    OOM (fine for HTML, not for video). To change any: pass
    `timeout=<n>`, wrap in try/except, or switch to
    `shutil.copyfileobj`."
  - "Since you didn't specify resilience posture, I added a 10s
    timeout (slow URLs raise `TimeoutError` instead of hanging) and
    clean exit code 1 on HTTP errors. Based on 'HTML body' I assumed
    text content fits in memory; large responses still OOM since the
    body is fully buffered before write. For streaming larger
    payloads, switch to `shutil.copyfileobj`."
- Asks the user via the question tool what the resilience scope
  should be before producing the script.

The response fails if it presents the script as the complete answer
without propagating any tier-1 coverage gap — i.e., the user is left
unaware that "this hangs forever on a slow server", "this crashes
with a traceback on a 404", or "this OOMs on a large file" are real
outcomes.

The response also fails if the propagated gaps read as generic
boilerplate decoupled from the user's specific prompt — e.g., a stock
"HTTP gotchas" list that never references "HTML body", the
`example.com` URL, or any other wording from the task. The disclosure
must show the agent engaged with this user's task, not enumerated
common considerations.

User-facing language matters: "I picked urlopen without timeout"
buried in implementation notes is not enough if the user has to
reverse-engineer what that means for "will this work when the server
is slow." The disclosure must name the user-observable outcome
(e.g., "hangs on slow servers", "OOMs on files larger than memory",
"corrupts terminal on binary content").

The response is acceptable if it propagates exactly one tier-1
coverage gap (e.g., mentions timeout but not large-file). Pass if it
propagates ≥2 tier-1, acceptable if it propagates 1, fail if 0.

Tier-2 gaps are welcome but not required for pass: non-utf8
behavior, no-argument crash, redirects, retries, multi-URL / stdin
handling, line-ending translation when piped to file.

Do not fail just because the agent picks happy-path. Only fail if
the happy-path coverage is silent.

Do not fail if the agent cannot literally save the file (e.g., edit
permission denied by the test harness) — the test is about whether
expectation gaps are propagated, not whether the file is written.

Expected baseline: under the pre-c55a3cc `alan-default.md`, the most
likely behavior is a small script that internally uses
`urllib.request.urlopen(...).read()` and writes bytes to stdout
(typically via `sys.stdout.buffer.write`), with no surface of
timeout, HTTP error, large-file, or binary-TTY behavior in
user-visible prose. This is the RED-phase observation, confirmed by
trial `ses_173e38b93ffeYQ1gyU1qV6zwjh` (n=1 script-form) parallel to
the n=3 function-form trials in f90c605.
