# Built-in skill bodies and files — claude-cli 2.1.289

533,724 characters of instruction the model can be handed, and 114 files
(2,897,457 bytes) that five skills extract for it to read, none of which a
`default` capture records. That capture carries each skill's *name and
description* — they ride in the same reminder block as the agent-type listing —
and the body only on invocation. The body is the part that changes between
releases, so it is the part worth diffing.

Regenerate with `../capture_skills.py`. The roster is read from the skill
listing inside `../opus-5/default/request.json`, not from a list in the script,
so a release that adds a built-in skill shows up as a test failure until it is
captured.

## Not per model

Stored once rather than under each model directory, because the bodies do not
vary by model: `workflow-authoring`, `code-review` and `loop` were captured
on both opus-5 and sonnet-5 (2.1.269) and came back byte-identical (same
sha256). This is the opposite of tool *descriptions*, some of which do vary —
`WebFetch` is 651 characters on opus-5 and 1,841 on sonnet-5 — which is why
`tool-search-loaded` is captured per model and this directory is not.

`manifest.json` records the model each body was captured on.

## What was captured

| skill | chars | files | route | shape |
|---|---:|---:|---|---|
| `update-config` | 288,012 |  | slash | body |
| `claude-api` | 100,907 | 79 | slash | body |
| `artifact-design` | 31,691 |  | skill | body |
| `artifact-capabilities` | 20,518 | 13 | slash | body |
| `workflow-authoring` | 16,966 |  | slash | body |
| `keybindings-help` | 14,924 |  | skill | body |
| `security-review` | 10,753 |  | slash | body |
| `plugin-authoring` | 8,638 | 7 | slash | body |
| `loop` | 8,122 |  | slash | body |
| `fewer-permission-prompts` | 7,523 |  | slash | body |
| `dataviz` | 7,036 | 9 | slash | body |
| `code-review` | 6,497 |  | slash | body |
| `artifact-diagramming` | 3,619 |  | slash | body |
| `run` | 3,250 | 6 | slash | body |
| `simplify` | 2,817 |  | slash | body |
| `init` | 2,312 |  | slash | body |
| `schedule` | 139 |  | slash | **stub** |

`update-config` is not a typo: its body is the settings.json schema, and it is
more than half of the characters in this table.

`schedule` is the one skill with no body here. It answers *"We're having trouble
connecting with your remote claude.ai account to set up a scheduled task"* — a
connectivity failure against the account backend, not an entitlement gate, so
its real text is capturable on a machine where that link works.

## Extracted files

A skill that ships files has them written as it is invoked, to
`<tmp>/claude-<uid>/bundled-skills/<version>/<random hex per process>/<name>`,
and its body opens by naming that directory. `capture_skills.py` copies it into
`<name>/` here, so `<bundled-skills-dir>/reference.md` in a body is
`<name>/reference.md` beside it; `manifest.json` records each file's size and
sha256. Three of the five sets are fixed by the release — `claude-api`'s with
the build's model ids filled in — and two are not:

- `plugin-authoring/types/claude-code.d.ts` is an embedded declaration file
  followed by typings generated from the session's non-MCP tools (`bBr`,
  `src/chunk-gppff98a.js:17425`), so a tool whose schema a server flag changes
  changes it too: `Artifact`'s differed between two 2.1.289 sessions.
- `artifact-capabilities/<contract>/` is the platform's `window.claude` type
  definitions for the runtime contract the server names, fetched as the skill
  loads (`src/chunk-3vz7qf6p.js:1053`); its body is composed from the same
  platform. 2026-10-06 got contract 0.2.69 and 2026-10-12 got 0.2.75, on one
  build. A failed fetch extracts nothing, which `capture_skills.py` warns about
  when the last capture had files.

## Two routes

Neither route reaches every skill, so `capture_skills.py` tries `slash` and
falls back to `skill`:

- **slash** — typing `/<name>` injects the body before the model acts at all, so
  nothing depends on the model choosing to comply.
- **skill** — the `Skill` tool, for the two that are not slash commands.
  `artifact-design` and `keybindings-help` answer `/name` with *"Unknown
  command"* and *"This skill can only be invoked by Claude, not directly by
  users"* respectively.

`manifest.json` records which route reached each skill, because that is a fact
about the release: a skill moving between them is a change in how users can
reach it.

## Capture conditions that change the result

Three settings materially change what comes back, and getting any of them wrong
yields a plausible-looking stub rather than an error:

- **Interactive, not `-p`.** Print mode carries a smaller tool roster, and the
  skills gated on the `Artifact` tool become unreachable — `artifact-design`,
  `artifact-diagramming` and `artifact-capabilities` all answer "Unknown
  command" there.
- **`--setting-sources project,local`.** With `local` alone `code-review`
  degrades to a stub.
- **A repo with a resolvable `origin/HEAD`.** `/security-review` interpolates
  `` !`git diff origin/HEAD...` `` into its own prompt and injects *nothing* when
  that command fails, so a bare `git init` captures it as empty. `capture.py`
  seeds a commit and an `origin/HEAD` for skill capture only
  (`seed_git_origin`), leaving every variant capture's environment unchanged.

## Normalized paths

Each value that differs between two captures of one release is replaced
exactly, wherever it appears: the extraction directory by
`<bundled-skills-dir>`, the child's session id by `<session-id>`, its working
directory by `<cwd>`, and the config directory by `<config-dir>` —
`plugin-authoring` names `<config-dir>/dev-mods/<session-id>`. What follows a
value is kept, so a body still says which file it means. `manifest.json` flags
each body and file that needed it. `tests/test_builtin_skills.py` fails if a
per-run path reaches a committed file, or if a body names a file under
`<bundled-skills-dir>` that was not captured.

## `security-review` embeds its repo

Its body interpolates live `git status` and the diff under review, so the
captured text contains the synthetic capture repo's state. That is reproducible
— the seeded repo is the same every run, and ignores its `.claude/` by its own
rule, not this machine's global one (`capture.py`) — but it means a diff in
that file can come from the capture environment rather than from the release.
