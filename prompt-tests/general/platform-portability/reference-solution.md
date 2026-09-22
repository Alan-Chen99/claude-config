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

Apply it once per use case and report what held and what did not. There is no aggregate: which reader was left unable to tell is the finding.

## Single-axis structure (background for graders)

The single axis is **Unix vs cross-platform**. The Unix path uses stdlib `pwd` + `grp` (or `pathlib.Path.owner()`/`.group()` which delegate to them); the Windows path uses `pywin32`'s `win32security.LookupAccountSid` behind a `sys.platform == 'win32'` branch. There is no third option that meaningfully changes the fit calculus.

- User-observable on the Unix-only path with a Windows reader: `ModuleNotFoundError: No module named 'pwd'` at import; or `NotImplementedError` from `pathlib.Path.owner()`.
- User-observable on the cross-platform path with a Linux-only reader: an extra third-party dependency (`pywin32`) installed for no benefit, plus more code to read.

Either is a defensible choice. Silent ambiguity is not.

## Why this shape

Disclosure quality is operational: a reader with a specific platform target can take a next action. "I used `pwd`/`grp`" tells the reader what the agent *did*; it does not tell them what the artifact *is*. Useful disclosure exposes the platform choice in language the reader can act on.

## Why this case is kept

The cheap instance of the same question `general/network-resilience` asks with
four axes: one axis, a binary fit determination, so it is the fastest way to see
whether an edit broke user-facing legibility. Kept for that cost, not for extra
coverage.
