# Documentation Conventions

The authoritative conventions for code-adjacent documentation (CLAUDE.md, README.md).

## Core Principles

**Self-contained documentation**: CLAUDE.md and README.md must not defer to
external authoritative sources (doc/ directories, wikis, external
documentation): summarize that knowledge locally. Duplication is acceptable;
the maintenance burden is the cost of locality.

**CLAUDE.md = pure index + policy**: CLAUDE.md says WHAT is in the directory
and WHEN to read each file, plus any agent policy -- behavioral rules and
constraints agents must follow, which apply to all descendants. Explanation
(architecture, decisions, invariants) belongs in README.md. Claude Code
auto-loads CLAUDE.md from the working directory and all parent directories
upward. That covers ancestors, not descendants: this repo
tracks 60 CLAUDE.md files and a session started at the root carries two of them
— the user's `~/.claude/CLAUDE.md` and this repo's root file — with every nested
one absent from the opening context (observed 2026-09-13, cc 2.1.269). Put
policy an agent must obey from its first turn at the root or above; a nested
file reaches the agent only once something pulls it in. In cc 2.1.310's source
that is a `Read` or a write of a file under it, or a Bash command viewing one
file (a lone `cat`, `head`, `tail`, `sed -n` or `grep`). A nested file over
40,000 characters, or over 5% of the model's context window at 3 characters a
token (4 on pre-5 models) if that is larger, loads only up to its last line
break within that size, with a note to `Read` the rest (`"Only the start of
this file is shown."`).

**README.md = invisible knowledge**: README.md captures knowledge NOT visible
from reading the source code. If ANY exists for a directory, README.md is
required.

## Documentation budget

Prose that is always present is always paid for. Every tracked `.md` counts
against a group in `doc-budget.toml`, grouped by how its text reaches a
context — every request, every session, per invocation, per spawn, on demand —
unless a `[data]` entry there declares it not guidance, though a `README.md` or
`CLAUDE.md` counts wherever it is unless a capture wrote it (an entry marked
`generated`: captured data is generated and does not count); design in
`docs/superpowers/specs/2026-09-29-doc-budget-design.md`. Measure with
`uv run doc-budget [path]` in the checkout you are editing — each checkout's
venv measures its own tree: local-tokenizer tokens, what `count-tokens`
reports without `--api`.

**Over cap, cut that group to 80% of cap in the same change** — the agent that
crossed the line pays. A group already over when you arrived is debt: say so,
and pay it when the task is about its docs rather than in passing. A
`[held.files]` row is the exception: it falls due with the next task on what
its file is about — for a `CLAUDE.md` or `SKILL.md`, its directory, and a task
on any part of it counts; for an agent body, that agent; for a doc, note, spec
or plan, the subproject, subcommand or behaviour it records; a sweep across the
tree is about none of them — whether or not the task edits the file: drop the
row and, over the class cap, cut the file to 80% of it or ask the user for a
cap of its own. `uv run doc-budget <dir>` lists the rows under a
directory; read the table for the rest. An addition in passing puts the file
over its row, which is its cap: cut to 80% of the row, then lower it to the
new size, or drop it when that size is within the class cap — the tool does
not ratchet, and a row left standing is headroom the file regrows into.

Only consolidation satisfies the cap: merge duplicates, resolve the conflicts
you find, delete what the code already says. Moving a body's reference material
into an on-demand `.md` under the group that loads it later (a skill's
`references/`, a `docs/` file) is a cut — it stays counted, under the mechanism
that pays for it. Moving prose out of `.md` (into a comment, JSON, a script's
`--help`, a pointer to an external source) is not a cut. Neither is loosening
the registry: a `[data]` entry, a held size or a cap above the one the group
would otherwise have needs the user's approval, asked for at cut time with what
the 80% target would lose, never ahead of it; the tool checks only that the
approving session is not the running one, so an entry an agent approves is
inert in the session that wrote it.

What survives is non-rederivable and changes an action — the test is whether
not knowing it makes an agent do the wrong thing. Everything else goes,
including good writing — git history keeps it.

## CLAUDE.md Format Specification

### Index Format

```markdown
## Files

| File       | What                           | When to read                              |
| ---------- | ------------------------------ | ----------------------------------------- |
| `cache.rs` | LRU cache with O(1) operations | Implementing caching, debugging evictions |
```

`## Subdirectories` is the same table with a `Directory` column.

- **File/Directory**: names in backticks: `cache.rs`, `config/`
- **What**: factual description of contents (nouns, not actions)
- **When to read**: task-oriented triggers using action verbs (implementing,
  debugging, modifying, adding, understanding). Test: given the task "add a new
  validation rule", can an LLM scan this column and identify the right file?
- At least one column must have content; empty cells use `-`

Generated and vendored files/directories MUST be flagged as not for manual
editing: the What column (or a Regenerate section) gives the origin and the
regeneration command, and When to read says so:

| Directory    | What                              | When to read        |
| ------------ | --------------------------------- | ------------------- |
| `proto/gen/` | Generated from proto/. Run `make` | Never edit directly |
| `vendor/`    | Vendored deps, upstream: go.mod   | Never edit directly |

### ROOT vs SUBDIRECTORY CLAUDE.md

**SUBDIRECTORY**: `# [directory-name]/`, then the Files and Subdirectories
tables.

**ROOT**: `# [Project Name]`, one sentence on what this is, the Files and
Subdirectories tables, then `## Build` and `## Test` (copy-pasteable commands),
`## Development` (setup, environment requirements, workflow notes) and
`## Agent Policy` (coding standards, tool preferences, workflow constraints,
things to always/never do).

A CLAUDE.md contains only the file/directory index (REQUIRED), a one-sentence
overview, operational sections (Build, Test, Regenerate, Deploy or similar:
copy-pasteable commands for this directory's artifacts with minimal context,
not prose on why the build works) and agent policy. Architecture, design
decisions and rationale, invariants and multi-paragraph prose go to README.md.

## README.md Specification

Create a README.md when the directory holds ANY invisible knowledge --
knowledge NOT visible from reading the code: planning decisions (from the
Decision Log), business context, architectural rationale, trade-offs,
invariants not in types, rejected alternatives, non-obvious performance
characteristics, non-obvious contracts between components, domain knowledge
encoded in the directory structure, failure modes or edge cases not apparent
from individual files, and rules not enforced by compiler or linter. The
trigger is semantic, not structural (file count, complexity). Do NOT create one
for a purely organizational directory, or to restate what the code shows.

**Content test**: for each sentence, ask "Could a developer learn this by
reading the source files?" If yes, delete it.

**Structure**: `# [Component Name]`, then `## Overview` (one paragraph: the
problem and the approach), `## Architecture` (how sub-components interact,
data flow, key abstractions), `## Design Decisions` (trade-offs, alternatives
considered), `## Invariants` (rules not enforced by code).

## Architecture Documentation

For cross-cutting concerns spanning several directories, write a dedicated
`# Architecture: [System/Feature Name]` document with `## Overview`,
`## Components` (each one's single responsibility and boundaries),
`## Data Flow` (critical paths), `## Design Decisions` and `## Boundaries`
(what the system does NOT do; where responsibility ends). Components must
explain relationships -- what each delegates, what it never touches, where its
state lives, and the flow between them -- not just list responsibilities.
Prefer diagrams over prose for relationships.

## In-Code Documentation

Knowledge belongs as close as possible to the code it describes; only
cross-cutting knowledge that cannot be localized goes to README.md.

### Tier 1: Inline Comments

Above a statement or expression whose choice is non-obvious. Document *why*
this approach, never *what* the code does: `# Polling: 30% webhook delivery
failures observed in production`, not `# Poll the endpoint`. When a decision
log entry exists, cite it: `# DL-003: Polling over webhooks`.

### Tier 2: Function-Level Explanation Blocks

After the signature, before the body logic, of a function with >3 distinct
transformation steps, that coordinates multiple subsystems, or that implements
a non-obvious algorithm: what it does, how, how it fits the overall
architecture and what problem it solves. Skip CRUD operations and standard
patterns where the code speaks for itself.

### Tier 3: Docstrings

**Private functions**: a one-line summary plus a trigger clause (when to call):
`"""Strip whitespace and lowercase. Use before cache lookup."""`

**Public functions**: summary, trigger clause, parameter semantics and an
example. Trigger clauses and examples let an LLM select the right tool.

### Tier 4: Module Documentation

A top-of-file comment or module docstring: what the module contains and why it
exists as a separate unit (e.g., the approach chosen and the alternatives
rejected).

### Tier 5: Invisible Knowledge Placement

Invisible knowledge (business context, architectural rationale, trade-offs,
constraints, rejected alternatives) goes to the closest viable location:

1. **Inline comment**: knowledge about a specific statement
2. **Function-level block**: about a whole function's approach or algorithm
3. **Module docstring**: about why the module exists or its overall design
4. **README.md**: cross-cutting (spans files/modules) or not localizable to a
   single code point

Knowledge captured only in planning artifacts (decision logs, plan documents,
conversation history) is not acceptable: every decision, constraint and
trade-off must land in code or README.md.

### Priority Order

Document the most uncertain first:

| Priority | Code Pattern                 | WHY Question           |
| -------- | ---------------------------- | ---------------------- |
| HIGH     | Multiple valid approaches    | Why this approach?     |
| HIGH     | Thresholds, timeouts, limits | Why these values?      |
| HIGH     | Error handling paths         | Recovery strategy?     |
| HIGH     | External system interactions | What assumptions?      |
| MEDIUM   | Non-standard pattern usage   | Why deviate from norm? |
| MEDIUM   | Performance-critical paths   | Why this optimization? |
| LOW      | Boilerplate, simple CRUD     | Skip unless unusual    |
