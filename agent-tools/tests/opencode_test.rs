use std::fs;
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
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

#[test]
fn help_lists_opencode_pretty_subcommand() {
    let out = Command::new(bin()).arg("--help").output().unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("opencode-pretty"), "stdout: {stdout}");
}

#[test]
fn opencode_pretty_dispatches_to_python_module_and_forwards_args() {
    let tmp = tempfile::tempdir().unwrap();
    let root = worktree_root();
    let bindir = tmp.path().join("bin");
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
        .env("CLAUDE_CONFIG_ROOT", &root)
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
    assert!(stdout.contains("--truncate-input 100"), "stdout: {stdout}");
    assert!(stdout.contains("--no-color"), "stdout: {stdout}");
    assert!(stdout.contains("--no-thinking"), "stdout: {stdout}");
    assert!(stdout.contains("--agent subagent"), "stdout: {stdout}");
}

#[test]
fn opencode_maps_langfuse_names_sets_git_identity_and_forwards_args() {
    let tmp = tempfile::tempdir().unwrap();
    let root = worktree_root();
    let bindir = tmp.path().join("bin");
    fs::create_dir_all(&bindir).unwrap();

    // The child reports presence, not value, for the two credential variables.
    // `agent-tools opencode` reads <root>/.env, and that file is machine-local:
    // asserting exact values makes the test pass only where the file happens to
    // lack these keys, and an assertion message interpolating them prints live
    // secrets into test output. Which source wins, and what each value becomes,
    // belongs to the langfuse_env tests in src/opencode.rs, which own a fixture
    // .env they can control. What this test owns is the part those cannot see:
    // that the wrapper reaches an exec'd child at all, under the names the
    // plugin reads, carrying nothing beyond them.
    let fake_opencode = bindir.join("opencode");
    fs::write(
        &fake_opencode,
        r#"#!/usr/bin/env bash
set -euo pipefail
printf 'secret_set=%s\n' "${LANGFUSE_SECRET_KEY:+yes}"
printf 'public_set=%s\n' "${LANGFUSE_PUBLIC_KEY:+yes}"
printf 'baseurl_set=%s\n' "${LANGFUSE_BASEURL:+yes}"
printf 'base_url=%s\n' "${LANGFUSE_BASE_URL-unset}"
printf 'extra=%s\n' "${LANGFUSE_EXTRA-unset}"
printf 'author_name=%s\n' "${GIT_AUTHOR_NAME-}"
printf 'author_email=%s\n' "${GIT_AUTHOR_EMAIL-}"
printf 'committer_name=%s\n' "${GIT_COMMITTER_NAME-}"
printf 'committer_email=%s\n' "${GIT_COMMITTER_EMAIL-}"
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

    // The prefixed values are what a checkout without a .env falls back to, so
    // the presence assertions below hold on any machine.
    let out = Command::new(bin())
        .arg("opencode")
        .args(["--model", "test/model", "prompt text"])
        .env("CLAUDE_CONFIG_ROOT", &root)
        .env("PATH", path)
        .env("OPENCODE_LANGFUSE_SECRET_KEY", "secret from process env")
        .env("OPENCODE_LANGFUSE_PUBLIC_KEY", "public from process env")
        .env("OPENCODE_LANGFUSE_BASE_URL", "https://langfuse.example")
        .env("OPENCODE_LANGFUSE_EXTRA", "must not be stripped")
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
    assert!(stdout.contains("secret_set=yes"), "stdout: {stdout}");
    assert!(stdout.contains("public_set=yes"), "stdout: {stdout}");
    assert!(stdout.contains("baseurl_set=yes"), "stdout: {stdout}");
    assert!(stdout.contains("base_url=unset"), "stdout: {stdout}");
    assert!(stdout.contains("extra=unset"), "stdout: {stdout}");
    assert!(stdout.contains("author_name=opencode"), "stdout: {stdout}");
    assert!(
        stdout.contains("author_email=opencode@users.noreply.github.com"),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains("committer_name=opencode"),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains("committer_email=opencode@users.noreply.github.com"),
        "stdout: {stdout}"
    );
    assert!(
        stdout.contains("args=--model test/model prompt text"),
        "stdout: {stdout}"
    );
}

#[test]
fn opencode_gate_accepts_heredoc_input_and_prints_instructions() {
    let tmp = tempfile::tempdir().unwrap();
    let mut child = Command::new(bin())
        .arg("opencode.gate")
        .env("HOME", tmp.path())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
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
    // Don't assert specific gate-stdout content here: the prompt-coupled
    // string in main.rs evolves frequently, and pinning phrases makes
    // every prompt iteration a test edit. Coupling drift between the
    // emitter and the prompt is caught by reading both files together,
    // not by this test. Keep only the shape: nonempty stdout, clean stderr.
    assert!(!out.stdout.is_empty(), "expected nonempty gate stdout");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "");
}

#[test]
fn opencode_gate_rejects_missing_root_assertion_when_default_is_unavailable() {
    let tmp = tempfile::tempdir().unwrap();
    let out = Command::new(bin())
        .arg("opencode.gate")
        .env("HOME", tmp.path())
        .env_remove("CLAUDE_CONFIG_ROOT")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .unwrap();

    assert!(!out.status.success(), "expected failure");
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("CLAUDE_CONFIG_ROOT is unset"),
        "stderr: {stderr}"
    );
}

#[test]
fn opencode_gate_allows_unset_root_assertion_when_default_matches_binary() {
    let tmp = tempfile::tempdir().unwrap();
    let claude_dir = tmp.path().join(".claude");
    fs::create_dir_all(&claude_dir).unwrap();
    std::os::unix::fs::symlink(worktree_root().join("skills"), claude_dir.join("skills")).unwrap();

    let out = Command::new(bin())
        .arg("opencode.gate")
        .env("HOME", tmp.path())
        .env_remove("CLAUDE_CONFIG_ROOT")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    // Same reasoning as opencode_gate_accepts_heredoc_input_and_prints_instructions:
    // gate body text is prompt-coupled and evolves; assert only on shape.
    assert!(!out.stdout.is_empty(), "expected nonempty gate stdout");
}

#[test]
fn opencode_gate_rejects_mismatched_root_assertion() {
    let tmp = tempfile::tempdir().unwrap();
    let out = Command::new(bin())
        .arg("opencode.gate")
        .env("CLAUDE_CONFIG_ROOT", tmp.path())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .unwrap();

    assert!(!out.status.success(), "expected failure");
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("does not match this agent-tools binary"),
        "stderr: {stderr}"
    );
}

#[test]
fn root_flag_is_rejected() {
    let out = Command::new(bin())
        .arg("--root")
        .arg(worktree_root())
        .arg("opencode.gate")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .unwrap();

    assert!(!out.status.success(), "expected failure");
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("unexpected argument '--root'"),
        "stderr: {stderr}"
    );
}
