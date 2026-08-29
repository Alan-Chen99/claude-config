use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use serde::Deserialize;

/// Local mirror of `agent_tools::meta::Reaped`.
#[derive(Debug, Deserialize)]
struct Reaped {
    #[allow(dead_code)]
    at: String,
    status: i32,
}

/// Local mirror of `agent_tools::meta::ChildMeta` so the test can parse
/// `meta.json` strictly via serde without depending on the binary crate
/// (which has no `lib` target).
///
/// Every field is required, so this fails loudly if `run` stops writing one of
/// the facts every reader derives status from. The meta parsed below is the one
/// the real `agent-tools run` subprocess wrote, not a fixture.
#[derive(Debug, Deserialize)]
struct ChildMeta {
    wrapper_pid: u32,
    wrapper_started_ticks: u64,
    child_pid: Option<u32>,
    desc: Option<String>,
    command: Vec<String>,
    started_at: String,
    spawn_error: Option<String>,
    reaped: Option<Reaped>,
    drained_at: Option<String>,
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
    assert_eq!(meta.command, vec!["echo".to_string(), "hi".to_string()]);
    assert!(!meta.started_at.is_empty(), "started_at must be recorded");
    // The capture dir is named for the wrapper, and the record says so itself.
    assert_eq!(
        meta.wrapper_pid.to_string(),
        pid_name,
        "capture dir name must be the wrapper pid it records"
    );
    // Liveness is decided by (wrapper_pid, wrapper_started_ticks); a zero here
    // would make every wrapper look like every other one after a pid wrap.
    assert!(
        meta.wrapper_started_ticks > 0,
        "wrapper start ticks must be real; got {}",
        meta.wrapper_started_ticks
    );
    assert!(
        meta.child_pid.is_some_and(|c| c != meta.wrapper_pid),
        "child pid must be the spawned child, not the wrapper; got {:?}",
        meta.child_pid
    );
    assert!(meta.spawn_error.is_none(), "echo hi should have spawned");
    // Reaped and drained are both recorded before the wrapper exits, so this
    // capture is `final(0)` — which is what the two readers below must say.
    assert_eq!(
        meta.reaped.as_ref().map(|r| r.status),
        Some(0),
        "reap status should be 0"
    );
    assert!(meta.drained_at.is_some(), "drain time should be recorded");

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
        ctx.contains("[agent-tools] run status @ "),
        "additionalContext missing status header; got: {ctx}"
    );
    // The wrapper exited, so it is reaped, drained, and dead: `final(0)`. The
    // line also carries the actual stdout byte size ("hi\n" = 3 bytes) and 0B
    // stderr, and this is the child's first report, so nothing deduplicates it.
    assert!(
        ctx.contains("probe [final(0)] pid "),
        "additionalContext missing `probe [final(0)] pid ` fragment; got: {ctx}"
    );
    // `.output()` hands the wrapper two pipes, so the merge rule splits — and
    // bare would have kept those two streams apart too, so nothing was lost and
    // the line says nothing about it. The `-> ` sitting directly against the
    // byte counts is what pins that: the notes segment lands between them, so a
    // note reappearing here fails on the real wrapper run rather than only on a
    // hand-written `meta.json`.
    assert!(
        ctx.contains("out=3B err=0B -> "),
        "additionalContext missing byte-size fragment \
         `out=3B err=0B -> `; got: {ctx}"
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
    // Same derivation as the report above, reached without the ledger — and
    // reached with hook-post's ledger files now sitting in the session dir,
    // which the capture walk must step over rather than trip on.
    assert!(
        ps_stdout.contains("probe [final(0)]"),
        "ps output missing derived status for probe; got:\n{ps_stdout}"
    );
    // What a size-capped report leaves out: the full command, the wrapper pid,
    // and the start time.
    assert!(
        ps_stdout.contains("cmd:     echo hi"),
        "ps output missing the full command; got:\n{ps_stdout}"
    );
    assert!(
        ps_stdout.contains(&format!("wrapper: pid {pid_name}")),
        "ps output missing wrapper pid `{pid_name}`; got:\n{ps_stdout}"
    );
    assert!(
        ps_stdout.contains("started: "),
        "ps output missing start time; got:\n{ps_stdout}"
    );
}
