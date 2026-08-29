//! `agent-tools run --background` through real processes.
//!
//! Every property here belongs to a process rather than to a value: a call that
//! returns while the job it started runs on, a start that failed reaching a
//! caller still listening for it, a wrapper that has let go of the descriptors
//! it was handed. None of them is reachable from a `#[cfg(test)]` module —
//! `background::detach` refuses to fork the multi-threaded process `libtest`
//! runs in — and the descriptor one is not visible in any captured string
//! either, which is why it reads `/proc` instead.
//!
//! Every wait below is a bounded poll on a fact the wrapper writes, never a
//! fixed sleep: a backgrounded run does all of its recording after the caller
//! has already returned, so a test that slept would be either slower than it
//! needs to be or green until the machine is busy. Bounding it is what makes a
//! regression fail by name instead of hanging the suite, which runs no `cargo
//! test` job in CI to notice.

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

/// A run scoped to its own `HOME` and its own capture directory, so no test
/// here can read another's captures or be delayed by them.
fn agent_tools(home: &Path, scope: &Path) -> Command {
    let mut c = Command::new(bin());
    c.env("CLAUDE_CONFIG_ROOT", worktree_root());
    c.env("HOME", home);
    c.env("AGENT_TOOLS_PARENT_DIR", scope);
    c
}

/// A scope directory under a fresh `HOME`, shaped like the one a `PreToolUse`
/// hook sets.
fn scope(home: &Path, session: &str, task: &str) -> PathBuf {
    let dir = home.join(".claude/agent-tools").join(session).join(task);
    std::fs::create_dir_all(&dir).expect("the scope directory should be creatable");
    dir
}

/// What the caller is told, parsed back into the three facts the line carries.
/// Parsing strictly is the point: the line is the whole of what a backgrounded
/// run tells its caller, so its shape is a contract, and a loose parse would
/// let that shape drift while every test stayed green.
struct Started {
    dir: PathBuf,
    wrapper_pid: u32,
    child_pid: u32,
}

impl Started {
    fn parse(printed: &str) -> Started {
        let line = printed.trim_end();
        let (dir, rest) = line
            .split_once("  wrapper pid ")
            .unwrap_or_else(|| panic!("the start line names no wrapper: {line:?}"));
        let (wrapper, child) = rest
            .split_once("  child pid ")
            .unwrap_or_else(|| panic!("the start line names no child: {line:?}"));
        Started {
            dir: PathBuf::from(dir),
            wrapper_pid: wrapper
                .parse()
                .unwrap_or_else(|e| panic!("wrapper pid {wrapper:?} in {line:?}: {e}")),
            child_pid: child
                .parse()
                .unwrap_or_else(|e| panic!("child pid {child:?} in {line:?}: {e}")),
        }
    }
}

/// Is this pid still the process the test started?
///
/// Matched on the argv rather than on the pid alone: these pids are read off a
/// line printed by a process that may already have exited, and a pid the kernel
/// has since handed to something else must not read as a wrapper that never
/// finished — nor be killed on the strength of a stale number.
fn still_running(pid: u32, argv_needle: &str) -> bool {
    match std::fs::read(format!("/proc/{pid}/cmdline")) {
        Ok(argv) => String::from_utf8_lossy(&argv).contains(argv_needle),
        Err(_) => false,
    }
}

/// Kills the wrapper a test started, however that test ends. A backgrounded
/// wrapper outlives its caller by design, so an assertion that fails before the
/// kill would otherwise leave it and its child running past the suite. The
/// wrapper forwards `SIGTERM` to the child it is supervising, so one signal
/// ends both.
struct KillWhenDone {
    wrapper_pid: u32,
    argv_needle: &'static str,
}

impl Drop for KillWhenDone {
    fn drop(&mut self) {
        if still_running(self.wrapper_pid, self.argv_needle) {
            let _ = Command::new("kill")
                .arg(self.wrapper_pid.to_string())
                .status();
        }
    }
}

/// Above anything these tests wait on, and far below a hung suite: every
/// wrapper here has a child that finishes in milliseconds once it is let go.
const DEADLINE: Duration = Duration::from_secs(20);

/// The capture, once the wrapper has finished with it.
///
/// `drained_at` is the last fact written, so a meta carrying it is a meta whose
/// other facts are all in place. Nothing else is safe to read: the caller
/// returned while the child was still running, so every fact but the start is
/// written behind its back.
fn wait_for_drain(dir: &Path) -> serde_json::Value {
    let deadline = Instant::now() + DEADLINE;
    loop {
        if let Ok(bytes) = std::fs::read(dir.join("meta.json")) {
            if let Ok(meta) = serde_json::from_slice::<serde_json::Value>(&bytes) {
                if meta.get("drained_at").is_some_and(|d| !d.is_null()) {
                    return meta;
                }
            }
        }
        assert!(
            Instant::now() < deadline,
            "the backgrounded wrapper never recorded a drain within {DEADLINE:?}: {}",
            dir.display()
        );
        std::thread::sleep(Duration::from_millis(20));
    }
}

/// Wait for a pid to stop being the process the test started.
fn wait_until_gone(pid: u32, argv_needle: &str) {
    let deadline = Instant::now() + DEADLINE;
    while still_running(pid, argv_needle) {
        assert!(
            Instant::now() < deadline,
            "pid {pid} was still running {argv_needle:?} {DEADLINE:?} after it reported"
        );
        std::thread::sleep(Duration::from_millis(20));
    }
}

/// The one file a backgrounded capture holds.
///
/// Named rather than unwrapped, because the way this goes missing is not the
/// way it reads: a run that forwarded to a caller writes `stdout` and `stderr`
/// instead, and a bare "No such file" points at the capture rather than at the
/// decision that shaped it. So the failure lists what is there.
fn merged_capture(dir: &Path) -> String {
    std::fs::read_to_string(dir.join("output")).unwrap_or_else(|e| {
        let present: Vec<_> = std::fs::read_dir(dir)
            .into_iter()
            .flatten()
            .flatten()
            .map(|e| e.file_name())
            .collect();
        panic!("a backgrounded run captures both streams into one `output`: {e}; holds {present:?}")
    })
}

/// The one capture directory under a scope, named for its wrapper's pid. Used
/// where no line was printed to name it — a start that failed still publishes
/// its capture, which is the whole difference from the shell's `&`.
fn only_capture_dir(scope: &Path) -> PathBuf {
    let mut dirs: Vec<PathBuf> = std::fs::read_dir(scope)
        .expect("the scope should be readable")
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.is_dir())
        .collect();
    assert_eq!(
        dirs.len(),
        1,
        "one run publishes one capture directory: {dirs:?}"
    );
    dirs.pop().expect("checked above")
}

/// The whole promise of `--background`: the call is over as soon as the child
/// exists, and what it prints is enough to find the capture that will outlive
/// it. The capture has to be on disk by then too — a line naming a directory a
/// reader cannot yet stat is a line that cannot be acted on.
#[test]
fn background_returns_immediately_and_names_where_the_output_will_be() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-bg", "toolu_bg");

    let started = Instant::now();
    let out = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "bg-slow-k4", "sleep", "5"])
        .output()
        .unwrap();
    let elapsed = started.elapsed();

    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = Started::parse(&String::from_utf8_lossy(&out.stdout));
    let _cleanup = KillWhenDone {
        wrapper_pid: s.wrapper_pid,
        argv_needle: "bg-slow-k4",
    };

    assert!(
        elapsed < Duration::from_secs(3),
        "--background returned only after the child finished: {elapsed:?}"
    );
    assert_eq!(
        s.dir.file_name().and_then(|n| n.to_str()),
        Some(s.wrapper_pid.to_string().as_str()),
        "the capture is named for the wrapper that owns it"
    );
    assert!(
        s.dir.join("meta.json").exists(),
        "the capture is on disk before the caller returns: {}",
        s.dir.display()
    );
    assert!(
        still_running(s.wrapper_pid, "bg-slow-k4"),
        "the wrapper the line named must still be running the job it reported"
    );
    assert!(
        still_running(s.child_pid, "sleep"),
        "the child pid must name the job itself, which is what a reader watches, \
         kills, or waits for"
    );
}

/// The failure `--background` exists to end. A start that fails under the
/// shell's `&` reports success and leaves nothing to look at; here the reason
/// travels the same channel the start line does, so it reaches the caller while
/// it is still reading.
#[test]
fn a_start_that_fails_is_loud_and_nothing_is_left_running() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-bf", "toolu_bf");

    let out = agent_tools(home.path(), &scope)
        .args([
            "run",
            "--background",
            "--desc",
            "bg-nope-k4",
            "/nonexistent/binary-x9",
        ])
        .output()
        .unwrap();

    assert!(!out.status.success(), "a failed start must not exit 0");
    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.contains("binary-x9") && err.contains("No such file"),
        "the reason must reach the caller while it is still reading: {err}"
    );
    assert!(
        String::from_utf8_lossy(&out.stdout).trim().is_empty(),
        "a start that never happened names no capture to watch: {}",
        String::from_utf8_lossy(&out.stdout)
    );

    // No line was printed, so the pid comes from the capture the wrapper
    // published before it tried to spawn — which is itself the difference from
    // `&`, where a failed start leaves nothing on disk at all.
    let meta: serde_json::Value =
        serde_json::from_slice(&std::fs::read(only_capture_dir(&scope).join("meta.json")).unwrap())
            .unwrap();
    let wrapper_pid = meta["wrapper_pid"].as_u64().unwrap() as u32;
    wait_until_gone(wrapper_pid, "binary-x9");
}

/// Not every failed start is a failed spawn. A wrapper that cannot find a scope,
/// or make a directory, or publish its capture, fails before there is anything
/// to spawn — and by then its own stderr is `/dev/null`, so the report channel
/// is the only way the reason leaves this process. Without it the caller learns
/// that the wrapper exited and nothing about why, which is the shell's `&` with
/// extra steps.
#[test]
fn a_failure_before_the_spawn_reaches_the_caller_with_its_reason() {
    let home = tempfile::TempDir::new().unwrap();

    let out = Command::new(bin())
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        // Every Claude Code shell exports this too, including whichever one is
        // running this suite; left in place it would answer through the
        // user-shell fallback and publish under the real session's scope.
        .env_remove("CLAUDE_CODE_SESSION_ID")
        .args(["run", "--background", "--desc", "bg-noscope-k4", "true"])
        .output()
        .unwrap();

    assert!(!out.status.success(), "a failed start must not exit 0");
    let err = String::from_utf8_lossy(&out.stderr);
    assert!(
        err.contains("neither AGENT_TOOLS_PARENT_DIR nor CLAUDE_CODE_SESSION_ID"),
        "the reason must reach the caller while it is still reading: {err}"
    );
    assert!(
        !err.contains("before saying whether it started"),
        "the wrapper died instead of reporting, and the reason went with it: {err}"
    );
}

/// Two rules at once, because the second is what makes the first mean anything.
///
/// The child's bytes go to the capture and nowhere else — one file, since the
/// wrapper owns both ends of the pipe it made. And the wrapper is off the
/// caller's descriptors: it inherits fd 1 and 2 as the very open file
/// description the caller handed it, so one that kept them would hold the
/// caller's stdout open and any reader waiting for EOF — Claude Code's Bash
/// tool, `Command::output`, `$(...)` — would wait for this wrapper rather than
/// for the parent that already answered it, while every assertion about content
/// still passed.
#[test]
fn a_backgrounded_child_captures_both_streams_into_one_file_and_forwards_neither() {
    const OUT_MARKER: &str = "out-marker-k4";
    const ERR_MARKER: &str = "err-marker-k4";

    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-bm", "toolu_bm");

    // Files rather than pipes, so the caller's two descriptors have names to
    // compare the wrapper's against — and so a wrapper that kept them fails
    // here by assertion instead of by making this call wait for the child it
    // was just told had started.
    let caller_out = home.path().join("caller-stdout");
    let caller_err = home.path().join("caller-stderr");
    let mut caller = agent_tools(home.path(), &scope)
        .args([
            "run",
            "--background",
            "--desc",
            "bg-both-k4",
            "sh",
            "-c",
            &format!("echo {OUT_MARKER}; echo {ERR_MARKER} 1>&2; exec cat"),
        ])
        // The child ends when this closes, so the wrapper stays alive for the
        // descriptor read below without anything sleeping for it.
        .stdin(Stdio::piped())
        .stdout(std::fs::File::create(&caller_out).unwrap())
        .stderr(std::fs::File::create(&caller_err).unwrap())
        .spawn()
        .unwrap();
    let caller_stdin = caller.stdin.take().expect("piped");
    assert!(
        caller.wait().unwrap().success(),
        "stderr: {}",
        std::fs::read_to_string(&caller_err).unwrap_or_default()
    );

    let line = std::fs::read_to_string(&caller_out).unwrap();
    let s = Started::parse(&line);

    let fd = |n: u32| {
        std::fs::read_link(format!("/proc/{}/fd/{n}", s.wrapper_pid))
            .unwrap_or_else(|e| panic!("the detached wrapper should still hold an fd {n}: {e}"))
    };
    assert_ne!(
        fd(1),
        caller_out.canonicalize().unwrap(),
        "the detached wrapper still holds the caller's stdout open"
    );
    assert_ne!(
        fd(2),
        caller_err.canonicalize().unwrap(),
        "the detached wrapper still holds the caller's stderr open"
    );

    // The other half of the same rule, one layer up: the destination the
    // wrapper forwards to, rather than the descriptors it holds.
    assert!(
        !line.contains(OUT_MARKER),
        "the child's stdout reached the caller: {line}"
    );
    assert!(
        !std::fs::read_to_string(&caller_err)
            .unwrap()
            .contains(ERR_MARKER),
        "the child's stderr reached the caller"
    );

    drop(caller_stdin);
    let meta = wait_for_drain(&s.dir);

    assert_eq!(meta["merge"], "backgrounded: wrapper owns the destination");
    assert!(
        !s.dir.join("stdout").exists() && !s.dir.join("stderr").exists(),
        "a merged capture holds one file; the others are absent, not empty"
    );
    let captured = merged_capture(&s.dir);
    assert!(
        captured.contains(OUT_MARKER) && captured.contains(ERR_MARKER),
        "both streams belong in the one capture: {captured}"
    );
    assert_eq!(meta["reaped"]["status"], 0);
}

/// Exit 0 means started, not succeeded. The child's own status is not the
/// wrapper's to return — the caller was answered while the child was still
/// running — so it reaches a reader through the record and nowhere else.
#[test]
fn exit_zero_means_started_not_succeeded() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-bx", "toolu_bx");

    let out = agent_tools(home.path(), &scope)
        .args([
            "run",
            "--background",
            "--desc",
            "bg-fails-k4",
            "sh",
            "-c",
            "exit 3",
        ])
        .output()
        .unwrap();

    assert!(
        out.status.success(),
        "the child's failure is not the wrapper's: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = Started::parse(&String::from_utf8_lossy(&out.stdout));
    assert_eq!(wait_for_drain(&s.dir)["reaped"]["status"], 3);
}

/// A detached process must not read a terminal, but everything else on stdin is
/// the caller's data and belongs to the child: `< file` and heredocs are how
/// commands are fed. Measured beforehand: a heredoc reaches a `setsid` child
/// that reads it after the parent has moved on.
#[test]
fn a_non_tty_stdin_is_inherited_so_redirection_still_works() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-bi", "toolu_bi");

    let mut caller = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "bg-reads-k4", "cat"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    let mut stdin = caller.stdin.take().expect("piped");
    stdin.write_all(b"payload-from-stdin\n").unwrap();
    // The child reads to EOF, which is this handle closing and not the caller
    // exiting: by then the caller has long returned.
    drop(stdin);

    let out = caller.wait_with_output().unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = Started::parse(&String::from_utf8_lossy(&out.stdout));
    wait_for_drain(&s.dir);

    let captured = merged_capture(&s.dir);
    assert!(
        captured.contains("payload-from-stdin"),
        "a detached child must still read the stdin it was given: {captured}"
    );
}

/// `--background` changes when the caller is answered, not what the run is.
#[test]
fn background_composes_with_the_flags_run_already_had() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-bc", "toolu_bc");

    let out = agent_tools(home.path(), &scope)
        .args([
            "run",
            "--background",
            "--hide-cmdline",
            "--drain-cap-bytes",
            "4096",
            "--desc",
            "composed",
            "echo",
            "ok",
        ])
        .output()
        .unwrap();

    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = Started::parse(&String::from_utf8_lossy(&out.stdout));
    let meta = wait_for_drain(&s.dir);
    assert_eq!(meta["desc"], "composed", "--desc still reaches the record");
    assert_eq!(meta["reaped"]["status"], 0, "the run still ran: {meta}");
    assert_eq!(merged_capture(&s.dir), "ok\n");
}

/// The start line is read a line at a time, by an agent taught which lines are
/// the wrapper's own. So nothing that reaches it may carry a newline: a second
/// line would read as a status line for a run that does not exist. The scope
/// directory is the only part a caller can choose — `--desc` never reaches this
/// line, and the pids are numbers — and it is escaped rather than refused,
/// since a path with a newline in it cannot be printed honestly either way.
#[test]
fn the_start_line_stays_one_line_whatever_the_scope_was_named() {
    let home = tempfile::TempDir::new().unwrap();
    let scope = scope(home.path(), "sid-be", "toolu\nforged");

    let out = agent_tools(home.path(), &scope)
        .args(["run", "--background", "--desc", "bg\nforged-desc", "true"])
        .output()
        .unwrap();

    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let printed = String::from_utf8_lossy(&out.stdout);
    assert_eq!(
        printed.lines().count(),
        1,
        "a newline reached the start line and forged a second one: {printed:?}"
    );
    assert!(
        printed.contains("toolu\\nforged"),
        "the newline is shown rather than obeyed: {printed:?}"
    );
    wait_for_drain(&only_capture_dir(&scope));
}
