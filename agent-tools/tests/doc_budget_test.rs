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
    assert!(
        stdout.contains("--print-held"),
        "stdout missing --print-held: {stdout}"
    );
    // Only the Python parser's epilog carries the exit-status table; clap's
    // help would list the flag from the doc comment and stop there.
    assert!(
        stdout.contains("exit status:"),
        "--help was answered by clap, not forwarded to Python: {stdout}"
    );
}

#[test]
fn doc_budget_forwards_flags_and_positionals_and_returns_the_modules_exit_code() {
    // clap forwards everything here (`trailing_var_arg`, `allow_hyphen_values`,
    // `disable_help_flag`), so any rejection at all proves argparse ran. Both
    // rejections happen before the registry is read or a file is tokenized, so
    // this stays a wiring test whatever `doc-budget.toml` says about the tree.
    let flag = doc_budget(&["--no-such-flag"]);
    assert_eq!(
        flag.status.code(),
        Some(2),
        "stdout={}",
        String::from_utf8_lossy(&flag.stdout)
    );
    let stderr = String::from_utf8_lossy(&flag.stderr);
    assert!(
        stderr.contains("unrecognized arguments: --no-such-flag")
            && stderr.contains("usage: doc-budget"),
        "expected argparse's rejection, got: {stderr}"
    );

    let outside = doc_budget(&["/etc"]);
    assert_eq!(
        outside.status.code(),
        Some(2),
        "stdout={}",
        String::from_utf8_lossy(&outside.stdout)
    );
    let stderr = String::from_utf8_lossy(&outside.stderr);
    assert!(
        stderr.contains("is outside"),
        "expected the module's own usage error, got: {stderr}"
    );
}
