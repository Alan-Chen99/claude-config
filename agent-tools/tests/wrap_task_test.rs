use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn seed_task(home: &std::path::Path, session: &str, task: &str, cmd: &str) -> PathBuf {
    let dir = home.join(format!(".claude/agent-tools/{session}/{task}"));
    std::fs::create_dir_all(dir.join("children")).unwrap();
    std::fs::write(dir.join("command.sh"), cmd).unwrap();
    let meta = serde_json::json!({
        "kind":"task","session_id":session,"agent_id":null,"task_id":task,
        "tool":"Bash","tool_use_id":task,"desc":null,"cwd":"/tmp",
        "pid":null,"started_at":null,"ended_at":null,"exit_code":null,
        "silence_threshold_ms":30000
    });
    std::fs::write(dir.join("meta.json"), serde_json::to_string_pretty(&meta).unwrap()).unwrap();
    dir
}

#[test]
fn captures_stdout_and_stderr_and_exits_with_child_code() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed_task(home.path(), "sid", "tuid", "echo hello; echo oh-no 1>&2; exit 3");

    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(3), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hello\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "oh-no\n");

    let captured_stdout = std::fs::read_to_string(dir.join("stdout")).unwrap();
    let captured_stderr = std::fs::read_to_string(dir.join("stderr")).unwrap();
    assert_eq!(captured_stdout, "hello\n");
    assert_eq!(captured_stderr, "oh-no\n");

    let meta: serde_json::Value = serde_json::from_slice(&std::fs::read(dir.join("meta.json")).unwrap()).unwrap();
    assert_eq!(meta["exit_code"], 3);
    assert!(meta["started_at"].is_string());
    assert!(meta["ended_at"].is_string());
    assert!(meta["pid"].is_number());

    let evts = std::fs::read_to_string(dir.join("events.jsonl")).unwrap();
    assert!(evts.contains("\"task_started\""));
    assert!(evts.contains("\"task_exit\""));
}

#[test]
fn propagates_task_id_env_to_child() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed_task(home.path(), "sid", "tuid",
        r#"echo "ATID=$AGENT_TOOLS_TASK_ID""#);
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_TASK_ID")
        .output()
        .unwrap();
    assert!(out.status.success());
    let s = String::from_utf8_lossy(&out.stdout).into_owned();
    assert!(s.contains(dir.to_str().unwrap()), "got: {s}");
}

#[test]
fn captures_unbuffered_streaming_output() {
    let home = tempfile::tempdir().unwrap();
    let dir = seed_task(home.path(), "sid", "tuid",
        r#"echo first; sleep 1; echo second"#);
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let captured = std::fs::read_to_string(dir.join("stdout")).unwrap();
    assert_eq!(captured, "first\nsecond\n");
}

#[test]
fn missing_command_sh_exits_nonzero() {
    let home = tempfile::tempdir().unwrap();
    let dir = home.path().join(".claude/agent-tools/sid/tuid");
    std::fs::create_dir_all(&dir).unwrap();
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(!out.status.success());
}

#[test]
fn unsets_mitm_intercept_env_in_child() {
    // Mirrors /workspace/scripts/claude.sh exports: HTTPS_PROXY,
    // NODE_EXTRA_CA_CERTS, NODE_OPTIONS — the three vars set when running
    // claude through the MITM intercept proxy.
    let home = tempfile::tempdir().unwrap();
    let script = r#"
echo "HTTPS_PROXY=[${HTTPS_PROXY-unset}]"
echo "NODE_EXTRA_CA_CERTS=[${NODE_EXTRA_CA_CERTS-unset}]"
echo "NODE_OPTIONS=[${NODE_OPTIONS-unset}]"
"#;
    let dir = seed_task(home.path(), "sid", "tuid", script);
    let out = Command::new(bin())
        .args(["wrap-task", dir.to_str().unwrap()])
        .env("HOME", home.path())
        .env("HTTPS_PROXY", "http://127.0.0.1:9160")
        .env("NODE_EXTRA_CA_CERTS", "/root/.mitmproxy/mitmproxy-ca-cert.pem")
        .env("NODE_OPTIONS", "--use-env-proxy")
        .output()
        .unwrap();
    assert!(out.status.success(), "stderr: {}", String::from_utf8_lossy(&out.stderr));
    let s = String::from_utf8_lossy(&out.stdout);
    let expected = "\
HTTPS_PROXY=[unset]\n\
NODE_EXTRA_CA_CERTS=[unset]\n\
NODE_OPTIONS=[unset]\n";
    assert_eq!(s, expected, "child saw MITM intercept env it should not have seen");
}
