use std::path::PathBuf;
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf()
}

fn agent_tools() -> Command {
    let mut c = Command::new(bin());
    c.env("CLAUDE_CONFIG_ROOT", worktree_root());
    c
}

#[test]
fn run_core_forwards_both_streams_and_exit_code() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(&cap)
        .args(["--", "bash", "-c", "echo to-out; echo to-err >&2; exit 7"])
        .output()
        .unwrap();

    assert_eq!(out.status.code(), Some(7), "exit code must be the child's");
    assert_eq!(String::from_utf8_lossy(&out.stdout), "to-out\n");
    assert_eq!(String::from_utf8_lossy(&out.stderr), "to-err\n");
    assert_eq!(std::fs::read_to_string(cap.join("stdout")).unwrap(), "to-out\n");
    assert_eq!(std::fs::read_to_string(cap.join("stderr")).unwrap(), "to-err\n");
}

#[test]
fn run_core_needs_no_parent_dir_env() {
    let tmp = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "echo", "hi"])
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();

    assert_eq!(out.status.code(), Some(0));
    assert_eq!(String::from_utf8_lossy(&out.stdout), "hi\n");
}

#[test]
fn run_core_inherits_stdin() {
    use std::io::Write;
    use std::process::Stdio;
    let tmp = tempfile::tempdir().unwrap();
    let mut child = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "cat"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(b"piped\n").unwrap();
    let out = child.wait_with_output().unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "piped\n");
}
