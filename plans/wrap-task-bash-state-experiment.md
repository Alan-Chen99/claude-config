# wrap-task vs Claude Code native bash — experiment notes

> **No version is stated in this file.** It was committed 2026-05-18 (`d493cc2`),
> citing `/repos/claude-code-decompiled/bundle/cli.js`. That repo's own history
> shows `bundle/cli.js` existed only from 2026-05-17 until the 2026-08-22
> re-extraction to 2.1.235, extracting 2.1.143 the whole time — so this was most
> likely measured against **2.1.143**, inferred here, not stated by the file
> itself. The decompiled repo has since been re-extracted twice and dropped
> `bundle/` entirely; see its README, "Re-resolving an old citation," for the
> current equivalent.

## What we ran

1. **Baseline (wrap-task active)** — captured bash state inside a normal
   Bash tool call:
   ```bash
   echo "$-"; echo "$0"; set -o; shopt; env | grep -iE 'agent_tools|claude'
   ```

2. **Disabled the hook at project level** — wrote
   `/root/claude-config-work/.claude/settings.local.json` containing
   `{"disableAllHooks": true}` (gitignored via new `/.claude/settings.local.json`
   line in `.gitignore`), then reloaded via `/hooks`.

3. **Post-reload capture** — same diagnostic, plus a `ps` to capture CC's
   actual `bash -c …` argv.

Sources checked alongside the empirical capture:
- `agent-tools/src/wrap_task.rs:24` — `Command::new("bash").arg(command_sh_path).spawn()`
- `agent-tools/src/hook_pre.rs` — rewrites `Bash`/`Monitor` to
  `exec agent-tools wrap-task <task_dir>`
- `/repos/claude-code-decompiled/bundle/cli.js` — `buildExecCommand` and
  `getSpawnArgs` for CC's native pipeline
- `/root/.claude/shell-snapshots/snapshot-bash-*.sh` — what CC sources

## What we got

CC's native bash invocation (captured from `ps -o args` after disabling hook):

```
/bin/bash -c "source /root/.claude/shell-snapshots/snapshot-bash-<id>.sh 2>/dev/null || true \
           && shopt -u extglob 2>/dev/null || true \
           && eval '<user cmd>' < /dev/null \
           && pwd -P >| /tmp/claude-<id>-cwd"
```

`-l` is included only when the snapshot fails to source (skipped in the
typical case).

Observable diff inside a wrapped command vs CC native:

| state                 | wrap-task          | CC native            |
| --------------------- | ------------------ | -------------------- |
| `$-`                  | `hB`               | `hmtBc`              |
| `$0` / `BASH_ARGV0`   | path to command.sh | `bash`               |
| `monitor` (job ctrl)  | off                | on                   |
| `onecmd`              | off                | on                   |
| `expand_aliases`      | off                | on                   |
| `vterm_*` functions   | absent             | defined              |
| `extglob`             | off                | off (explicit unset) |
| `errexit` / `pipefail`| off / off          | off / off            |
| post-`cd` cwd capture | none               | written to cwdfile   |
| `AGENT_TOOLS_TASK_ID` | set                | unset                |

The snapshot is what sets `monitor`, `onecmd`, `expand_aliases`, and defines
the `vterm_*` functions; wrap-task does not source it. CC's pipeline also
wraps the user command in `eval … < /dev/null` (heredoc guard) and captures
`pwd -P` to a per-command file that CC reads on return — neither happens
under wrap-task, so `cd` inside a wrapped command does not update CC's
tracked cwd.

## Implications

- Don't rely on `c`/`m`/`t` flags in `$-`, on `$0` being `bash`, on aliases,
  on snapshot-defined functions, or on CC tracking `cd` changes inside a
  wrap-task'd command.
- The override recipe (`{"disableAllHooks": true}` in
  `.claude/settings.local.json` + `/hooks` reload) works and is the right
  way to A/B test wrap-task changes against CC native.
- Closing the gap in wrap-task would mean at minimum: invoking
  `bash -c "source <snapshot> && eval <cmd> && pwd -P >| <file>"` instead of
  `bash <command.sh>`. Would close `$-`/`$0`/monitor/onecmd/aliases/cwd; would
  leave the design choice of "command.sh on disk for durable capture" needing
  rework (the current value of having the original bytes on disk would have
  to come from somewhere else, e.g. recording argv pre-eval).
