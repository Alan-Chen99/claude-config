use std::path::PathBuf;
use std::process::{Command, Stdio};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

/// Worktree root = parent of agent-tools/ (which is CARGO_MANIFEST_DIR).
fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

#[test]
fn count_tokens_help_dispatches_to_python_and_shows_flags() {
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("--help")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens --help");

    assert!(
        out.status.success(),
        "exit={:?} stderr={}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.contains("--model"),
        "stdout missing --model: {stdout}"
    );
    assert!(stdout.contains("--file"), "stdout missing --file: {stdout}");
}

#[test]
fn count_tokens_file_not_found_propagates_loudly() {
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("--file")
        .arg("/nonexistent/path/that/should/not/exist")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens --file /nonexistent");

    assert!(
        !out.status.success(),
        "expected failure, got exit=0 stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("FileNotFoundError") || stderr.contains("/nonexistent/path"),
        "expected loud file-not-found error, got stderr: {stderr}"
    );
}

#[test]
fn count_tokens_rejects_file_plus_positional() {
    // Use an existing path so the failure is unambiguously the mutual-exclusion
    // check, not a missing-file error.
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("--file")
        .arg("/etc/hostname")
        .arg("inline text")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens --file ... TEXT");

    assert!(
        !out.status.success(),
        "expected non-zero exit, got 0; stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("mutually exclusive"),
        "expected 'mutually exclusive' in stderr, got: {stderr}"
    );
}

#[test]
fn count_tokens_missing_api_key_fails_loudly() {
    // NOTE: this test assumes the worktree does NOT have a populated
    // ANTHROPIC_TOKEN_COUNT_API_KEY in its top-level .env file. In a fresh
    // worktree, .env is gitignored and absent, so claude_config.config.load()
    // is a no-op and os.environ remains without the key.
    let out = Command::new(bin())
        .arg("count-tokens")
        .arg("hello")
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("PYTHON_DOTENV_DISABLED", "1")
        .env_remove("ANTHROPIC_TOKEN_COUNT_API_KEY")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens hello");

    assert!(
        !out.status.success(),
        "expected non-zero exit (missing API key), got 0; stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("ANTHROPIC_TOKEN_COUNT_API_KEY"),
        "expected stderr to name the missing key, got: {stderr}"
    );
}
