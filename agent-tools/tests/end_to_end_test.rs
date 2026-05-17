use std::io::Write;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

#[test]
fn full_loop_hook_pre_wrap_task_run_ps() {
    let home = tempfile::tempdir().unwrap();
    let bin_dir = tempfile::tempdir().unwrap();
    let link = bin_dir.path().join("agent-tools");
    std::os::unix::fs::symlink(bin(), &link).unwrap();
    let path_with_bin = format!("{}:{}", bin_dir.path().display(), std::env::var("PATH").unwrap_or_default());

    let input = serde_json::json!({
        "session_id": "sid-e2e",
        "cwd": "/tmp",
        "tool_name": "Bash",
        "tool_input": {"command":
            "echo upstream; agent-tools run --desc inner -- bash -c 'echo inner-out; echo inner-err 1>&2'"
        },
        "tool_use_id": "tuid-e2e"
    }).to_string();
    let mut c = Command::new(bin())
        .arg("hook-pre")
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
        .spawn().unwrap();
    c.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let parsed: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let rewritten = parsed["hookSpecificOutput"]["updatedInput"]["command"].as_str().unwrap().to_string();

    let exec = Command::new("bash")
        .args(["-c", &rewritten])
        .env("HOME", home.path())
        .env("PATH", &path_with_bin)
        .output()
        .unwrap();
    assert!(exec.status.success(), "stderr: {}", String::from_utf8_lossy(&exec.stderr));
    let stdout = String::from_utf8_lossy(&exec.stdout);
    assert!(stdout.contains("upstream"));
    assert!(stdout.contains("inner-out"));
    assert!(String::from_utf8_lossy(&exec.stderr).contains("inner-err"));

    let task_dir = home.path().join(".claude/agent-tools/sid-e2e/tuid-e2e");
    let captured_stdout = std::fs::read_to_string(task_dir.join("stdout")).unwrap();
    assert!(captured_stdout.contains("upstream"));
    assert!(captured_stdout.contains("inner-out"));

    let kids: Vec<_> = std::fs::read_dir(task_dir.join("children")).unwrap()
        .filter_map(|e| e.ok().map(|e| e.path())).collect();
    assert_eq!(kids.len(), 1);
    let child_stdout = std::fs::read_to_string(kids[0].join("stdout")).unwrap();
    assert!(child_stdout.contains("inner-out"));

    let out = Command::new(bin())
        .arg("ps")
        .env("HOME", home.path())
        .env("AGENT_TOOLS_TASK_ID", &task_dir)
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid-e2e"));
    assert!(s.contains("inner"));
}
