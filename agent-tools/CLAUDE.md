# agent-tools

Rust binary wrapping skill / Python tool invocations and Claude Code lifecycle hooks. Subcommand surface and root resolution are documented in the repo-root `CLAUDE.md`; this file covers internals that aren't obvious from the source.

## Prompt-coupled strings

These strings are emitted by `agent-tools` and quoted verbatim in the system prompt (`sys_prompt/alan-default-next.md`). The system prompt teaches the agent to recognize them. Any drift between the emitter and the prompt silently breaks recognition without breaking any test — the agent simply stops finding the section it's looking for.

| Emitter                                                                                          | Prompt quote location                                  | Notes                                                                                              |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `hook_post.rs::LATE_CAPTURES_HEADER_PREFIX` = `"Late captures from prior backgrounded call "`    | `sys_prompt/alan-default-next.md`, "Bash Output Recovery (agent-tools run)" section | Edit both sides together. The CI grep test `scripts/check-prompt-coupling.sh` fails if they drift. |
| `hook_post.rs` line `"[agent-tools] captures from this Bash call: …"`                            | Same section, opening paragraph                        | Same rule.                                                                                         |
| `hook_post.rs::bg_notice` → `"BACKGROUNDED: Command was backgrounded. Cause: …"`                 | Same section, "If you see a `BACKGROUNDED:` marker …" | The agent triggers late-capture awareness off the substring `BACKGROUNDED:`.                       |

## Late-capture surfacing

`hook_post.rs` fires after Bash, Monitor, **and** Read tool calls. On every fire it does two things under a per-scope flock:

1. **Seed**: records the current Bash/Monitor call's child PIDs into `<scope>/.hook-post-surfaced.json` so they will not be re-emitted as "late captures" by a later hook firing.
2. **Scan**: walks every other `tool_use_id` subdirectory in the scope (those whose own `events.jsonl` exists). For each `child_started` entry not yet in the ledger AND whose matching `child_exit` has landed (OR whose `child_started` timestamp is older than 5 minutes — the `[unfinalized]` fallback for SIGKILL / host-shutdown paths), emit a line:

   ```
   Late captures from prior backgrounded call <toolu_id>: <desc> → /path/<pid>/{stdout,stderr}; …
   ```

   and add those PIDs to the ledger.

Lock target is a sibling `.hook-post-surfaced.lock` sentinel file, not the JSON itself — keeps the rename-based atomic write straightforward and avoids stale-fd issues across rename.

### Scope isolation

Scope is `~/.claude/agent-tools/<session_id>/[<agent_id>/]`. The ledger and lock live in that scope. A subagent's hook scans only its own scope; the main thread's hook scans only the main-thread scope. The discriminator is "does this directory contain `events.jsonl` directly?" — wrap-parent dirs have one, subagent-id dirs do not.

### Why Read is in the matcher

The most common recovery path after a backgrounded multi-stage wrap is `<task-notification>` → `Read .output`. Without `Read` in the matcher, that path would never trigger the catch-up scan. Adding Read costs <5ms per Read call (one filesystem stat for `events.jsonl` per prior toolu_id in scope) and gives the agent visibility into late captures without requiring an unrelated Bash call.

## Testing from a worktree

Per repo-root `CLAUDE.md`: **worktrees must NEVER run `install.sh`**. Build in place, then point at the worktree via env var or CLI flag:

```bash
cd agent-tools && cargo build --release

# (a) env var (persistent across multiple calls in the same shell):
CLAUDE_CONFIG_ROOT=/path/to/worktree ./target/release/agent-tools skill <module> [args...]

# (b) --root flag (per-invocation, takes precedence over the env var):
./target/release/agent-tools --root /path/to/worktree skill <module> [args...]
```

Place `--root` before the subcommand to avoid ambiguity with subcommand args (subcommands capture trailing args verbatim, so `--root` placed after a subcommand's first positional arg is forwarded to the skill instead of being parsed as the global flag). The flag is a no-op for subcommands that don't resolve the repo root (`run`, `hook-pre`, `hook-post`, `ps`).

For testing hook behavior end-to-end in a worktree, copy the built binary onto a test path and invoke it directly with synthetic hook input on stdin:

```bash
echo '{"session_id":"…","tool_name":"Bash",…}' | ./target/release/agent-tools hook-post
```

The unit tests in `tests/hook_post_test.rs` cover the full hook lifecycle (current-call captures, BACKGROUNDED notice, late-capture surfacing, ledger dedup, in-flight skipping, `[unfinalized]` fallback, subagent isolation, and the parallel-hook race).
