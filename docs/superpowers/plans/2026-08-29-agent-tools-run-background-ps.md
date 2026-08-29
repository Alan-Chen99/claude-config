# `agent-tools run --background`, `ps` as data, and the user's channels — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `docs/superpowers/specs/2026-08-29-agent-tools-run-background-ps-design.md` — a `--background` flag whose start is synchronous and whose failure is loud, a `ps` that emits data about what is running, timestamps that resolve after a compaction, reports that collapse what is merely running, a scope for the `!` shell shortcut, and a statusline that shows open tasks.

**Architecture:** One status derivation feeds three renderers. `status.rs` gains duration and note accessors; a new `psrecord.rs` turns a capture directory into a serializable record; `ps.rs`, `hook_post.rs` and a new statusline renderer all read from that instead of computing their own. `--background` forks *before* the tokio runtime starts (a runtime cannot survive `fork`), the parent blocks on a readiness pipe until the child has published `meta.json` and spawned, and the detached child then runs the existing `run_core` with its forward target set to a sink.

**Tech Stack:** Rust 2021, `clap` 4 derive, `tokio` (multi-thread), `serde`/`serde_json`, `chrono` (with `serde`), `nix` 0.29 (`process`, `fs`, `signal`), `anyhow`. Tests are `cargo test` — unit tests inline under `#[cfg(test)]`, integration tests in `agent-tools/tests/` driving the built binary via `env!("CARGO_BIN_EXE_agent-tools")`.

**Build and test from a worktree — never run `install.sh`:**

```bash
cd agent-tools && cargo build --release
CLAUDE_CONFIG_ROOT=<worktree-root> ./target/release/agent-tools <subcommand>
```

Integration tests set `CLAUDE_CONFIG_ROOT` themselves (see `agent_tools()` in `tests/ps_test.rs`). Run the suite with `cd agent-tools && cargo test`.

---

## File Structure

| File | Responsibility | Create/Modify |
| --- | --- | --- |
| `agent-tools/src/status.rs` | Status derivation; adds `is_terminal`, `duration_s`, `notes`, local-time and duration formatting | Modify |
| `agent-tools/src/psrecord.rs` | The serializable per-child record and envelope every renderer reads | **Create** |
| `agent-tools/src/ps.rs` | Collect captures, build records, dispatch to the json/text/statusline renderers | Modify |
| `agent-tools/src/statusline.rs` | The one-line renderer | **Create** |
| `agent-tools/src/hook_post.rs` | Report header stamp; terminal-in-full and running-collapsed | Modify |
| `agent-tools/src/hook_prompt.rs` | Report header stamp | Modify |
| `agent-tools/src/meta.rs` | `claude_pid` field | Modify |
| `agent-tools/src/paths.rs` | Scope resolution with the `user-shell` fallback | Modify |
| `agent-tools/src/core.rs` | `Destination` parameter: forward to the caller, or to a sink | Modify |
| `agent-tools/src/background.rs` | `fork`/`setsid`/readiness pipe — the only `unsafe` in the change | **Create** |
| `agent-tools/src/run.rs` | Phase split for `--background` | Modify |
| `agent-tools/src/main.rs` | `--background` on `Run`; `--format`/`--all`/`--events` on `Ps`; module declarations | Modify |
| `agent-tools/tests/background_test.rs` | End-to-end `--background` behaviour | **Create** |
| `agent-tools/tests/ps_test.rs` | JSON envelope, live-only, formats, ledger untouched | Modify |
| `agent-tools/tests/hook_post_test.rs` | Header stamp, collapsing | Modify |
| `statusline.sh` | Wire the open-tasks line in | Modify |
| `sys_prompt/alan-default-next.md` | Correct the false `setsid` claim; teach `--background` | Modify |
| `agent-tools/CLAUDE.md`, `CLAUDE.md` | Document the new surface | Modify |

Tasks 1–4 change what every reader shows. Tasks 5–9 build the pull path and the statusline on top. Tasks 10–13 add `--background`. Task 14 is documentation. Each task ends green and committed.

---

### Task 1: A duration that stops at the reap

The current line renders `last byte Ns ago` and nothing else about time. A terminal child needs a duration that stopped when it was reaped, or a `final(0)` from an hour ago reads as a 67-minute job.

**Files:**
- Modify: `agent-tools/src/status.rs`

- [ ] **Step 1: Write the failing tests**

Add to the `mod tests` block at the bottom of `agent-tools/src/status.rs`:

```rust
    #[test]
    fn a_live_child_measures_to_now() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        let now = Utc::now();
        m.started_at = now - Duration::seconds(191);
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let st = derive(dir.path(), now);
        assert!(!st.is_terminal(), "a live wrapper with no reap is not terminal");
        let d = st.duration_s(now).expect("a started child has a duration");
        assert!((d - 191.0).abs() < 1.0, "duration was {d}");
    }

    #[test]
    fn a_terminal_child_measures_to_its_reap_not_to_now() {
        let dir = TempDir::new().unwrap();
        let mut m = dead();
        let started = Utc::now() - Duration::seconds(4020);
        m.started_at = started;
        m.reaped = Some(crate::meta::Reaped {
            at: started + Duration::seconds(242),
            status: 1,
        });
        m.drained_at = Some(started + Duration::seconds(242));
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let now = Utc::now();
        let st = derive(dir.path(), now);
        assert!(st.is_terminal(), "a drained, reaped, dead wrapper is terminal");
        let d = st.duration_s(now).expect("a reaped child has a duration");
        assert!(
            (d - 242.0).abs() < 1.0,
            "the clock must stop at the reap, got {d}"
        );
    }

    #[test]
    fn a_child_with_no_meta_has_no_duration() {
        let dir = TempDir::new().unwrap();
        let st = derive(dir.path(), Utc::now());
        assert_eq!(st.key, StatusKey::Abandoned);
        assert_eq!(st.duration_s(Utc::now()), None);
    }

    #[test]
    fn every_key_is_classified_as_terminal_or_not() {
        assert!(StatusKey::Final(0).is_terminal());
        assert!(StatusKey::Abandoned.is_terminal());
        assert!(StatusKey::SpawnFailed("x".into()).is_terminal());
        assert!(!StatusKey::Producing.is_terminal());
        assert!(!StatusKey::Quiet("30s").is_terminal());
        assert!(!StatusKey::Exited(0).is_terminal());
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-tools && cargo test --bin agent-tools status:: 2>&1 | tail -20`
Expected: FAIL — `no method named 'is_terminal'`, `no method named 'duration_s'`.

- [ ] **Step 3: Implement**

In `agent-tools/src/status.rs`, add to `impl fmt::Display for StatusKey`'s neighbourhood — a new `impl` block directly after the `Display` impl:

```rust
impl StatusKey {
    /// Terminal keys end watching: the child's fate is settled and cannot change.
    /// The set is the 2026-08-26 spec's, not a second definition — `ps` selects
    /// live children by the negation of this, and the report ranks by it.
    pub fn is_terminal(&self) -> bool {
        match self {
            StatusKey::SpawnFailed(_) | StatusKey::Final(_) | StatusKey::Abandoned => true,
            StatusKey::Producing | StatusKey::Quiet(_) | StatusKey::Exited(_) => false,
        }
    }
}
```

Then add an `impl Status` block directly after the `pub struct Status { ... }` definition:

```rust
impl Status {
    pub fn is_terminal(&self) -> bool {
        self.key.is_terminal()
    }

    /// How long the child has run: to `now` while it is live, to the reap once it
    /// is terminal. A settled child's clock has stopped, and a duration that kept
    /// growing after it would describe waiting, not running.
    ///
    /// `None` when there is no `meta.json` to hold a start time. A child whose
    /// record is unreadable still has a status; it has no measurable duration.
    pub fn duration_s(&self, now: DateTime<Utc>) -> Option<f64> {
        let m = self.meta.as_ref()?;
        let end = match (self.is_terminal(), m.reaped) {
            (true, Some(r)) => r.at,
            // Terminal without a reap is `abandoned` or `spawn-failed`: nothing
            // observed an end, so the last defensible instant is now.
            _ => now,
        };
        Some(((end - m.started_at).num_milliseconds() as f64 / 1000.0).max(0.0))
    }
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-tools && cargo test --bin agent-tools status:: 2>&1 | tail -20`
Expected: PASS, all status tests green.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/status.rs
git commit -m "status: a terminal child's elapsed time kept growing after it stopped running"
```

---

### Task 2: Times render local, and a line carries start and duration

`status::render` formats UTC instants with no zone, so `started: 00:22:24.263` read against `date` is wrong by the offset with no way to see it.

**Files:**
- Modify: `agent-tools/src/status.rs`

- [ ] **Step 1: Write the failing tests**

Add to `mod tests` in `agent-tools/src/status.rs`:

```rust
    #[test]
    fn a_duration_reads_at_a_glance() {
        assert_eq!(fmt_duration(4.0), "4s");
        assert_eq!(fmt_duration(59.4), "59s");
        assert_eq!(fmt_duration(191.0), "3m11s");
        assert_eq!(fmt_duration(242.0), "4m02s");
        assert_eq!(fmt_duration(3720.0), "1h02m");
        assert_eq!(fmt_duration(0.0), "0s");
    }

    #[test]
    fn a_live_line_carries_its_start_and_how_long_so_far() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        let now = Utc::now();
        m.started_at = now - Duration::seconds(191);
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let st = derive(dir.path(), now);
        let line = render(dir.path(), &st, now);
        assert!(line.contains("started "), "line: {line}");
        assert!(line.contains("(+3m11s)"), "line: {line}");
        assert!(!line.contains("ran "), "a live child has not `ran`: {line}");
    }

    #[test]
    fn a_terminal_line_says_how_long_it_ran() {
        let dir = TempDir::new().unwrap();
        let mut m = dead();
        let started = Utc::now() - Duration::seconds(4020);
        m.started_at = started;
        m.reaped = Some(crate::meta::Reaped {
            at: started + Duration::seconds(242),
            status: 1,
        });
        m.drained_at = Some(started + Duration::seconds(242));
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let now = Utc::now();
        let line = render(dir.path(), &st_of(dir.path(), now), now);
        assert!(line.contains("ran 4m02s"), "line: {line}");
        assert!(!line.contains("(+"), "a terminal child has no running total: {line}");
    }

    /// The start time must be the local rendering of the stored instant, not the
    /// UTC one wearing local clothes.
    #[test]
    fn a_rendered_start_is_local_time() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        let started = Utc::now() - Duration::seconds(30);
        m.started_at = started;
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let now = Utc::now();
        let line = render(dir.path(), &st_of(dir.path(), now), now);
        let expected = started.with_timezone(&chrono::Local).format("%H:%M:%S").to_string();
        assert!(
            line.contains(&format!("started {expected}")),
            "line {line} did not carry the local start {expected}"
        );
    }

    fn st_of(dir: &std::path::Path, now: DateTime<Utc>) -> Status {
        derive(dir, now)
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-tools && cargo test --bin agent-tools status:: 2>&1 | tail -20`
Expected: FAIL — `cannot find function 'fmt_duration'`.

- [ ] **Step 3: Implement**

In `agent-tools/src/status.rs`, add near `cap_to`:

```rust
/// A duration a reader takes in without arithmetic. Seconds below a minute,
/// minutes and zero-padded seconds below an hour, hours and zero-padded minutes
/// above. Never a bare float: `191.7s` makes a reader do the division that this
/// is here to have already done.
pub fn fmt_duration(secs: f64) -> String {
    let s = secs.max(0.0).round() as i64;
    if s < 60 {
        format!("{s}s")
    } else if s < 3600 {
        format!("{}m{:02}s", s / 60, s % 60)
    } else {
        format!("{}h{:02}m", s / 3600, (s % 3600) / 60)
    }
}

/// The local rendering of an instant. Every displayed time goes through here:
/// the previous renderer formatted UTC instants with no zone, so a reader
/// correlating one against `date` was wrong by the offset and could not see it.
pub fn fmt_local_hms(t: DateTime<Utc>) -> String {
    t.with_timezone(&chrono::Local).format("%H:%M:%S").to_string()
}

/// The stamp a pushed report carries in its header. Local, with the offset,
/// because a report line outlives the terminal it was printed to and is re-read
/// after a compaction, when nothing else on the line says when "4s ago" was.
pub fn fmt_local_stamp(t: DateTime<Utc>) -> String {
    t.with_timezone(&chrono::Local)
        .format("%H:%M:%S %z")
        .to_string()
}
```

Then in `render`, replace the `let age = ...` block and the final `format!` with:

```rust
    let age = match s.last_byte_at {
        Some(t) if s.capture.bytes() > 0 => {
            format!("last byte {}s ago", (now - t).num_seconds().max(0))
        }
        _ => "no output".to_string(),
    };
    // Start and duration, in the two shapes the spec fixes: a live child is
    // still accumulating and says so with `+`; a terminal one reports the total
    // it finished with. Absent when there is no meta to read a start from.
    let timing = match (s.meta.as_ref(), s.duration_s(now)) {
        (Some(m), Some(d)) if s.is_terminal() => {
            format!("started {}, ran {}, ", fmt_local_hms(m.started_at), fmt_duration(d))
        }
        (Some(m), Some(d)) => {
            format!("started {} (+{}), ", fmt_local_hms(m.started_at), fmt_duration(d))
        }
        // A terminal child with no reap — `abandoned` or `spawn-failed`. The
        // start is known; the end was never observed, and a duration here would
        // assert one. The start alone is what there is.
        (Some(m), None) => format!("started {}, ", fmt_local_hms(m.started_at)),
        // No meta to read a start from.
        (None, _) => String::new(),
    };
```

Add a test for that third arm, since `Status::duration_s` returns `None` for a terminal status with no reap (established in Task 1) and a line must not silently lose the start time it does know:

```rust
    #[test]
    fn an_abandoned_line_still_says_when_it_started() {
        let dir = TempDir::new().unwrap();
        let mut m = dead();
        let started = Utc::now() - Duration::seconds(4020);
        m.started_at = started;
        m.reaped = None;
        m.drained_at = None;
        write(&dir, &m);
        let now = Utc::now();
        let st = derive(dir.path(), now);
        assert_eq!(st.key, StatusKey::Abandoned);
        let line = render(dir.path(), &st, now);
        let expected = started.with_timezone(&chrono::Local).format("%H:%M:%S").to_string();
        assert!(line.contains(&format!("started {expected}")), "line: {line}");
        assert!(!line.contains("ran "), "nothing observed an end: {line}");
        assert!(!line.contains("(+"), "a settled child is not accumulating: {line}");
    }
```

and the return expression:

```rust
    format!("{name} [{key}] pid {pid}, {timing}{age}, {bytes}{notes}{problems} -> {paths}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-tools && cargo test --bin agent-tools status:: 2>&1 | tail -20`
Expected: PASS.

Then run the full suite, because integration tests assert on line shape:
Run: `cd agent-tools && cargo test 2>&1 | tail -30`
Expected: some `ps_test`/`hook_post_test` assertions may fail on the changed line. Update those assertions to match the new format — do not weaken them to substring-of-anything checks; they should still assert position and content.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/status.rs agent-tools/tests/
git commit -m "status: rendered times were UTC instants that read as local, and a line said nothing about when"
```

---

### Task 3: A report says when it was made

**Files:**
- Modify: `agent-tools/src/hook_post.rs`, `agent-tools/src/hook_prompt.rs`
- Test: `agent-tools/tests/hook_post_test.rs`

- [ ] **Step 1: Write the failing test**

Add to `agent-tools/tests/hook_post_test.rs`:

```rust
#[test]
fn a_report_header_carries_the_clock_it_was_made_at() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(home.path(), "sid-hdr", None, "toolu_hdr", 4242, Some("build"), Some(0), "x");
    let out = run_hook_post(home.path(), "sid-hdr", None);
    let ctx = out["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    let first = ctx.lines().next().unwrap();
    assert!(
        first.starts_with("[agent-tools] run status @ "),
        "header must carry a stamp, got: {first}"
    );
    assert!(first.ends_with(':'), "header ends with a colon, got: {first}");
    // A stamp with an offset, so the line still resolves after a compaction.
    let stamp = first
        .trim_start_matches("[agent-tools] run status @ ")
        .trim_end_matches(':');
    assert!(
        chrono::NaiveTime::parse_from_str(&stamp[..8], "%H:%M:%S").is_ok(),
        "stamp did not start with HH:MM:SS: {stamp}"
    );
    let offset = &stamp[9..];
    assert!(
        offset.len() == 5
            && (offset.starts_with('+') || offset.starts_with('-'))
            && offset[1..].chars().all(|c| c.is_ascii_digit()),
        "stamp {stamp} carried {offset} where a signed four-digit offset belongs"
    );
}
```

Reuse the file's existing `seed_capture` and `run_hook_post` helpers; if `run_hook_post` does not already exist with that signature, use whatever the file's existing helper is named and adapt the call — do not add a second helper.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd agent-tools && cargo test --test hook_post_test a_report_header 2>&1 | tail -20`
Expected: FAIL — the header is `[agent-tools] run status:` with no stamp.

- [ ] **Step 3: Implement**

In `agent-tools/src/hook_post.rs`, replace the two `format!("[agent-tools] run status:\n{}", ...)` occurrences with a shared constructor. Add near the top of the file:

```rust
/// The one place a report header is built. Both delivery points use it, so the
/// prompt's quoted form matches what either emits rather than one of them.
pub(crate) fn report_header(now: chrono::DateTime<chrono::Utc>) -> String {
    format!(
        "[agent-tools] run status @ {}:",
        crate::status::fmt_local_stamp(now)
    )
}
```

In `run()`, replace the success arm's push with:

```rust
        Ok(report) if !report.lines.is_empty() => {
            parts.push(format!(
                "{}\n{}",
                report_header(chrono::Utc::now()),
                report.lines.join("\n")
            ));
            delivered = Some(report);
        }
```

In `agent-tools/src/hook_prompt.rs`, replace the corresponding line with:

```rust
        Ok(report) => {
            let ctx = format!(
                "{}\n{}",
                crate::hook_post::report_header(chrono::Utc::now()),
                report.lines.join("\n")
            );
            delivered = Some(report);
            ctx
        }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-tools && cargo test --test hook_post_test --test hook_prompt_test 2>&1 | tail -20`
Expected: PASS. Update any existing assertion that matched the old header verbatim.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/hook_post.rs agent-tools/src/hook_prompt.rs agent-tools/tests/
git commit -m "report: a line saying \"4s ago\" resolved to nothing once the turn it landed in was compacted"
```

---

### Task 4: Terminal changes in full, running ones collapsed

A fan-out of twenty wrapped commands costs twenty near-identical lines twice over.

**Files:**
- Modify: `agent-tools/src/hook_post.rs`
- Test: `agent-tools/tests/hook_post_test.rs`

- [ ] **Step 1: Write the failing tests**

Add to `agent-tools/tests/hook_post_test.rs`:

```rust
#[test]
fn running_children_collapse_to_one_line_that_still_names_each_of_them() {
    let home = tempfile::TempDir::new().unwrap();
    // Live children: a real wrapper pid with no reap derives to producing.
    for (i, name) in ["alpha", "beta", "gamma"].iter().enumerate() {
        seed_live_capture(home.path(), "sid-coll", "toolu_coll", 9000 + i as u32, name);
    }
    seed_capture(home.path(), "sid-coll", None, "toolu_coll", 9500, Some("done"), Some(1), "x");

    let out = run_hook_post(home.path(), "sid-coll", None);
    let ctx = out["hookSpecificOutput"]["additionalContext"].as_str().unwrap();

    // The terminal child keeps its own full line.
    assert!(
        ctx.lines().any(|l| l.contains("done [final(1)]") && l.contains("-> ")),
        "a terminal change keeps full detail:\n{ctx}"
    );
    // The three running ones share one line, and every one of them is named.
    let collapsed: Vec<&str> = ctx.lines().filter(|l| l.contains("still running:")).collect();
    assert_eq!(collapsed.len(), 1, "running children collapse to one line:\n{ctx}");
    let line = collapsed[0];
    assert!(line.contains("[producing]"), "key names the group: {line}");
    for name in ["alpha", "beta", "gamma"] {
        assert!(line.contains(name), "{name} was not named: {line}");
    }
    assert!(line.contains("agent-tools ps"), "the collapsed line points at ps: {line}");
}

#[test]
fn a_collapsed_child_is_recorded_as_told_and_does_not_repeat() {
    let home = tempfile::TempDir::new().unwrap();
    seed_live_capture(home.path(), "sid-once", "toolu_once", 9600, "alpha");
    let first = run_hook_post(home.path(), "sid-once", None);
    assert!(first["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap()
        .contains("alpha"));
    // Named under its key, so the ledger may retire it. Nothing changed since.
    let second = run_hook_post(home.path(), "sid-once", None);
    assert!(
        second.get("hookSpecificOutput").is_none(),
        "an already-reported child must not repeat: {second}"
    );
}
```

Add this helper beside the file's existing `seed_capture`:

```rust
/// A capture whose wrapper is this test process — alive, with no reap — so it
/// derives to `producing` rather than to a terminal key.
fn seed_live_capture(home: &Path, session: &str, tuid: &str, child_pid: u32, desc: &str) -> PathBuf {
    let wrapper_pid = std::process::id();
    let dir = home
        .join(".claude/agent-tools")
        .join(session)
        .join(tuid)
        .join(format!("{wrapper_pid}{child_pid}"));
    std::fs::create_dir_all(&dir).unwrap();
    let ticks = std::fs::read_to_string(format!("/proc/{wrapper_pid}/stat"))
        .ok()
        .and_then(|s| s.rsplit_once(')').map(|(_, rest)| rest.to_string()))
        .and_then(|rest| rest.split_whitespace().nth(19).map(|t| t.to_string()))
        .expect("field 22 of /proc/<pid>/stat is the start time in ticks");
    let meta = serde_json::json!({
        "wrapper_pid": wrapper_pid,
        "wrapper_started_ticks": ticks.parse::<u64>().unwrap(),
        "child_pid": child_pid,
        "desc": desc,
        "command": ["sleep", "9999"],
        "started_at": chrono::Utc::now().to_rfc3339(),
        "spawn_error": serde_json::Value::Null,
        "reaped": serde_json::Value::Null,
        "drained_at": serde_json::Value::Null,
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    std::fs::write(dir.join("output"), "").unwrap();
    dir
}
```

Note: the capture directory is named `{wrapper_pid}{child_pid}` so several live captures in one test share one live wrapper pid while still occupying distinct directories — the directory name only has to parse as `u32` and be unique.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-tools && cargo test --test hook_post_test collapse 2>&1 | tail -20`
Expected: FAIL — every running child still gets its own line, and no line contains `still running:`.

- [ ] **Step 3: Implement**

In `agent-tools/src/hook_post.rs`, `report_changes` currently pushes one `(id, key, line)` per changed child and passes the lot to `bound`. Change it to separate the two populations. Replace the block from `pending.sort_by(...)` through `let mut lines = bound(&mut ledger, pending);` with:

```rust
    // Terminal first when the budget forces a choice: "this finished" matters
    // more than "this is still running". Identity breaks ties, so the report is
    // reproducible rather than in whatever order `read_dir` yielded — which
    // would also make the dropped set arbitrary.
    pending.sort_by(|a, b| rank(&a.1).cmp(&rank(&b.1)).then_with(|| a.0.cmp(&b.0)));
    let (terminal, running): (Vec<_>, Vec<_>) =
        pending.into_iter().partition(|(_, key, _)| rank(key) == 0);
    let mut lines = bound(&mut ledger, terminal);
    if let Some(collapsed) = collapse_running(&mut ledger, running) {
        lines.push(collapsed);
    }
```

Add, next to `bound`:

```rust
/// One line for every child that is merely still running, grouping them by key
/// and naming each one under its own.
///
/// Naming is not decoration. Counts alone — "17 producing, 2 quiet" — would tell
/// the agent that two children are quiet without telling it which, and the ledger
/// could then not honestly retire them: a key would be recorded as reported when
/// the child holding it was never named. So a child is recorded only once its
/// name is in the line, and if the line will not fit, nothing is recorded and
/// every one of them stays pending for the next delivery point.
fn collapse_running(
    ledger: &mut crate::ledger::Ledger,
    running: Vec<(String, String, String)>,
) -> Option<String> {
    if running.is_empty() {
        return None;
    }
    // `running` arrives sorted by (rank, id); rank is equal across it, so the
    // groups below come out in a stable order without a second sort.
    let mut groups: std::collections::BTreeMap<String, Vec<(String, String)>> =
        std::collections::BTreeMap::new();
    for (id, key, line) in running {
        // The rendered line begins `  <name> [<key>] ...`; the name is what a
        // reader recognizes, and re-deriving it here would be a second place
        // that decides what a child is called.
        let name = line
            .trim_start()
            .split(" [")
            .next()
            .unwrap_or("?")
            .to_string();
        groups.entry(key).or_default().push((id, name));
    }
    let body = groups
        .iter()
        .map(|(key, members)| {
            let names: Vec<&str> = members.iter().map(|(_, n)| n.as_str()).collect();
            format!("[{}] {}", key, names.join(", "))
        })
        .collect::<Vec<_>>()
        .join("; ");
    let line = format!("  still running: {body}  -> agent-tools ps");
    if line.len() + 1 > REPORT_BUDGET {
        // Every name did not fit, so no child here was told. Reporting a count
        // instead would retire nothing and say nothing; staying silent leaves
        // them all pending, which is what the next delivery point is for.
        return None;
    }
    // Recorded only now, with the line built: a child is marked as told exactly
    // when its name is in the text that reaches the agent.
    for (key, members) in &groups {
        for (id, _) in members {
            ledger.record(id, key);
        }
    }
    Some(line)
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-tools && cargo test --test hook_post_test 2>&1 | tail -25`
Expected: PASS, including the pre-existing tests.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/hook_post.rs agent-tools/tests/hook_post_test.rs
git commit -m "report: a fan-out of twenty cost twenty near-identical lines, twice over"
```

---

### Task 5: The wrapper records which session started it

**Files:**
- Modify: `agent-tools/src/meta.rs`, `agent-tools/src/run.rs`, `agent-tools/src/status.rs`

- [ ] **Step 1: Write the failing test**

Add to `mod tests` in `agent-tools/src/status.rs`:

```rust
    #[test]
    fn orphanhood_is_unknown_when_nobody_recorded_a_session() {
        let dir = TempDir::new().unwrap();
        let m = base();
        assert_eq!(m.claude_pid, None);
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let st = derive(dir.path(), Utc::now());
        assert_eq!(
            st.orphaned(),
            None,
            "\"the session is gone\" and \"nobody looked\" are different answers"
        );
    }

    #[test]
    fn a_child_whose_session_is_gone_is_orphaned() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        // pid 0 has no /proc entry, so it can never be alive.
        m.claude_pid = Some(0);
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let st = derive(dir.path(), Utc::now());
        assert_eq!(st.orphaned(), Some(true));
    }

    #[test]
    fn a_child_whose_session_still_runs_is_not_orphaned() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        m.claude_pid = Some(std::process::id());
        crate::meta::write_meta(dir.path(), &m).unwrap();
        let st = derive(dir.path(), Utc::now());
        assert_eq!(st.orphaned(), Some(false));
    }
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools status::tests::orphan 2>&1 | tail -20`
Expected: FAIL — `no field 'claude_pid'`.

- [ ] **Step 3: Implement**

In `agent-tools/src/meta.rs`, add to `ChildMeta` after `capture_error`:

```rust
    /// The Claude Code process that started this child, when one said so.
    /// `None` means nobody recorded it, which is not the same as the session
    /// being gone — `status::orphaned` keeps those apart.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub claude_pid: Option<u32>,
```

Every struct literal of `ChildMeta` must gain `claude_pid`. There are three: `run.rs` (the pre-spawn record), `run.rs`'s test module, and `status.rs`'s `base()`. Set the first from the environment and the two test ones to `None`.

In `agent-tools/src/run.rs`, in the `ChildMeta { ... }` literal:

```rust
        claude_pid: std::env::var("CLAUDE_PID").ok().and_then(|s| s.parse().ok()),
```

In `agent-tools/src/status.rs`, add to `impl Status`:

```rust
    /// Whether the session that started this child is gone. `None` when no
    /// session was recorded: absence of an answer is not a negative one, and a
    /// `false` here would assert the session is alive on no evidence at all.
    pub fn orphaned(&self) -> Option<bool> {
        let pid = self.meta.as_ref()?.claude_pid?;
        // Liveness by pid alone, deliberately: unlike a wrapper, whose start
        // ticks this process recorded, nothing here observed the session
        // starting, so there are no ticks to compare and a recycled pid cannot
        // be ruled out. Reporting a recycled pid as "still running" errs toward
        // not calling a live child an orphan.
        Some(!std::path::Path::new(&format!("/proc/{pid}")).exists())
    }
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd agent-tools && cargo test 2>&1 | tail -20`
Expected: PASS across the suite.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/meta.rs agent-tools/src/run.rs agent-tools/src/status.rs
git commit -m "meta: a detached wrapper outlives its session and nothing recorded which session that was"
```

---

### Task 6: One record every renderer reads

**Files:**
- Create: `agent-tools/src/psrecord.rs`
- Modify: `agent-tools/src/main.rs` (module declaration), `agent-tools/src/status.rs` (expose `notes`)

- [ ] **Step 1: Write the failing test**

Create `agent-tools/src/psrecord.rs` containing only its test module for now:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, Utc};
    use tempfile::TempDir;

    fn seed(dir: &std::path::Path, reaped: Option<i32>) {
        let now = Utc::now();
        let meta = serde_json::json!({
            "wrapper_pid": 4709u32,
            "wrapper_started_ticks": 1u64,
            "child_pid": 4711u32,
            "desc": "build",
            "command": ["make", "-j8"],
            "started_at": (now - Duration::seconds(191)).to_rfc3339(),
            "spawn_error": serde_json::Value::Null,
            "reaped": reaped.map(|s| serde_json::json!({
                "at": (now - Duration::seconds(60)).to_rfc3339(), "status": s
            })),
            "drained_at": reaped.map(|_| (now - Duration::seconds(60)).to_rfc3339()),
        });
        std::fs::write(dir.join("meta.json"), serde_json::to_vec(&meta).unwrap()).unwrap();
        std::fs::write(dir.join("output"), "hello").unwrap();
    }

    #[test]
    fn a_record_carries_the_facts_a_renderer_needs() {
        let d = TempDir::new().unwrap();
        seed(d.path(), Some(0));
        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert_eq!(v["name"], "build");
        assert_eq!(v["origin"], "tool");
        assert_eq!(v["tool_use_id"], "toolu_x");
        assert_eq!(v["wrapper_pid"], 4709);
        assert_eq!(v["child_pid"], 4711);
        assert_eq!(v["bytes"], 5);
        assert!(v["capture"].as_str().unwrap().ends_with("/output"));
        assert!(v["started_at"].as_str().unwrap().contains('T'));
    }

    /// `seed` writes `wrapper_started_ticks: 1`, which cannot match a live
    /// process, so those fixtures always derive terminal. A live record needs a
    /// wrapper that really is alive: this one.
    #[test]
    fn a_live_record_carries_elapsed_and_no_ran() {
        let d = TempDir::new().unwrap();
        let pid = std::process::id();
        let ticks = crate::procstat::start_ticks(pid).unwrap();
        let meta = serde_json::json!({
            "wrapper_pid": pid,
            "wrapper_started_ticks": ticks,
            "child_pid": pid + 1,
            "desc": "build",
            "command": ["sleep", "9999"],
            "started_at": (Utc::now() - Duration::seconds(191)).to_rfc3339(),
            "spawn_error": serde_json::Value::Null,
            "reaped": serde_json::Value::Null,
            "drained_at": serde_json::Value::Null,
        });
        std::fs::write(d.path().join("meta.json"), serde_json::to_vec(&meta).unwrap()).unwrap();
        std::fs::write(d.path().join("output"), "hello").unwrap();

        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        assert!(!r.terminal, "a live wrapper with no reap is not terminal");
        let v = serde_json::to_value(&r).unwrap();
        assert!(v["elapsed_s"].as_f64().unwrap() > 190.0, "{v}");
        assert!(
            v.get("ran_s").is_none(),
            "a running child has not `ran` anything yet: {v}"
        );
    }

    #[test]
    fn a_user_shell_record_names_no_tool_use() {
        let d = TempDir::new().unwrap();
        seed(d.path(), Some(0));
        let r = Record::build(d.path(), None, USER_SHELL, Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert_eq!(v["origin"], "user-shell");
        assert!(v["tool_use_id"].is_null(), "a ! command has no tool use to name");
    }

    #[test]
    fn a_terminal_record_carries_ran_and_no_elapsed() {
        let d = TempDir::new().unwrap();
        seed(d.path(), Some(1));
        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert_eq!(v["key"], "final(1)");
        assert!(v.get("ran_s").is_some(), "a settled child reports what it ran: {v}");
        assert!(
            v.get("elapsed_s").is_none(),
            "a settled child's clock stopped; elapsed_s would keep growing: {v}"
        );
    }

    #[test]
    fn withheld_groups_spawn_failures_without_their_messages() {
        let mut w = Withheld::default();
        w.add("final(0)");
        w.add("final(0)");
        w.add("final(1)");
        w.add("spawn-failed(No such file or directory)");
        w.add("spawn-failed(Permission denied)");
        assert_eq!(w.by_key.get("final(0)"), Some(&2));
        assert_eq!(w.by_key.get("final(1)"), Some(&1));
        assert_eq!(
            w.by_key.get("spawn-failed"),
            Some(&2),
            "free-text messages must not each open a bucket: {:?}",
            w.by_key
        );
    }
}
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools psrecord 2>&1 | tail -20`
Expected: FAIL to compile — `psrecord` is not a module, `Record` and `Withheld` do not exist.

- [ ] **Step 3: Implement**

Add `mod psrecord;` to the module list near the top of `agent-tools/src/main.rs` (beside `mod ps;`).

Delete the `struct Capture` definition from `agent-tools/src/ps.rs` — the version below replaces it — and add `use crate::psrecord::Capture;` there. `collect_captures` and `collect_pid_captures` stay in `ps.rs`; only the type moves.

In `agent-tools/src/status.rs`, extract the note computation out of `render` into a reusable function, and have `render` call it. Add:

```rust
/// Everything that explains a difference from bare, as data. Empty on a clean
/// run, which is nearly every run: a note that is always there stops being read.
///
/// A split says something only when the caller's own two descriptors reached one
/// destination and the rule declined anyway. When they provably reached two,
/// bare kept them apart too and there is nothing to explain.
pub fn notes(s: &Status) -> Vec<String> {
    let mut notes: Vec<String> = Vec::new();
    if let (Capture::Split { .. }, Some(why)) =
        (&s.capture, s.meta.as_ref().and_then(|m| m.merge.as_deref()))
    {
        if why != core::DESTINATIONS_ALREADY_DIFFERED {
            notes.push(format!("streams split: {}", meta::escape_control(why)));
        }
    }
    if s.meta.as_ref().is_some_and(|m| m.forward_closed) {
        notes.push("downstream closed".to_string());
    }
    if s.meta.as_ref().is_some_and(|m| m.drain_capped) {
        notes.push("drain capped".to_string());
    }
    if let Some(e) = s.meta.as_ref().and_then(|m| m.capture_error.as_deref()) {
        notes.push(format!("capture failed: {}", meta::escape_control(e)));
    }
    notes
}
```

and in `render`, replace the inline note block with `let notes_v = notes(s);` followed by the existing empty/join formatting over `notes_v`.

Now write the body of `agent-tools/src/psrecord.rs`, above its test module:

```rust
use chrono::{DateTime, Utc};
use serde::Serialize;
use std::collections::BTreeMap;
use std::path::Path;

use crate::status::{self, Capture};

/// The directory name a capture gets when no hook set a scope. It is not a
/// tool-use id and never pretends to be one: `Record::origin` says so, and
/// `tool_use_id` is null.
pub const USER_SHELL: &str = "user-shell";

/// One child, as data. Every renderer reads this; none derives a status of its
/// own, or the guarantee that push and pull never describe one child
/// differently becomes a coincidence maintained by hand.
#[derive(Debug, Serialize)]
pub struct Record {
    pub name: String,
    pub key: String,
    /// `"tool"` or `"user-shell"`.
    pub origin: &'static str,
    pub agent: Option<String>,
    pub tool_use_id: Option<String>,
    pub wrapper_pid: u32,
    pub child_pid: Option<u32>,
    /// When the *wrapper* started, which is what `meta.json` records — it is
    /// stamped before the exec is attempted. For every key but `spawn-failed`
    /// that is within milliseconds of the child's own start. For
    /// `spawn-failed` there was no child, so this dates the attempt and
    /// nothing else; `child_pid` is `null` there, which is what says so.
    pub started_at: Option<DateTime<chrono::Local>>,
    /// Present only while the child is live.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub elapsed_s: Option<f64>,
    /// Present only once the child is terminal. Never both: the field present
    /// is itself the statement of which kind of record this is.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ran_s: Option<f64>,
    pub last_byte_at: Option<DateTime<chrono::Local>>,
    pub last_byte_s: Option<f64>,
    pub bytes: u64,
    pub capture: String,
    pub notes: Vec<String>,
    /// Whether the session that started this child is gone — a fact about the
    /// session, not about the child. Every record carries it, terminal ones
    /// included, so a child that finished normally hours ago reads
    /// `orphaned: true` once its session ends. That is correct and is not a
    /// leak. The leak is the pair: `Some(true)` on a child that is not terminal.
    /// `null` means the record cannot support the question.
    pub orphaned: Option<bool>,
    /// Not serialized: renderers select on it, readers read `key`.
    #[serde(skip)]
    pub terminal: bool,
}

impl Record {
    /// Derive one record from a capture directory. `group` is the third path
    /// component — a tool-use id, or `USER_SHELL`.
    pub fn build(dir: &Path, agent: Option<String>, group: &str, now: DateTime<Utc>) -> Record {
        let st = status::derive(dir, now);
        let key = st.key.to_string();
        let terminal = st.is_terminal();
        let duration = st.duration_s(now);
        // `status::name` (extracted in Task 4) is the one place that decides
        // what a child is called, cap included. Re-deriving the
        // meta -> display_name -> directory chain here would drop the 200-char
        // cap `render` applies, so the same status core would emit a capped name
        // on one surface and an uncapped one on the other.
        let name = status::name(dir, &st);
        let capture = match st.capture {
            Capture::Merged(_) => format!("{}/output", dir.display()),
            Capture::Split { .. } => format!("{}/{{stdout,stderr}}", dir.display()),
        };
        let user_shell = group == USER_SHELL;
        Record {
            name,
            key,
            origin: if user_shell { "user-shell" } else { "tool" },
            agent,
            tool_use_id: (!user_shell).then(|| group.to_string()),
            wrapper_pid: st.meta.as_ref().map(|m| m.wrapper_pid).unwrap_or(0),
            child_pid: st.meta.as_ref().and_then(|m| m.child_pid),
            started_at: st.meta.as_ref().map(|m| m.started_at.with_timezone(&chrono::Local)),
            elapsed_s: (!terminal).then_some(duration).flatten(),
            ran_s: terminal.then_some(duration).flatten(),
            last_byte_at: st.last_byte_at.map(|t| t.with_timezone(&chrono::Local)),
            last_byte_s: st
                .last_byte_at
                .map(|t| ((now - t).num_milliseconds() as f64 / 1000.0).max(0.0)),
            bytes: st.capture.bytes(),
            capture,
            notes: status::notes(&st),
            orphaned: st.orphaned(),
            terminal,
        }
    }
}

/// What `ps` did not show, and how to get it. A bare total hides the one thing a
/// reader most needs from a set of terminal children — that one of them is a
/// spawn failure.
#[derive(Debug, Default, Serialize)]
pub struct Withheld {
    pub by_key: BTreeMap<String, usize>,
    pub retrieve_with: &'static str,
}

impl Withheld {
    pub fn add(&mut self, key: &str) {
        // `final(0)` and `final(1)` are worth separating and there are few of
        // them. A spawn error is free text, so grouping on the whole key would
        // let one distinct bucket per child into a field whose purpose is to be
        // small. The messages are retrievable through `--all`.
        let bucket = if key.starts_with("spawn-failed") {
            "spawn-failed".to_string()
        } else {
            key.to_string()
        };
        *self.by_key.entry(bucket).or_insert(0) += 1;
        self.retrieve_with = "agent-tools ps --all";
    }
}

/// What `ps` prints. `now` is here because every relative figure below it is
/// measured against it, and a reader who cannot see the clock cannot check one.
///
/// `--all` fills `settled` rather than padding `live`: a field named `live`
/// holding children that have finished would make the one selector every
/// consumer needs into a lie, and `withheld` would then have to be empty for a
/// reason no reader could see.
#[derive(Debug, Serialize)]
pub struct Envelope {
    pub now: DateTime<chrono::Local>,
    pub session: String,
    pub live: Vec<Record>,
    /// Present only under `--all`.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub settled: Option<Vec<Record>>,
    pub withheld: Withheld,
}

/// One captured `agent-tools run` invocation on disk, as `ps` finds it.
///
/// It lives here rather than in `ps.rs` because it is the input every renderer
/// takes: the statusline builds records from it too, and a type two modules
/// need does not belong inside one of them.
pub struct Capture {
    pub agent_id: Option<String>,
    /// The third path component: a tool-use id, or `USER_SHELL`.
    pub tool_use_id: String,
    /// `<tool_use_id_dir>/<wrapper_pid>/`, holding `meta.json` and either
    /// `output` or `stdout`+`stderr`.
    pub capture_dir: std::path::PathBuf,
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd agent-tools && cargo test --bin agent-tools psrecord 2>&1 | tail -20`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/psrecord.rs agent-tools/src/status.rs agent-tools/src/main.rs
git commit -m "psrecord: three renderers each computed their own view of a child's status"
```

---

### Task 7: `ps` answers what is running, as data

**Files:**
- Modify: `agent-tools/src/ps.rs`, `agent-tools/src/main.rs`
- Test: `agent-tools/tests/ps_test.rs`

- [ ] **Step 1: Write the failing tests**

Add to `agent-tools/tests/ps_test.rs`:

```rust
#[test]
fn ps_prints_json_and_withholds_terminal_children_by_default() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(home.path(), "sid-j", None, "toolu_a", 100, Some("one"), Some(0), "x");
    seed_capture(home.path(), "sid-j", None, "toolu_a", 101, Some("two"), Some(1), "y");
    let out = agent_tools()
        .args(["ps", "--session-id", "sid-j"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).expect("ps emits json by default");
    assert_eq!(v["session"], "sid-j");
    assert!(v["now"].as_str().unwrap().contains('T'), "now is an instant: {v}");
    assert_eq!(v["live"].as_array().unwrap().len(), 0, "nothing here is running");
    assert_eq!(v["withheld"]["by_key"]["final(0)"], 1);
    assert_eq!(v["withheld"]["by_key"]["final(1)"], 1);
    assert_eq!(v["withheld"]["retrieve_with"], "agent-tools ps --all");
}

#[test]
fn ps_all_brings_the_withheld_children_back() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(home.path(), "sid-all", None, "toolu_a", 100, Some("one"), Some(0), "x");
    let out = agent_tools()
        .args(["ps", "--all", "--session-id", "sid-all"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(
        v["live"].as_array().unwrap().len(),
        0,
        "`live` must not gain children that have finished: {v}"
    );
    let settled = v["settled"].as_array().expect("--all fills settled");
    assert_eq!(settled.len(), 1);
    assert_eq!(settled[0]["name"], "one");
    assert_eq!(settled[0]["key"], "final(0)");
    assert!(settled[0]["ran_s"].is_number());
    assert!(settled[0].get("elapsed_s").is_none());
    assert!(
        v["withheld"]["by_key"].as_object().unwrap().is_empty(),
        "nothing was withheld: {v}"
    );
}

#[test]
fn without_all_there_is_no_settled_array_to_mistake_for_an_empty_one() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(home.path(), "sid-ns", None, "toolu_a", 100, Some("one"), Some(0), "x");
    let out = agent_tools()
        .args(["ps", "--session-id", "sid-ns"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert!(v.get("settled").is_none(), "{v}");
    assert_eq!(v["withheld"]["by_key"]["final(0)"], 1);
}

#[test]
fn ps_text_still_renders_the_human_layout() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(home.path(), "sid-t", None, "toolu_a", 100, Some("one"), Some(0), "x");
    let out = agent_tools()
        .args(["ps", "--format", "text", "--all", "--session-id", "sid-t"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.starts_with("session: sid-t"), "{s}");
    assert!(s.contains("one [final(0)]"), "{s}");
}

#[test]
fn the_event_log_is_out_of_the_way_until_asked_for() {
    let home = tempfile::TempDir::new().unwrap();
    let dir = seed_capture(home.path(), "sid-e", None, "toolu_a", 100, Some("one"), Some(0), "x");
    let events = dir.parent().unwrap().join("events.jsonl");
    std::fs::write(
        &events,
        "{\"ts\":\"2026-05-17T10:00:01Z\",\"kind\":\"child_started\",\"data\":{}}\n",
    )
    .unwrap();

    let without = agent_tools()
        .args(["ps", "--all", "--session-id", "sid-e"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(
        !String::from_utf8_lossy(&without.stdout).contains("child_started"),
        "the event log is not what \"what is running\" means"
    );

    let with = agent_tools()
        .args(["ps", "--format", "text", "--all", "--events", "--session-id", "sid-e"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(String::from_utf8_lossy(&with.stdout).contains("child_started"));
}

#[test]
fn ps_never_retires_a_pending_report() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(home.path(), "sid-led", None, "toolu_a", 100, Some("one"), Some(0), "x");
    let ledger = home.path().join(".claude/agent-tools/sid-led/.reported.json");
    assert!(!ledger.exists());
    agent_tools()
        .args(["ps", "--all", "--session-id", "sid-led"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(
        !ledger.exists(),
        "ps must not mark anything as told: whether its output reached the agent \
         is not something it can observe"
    );
}
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd agent-tools && cargo test --test ps_test 2>&1 | tail -25`
Expected: FAIL — `ps` prints text, `--all` / `--format` / `--events` are unrecognized.

- [ ] **Step 3: Implement**

In `agent-tools/src/main.rs`, replace the `Ps` variant with:

```rust
    /// List live tasks for this session. Prints JSON by default.
    Ps {
        #[arg(long)]
        task: Option<String>,
        #[arg(long = "session-id")]
        session_id: Option<String>,
        /// json (default), text, or statusline.
        #[arg(long, default_value = "json")]
        format: String,
        /// Include children whose fate is settled. Off by default: what is
        /// running is what a reader is still acting on.
        #[arg(long)]
        all: bool,
        /// Include the chronological event log. Off by default: it is more than
        /// half the output and answers a different question.
        #[arg(long)]
        events: bool,
    },
```

and its dispatch arm:

```rust
        Commands::Ps { task, session_id, format, all, events } => {
            if let Err(e) = ps::run(task, session_id, &format, all, events) {
                eprintln!("agent-tools: ps: {e:#}");
                std::process::exit(1);
            }
        }
```

In `agent-tools/src/ps.rs`, change the signature and split the body. `run` keeps the collection and sorting it already has, then branches:

```rust
pub fn run(
    task_filter: Option<String>,
    session_override: Option<String>,
    format: &str,
    all: bool,
    events: bool,
) -> Result<()> {
    let session_id = resolve_session(session_override)?;
    let session_dir = paths::state_root()?.join(&session_id);

    let mut captures: Vec<Capture> = Vec::new();
    if session_dir.is_dir() {
        collect_captures(&session_dir, &mut captures)?;
    }
    if let Some(ref t) = task_filter {
        captures.retain(|c| &c.tool_use_id == t);
    }
    // (the existing newest-first sort stays exactly as it is)

    let now = chrono::Utc::now();
    match format {
        "json" => render_json(&session_id, &captures, all, now),
        "text" => render_text(&session_id, &captures, all, events, now),
        "statusline" => {
            println!("{}", crate::statusline::render(&captures, now));
            Ok(())
        }
        other => anyhow::bail!("unknown --format {other}; expected json, text or statusline"),
    }
}

/// The session whose state to read. An explicit `--session-id` wins; otherwise
/// the scope a hook set; otherwise the session id every Claude Code shell
/// carries, which is what makes `! agent-tools ps` work where no hook runs.
fn resolve_session(session_override: Option<String>) -> Result<String> {
    if let Some(s) = session_override {
        return Ok(s);
    }
    if let Ok(parent_dir) = paths::parent_dir_from_env() {
        let (sid, _, _) = paths::parse_parent_dir(&parent_dir)?;
        return Ok(sid);
    }
    std::env::var("CLAUDE_CODE_SESSION_ID").context(
        "no session: AGENT_TOOLS_PARENT_DIR and CLAUDE_CODE_SESSION_ID are both unset. \
         Pass --session-id when invoking ps outside a Claude Code shell",
    )
}

fn render_json(
    session_id: &str,
    captures: &[Capture],
    all: bool,
    now: chrono::DateTime<chrono::Utc>,
) -> Result<()> {
    let mut live = Vec::new();
    let mut settled = Vec::new();
    let mut withheld = crate::psrecord::Withheld::default();
    for c in captures {
        let r = crate::psrecord::Record::build(
            &c.capture_dir,
            c.agent_id.clone(),
            &c.tool_use_id,
            now,
        );
        match (r.terminal, all) {
            (false, _) => live.push(r),
            // Asked for, so shown — in its own array, because `live` means live.
            (true, true) => settled.push(r),
            // Not asked for, so counted. The count is by key, so a spawn failure
            // among a hundred clean exits is still visible.
            (true, false) => withheld.add(&r.key),
        }
    }
    let env = crate::psrecord::Envelope {
        now: now.with_timezone(&chrono::Local),
        session: session_id.to_string(),
        live,
        settled: all.then_some(settled),
        withheld,
    };
    println!("{}", serde_json::to_string_pretty(&env)?);
    Ok(())
}
```

`render_text` is the body `run` has today — the `session:` header, the agent/tool-use grouping, `write_capture`, and the events merge — with three changes:

1. It counts and skips terminal captures unless `all`:

```rust
    let mut withheld = 0usize;
    // …inside the per-capture loop, before `write_capture`:
    if !all && crate::status::derive(&c.capture_dir, now).is_terminal() {
        withheld += 1;
        continue;
    }
```

   Note this makes the group headers (`tool-use <id> (N captures)`) count captures that may then be skipped. Compute `group_sizes` over the captures that survive the filter, not over all of them, or a group announces four and shows one.

2. It emits the events block only when `events` is true — wrap the existing chronological merge in `if events { … }`.

3. When it withholds anything it says so, on the same terms as JSON — silence about a withheld capture reads as "there were none":

```rust
    if withheld > 0 {
        writeln!(
            buf,
            "{withheld} settled capture{} withheld -> agent-tools ps --all",
            if withheld == 1 { "" } else { "s" }
        )?;
    }
```

4. **`write_capture` carries the second UTC formatter, and it must go through `fmt_local_hms` too.** Task 2 routed `status::render`'s times through local rendering, but `write_capture` in `ps.rs` formats `m.started_at` with its own `format("%H:%M:%S%.3f")` on a UTC instant. Left alone, `ps --format text` keeps printing a UTC time that reads as local — the exact hazard the spec's timing section exists to close, surviving in the one renderer nobody looked at. Replace it:

```rust
        writeln!(
            buf,
            "      started: {}",
            crate::status::fmt_local_hms(m.started_at)
        )?;
```

   The sub-second precision goes with it. It was never load-bearing — a capture's start is read against a wall clock, and milliseconds on a wrong-by-four-hours value bought nothing. Add a test asserting the text renderer's start matches the local rendering of the stored instant, mirroring `a_rendered_start_is_local_time` in `status.rs`, and update `ps_test.rs`'s existing `"started: 10:00:00.000"` assertion, which encodes both the UTC reading and the millisecond format.

- [ ] **Step 4: Run to verify they pass**

Run: `cd agent-tools && cargo test --test ps_test 2>&1 | tail -25`
Expected: PASS. Pre-existing `ps_test` cases that asserted the old default output must be updated to pass `--format text --all`.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/ps.rs agent-tools/src/main.rs agent-tools/tests/ps_test.rs
git commit -m "ps: 87712 bytes over 814 lines for a session whose every capture had already finished"
```

---

### Task 8: The statusline renderer

**Files:**
- Create: `agent-tools/src/statusline.rs`
- Modify: `agent-tools/src/main.rs` (module declaration)

- [ ] **Step 1: Write the failing test**

Create `agent-tools/src/statusline.rs` with only its tests:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn rec(name: &str, key: &str, elapsed: f64) -> crate::psrecord::Record {
        crate::psrecord::Record {
            name: name.into(),
            key: key.into(),
            origin: "tool",
            agent: None,
            tool_use_id: Some("toolu_x".into()),
            wrapper_pid: Some(1),
            child_pid: Some(2),
            started_at: None,
            elapsed_s: Some(elapsed),
            ran_s: None,
            last_byte_at: None,
            last_byte_s: None,
            bytes: 0,
            capture: vec!["/tmp/x/output".into()],
            notes: vec![],
            stat_errors: vec![],
            orphaned: None,
            terminal: key.starts_with("final") || key == "abandoned",
        }
    }
```

**This literal is a hostage to `Record`'s shape and will drift again.** Check it against the struct as it actually stands before transcribing — `wrapper_pid` became `Option<u32>` so `0` could stop impersonating a real pid, `capture` became `Vec<String>` so a split capture lists openable paths instead of a shell glob, and `stat_errors` was added so a broken filesystem stops reading as a healthy idle child. If the struct has moved again, follow the struct.

```rust

    #[test]
    fn nothing_running_prints_nothing() {
        assert_eq!(render_records(&[], now_fixed()), "");
    }

    #[test]
    fn a_line_stamps_itself_because_the_bar_does_not_tick() {
        let line = render_records(&[rec("build", "producing", 191.0)], now_fixed());
        assert!(line.starts_with("▶ @"), "{line}");
        assert!(line.contains("build 3m11s"), "{line}");
    }

    #[test]
    fn a_quiet_child_is_marked() {
        let line = render_records(&[rec("deploy", "quiet(30s)", 724.0)], now_fixed());
        assert!(line.contains("~deploy 12m04s"), "{line}");
    }

    #[test]
    fn beyond_three_the_rest_are_counted() {
        let rs: Vec<_> = ["a", "b", "c", "d", "e"]
            .iter()
            .map(|n| rec(n, "producing", 61.0))
            .collect();
        let line = render_records(&rs, now_fixed());
        assert!(line.contains("(+2)"), "{line}");
        assert!(!line.contains(" e "), "the fourth and fifth are not named: {line}");
    }

    #[test]
    fn a_long_name_is_cut_rather_than_pushing_everything_else_off() {
        let line = render_records(
            &[rec("an-extremely-long-description-of-a-task", "producing", 61.0)],
            now_fixed(),
        );
        assert!(line.contains('…'), "{line}");
        assert!(line.len() < 60, "one name must not own the bar: {line}");
    }

    fn now_fixed() -> chrono::DateTime<chrono::Utc> {
        chrono::DateTime::parse_from_rfc3339("2026-08-29T14:05:23Z")
            .unwrap()
            .with_timezone(&chrono::Utc)
    }
}
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools statusline 2>&1 | tail -20`
Expected: FAIL to compile — no `statusline` module, no `render_records`.

- [ ] **Step 3: Implement**

Add `mod statusline;` to `agent-tools/src/main.rs`. Then write the body of `agent-tools/src/statusline.rs` above its tests:

```rust
use chrono::{DateTime, Utc};

use crate::psrecord::{Capture, Record};
use crate::status::{fmt_duration, fmt_local_hms};

/// Names shown before the rest become a count.
const NAMES: usize = 3;
/// Longest name shown. The cap is fixed rather than computed: terminal width is
/// absent from the statusline payload, and `tput cols` does not supply it — it
/// returns 80 against the pipe the command's stdout is, which is worse than
/// failing, because a plausible wrong width would size the line confidently and
/// wrongly.
const NAME_MAX: usize = 14;

/// The whole line, from the captures `ps` collected.
pub fn render(captures: &[Capture], now: DateTime<Utc>) -> String {
    let records: Vec<Record> = captures
        .iter()
        .map(|c| Record::build(&c.capture_dir, c.agent_id.clone(), &c.tool_use_id, now))
        .collect();
    render_records(&records, now)
}

/// The line, from records. Separate from `render` so the formatting rules can be
/// driven without a filesystem.
pub fn render_records(records: &[Record], now: DateTime<Utc>) -> String {
    let live: Vec<&Record> = records.iter().filter(|r| !r.terminal).collect();
    if live.is_empty() {
        // Nothing running means no row at all. A bar that always carries an
        // empty slot teaches a reader to stop looking at it.
        return String::new();
    }
    let shown: Vec<String> = live
        .iter()
        .take(NAMES)
        .map(|r| {
            let quiet = if r.key.starts_with("quiet(") { "~" } else { "" };
            let name = truncate(&r.name, NAME_MAX);
            let dur = r.elapsed_s.map(fmt_duration).unwrap_or_else(|| "?".into());
            format!("{quiet}{name} {dur}")
        })
        .collect();
    let overflow = live.len().saturating_sub(NAMES);
    let tail = if overflow > 0 {
        format!("  (+{overflow})")
    } else {
        String::new()
    };
    format!("▶ @{} {}{}", fmt_local_hms(now), shown.join(" · "), tail)
}

fn truncate(s: &str, max: usize) -> String {
    if s.chars().count() <= max {
        return s.to_string();
    }
    s.chars().take(max).chain(['…']).collect()
}
```

**Escaping.** `Record` is a JSON sink, so it carries `key` raw — a newline in a spawn error is harmless there. This renderer is not a JSON sink: its output is one line in a terminal, where a newline splits the status bar and a terminal escape sequence is executed. `Record.name` arrives already escaped, because `status::name` routes through `meta::escape_control`; `key` does not. Anything this renderer prints that did not come through `name` must go through `meta::escape_control` first. Add a test seeding a `--desc` and a spawn error containing a newline and an ANSI escape, asserting the rendered line contains neither.

`Capture` already lives in `psrecord.rs` as of Task 6, so `use crate::psrecord::{Capture, Record};` at the top of this file and write `&[Capture]` rather than `&[crate::Capture]` in `render`'s signature.

- [ ] **Step 4: Run to verify it passes**

Run: `cd agent-tools && cargo test --bin agent-tools statusline 2>&1 | tail -20`
Expected: PASS.

Then verify the wiring end to end:
Run: `cd agent-tools && cargo build --release && HOME=$(mktemp -d) CLAUDE_CONFIG_ROOT=/root/claude-config-work ./target/release/agent-tools ps --format statusline --session-id nope`
Expected: an empty line, exit 0.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/statusline.rs agent-tools/src/psrecord.rs agent-tools/src/ps.rs agent-tools/src/main.rs
git commit -m "statusline: the bar said nothing about the jobs the session had running"
```

---

### Task 9: Wire the statusline

**Files:**
- Modify: `statusline.sh`

**Read this before running any step below.** Two facts make the obvious verification lie, and both were measured:

- `~/.claude/statusline.sh` resolves to the **canonical** checkout's copy, not this worktree's. Editing the file here changes nothing about the running session's bar, by design — worktrees must never `install.sh`.
- Bare `agent-tools` on `PATH` resolves to the canonical build, which predates `--format` entirely and exits 2 with `unexpected argument '--format' found`.

So the script under test must be run with this worktree's binary ahead of the installed one, or every check below reports the failure marker rather than the feature:

```bash
PATH=/root/claude-config-work/agent-tools/target/release:$PATH ./statusline.sh
```

**The live status bar will not change until the canonical checkout is rebuilt from this branch.** That is a merge-time action and is deliberately outside this branch's reach; do not attempt it, and do not treat an unchanged live bar as a defect in this task.

- [ ] **Step 1: Verify the current script runs**

Run:
```bash
cd /root/claude-config-work
echo '{"model":{"display_name":"Opus"},"session_id":"probe-none","transcript_path":"/tmp/t.jsonl","workspace":{"current_dir":"/tmp"},"context_window":{}}' \
  | PATH=/root/claude-config-work/agent-tools/target/release:$PATH ./statusline.sh
```
Expected: four lines, the first beginning `Context: 0K`.

- [ ] **Step 2: Add the open-tasks line**

In `statusline.sh`, after the `TRANSCRIPT=` assignment, add:

```bash
SESSION=$(echo "$input" | jq -r '.session_id // empty' 2>/dev/null)

# Open tasks. `ps` prints nothing when nothing is running, so the row appears
# only when there is something to say. A failure must be visible: an empty line
# and a broken one are otherwise identical, and silence reads as "nothing is
# running".
TASKS=""
if [ -n "$SESSION" ]; then
    if TASKS=$(agent-tools ps --format statusline --session-id "$SESSION" 2>/dev/null); then
        :
    else
        TASKS="▶ ?"
    fi
fi
```

and after the existing `printf` block:

```bash
[ -n "$TASKS" ] && printf "%s\n" "$TASKS"
exit 0
```

**The `exit 0` is load-bearing, not tidiness.** `[ -n "$TASKS" ] && printf …` as the last
statement returns non-zero whenever `TASKS` is empty — the ordinary case, when nothing is
running. `executeStatusLineCommand` in `/repos/claude-code-src/src/utils/hooks.ts` reads
stdout only `if (result.status === 0)` and otherwise returns undefined, which blanks the
**whole** bar rather than just omitting the new row. Without the explicit exit, adding a
status row deletes the status line for every session that has no wrapped job running.

- [ ] **Step 3: Verify it prints nothing when nothing runs**

Run:
```bash
cd /root/claude-config-work
echo '{"model":{"display_name":"Opus"},"session_id":"probe-none","transcript_path":"/tmp/t.jsonl","workspace":{"current_dir":"/tmp"},"context_window":{}}' | PATH=/root/claude-config-work/agent-tools/target/release:$PATH ./statusline.sh
```
Expected: the same four lines, no fifth.

- [ ] **Step 4: Verify it prints a row when something runs**

Run:
```bash
cd /root/claude-config-work
agent-tools run --desc "statusline-probe" sleep 20 &
sleep 1
echo "{\"model\":{\"display_name\":\"Opus\"},\"session_id\":\"$CLAUDE_CODE_SESSION_ID\",\"transcript_path\":\"/tmp/t.jsonl\",\"workspace\":{\"current_dir\":\"/tmp\"},\"context_window\":{}}" | PATH=/root/claude-config-work/agent-tools/target/release:$PATH ./statusline.sh
```
Expected: a fifth line beginning `▶ @` and naming the probe. Note the name is cut at
`NAME_MAX = 14`, so a 16-character `--desc` renders as `statusline-pro…` — assert on the
truncated form, not the full string.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add statusline.sh
git commit -m "statusline: a backgrounded job was invisible to the person who started it"
```

---

### Task 10: A scope for the shell shortcut

The `!` path fires no hook, so `AGENT_TOOLS_PARENT_DIR` is unset and `run` fails outright.

**Files:**
- Modify: `agent-tools/src/paths.rs`, `agent-tools/src/run.rs`

- [ ] **Step 1: Write the failing tests**

Add to `mod tests` in `agent-tools/src/paths.rs`:

```rust
    #[test]
    fn a_hook_set_scope_wins() {
        std::env::set_var("HOME", "/h");
        std::env::set_var("AGENT_TOOLS_PARENT_DIR", "/h/.claude/agent-tools/sid/tid");
        std::env::set_var("CLAUDE_CODE_SESSION_ID", "other");
        let (dir, origin) = scope_for_run().unwrap();
        assert_eq!(dir, PathBuf::from("/h/.claude/agent-tools/sid/tid"));
        assert_eq!(origin, "tool");
        std::env::remove_var("AGENT_TOOLS_PARENT_DIR");
        std::env::remove_var("CLAUDE_CODE_SESSION_ID");
    }

    #[test]
    fn with_no_hook_the_session_id_gives_a_user_shell_scope() {
        std::env::set_var("HOME", "/h");
        std::env::remove_var("AGENT_TOOLS_PARENT_DIR");
        std::env::set_var("CLAUDE_CODE_SESSION_ID", "sid-9");
        let (dir, origin) = scope_for_run().unwrap();
        assert_eq!(dir, PathBuf::from("/h/.claude/agent-tools/sid-9/user-shell"));
        assert_eq!(origin, "user-shell");
        std::env::remove_var("CLAUDE_CODE_SESSION_ID");
    }

    #[test]
    fn with_neither_the_error_names_both_routes() {
        std::env::set_var("HOME", "/h");
        std::env::remove_var("AGENT_TOOLS_PARENT_DIR");
        std::env::remove_var("CLAUDE_CODE_SESSION_ID");
        let e = scope_for_run().unwrap_err().to_string();
        assert!(e.contains("AGENT_TOOLS_PARENT_DIR"), "{e}");
        assert!(e.contains("CLAUDE_CODE_SESSION_ID"), "{e}");
    }
```

These tests mutate process-global environment; run this module's tests single-threaded (`cargo test --bin agent-tools paths:: -- --test-threads=1`) or the existing suite convention if the file already has one.

- [ ] **Step 2: Run to verify they fail**

Run: `cd agent-tools && cargo test --bin agent-tools paths:: -- --test-threads=1 2>&1 | tail -20`
Expected: FAIL — `cannot find function 'scope_for_run'`.

- [ ] **Step 3: Implement**

Add to `agent-tools/src/paths.rs`:

```rust
/// Where a `run` invocation's captures belong, and what that location means.
///
/// A hook-set `AGENT_TOOLS_PARENT_DIR` wins whenever it exists. Otherwise the
/// session id every Claude Code shell exports gives a scope named `user-shell`,
/// which is what makes `! agent-tools run …` work where no hook fires.
///
/// The fallback cannot tell "the user typed `!`" from "a subagent whose
/// PreToolUse hook failed": a subagent's shell exports an identical variable
/// set, with the same session id, and only `AGENT_TOOLS_PARENT_DIR` differs by
/// carrying the agent id. Both land here, and `user-shell` asserts exactly what
/// was observed — that no hook set a scope. A subagent's child is then reported
/// to the main thread rather than to that subagent: over-reported, never lost,
/// which is the direction the invariant already prefers.
pub fn scope_for_run() -> Result<(PathBuf, &'static str)> {
    if let Ok(p) = parent_dir_from_env() {
        return Ok((p, "tool"));
    }
    let session = env::var("CLAUDE_CODE_SESSION_ID").map_err(|_| {
        anyhow::anyhow!(
            "no scope for this run.\n\
             AGENT_TOOLS_PARENT_DIR is unset, so no PreToolUse hook ran, and \
             CLAUDE_CODE_SESSION_ID is unset too, so this is not a Claude Code shell.\n\
             Inside a Claude Code Bash tool, the hook is not installed."
        )
    })?;
    Ok((
        state_root()?.join(session).join(crate::psrecord::USER_SHELL),
        "user-shell",
    ))
}
```

In `agent-tools/src/run.rs`, replace the `paths::parent_dir_from_env().map_err(...)` block with:

```rust
    let (parent_dir, _origin) = paths::scope_for_run()?;
```

- [ ] **Step 4: Run to verify they pass**

Run: `cd agent-tools && cargo test 2>&1 | tail -20`
Expected: PASS.

Then verify by hand:
```bash
cd agent-tools && cargo build --release
env -u AGENT_TOOLS_PARENT_DIR CLAUDE_CODE_SESSION_ID=probe-shell CLAUDE_CONFIG_ROOT=/root/claude-config-work \
  ./target/release/agent-tools run --desc "shell-probe" echo hi
ls ~/.claude/agent-tools/probe-shell/user-shell/
```
Expected: `hi` on stdout, and one pid-named directory under `user-shell/`.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/paths.rs agent-tools/src/run.rs
git commit -m "paths: the ! shell shortcut fires no hook, so run had no scope and refused to start"
```

---

### Task 11: The core can forward to nowhere

**Files:**
- Modify: `agent-tools/src/core.rs`
- Test: `agent-tools/tests/core_test.rs`

- [ ] **Step 1: Write the failing test**

Add to `agent-tools/tests/core_test.rs`:

```rust
#[tokio::test]
async fn a_run_with_no_destination_captures_one_merged_file_and_forwards_nothing() {
    let dir = tempfile::TempDir::new().unwrap();
    let out = agent_tools::core::run_core(
        &["sh".into(), "-c".into(), "echo out; echo err 1>&2".into()],
        dir.path(),
        None,
        agent_tools::core::Destination::Nowhere,
        |_pid, merge| {
            assert_eq!(
                merge, agent_tools::core::BACKGROUNDED,
                "a run with no caller records why it merged"
            );
        },
        |_code| {},
    )
    .await
    .unwrap();
    assert_eq!(out.exit_code, 0);
    let captured = std::fs::read_to_string(dir.path().join("output")).unwrap();
    assert!(captured.contains("out"), "{captured}");
    assert!(captured.contains("err"), "{captured}");
    assert!(
        !dir.path().join("stdout").exists(),
        "a merged capture holds one file; the other is absent, not empty"
    );
    assert!(!out.forward_closed, "there was no downstream to close");
}
```

If `core_test.rs` drives the binary rather than the library, add this as a unit test in `agent-tools/src/core.rs`'s own `mod tests` instead and drop the `agent_tools::` prefixes.

- [ ] **Step 2: Run to verify it fails**

Run: `cd agent-tools && cargo test destination 2>&1 | tail -20`
Expected: FAIL — `run_core` takes five arguments, `Destination` does not exist.

- [ ] **Step 3: Implement**

In `agent-tools/src/core.rs`, add beside `Merge`:

```rust
/// The condition recorded when the wrapper, not the caller, owns where the
/// child's bytes go. Not an exception to the merge rule but an instance of it:
/// one appending regular file has no offset to disagree about.
pub const BACKGROUNDED: &str = "backgrounded: wrapper owns the destination";

/// Where the child's streams are forwarded, beyond the capture.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Destination {
    /// This process's own stdout and stderr, which the merge rule inspects.
    Caller,
    /// Nowhere. The caller has gone; the capture is the whole record.
    None,
}
```

Change `run_core`'s signature to take `destination: Destination` after `drain_cap_bytes`, and replace the merge decision with:

```rust
    let merge = match destination {
        Destination::Caller => decide_merge(libc::STDOUT_FILENO, libc::STDERR_FILENO),
        // Nothing to inspect: there is no caller destination for the streams to
        // agree or disagree about, and the one this wrapper opens is a single
        // appending regular file.
        Destination::Nowhere => Merge::Merged(BACKGROUNDED),
    };
```

In the `Streams::Merged(rx)` arm, make the forward target depend on the destination. `capture::tee` is already generic over its writer, and both spawns produce the same `JoinHandle<Result<TeeOutcome>>`:

```rust
        Streams::Merged(rx) => {
            let tee = match destination {
                Destination::Caller => tokio::spawn(capture::tee(
                    "output", rx, dir.join("output"), tokio::io::stdout(),
                    drain_cap_bytes, last_stdout.clone(), dir.clone(),
                )),
                Destination::Nowhere => tokio::spawn(capture::tee(
                    "output", rx, dir.join("output"), tokio::io::sink(),
                    drain_cap_bytes, last_stdout.clone(), dir.clone(),
                )),
            };
            // (the watch_silence spawn is unchanged)
```

Update both existing call sites to pass `Destination::Caller`: `run.rs`'s `core::run_core(...)` and `main.rs`'s `RunCore` arm.

- [ ] **Step 4: Run to verify it passes**

Run: `cd agent-tools && cargo test 2>&1 | tail -25`
Expected: PASS across the suite, including the `run-core` passthrough differencing tests, which must be unaffected — they pass `Destination::Caller`.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/core.rs agent-tools/src/run.rs agent-tools/src/main.rs agent-tools/tests/
git commit -m "core: a run whose caller has gone still wrote to the caller's descriptors"
```

---

### Task 12: Fork, setsid, and a readiness pipe

A tokio runtime cannot survive `fork` — its worker threads do not cross. So the fork happens before any runtime exists, and the parent learns the outcome through a pipe.

**Files:**
- Create: `agent-tools/src/background.rs`
- Modify: `agent-tools/src/main.rs` (module declaration)

- [ ] **Step 1: Write the failing test**

Create `agent-tools/src/background.rs` with only its tests:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_parent_learns_success_and_the_child_leads_its_own_session() {
        match detach() {
            Detached::Parent(Ok(msg)) => assert_eq!(msg, "started: pid 1234"),
            Detached::Parent(Err(e)) => panic!("parent saw failure: {e}"),
            Detached::Child(reporter) => {
                // Its own session is what survives the caller's group being killed.
                assert_eq!(
                    nix::unistd::getsid(None).unwrap(),
                    nix::unistd::getpid(),
                    "the detached child must lead its own session"
                );
                reporter.started("started: pid 1234");
                std::process::exit(0);
            }
        }
    }

    #[test]
    fn the_parent_learns_the_reason_a_start_failed() {
        match detach() {
            Detached::Parent(Ok(msg)) => panic!("parent saw success: {msg}"),
            Detached::Parent(Err(e)) => {
                assert!(e.to_string().contains("Permission denied"), "{e}")
            }
            Detached::Child(reporter) => {
                reporter.failed(&anyhow::anyhow!("mkdir /nope: Permission denied"))
            }
        }
    }

    #[test]
    fn a_child_that_dies_without_reporting_is_a_failed_start() {
        match detach() {
            Detached::Parent(Ok(msg)) => panic!("parent saw success: {msg}"),
            Detached::Parent(Err(e)) => assert!(
                e.to_string().contains("before saying whether it started"),
                "{e}"
            ),
            // Drops the reporter and exits: the write end closes with nothing on it.
            Detached::Child(_) => std::process::exit(1),
        }
    }
}
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd agent-tools && cargo test --bin agent-tools background 2>&1 | tail -20`
Expected: FAIL to compile — no `background` module, no `detach`, no `Detached`, no `Reporter`.

- [ ] **Step 3: Implement**

Add `mod background;` to `agent-tools/src/main.rs`. Write `agent-tools/src/background.rs` above its tests:

```rust
use anyhow::{anyhow, Result};
use std::io::Read;
use std::os::fd::OwnedFd;

/// Which side of the fork the caller is on.
pub enum Detached {
    /// The original process. Carries what the child reported about starting: the
    /// line to print, or the reason nothing started.
    Parent(Result<String>),
    /// The detached process, in a session of its own. It owns the one channel
    /// back to the caller and must use it exactly once.
    Child(Reporter),
}

/// The detached child's single message to the caller that is still blocking on
/// it. Consuming `self` is the type saying what the protocol says: one report,
/// then the pipe closes and the caller stops waiting.
pub struct Reporter {
    fd: OwnedFd,
}

impl Reporter {
    /// The child started. `line` is what the caller prints.
    pub fn started(self, line: &str) {
        self.write(&format!("ok\n{line}"));
        // Dropping closes the write end, which is what ends the parent's read.
    }

    /// Nothing started, and this is why. Does not return: a process that failed
    /// to start a child has nothing left to do, and continuing would leave a
    /// detached wrapper supervising a child that does not exist.
    pub fn failed(self, e: &anyhow::Error) -> ! {
        self.write(&format!("err\n{e:#}"));
        drop(self);
        std::process::exit(1)
    }

    /// Best effort. The caller may already be gone — killed, or interrupted —
    /// and there is nothing useful to do about that from here: the capture on
    /// disk is the durable record, and the status channel carries it.
    fn write(&self, msg: &str) {
        let mut buf = msg.as_bytes();
        while !buf.is_empty() {
            match nix::unistd::write(&self.fd, buf) {
                Ok(0) => break,
                Ok(n) => buf = &buf[n..],
                Err(nix::errno::Errno::EINTR) => continue,
                Err(_) => break,
            }
        }
    }
}

/// Fork, put the child in its own session, and block the parent until the child
/// reports.
///
/// The fork is here, before any tokio runtime exists, because a runtime does not
/// survive `fork`: its worker threads do not cross, and the child would hold a
/// runtime whose executor is gone. Everything asynchronous therefore happens
/// after this returns `Child`.
///
/// The parent blocks on the pipe until the child calls `Reporter::started` or
/// `Reporter::failed`, or dies holding it. That is the whole point: a caller
/// that walked away before learning a start failed is the failure mode `&` has
/// and this does not.
///
/// `setsid` is what makes the child survive the caller's process group being
/// killed. Measured: a `setsid` child outlives a Claude Code Bash call killed at
/// its timeout, where `nohup` and a bare `&` do not.
pub fn detach() -> Detached {
    // O_CLOEXEC so no descendant of the wrapped command inherits the write end
    // and holds the parent's read open after this process is done with it.
    let (read_fd, write_fd) = match nix::unistd::pipe2(nix::fcntl::OFlag::O_CLOEXEC) {
        Ok(p) => p,
        Err(e) => return Detached::Parent(Err(anyhow!("pipe: {e}"))),
    };

    // SAFETY: this process is single-threaded here — the fork happens before any
    // tokio runtime is built, which is the reason it happens here at all. The
    // child's only work before it diverges is `setsid`, and nothing it touches
    // is shared with a thread that no longer exists on its side.
    match unsafe { nix::unistd::fork() } {
        Err(e) => Detached::Parent(Err(anyhow!("fork: {e}"))),
        Ok(nix::unistd::ForkResult::Parent { .. }) => {
            // The parent must not hold a write end, or its own read never ends.
            drop(write_fd);
            let mut buf = String::new();
            let mut f = std::fs::File::from(read_fd);
            if let Err(e) = f.read_to_string(&mut buf) {
                return Detached::Parent(Err(anyhow!("read start status: {e}")));
            }
            match buf.split_once('\n') {
                Some(("ok", rest)) => Detached::Parent(Ok(rest.trim_end().to_string())),
                Some(("err", rest)) => Detached::Parent(Err(anyhow!("{}", rest.trim_end()))),
                // Includes the empty read: the child died holding the pipe, which
                // is a failure to start however it happened.
                _ => Detached::Parent(Err(anyhow!(
                    "the backgrounded wrapper exited before saying whether it started"
                ))),
            }
        }
        Ok(nix::unistd::ForkResult::Child) => {
            drop(read_fd);
            let reporter = Reporter { fd: write_fd };
            // A child that could not detach must not pass for one that did.
            if let Err(e) = nix::unistd::setsid() {
                reporter.failed(&anyhow!("setsid: {e}"));
            }
            Detached::Child(reporter)
        }
    }
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd agent-tools && cargo test --bin agent-tools background 2>&1 | tail -20`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/background.rs agent-tools/src/main.rs
git commit -m "background: nothing could start a child that both outlived its caller and told the caller it started"
```

---

### Task 13: `run --background`

**Files:**
- Modify: `agent-tools/src/run.rs`, `agent-tools/src/main.rs`
- Test: `agent-tools/tests/background_test.rs` (create)

- [ ] **Step 1: Write the failing tests**

Create `agent-tools/tests/background_test.rs`:

```rust
use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf()
}

fn agent_tools(home: &std::path::Path, scope: &std::path::Path) -> Command {
    let mut c = Command::new(bin());
    c.env("CLAUDE_CONFIG_ROOT", worktree_root());
    c.env("HOME", home);
    c.env("AGENT_TOOLS_PARENT_DIR", scope);
    c
}

#[test]
fn background_returns_immediately_and_names_where_the_output_will_be() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid-bg/toolu_bg");
    std::fs::create_dir_all(&scope).unwrap();

    let started = std::time::Instant::now();
    let out = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "slow", "sleep", "5"])
        .output()
        .unwrap();
    let elapsed = started.elapsed();

    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    assert!(
        elapsed.as_secs() < 3,
        "--background returned only after the child finished: {elapsed:?}"
    );
    let line = String::from_utf8_lossy(&out.stdout);
    assert!(line.contains("wrapper pid"), "{line}");
    assert!(line.contains("child pid"), "{line}");
    let dir: PathBuf = line.split_whitespace().next().unwrap().into();
    assert!(dir.join("meta.json").exists(), "the capture exists before the call returns");
}

#[test]
fn a_start_that_fails_is_loud_and_nothing_is_left_running() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid-bf/toolu_bf");
    std::fs::create_dir_all(&scope).unwrap();

    let out = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "nope", "/nonexistent/binary-x9"])
        .output()
        .unwrap();

    assert!(!out.status.success(), "a failed start must not exit 0");
    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.contains("No such file") || err.contains("binary-x9"),
        "the reason must reach the caller while it is still reading: {err}"
    );
}

#[test]
fn a_backgrounded_child_captures_both_streams_into_one_file_and_forwards_neither() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid-bm/toolu_bm");
    std::fs::create_dir_all(&scope).unwrap();

    let out = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "both", "sh", "-c", "echo O; echo E 1>&2"])
        .output()
        .unwrap();
    let line = String::from_utf8_lossy(&out.stdout);
    let dir: PathBuf = line.split_whitespace().next().unwrap().into();

    // The identity line is all the caller gets; the child's bytes are not on it.
    assert!(!line.contains('O'), "no forwarding: {line}");
    assert!(!String::from_utf8_lossy(&out.stderr).contains('E'), "no forwarding");

    // Wait for the detached wrapper to finish recording.
    for _ in 0..100 {
        let m = std::fs::read_to_string(dir.join("meta.json")).unwrap_or_default();
        if m.contains("\"drained_at\": \"") {
            break;
        }
        std::thread::sleep(std::time::Duration::from_millis(50));
    }
    let captured = std::fs::read_to_string(dir.join("output")).unwrap();
    assert!(captured.contains('O') && captured.contains('E'), "{captured}");
    assert!(
        !dir.join("stdout").exists(),
        "a merged capture holds one file; the other is absent, not empty"
    );
    let meta: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(dir.join("meta.json")).unwrap()).unwrap();
    assert_eq!(meta["merge"], "backgrounded: wrapper owns the destination");
    assert_eq!(meta["reaped"]["status"], 0);
}

#[test]
fn exit_zero_means_started_not_succeeded() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid-bx/toolu_bx");
    std::fs::create_dir_all(&scope).unwrap();

    let out = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "fails", "sh", "-c", "exit 3"])
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "the child's failure is not the wrapper's; it reaches the caller through the status channel"
    );
    let dir: PathBuf = String::from_utf8_lossy(&out.stdout)
        .split_whitespace()
        .next()
        .unwrap()
        .into();
    for _ in 0..100 {
        let m = std::fs::read_to_string(dir.join("meta.json")).unwrap_or_default();
        if m.contains("\"drained_at\": \"") {
            break;
        }
        std::thread::sleep(std::time::Duration::from_millis(50));
    }
    let meta: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(dir.join("meta.json")).unwrap()).unwrap();
    assert_eq!(meta["reaped"]["status"], 3);
}

#[test]
fn a_non_tty_stdin_is_inherited_so_redirection_still_works() {
    use std::io::Write;
    use std::process::Stdio;

    let home = tempfile::TempDir::new().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid-bi/toolu_bi");
    std::fs::create_dir_all(&scope).unwrap();

    let mut child = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "reads", "cat"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(b"payload-from-stdin\n")
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success());
    let dir: PathBuf = String::from_utf8_lossy(&out.stdout)
        .split_whitespace()
        .next()
        .unwrap()
        .into();
    for _ in 0..100 {
        if std::fs::read_to_string(dir.join("meta.json"))
            .unwrap_or_default()
            .contains("\"drained_at\": \"")
        {
            break;
        }
        std::thread::sleep(std::time::Duration::from_millis(50));
    }
    let captured = std::fs::read_to_string(dir.join("output")).unwrap();
    assert!(
        captured.contains("payload-from-stdin"),
        "a detached child must still read the stdin it was given: {captured}"
    );
}

#[test]
fn background_composes_with_the_flags_run_already_had() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid-bc/toolu_bc");
    std::fs::create_dir_all(&scope).unwrap();

    let out = agent_tools(home.path(), &scope)
        .args([
            "run",
            "--background",
            "--hide-cmdline",
            "--drain-cap-bytes",
            "4096",
            "--desc",
            "composed",
            "echo",
            "ok",
        ])
        .output()
        .unwrap();
    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    let dir: PathBuf = String::from_utf8_lossy(&out.stdout)
        .split_whitespace()
        .next()
        .unwrap()
        .into();
    let meta: serde_json::Value =
        serde_json::from_str(&std::fs::read_to_string(dir.join("meta.json")).unwrap()).unwrap();
    assert_eq!(meta["desc"], "composed", "--desc still reaches the record");
}
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd agent-tools && cargo test --test background_test 2>&1 | tail -25`
Expected: FAIL — `--background` is unrecognized.

- [ ] **Step 3: Implement**

In `agent-tools/src/main.rs`, add to the `Run` variant:

```rust
        /// Return as soon as the child has started, then detach. Exit 0 means
        /// started, not succeeded: the child's own status reaches the caller
        /// through the status channel and nowhere else.
        #[arg(long)]
        background: bool,
```

The `Run` arm currently builds a tokio runtime and blocks on `run::run(...)`. Restructure it so the fork happens before the runtime exists:

```rust
        Commands::Run { desc, hide_cmdline, drain_cap_bytes, background, cmd } => {
            let mut reporter = None;
            if background {
                match crate::background::detach() {
                    background::Detached::Parent(Ok(line)) => {
                        println!("{line}");
                        return;
                    }
                    background::Detached::Parent(Err(e)) => {
                        eprintln!("agent-tools: run: {e:#}");
                        std::process::exit(2);
                    }
                    // This process is now detached, in its own session, holding
                    // the one channel back to a caller that is still blocking.
                    background::Detached::Child(r) => {
                        detach_std_fds();
                        reporter = Some(r);
                    }
                }
            }
            // (existing runtime construction, then:)
            let code = rt.block_on(run::run(desc, hide_cmdline, drain_cap_bytes, reporter, cmd));
            // (existing handling of `code`)
        }
```

Note `reporter` is `Option<Reporter>`, and its presence *is* the "am I backgrounded" flag — one fact with one representation, rather than a `bool` that could disagree with it.

Add to `agent-tools/src/main.rs`:

```rust
/// Take the detached wrapper off the caller's descriptors.
///
/// stdout and stderr go to `/dev/null`: the caller has its answer and has moved
/// on, so anything written now lands in the middle of whatever the shell ran
/// next. The child's own bytes are unaffected — they go to the capture, which is
/// the whole record for a backgrounded run.
///
/// stdin is left alone when it is not a terminal, so `< file` and a heredoc
/// behave (measured: a heredoc reaches a `setsid` child that reads it after the
/// parent has moved on). A terminal is replaced, because a detached process must
/// not read the terminal — it is no longer in the foreground process group and
/// would be stopped with SIGTTIN.
fn detach_std_fds() {
    use std::os::fd::AsRawFd;
    if let Ok(devnull) = std::fs::OpenOptions::new().read(true).write(true).open("/dev/null") {
        let fd = devnull.as_raw_fd();
        unsafe {
            libc::dup2(fd, libc::STDOUT_FILENO);
            libc::dup2(fd, libc::STDERR_FILENO);
            if libc::isatty(libc::STDIN_FILENO) == 1 {
                libc::dup2(fd, libc::STDIN_FILENO);
            }
        }
    }
}
```

Then change `run::run`'s signature to take the reporter, and use its presence for both decisions:

```rust
pub async fn run(
    desc: Option<String>,
    hide_cmdline: bool,
    drain_cap_bytes: Option<u64>,
    mut reporter: Option<crate::background::Reporter>,
    cmd: Vec<String>,
) -> Result<i32> {
```

Every early return in `run` — the empty-command check, the scope failure, the `create_dir_all` failure, the pre-spawn `publish_child_dir` failure — must go through the reporter when there is one, or the caller blocks until this process exits and then reads an empty pipe. Add at the top, right after the signature:

```rust
    // A failure before the spawn is the caller's to hear about, synchronously.
    // Without this every early return would reach it only as "exited before
    // saying whether it started", losing the reason.
    macro_rules! bail_to_caller {
        ($e:expr) => {{
            let e: anyhow::Error = $e;
            match reporter.take() {
                Some(r) => r.failed(&e),
                None => return Err(e),
            }
        }};
    }
```

and route those four early returns through it, e.g.:

```rust
    if cmd.is_empty() {
        bail_to_caller!(anyhow!("no command supplied after --"));
    }
    let (parent_dir, _origin) = match paths::scope_for_run() {
        Ok(v) => v,
        Err(e) => bail_to_caller!(e),
    };
```

The destination follows the same fact:

```rust
    let destination = if reporter.is_some() {
        core::Destination::Nowhere
    } else {
        core::Destination::Caller
    };
```

and `destination` is passed to `core::run_core`.

The spawn is the last thing that can fail before there is a child, and it happens inside `run_core`. Two sites therefore finish the protocol:

In the `on_spawn` callback, once the child exists — this is the success path, and it is here rather than earlier so the line can name the child pid:

```rust
    // `on_spawn` is `FnOnce`, so the reporter can be moved into it; it fires
    // exactly once, the moment there is a child to name.
    let report_started = reporter.take();
    // …inside the existing `on_spawn` closure body, after the meta write:
    if let Some(r) = report_started {
        r.started(&format!(
            "{}  wrapper pid {}  child pid {}",
            dir.display(),
            wrapper_pid,
            pid
        ));
    }
```

In the `CoreError::Spawn(e)` arm, after the existing `spawn_error` meta write and `spawn_failed` event — `on_spawn` never ran, so the reporter is still unconsumed and must carry the reason:

```rust
            // The caller is still blocking. Without this it learns only that the
            // wrapper exited, and the one thing that went wrong goes unsaid.
            if let Some(r) = report_started {
                r.failed(&anyhow!("spawn {:?}: {e}", cmd));
            }
            return Err(anyhow!("spawn {:?}: {e}", cmd));
```

Because `report_started` is moved into `on_spawn`, hold it in an `Arc<Mutex<Option<Reporter>>>` shared between the closure and the error arm, matching how `cm` is already shared, and take from it at whichever site runs first.

- [ ] **Step 4: Run to verify they pass**

Run: `cd agent-tools && cargo test --test background_test 2>&1 | tail -30`
Expected: PASS.

Then the whole suite, because `run::run`'s signature changed:
Run: `cd agent-tools && cargo test 2>&1 | tail -30`
Expected: PASS.

Then verify detachment by hand, which no test can assert (it needs a Bash tool timeout):

```bash
cd agent-tools && cargo build --release
CLAUDE_CONFIG_ROOT=/root/claude-config-work ./target/release/agent-tools run --background --desc "detach-probe-k4" sleep 45
ps -o pid,ppid,pgid,sess,args -p "$(pgrep -f 'sleep 45' | head -1)"
```
Expected: the identity line, then a process whose `PGID` and `SESS` equal its own pid — its own session, which is what survives the caller's group being killed. Kill it afterwards by pid, after checking its argv.

- [ ] **Step 5: Commit**

```bash
cd /root/claude-config-work
git add agent-tools/src/run.rs agent-tools/src/background.rs agent-tools/src/main.rs agent-tools/tests/background_test.rs
git commit -m "run: backgrounding meant the shell's &, which swallows the exit code and can leave nothing on disk"
```

---

### Task 14: Documentation, and the claim that is false

**Files:**
- Modify: `sys_prompt/alan-default-next.md`, `agent-tools/CLAUDE.md`, `CLAUDE.md`

- [ ] **Step 1: Find the false claim**

Run: `cd /root/claude-config-work && grep -n "setsid" sys_prompt/alan-default-next.md`
Expected: the backgrounding bullet, stating that a killed call takes `&`, `nohup` and `setsid` alike.

- [ ] **Step 2: Rewrite the backgrounding bullet**

Replace it so it teaches `--background` and states the measured truth. The bullet must say:

- A command started with `&` keeps running across later calls, but is killed with the call if the call outruns its `timeout`. `nohup` does not change that.
- `agent-tools run --background <cmd>` returns as soon as the child has started, prints the capture directory and the pids, and exits non-zero with the reason on stderr if nothing started. It detaches into its own session, so it survives the call being killed.
- Its exit code means started, not succeeded. The child's own status arrives on the status channel.
- It captures both streams into one `output` file and forwards neither, so nothing from the child appears in the rest of the call.

Remove the `timeout <seconds> tail --pid=…` incantation from the recommended path — it remains correct for a bare `&`, but `--background` is what the prompt should teach.

**Also fix the status-line shape in the same file.** It states `<detail>` is `pid <pid>, <age>, <bytes>`, which Task 2 superseded — a `timing` fragment now sits between the pid and the age. That sentence is the one the agent actually reads, and the spec requires the prompt's quoted lines to match what is emitted. Update it to the three real forms:

- `pid <pid>, started <t>, ran <d>, <age>, <bytes>` for a terminal child
- `pid <pid>, started <t> (+<d>), <age>, <bytes>` for a live one
- `pid <pid>, started <t>, <age>, <bytes>` for a terminal child with no reap

Then check `scripts/check-prompt-coupling.sh`: it has no needle for `<detail>`, `pid <pid>` or `<age>`, so nothing currently catches this drift. Add one, or the next change to the line shape breaks the prompt silently again.

**Close the recurring hole rather than patching it a fourth time.** Tasks 2, 3 and 4 each shipped agent-facing text the script had no needle for, and each time the gate stayed green while the prompt went false — the failure mode the script exists to prevent, arriving through the one route it cannot see. Patching needle-by-needle has now failed three times, so add the coverage check instead: require a marker comment (`// PROMPT-COUPLED`) directly above every literal in `hook_post.rs` and `status.rs` that reaches `additionalContext`, and have the script assert that the number of markers equals the number of `check` lines targeting those files. A new prompt-facing literal shipped without a needle then fails as a count mismatch at the top of the script, before any individual `check` runs. One extra grep; it does not touch the existing needle list, its ordering, or its comments.

- [ ] **Step 3: Update `agent-tools/CLAUDE.md`**

Add `--background` to the `run` entry, and replace the `ps` entry with one naming `--format <json|text|statusline>` (default `json`), `--all`, `--events`, and the live-only default. Add a `psrecord.rs`, `statusline.rs` and `background.rs` row to the file index.

**Update the "Report lines" section.** It documents the line shape as `<name> [<key>] pid <pid>, <age>, <bytes> …`, which Task 2 superseded: a `timing` fragment now sits between the pid and the age, in one of three forms — `started <t>, ran <d>, ` for a terminal child, `started <t> (+<d>), ` for a live one, and `started <t>, ` for a terminal child with no reap, whose end nobody observed. That section also enumerates which fields are capped versus escaped; check the enumeration still holds.

State the two rules that are easy to break later:

- `ps` never commits the ledger, in any format. Whether its output reached the agent is not something it can observe.
- Push report, `ps` and statusline read `psrecord::Record`; none derives a status of its own.

- [ ] **Step 4: Update the repo `CLAUDE.md`**

In the `agent-tools/` subcommand list, update the `run` and `ps` lines to match, and add the statusline consumer to the `scripts/`/`statusline.sh` description.

- [ ] **Step 5: Verify nothing else still describes the old surface**

Run:
```bash
cd /root/claude-config-work
grep -rn "agent-tools ps" --include=*.md . | grep -v docs/superpowers/
```
Expected: every hit describes the new surface. Fix any that do not.

- [ ] **Step 6: Commit**

```bash
cd /root/claude-config-work
git add sys_prompt/alan-default-next.md agent-tools/CLAUDE.md CLAUDE.md
git commit -m "docs: the prompt said a killed call takes setsid too, and it does not"
```

---

## Verification

After Task 14, confirm the whole change end to end:

```bash
cd /root/claude-config-work/agent-tools && cargo test 2>&1 | tail -5
cargo build --release
CLAUDE_CONFIG_ROOT=/root/claude-config-work ./target/release/agent-tools run --background --desc "verify-probe" sh -c 'sleep 2; echo done'
CLAUDE_CONFIG_ROOT=/root/claude-config-work ./target/release/agent-tools ps
sleep 3
CLAUDE_CONFIG_ROOT=/root/claude-config-work ./target/release/agent-tools ps
```

Expected: the identity line; then a `live` array holding `verify-probe` with an `elapsed_s` and no `ran_s`; then an empty `live` array with `withheld.by_key` holding `final(0): 1`.
