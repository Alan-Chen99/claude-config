use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

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

/// The `run-core` invocation, in one place. `argv` is the command after `--`;
/// stdio stays the caller's to wire, since where the caller's own two
/// descriptors point is itself under test.
fn run_core_cmd(capture_dir: &Path, argv: &[&str]) -> Command {
    let mut c = agent_tools();
    c.args(["run-core", "--capture-dir"])
        .arg(capture_dir)
        .arg("--")
        .args(argv);
    c
}

#[test]
fn run_core_forwards_both_streams_and_exit_code() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let out = run_core_cmd(&cap, &["bash", "-c", "echo to-out; echo to-err >&2; exit 7"])
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
    let out = run_core_cmd(&tmp.path().join("cap"), &["echo", "hi"])
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
    let mut child = run_core_cmd(&tmp.path().join("cap"), &["cat"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(b"piped\n").unwrap();
    let out = child.wait_with_output().unwrap();
    assert_eq!(String::from_utf8_lossy(&out.stdout), "piped\n");
}

/// One side of a differential run: the bytes that reached the caller's own two
/// streams, and the exit status the caller saw. The capture on disk is separate,
/// and outlives the call under the `capture_dir` its caller owns.
struct Captured {
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    code: Option<i32>,
}

/// Run `script` bare, and again through `run-core` capturing under `capture_dir`,
/// and return both. `capture_dir` belongs to the caller, so what landed on disk
/// can be compared against what was forwarded.
fn differential(script: &str, capture_dir: &Path) -> (Captured, Captured) {
    // Both sides get the same environment: the only difference between them must
    // be the wrapper itself.
    let bare = Command::new("bash")
        .args(["-c", script])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap();
    let wrapped = run_core_cmd(capture_dir, &["bash", "-c", script])
        .output()
        .unwrap();
    (
        Captured { stdout: bare.stdout, stderr: bare.stderr, code: bare.status.code() },
        Captured { stdout: wrapped.stdout, stderr: wrapped.stderr, code: wrapped.status.code() },
    )
}

/// Compare on bytes, report as text. The guarantee under test is "unmodified and
/// in order", and `from_utf8_lossy` maps every invalid sequence onto the same
/// replacement character — so comparing rendered strings would accept a wrapper
/// that reordered bytes inside invalid UTF-8.
fn assert_same(script: &str) {
    let tmp = tempfile::tempdir().unwrap();
    let (bare, wrapped) = differential(script, &tmp.path().join("cap"));
    assert_eq!(bare.code, wrapped.code, "exit code differs for {script:?}");
    assert_stream_same("stdout", script, &bare.stdout, &wrapped.stdout);
    assert_stream_same("stderr", script, &bare.stderr, &wrapped.stderr);
}

/// Where the two streams part, in bytes. The renderings cannot always show it:
/// bytes no `String` can hold render the same on both sides.
fn first_difference(bare: &[u8], wrapped: &[u8]) -> String {
    match bare.iter().zip(wrapped).position(|(a, b)| a != b) {
        Some(i) => format!(
            "first difference at byte {i}: bare {:#04x}, wrapped {:#04x}",
            bare[i], wrapped[i]
        ),
        None => format!("equal for {} bytes, then one side ends", bare.len().min(wrapped.len())),
    }
}

fn assert_stream_same(stream: &str, script: &str, bare: &[u8], wrapped: &[u8]) {
    assert!(
        bare == wrapped,
        "{stream} differs for {script:?}\n  {}\n  bare    ({} bytes): {}\n  wrapped ({} bytes): {}",
        first_difference(bare, wrapped),
        bare.len(),
        preview(bare),
        wrapped.len(),
        preview(wrapped)
    );
}

/// Render a stream for a failure message, capped. A mismatch on the 100 KB case
/// would otherwise put 200 KB into the panic, burying every other failure in the
/// run. The offset and the two lengths above already carry the answer, so the
/// rendering only has to be recognizable.
fn preview(bytes: &[u8]) -> String {
    const MAX: usize = 200;
    if bytes.len() <= MAX {
        return format!("{:?}", String::from_utf8_lossy(bytes));
    }
    format!(
        "{:?}… ({} more bytes)",
        String::from_utf8_lossy(&bytes[..MAX]),
        bytes.len() - MAX
    )
}

#[test]
fn core_agrees_with_bare_on_content_and_exit_code() {
    assert_same("echo plain");
    assert_same("echo out; echo err >&2");
    assert_same("exit 3");
    assert_same("printf 'no trailing newline'");
    assert_same("for i in $(seq 1 500); do echo line-$i; done");
    assert_same("head -c 100000 /dev/zero | tr '\\0' 'x'");
    // Invalid UTF-8: bytes the lossy rendering cannot tell apart.
    assert_same("printf '\\xff\\xfe\\xfd'");
}

#[test]
fn a_pipeline_inside_a_wrapped_command_still_dies_of_sigpipe() {
    // The wrapper ignores SIGPIPE for its own writes; the child must not inherit
    // that, or an inner pipeline behaves differently than it does bare. `head`
    // closes the pipe after two lines and `yes` dies of SIGPIPE, so
    // `PIPESTATUS[0]` is 128 + 13 on both sides.
    assert_same("yes | head -2; exit ${PIPESTATUS[0]}");
}

#[test]
fn core_agrees_with_bare_on_signalled_death_status() {
    let tmp = tempfile::tempdir().unwrap();
    let (bare, wrapped) = differential("kill -TERM $$", &tmp.path().join("cap"));
    assert_eq!(bare.code, None, "bare: killed by a signal reports no code");
    assert_eq!(
        wrapped.code,
        Some(143),
        "wrapped: the spec promises 128+signum as the wrapper's own exit code"
    );
}

/// Both of the caller's own descriptors on one appending file, which is what
/// the merge rule admits and what the Claude Code Bash tool presents.
fn one_appending_file(path: &Path) -> (Stdio, Stdio) {
    let f = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .unwrap();
    let f2 = f.try_clone().unwrap();
    (Stdio::from(f), Stdio::from(f2))
}

/// Run `script` with both of the caller's own descriptors on one appending file:
/// the shape the merge rule admits, and the shape the Claude Code Bash tool has.
/// The returned `TempDir` keeps `cap/` alive so the capture can be inspected.
fn run_core_to_one_appending_file(script: &str) -> (String, tempfile::TempDir) {
    let tmp = tempfile::tempdir().unwrap();
    let sink = tmp.path().join("caller.log");
    let (out, err) = one_appending_file(&sink);
    let status = run_core_cmd(&tmp.path().join("cap"), &["bash", "-c", script])
        .stdout(out)
        .stderr(err)
        .status()
        .unwrap();
    assert!(status.code().is_some());
    (std::fs::read_to_string(&sink).unwrap(), tmp)
}

#[test]
fn merged_streams_keep_their_relative_order() {
    let script = "for i in $(seq 1 200); do echo out-$i; echo err-$i >&2; done";
    let (text, _tmp) = run_core_to_one_appending_file(script);
    let lines: Vec<&str> = text.lines().collect();
    assert_eq!(lines.len(), 400, "every line arrives exactly once");
    for i in 0..200 {
        assert_eq!(lines[i * 2], format!("out-{}", i + 1));
        assert_eq!(lines[i * 2 + 1], format!("err-{}", i + 1));
    }
}

#[test]
fn merged_capture_holds_one_file_and_no_empty_stderr() {
    let (_text, tmp) = run_core_to_one_appending_file("echo a; echo b >&2");
    let cap = tmp.path().join("cap");
    let merged = std::fs::read_to_string(cap.join("output")).unwrap();
    assert_eq!(merged, "a\nb\n");
    assert!(
        !cap.join("stderr").exists(),
        "an empty stderr file would read as 'no diagnostics'"
    );
    assert!(!cap.join("stdout").exists());
}

#[test]
fn split_capture_holds_two_files() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    run_core_cmd(&cap, &["bash", "-c", "echo a; echo b >&2"])
        .output()
        .unwrap();
    assert_eq!(std::fs::read_to_string(cap.join("stdout")).unwrap(), "a\n");
    assert_eq!(std::fs::read_to_string(cap.join("stderr")).unwrap(), "b\n");
    assert!(!cap.join("output").exists());
}

#[test]
fn long_lines_survive_the_merge_uncorrupted() {
    // The splice has to be forced. A long line crosses several of the tee's
    // 8192-byte reads, and the other stream has to land a write between two of
    // them, which only happens while the gap between the child's own two writes
    // stays under roughly 50 us. One command substitution inside the loop is
    // twenty times that by itself, so the long line is built once and the loop
    // runs on builtins alone.
    let script = "long=$(printf 'O%.0s' $(seq 1 12000)); i=0; \
                  while ((i<200)); do echo \"$long\"; echo E >&2; ((i++)); done";
    let (text, _tmp) = run_core_to_one_appending_file(script);
    let (mut long_lines, mut short_lines) = (0, 0);
    for line in text.lines() {
        let first = *line
            .as_bytes()
            .first()
            .expect("an empty line means one write was split in two");
        assert!(
            line.bytes().all(|b| b == first),
            "a line mixing O and E is two writes spliced together"
        );
        if first == b'O' {
            assert_eq!(line.len(), 12000, "a spliced line means the merge failed");
            long_lines += 1;
        } else {
            assert_eq!(line, "E", "a spliced line means the merge failed");
            short_lines += 1;
        }
    }
    assert_eq!((long_lines, short_lines), (200, 200), "every line arrives whole, exactly once");
}

/// A child that closes its own stdout and stderr, leaving behind a descendant
/// that inherited neither, is done as far as its streams are concerned. Bare
/// returns at once and so must the wrapper.
///
/// This guards two single lines of the merged path that nothing else can see.
/// The pipe is created with `O_CLOEXEC`, so the descriptors the child was
/// spawned with do not survive into a descendant; and the `Command` is dropped
/// once the child holds its own, so the wrapper is not left holding a write end
/// itself. Take away either and a pipe with a live write end never reports EOF:
/// measured at 20 s against `sleep 20` where bare and the split path both
/// returned in 0 s. Neither shows up as a wrong byte anywhere — only as a wait.
#[test]
fn a_merged_run_ends_when_the_child_closes_its_streams() {
    let tmp = tempfile::tempdir().unwrap();
    let sink = tmp.path().join("caller.log");
    let (out, err) = one_appending_file(&sink);
    let mut child = run_core_cmd(
        &tmp.path().join("cap"),
        &["bash", "-c", "exec 1>&- 2>&-; sleep 5 & exit 0"],
    )
    .stdout(out)
    .stderr(err)
    .spawn()
    .unwrap();

    // Polled rather than waited on: a regression here is an unbounded hang, and
    // a test that hangs reports nothing at all.
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(2);
    let finished = loop {
        if child.try_wait().unwrap().is_some() {
            break true;
        }
        if std::time::Instant::now() >= deadline {
            child.kill().unwrap();
            child.wait().unwrap();
            break false;
        }
        std::thread::sleep(std::time::Duration::from_millis(10));
    };

    assert!(
        finished,
        "still waiting on a descendant that holds a descriptor it should never have had"
    );
    assert_eq!(
        std::fs::read_to_string(&sink).unwrap(),
        "",
        "the child closed its streams before writing"
    );
}
