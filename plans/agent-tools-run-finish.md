# agent-tools run — finish prompt + post-hook delivery

Companion to `plans/agent-tools-run-spec.md`. The Rust code in
`agent-tools/src/` is mostly implemented. Two coordinated changes remain
before the feature delivers any user-visible value:

1. `sys_prompt/alan-default-next.md` never mentions `agent-tools run`, so
   the agent has no instruction to insert it into pipelines where upstream
   stdout would be discarded.
2. `agent-tools/src/hook_post.rs` only emits PostToolUse
   `additionalContext` when a command was involuntarily backgrounded. On
   normal Bash/Monitor completion it returns silently, so the agent never
   learns the absolute path where wrap-task captured stdout/stderr.

Both legs must land together: the prompt rule is useless without the hook
delivering paths, and the hook output is undiscoverable without the prompt
rule.

---

## Design decisions

| # | Decision | Options considered | Chosen | Reason |
|---|----------|--------------------|--------|--------|
| 1 | How does the agent learn about `agent-tools run`? | (A) always-emit hook + system-prompt decision rule; (B) reactive heuristic hook only, no prompt change | A | B's heuristic silently misses chained-with-semicolons (`make; tail`), bash-function-wrapped truncators, and tool-result-truncation cases — violates the Loud Failure rule at `alan-default-next.md:64`. A restores all four invariant pairs from the prompt-patch analysis. |
| 2 | `additionalContext` layout | multi-line `\n`; single-line `;`-separated | single-line `;` | Existing hook output (`hook_post.rs:56-64`) has no precedent for `\n` in this field; rendering of newlines in `additionalContext` is unverified in the codebase. Single-line matches existing style and removes the rendering question. |
| 3 | Where in `alan-default-next.md` does the rule go? | new top-level section; subsection of `# Using your tools` co-located with `## Bash Tool Timeout Behavior` | co-located, immediately after Bash Tool Timeout Behavior | Same shape (non-obvious Bash failure mode + concrete decision rule). Visually paired so the agent reads both together. |
| 4 | Decision rule shape | wrap last stage; drop the truncator entirely; wrap upstream stage | wrap upstream stage | wrap-task already captures the last stage. Dropping the truncator forces full output into the visible result, which Claude Code may itself truncate. Wrap-upstream is the only fix that preserves both compact visible result and full disk capture. End-to-end probe (`echo "hi $(date +%s)" \| agent-tools run --desc probe -- cat \| head -1`) verified: outer captures head's output, child captures cat's output. |
| 5 | Idempotency for Monitor streaming PostToolUse | no marker; marker file in task dir; stat capture file size > 0 before emit | marker file `.paths_emitted` | First-call wins is the simplest correct behavior. Stat-based deferral adds disk read per call; marker is at most one `fs::write` per task. If Claude Code fires PostToolUse only once per Monitor instance, marker is a no-op. |
| 6 | "(if any)" wording vs. dynamic omission of the children-paths clause | always-emit with "(if any)"; `fs::read_dir(children/)` and omit when empty | "(if any)" with explicit `list children/` instruction | Cheaper (no read_dir per Bash call) and unambiguous. Implementer can revisit if children-line noise becomes a real problem. |
| 7 | Include a `REDUNDANT` anti-example? | decision text only; decision text + anti-example showing top-level `agent-tools run` wrap | both | Anti-example pre-empts the medium-severity over-application regression (agent wrapping every stage "to be safe"). Cost: 2 prompt lines. |
| 8 | Ship both changes together vs. independently? | prompt rule first; hook change first; coordinated | coordinated single landing | A prompt rule citing a path the hook never prints, or a hook printing a path the agent has no instruction to use, is dead weight on its own. The invariant is restored only when both legs land. |
| 9 | Hook emits paths block for trivial commands (`ls`, `pwd`)? | yes (always); no (heuristic gating) | yes (always) | Heuristic gating reintroduces the silent-miss class Decision #1 rejected. Accepted token cost: ~250 bytes per call (~60 tokens). |
| 10 | What `agent-tools run` argument is the wrapped segment? | child (segment immediately after `--`); parent (stdin source) | child | Verified by `run.rs:25-31` + `capture.rs:18-60`: `agent-tools run` spawns its argv as a child, captures the child's stdout/stderr via tee, and forwards transparently to the next pipe stage. Documented this in the prompt subsection. |

---

## Change 1 — `sys_prompt/alan-default-next.md`

Insert a new `## Bash Output Recovery (agent-tools wrap)` subsection
between the current end of `## Bash Tool Timeout Behavior` (line 182, last
bullet: "if a 3-second test hasn't finished in 120s, it is stuck, not
slow.") and the next heading `# Communication` (line 184). Preserve the
one-blank-line separator above and below to match existing style.

Exact text to insert:

```
## Bash Output Recovery (agent-tools wrap)

Every Bash and Monitor call is wrapped by `agent-tools wrap-task` via the
PreToolUse hook. The outer command's full stdout and stderr are captured
to disk regardless of what you see in the tool result. The PostToolUse
hook appends the absolute capture paths to the tool result; Read those
paths when you need the untruncated output. The wrapping is automatic —
never invoke `agent-tools wrap-task` directly.

Pipeline capture: the bash command's stdout IS the LAST stage's stdout,
so wrap-task automatically captures the last stage with no action from
you. Each upstream stage's output is consumed by the next stage and is
invisible to wrap-task. If you write `<expensive-producer> |
<truncating-filter>` (filters: `tail`, `head`, `grep`, `jq .field`, `wc`,
`sed -n`), the producer's full output is gone — only the filter's result
reaches wrap-task. To preserve an upstream stage's output, wrap THAT
stage (not the last stage) with `agent-tools run`.

Decision:

- Top-level Bash, or pipeline where the last stage's output is what you want — wrap-task already captures it. Do NOT wrap the top-level command with `agent-tools run`; double-wrapping creates a redundant child capture.
- Pipeline where an UPSTREAM stage's output is what you want preserved — wrap that stage with `agent-tools run --desc <short label> --`. `run` tees the wrapped stage's stdout/stderr to disk and forwards them transparently to the next pipe stage. Wrap each upstream stage independently if you want multiple intermediate captures.
- Wrap only upstream stages whose output you actually expect to read later. Speculative wrapping just creates child-capture dirs that nobody will look at. When in doubt, leave it un-wrapped — wrap-task will still capture the last stage.

"Upstream stage worth wrapping" = slow (compile, test suite), costly
(paid API call), side-effecting (apt, gdb, network mutation), or a
structured intermediate that a later stage consumes (find output before
xargs, jq output before sort).

Examples:

    # WRONG — wc -l's counts are consumed by tail and lost
    find . -name '*.py' | xargs wc -l | tail -3

    # RIGHT — wc -l captured before tail truncates them
    find . -name '*.py' | agent-tools run --desc wc -- xargs wc -l | tail -3

    # Multiple upstream captures
    find . | agent-tools run --desc found -- xargs wc -l | agent-tools run --desc counts -- sort -n | tail -3

    # Shell features (redirection, glob expansion) — wrap with bash -c
    agent-tools run --desc build -- bash -c 'make 2>&1' | tail -20

    # REDUNDANT — wrap-task already captures top-level commands; do NOT double-wrap
    agent-tools run --desc pytest -- pytest tests/

To recover lost output, Read the `stdout` / `stderr` path listed in the
PostToolUse additionalContext. Do not re-run the producer.
```

---

## Change 2 — `agent-tools/src/hook_post.rs`

Replace the body of `pub fn run()` (lines 8–74) with the version below.

Behavioral diff vs. current:

- Removed the early-return on missing `backgroundTaskId` (current lines 25–27).
- `task_dir` resolution lifted out of the bg branch — runs for every Bash/Monitor call.
- New `.paths_emitted` marker in `task_dir` suppresses repeat emission for streaming Monitor tools.
- New single-line `paths_block` is the always-on `additionalContext`.
- BACKGROUNDED supplement is appended to `paths_block` (with a leading space) instead of containing the old `"Captured output paths in: {task_dir}"` fragment — path list no longer duplicated.
- Existing `events::append("backgrounded", ...)` preserved unchanged.
- `input.agent_id.as_deref()` MUST be passed to `paths::task_dir_for` in the lifted call so subagent task dirs continue to namespace correctly under `~/.claude/agent-tools/<session>/<subagent session>/<taskid>/` (per `plans/agent-tools-run-spec.md:30`).

```rust
pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    let input = match hook_input::parse_post(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-post: parse error: {e:#}");
            return Ok(());
        }
    };

    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        return Ok(());
    }

    let task_dir = paths::task_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;

    // Idempotency for tools (e.g. Monitor) that may fire PostToolUse
    // repeatedly against the same tool_use_id.
    let marker = task_dir.join(".paths_emitted");
    if marker.exists() {
        return Ok(());
    }
    let _ = std::fs::write(&marker, b"");

    let paths_block = format!(
        "[agent-tools] captured: task_dir={td}; stdout={td}/stdout; stderr={td}/stderr; agent-tools run child captures (if any) live under {td}/children/ — one subdir per `agent-tools run` invocation, named by pid, each containing stdout and stderr. Read these paths for the full untruncated output.",
        td = task_dir.display(),
    );

    let bg_task_id = input.tool_response.get("backgroundTaskId").and_then(|v| v.as_str());
    let additional_context = if let Some(bg_task_id) = bg_task_id {
        let auto = input.tool_response.get("assistantAutoBackgrounded").and_then(|v| v.as_bool()).unwrap_or(false);
        let user = input.tool_response.get("backgroundedByUser").and_then(|v| v.as_bool()).unwrap_or(false);
        let (cause_label, cause_for_context) = if auto {
            ("assistant_auto", "assistant-mode auto-background (KAIROS)".to_string())
        } else if user {
            ("user", "user manually backgrounded (Ctrl+B)".to_string())
        } else {
            let limit = input.tool_input.timeout.unwrap_or(120_000);
            ("timeout", format!("timeout ({limit}ms limit hit)"))
        };
        let _ = events::append(
            &task_dir,
            "backgrounded",
            serde_json::json!({
                "cause": cause_label,
                "background_task_id": bg_task_id,
                "timeout_ms": input.tool_input.timeout
            }),
        );
        format!(
            "{paths_block} BACKGROUNDED: Command was involuntarily backgrounded. Cause: {cause}. Process is still running (task_id: {tid}). To kill it: use TaskStop tool with task_id {tid}.",
            paths_block = paths_block,
            cause = cause_for_context,
            tid = bg_task_id,
        )
    } else {
        paths_block
    };

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional_context
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}
```

---

## Change 3 — `agent-tools/tests/hook_post_test.rs`

Add cases covering the always-emit behavior:

1. Bash, no `backgroundTaskId`, exit 0 → `additionalContext` present; substring `[agent-tools] captured:`, `stdout=`, `stderr=`.
2. Bash with `backgroundTaskId` → `additionalContext` contains both `[agent-tools] captured:` AND `BACKGROUNDED:` AND `TaskStop`.
3. Second `hook_post::run()` against the same `task_dir` (marker pre-created) → no `additionalContext` emitted (stdout empty).
4. Non-Bash, non-Monitor tool (e.g. `Read`) → no output.
5. Subagent input (`agent_id` set) → emitted `task_dir` path contains the subagent-id segment.

Update any pre-existing test that asserted the old `"Captured output paths in: {task_dir}"` fragment.

---

## Mandatory verification before commit

The `agent-tools run` semantics described in the prompt were verified
end-to-end against the existing binary in this session:

```
$ echo "hi $(date +%s)" | agent-tools run --desc probe -- cat | head -1
hi 1779065998

# Outer wrap-task capture (LAST stage = head -1):
$ cat <task_dir>/stdout
hi 1779065998

# agent-tools run child capture (UPSTREAM stage = cat):
$ cat <task_dir>/children/<pid>/stdout
hi 1779065998
```

After applying the changes and rebuilding, re-run inside a Claude Code
session to confirm the new hook output:

```
cd /root/claude-config-work/agent-tools && cargo build --release
# inside a fresh Claude Code session:
echo "hi $(date +%s)" | agent-tools run --desc probe -- cat | head -1
```

Verify:

1. Visible tool result contains `hi <timestamp>`.
2. PostToolUse `additionalContext` contains `[agent-tools] captured: task_dir=...`.
3. Read the listed `<task_dir>/stdout` → `hi <timestamp>\n` (head -1's output).
4. List `<task_dir>/children/` → one subdir; Read its `stdout` → `hi <timestamp>\n` (cat's output, proves upstream capture).

If any step diverges, fix the prompt text or hook code to match observed
behavior before committing.

---

## Environment requirements

- `agent-tools` binary at `~/.local/bin/agent-tools` (canonical install via `install.sh`; do NOT run `install.sh` from a worktree — would re-point the symlink at the worktree's build and break other sessions).
- PreToolUse + PostToolUse hooks for `Bash|Monitor` already wired in `settings.json:70-91`. No `settings.json` change.
- Writable `~/.claude/agent-tools/`.
- `cargo` to rebuild after `hook_post.rs` changes.

---

## Known tradeoffs

- Every Bash/Monitor PostToolUse adds ~250 bytes of additionalContext (~60 tokens). 100-call sessions pay ~6k tokens of hook chrome. Accepted; the alternative (heuristic emit) silently misses pipeline shapes the user cares about, which violates the Loud Failure rule at `alan-default-next.md:64`.
- The "agent-tools run child captures (if any)" clause is always present even when no `agent-tools run` was invoked. "(if any)" makes this clear in text; a follow-up can stat `children/` and omit the clause when empty.
- `.paths_emitted` is best-effort idempotency. If the marker write fails (read-only fs, missing parent), Monitor may emit the block multiple times — preferred to silently missing emission.
- Monitor-on-slow-producer: paths block may surface before the capture file has bytes. Agent should re-Read if an initial read returns empty. If this becomes a real workflow, defer the marker until the capture file is non-empty (`fs::metadata(stdout_path).map(|m| m.len() > 0)`).

---

## Testing suggestion

Run the verification probe above. For unit confidence, the 5
`hook_post_test.rs` cases cover always-emit, marker idempotency,
BACKGROUNDED supplement, and subagent namespacing.
