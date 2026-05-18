use std::io::Write;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn run_post(home: &std::path::Path, body: serde_json::Value) -> (std::process::ExitStatus, String, String) {
    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin.as_mut().unwrap().write_all(body.to_string().as_bytes()).unwrap();
    let out = c.wait_with_output().unwrap();
    (out.status, String::from_utf8_lossy(&out.stdout).into_owned(), String::from_utf8_lossy(&out.stderr).into_owned())
}

/// Compute the parent dir for captures under `home` matching `paths::parent_dir_for`.
fn parent_dir(home: &std::path::Path, session: &str, agent: Option<&str>, tuid: &str) -> std::path::PathBuf {
    let mut p = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        p.push(a);
    }
    p.push(tuid);
    p
}

/// Create a `<pid>/meta.json` capture directory under `parent`, with optional desc.
fn seed_capture(parent: &std::path::Path, pid: u32, desc: Option<&str>) -> std::path::PathBuf {
    let child = parent.join(pid.to_string());
    std::fs::create_dir_all(&child).unwrap();
    let desc_json = match desc {
        Some(d) => format!("\"{d}\""),
        None => "null".to_string(),
    };
    let meta = format!(
        r#"{{"child_id":{pid},"desc":{desc_json},"command":["echo","hi"],"started_at":null,"ended_at":null,"exit_code":null}}"#
    );
    std::fs::write(child.join("meta.json"), meta).unwrap();
    child
}

#[test]
fn no_parent_dir_no_bg_emits_nothing() {
    let home = tempfile::tempdir().unwrap();
    // No parent dir created on disk.
    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    if !stdout.trim().is_empty() {
        let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
        assert!(v.get("hookSpecificOutput")
            .and_then(|h| h.get("additionalContext"))
            .is_none(), "should not emit additionalContext, got {stdout}");
    }
}

#[test]
fn two_captures_no_bg_lists_them() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    let dir1 = seed_capture(&parent, 100, Some("first"));
    let dir2 = seed_capture(&parent, 200, Some("second"));

    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("[agent-tools] captures from this Bash call:"), "ctx: {ctx}");

    // Directory-sorted order: "100" sorts before "200" lexicographically.
    let expected_first = format!("first → {}/{{stdout,stderr}}", dir1.display());
    let expected_second = format!("second → {}/{{stdout,stderr}}", dir2.display());
    let expected = format!(
        "[agent-tools] captures from this Bash call: {expected_first}; {expected_second}"
    );
    assert_eq!(ctx, expected, "ctx: {ctx}");
}

#[test]
fn bg_only_emits_only_bg_notice() {
    let home = tempfile::tempdir().unwrap();
    // No captures, but backgroundTaskId present.
    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "sleep 9999", "timeout": 5000},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-7"}
    }));
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
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

    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running"},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-9", "assistantAutoBackgrounded": true}
    }));
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();

    let captures_part = format!(
        "[agent-tools] captures from this Bash call: probe → {}/{{stdout,stderr}}",
        dir1.display()
    );
    assert!(ctx.starts_with(&captures_part), "ctx: {ctx}");
    // Captures and bg notice are joined by a single space.
    let after_captures = &ctx[captures_part.len()..];
    assert!(after_captures.starts_with(" BACKGROUNDED:"), "after: {after_captures}");
    assert!(ctx.contains("KAIROS"), "ctx: {ctx}");
    assert!(ctx.contains("bt-9"), "ctx: {ctx}");
}

#[test]
fn subagent_capture_paths_contain_agent_segment() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", Some("agent-abc"), "tuid");
    let dir1 = seed_capture(&parent, 77, Some("sub"));

    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "agent_id": "agent-abc",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
    assert!(ctx.contains("/agent-abc/"), "ctx: {ctx}");
    assert!(ctx.contains(&dir1.display().to_string()), "ctx: {ctx}");
}

#[test]
fn per_capture_format_with_and_without_desc() {
    let home = tempfile::tempdir().unwrap();
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    let dir_with = seed_capture(&parent, 100, Some("labeled"));
    let dir_without = seed_capture(&parent, 200, None);

    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hi"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();

    // With-desc branch: "<desc> → <dir>/{stdout,stderr}"
    let with_fragment = format!("labeled → {}/{{stdout,stderr}}", dir_with.display());
    assert!(ctx.contains(&with_fragment), "ctx: {ctx}");
    // Without-desc branch: bare "<dir>/{stdout,stderr}"
    let without_fragment = format!("{}/{{stdout,stderr}}", dir_without.display());
    assert!(ctx.contains(&without_fragment), "ctx: {ctx}");
    // The without-desc form must NOT be prefixed by a space-arrow construct.
    assert!(!ctx.contains(&format!("→ {without_fragment}")), "ctx: {ctx}");
}

#[test]
fn non_bash_non_monitor_emits_nothing() {
    let home = tempfile::tempdir().unwrap();
    // Even with a capture present, a Read tool call should emit no output.
    let parent = parent_dir(home.path(), "sid", None, "tuid");
    seed_capture(&parent, 1, Some("ignored"));

    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Read",
        "tool_input": {"command": "n/a"},
        "tool_use_id": "tuid",
        "tool_response": {}
    }));
    assert!(status.success(), "stderr: {stderr}");
    assert!(stdout.trim().is_empty(), "expected no stdout, got: {stdout}");
}

#[test]
fn explicit_run_in_background_is_not_reported_as_timeout() {
    // Regression (main b279c25): when tool_input.run_in_background == true,
    // BashTool returns a backgroundTaskId immediately with neither
    // assistantAutoBackgrounded nor backgroundedByUser set
    // (BashTool.tsx:989-1000). The post-hook must recognize this as an
    // intentional background, not a timeout.
    let home = tempfile::tempdir().unwrap();
    let (status, stdout, stderr) = run_post(home.path(), serde_json::json!({
        "session_id": "sid",
        "tool_name": "Bash",
        "tool_input": {"command": "long-running", "run_in_background": true},
        "tool_use_id": "tuid",
        "tool_response": {"backgroundTaskId": "bt-rib"}
    }));
    assert!(status.success(), "stderr: {stderr}");
    let v: serde_json::Value = serde_json::from_str(&stdout).unwrap();
    let ctx = v["hookSpecificOutput"]["additionalContext"].as_str().unwrap();
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
