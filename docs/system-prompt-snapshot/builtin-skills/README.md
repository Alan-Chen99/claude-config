# Built-in skill bodies and files — claude-cli 2.1.310

What invoking each built-in skill hands the model, and the files five of them extract for it to
read, none of which a `default` capture records: that capture carries each skill's *name and
description*, in the same reminder block as the agent-type listing, and the body only on
invocation. The body is the part that changes between releases, so it is the part worth
diffing.

Regenerate with `../capture_skills.py`. The roster is read from the skill listing inside
`../opus-5/default/request.json`, not from a list in the script, so a release that adds a
built-in skill shows up as a test failure until it is captured. `manifest.json` is the
per-skill record: shape (`body` or `stub`), the route that reached it, characters, sha256, each
extracted file's bytes and sha256, which needed normalized paths, and the model captured on.

## Not per model

Stored once rather than under each model directory, because the bodies do not vary by model:
`workflow-authoring`, `code-review` and `loop` were captured on both opus-5 and sonnet-5
(2.1.269) and came back byte-identical (same sha256). Some tool *descriptions* do vary, which is
why `tool-search-loaded` is captured per model and this directory is not.

## What was captured

`update-config` is the largest body by far, more than half of all the characters here: it is
the settings.json schema.

`schedule` is the one skill with no body here. It answers *"We're having trouble
connecting with your remote claude.ai account to set up a scheduled task"* — a
connectivity failure against the account backend, not an entitlement gate, so
its real text is capturable on a machine where that link works.

## Extracted files

A skill that ships files has them written as it is invoked, to
`<tmp>/claude-<uid>/bundled-skills/<version>/<random hex per process>/<name>`,
and its body opens by naming that directory. `capture_skills.py` copies it into
`<name>/` here, so `<bundled-skills-dir>/reference.md` in a body is
`<name>/reference.md` beside it. Three of the five sets are fixed by the release —
`claude-api`'s with the build's model ids filled in — and two are not:

- `plugin-authoring/types/claude-code.d.ts` is an embedded declaration file
  followed by typings generated from the session's non-MCP tools (`Ue()`,
  `src/chunk-shyejxf8.js:1454`), so a tool whose schema a server flag changes
  changes it too: `Artifact`'s differed between two 2.1.289 sessions.
- `artifact-capabilities/<contract>/` is the platform's `window.claude` type
  definitions for the runtime contract the server names, fetched as the skill
  loads (its `**Call contract**` line, `src/chunk-n7dvjfwp.js:250`); its body is
  composed from the same platform. One build got contract 0.2.69 on 2026-10-06
  and 0.2.75 on 2026-10-12; 2.1.310 got 0.2.90. A failed fetch extracts nothing,
  which `capture_skills.py` warns about when the last capture had files.

## Two routes

Neither route reaches every skill, so `capture_skills.py` tries `slash` and
falls back to `skill`:

- **slash** — typing `/<name>` injects the body before the model acts at all, so
  nothing depends on the model choosing to comply.
- **skill** — the `Skill` tool, for the two that are not slash commands.
  `artifact-design` and `keybindings-help` answer `/name` with *"Unknown
  command"* and *"This skill can only be invoked by Claude, not directly by
  users"* respectively.

The route is recorded because a skill moving between them is a change in how users can reach
it.

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

Each value that differs between two captures of one release is replaced exactly, wherever it
appears: the extraction directory by `<bundled-skills-dir>`, the child's session id by
`<session-id>`, its working directory by `<cwd>`, and the config directory by `<config-dir>`
(`plugin-authoring` names `<config-dir>/dev-mods/<session-id>`); what follows a value is kept.
`tests/test_builtin_skills.py` fails if a per-run path reaches a committed file, or if a body
names a file under `<bundled-skills-dir>` that was not captured.

## `security-review` embeds its repo

Its body interpolates live `git status` and the diff under review, so the captured text holds
the synthetic capture repo's state: the same every run, its `.claude/` ignored by its own rule
rather than this machine's global one (`capture.py`), but a diff in that file can come from
the capture environment rather than from the release.
