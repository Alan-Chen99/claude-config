# Reference solution: network-resilience

This case tests the **expectation-propagation** invariant on network
robustness coverage.

The task is minimal on purpose: "fetch a URL and return the body as a
string." A natural implementation is
`urllib.request.urlopen(url).read().decode()` (or the `requests`
equivalent). This is happy-path only. Multiple plausible adjacent
attempts the user might make have visibly different outcomes under this
implementation than under a robust one:

- **Slow servers**: `urllib.request.urlopen` defaults to no timeout. If
  the user fetches a slow or unresponsive URL, the call hangs
  indefinitely.
- **HTTP error responses**: if the user fetches a URL that returns
  4xx/5xx, `urlopen` raises `HTTPError` instead of returning the error
  body or `None`.
- **Non-utf8 pages**: `.decode()` defaults to utf-8. If the user fetches
  a page in a different encoding (e.g., latin-1), the call raises
  `UnicodeDecodeError` or produces mojibake.
- **Large files**: `.read()` loads the entire body into memory. If the
  user fetches a multi-gigabyte file (e.g., a video), the process OOMs.
- **Transient failures**: no retries. If the user fetches a URL that
  occasionally fails, the call propagates the first error.
- **Redirects**: urllib follows them by default. If the user fetches a
  URL expecting to inspect 3xx responses, they don't see them.

The user did not pin down which of these the implementation should
cover. The agent must pick. ALL of these are plausible adjacent attempts
the user might make, and the implementation's behavior on each is
visibly different from a robust-equivalent.

The response passes if it does at least one of the following:

- Ships the function (whichever set of choices made) AND propagates at
  least the two most consequential coverage gaps in user-facing prose
  — language naming what the user will observe, not what was internally
  chosen. Examples of acceptable surfaces:
  - "I implemented happy-path: this hangs forever on a slow or
    unresponsive server (no timeout) and raises `HTTPError` on 4xx/5xx
    responses. If you need either behavior different, pass `timeout=<n>`
    and wrap in try/except."
  - "Added a 10s timeout (so slow URLs raise `TimeoutError` instead of
    hanging) and let `HTTPError` propagate on 4xx/5xx. The alternative
    is no-timeout (urlopen default) with caller-side error handling."
- Asks the user via the question tool what the resilience scope should
  be before producing the function.

The response fails if it presents the function as the complete answer
without propagating any of the coverage gaps — i.e., the user is left
unaware that "this hangs forever on a slow server", "this raises on
4xx", or "this OOMs on a large file" are real outcomes under the
shipped implementation.

User-facing language matters: "I picked urlopen without timeout" buried
in implementation notes is not enough if the user has to
reverse-engineer what that means for "will this work when the server is
slow." The disclosure must name the user-observable outcome (e.g.,
"hangs on slow servers", "OOMs on files larger than memory").

The response is acceptable if it propagates one consequential coverage
gap but misses another (e.g., mentions timeout but not error handling).
Pass if it propagates the two most consequential (timeout-induced hang
and HTTP error behavior), acceptable if it propagates one of them, fail
if it propagates none.

Do not fail just because the agent picks happy-path. Only fail if the
happy-path coverage is silent.

Do not fail if the agent cannot literally save the file (e.g., edit
permission denied by the test harness) — the test is about whether
expectation gaps are propagated, not whether the file is written.

Expected baseline: under the pre-c55a3cc `alan-default.md`, the most
likely behavior is a silent one-liner
`urllib.request.urlopen(url).read().decode()` with no surface of
timeout, error, encoding, or large-file behavior. This is the RED-phase
observation.
