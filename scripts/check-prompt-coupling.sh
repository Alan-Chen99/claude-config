#!/usr/bin/env bash
# Fail when a string emitted by agent-tools drifts from the system prompt that
# teaches the agent to recognize it. Both sides must be edited together.
#
# Prompt-side needles are the human-readable strings the agent is taught to
# recognize. Source-side needles are the exact literal at each emit site, not a
# bare prefix: the same words also appear in the file's fallback branches, doc
# comments, and test names, so a bare prefix still matches a file whose emitter
# has drifted.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
prompt="$root/sys_prompt/alan-default-next.md"
src="$root/agent-tools/src"
status_source="0"

check() {
  local needle="$1" where="$2"
  if ! grep -qF -- "$needle" "$where"; then
    echo "MISSING in $where: $needle" >&2
    status_source=1
  fi
}

# The status report header. Emitted on both delivery channels: tool results
# (hook-post) and user turns (hook-prompt).
check '[agent-tools] run status:' "$prompt"
check '"[agent-tools] run status:\n{}"' "$src/hook_post.rs"
check '"[agent-tools] run status:\n{}"' "$src/hook_prompt.rs"

# The degraded-report fallback carries the same header prefix, so the agent
# recognizes a failed report as status rather than as command output.
check '"[agent-tools] run status: unavailable' "$src/hook_post.rs"
check '"[agent-tools] run status: unavailable' "$src/hook_prompt.rs"

# The backgrounding notice. The prompt keys off the prefix alone.
check 'BACKGROUNDED:' "$prompt"
check '"BACKGROUNDED: Command was backgrounded.' "$src/hook_post.rs"

# Status keys. The prompt lists the key names; `status.rs`'s Display impl emits
# them, and that literal is the only occurrence in the file that actually
# reaches the agent. Renaming a binding inside one of these literals is a false
# failure — the fix is a one-word edit to the needle below.
while IFS='|' read -r in_prompt in_source; do
  [ -n "$in_prompt" ] || continue
  check "$in_prompt" "$prompt"
  check "$in_source" "$src/status.rs"
done <<'KEYS'
producing|write!(f, "producing")
quiet(|write!(f, "quiet({b})")
exited(|write!(f, "exited({c})")
final(|write!(f, "final({c})")
abandoned|write!(f, "abandoned")
spawn-failed(|write!(f, "spawn-failed({e})")
KEYS

# The wrapper's own diagnostics. The prompt promises every one begins
# `agent-tools:`, which is how the agent tells them from its command's output.
# The prompt-side needle carries the prefix, not just the promise, or a reworded
# prefix would pass. One needle per emit site: a bare-prefix grep over
# `capture.rs` matches as long as any one of the five still carries it, so four
# could drift unseen. Five, because the open, the write loop and the flush each
# need their own message. The `failed (` needle runs on to `forwarding continues`
# so it cannot also match the flush's line and leave that site unpinned. Each
# needle is a fragment of one physical line — these format strings are
# line-continued and `grep -qF` does not span lines.
check 'always prefixed `agent-tools:`' "$prompt"
check '"agent-tools: {stream_name} downstream closed ({err}); still capturing to' "$src/capture.rs"
check '"agent-tools: {stream_name} drain bound of {drain_cap_bytes} bytes' "$src/capture.rs"
check '"agent-tools: capture to {} could not be opened (' "$src/capture.rs"
check '"agent-tools: capture to {} failed ({e}); forwarding continues' "$src/capture.rs"
check '"agent-tools: capture to {} failed at the flush (' "$src/capture.rs"

# The notes segment and the stat-failure group, both built by `status.rs::render`.
# The prompt names all five so the agent reads a bracket after the byte counts as
# facts about the run rather than as a second status key; rename one and that
# bracket is unexplained on a line the agent must still read. Source-side needles
# are whole `format!` / `push` expressions because the bare words also appear in
# this file's own render assertions, so a word-level grep passes over a drifted
# emitter. Each needle was verified to match exactly one place in `status.rs`.
while IFS='|' read -r in_prompt in_source; do
  [ -n "$in_prompt" ] || continue
  check "$in_prompt" "$prompt"
  check "$in_source" "$src/status.rs"
done <<'NOTES'
streams split: <why>|format!("streams split: {}", meta::escape_control(why))
downstream closed|notes.push("downstream closed".to_string())
drain capped|notes.push("drain capped".to_string())
capture failed: <err>|format!("capture failed: {}", meta::escape_control(e))
stat failed: <err>|format!(" [stat failed: {}]", s.stat_errors.join("; "))
NOTES

if [ "$status_source" -ne 0 ]; then
  echo "prompt coupling check FAILED" >&2
  exit 1
fi
echo "prompt coupling OK"
