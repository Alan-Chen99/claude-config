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

if [ "$status_source" -ne 0 ]; then
  echo "prompt coupling check FAILED" >&2
  exit 1
fi
echo "prompt coupling OK"
