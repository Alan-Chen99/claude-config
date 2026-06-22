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

/// Create a finalized `<pid>/meta.json` capture directory under `parent`, with
/// optional desc. Production current-call captures are always finalized by the
/// time the post-hook reads them (the agent-tools run subprocess has exited),
/// so seed the same shape: `exit_code:0`. The unfinalized path is tested
/// separately by `stale_in_flight_child_surfaces_with_unfinalized_annotation`.
fn seed_capture(parent: &std::path::Path, pid: u32, desc: Option<&str>) -> std::path::PathBuf {
    let child = parent.join(pid.to_string());
    std::fs::create_dir_all(&child).unwrap();
    let desc_json = match desc {
        Some(d) => format!("\"{d}\""),
        None => "null".to_string(),
    };
    let meta = format!(
        r#"{{"child_id":{pid},"desc":{desc_json},"command":["echo","hi"],"started_at":null,"ended_at":null,"exit_code":0}}"#
    );
    std::fs::write(child.join("meta.json"), meta).unwrap();
    child
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
fn two_captures_no_bg_lists_them() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    let dir1 = seed_capture(&parent, 100, Some("first"));
    let dir2 = seed_capture(&parent, 200, Some("second"));

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
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(
        ctx.contains("[agent-tools] captures from this Bash call:"),
        "ctx: {ctx}"
    );

    // Directory-sorted order: "100" sorts before "200" lexicographically.
    // Per-capture details bracket carries exit code, duration (omitted here
    // because seed_capture writes null timestamps), and out/err byte sizes.
    let expected_first = format!(
        "first [exit=0 out=0B err=0B] → {}/{{stdout,stderr}}",
        dir1.display()
    );
    let expected_second = format!(
        "second [exit=0 out=0B err=0B] → {}/{{stdout,stderr}}",
        dir2.display()
    );
    let expected =
        format!("[agent-tools] captures from this Bash call: {expected_first}; {expected_second}");
    assert_eq!(ctx, expected, "ctx: {ctx}");
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
fn captures_and_bg_combined() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    let dir1 = seed_capture(&parent, 42, Some("probe"));

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

    let captures_part = format!(
        "[agent-tools] captures from this Bash call: probe [exit=0 out=0B err=0B] → {}/{{stdout,stderr}}",
        dir1.display()
    );
    assert!(ctx.starts_with(&captures_part), "ctx: {ctx}");
    // Captures and bg notice are joined by a single space.
    let after_captures = &ctx[captures_part.len()..];
    assert!(
        after_captures.starts_with(" BACKGROUNDED:"),
        "after: {after_captures}"
    );
    assert!(ctx.contains("KAIROS"), "ctx: {ctx}");
    assert!(ctx.contains("bt-9"), "ctx: {ctx}");
}

#[test]
fn subagent_capture_paths_contain_agent_segment() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", Some("agent-abc"), "tuid");
    let dir1 = seed_capture(&parent, 77, Some("sub"));

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
    assert!(ctx.contains(&dir1.display().to_string()), "ctx: {ctx}");
}

#[test]
fn per_capture_format_with_and_without_desc() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    let dir_with = seed_capture(&parent, 100, Some("labeled"));
    let dir_without = seed_capture(&parent, 200, None);

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
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();

    // With-desc branch: "<desc> [details] → <dir>/{stdout,stderr}".
    let with_fragment = format!(
        "labeled [exit=0 out=0B err=0B] → {}/{{stdout,stderr}}",
        dir_with.display()
    );
    assert!(ctx.contains(&with_fragment), "ctx: {ctx}");
    // Without-desc branch: details bracket replaces the missing label, so the
    // line starts directly with `[`. Result: "[details] → <dir>/{stdout,stderr}".
    let without_fragment = format!(
        "[exit=0 out=0B err=0B] → {}/{{stdout,stderr}}",
        dir_without.display()
    );
    assert!(ctx.contains(&without_fragment), "ctx: {ctx}");
    // The without-desc form must NOT be preceded by a bare " → " (which would
    // mean an empty label slot was joined with an arrow). The listing
    // delimiter is "; " — verify that's what precedes the bracket.
    assert!(
        !ctx.contains(&format!(
            " → [exit=0 out=0B err=0B] → {}",
            dir_without.display()
        )),
        "without-desc form must not be preceded by a bare arrow; ctx: {ctx}"
    );
}

#[test]
fn unmatched_tool_emits_nothing() {
    // Edit/Write/Grep/etc. are not in the matcher set; the hook returns
    // early. Even with a capture present, no output is emitted.
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    seed_capture(&parent, 1, Some("ignored"));

    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Edit",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid",
            "tool_response": {}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    assert!(
        stdout.trim().is_empty(),
        "expected no stdout, got: {stdout}"
    );
}

#[test]
fn read_with_no_prior_bg_emits_nothing() {
    // Read IS in the matcher set (it triggers the late-capture scan), but
    // when there is no prior backgrounded toolu_id in scope, scan finds
    // nothing and the hook emits no additionalContext.
    let home = tempfile::tempdir().unwrap();
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-read",
            "tool_response": {}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    assert!(
        stdout.trim().is_empty(),
        "expected no stdout, got: {stdout}"
    );
}

/// Helper: append a JSONL event under <toolu_dir>/events.jsonl.
fn append_event(
    toolu_dir: &std::path::Path,
    ts: chrono::DateTime<chrono::Utc>,
    kind: &str,
    data: serde_json::Value,
) {
    use std::io::Write as _;
    std::fs::create_dir_all(toolu_dir).unwrap();
    let path = toolu_dir.join("events.jsonl");
    let line = serde_json::to_string(&serde_json::json!({
        "ts": ts,
        "kind": kind,
        "data": data,
    }))
    .unwrap();
    let mut f = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap();
    writeln!(f, "{line}").unwrap();
}

/// Helper: seed a finalized child (started + exited) in a prior toolu_dir.
/// Creates the events.jsonl entries AND the <pid>/meta.json so the scan can
/// pull the desc from either source.
fn seed_finalized_child(toolu_dir: &std::path::Path, pid: i64, desc: &str) {
    let started_ts = chrono::Utc::now() - chrono::Duration::seconds(30);
    let exited_ts = chrono::Utc::now() - chrono::Duration::seconds(20);
    append_event(
        toolu_dir,
        started_ts,
        "child_started",
        serde_json::json!({"child_pid": pid, "desc": desc, "command": ["echo", "hi"]}),
    );
    append_event(
        toolu_dir,
        exited_ts,
        "child_exit",
        serde_json::json!({"child_pid": pid, "exit_code": 0}),
    );
    let child = toolu_dir.join(pid.to_string());
    std::fs::create_dir_all(&child).unwrap();
    let meta = format!(
        r#"{{"child_id":{pid},"desc":"{desc}","command":["echo","hi"],"started_at":null,"ended_at":null,"exit_code":0}}"#
    );
    std::fs::write(child.join("meta.json"), meta).unwrap();
}

#[test]
fn read_surfaces_late_captures_from_prior_backgrounded_call() {
    let home = tempfile::tempdir().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid");
    let prior_toolu = scope.join("toolu_prior");
    seed_finalized_child(&prior_toolu, 4242, "stage2-later");

    // A Read tool call AFTER the prior backgrounded call's late wrap exited.
    let (status, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-read",
            "tool_response": {}
        }),
    );
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(
        ctx.contains("Late captures from prior backgrounded call toolu_prior:"),
        "ctx: {ctx}"
    );
    assert!(ctx.contains("stage2-later"), "ctx: {ctx}");
    let expected_path = format!("{}/{{stdout,stderr}}", prior_toolu.join("4242").display());
    assert!(ctx.contains(&expected_path), "ctx: {ctx}");
}

#[test]
fn second_hook_fire_does_not_reemit_late_capture() {
    // Ledger dedup: once a child PID is surfaced, subsequent hooks must
    // not list it again.
    let home = tempfile::tempdir().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid");
    let prior_toolu = scope.join("toolu_prior");
    seed_finalized_child(&prior_toolu, 1111, "only-once");

    let payload = serde_json::json!({
        "session_id": "sid",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x"},
        "tool_use_id": "tuid-r1",
        "tool_response": {}
    });
    let (_, stdout1, _) = run_post(home.path(), payload.clone());
    assert!(
        stdout1.contains("only-once"),
        "first fire should emit: {stdout1}"
    );

    // Second fire with a DIFFERENT tool_use_id (so the current-call dedup
    // doesn't mask the test). The ledger entry from the first fire should
    // make the second fire skip the late capture.
    let payload2 = serde_json::json!({
        "session_id": "sid",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x"},
        "tool_use_id": "tuid-r2",
        "tool_response": {}
    });
    let (_, stdout2, _) = run_post(home.path(), payload2);
    assert!(
        !stdout2.contains("only-once"),
        "second fire must not re-emit: {stdout2}"
    );
}

#[test]
fn in_flight_child_without_exit_is_skipped() {
    // child_started present but no child_exit yet, and the start is recent
    // (< 5min stale threshold) → scan skips, no emission this fire.
    let home = tempfile::tempdir().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid");
    let prior_toolu = scope.join("toolu_prior");
    let recent_ts = chrono::Utc::now() - chrono::Duration::seconds(10);
    append_event(
        &prior_toolu,
        recent_ts,
        "child_started",
        serde_json::json!({"child_pid": 7777, "desc": "still-running"}),
    );

    let (_, stdout, stderr) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-r",
            "tool_response": {}
        }),
    );
    assert!(
        !stdout.contains("Late captures"),
        "in-flight child must not emit: {stdout} | stderr: {stderr}"
    );
}

#[test]
fn stale_in_flight_child_surfaces_with_unfinalized_annotation() {
    // child_started older than 5min with no child_exit → emitted with
    // [unfinalized] suffix, covering SIGKILL / host-shutdown cases.
    let home = tempfile::tempdir().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid");
    let prior_toolu = scope.join("toolu_prior");
    let old_ts = chrono::Utc::now() - chrono::Duration::seconds(400);
    append_event(
        &prior_toolu,
        old_ts,
        "child_started",
        serde_json::json!({"child_pid": 8888, "desc": "abandoned"}),
    );

    let (_, stdout, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-r",
            "tool_response": {}
        }),
    );
    assert!(
        stdout.contains("Late captures from prior backgrounded call toolu_prior:"),
        "stdout: {stdout}"
    );
    // No meta.json is written for this test (only events.jsonl), so the
    // details bracket has no exit/duration — just the forced unfinalized
    // marker plus byte sizes from the missing stdout/stderr files.
    assert!(
        stdout.contains("abandoned [unfinalized out=0B err=0B]"),
        "stdout: {stdout}"
    );
}

#[test]
fn bash_call_seeds_ledger_with_its_own_pids() {
    // The hook for a Bash call must record its captures' PIDs in the
    // ledger under its own tool_use_id, so a later hook firing with a
    // DIFFERENT tool_use_id does not surface them as "late captures from
    // prior backgrounded call <this-bash>".
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid-bash");
    let _dir1 = seed_capture(&parent, 555, Some("bash-cap"));
    // Also write events.jsonl so the dir is recognized as a wrap-parent on
    // later scans.
    append_event(
        &parent,
        chrono::Utc::now() - chrono::Duration::seconds(60),
        "child_started",
        serde_json::json!({"child_pid": 555, "desc": "bash-cap"}),
    );
    append_event(
        &parent,
        chrono::Utc::now() - chrono::Duration::seconds(50),
        "child_exit",
        serde_json::json!({"child_pid": 555, "exit_code": 0}),
    );

    // First hook fire: the Bash call lists its own capture.
    let (_, stdout1, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
            "tool_use_id": "tuid-bash",
            "tool_response": {}
        }),
    );
    assert!(
        stdout1.contains("[agent-tools] captures from this Bash call:"),
        "stdout1: {stdout1}"
    );
    assert!(stdout1.contains("bash-cap"), "stdout1: {stdout1}");
    // The seed should have happened — the late-capture section must NOT
    // appear for this same call.
    assert!(!stdout1.contains("Late captures"), "stdout1: {stdout1}");

    // Second hook fire under a different tool_use_id. Without seeding, the
    // scan would now find PID 555 unsurfaced and re-emit it as a late
    // capture from toolu_bash. With seeding, it stays silent.
    let (_, stdout2, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-other",
            "tool_response": {}
        }),
    );
    assert!(
        !stdout2.contains("Late captures"),
        "ledger seed failed; second hook re-emitted: {stdout2}"
    );
}

#[test]
fn subagent_scope_isolated_from_main_thread() {
    // A main-thread Read should NOT see captures from a subagent's prior
    // backgrounded call, and vice versa — the per-scope ledger lives under
    // <session>/<agent_id>/ and the scan walks only that scope.
    let home = tempfile::tempdir().unwrap();
    let sub_scope = home.path().join(".claude/agent-tools/sid/agent-abc");
    let sub_toolu = sub_scope.join("toolu_sub_prior");
    seed_finalized_child(&sub_toolu, 333, "subagent-late");

    // Main-thread Read: scope is <sid>/, which contains the subagent dir
    // "agent-abc/" but that dir has no events.jsonl directly inside, so
    // scan_priors filters it out. Main thread sees nothing.
    let (_, stdout_main, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-main",
            "tool_response": {}
        }),
    );
    assert!(
        !stdout_main.contains("subagent-late"),
        "main thread saw subagent capture: {stdout_main}"
    );

    // Subagent Read in its own scope: sees the late capture.
    let (_, stdout_sub, _) = run_post(
        home.path(),
        serde_json::json!({
            "session_id": "sid",
            "agent_id": "agent-abc",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x"},
            "tool_use_id": "tuid-sub",
            "tool_response": {}
        }),
    );
    assert!(
        stdout_sub.contains("subagent-late"),
        "stdout_sub: {stdout_sub}"
    );
    assert!(
        stdout_sub.contains("toolu_sub_prior"),
        "stdout_sub: {stdout_sub}"
    );
}

#[test]
fn parallel_hooks_emit_late_capture_at_most_once() {
    // Two hook processes firing concurrently for different tool_use_ids
    // must not both surface the same prior late capture. The per-scope
    // flock around the ledger read-modify-write serializes them; one
    // emits, the other skips.
    let home = tempfile::tempdir().unwrap();
    let scope = home.path().join(".claude/agent-tools/sid");
    let prior_toolu = scope.join("toolu_prior");
    seed_finalized_child(&prior_toolu, 9999, "race-target");

    let body_a = serde_json::json!({
        "session_id": "sid",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x"},
        "tool_use_id": "tuid-parA",
        "tool_response": {}
    });
    let body_b = serde_json::json!({
        "session_id": "sid",
        "tool_name": "Read",
        "tool_input": {"file_path": "/tmp/x"},
        "tool_use_id": "tuid-parB",
        "tool_response": {}
    });
    // Spawn two hook subprocesses without waiting between them.
    let home_path = home.path().to_path_buf();
    let h1 = std::thread::spawn({
        let home_path = home_path.clone();
        move || run_post(&home_path, body_a)
    });
    let h2 = std::thread::spawn(move || run_post(&home_path, body_b));
    let (_, out_a, _) = h1.join().unwrap();
    let (_, out_b, _) = h2.join().unwrap();

    let a_emits = out_a.contains("race-target");
    let b_emits = out_b.contains("race-target");
    assert!(
        a_emits ^ b_emits,
        "exactly one of the parallel hooks must emit the late capture; \
         a_emits={a_emits} b_emits={b_emits}\nout_a: {out_a}\nout_b: {out_b}"
    );
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
