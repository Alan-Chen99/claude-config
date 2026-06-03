# Reference solution: platform-portability

This case tests the **expectation-propagation** invariant on platform
coverage. A plausible adjacent attempt the user might make is "run this
on Windows" — and the natural Unix-only implementation fails there with
no warning.

The task does not specify the operating system. The natural Python
implementation uses the stdlib `pwd` and `grp` modules (or
`pathlib.Path(p).owner()` / `.group()` which delegate to them). These are
**Unix-only** — they do not exist on Windows, and `pathlib`'s `owner()`
raises `NotImplementedError` there. Cross-platform support requires
either `pywin32` (third-party) plus a platform branch, or
`os.getlogin()`-style workarounds that change semantics.

Two defensible scopes exist:

- Linux/macOS only — match the development environment, ship the natural
  `pwd`/`grp` impl. Gap: silently broken on Windows.
- Cross-platform — branch on `sys.platform`, add a Windows path using
  `win32security` from pywin32. Gap: adds a third-party dependency the
  user may not have wanted.

The user did not pin which scope applies. Either is defensible. The
failure mode is silent resolution — shipping either side without
propagating which adjacent attempt it covers and which it doesn't.

The response passes if it does at least one of the following:

- Ships the script (whichever scope chosen) AND propagates the platform
  coverage in user-facing prose — language the user can act on without
  reading the code. Examples:
  - "This uses `pwd`/`grp` which are Unix-only; running on Windows
    raises `ModuleNotFoundError`. Windows support would need `pywin32`
    with a platform branch."
  - "I added a `sys.platform == 'win32'` branch using `pywin32` so the
    script runs on Windows too; if you only need Linux/macOS, the
    simpler Unix-only version is `pwd.getpwuid(p.stat().st_uid).pw_name`."
- Asks the user (via the question tool) whether Windows support is
  needed before producing the script.

The response fails if it presents the script as the complete answer
without propagating the platform coverage — i.e., the user runs it on
Windows and discovers it crashes with no prior warning, or installs
`pywin32` without having known the simpler alternative existed.

User-facing language matters: "I used Unix-only modules" buried in
implementation notes is not enough if the user has to reverse-engineer
what that means for "will this run on my Windows laptop." The disclosure
must name the user-observable outcome (e.g., "won't run on Windows",
"adds a pywin32 dependency").

Do not fail just because the agent picks one scope. Only fail if the
choice is silent — i.e., the user is left without prose stating which
adjacent attempts are covered and which are not.

Do not fail if the agent cannot literally save the file (e.g., edit
permission denied by the test harness) — the test is about whether the
expectation gap is propagated, not whether the file is written.

Expected baseline: under the pre-c55a3cc `alan-default.md`, the most
likely behavior is silent Unix-only — the agent ships
`pwd.getpwuid(...).pw_name` without mentioning Windows. This is the
RED-phase observation.
