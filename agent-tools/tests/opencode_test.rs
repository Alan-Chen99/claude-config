use std::fs;
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

#[test]
fn help_lists_opencode_pretty_subcommand() {
    let out = Command::new(bin()).arg("--help").output().unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains("opencode-pretty"),
        "stdout: {stdout}"
    );
}

#[test]
fn opencode_pretty_dispatches_to_python_module_and_forwards_args() {
    let tmp = tempfile::tempdir().unwrap();
    let root = tmp.path().join("repo");
    let bindir = tmp.path().join("bin");
    fs::create_dir_all(&root).unwrap();
    fs::create_dir_all(&bindir).unwrap();

    let fake_uv = bindir.join("uv");
    fs::write(
        &fake_uv,
        r#"#!/usr/bin/env bash
set -euo pipefail
printf 'cwd=%s\n' "$PWD"
printf 'args=%s\n' "$*"
"#,
    )
    .unwrap();
    let mut perms = fs::metadata(&fake_uv).unwrap().permissions();
    perms.set_mode(0o755);
    fs::set_permissions(&fake_uv, perms).unwrap();

    let path = format!(
        "{}:{}",
        bindir.display(),
        std::env::var("PATH").unwrap_or_default()
    );

    let out = Command::new(bin())
        .arg("--root")
        .arg(PathBuf::from(&root))
        .arg("opencode-pretty")
        .args([
            "session-123",
            "--tool-max",
            "10",
            "--truncate-input",
            "100",
            "--no-color",
            "--no-thinking",
            "--agent",
            "subagent",
        ])
        .env("PATH", path)
        .output()
        .unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains(&format!("cwd={}", root.display())),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains(&format!("run --project {}", root.display())),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains("python3 -m claude_config.opencode_pretty.main"),
        "stdout: {stdout}"
    );
    assert!(stdout.contains("session-123"), "stdout: {stdout}");
    assert!(stdout.contains("--tool-max 10"), "stdout: {stdout}");
    assert!(
        stdout.contains("--truncate-input 100"),
        "stdout: {stdout}"
    );
    assert!(stdout.contains("--no-color"), "stdout: {stdout}");
    assert!(stdout.contains("--no-thinking"), "stdout: {stdout}");
    assert!(stdout.contains("--agent subagent"), "stdout: {stdout}");
}

#[test]
fn opencode_loads_prefixed_langfuse_env_and_forwards_args() {
    let tmp = tempfile::tempdir().unwrap();
    let root = tmp.path().join("repo");
    let bindir = tmp.path().join("bin");
    fs::create_dir_all(&root).unwrap();
    fs::create_dir_all(&bindir).unwrap();

    fs::write(
        root.join(".env"),
        r#"
OPENCODE_LANGFUSE_SECRET_KEY="secret from env"
OPENCODE_LANGFUSE_PUBLIC_KEY="public from env"
OPENCODE_LANGFUSE_BASE_URL="https://langfuse.example"
OPENCODE_LANGFUSE_EXTRA="must not be stripped"
"#,
    )
    .unwrap();

    let fake_opencode = bindir.join("opencode");
    fs::write(
        &fake_opencode,
        r#"#!/usr/bin/env bash
set -euo pipefail
printf 'secret=%s\n' "${LANGFUSE_SECRET_KEY-}"
printf 'public=%s\n' "${LANGFUSE_PUBLIC_KEY-}"
printf 'baseurl=%s\n' "${LANGFUSE_BASEURL-}"
printf 'base_url=%s\n' "${LANGFUSE_BASE_URL-unset}"
printf 'extra=%s\n' "${LANGFUSE_EXTRA-unset}"
printf 'args=%s\n' "$*"
"#,
    )
    .unwrap();
    let mut perms = fs::metadata(&fake_opencode).unwrap().permissions();
    perms.set_mode(0o755);
    fs::set_permissions(&fake_opencode, perms).unwrap();

    let path = format!(
        "{}:{}",
        bindir.display(),
        std::env::var("PATH").unwrap_or_default()
    );

    let out = Command::new(bin())
        .arg("--root")
        .arg(PathBuf::from(&root))
        .arg("opencode")
        .args(["--model", "test/model", "prompt text"])
        .env("PATH", path)
        .env_remove("LANGFUSE_SECRET_KEY")
        .env_remove("LANGFUSE_PUBLIC_KEY")
        .env_remove("LANGFUSE_BASEURL")
        .env_remove("LANGFUSE_BASE_URL")
        .env_remove("LANGFUSE_EXTRA")
        .output()
        .unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains("secret=secret from env"),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains("public=public from env"),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains("baseurl=https://langfuse.example"),
        "stdout: {stdout}"
    );
    assert!(stdout.contains("base_url=unset"), "stdout: {stdout}");
    assert!(stdout.contains("extra=unset"), "stdout: {stdout}");
    assert!(
        stdout.contains("args=--model test/model prompt text"),
        "stdout: {stdout}"
    );
}

#[test]
fn opencode_gate_accepts_heredoc_input_and_does_nothing() {
    let tmp = tempfile::tempdir().unwrap();
    let mut child = Command::new(bin())
        .arg("opencode.gate")
        .env("HOME", tmp.path())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();

    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(b"Gate: Iteration 1\n\n# Task\nTest\n")
        .unwrap();

    let out = child.wait_with_output().unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    assert_eq!(String::from_utf8_lossy(&out.stdout), "");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "");
}
