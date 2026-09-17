# cc-pretty: accept a session id as well as a path

`cc-pretty` takes a filesystem path to a `.jsonl` log. Its sibling
`opencode-pretty` takes a session id. `skills/session-analysis/SKILL.md` prints
the asymmetry on two adjacent lines:

```
- opencode:    agent-tools opencode-pretty <session-id> --skeleton
- Claude Code: agent-tools cc-pretty <file.jsonl> --skeleton
```

An id is what a reader actually has. It is what `env-context` reports at session
start, what a `sessionId` field holds, what an `agentId` field holds, and what a
notification names. Turning one into a path means knowing the project-slug
encoding and running a `find`. This closes that gap.

Every count below was measured on 2026-09-17 against `~/.claude/projects` on this
machine, not inferred.

## What resolves

Two families of transcript are addressable by id.

| Family | Path shape | Count here |
| --- | --- | --- |
| Session | `<config>/projects/<slug>/<uuid>.jsonl` | 1437 |
| Subagent | `<config>/projects/<slug>/<uuid>/subagents/**/agent-<hex>.jsonl` | 1427 |

`<config>` is `$CLAUDE_CONFIG_DIR` when set, else `~/.claude` — the directory
Claude Code itself reads, matching the rule `agent-tools` uses to resolve its
root.

The `**` in the subagent pattern is load-bearing. 21 of the 1427 sit one level
deeper, at `subagents/workflows/wf_<id>/agent-<hex>.jsonl`, written by the
Workflow tool. They are ordinary subagent transcripts. A non-recursive glob finds
1406 and silently misses every one of them.

The `agent-` prefix in the pattern is also load-bearing, and for the opposite
reason: it excludes `subagents/workflows/wf_<id>/journal.jsonl`, which shares the
extension but is a content-hash-keyed record of `started`/`result` pairs, not a
transcript.

Both stems and 8-character prefixes are collision-free across all 2864 files, so
prefix matching is not a theoretical convenience here.

## Resolution rules

`resolve_log_arg(arg, *, config_dir=None) -> str`, in
`src/claude_config/cc_pretty/locate.py`.

1. **Path wins.** If `os.path.exists(arg)`, return `os.path.abspath(arg)`. An
   existing file is never reinterpreted as an id, so a file named
   `fdca30e5-….jsonl` sitting in the working directory still opens as itself.
2. Otherwise glob both families under `<config>/projects/`.
3. A candidate matches when its stem starts with `arg`, **or** its stem starts
   with `agent-` + `arg`.
4. Exactly one match wins. Zero raises. Two or more raise, listing up to 10
   candidate paths and a count of any remainder.

Rule 3's second clause exists because both id spellings genuinely occur in the
logs: a transcript's `agentId` field holds bare hex (`a347c60a97a0451fb`), while
filenames and inline references carry the prefix (`agent-a319b990d0ab0087c`).
Accepting one form would reject whichever the reader happened to copy.

A bare hex argument can in principle prefix-match a session UUID as well as a
subagent stem. That is not a special case — it is two matches, and rule 4 already
reports it.

Both globs together cost 14 ms over 2864 files. No cache, no index, no manifest.

## Failure

`SessionNotFound` is raised by the resolver, so the function is testable and
usable as a library call. `main()` catches that one type, prints its message to
stderr, and exits 2.

A raw traceback is wrong here. Command-line arguments are a system boundary, the
one place validation earns its keep — and a typo'd id is an expected input, not
an unexpected exception. Unknown exceptions still propagate.

The zero-match message names the config directory that was searched, because the
common cause is a session logged under a different `$CLAUDE_CONFIG_DIR`, which is
invisible from the argument alone.

## The resolved path in the output

`log_path` becomes the resolved **absolute** path. The legend's recovery line is
built from it:

```
# recover: sed -n '<n>p' /root/.claude/projects/<slug>/<uuid>.jsonl | jq -r '<path>'
```

Absolute rather than as-typed, so the recipe runs from any directory. A relative
argument previously produced a recipe that worked only from the directory the
render happened in — a trap for a reader who reads the render later or elsewhere.

When the argument was resolved from an id, one line precedes the legend:

```
# source: fdca30e5 → /root/.claude/projects/-root-claude-config-work3/fdca30e5-0961-4ff2-8197-f8554d372964.jsonl
```

Only in the id case. In the path case the reader typed the path and the recovery
line repeats it; an unconditional line would be duplicated context in a header
that agents read on every invocation. It appears in both full and `--skeleton`
renders, since either may be the only thing a reader sees.

## CLI

The positional becomes `target`:

```
cc-pretty <target>   session id, subagent id (full or unique prefix),
                     or path to a .jsonl file
```

`--validate-only` resolves first, so it validates the same file the render would.

## Out of scope

`cc-pretty-intercept` takes `~/.claude/requests-log/<session>/NNNN.json` — also
id-shaped, and a candidate for the same treatment, but a different store with a
different key. `cc-render-coverage` dispatches on the `.jsonl` extension to pick
a renderer and reads paths from stdin; ids would need that dispatch rethought.
Both keep taking paths.

## Tests

`tests/test_cc_pretty_locate.py`, driving `main()` end-to-end against a synthetic
`projects/` tree in `tmp_path` with `CLAUDE_CONFIG_DIR` monkeypatched:

- a relative path, an absolute path, and a file in the working directory named
  like a session id — all open as paths
- a full session id, and a session id prefix
- a subagent id in both spellings
- a subagent nested under `workflows/wf_<id>/`
- `journal.jsonl` is not resolvable
- an ambiguous prefix names its candidates; an unknown id names the config dir
- the `# source:` line appears for an id and not for a path, in both render modes

## Documentation

Updated: the `main.py` module docstring, the root `CLAUDE.md` `cc-pretty` bullet,
and `skills/session-analysis/SKILL.md` where the two commands sit adjacent.

Not updated: `docs/superpowers/plans/` and `docs/prompt-trials/`, which record
what was done at the time.
