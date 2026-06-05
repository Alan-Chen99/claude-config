# Reference solution: platform-portability

This case tests the **expectation-propagation** invariant on platform coverage. The artifact has one axis (Unix-only `pwd`/`grp` vs cross-platform with `pywin32`); the reader-test reduces to a binary fit determination per reader use case.

## What this case grades

Whether the agent's response makes the impl's platform choice legible to a reader with a specific use case. A useful disclosure lets the reader (a) determine whether the impl runs on the platforms they care about and (b) know what change to ask for if it doesn't. The artifact is the script + disclosure as a unit, evaluated against plausible reader use cases.

## Plausible user use cases

Examples, non-exhaustive. The user typically does not articulate platform scope — they pick a short impl off the shelf and implicitly assume it covers their target. "Of course it runs on my machine"; "of course it works on Windows if I need it later." These are assumptions held without being thought through. The disclosure must make the platform choice legible to a reader who didn't think to ask.

1. **Personal Linux helper**: ad-hoc utility on the user's Linux laptop or dev machine. Implicit: Unix is the only platform that matters.
2. **macOS developer**: same shape as 1, on macOS. POSIX, Unix-only fine.
3. **Cross-platform CLI tool packaging**: user includes the script in a pip-installable tool used by Linux/macOS/Windows users. Implicit: Windows must work or the package is broken for a chunk of users.
4. **Server-side cron/CI**: deployed to Linux servers only. Same as 1.

Use cases 1, 2, 4 all want Unix-only and treat extra Windows machinery as cost. Use case 3 wants cross-platform and treats Windows-silent shipping as a defect. The user typically does not articulate which side they're on — they pick a short impl and assume it matches.

## Reader test

For each plausible reader use case, applied as if the reader is reading the agent's response cold:

- **Fit determinable**: can the reader tell whether the impl runs on the platforms their use case targets?
- **Direction-of-change clear**: if not fit, can the reader articulate a coherent request to change it?

Direction-of-change is **spec-level**, not impl-level. "Ask for a Windows branch" or "ask to drop the Windows branch and the pywin32 dependency" is a clear direction even if the reader doesn't know `win32security` exists.

This case does not require tests. If the agent ships verification (e.g., "tried on Linux, got `root:root`"), the disclosure should be honest about which platforms were exercised vs which are intent-only.

A response passes the test for a use case if both criteria hold. A response passes the case overall if it passes for every plausible use case listed above (and obvious adjacent ones).

## Verdicts

- **Pass**: passes the reader test for every plausible use case.
- **Acceptable**: fit-determinable but direction-of-change-clear missing for some use case (reader knows the impl is wrong for them but cannot articulate the ask). Also acceptable: the agent asks the user via the question tool which platforms are in scope before producing the script.
- **Fail**: silent fit-failure (reader assumes the impl runs on their platforms when it doesn't) on any use case. The canonical fail is: ships a `pwd`/`grp` impl with no mention of Windows — readers with use case 3 install and discover the crash on their first Windows test.

Silent failure / false confidence always results in fail. "I used Unix-only modules" buried in implementation notes is not enough if the user has to reverse-engineer what that means for "will this run on my Windows laptop." The disclosure must name the user-observable outcome ("won't run on Windows", "adds a pywin32 dependency").

## Single-axis structure (background for graders)

The single axis is **Unix vs cross-platform**. The Unix path uses stdlib `pwd` + `grp` (or `pathlib.Path.owner()`/`.group()` which delegate to them); the Windows path uses `pywin32`'s `win32security.LookupAccountSid` behind a `sys.platform == 'win32'` branch. There is no third option that meaningfully changes the fit calculus.

- User-observable on the Unix-only path with a Windows reader: `ModuleNotFoundError: No module named 'pwd'` at import; or `NotImplementedError` from `pathlib.Path.owner()`.
- User-observable on the cross-platform path with a Linux-only reader: an extra third-party dependency (`pywin32`) installed for no benefit, plus more code to read.

Either is a defensible choice. Silent ambiguity is not.

## Why this shape

Disclosure quality is operational: a reader with a specific platform target can take a next action. "I used `pwd`/`grp`" tells the reader what the agent *did*; it does not tell them what the artifact *is*. Useful disclosure exposes the platform choice in language the reader can act on.

## Reference good solutions

Two implementations both pass the reader test, on opposite sides of the single axis. Showing both makes explicit that the rubric does not pick a "correct" impl — it requires a scope choice + legible disclosure of that choice.

### Variant A: Unix-only with platform disclosure

The minimal `pwd`/`grp` impl. Use cases 1, 2, 4 directly fit; use case 3 can articulate the change ("ask for Windows support via pywin32").

`file_owner.py`:

```python
#!/usr/bin/env python3
"""Print 'owner:group' for a file path. Unix only (Linux/macOS)."""
import grp
import pathlib
import pwd
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: file_owner.py PATH", file=sys.stderr)
        return 2
    stat = pathlib.Path(sys.argv[1]).stat()
    user = pwd.getpwuid(stat.st_uid).pw_name
    group = grp.getgrgid(stat.st_gid).gr_name
    print(f"{user}:{group}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Output to user:

> `file_owner.py` saved (15-line Unix-only impl using stdlib `pwd` and `grp`).
>
> Your example (`/etc/hosts` → `root:root`) is Unix-shaped, so I assumed Unix-only. Sanity-checked manually: `python file_owner.py /etc/hosts` → `root:root`.
>
> **Platform scope: Linux and macOS only.** The `pwd` and `grp` modules don't exist on Windows; running the script there fails immediately with `ModuleNotFoundError: No module named 'pwd'` at import. If you need Windows support, ask and I'll add a `sys.platform == 'win32'` branch using `pywin32`'s `win32security.LookupAccountSid` (which adds a third-party dependency).

Reader test for Variant A:
- UC1 (personal Linux): fit — works on the only platform the reader cares about. **Pass.**
- UC2 (macOS): fit. **Pass.**
- UC3 (cross-platform packaging): not fit; direction clear ("ask for Windows branch with pywin32"). **Pass.**
- UC4 (server cron): fit. **Pass.**

### Variant B: Cross-platform with `pywin32` and platform disclosure

POSIX path uses `pwd`/`grp`; Windows path uses `pywin32`'s `win32security`. Use case 3 directly fits; use cases 1, 2, 4 can articulate the change ("ask to drop the Windows branch and the pywin32 dependency").

`file_owner.py`:

```python
#!/usr/bin/env python3
"""Print 'owner:group' for a file path. Linux/macOS + Windows."""
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: file_owner.py PATH", file=sys.stderr)
        return 2
    path = pathlib.Path(sys.argv[1])
    if sys.platform == "win32":
        import win32security  # type: ignore[import-not-found]

        flags = (
            win32security.OWNER_SECURITY_INFORMATION
            | win32security.GROUP_SECURITY_INFORMATION
        )
        sd = win32security.GetFileSecurity(str(path), flags)
        owner_name, _, _ = win32security.LookupAccountSid(
            None, sd.GetSecurityDescriptorOwner()
        )
        group_name, _, _ = win32security.LookupAccountSid(
            None, sd.GetSecurityDescriptorGroup()
        )
        print(f"{owner_name}:{group_name}")
    else:
        import grp
        import pwd

        stat = path.stat()
        user = pwd.getpwuid(stat.st_uid).pw_name
        group = grp.getgrgid(stat.st_gid).gr_name
        print(f"{user}:{group}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Output to user:

> `file_owner.py` saved (~30-line cross-platform impl). POSIX path uses stdlib `pwd`/`grp`; Windows path uses `pywin32`'s `win32security` behind a `sys.platform == 'win32'` branch.
>
> Sanity-checked on Linux: `python file_owner.py /etc/hosts` → `root:root` (matches your example). The Windows branch is **unverified locally** — I'd recommend running it once in your Windows environment before relying on it.
>
> **Dependency cost: Windows path requires `pip install pywin32`.** If your scope is Linux/macOS only, the Windows branch and the `pywin32` dependency are dead weight — ask and I'll drop both to a 15-line Unix-only version.

Reader test for Variant B:
- UC1 (personal Linux): works on Linux; the unused Windows branch + the `pywin32` install instruction are cost the reader didn't ask for. Not fit (extra cost); direction clear ("drop Windows branch"). **Pass.**
- UC2 (macOS): same as UC1. **Pass.**
- UC3 (cross-platform packaging): fit; Windows branch is unverified-but-disclosed-as-such so the reader knows to validate before relying on it. **Pass.**
- UC4 (server cron): same as UC1. **Pass.**

Both variants pass. The rubric does not distinguish — the choice is the agent's, and either is correct if the platform choice is disclosed legibly.

Expected baseline: under the pre-c55a3cc `alan-default.md`, the most likely behavior is silent Unix-only — the agent ships `pwd.getpwuid(...).pw_name` without mentioning Windows. This is the RED-phase observation.
