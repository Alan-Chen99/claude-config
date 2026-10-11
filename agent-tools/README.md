# agent-tools

What spans files here, or concerns a task rather than a file; each file's own design is in its comments. The status-line grammar agents are taught is `docs/agent-tools-status-reference.md`.

## Launching an uninstalled checkout

`agent-tools claude` runs this checkout's `scripts/claude.sh` against `CLAUDE_CONFIG_DIR=<root>/.claude/worktree-config/`, so hooks, settings, system prompt and output style all come from one checkout.

- `.credentials.json` is linked: once its `expiresAt` passes and refresh fails, the child dies on its first request with `OAuth session expired and could not be refreshed`, and nothing earlier says so. Claude Code strips `CLAUDE_CODE_OAUTH_TOKEN` from tool subprocesses, so source the runners' token first: `set -a && . /workspace/.env && set +a`.
- Transcripts land under `<root>/.claude/worktree-config/projects/`, out of a normal session's `/resume`.
- A hook can be driven by hand: `echo '{"session_id":"…","tool_name":"Bash",…}' | CLAUDE_CONFIG_ROOT=<root> ./target/release/agent-tools hook-post`.

## Status channel

`status::derive` is the one place a capture directory becomes a status. Renderers choose only what to show, and by different predicates:

| Renderer | Reaches `derive` via | Selects live by |
| --- | --- | --- |
| push report (`hook_post::report_changes`) | `status::derive` | `StatusKey::is_still_running`, so `exited` gets a full line |
| `ps --format text` | `status::derive` | `Status::is_terminal` |
| `ps --format json` | `psrecord::Record::build` | `Record::terminal` |
| statusline | `psrecord::Record::build` | `Record::terminal`, plus a marker per key |

`exited` is where they part: its process is finished and its wrapper is not. A new renderer must say which axis it means and what an `exited` child looks like under it, and pass free text through `meta::escape_control`; no compiler asks for either.

- Only a delivery point (`hook-post`, `hook-prompt`) commits the ledger, and only after its report is written and flushed. `ps` never commits, in any format: it cannot know its output reached the agent, and a commit retires a change the push report still owes.
- The ledger's lock is `.reported.lock`, not the JSON, because the commit renames a temp file over the JSON and would strand a lock held on the old one.
- A `TaskStop` success is not evidence about a wrapped child: a `--background` run leaves the call's process tree on purpose and outlives the stop (the status reference, "The kill boundary"). Where the two disagree, the status line is right; nothing here compensates, as polling would delay every delivery point.

## The merge rule

`core::decide_merge` carries it. Admit a new destination only for a measured caller: a tty or `/dev/null` would be a guess, as character devices are not uniformly unseekable, and a socket, though sound, has no caller yet.
