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

/// Seed one capture dir whose wrapper pid has no /proc entry, so its derived
/// status is `abandoned`.
fn seed(home: &std::path::Path, agent: Option<&str>, tuid: &str, desc: &str) {
    let mut dir = home.join(".claude/agent-tools/sid");
    if let Some(a) = agent {
        dir.push(a);
    }
    dir.push(tuid);
    dir.push("0");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":0,"wrapper_started_ticks":1,"child_pid":5,"desc":"{desc}",
                "command":["make"],"started_at":"{}","spawn_error":null,"reaped":null,"drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();
}

fn run_prompt(home: &std::path::Path, body: &str) -> (std::process::ExitStatus, String, String) {
    let mut c = Command::new(bin())
        .arg("hook-prompt")
        .env("HOME", home)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(body.as_bytes())
        .unwrap();
    let out = c.wait_with_output().unwrap();
    (
        out.status,
        String::from_utf8_lossy(&out.stdout).into_owned(),
        String::from_utf8_lossy(&out.stderr).into_owned(),
    )
}

#[test]
fn a_user_turn_carries_pending_status_changes() {
    let home = tempfile::tempdir().unwrap();
    let dir = home.path().join(".claude/agent-tools/sid/toolu_x/0");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("meta.json"),
        format!(
            r#"{{"wrapper_pid":0,"wrapper_started_ticks":1,"child_pid":5,"desc":"orphaned build",
                "command":["make"],"started_at":"{}","spawn_error":null,"reaped":null,"drained_at":null}}"#,
            chrono::Utc::now().to_rfc3339()
        ),
    )
    .unwrap();

    let mut c = Command::new(bin())
        .arg("hook-prompt")
        .env("HOME", home.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(br#"{"session_id":"sid","prompt":"hi"}"#)
        .unwrap();
    let out = c.wait_with_output().unwrap();
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("UserPromptSubmit"), "stdout: {stdout}");
    assert!(stdout.contains("orphaned build"), "stdout: {stdout}");
    assert!(stdout.contains("abandoned"), "stdout: {stdout}");
}

#[test]
fn the_report_is_carried_in_the_envelope_the_runtime_reads() {
    // Substring assertions pass on a malformed envelope, and a malformed
    // envelope delivers nothing while looking correct in a test log. The two
    // field names and the nesting are the contract with the runtime.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), None, "toolu_x", "orphaned build");
    let (status, stdout, stderr) = run_prompt(home.path(), r#"{"session_id":"sid","prompt":"hi"}"#);
    assert!(status.success(), "stderr: {stderr}");

    let v: serde_json::Value = serde_json::from_str(stdout.trim())
        .unwrap_or_else(|e| panic!("stdout is not JSON ({e}): {stdout}"));
    let hso = v
        .get("hookSpecificOutput")
        .unwrap_or_else(|| panic!("no hookSpecificOutput: {stdout}"));
    assert_eq!(
        hso.get("hookEventName").and_then(|s| s.as_str()),
        Some("UserPromptSubmit"),
        "the response must name the event it answers: {stdout}"
    );
    let ctx = hso
        .get("additionalContext")
        .and_then(|s| s.as_str())
        .unwrap_or_else(|| panic!("additionalContext must be a string: {stdout}"));
    assert!(ctx.starts_with("[agent-tools] run status:\n"), "ctx: {ctx}");
    assert!(ctx.contains("orphaned build [abandoned]"), "ctx: {ctx}");
}

#[test]
fn nothing_changed_emits_no_context_at_all() {
    // An empty report every turn is noise: the agent cannot tell "no change"
    // from "the reporter is broken" if both look like a block of text.
    let home = tempfile::tempdir().unwrap();
    std::fs::create_dir_all(home.path().join(".claude/agent-tools/sid")).unwrap();
    let (status, stdout, stderr) = run_prompt(home.path(), r#"{"session_id":"sid","prompt":"hi"}"#);
    assert!(status.success(), "stderr: {stderr}");
    assert!(
        !stdout.contains("hookSpecificOutput"),
        "an unchanged scope must emit nothing: {stdout}"
    );
    assert!(
        stdout.trim().is_empty(),
        "an unchanged scope must emit nothing: {stdout}"
    );
}

#[test]
fn the_same_change_is_not_carried_by_a_second_user_turn() {
    // The report goes through the ledger, so a change is delivered once and
    // then retired — the second turn has nothing left to say.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), None, "toolu_x", "orphaned build");
    let (_, first, _) = run_prompt(home.path(), r#"{"session_id":"sid","prompt":"hi"}"#);
    assert!(first.contains("orphaned build"), "stdout: {first}");
    let (_, second, _) = run_prompt(home.path(), r#"{"session_id":"sid","prompt":"again"}"#);
    assert!(
        !second.contains("hookSpecificOutput"),
        "the second turn repeated a retired change: {second}"
    );
}

#[test]
fn a_subagents_children_are_not_carried_by_a_user_turn() {
    // A user turn is never addressed to a subagent. Reporting a subagent's
    // child here would retire a change the subagent has not been told about.
    //
    // The main-thread child is the positive control: without it, an
    // implementation that reported nothing at all — or no `hook-prompt` at all —
    // would satisfy the negative assertion by doing nothing.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), Some("agent-1"), "toolu_sub", "subagent child");
    seed(home.path(), None, "toolu_main", "main thread child");
    let (_, stdout, _) = run_prompt(home.path(), r#"{"session_id":"sid","prompt":"hi"}"#);
    assert!(
        stdout.contains("main thread child"),
        "the main thread's own child must be reported: {stdout}"
    );
    assert!(!stdout.contains("subagent child"), "scope leak: {stdout}");

    // And the change is still pending for the subagent itself: the user turn
    // must not have retired it. Its own tool-result channel still delivers it.
    let (_, sub, _) = run_post_as(home.path(), Some("agent-1"));
    assert!(
        sub.contains("subagent child"),
        "the user turn consumed the subagent's pending report: {sub}"
    );
}

/// A `hook-post` in the given scope — the subagent's own delivery channel.
fn run_post_as(
    home: &std::path::Path,
    agent: Option<&str>,
) -> (std::process::ExitStatus, String, String) {
    let mut body = serde_json::json!({
        "session_id": "sid",
        "tool_name": "Grep",
        "tool_input": {},
        "tool_use_id": "toolu_later",
        "tool_response": {}
    });
    if let Some(a) = agent {
        body["agent_id"] = serde_json::Value::String(a.to_string());
    }
    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
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

#[test]
fn a_failed_status_report_does_not_error_the_users_turn() {
    // A directory where the lock file belongs makes Ledger::open fail. A flock
    // or disk problem has nothing to do with the user typing, so the turn keeps
    // moving and the failure is named in the context rather than raised as a
    // hook error on the user's own prompt.
    let home = tempfile::tempdir().unwrap();
    seed(home.path(), None, "toolu_x", "orphaned build");
    std::fs::create_dir_all(home.path().join(".claude/agent-tools/sid/.reported.lock")).unwrap();

    let (status, stdout, stderr) = run_prompt(home.path(), r#"{"session_id":"sid","prompt":"hi"}"#);
    assert!(
        status.success(),
        "a reporting failure must not error the user's turn: {status:?} stderr: {stderr}"
    );
    assert!(stdout.contains("UserPromptSubmit"), "stdout: {stdout}");
    assert!(
        stdout.contains("run status: unavailable"),
        "the reporting failure was swallowed: {stdout}"
    );
    assert!(
        stderr.contains("status report failed"),
        "the failure must also reach stderr: {stderr}"
    );
}
