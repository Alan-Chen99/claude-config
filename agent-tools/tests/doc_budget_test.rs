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

fn doc_budget(args: &[&str]) -> std::process::Output {
    Command::new(bin())
        .arg("doc-budget")
        .args(args)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("failed to run agent-tools doc-budget")
}

#[test]
fn doc_budget_help_is_forwarded_to_python() {
    let out = doc_budget(&["--help"]);
    assert!(
        out.status.success(),
        "exit={:?} stderr={}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("--print-held"), "stdout missing --print-held: {stdout}");
    // Only the Python parser's epilog carries the exit-status table; clap's
    // help would list the flag from the doc comment and stop there.
    assert!(
        stdout.contains("exit status:"),
        "--help was answered by clap, not forwarded to Python: {stdout}"
    );
}

#[test]
fn doc_budget_forwards_the_modules_exit_code_and_stderr() {
    // A path that names no group is the module's own usage error: exit 2 with
    // its wording, which clap could not have produced.
    let out = doc_budget(&["nothing-here-xyz"]);
    assert_eq!(out.status.code(), Some(2), "stdout={}", String::from_utf8_lossy(&out.stdout));
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        stderr.contains("no group is named under"),
        "expected the module's usage error, got: {stderr}"
    );
}
