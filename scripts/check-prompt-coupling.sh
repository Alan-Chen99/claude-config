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

# A needle is registered here and grepped at the bottom, after the coverage
# assertion in between has run. A prompt-facing literal with no needle behind it
# is then reported on its own terms, instead of being read as whichever
# individual needle happens to fail beside it.
needle=()
target=()
check() {
  needle+=("$1")
  target+=("$2")
}

# The status report header. `report_header` in hook_post.rs is the one place
# that builds it; hook_post's own success arm and hook_prompt.rs both call it,
# so the two delivery channels (tool results and user turns) emit the same
# text. The hook_prompt.rs check has no header literal to look for there —
# none exists — so it looks for the call instead, catching a hook_prompt.rs
# that grew its own inline header rather than calling the shared constructor.
check '[agent-tools] run status @ ' "$prompt"
check '"[agent-tools] run status @ {}:"' "$src/hook_post.rs"
check 'hook_post::report_header(' "$src/hook_prompt.rs"

# The degraded-report fallback keeps the bare header, without the stamp: it
# carries no relative figure for a stamp to anchor. The agent reads it as status
# via the "lines beginning [agent-tools]" rule, not via the stamped header's shape.
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

# The `<detail>` field, also built by `render`. Five shapes, not four: a
# settled duration, a live running total, a settled child with no reap to
# time, a spawn that never produced a pid (`spawn-failed`, but still
# `started`), and — only when the record itself did not read — no start at
# all and `pid -` (`abandoned`). The fourth and fifth both render `pid -`;
# what tells them apart is that `timing`'s arms and the `pid` fallback are
# independent of each other, so the shape is the crossing of the two, not the
# arm alone — the mistake that once had this prompt calling `spawn-failed` a
# `pid <pid>` line. `render`'s final `format!` supplies the skeleton every
# shape shares; each `timing` arm supplies the span text, and the two `pid`
# checks below pin the field the fallback reads and the fallback itself,
# since a needle on either alone would let the other drift. Each source
# needle here was verified to match exactly one place in `status.rs`.
check 'started <t>, ran <d>' "$prompt"
check '"started {}, ran {}"' "$src/status.rs"
check 'started <t> (+<d>)' "$prompt"
check '"started {} (+{})"' "$src/status.rs"
check 'started <t>, <age>, <bytes>' "$prompt"
check 'pid -, started <t>' "$prompt"
check '"started {}"' "$src/status.rs"
check 'pid -, <age>, <bytes>' "$prompt"
check '<name> [<key>] <detail> -> <paths>' "$prompt"
check '"{name} [{key}] pid {pid}, {timing}{age}, {bytes}{notes}{problems} -> {paths}"' "$src/status.rs"
check 'unwrap_or_else(|| "-".into())' "$src/status.rs"
check '.and_then(|m| m.child_pid)' "$src/status.rs"

# The collapsed running-children line. `producing`/`quiet(<bucket>)` children
# do not reach the standard per-child line above; `collapse_running` in
# hook_post.rs groups them into this one instead. The prompt must say so, or
# an agent reads a `still running: [...]` line as a malformed single-child one
# rather than the deliberate group it is.
check 'still running: [<key>] <name>, <name>; [<key>] <name>  -> agent-tools ps' "$prompt"
check '"  still running: {body}  -> agent-tools ps"' "$src/hook_post.rs"

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
check '"agent-tools: {stream_name} {what} bound of {size} bytes reached' "$src/capture.rs"
check '"agent-tools: capture to {} could not be opened (' "$src/capture.rs"
check '"agent-tools: capture to {} failed ({e}); forwarding continues' "$src/capture.rs"
check '"agent-tools: capture to {} failed at the flush (' "$src/capture.rs"

# The bound's size. The prompt names 256 MiB because "bounded" alone leaves an
# agent unable to predict which of two behaviours a runaway producer gets —
# `pipefail` reporting the producer's status, or the `141` the bound forces. One
# number serves both bounds, the post-close drain and a backgrounded run's
# capture, and the prompt quotes it under each; it is a constant in `core.rs`,
# and nothing else would notice it moving.
check '256 MiB bound' "$prompt"
check 'DEFAULT_DRAIN_CAP_BYTES: u64 = 256 * 1024 * 1024;' "$src/core.rs"

# Bare `agent-tools ps`'s output shape: JSON by default, live captures only.
# An agent deciding whether it needs `--all` reads this sentence, so it must
# match the flag's actual default rather than the shape the default replaced.
check 'bare `agent-tools ps` reports what is running now, as JSON' "$prompt"
check 'default_value_t = ps::PsFormat::Json' "$src/main.rs"

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
capture capped|notes.push("capture capped".to_string())
capture failed: <err>|format!("capture failed: {}", meta::escape_control(e))
stat failed: <err>|format!(" [stat failed: {}]", s.stat_errors.join("; "))
NOTES

# The `--background` start line: the whole of what a backgrounded run tells its
# caller, being the capture directory and the two pids on one line. It carries no
# `[agent-tools]` prefix, because it is the command's own stdout rather than the
# status channel, so the prompt shows its shape instead — which is the only thing
# separating it from the child's first line of output. Drift makes that shape a
# lie and the capture directory unfindable. The needle is the whole format
# literal: the bare words also occur in `run.rs`'s own comments and in the test
# asserting the line, so a word-level grep passes over a drifted emitter.
check '<capture_dir>  wrapper pid <n>  child pid <n>' "$prompt"
check '"{}  wrapper pid {wrapper_pid}  child pid {pid}"' "$src/run.rs"

# Coverage, for the literal nobody pinned.
#
# The list above is what someone remembered to pin. What it cannot see is a new
# prompt-facing literal shipped with its prompt sentence and no needle: the gate
# stays green while the prompt goes false, which is the failure this script exists
# to prevent arriving by the one route a needle list cannot see. So every literal
# in `hook_post.rs` and `status.rs` whose text the prompt quotes carries a
# `// PROMPT-COUPLED` marker on the line above it, and the counts must agree.
#
# The marker means the prompt quotes this text rather than standing a placeholder
# in for it: `started {}, ran {}` is quoted and marked, while `last byte {}s ago`
# only fills the prompt's `<age>` slot and is not. The marker is the author's
# declaration and this script cannot tell that an unmarked literal should have
# been marked; what it enforces is that a declared coupling is pinned, and what
# prompts the declaration is the marker standing beside every neighbour.
#
# Only these two files: they are the ones whose text reaches the agent through
# `additionalContext`, where a string is read rather than shown. Needles aimed at
# any other file are outside the count, so `hook_prompt.rs` sharing the
# `unavailable` needle does not have to carry a marker for it.
coverage() {
  local file="$1" markers registered=0 t
  markers=$(grep -c '^[[:space:]]*// PROMPT-COUPLED$' "$src/$file" || true)
  for t in "${target[@]}"; do
    if [ "$t" = "$src/$file" ]; then
      registered=$((registered + 1))
    fi
  done
  if [ "$markers" -ne "$registered" ]; then
    echo "COVERAGE $file: $markers // PROMPT-COUPLED marker(s), $registered needle(s)" >&2
    echo "  a marked literal needs a check line for it; a check line needs its marker" >&2
    status_source=1
  fi
}
coverage hook_post.rs
coverage status.rs

# The registered needles, grepped last.
for i in "${!needle[@]}"; do
  if ! grep -qF -- "${needle[$i]}" "${target[$i]}"; then
    echo "MISSING in ${target[$i]}: ${needle[$i]}" >&2
    status_source=1
  fi
done

if [ "$status_source" -ne 0 ]; then
  echo "prompt coupling check FAILED" >&2
  exit 1
fi
echo "prompt coupling OK"
