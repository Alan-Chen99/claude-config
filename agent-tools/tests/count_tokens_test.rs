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

/// A `count-tokens` invocation with no reachable Anthropic credential.
///
/// `PYTHON_DOTENV_DISABLED=1` is honored by python-dotenv's `load_dotenv`
/// (`dotenv/main.py:412`), so the key stays unreachable even from the canonical
/// checkout, whose gitignored `.env` does carry one.
fn without_credentials(args: &[&str]) -> std::process::Output {
    Command::new(bin())
        .arg("count-tokens")
        .args(args)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("PYTHON_DOTENV_DISABLED", "1")
        .env_remove("ANTHROPIC_TOKEN_COUNT_API_KEY")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools count-tokens")
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
    for flag in ["--api", "--model", "--file"] {
        assert!(stdout.contains(flag), "stdout missing {flag}: {stdout}");
    }
    // Only the Python parser emits the epilog. Asserting on it proves --help
    // was forwarded rather than answered by clap, which would list the flags
    // from the subcommand doc comment and look identical at a glance.
    assert!(
        stdout.contains("not interchangeable"),
        "--help was answered by clap, not forwarded to Python: {stdout}"
    );
}

#[test]
fn count_tokens_defaults_to_local_and_needs_no_credentials() {
    // The whole point of the local default: a worktree has no .env, so before
    // this backend existed every invocation here died on a missing key.
    let out = without_credentials(&["hello world"]);

    assert!(
        out.status.success(),
        "expected success without credentials, exit={:?} stderr={}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    let count: u32 = stdout
        .trim()
        .parse()
        .unwrap_or_else(|e| panic!("stdout {stdout:?} is not an integer: {e}"));
    assert!(count > 0, "expected a positive count, got {count}");
}

#[test]
fn count_tokens_local_backend_reads_a_file_without_credentials() {
    let out = without_credentials(&["--file", "/etc/hostname"]);

    assert!(
        out.status.success(),
        "exit={:?} stderr={}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(
        stdout.trim().parse::<u32>().is_ok(),
        "stdout is not an integer: {stdout}"
    );
}

#[test]
fn count_tokens_file_not_found_propagates_loudly() {
    let out = without_credentials(&["--file", "/nonexistent/path/that/should/not/exist"]);

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
    let out = without_credentials(&["--file", "/etc/hostname", "inline text"]);

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
fn count_tokens_rejects_model_without_api() {
    // --model selects a Claude model, which only the API backend consults.
    // Accepting it silently would report a local count under a model name the
    // caller believes was honored.
    let out = without_credentials(&["--model", "claude-opus-5", "hello"]);

    assert!(
        !out.status.success(),
        "expected non-zero exit, got 0; stdout={}",
        String::from_utf8_lossy(&out.stdout)
    );
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("--model applies to --api only"),
        "expected the --model/--api guidance in stderr, got: {stderr}"
    );
}

#[test]
fn count_tokens_api_backend_missing_key_fails_loudly() {
    let out = without_credentials(&["--api", "hello"]);

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
