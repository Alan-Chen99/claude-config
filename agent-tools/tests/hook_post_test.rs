use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

fn agent_tools() -> Command {
    let mut command = Command::new(bin());
    command.env("CLAUDE_CONFIG_ROOT", worktree_root());
    command
}

fn run_post(
    home: &std::path::Path,
    body: serde_json::Value,
) -> (std::process::ExitStatus, String, String) {
    let mut c = agent_tools()
        .arg("hook-post")
        .env("HOME", home)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(body.to_string().as_bytes())
        .unwrap();
    let out = c.wait_with_output().unwrap();
    (
        out.status,
        String::from_utf8_lossy(&out.stdout).into_owned(),
        String::from_utf8_lossy(&out.stderr).into_owned(),
    )
}

/// Compute the parent dir for captures under `home` matching `paths::parent_dir_for`.
fn parent_dir(
    home: &std::path::Path,
    session: &str,
    agent: Option<&str>,
    tuid: &str,
) -> std::path::PathBuf {
    let mut p = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        p.push(a);
    }
    p.push(tuid);
    p
}

/// Write a capture dir with the given facts and return its identity string.
///
/// `wrapper_started_ticks: 1` never matches a real process's start time, so the
/// wrapper reads as dead however the pid is allocated on this machine.
fn seed(home: &std::path::Path, tuid: &str, wrapper_pid: u32, reaped: Option<i32>) -> String {
    let parent = parent_dir(home, "sid", None, tuid);
    let dir = parent.join(wrapper_pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let reaped_json = match reaped {
        Some(s) => format!(
            r#"{{"at":"{}","status":{s}}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
        None => "null".to_string(),
    };
    let meta = format!(
        r#"{{"wrapper_pid":{wrapper_pid},"wrapper_started_ticks":1,"child_pid":4242,
            "desc":"seeded","command":["true"],"started_at":"{}",
            "spawn_error":null,"reaped":{reaped_json},"drained_at":null}}"#,
        chrono::Utc::now().to_rfc3339()
    );
    std::fs::write(dir.join("meta.json"), meta).unwrap();
    format!("{tuid}/{wrapper_pid}")
}

fn post_body(tool: &str, tuid: &str) -> serde_json::Value {
    serde_json::json!({
        "session_id": "sid",
        "tool_name": tool,
        "tool_input": {},
        "tool_use_id": tuid,
        "tool_response": {}
    })
}

#[test]
fn no_parent_dir_no_bg_emits_nothing() {
    let home = tempfile::tempdir().unwrap();
    // No parent dir created on disk.
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "tool_use_id": "tuid",
            "tool_response": {}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    if !stdout.trim().is_empty() {
        let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
        assert!(
            v.get("hookSpecificOutput")
                .and_then(|h| h.get("additionalContext"))
                .is_none(),
            "should not emit additionalContext, got {stdout}"
        );
    }
}

#[test]
fn bg_only_emits_only_bg_notice() {
    let home = tempfile::tempdir().unwrap();
    // No captures, but backgroundTaskId present.
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "sleep 9999", "timeout": 5000},
            "tool_use_id": "tuid",
            "tool_response": {"backgroundTaskId": "bt-7"}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(ctx.starts_with("BACKGROUNDED:"), "ctx: {ctx}");
    assert!(ctx.contains("bt-7"), "ctx: {ctx}");
    assert!(ctx.contains("5000"), "ctx: {ctx}");
    assert!(!ctx.contains("[agent-tools] captures"), "ctx: {ctx}");
}

#[test]
fn explicit_run_in_background_is_not_reported_as_timeout() {
    // Regression (main b279c25): when tool_input.run_in_background == true,
    // BashTool returns a backgroundTaskId immediately with neither
    // assistantAutoBackgrounded nor backgroundedByUser set
    // (BashTool.tsx:989-1000). The post-hook must recognize this as an
    // intentional background, not a timeout.
    let home = tempfile::tempdir().unwrap();
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "long-running", "run_in_background": true},
            "tool_use_id": "tuid",
            "tool_response": {"backgroundTaskId": "bt-rib"}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(ctx.starts_with("BACKGROUNDED:"), "ctx: {ctx}");
    assert!(ctx.contains("bt-rib"), "ctx: {ctx}");
    assert!(
        !ctx.contains("timeout"),
        "should NOT report timeout for explicit run_in_background: {ctx}"
    );
    assert!(
        ctx.contains("explicit run_in_background"),
        "should label cause as explicit run_in_background: {ctx}"
    );
}

#[test]
fn bg_notice_and_status_report_combined() {
    // The notice is about this tool call; the status block is about children.
    // Both belong in one additionalContext, notice first.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "tuid", 42, Some(0));

    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "long-running"},
            "tool_use_id": "tuid",
            "tool_response": {"backgroundTaskId": "bt-9", "assistantAutoBackgrounded": true}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();

    assert!(ctx.starts_with("BACKGROUNDED:"), "ctx: {ctx}");
    assert!(ctx.contains("KAIROS"), "ctx: {ctx}");
    assert!(ctx.contains("bt-9"), "ctx: {ctx}");
    // Notice and report are joined by a single space, in that order.
    assert!(ctx.contains(" [agent-tools] run status:\n"), "ctx: {ctx}");
    assert!(ctx.contains("seeded [final(0)]"), "ctx: {ctx}");
}

#[test]
fn a_non_backgroundable_tool_gets_no_backgrounded_notice() {
    // Only Bash and Monitor can be backgrounded. Every other tool is a delivery
    // point for status and nothing else, even if its response carries the field.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Grep",
            "tool_input": {"pattern": "x"},
            "tool_use_id": "toolu_now",
            "tool_response": {"backgroundTaskId": "bt-impossible"}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    assert!(
        stdout.contains("[agent-tools] run status:"),
        "stdout: {stdout}"
    );
    assert!(!stdout.contains("BACKGROUNDED"), "stdout: {stdout}");
}

#[test]
fn subagent_capture_paths_contain_agent_segment() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", Some("agent-abc"), "tuid");
    let dir = parent.join("77");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":77,"wrapper_started_ticks":1,"child_pid":4242,"desc":"sub",
                "command":["true"],"started_at":"{}","spawn_error":null,"reaped":null,
                "drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();

    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "agent_id": "agent-abc",
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "tool_use_id": "tuid",
            "tool_response": {}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(ctx.contains("/agent-abc/"), "ctx: {ctx}");
    assert!(ctx.contains(&dir.display().to_string()), "ctx: {ctx}");
}

#[test]
fn abandoned_child_is_reported_without_any_five_minute_wait() {
    // wrapper_pid 0 has no /proc entry, so the wrapper is dead. The child was
    // seeded seconds ago; the old implementation would have waited 300s.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    assert!(
        stdout.contains("[agent-tools] run status:"),
        "stdout: {stdout}"
    );
    assert!(stdout.contains("abandoned"), "stdout: {stdout}");
}

#[test]
fn the_same_key_is_never_reported_twice() {
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (_, first, _) = run_post(home.path(), post_body("Grep", "toolu_a"));
    assert!(first.contains("abandoned"));
    let (_, second, _) = run_post(home.path(), post_body("Grep", "toolu_b"));
    assert!(
        !second.contains("abandoned"),
        "second report was redundant: {second}"
    );
}

#[test]
fn a_new_key_for_a_known_child_is_reported_again() {
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, Some(0));
    let (_, first, _) = run_post(home.path(), post_body("Grep", "toolu_a"));
    assert!(first.contains("final(0)"), "stdout: {first}");
    // Same child, now unreadable meta -> abandoned, a different key.
    std::fs::remove_file(
        parent_dir(home.path(), "sid", None, "toolu_prior")
            .join("0")
            .join("meta.json"),
    )
    .unwrap();
    let (_, second, _) = run_post(home.path(), post_body("Grep", "toolu_b"));
    assert!(second.contains("abandoned"), "stdout: {second}");
}

#[test]
fn a_subagents_children_are_not_reported_to_the_main_thread() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", Some("agent-1"), "toolu_sub");
    let dir = parent.join("7");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":0,"wrapper_started_ticks":1,"child_pid":1,"desc":"subagent child",
                "command":["true"],"started_at":"{}","spawn_error":null,"reaped":null,"drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_main"));
    assert!(!stdout.contains("subagent child"), "scope leak: {stdout}");
}

#[test]
fn a_failure_event_is_answered_in_its_own_name() {
    // PostToolUse does not fire for an errored tool result; PostToolUseFailure
    // does, and a response naming the wrong event is dropped.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "hook_event_name": "PostToolUseFailure",
            "tool_name": "Bash",
            "tool_input": {"command": "false"},
            "tool_use_id": "toolu_now",
            "tool_response": {}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    assert_eq!(
        v["hookSpecificOutput"]["hookEventName"].as_str(),
        Some("PostToolUseFailure"),
        "stdout: {stdout}"
    );
}

#[test]
fn an_event_name_absent_from_the_input_falls_back_to_post_tool_use() {
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    assert_eq!(
        v["hookSpecificOutput"]["hookEventName"].as_str(),
        Some("PostToolUse"),
        "stdout: {stdout}"
    );
}

#[test]
fn lines_dropped_for_size_are_reported_later_not_lost() {
    // The bound must record only the lines it kept. If it recorded a dropped
    // line, that child's key would match forever after and its change would
    // never reach the agent. Seed far more than one report can carry and prove
    // every child lands exactly once across successive delivery points.
    const CHILDREN: u32 = 150;
    let home = tempfile::tempdir().unwrap();
    let ids: Vec<String> = (0..CHILDREN)
        .map(|i| seed(home.path(), &format!("toolu_bulk_{i:03}"), 1000 + i, None))
        .collect();

    let mut rounds: Vec<String> = Vec::new();
    for round in 0..10 {
        let (_, out, _) = run_post(home.path(), post_body("Grep", &format!("toolu_r{round}")));
        rounds.push(out);
    }
    assert!(
        rounds[0].contains("more changed, omitted for size"),
        "the first report must say it was truncated; round 0: {}",
        rounds[0]
    );

    let combined = rounds.join("\n");
    for id in &ids {
        let needle = format!("{id}/{{stdout,stderr}}");
        assert_eq!(
            combined.matches(&needle).count(),
            1,
            "child {needle} must be reported exactly once across all rounds"
        );
    }
}

#[test]
fn a_lost_ledger_says_so_before_repeating_itself() {
    // With no record of what the agent was already told, every child looks new.
    // The burst of repeats is unavoidable; being unexplained is not.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let (_, first, _) = run_post(home.path(), post_body("Grep", "toolu_a"));
    assert!(first.contains("abandoned"), "stdout: {first}");

    std::fs::write(
        home.path().join(".claude/agent-tools/sid/.reported.json"),
        b"{not json",
    )
    .unwrap();
    let (_, second, _) = run_post(home.path(), post_body("Grep", "toolu_b"));
    let note = second
        .find("report history lost")
        .unwrap_or_else(|| panic!("a reset ledger must announce itself; stdout: {second}"));
    let repeat = second
        .find("abandoned")
        .unwrap_or_else(|| panic!("the repeat itself must still happen; stdout: {second}"));
    assert!(
        note < repeat,
        "the reason must lead the repeats; stdout: {second}"
    );
}

/// Seed a capture whose rendered line alone exceeds the whole report budget.
fn seed_oversized(home: &std::path::Path, tuid: &str, wrapper_pid: u32) -> String {
    let id = seed(home, tuid, wrapper_pid, None);
    let dir = parent_dir(home, "sid", None, tuid).join(wrapper_pid.to_string());
    let meta = format!(
        r#"{{"wrapper_pid":{wrapper_pid},"wrapper_started_ticks":1,"child_pid":4242,
            "desc":"{}","command":["true"],"started_at":"{}",
            "spawn_error":null,"reaped":null,"drained_at":null}}"#,
        "x".repeat(9_500),
        chrono::Utc::now().to_rfc3339()
    );
    std::fs::write(dir.join("meta.json"), meta).unwrap();
    id
}

#[test]
fn a_short_line_after_an_oversized_one_still_fits() {
    // Scan order is the filesystem's. A child whose own line cannot fit must not
    // end the report: the ones after it in that order still have room.
    let home = tempfile::tempdir().unwrap();
    for i in 0..9u32 {
        seed_oversized(home.path(), &format!("toolu_huge_{i}"), 100 + i);
    }
    let small = seed(home.path(), "toolu_small", 200, None);

    let (_, stdout, stderr) = run_post(home.path(), post_body("Grep", "toolu_now"));
    assert!(
        stdout.contains(&format!("{small}/{{stdout,stderr}}")),
        "the small child must be reported despite the oversized ones; \nstdout: {stdout}\nstderr: {stderr}"
    );
    assert!(
        stdout.contains("9 more changed, omitted for size"),
        "every oversized line is dropped and counted; stdout: {stdout}"
    );
}

#[test]
fn a_failed_status_report_does_not_discard_the_backgrounded_notice() {
    // A directory where the lock file belongs makes Ledger::open fail. The
    // notice is computed from the tool response and owes nothing to the ledger,
    // so it must survive — and the failure must be visible, not swallowed.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_prior", 0, None);
    let scope = home.path().join(".claude/agent-tools/sid");
    std::fs::create_dir_all(scope.join(".reported.lock")).unwrap();

    let (_, stdout, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "x", "run_in_background": true},
            "tool_use_id": "toolu_now",
            "tool_response": {"backgroundTaskId": "bg_1"}
        }),
    );
    assert!(
        stdout.contains("BACKGROUNDED:"),
        "notice was lost: {stdout}"
    );
    assert!(
        stdout.contains("run status: unavailable"),
        "the reporting failure was swallowed: {stdout}"
    );
}

/// This process's own start ticks, so a fixture can name a wrapper that is
/// genuinely alive. `seed`'s hardcoded ticks never match a real process, which
/// is why every other fixture derives `abandoned`.
fn own_start_ticks() -> u64 {
    let raw = std::fs::read_to_string("/proc/self/stat").unwrap();
    let tail = raw.rsplit_once(')').unwrap().1;
    tail.split_whitespace().nth(19).unwrap().parse().unwrap()
}

/// Seed a child whose wrapper is this live test process, so it derives
/// `producing` rather than `abandoned`.
fn seed_live(home: &std::path::Path, tuid: &str) -> String {
    let pid = std::process::id();
    let parent = parent_dir(home, "sid", None, tuid);
    let dir = parent.join(pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let meta = format!(
        r#"{{"wrapper_pid":{pid},"wrapper_started_ticks":{},"child_pid":4242,
            "desc":"live child","command":["true"],"started_at":"{}",
            "spawn_error":null,"reaped":null,"drained_at":null}}"#,
        own_start_ticks(),
        chrono::Utc::now().to_rfc3339()
    );
    std::fs::write(dir.join("meta.json"), meta).unwrap();
    format!("{tuid}/{pid}")
}

#[test]
fn a_still_running_child_is_reported_after_finished_ones() {
    // Identity order alone would put the running child first. Only `rank`
    // overrides that, so an inverted or absent rank fails this test.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), "toolu_zzz_done", 7, Some(0));
    seed_live(home.path(), "toolu_aaa_running");

    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    let done = stdout
        .find("toolu_zzz_done")
        .expect("finished child reported");
    let running = stdout
        .find("toolu_aaa_running")
        .expect("running child reported");
    assert!(
        done < running,
        "a finished child must reach the agent before a still-running one: {stdout}"
    );
}

#[test]
fn report_order_is_reproducible_rather_than_filesystem_order() {
    // Seeded in reverse so creation order cannot be mistaken for sorted order.
    let home = tempfile::tempdir().unwrap();
    for i in (1..=5u32).rev() {
        seed(home.path(), &format!("toolu_{i}"), i, None);
    }
    let (_, stdout, _) = run_post(home.path(), post_body("Grep", "toolu_now"));
    let order: Vec<usize> = (1..=5u32)
        .map(|i| {
            stdout
                .find(&format!("toolu_{i}/{i}"))
                .expect("every child reported")
        })
        .collect();
    let mut sorted = order.clone();
    sorted.sort_unstable();
    assert_eq!(
        order, sorted,
        "children must appear in identity order: {stdout}"
    );
}

#[test]
fn parallel_hooks_report_each_child_exactly_once() {
    // The reason this uses a lock file at all is that concurrent tool calls must
    // not both report the same change, nor lose one another's ledger writes.
    // Only real processes exercise an flock; threads in one process cannot.
    let home = tempfile::tempdir().unwrap();
    for i in 1..=8u32 {
        seed(home.path(), &format!("toolu_prior_{i}"), i, None);
    }

    let mut kids = Vec::new();
    for i in 0..8 {
        let mut c = Command::new(bin())
            .arg("hook-post")
            .env("HOME", home.path())
            .env("CLAUDE_CONFIG_ROOT", worktree_root())
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .unwrap();
        // Close stdin immediately so all eight run at once rather than each
        // waiting for the collect loop to reach it.
        let mut si = c.stdin.take().unwrap();
        si.write_all(
            post_body("Grep", &format!("toolu_call_{i}"))
                .to_string()
                .as_bytes(),
        )
        .unwrap();
        drop(si);
        kids.push(c);
    }

    let combined = kids
        .into_iter()
        .map(|c| String::from_utf8_lossy(&c.wait_with_output().unwrap().stdout).into_owned())
        .collect::<Vec<_>>()
        .join("\n");

    for i in 1..=8u32 {
        let needle = format!("toolu_prior_{i}/{i}");
        assert_eq!(
            combined.matches(&needle).count(),
            1,
            "child {needle} must be reported exactly once across all hooks; combined:\n{combined}"
        );
    }
}
