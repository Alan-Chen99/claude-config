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

/// Run `script` under `bash -c` with `pipefail`, so the pipeline reports the
/// producer's status rather than the consumer's — which is the whole question a
/// quitting downstream raises.
fn pipefail(script: &str) -> std::process::Output {
    Command::new("bash")
        .args(["-c", &format!("set -o pipefail; {script}")])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .output()
        .unwrap()
}

/// Enough output that the close is seen inside the read loop, not at the flush.
///
/// The size is load-bearing, and the regime boundary is one of the tee's
/// 8192-byte reads — not any buffer size in tokio. `TeeOutcome`'s
/// `bytes_since_close_detected` states the mechanism: a forwarded write's error
/// surfaces one chunk after the write that caused it, so a child whose whole
/// output arrives in a single read fails nothing in the loop, and
/// `ARRIVES_IN_ONE_CHUNK` covers that band. 588,895 bytes cannot arrive in one
/// read however the producer paces it — it is seventy-two of them — so this one
/// always fails in the loop.
const OVERFLOWS_THE_PIPE: &str = "bash -c 'echo done >&2; seq 1 100000'";

/// The producer is last on purpose: `bash` exits with the status of the last
/// command, so bare it is `seq`'s death by SIGPIPE that the shell reports. Put
/// the `echo` last and bare exits 0 too, and the differential proves nothing.
fn wrapped_into_head(cap: &Path) -> String {
    format!(
        "{} run-core --capture-dir {} -- {OVERFLOWS_THE_PIPE} | head -3",
        bin(),
        cap.display()
    )
}

/// Not a guard for the forward close. This passes unchanged against code that
/// discards the error from the final flush, and against code whose read loop
/// never checked its forward writes at all — it was green before either fix and
/// after. `a_close_seen_only_at_the_flush_is_stated_too` is the test that guards
/// the flush; `a_closed_downstream_is_stated_on_stderr` guards the loop.
///
/// What this one pins is that losing the downstream costs the caller neither the
/// child nor the call: the child runs to completion, the whole result still
/// reaches disk, and the wrapper exits on the child's own status instead of
/// dying of SIGPIPE the way bare does. A later drain bound that stops reading
/// too early breaks it, which is why it stays.
#[test]
fn downstream_quitting_neither_kills_the_child_nor_the_call() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let bare = pipefail(&format!("{OVERFLOWS_THE_PIPE} | head -3"));
    assert_eq!(
        bare.status.code(),
        Some(141),
        "bare: the producer dies of SIGPIPE and pipefail reports it"
    );

    let out = pipefail(&wrapped_into_head(&cap));
    assert_eq!(
        String::from_utf8_lossy(&out.stdout),
        "1\n2\n3\n",
        "the caller still sees exactly what it asked for"
    );
    let captured = std::fs::read_to_string(cap.join("stdout")).unwrap();
    assert!(
        captured.ends_with("100000\n"),
        "the whole result still lands on disk; got {} bytes",
        captured.len()
    );
    assert_eq!(
        out.status.code(),
        Some(0),
        "nothing died of SIGPIPE: the producer's own status is reported, not 141"
    );
}

/// The difference from bare is stated, never inferred: "a forwarded stream is
/// never silently short … either failure is stated on stderr and in the status."
///
/// The `agent-tools:` prefix at the start of a line is the contract the system
/// prompt teaches — that such a line is the wrapper speaking, not the command —
/// so its position is asserted, not just its presence. The child writes to stderr
/// too, which is why the diagnostic cannot be assumed to start the stream.
#[test]
fn a_closed_downstream_is_stated_on_stderr() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");

    let out = pipefail(&wrapped_into_head(&cap));

    let err = String::from_utf8_lossy(&out.stderr);
    let stated = err
        .lines()
        .find(|l| l.starts_with("agent-tools: stdout downstream closed"))
        .unwrap_or_else(|| panic!("nothing said the forwarding stopped; stderr was {err:?}"));
    assert!(
        stated.contains(&cap.join("stdout").display().to_string()),
        "the notice names where the output is still going; got {stated:?}"
    );
    assert_eq!(
        err.lines()
            .filter(|l| l.starts_with("agent-tools: stdout downstream closed"))
            .count(),
        1,
        "said once, not once per chunk; stderr was {err:?}"
    );
}

/// One chunk, one read, so only the flush can ever see the close.
///
/// `TeeOutcome`'s `bytes_since_close_detected` states the mechanism: the error
/// from a forwarded write appears one chunk after the write that caused it. A
/// child whose whole output is a single chunk fails nothing in the loop, so
/// `EPIPE` has exactly one place left to appear.
///
/// 2000 bytes is one `write` under `PIPE_BUF`, so it reaches the tee whole in a
/// single read rather than in however many pieces the producer chose, and it
/// sits four times inside the 8192-byte read rather than near its edge. The
/// consumer is gone before any of it exists: `(exit 0)` forks, exits and closes
/// the read end while the child is still sleeping. Nothing races.
const ARRIVES_IN_ONE_CHUNK: &str = r#"bash -c 'sleep 0.5; printf "%01999d\n" 0'"#;

#[test]
fn a_close_seen_only_at_the_flush_is_stated_too() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    let out = pipefail(&format!(
        "{} run-core --capture-dir {} -- {ARRIVES_IN_ONE_CHUNK} | (exit 0)",
        bin(),
        cap.display()
    ));

    let err = String::from_utf8_lossy(&out.stderr);
    assert_eq!(
        err.lines()
            .filter(|l| l.starts_with("agent-tools: stdout downstream closed"))
            .count(),
        1,
        "a close only the flush can see is still stated, once, and at the start of a \
         line — the position the prompt teaches; stderr was {err:?}"
    );
    let captured = std::fs::read_to_string(cap.join("stdout")).unwrap();
    assert_eq!(
        captured.len(),
        2000,
        "and the capture still holds everything the child wrote"
    );
}

/// Far more than the bound, and it ends on its own.
///
/// Ending on its own is the load-bearing half. `yes yes-line` never stops, so
/// against an implementation that adds the flag but not the `break` the test
/// does not fail — it hangs, writing at F1's measured 400 MB/s into the temp
/// dir until the disk is gone. A test for a disk-filling bug must not be one.
/// 10 MiB overruns a 64 KiB bound by 160x and takes about 25 ms either way.
const OVERRUNS_THE_BOUND: &str = "bash -c 'yes yes-line | head -c 10485760'";

#[test]
fn post_close_drain_is_bounded_and_the_bound_is_recorded() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    let out = pipefail(&format!(
        "{} run-core --drain-cap-bytes 65536 --capture-dir {} -- {OVERRUNS_THE_BOUND} | head -1",
        bin(),
        cap.display()
    ));

    assert_eq!(String::from_utf8_lossy(&out.stdout), "yes-line\n");
    // `stdout`, not a fallback to `output`: `Command::output()` hands the outer
    // bash two independent pipes, so `decide_merge` sees two inodes and always
    // splits. A hedge here would be a branch that cannot run.
    let captured = std::fs::metadata(cap.join("stdout")).unwrap().len();
    // Generous but not vacuous. At most the 64 KiB pipe buffer got through
    // before the consumer quit, the counter starts up to two 8192-byte reads
    // after that, and the bound then allows 64 KiB more: about 145 KiB worst
    // case. 300 KB catches a bound that fires at twice its size; 10 MB, the
    // producer's own length, would only catch one that never fires at all.
    assert!(
        captured < 300_000,
        "the drain stops at the bound, not at the producer's end; \
         captured {captured} bytes of 10485760"
    );
    let err = String::from_utf8_lossy(&out.stderr);
    // Position, not presence: the `agent-tools:` prefix begins a line is what
    // the system prompt teaches, so nothing a child writes can forge it.
    assert!(
        err.lines()
            .any(|l| l.starts_with("agent-tools: stdout drain bound")),
        "reaching the bound is recorded, never silent; stderr was {err:?}"
    );
    assert_eq!(
        out.status.code(),
        Some(141),
        "at the bound the read end closes, so the child sees SIGPIPE as it would bare"
    );
}

/// The low end of the range. A bound of `0` is a bound like any other, and the
/// drain stops at the first read past the close — one read of capture rather
/// than none, because `tee` counts the chunk that detected the close without
/// comparing on it and reaches the comparison only on the next one.
#[test]
fn the_lowest_bound_stops_the_drain_at_the_first_read_past_the_close() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    let out = pipefail(&format!(
        "{} run-core --drain-cap-bytes 0 --capture-dir {} -- {OVERRUNS_THE_BOUND} | head -1",
        bin(),
        cap.display()
    ));

    assert_eq!(String::from_utf8_lossy(&out.stdout), "yes-line\n");
    let captured = std::fs::metadata(cap.join("stdout")).unwrap().len();
    // The ceiling is twelve of the tee's 8192-byte reads, and every term of it
    // is structural: the one 8192-byte block `head -1` reads before it quits,
    // the eight the 64 KiB pipe buffer holds, the one tokio's stdout has in
    // hand when the close lands, the one
    // `TeeOutcome::bytes_since_close_detected` describes as the lag, and the
    // one read the drain arm takes before breaking. 98,304 bytes — which is
    // also the largest of 160 runs, across an idle machine and one with every
    // core saturated; the smallest was 20,480. 150,000 keeps margin over that
    // ceiling and still catches both ways a bound of 0 stops being one — read
    // as "uncapped", or swapped for the 256 MiB default — since either lets
    // the producer run its whole 10,485,760 bytes into the capture.
    assert!(
        captured < 150_000,
        "the drain stops one read past the close, not at the producer's end; \
         captured {captured} bytes of 10485760"
    );
    let err = String::from_utf8_lossy(&out.stderr);
    // Position, as the neighbouring tests check it, and the bound's own value
    // with it. Size alone cannot tell a bound of 0 from one of 64 KiB here:
    // measured, the two bands overlap under load — 0 reaching 98,304 and 65,536
    // falling to 81,920 — because both are dominated by what was in flight when
    // the close surfaced rather than by the bound. The line is exact where the
    // size is not.
    assert!(
        err.lines()
            .any(|l| l.starts_with("agent-tools: stdout drain bound of 0 bytes")),
        "the bound that fired is the one that was asked for; stderr was {err:?}"
    );
    assert_eq!(
        out.status.code(),
        Some(141),
        "at the bound the read end closes, so the child sees SIGPIPE as it would bare"
    );
}

/// The child F2 was measured against: enough output to keep writing well past
/// the first failed capture write, and an exit code nothing else would produce.
const TALKS_THEN_EXITS_5: [&str; 3] = [
    "bash",
    "-c",
    "for i in $(seq 1 2000); do echo line-$i; done; exit 5",
];

#[test]
fn capture_failure_never_kills_the_child() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    // `/dev/full` opens and then fails every write with ENOSPC, which is F2's
    // own trigger — a full disk — reached without privileges or a mount. A
    // directory in the same place would fail the *open* instead, and the open
    // is a different branch from the one that kills the child; it gets its own
    // test below. Two shapes are symlinked because the merge decision picks the
    // capture name, and `stderr` deliberately is not, so the test can tell one
    // failed stream from a wholly broken run.
    std::os::unix::fs::symlink("/dev/full", cap.join("stdout")).unwrap();
    std::os::unix::fs::symlink("/dev/full", cap.join("output")).unwrap();

    let out = run_core_cmd(&cap, &TALKS_THEN_EXITS_5).output().unwrap();

    assert_eq!(
        out.status.code(),
        Some(5),
        "the child's own status is reported, not one the wrapper inflicted"
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("line-1\n"), "forwarding continues");
    assert!(
        stdout.contains("line-2000\n"),
        "the caller's stream is never cut short by the wrapper's own failure"
    );
    let err = String::from_utf8_lossy(&out.stderr);
    // Position, not presence, the same way the forward-close tests check it:
    // the prefix beginning a line is the contract, not the substring.
    let stated: Vec<&str> = err
        .lines()
        .filter(|l| l.starts_with("agent-tools: capture to"))
        .collect();
    assert_eq!(
        stated.len(),
        1,
        "stated once on stderr, not once per chunk and not inferred from a wrong \
         exit code; stderr was {err:?}"
    );
    // And the words after the prefix, which the open and the flush share with
    // this one. A write that failed part-way is the only one of the three that
    // captured a prefix and then stopped, so it is the only one "from here"
    // describes.
    assert!(
        stated[0].contains("the capture is incomplete from here"),
        "the message names a capture that stopped part-way, not one that never \
         opened or one short by what was in flight; got {:?}",
        stated[0]
    );
}

#[test]
fn a_capture_that_cannot_be_opened_is_stated_and_not_fatal() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    // A directory where the capture file goes: the open fails with EISDIR and
    // the loop never runs, so this reaches the branch the test above cannot.
    std::fs::create_dir_all(cap.join("stdout")).unwrap();
    std::fs::create_dir_all(cap.join("output")).unwrap();

    let out = run_core_cmd(&cap, &TALKS_THEN_EXITS_5).output().unwrap();

    assert_eq!(out.status.code(), Some(5));
    assert!(String::from_utf8_lossy(&out.stdout).contains("line-2000\n"));
    let err = String::from_utf8_lossy(&out.stderr);
    let stated = err
        .lines()
        .find(|l| l.starts_with("agent-tools: capture to"))
        .unwrap_or_else(|| panic!("an open that failed is stated too; stderr was {err:?}"));
    // Nothing was ever captured here, so neither of the other two messages is
    // true of it: there is no "here" for the capture to be incomplete from, and
    // nothing was in flight to be short by.
    assert!(
        stated.contains("could not be opened"),
        "the message names an open that failed, not a capture that stopped \
         part-way; got {stated:?}"
    );
}

/// One chunk, one read, so only the flush can ever see the capture fail.
///
/// The capture-side counterpart to `ARRIVES_IN_ONE_CHUNK`, and 2000 bytes for
/// the same reason: one `write` under `PIPE_BUF` reaches the tee whole, four
/// times inside the 8192-byte read rather than near its edge, so the first
/// chunk's error has no second chunk to surface at. `capture.rs`'s
/// `read_buf_divides_the_two_regimes` names this constant, because a smaller
/// `READ_BUF` moves the test into the loop's regime where it passes while
/// guarding nothing. Argv rather than a shell string: this side needs no
/// pipeline, only a capture it cannot write.
const ONE_CHUNK_THEN_EXITS_5: [&str; 3] = ["bash", "-c", r#"printf "%01999d\n" 0; exit 5"#];

#[test]
fn a_capture_that_fails_only_at_the_flush_is_stated_too() {
    let tmp = tempfile::tempdir().unwrap();
    let cap = tmp.path().join("cap");
    std::fs::create_dir_all(&cap).unwrap();
    std::os::unix::fs::symlink("/dev/full", cap.join("stdout")).unwrap();
    std::os::unix::fs::symlink("/dev/full", cap.join("output")).unwrap();

    let out = run_core_cmd(&cap, &ONE_CHUNK_THEN_EXITS_5)
        .output()
        .unwrap();

    assert_eq!(out.status.code(), Some(5));
    assert_eq!(out.stdout.len(), 2000, "the caller still gets everything");
    let err = String::from_utf8_lossy(&out.stderr);
    let stated = err
        .lines()
        .find(|l| l.starts_with("agent-tools: capture to"))
        .unwrap_or_else(|| panic!("a flush that failed is stated too; stderr was {err:?}"));
    // Nothing was left to write, so the loop's wording would place the loss at a
    // point in a stream that has already ended. What this one cost is whatever
    // the last write had not yet reached disk with.
    assert!(
        stated.contains("short by whatever was still in flight"),
        "the message names a flush that failed, not a capture that stopped \
         part-way; got {stated:?}"
    );
}
