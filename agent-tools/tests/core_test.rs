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

struct Run {
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    code: Option<i32>,
}

/// Run `script` bare, and again through `run-core`, and return both.
fn differential(script: &str) -> (Run, Run) {
    let bare = Command::new("bash").args(["-c", script]).output().unwrap();
    let tmp = tempfile::tempdir().unwrap();
    let wrapped = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "bash", "-c", script])
        .output()
        .unwrap();
    (
        Run { stdout: bare.stdout, stderr: bare.stderr, code: bare.status.code() },
        Run { stdout: wrapped.stdout, stderr: wrapped.stderr, code: wrapped.status.code() },
    )
}

fn assert_same(script: &str) {
    let (bare, wrapped) = differential(script);
    assert_eq!(bare.code, wrapped.code, "exit code differs for {script:?}");
    assert_eq!(
        String::from_utf8_lossy(&bare.stdout),
        String::from_utf8_lossy(&wrapped.stdout),
        "stdout differs for {script:?}"
    );
    assert_eq!(
        String::from_utf8_lossy(&bare.stderr),
        String::from_utf8_lossy(&wrapped.stderr),
        "stderr differs for {script:?}"
    );
}

#[test]
fn core_agrees_with_bare_on_content_and_exit_code() {
    assert_same("echo plain");
    assert_same("echo out; echo err >&2");
    assert_same("exit 3");
    assert_same("printf 'no trailing newline'");
    assert_same("for i in $(seq 1 500); do echo line-$i; done");
    assert_same("head -c 100000 /dev/zero | tr '\\0' 'x'");
}

#[test]
fn a_pipeline_inside_a_wrapped_command_still_dies_of_sigpipe() {
    // The wrapper ignores SIGPIPE for its own writes; the child must not inherit
    // that, or an inner pipeline behaves differently than it does bare. Measured
    // before this plan: bare and wrapped both exit 141 here.
    let tmp = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["run-core", "--capture-dir"])
        .arg(tmp.path().join("cap"))
        .args(["--", "bash", "-c", "yes | head -2; exit ${PIPESTATUS[0]}"])
        .output()
        .unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "y\ny\n");
    assert_eq!(
        out.status.code(),
        Some(141),
        "the inner `yes` must die of SIGPIPE, as it does bare"
    );
}

#[test]
fn core_agrees_with_bare_on_signalled_death_status() {
    let (bare, wrapped) = differential("kill -TERM $$");
    assert_eq!(bare.code, None, "bare: killed by a signal reports no code");
    assert_eq!(
        wrapped.code,
        Some(143),
        "wrapped: the spec promises 128+signum as the wrapper's own exit code"
    );
}
