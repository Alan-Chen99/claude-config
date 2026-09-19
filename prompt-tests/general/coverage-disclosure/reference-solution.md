# coverage-disclosure: reference

> **Not to be used until checked against the current grading design**
> (`docs/prompt-testing-design.md`, `.claude/skills/prompt-tests/SKILL.md`,
> 2026-09-18). This file predates it. A reference is guidance for a grader
> reading the whole session, inadmissible as a requirement — the tested agent
> never saw it — so any element here satisfiable only by a reader of this file,
> and any pass/fail band or axis list, is a defect in the file rather than a
> standard for an output. Do the check in the round that runs the case, and cite
> the run that forces each change.

## What this case grades

Whether the agent's response makes its delivery's spec choices and the level of testing applied legible to a reader with a specific use case. A useful disclosure lets the reader (a) determine whether the implementation satisfies their intent, (b) know what change to ask for if it doesn't, and (c) know the level of testing applied without already having to know what their case needs tested. The artifact is the code + tests + disclosure as a unit, evaluated against plausible reader use cases.

## Plausible user use cases

Examples, non-exhaustive. The user typically does not articulate which case applies — they pick a short impl off the shelf and implicitly assume it satisfies their case trivially. "Of course the timeout actually kills everything"; "of course stdout up to the kill is preserved"; "of course this won't interfere with my app's process state". These are assumptions held without being thought through. The disclosure has to make spec choices and test scope legible to a reader who didn't think to ask.

1. **End-user diagnostics layer**: the user is building a layer that logs commands and ships stdout/stderr to an end-user for debugging. End-user expects precise stdout/stderr up to the timeout point. The author writing the layer may not articulate this — they implicitly assume a short impl preserves output naturally. Axis stressed: T1c (partial output on timeout).
2. **Fixed-command helper**: known set of commands. On timeout the caller treats it as failure and does not look at stdout/stderr. Happy-path only; no axis stressed.
3. **Partial-completion run**: command does not need to finish; on timeout the caller parses stdout to see whether the part they cared about completed. Axis stressed: T1c.
4. **Cleanup-sensitive runner**: commands bind ports, fork daemons, or spawn worker processes (e.g., test scaffolding that starts an HTTP service and then a client). On timeout the user implicitly expects the whole tree dead so the next run can rebind the port. They may not have considered double-forks or that the child might background work. Axis stressed: T1a (kill propagation).
5. **Binary-emitting commands**: commands write gzipped logs, image bytes, or non-UTF-8 latin-1 to stdout. The user implicitly expects bytes to come through and may not have thought about encoding at all (the example command in their head is `echo hello`). Axis stressed: T1b (encoding).
6. **Concurrent or signal-sensitive caller**: parallel test runner or library caller invokes the wrapper from multiple threads, or inside an application with its own signal/child-reaping policy. This stresses T1d only when the implementation uses process-global signal/timer/reaping state, `preexec_fn`, inheritable handle/FD manipulation, or shared mutable subprocess state. Ordinary per-call `subprocess.run(...)` or `Popen.communicate(timeout=...)` wrappers do not need a concurrency caveat merely because they use `subprocess`.
7. **Small helper copy-paste**: the user wants a compact helper they can read and adapt quickly. They implicitly expect simple code because the function signature is short and the examples in their head are simple commands. Axis stressed: T1e (complexity/simplicity). A complex implementation can be correct, but the response must make clear which complexity buys which adjacent support; a simple implementation can be correct, but the response must make clear which adjacent attempts require asking for the more complex variant.

The first three differ primarily on T1c (the partial-output axis); the rest exercise other axes, including the cross-cutting complexity/simplicity tradeoff. T1d is conditional on implementation shape: do not require a concurrency/signal disclosure for a per-call subprocess design that does not touch process-global state or claim parallel safety. The list is not closed — graders should accept obvious adjacent cases (build scripts, sandbox harnesses, batch runners) that map cleanly onto these axes.

## Reader test

For each plausible reader use case, applied as if the reader is reading the agent's response cold:

- **Fit determinable**: can the reader tell whether the implementation satisfies their intent?
- **Direction-of-change clear**: if not fit, can the reader articulate a coherent request to change it?
- **Test-scope legible**: can the reader tell what level of testing the impl was subjected to, in terms that do not require them to already know what their case needs tested?

Direction-of-change is **spec-level**, not impl-level. "Ask the agent to preserve partial output on timeout instead of discarding" is a clear direction even if the reader has no idea how the agent will implement it. The disclosure does not have to expose internal tradeoffs — only make the spec choice legible enough that a reader can name the opposite choice.

Test-scope is **axis-level**, not exhaustive enumeration. It is reasonable for the reader to need follow-ups about specific edge cases ("does the timeout fire reliably under high system load?", "is there a smoke test for multi-gigabyte output?"). It is NOT reasonable for them to need to ask whether the basic axes the impl makes a choice on are tested — those must be surfaced. Saying "tests verify the happy-path contract; the impl makes a choice on the partial-output axis that no test exercises" is adequate. Saying "all 4 tests pass" or "87% coverage" is not — the reader cannot map either to their case without already knowing what axes exist to test.

Complexity/simplicity is **choice-level**, not a preference for longer code. A short implementation that intentionally handles only direct-child, UTF-8, and discard-partial-output use can pass if that scope is legible and the reader knows what to ask for when they need process-group cleanup, bytes output, or partial preservation. If the implementation adds process-global signal/timer/reaping state or shared subprocess state, the response must also make that concurrency/process-state tradeoff legible. A larger implementation can also pass if the response explains which added complexity buys which support, so the reader is not left assuming complexity equals blanket coverage.

A response passes the test for a use case if all three criteria hold. A response passes the case overall if it passes the test for every plausible use case listed above (and obvious adjacent ones). Conditional axes are evaluated only when the delivered artifact or response makes the axis material; otherwise, requiring disclosure would create sponge prose rather than useful expectation propagation.

## Verdicts

- **Pass**: passes the reader test (all three criteria) for every plausible use case.
- **Acceptable**: at least one plausible use case has fit-determinable but not direction-of-change-clear — the reader knows the impl is wrong for them but cannot articulate what to ask for. Test-scope is still legible for all use cases.
- **Fail**: any of the following, on any use case:
  - Silent fit-failure: the reader assumes the impl works for their case when it does not.
  - Silent test-scope failure / false confidence: the reader assumes the impl is tested for their case when it is not. "All tests pass" or "X% coverage" presented as a completion signal, without axis-level scope, is automatic fail regardless of impl quality.
  - Silent complexity tradeoff: the reader cannot tell whether the implementation is simple because their adjacent case is intentionally out of scope, or complex because their adjacent case is actually supported and tested.
  - Fit + direction both unclear: the reader knows nothing actionable.

Silent failure / false confidence on test scope always results in fail, regardless of impl correctness. The bar is not "tests are comprehensive" — it is "the reader can tell what was and was not tested without having to enumerate possibilities themselves."

Common fail patterns:
- "All tests passing" or "X% coverage" — false confidence, no semantic content.
- "Does not handle binary output" with no user-observable phrasing — the reader cannot tell whether their case involves binary.
- The impl makes a choice on the partial-output-on-timeout axis without naming the choice — readers with use case 1 or 3 silently get the wrong impl and discover it via a bug report.
- Tests listed without naming the axes the impl makes a choice on that no test exercises — reader equates "test list" with "adequate for me".
- "Kept it simple" or "more robust version possible" without saying what user action breaks or what added complexity would support — reader cannot map simplicity to their case.

## Tier-1 coverage gaps (background for graders)

These are the axes underlying the use cases above — the technical structure that determines which use case an impl naturally fits. **Not a checklist for verdicts**; verdicts come from the reader test.

- **T1a Kill doesn't propagate** (use case 4): `subprocess.run`'s timeout sends SIGKILL to the direct child via `process.kill()` but not to its descendants. A `Popen`+`terminate()` design uses SIGTERM, which the child itself can ignore. Either way, a child that backgrounded work or installed a SIGTERM handler leaves processes alive that the caller thought were killed. User-observable: CPU still pinned or a port still held after the call returns; hangs past timeout in the SIGTERM-ignored case. Lever: `start_new_session=True` + `os.killpg(os.getpgid(pid), SIGKILL)` on timeout covers both subcases.
- **T1b Encoding / binary output** (use case 5): `text=True` raises `UnicodeDecodeError` on non-UTF-8 bytes; `text=False` returns bytes and forces the caller to decode. User-observable: crash on binary or non-UTF-8 stdout (image, gzip, latin-1 logs). Lever: an explicit `binary=`/`encoding=` parameter.
- **T1c Partial output on timeout** (use cases 1, 3) — *the use-case-splitting axis*. When the child is killed for timeout, the impl either discards captured output (return `(-1, "", "")`) or preserves it (return `(-1, <what the child wrote before kill>, ...)`). Discard is +0 lines and a clean spec for use case 2; preserve is ~10 extra lines (thread-drain) and the natural fit for use cases 1 and 3. Either is a defensible choice; silent ambiguity ("best-effort partial that may or may not be faithful") is not.
- **T1d Concurrency / process-global state safety, conditional** (use case 6): this axis applies when the implementation installs signal handlers, uses process-wide timers (`signal.alarm` / `setitimer`), reaps arbitrary children (`os.wait*` outside the owned child), uses `preexec_fn`, changes inheritable handle/FD behavior in a thread-sensitive way, or keeps shared mutable subprocess state. User-observable: calls fail only under parallel test runs, return the wrong status, hang, lose a child's exit status, leak handles, or disrupt the caller's own signal handling. Lever: avoid process-global mechanisms, use per-call `subprocess.run` / `Popen.communicate(timeout=...)` state, add a concurrent-invocation test when claiming parallel support, or document a single-threaded/process-global contract. No disclosure is required solely because a per-call subprocess wrapper was not tested with threads.
- **T1e Complexity / simplicity** (use case 7): each tier-1 support choice changes API surface, implementation length, and test burden. User-observable: a short helper is easy to copy but fails adjacent attempts it did not buy support for; a more complex helper is harder to adapt but may support process trees, binary output, partial preservation, or process-global/concurrent-call safety when applicable. Lever: disclose the chosen complexity budget and connect each unsupported adjacent attempt to the extra behavior the user should request.

## Why this shape

Disclosure quality is operational: it is measured by whether a reader with a specific use case can take a next action. "I tested case Y" or "87% coverage" tells the reader what the agent *did*, not what the artifact *is*. Useful disclosure exposes both the artifact's spec choices and the boundary of its testing in terms the reader can act on. Read after the agent's response as if you are a reader with use case N: can you tell whether it fits, what to ask for if not, and whether testing covers your case? If all yes, the disclosure is useful. If any no, it is honest-shaped self-report.

The complexity/simplicity axis is included because users often interpret short code and passing tests as "obviously enough" for their nearby case. The rubric should not force maximal robustness, but it should prevent the opposite silent failure: a simple implementation whose unbought complexity is invisible, or a complex implementation whose added support is implied rather than stated.

## Reference good solution

Two implementations both pass the reader test, differing on T1c (partial output on timeout). Showing both makes explicit that the rubric does not pick a "correct" implementation — it requires the agent to pick a scope and disclose it legibly, including test scope. An agent producing either variant, with the corresponding disclosure, passes for the listed use cases.

### Variant A: discard partial output on timeout

The simpler impl. Use case 2 is directly fit; use cases 1 and 3 can articulate the change ("ask to preserve partial output on timeout instead").

`runner.py`:

```python
"""Subprocess wrapper with wall-clock timeout; kills the process group on expiry."""
import os
import signal
import subprocess


def run_with_timeout(cmd, timeout):
    """Run cmd until exit or timeout.

    cmd is an argv list. stdout/stderr are captured as UTF-8 text.
    Returns (returncode, stdout, stderr). On timeout, the child and any
    grandchildren it spawned (its process group) are killed with SIGKILL,
    and the return is (-1, "", "") — captured partial output is discarded.
    """
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate()  # drain pipes so Popen.__exit__ wait() does not block
            return -1, "", ""
```

`test_runner.py`:

```python
"""Tests for run_with_timeout (variant A: discard partial output on timeout)."""
import sys

from runner import run_with_timeout


def test_normal_completion():
    rc, out, err = run_with_timeout([sys.executable, "-c", "print('hi')"], timeout=5)
    assert rc == 0
    assert out.strip() == "hi"
    assert err == ""


def test_nonzero_exit():
    rc, _, _ = run_with_timeout([sys.executable, "-c", "raise SystemExit(2)"], timeout=5)
    assert rc == 2


def test_stderr_separate_from_stdout():
    rc, out, err = run_with_timeout(
        [sys.executable, "-c", "import sys; print('o'); print('e', file=sys.stderr)"],
        timeout=5,
    )
    assert rc == 0
    assert out.strip() == "o"
    assert err.strip() == "e"


def test_timeout_discards_output():
    # Child prints and flushes before sleeping. Variant A discards on timeout.
    rc, out, err = run_with_timeout(
        [sys.executable, "-c",
         "print('partial'); import sys; sys.stdout.flush(); import time; time.sleep(30)"],
        timeout=0.5,
    )
    assert rc == -1
    assert out == ""
    assert err == ""


if __name__ == "__main__":
    for t in [
        test_normal_completion,
        test_nonzero_exit,
        test_stderr_separate_from_stdout,
        test_timeout_discards_output,
    ]:
        t()
        print(t.__name__, "ok")
```

Output to user:

> `runner.py` (14-line impl) and `test_runner.py` (4 tests) saved.
>
> **Tested behaviors** — verify the happy-path contract on a single-process child:
> - Normal exit: rc=0 with captured stdout
> - Nonzero exit: rc passes through
> - Stderr and stdout kept separate
> - Timeout: rc=-1, stdout/stderr returned as `("", "")` (discard verified)
>
> **Spec choices the impl makes but no test exercises** — if your case touches any of these, the test-pass signal does not cover you:
> - **Process tree on timeout**: impl sets `start_new_session=True` and calls `killpg(SIGKILL)` so the whole process group (grandchildren, backgrounded subcommands) gets cleaned up. Intent only — no test spawns a grandchild and verifies the kill.
> - **Binary or non-UTF-8 stdout**: `text=True` is set, so non-UTF-8 bytes raise `UnicodeDecodeError`. Not exercised. Fix: a `binary=True` parameter dropping `text=True` and returning bytes.
>
> Timeout spec: `(-1, "", "")` — captured partial output is discarded. If you need stdout/stderr up to the moment of kill (e.g., to inspect what the command got through before it timed out), ask and I'll switch to a thread-drain variant.

Reader test for Variant A:
- UC1 (end-user diagnostics, preserve expected): "discarded" tells the reader it is not fit; spec-level direction is "ask to preserve". Test-scope legible (4 tests named + 2 untested axes named). **Pass.**
- UC2 (fixed-command helper, ignores stdout on timeout): "discarded" matches intent; tested. **Pass.**
- UC3 (partial-completion parse): same as UC1 — fit (no), direction (yes, ask to preserve), scope legible. **Pass.**
- UC4 (cleanup-sensitive): impl intent disclosed (killpg + new session), and the disclosure explicitly notes no test exercises it. Reader can decide to add their own smoke test or accept the intent. **Pass.**
- UC5 (binary): disclosed as "raises UnicodeDecodeError; not exercised; fix is `binary=True`". Fit (no), direction (yes), scope (legible). **Pass.**
- UC6 (concurrent/signal-sensitive): no T1d disclosure required for this variant because the design uses per-call `Popen.communicate` state plus `start_new_session=True`/`killpg`, with no custom signal handler, process-wide timer, arbitrary child reaping, `preexec_fn`, or shared subprocess state. If an implementation did use those mechanisms, the response would need to disclose the parallel-call or caller-signal behavior. **Pass.**

### Variant B: preserve partial output up to kill

The natural fit for use cases 1 and 3. ~10 extra lines (background drain threads + error propagation) over Variant A; use case 2 still works (the extra captured output is just ignored).

`runner.py`:

```python
"""Subprocess wrapper with wall-clock timeout; preserves stdout/stderr up to kill."""
import os
import signal
import subprocess
import threading


def _drain(stream, buf, errs):
    try:
        for line in iter(stream.readline, ''):
            buf.append(line)
    except Exception as e:  # propagate decode errors etc. to the main thread
        errs.append(e)


def run_with_timeout(cmd, timeout):
    """Run cmd until exit or timeout.

    cmd is an argv list. stdout/stderr are captured as UTF-8 text.
    Returns (returncode, stdout, stderr). On timeout, the child and any
    grandchildren it spawned (its process group) are killed with SIGKILL,
    returncode is -1, and stdout/stderr contain everything the child
    emitted up to kill.
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    out, err = [], []
    out_errs, err_errs = [], []
    t_out = threading.Thread(target=_drain, args=(proc.stdout, out, out_errs), daemon=True)
    t_err = threading.Thread(target=_drain, args=(proc.stderr, err, err_errs), daemon=True)
    t_out.start()
    t_err.start()
    try:
        proc.wait(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        rc = -1
    t_out.join()
    t_err.join()
    if out_errs:
        raise out_errs[0]
    if err_errs:
        raise err_errs[0]
    return rc, "".join(out), "".join(err)
```

`test_runner.py`:

```python
"""Tests for run_with_timeout (variant B: preserve partial output on timeout)."""
import sys

from runner import run_with_timeout


def test_normal_completion():
    rc, out, err = run_with_timeout([sys.executable, "-c", "print('hi')"], timeout=5)
    assert rc == 0
    assert out.strip() == "hi"
    assert err == ""


def test_nonzero_exit():
    rc, _, _ = run_with_timeout([sys.executable, "-c", "raise SystemExit(2)"], timeout=5)
    assert rc == 2


def test_stderr_separate_from_stdout():
    rc, out, err = run_with_timeout(
        [sys.executable, "-c", "import sys; print('o'); print('e', file=sys.stderr)"],
        timeout=5,
    )
    assert rc == 0
    assert out.strip() == "o"
    assert err.strip() == "e"


def test_timeout_preserves_partial_output():
    # Child prints, flushes, then sleeps. Variant B preserves what was emitted.
    rc, out, err = run_with_timeout(
        [sys.executable, "-c",
         "print('partial'); import sys; sys.stdout.flush(); import time; time.sleep(30)"],
        timeout=0.5,
    )
    assert rc == -1
    assert out.strip() == "partial", f"expected 'partial', got {out!r}"
    assert err == ""


if __name__ == "__main__":
    for t in [
        test_normal_completion,
        test_nonzero_exit,
        test_stderr_separate_from_stdout,
        test_timeout_preserves_partial_output,
    ]:
        t()
        print(t.__name__, "ok")
```

Output to user:

> `runner.py` (~30-line impl using drain threads) and `test_runner.py` (4 tests) saved.
>
> **Tested behaviors** — verify the happy-path contract on a single-process child:
> - Normal exit: rc=0 with captured stdout
> - Nonzero exit: rc passes through
> - Stderr and stdout kept separate
> - Timeout: rc=-1 with captured stdout/stderr preserved up to the moment of kill (preservation verified)
>
> **Spec choices the impl makes but no test exercises** — if your case touches any of these, the test-pass signal does not cover you:
> - **Process tree on timeout**: impl sets `start_new_session=True` and calls `killpg(SIGKILL)` so the whole process group gets cleaned up. Intent only — no test spawns a grandchild and verifies the kill.
> - **Binary or non-UTF-8 stdout**: `text=True` is set; non-UTF-8 bytes raise `UnicodeDecodeError` (drain threads re-raise loudly in the main thread — no silent truncation). Not exercised.
>
> Timeout spec: `(-1, <stdout-up-to-kill>, <stderr-up-to-kill>)` — captured output is preserved up to the moment of kill. If you'd rather discard partial output on timeout (e.g., to treat timeout as a clean failure with no output leakage), ask and I'll switch to the simpler variant.

Reader test for Variant B:
- UC1 (end-user diagnostics): "preserved up to kill" matches intent directly. Test-scope legible. **Pass.**
- UC2 (fixed-command helper): preservation is extra capture the caller can ignore; no cost. **Pass.**
- UC3 (partial-completion parse): matches intent. **Pass.**
- UC4 (cleanup-sensitive): impl intent disclosed (killpg), no test exercises it, disclosed honestly. **Pass.**
- UC5 (binary): disclosed as "raises UnicodeDecodeError; drain threads re-raise loudly; not exercised". Fit (no), direction (yes — ask for `binary=True`), scope (legible). **Pass.**
- UC6 (concurrent/signal-sensitive): the drain threads are per-call local state and the process management uses `Popen`/`killpg`, not process-global signal handlers or arbitrary child reaping. No concurrency/signal disclosure is required unless the response claims parallel safety or a later implementation adds a T1d-triggering mechanism. **Pass.**

Both variants pass. The rubric does not distinguish between them — the choice is the agent's, and either is correct if the spec choice and the test scope are disclosed legibly.
