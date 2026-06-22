use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use serde::Deserialize;

/// Local mirror of `agent_tools::meta::ChildMeta` so the test can parse
/// `meta.json` strictly via serde without depending on the binary crate
/// (which has no `lib` target).
#[derive(Debug, Deserialize)]
struct ChildMeta {
    #[allow(dead_code)]
    child_id: u32,
    desc: Option<String>,
    #[allow(dead_code)]
    command: Vec<String>,
    #[allow(dead_code)]
    started_at: Option<String>,
    #[allow(dead_code)]
    ended_at: Option<String>,
    #[allow(dead_code)]
    exit_code: Option<i32>,
}

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

/// Directory containing the test binary; we prepend this to PATH so that
/// `agent-tools` resolved inside `bash -c <rewritten>` is the same binary
/// the test is exercising.
fn bin_dir() -> PathBuf {
    PathBuf::from(bin())
        .parent()
        .expect("bin has a parent dir")
        .to_path_buf()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

#[test]
fn full_loop_hook_pre_run_hook_post_ps() {
    let home = tempfile::tempdir().unwrap();
    let sid = "sid-e2e";
    let tuid = "tuid-e2e";
    let expected_parent: PathBuf = home.path().join(".claude/agent-tools").join(sid).join(tuid);

    let path_with_bin = format!(
        "{}:{}",
        bin_dir().display(),
        std::env::var("PATH").unwrap_or_default()
    );

    // --- Step 1: hook-pre rewrites the Bash command. -------------------------
    let orig_cmd = "agent-tools run --desc probe -- echo hi";
    let pre_input = serde_json::json!({
        "session_id": sid,
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command": orig_cmd},
        "tool_use_id": tuid,
    })
    .to_string();

    let rewritten = {
        let mut c = Command::new(bin())
            .arg("hook-pre")
            .env("HOME", home.path())
            .env("PATH", &path_with_bin)
            .env("CLAUDE_CONFIG_ROOT", worktree_root())
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        c.stdin
            .as_mut()
            .unwrap()
            .write_all(pre_input.as_bytes())
            .unwrap();
        let out = c.wait_with_output().unwrap();
        assert!(
            out.status.success(),
            "hook-pre failed; stderr: {}",
            String::from_utf8_lossy(&out.stderr)
        );
        let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
        parsed["hookSpecificOutput"]["updatedInput"]["command"]
            .as_str()
            .expect("updatedInput.command is a string")
            .to_string()
    };

    let expected_prefix = format!(
        "unset HTTPS_PROXY NODE_EXTRA_CA_CERTS NODE_OPTIONS; \
         export AGENT_TOOLS_PARENT_DIR='{}'; ",
        expected_parent.display()
    );
    assert!(
        rewritten.starts_with(&expected_prefix),
        "rewritten command missing expected env prefix\n  expected prefix: {expected_prefix}\n  got: {rewritten}"
    );
    assert!(
        rewritten.ends_with(orig_cmd),
        "rewritten command does not end with original command\n  original: {orig_cmd}\n  got: {rewritten}"
    );

    // The hook is lazy: parent dir must not exist yet.
    assert!(
        !expected_parent.exists(),
        "parent dir should not exist before `agent-tools run` runs; found {}",
        expected_parent.display()
    );

    // --- Step 2: execute the rewritten command via bash -c. ------------------
    let exec = Command::new("bash")
        .args(["-c", &rewritten])
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();
    assert!(
        exec.status.success(),
        "bash exec failed; stdout: {}; stderr: {}",
        String::from_utf8_lossy(&exec.stdout),
        String::from_utf8_lossy(&exec.stderr),
    );
    assert_eq!(
        String::from_utf8_lossy(&exec.stdout),
        "hi\n",
        "stdout from rewritten command should be `hi\\n`"
    );

    // --- Step 3: inspect on-disk capture. ------------------------------------
    assert!(
        expected_parent.is_dir(),
        "parent dir should exist after run; missing {}",
        expected_parent.display()
    );

    let pid_dirs: Vec<PathBuf> = std::fs::read_dir(&expected_parent)
        .unwrap()
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    assert_eq!(
        pid_dirs.len(),
        1,
        "expected exactly one pid subdir under {}; got {:?}",
        expected_parent.display(),
        pid_dirs
    );
    let pid_dir = &pid_dirs[0];
    let pid_name = pid_dir.file_name().unwrap().to_string_lossy().into_owned();
    assert!(
        pid_name.chars().all(|c| c.is_ascii_digit()),
        "pid subdir name must be numeric; got {pid_name}"
    );

    let captured_stdout = std::fs::read_to_string(pid_dir.join("stdout")).unwrap();
    assert_eq!(captured_stdout, "hi\n", "captured stdout mismatch");

    let meta_bytes = std::fs::read(pid_dir.join("meta.json")).unwrap();
    let meta: ChildMeta =
        serde_json::from_slice(&meta_bytes).expect("meta.json parses as ChildMeta");
    assert_eq!(
        meta.desc.as_deref(),
        Some("probe"),
        "ChildMeta.desc should be Some(\"probe\")"
    );

    // --- Step 4: hook-post lists the capture in additionalContext. ----------
    let post_input = serde_json::json!({
        "session_id": sid,
        "tool_name": "Bash",
        "tool_input": {"command": orig_cmd, "timeout": null},
        "tool_use_id": tuid,
        "tool_response": {},
    })
    .to_string();

    let mut c = Command::new(bin())
        .arg("hook-post")
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin
        .as_mut()
        .unwrap()
        .write_all(post_input.as_bytes())
        .unwrap();
    let post_out = c.wait_with_output().unwrap();
    assert!(
        post_out.status.success(),
        "hook-post failed; stderr: {}",
        String::from_utf8_lossy(&post_out.stderr)
    );
    let post_parsed: serde_json::Value = serde_json::from_slice(&post_out.stdout).unwrap();
    let ctx = post_parsed["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .expect("additionalContext is a string");
    assert!(
        ctx.contains("[agent-tools] captures from this Bash call:"),
        "additionalContext missing captures header; got: {ctx}"
    );
    // End-to-end run uses the real `agent-tools run` subprocess, so meta.json
    // is finalized with exit=0 and a real (small) duration. The bracket also
    // carries the actual stdout byte size ("hi\n" = 3 bytes) and 0B stderr.
    assert!(
        ctx.contains("probe [exit=0 "),
        "additionalContext missing `probe [exit=0 ` fragment; got: {ctx}"
    );
    assert!(
        ctx.contains("out=3B err=0B] → "),
        "additionalContext missing byte-size fragment `out=3B err=0B] → `; got: {ctx}"
    );
    assert!(
        ctx.contains("{stdout,stderr}"),
        "additionalContext missing `{{stdout,stderr}}` brace fragment; got: {ctx}"
    );

    // --- Step 5: ps --session-id lists the capture. -------------------------
    let ps_out = Command::new(bin())
        .arg("ps")
        .arg("--session-id")
        .arg(sid)
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        ps_out.status.success(),
        "ps failed; stderr: {}",
        String::from_utf8_lossy(&ps_out.stderr)
    );
    let ps_stdout = String::from_utf8_lossy(&ps_out.stdout);
    assert!(
        ps_stdout.contains(&format!("tool-use {tuid}")),
        "ps output missing `tool-use {tuid}`; got:\n{ps_stdout}"
    );
    assert!(
        ps_stdout.contains("desc:    probe") || ps_stdout.contains("desc: probe"),
        "ps output missing desc line for probe; got:\n{ps_stdout}"
    );
    assert!(
        ps_stdout.contains(&pid_name),
        "ps output missing pid `{pid_name}`; got:\n{ps_stdout}"
    );
}
