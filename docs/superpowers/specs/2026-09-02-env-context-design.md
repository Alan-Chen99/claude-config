# env-context: dynamic session context under `--system-prompt-file`

Redesign of `agent-tools env-context` (`src/claude_config/env_context/`), the
`SessionStart` hook that supplies dynamic context to sessions whose system prompt
comes from `sys_prompt/alan-default-next.md`.

Source citations below point at `/repos/claude-code-decompiled`, an ESM-rewritten
dump of the Claude Code 2.1.235 binary. `claude --version` reports 2.1.235, so the
dump matches what is installed. Identifier hashes are version-specific; the line
numbers hold for 2.1.235 only.

## Problem

This section describes `env-context` as it stood before this redesign —
including a `jq`-piped `SessionStart` wiring since replaced (see "Hook input
and wiring") — not the implementation specified below.

`env-context` reproduces the five-field env block of cc 2.1.143. Three defects
follow from that, all measured rather than inferred.

**The block is four minor versions stale.** cc 2.1.235 builds its env block in
`_dE` (`src/globals/21.js:13480`), which emits up to fifteen bullets. Ours emits
five.

**`Shell: unknown` is faithful, not broken.** cc's `Kml()`
(`src/globals/21.js:13560`) reads `$SHELL` and falls back to the literal string
`'unknown'`; there is no other POSIX fallback. The `claude` process has no `SHELL`
in its environment, so cc itself would print `Shell: unknown` here. Meanwhile the
Bash tool's own shell resolution (`src/globals/10.js:22633`) independently selects
a real shell and exports it — a Bash tool subprocess sees `SHELL=/bin/bash`. The
field is accurate about cc and useless about the session.

**The scratchpad section is missing for the main agent but present for
subagents.** `cvi()` (`src/globals/21.js:13624`) renders `# Scratchpad Directory`;
`sV()` includes it at `src/globals/21.js:13377`, and `--system-prompt-file`
discards that whole assembly. Subagents are unaffected, because `Xff`
(`src/globals/14.js:26405`) appends the section to subagent prompts on a separate
path. In session `c8978898-32b4-4d5e-a29c-f8f79e1d6759`, 61 intercepted requests
under `~/.claude/requests-log/` carry `# Scratchpad Directory` naming
`/tmp/claude-0/-root-claude-config-work/c8978898-.../scratchpad`, while the main
agent was told nothing. Those directories currently hold 1.2 GB across 139
sessions, 9 of them non-empty.

Two further facts constrain the design.

**The hook discards its input.** `settings.json` runs
`agent-tools env-context | jq -Rs …`, so the payload on stdin is thrown away. A
`SessionStart` payload captured from a probe session carries `session_id`,
`transcript_path`, `cwd`, `hook_event_name`, `source`, and sometimes a resolved
`model` such as `claude-haiku-4-5-20251001`.

Whether `model` is present depends on which internal call site fired the hook,
not on `source` or interactive-vs-print: a fresh interactive startup, an in-app
session resume/fork, and `compact` each pass one (`globals/28.js:8017`,
`globals/13.js:32825`), while a process-launched `--resume`/`--continue` and
`/clear` do not (`globals/17.js:19270`, `globals/18.js:7920`) — and that
no-model resume path shares the identical `source: "resume"` label with the one
that does, so `source` cannot predict it either. There is no clean rule to
state; the hook already treats `model` as always possibly absent.

**Only two sections are actually missing.** Reading this session's own request
(`~/.claude/requests-log/c8978898-…/0002.json`) shows the system array as three
blocks: a 132-byte identity block, a 57-byte block, and the prompt file with a
`gitStatus:` block appended. `claudeMd`, `userEmail` and `currentDate` still
arrive in the `<system-reminder>` user message, and `<total_tokens>` is still
present. The gaps are the env block and the scratchpad section, nothing else.

## Decisions

| Decision | Choice |
| --- | --- |
| Fidelity to cc | Purpose-built block; divergence is reviewed, not prevented |
| Scratch location | `CLAUDE_CODE_TMPDIR` redirect, so cc builds the path itself |
| Drift detection | Hook warns, `scripts/check-env-context.sh` explains |
| Scratch pruning | Manual script only; the hook never mentions size |

`env-context` no longer tries to be a copy of `_dE`. It emits the context this
setup needs, and a drift check reports when cc's own block changes so the field
set is re-reviewed deliberately.

## Hook input and wiring

`env_context/__main__.py` reads the hook JSON from stdin and writes the
`hookSpecificOutput` envelope itself. `settings.json` drops the `jq` pipe:

```
"command": "agent-tools env-context"
```

`cwd` comes from the payload rather than `os.getcwd()`. `model` is rendered when
present and omitted when absent; print-mode sessions therefore lose the model line
rather than gaining a fabricated one. A payload that fails to parse is an error
that propagates — a hook that silently emits a partial block would leave the
session believing it had context it does not have.

## The env block

```
# Environment
You have been invoked in the following environment: 
 - Primary working directory: <payload cwd>
 - This is a git worktree of <main checkout>. …        (worktrees only)
 - <git stash caution>                                  (worktrees only)
 - Is a git repository: <true|false>
 - Platform: <sys.platform>
 - Shell: <resolved Bash-tool shell>
 - OS Version: <platform.system()> <platform.release()>
 - You are powered by the model <model id>             (when payload carries it)
 - Session ID: <session id>
 - NOTE: <drift note>                                  (when cc's own block has drifted)
```

Bullets use cc's ` - ` prefix (`jSe`, `src/globals/21.js:13158`), and the header
line keeps cc's trailing space after the colon, so the block reads identically,
byte for byte, to the one cc produces elsewhere.

**Shell** reports the shell the Bash tool will actually run, resolved by cc's
algorithm at `src/globals/10.js:22633`: `CLAUDE_CODE_SHELL` when it names a valid
bash or zsh; else `$SHELL` when it contains `bash` or `zsh`; else a candidate list
ordered zsh-first unless `$SHELL` names bash, drawn from `which zsh`, `which bash`,
`/bin`, `/usr/bin`, `/usr/local/bin`, `/opt/homebrew/bin`; first executable wins.
On this machine zsh is absent and the result is `/bin/bash`, matching the `SHELL`
a Bash tool subprocess actually sees. This is a deliberate reimplementation: the
value cc puts in its own block is not the value it runs commands with.

**Worktree lines** are emitted when `git rev-parse --git-common-dir` differs from
`--git-dir`. cc keys its equivalent on an internal worktree-session registry
(`cv()`, `src/globals/04.js:7126`) that only tracks worktrees cc created, so cc
stays silent in a worktree made by hand. The bullet names the main checkout, not
the raw `--git-common-dir` path: an ordinary (non-bare) main checkout's common
dir is `<main>/.git`, and a trailing `.git` path component is stripped before
naming it, since naming that `.git` directory while telling the agent not to
edit or build in the directory just named would point at a path the message
never actually gave. `/root/claude-config-work` is one of five
worktrees of `/repos/claude-config`, and `git worktree list` shows four of them
checked out concurrently. They share one stash stack, which is a live hazard for
concurrent sessions and worth stating where cc would not. The stash caution is
cc's own text (`cTm`, `src/globals/21.js:13688`).

**Session ID** is not a cc field. It is included because the scratchpad path,
`~/.claude/projects/<slug>/<id>.jsonl`, and `~/.claude/requests-log/<id>/` are all
keyed by it, and a session that knows its own id can find its own artifacts.

Dropped from cc's block as carrying no operational value here: knowledge cutoff,
the model-ID list (`iTm`, `src/globals/21.js:13029`), the product-availability
line, and the fast-mode line. Not implemented because the payload does not carry
them: additional working directories, and the proxy note (`jWo`,
`src/globals/05.js:6878`).

## Scratchpad

### Redirect

`scripts/claude.sh` exports `CLAUDE_CODE_TMPDIR=/root/.claude/tmp` before its
`exec`. cc feeds that variable into `Spe()` (`src/globals/05.js:8056`), which roots
the scratchpad path, so cc builds the new location itself — for the main agent and
for subagents, whose section we cannot otherwise edit. `agent-tools claude` execs
`scripts/claude.sh` (`agent-tools/src/claude.rs:84`), so one change covers both
launchers.

The resulting path, which cc constructs and `env-context` reports:

```
/root/.claude/tmp/claude-0/-root-claude-config-work/<session-id>/scratchpad
```

The `claude-<uid>/<slug>/<session-id>/scratchpad` tail is cc's own construction
(`Bbt()`, `src/globals/20.js:18616`) and cannot be shortened without giving up the
agreement between main agent and subagents.

A probe session run with `CLAUDE_CODE_TMPDIR` set created `claude-0` under the
redirected root and nothing under `/tmp/claude-0`, confirming cc honours it.

`Spe()` also roots plugin session directories, skill and plugin zip staging, the
IPC socket directory, and entries in the sandbox write allowlist. The socket is
the only one with a hard constraint, and cc already guards it — but `Spe()` is
only its fallback root: `SFm()` (`src/globals/22.js:14393`) roots the socket at
`XDG_RUNTIME_DIR` first, reaching `Spe()` only when that is unset, and falls
back further to `/tmp/cc-socks-<uid>/` when the resulting path exceeds the
`sun_path` limit.

### Reporting and creation

`env-context` emits:

```
# Scratchpad Directory

Use this directory for temporary files instead of `/tmp` or other system
temp directories:
`<path>`

Only use `/tmp` if the user explicitly requests it.

It is session-specific, isolated from the project, and is normally the same
directory your subagents are given.
```

**Why `Only use /tmp...` is there at all:** four other places in this
deployment say the opposite — `sys_prompt/alan-default-next.md`, both output
styles, and the user's global `CLAUDE.md` (outside this repo) each carry a
`git clone … /tmp/<repo>` instruction or a "use a new directory under
`/tmp/*`" rule. None of them is edited to match: the system prompt and
output styles shape agent behaviour well beyond this hook, and the global
`CLAUDE.md` is the user's own. The clause's own wording is the
reconciliation, not an edit to those four files — a standing instruction
that names `/tmp` counts as the user "explicitly" requesting it, so an
agent reading both clones a repo to `/tmp` as directed and puts everything
else, its own working files, in the scratchpad.

The path is computed the way cc computes it, reading the root from
`CLAUDE_CODE_TMPDIR` with the same `os.tmpdir()` default rather than hardcoding
`/root/.claude/tmp`. A session launched by bare `claude` therefore still gets a
truthful path instead of one naming a directory cc did not use.

The slug is `cwd` with `[^a-zA-Z0-9]` replaced by `-` (`FDo`,
`src/globals/02.js:2156`). Past 200 characters (`vie`,
`src/globals/02.js:2753`) cc appends a hash suffix (`q9`,
`src/globals/02.js:2160`); that branch raises rather than guessing, because the
hash function behind it has not been verified and a wrong path is worse than a
loud failure. Our paths are far below the limit.

`env-context` creates the directory with `mkdir -p`, mode `0o700`, matching
`_Fi()` (`src/globals/20.js:18630`). This is not redundant. Creation is gated by
`b1e()` (`src/globals/20.js:18583`) on a remote `tengu_scratch` gate or
artifact-tool eligibility, and an unauthenticated probe session produced no
scratchpad after 30 seconds of uptime. The directory cannot be assumed to exist.

A background session (`CLAUDE_CODE_SESSION_KIND=bg`) gets no `# Scratchpad
Directory` section at all: the hook checks that env var before ever calling
into scratchpad creation, and drops the whole block once there is no path to
name. `SessionStart` hooks fire from `settings.json` regardless of
which prompt the session runs, so `env-context` still runs there — cc's own
`cvi()` (`src/globals/21.js:13624`) drops its scratchpad section the same way
and substitutes a `# Background Session` block naming `$CLAUDE_JOB_DIR/tmp`
(`SdE()`, `src/globals/21.js:13595`) instead. Emitting ours too would leave
the session with two conflicting temp-directory instructions.

## Pruning

`scripts/prune-scratch.sh`, run by hand. Nothing deletes automatically and the
hook never mentions scratch size.

It resolves the tmp root by calling `scratchpad.tmp_root()` directly — a
bare `python3 -c` one-liner shelling into the same function the hook itself
uses, not a shell reimplementation of its search order — so the two cannot
independently drift on which tree "the" scratch root names, the way a bare
`${CLAUDE_CODE_TMPDIR:-/tmp}` expansion once did by skipping `$TMPDIR`. It
then reports each session directory beneath it in three buckets: empty
scratchpads as prunable, non-empty ones with their sizes, and sessions with
no scratchpad directory at all (reported, but never touched by bulk
`--apply` — there is nothing there for it to delete). It is dry-run by
default and deletes only under `--apply`, and only empty scratchpads — a
non-empty one may hold work in progress, and a session id alone does not
distinguish a dead session from a live one. Deleting a named non-empty
session requires naming it explicitly.

Run it to see current counts rather than trust a quoted figure here: the
1.2 GB/139-session count in "Problem" above was itself gone by the time this
feature shipped — `/tmp` was wiped mid-project, which is exactly what the
redirect now survives.

## Drift check

`scripts/check-env-context.sh` resolves the installed binary from
`CLAUDE_CODE_EXECPATH`, falling back to resolving `claude` through `PATH`, and
extracts printable strings from a window around the anchor
`You have been invoked in the following environment: `. That window yields cc's
field templates directly — `Primary working directory: `, `Is a git repository: `,
`OS Version: `, `You are powered by the model named `, `Assistant knowledge cutoff
is `, and the rest. It diffs them against a checked-in JSON manifest recording
the cc version and the literal set — JSON because the literals carry
significant trailing spaces — prints the difference, and exits non-zero.

Reading the installed binary rather than the decompiled dump is what makes the
check track upgrades on its own: the dump is regenerated by hand, the binary
changes underfoot.

`env-context` performs the same comparison and appends one line to the env block
when it differs, naming the script. The result is cached at
`~/.claude/env-context-drift.json`, keyed on the binary's path, size, and
mtime, plus a hash of the manifest's content — not the manifest's own mtime,
because one global cache serves every worktree, and an mtime key would
thrash on every alternation between checkouts even when their manifests are
byte-identical copies of each other — so a full scan runs once per cc
upgrade or manifest re-pin rather than once per session. Deleting that file
forces a fresh scan on the next session; nothing else needs to happen, since
a missing, truncated, or corrupt cache file is treated as a miss and
overwritten rather than raised. A warm `compare()` run — the read, the
window-literal extraction, and all three `required_literals` whole-binary
count passes — measured 0.36-0.37 s across six repeated runs against the
hook's 30 s timeout; the cache exists for the cold case. ("Timeout budget"
below cites 0.75 s for the same call measured cold, page-cache evicted, and
padded for the worst case — the two numbers are not in tension, they are
different conditions.) See "Timeout budget" below for how that 30 s was
arrived at and what else draws on it.

The check covers literals only. A change to how cc computes a value without
changing its label — the shell-resolution order, say — will not trip it. The
manifest therefore records the cc version alongside the literals, so a version
bump is itself reviewable.

### Re-pinning after a cc upgrade

When `check-env-context.sh` reports drift, review
`src/claude_config/env_context/render.py` against whatever cc changed before
doing anything else: the check only reports that a label changed or
disappeared, not whether the redesigned block still needs that field, or
under what literal — that judgment is `render.py`'s to make, not the
script's. Once render.py has been reconciled (or found not to need
changing), `check-env-context.sh --update` re-derives both literal lists
from the installed binary and rewrites `docs/env-context-manifest.json` to
match (`drift.repin()`). It refuses outright to write a `required_literals`
count of zero: reaching zero from a positive count is exactly the rename or
removal the check exists to catch, and `compare()`'s count-changed check
fires only on a change *from* the pinned count — a literal re-pinned at 0
could never fail it again, making that entry a permanently-passing
assertion instead of a live one. A field that has genuinely vanished from
cc needs a decision in `render.py` about whether and how to keep watching
it, not a silent re-pin at 0.

## Timeout budget

Three numbers, set together, none of them independently meaningful:

| Setting | Value | Location |
| --- | --- | --- |
| `SessionStart` hook timeout | 30 s | `settings.json` |
| `environment._git`'s per-call timeout | 2 s (called twice per run: `is_git_repo`, `worktree_common_dir`) | `src/claude_config/env_context/environment.py` |
| `drift.installed_version`'s subprocess timeout | 10 s | `src/claude_config/env_context/drift.py` |

The outer number has to be bigger than the two inner ones can add up to, with
margin — cc SIGTERMs then SIGKILLs the hook's process group at the outer
timeout, and on that path it returns before parsing stdout at all
(`y0m`, `src/globals/21.js:9240` in the decompiled 2.1.235 dump), discarding
the whole block rather than whatever had already been written. A hook that
times out costs the session its env block and its scratchpad path, silently:
`hook_cancelled` maps to `[]` for the model, and the terminal banner that
would say a hook timed out is gated to `UserPromptSubmit` only
(`globals/23.js:21023`).

The three numbers above replaced an inherited, inconsistent set: a 5 s outer
timeout left over from a much smaller hook (one `git rev-parse`, five printed
lines), a 5 s `_git` timeout that let two sequential git calls alone consume
the entire outer budget, and a 2 s `installed_version` timeout reasoned
against that 5 s outer number in its own docstring. Measured against the old
numbers: a hung `git` on PATH made the hook take 10.115 s to finish
naturally — twice the old 5 s outer budget, so cc would have killed it
mid-block. Separately, with the installed binary's page cache evicted,
`claude --version` measured 3.365 s, over the old 2 s cap on that call alone
— meaning the drift check failed on the first session after every Claude
Code upgrade, exactly the moment it exists to catch.

Worst case under the new numbers, every capped call spending its full
budget rather than actually finishing:

```
2 s + 2 s   two _git() calls, each timing out rather than returning  4 s
10 s        installed_version()'s subprocess timing out              10 s
~2 s        drift.compare(): a from-disk read of the 331 MB binary
            plus the required_literals count passes, generously
            padded from a measured cold (page-cache-evicted) 0.75 s   2 s
<1 s        everything else: platform/shell/os_version, scratchpad
            mkdir, cache stat, JSON parsing — none of it capped, all
            of it measured in the single-digit milliseconds           1 s
                                                                     ------
                                                                     ~17 s
```

roughly 17 s against a 30 s outer timeout — comfortably inside it rather than
matching it, so a genuinely wedged call still gets cut off by its own,
smaller timeout before cc's outer one would ever need to fire. `compare()`'s
read has no timeout of its own (it is a plain `Path.read_bytes()`), which is
why its contribution above is a measured, padded estimate rather than a cap;
everything else in the sum is a hard ceiling.

If any one of these three numbers changes, re-check this arithmetic — that is
the whole reason it is written out here rather than left implicit in each
value's own docstring. `settings.json` cannot carry a comment (it is parsed
as plain JSON), so this section is the one place a future change to any of
the three is checked against the other two; `environment.py`'s and
`drift.py`'s docstrings point back here rather than duplicating the sum.

## Files

| File | Change |
| --- | --- |
| `src/claude_config/env_context/environment.py` | Machine facts: shell resolution mirroring the Bash tool (not cc's own `$SHELL`), git/worktree detection, platform name, OS version |
| `src/claude_config/env_context/scratchpad.py` | The per-session scratchpad path, mirroring cc's own `claude-<uid>/<project-slug>/<session-id>/scratchpad` layout, and its creation at mode `0o700` |
| `src/claude_config/env_context/render.py` | Assembles the `# Environment` and `# Scratchpad Directory` sections from a `Facts` TypedDict |
| `src/claude_config/env_context/drift.py` | Extracts cc's env-block literals from the installed binary, compares them against the pinned manifest, caches the result, and re-pins it (`repin`) |
| `src/claude_config/env_context/__main__.py` | Reads the `SessionStart` payload from stdin, orchestrates the above, emits the `hookSpecificOutput` JSON envelope |
| `settings.json` | `SessionStart` command becomes bare `agent-tools env-context` |
| `scripts/claude.sh` | Export `CLAUDE_CODE_TMPDIR` |
| `scripts/check-env-context.sh` | New |
| `scripts/prune-scratch.sh` | New |
| `docs/env-context-manifest.json` | New: pinned cc version and literal set |
| `notes/env-context-manifest.md` | New: byte-offset forensics behind the manifest's two literal lists |
| `tests/test_env_context.py` | New |
| `tests/test_claude_sh.py` | New |
| `tests/test_prune_scratch.py` | New |
| `tests/test_check_env_context_sh.py` | New |
| `CLAUDE.md` | Update the `env-context` and `claude.sh` entries and the `scripts/` table |

## Tests

141 tests across four files under `tests/`.

`tests/test_env_context.py` (119 tests) covers the whole `env_context`
package:

- Rendering from a synthetic `Facts` dict: the interactive payload (with
  `model`) versus the print-mode payload (without), each bullet's presence
  and exact wording, and two full-text snapshot tests (plain and worktree).
- Shell resolution across a synthetic filesystem: `CLAUDE_CODE_SHELL`
  honoured, `$SHELL` honoured when it names bash or zsh, zsh preferred when
  `$SHELL` names neither, the documented directory order, and the raise when
  nothing resolves.
- Git and worktree detection: true/false against a real repo, a plain
  checkout, a missing cwd, a file cwd, and git absent from PATH; a linked
  worktree resolves the shared dir, a plain one returns nothing.
- Scratchpad path construction and creation: the cc-matching layout, mode
  `0o700`, idempotence, a symlinked tmp root, a symlinked `claude-<uid>`
  directory, the 200-character slug limit, and `session_id` rejected when
  empty, `.`/`..`, or carrying a path separator.
- Drift detection: literal extraction and its length/anchor guards,
  `compare()` against a matching manifest and against every kind of mutated
  one (new field, removed field, a count drop, a version-only mismatch),
  `installed_version()` raising on a nonzero exit, empty output, or a
  timeout, `find_binary()` across `CLAUDE_CODE_EXECPATH`, a wrapped Nix
  `claude`, and every failure branch, and the cache: hits and misses on
  mtime, size, and manifest content, self-healing from a corrupt,
  wrong-shaped, non-UTF-8, or unreadable cache file, and a failed write
  leaving no temp file behind.
- Hook orchestration (`__main__.py`): the envelope shape, the model line
  omitted in print mode, scratchpad creation, a malformed payload exiting
  loudly and naming the contract, an empty cwd/session_id degrading quietly
  instead, the scratchpad suppressed entirely in a background session, and
  `drift_note()`/`scratchpad_or_none()` surfacing their own failures — as a
  block note or stderr — rather than raising.

`tests/test_claude_sh.py` (1 test) runs `scripts/claude.sh` for real against
a stub `claude`, confirming `IS_SANDBOX`, `CLAUDE_CODE_DISABLE_AGENT_VIEW`,
and `CLAUDE_CODE_TMPDIR` all reach the exec'd process, and that a missing
MITM listener degrades to a stderr warning rather than a broken proxy env.

`tests/test_prune_scratch.py` (19 tests) covers `scripts/prune-scratch.sh`
against synthetic trees named only through `CLAUDE_CODE_TMPDIR`: a
`--session` value that looks like a glob is rejected rather than matched, an
ambiguous id across two projects refuses, a symlinked session or project
directory is refused while a symlinked root itself is still scanned, bulk
`--apply` deletes only empty scratchpads (and the parent session directory
once it is the only child left), a session with no scratchpad is reported
but not bulk-deleted, an `rmdir` refusal is skipped rather than fatal, and a
bad top-level argument or a bad `--session` id each exit 2.

`tests/test_check_env_context_sh.py` (2 tests) runs
`scripts/check-env-context.sh` for real against a stub `uv`, confirming
the script pins `UV_PROJECT_ENVIRONMENT` to the out-of-tree venv
`install.sh` provisions and leaves no `.venv` inside the checkout.
Unpinned, `uv run` builds one there and the script still exits 0, so
nothing but this test reports the loss.

`scripts/check-env-context.sh` and `scripts/prune-scratch.sh` are run by
hand, like `scripts/check-prompt-coupling.sh`: `check-env-context.sh` needs
an installed cc, and pruning scratch is a deliberate, one-off action by
design (see the script's own header). Neither script is itself wired into
`.github/workflows/skills-test.yml`, which runs a different, unrelated
`tests/` tree under `skills/scripts/` — the 141 tests above run locally
only, via `uv run --project . pytest -q`.

`scripts/check-env-context.sh` is a local check like
`scripts/check-prompt-coupling.sh`; it needs an installed cc and so does not run
in GitHub CI.

## Risks

The redirect only takes effect for sessions started after the change, since it is
set by the launcher. Sessions already running keep `/tmp/claude-0`.

Persistence changes the failure mode of accumulation. `/tmp` is container overlay
and is discarded on rebuild; `/root` is a host bind mount
(`/dev/mapper/data-root[/home/alan/personal/docker_home]`) and is not. Scratch
that used to evaporate now survives, which is the point, but it makes
`prune-scratch.sh` the only thing standing between the tree and unbounded growth.
Both paths sit on the same 929 GB device, so this is a persistence change and not
a capacity change.

Reimplementing cc's shell resolution adds a divergence surface the literal-based
drift check cannot see, which is why the manifest pins the cc version too.

Nothing migrates. Whatever the old sessions left under `/tmp/claude-0` stays until the
container is rebuilt.

## Out of scope

Background sessions (`CLAUDE_CODE_SESSION_KIND=bg`) receive a
`# Background Session` block naming `$CLAUDE_JOB_DIR/tmp` instead of a scratchpad
(`SdE()`, `src/globals/21.js:13595`), and they drop `--system-prompt-file` entirely
(`docs/background-sessions.md`), so they run cc's own prompt and want nothing this
hook adds.

That is not the same as needing nothing *from* it. `SessionStart` hooks are
configured in `settings.json` and fire whichever prompt the session runs, so the
hook must actively suppress its own scratchpad section for such a session or it
contributes a second, conflicting temp-directory instruction. The gate lives in
`scratchpad_or_none()` and is described under Scratchpad above.

The other sections `--system-prompt-file` discards — output style, language,
memory, focus mode — are either hand-written into
`sys_prompt/alan-default-next.md` already or inactive in this configuration.
