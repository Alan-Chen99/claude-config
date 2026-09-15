# Built-in skill bodies — claude-cli 2.1.269

512,397 characters of instruction the model can be handed, none of which a
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
vary by model: `workflow-authoring`, `code-review`, `design` and `loop` were
captured on both opus-5 and sonnet-5 and came back byte-identical (same
sha256). This is the opposite of tool *descriptions*, which do vary — `WebFetch`
is 469 characters on opus-5 and 1,608 on sonnet-5 — which is why
`tool-search-loaded` is captured per model and this directory is not.

`manifest.json` records the model each body was captured on.

## What was captured

| skill | chars | route | shape |
|---|---:|---|---|
| `update-config` | 260,942 | slash | body |
| `claude-api` | 88,344 | slash | body |
| `design` | 55,398 | slash | body |
| `workflow-authoring` | 16,966 | slash | body |
| `artifact-design` | 16,627 | skill | body |
| `keybindings-help` | 13,946 | skill | body |
| `artifact-capabilities` | 13,278 | slash | body |
| `security-review` | 10,763 | slash | body |
| `loop` | 7,865 | slash | body |
| `fewer-permission-prompts` | 7,523 | slash | body |
| `dataviz` | 7,036 | slash | body |
| `artifact-diagramming` | 3,619 | slash | body |
| `run` | 3,250 | slash | body |
| `simplify` | 2,817 | slash | body |
| `init` | 2,312 | slash | body |
| `code-review` | 1,572 | slash | body |
| `schedule` | 139 | slash | **stub** |

`update-config` is not a typo: its body is the settings.json schema, and it is
half of everything in this table.

`schedule` is the one skill with no body here. It answers *"We're having trouble
connecting with your remote claude.ai account to set up a scheduled task"* — a
connectivity failure against the account backend, not an entitlement gate, so
its real text is capturable on a machine where that link works.

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
  command" there. `design` returns a 169-character *"only manages agent access"*
  stub in `-p` and its full 55,398-character body interactively.
- **`--setting-sources project,local`.** With `local` alone `design` and
  `code-review` degrade to stubs.
- **A repo with a resolvable `origin/HEAD`.** `/security-review` interpolates
  `` !`git diff origin/HEAD...` `` into its own prompt and injects *nothing* when
  that command fails, so a bare `git init` captures it as empty. `capture.py`
  seeds a commit and an `origin/HEAD` for skill capture only
  (`seed_git_origin`), leaving every variant capture's environment unchanged.

## Normalized paths

A skill shipping resource files is extracted to
`<tmp>/bundled-skills/<version>/<random hex>/<name>` and told that absolute path,
which differs on every capture. `capture_skills._normalize` rewrites it to
`<bundled-skills-dir>`; `manifest.json` flags the five bodies that needed it
(`artifact-capabilities`, `claude-api`, `dataviz`, `design`, `run`).
`tests/test_builtin_skills.py` fails if an un-normalized path reaches a
committed file.

## `security-review` embeds its repo

Its body interpolates live `git status` and the diff under review, so the
captured text contains the synthetic capture repo's state. That is reproducible
— the seeded repo is the same every run — but it means a diff in that file can
come from the capture environment rather than from the release.
