use std::path::{Path, PathBuf};
use std::process::{Child, Command, Output, Stdio};
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

/// The scope a hook would set for one tool call: `<home>/.claude/agent-tools/sid/[<agent>/]<tuid>`.
fn scope(home: &Path, agent: Option<&str>, tuid: &str) -> PathBuf {
    let mut p = home.join(".claude/agent-tools/sid");
    if let Some(a) = agent {
        p.push(a);
    }
    p.push(tuid);
    std::fs::create_dir_all(&p).unwrap();
    p
}

/// A wrapped job, as a background Bash call would start it, killed on drop.
struct Job(Child);

impl Drop for Job {
    fn drop(&mut self) {
        let _ = Command::new("kill").arg(self.0.id().to_string()).status();
        let _ = self.0.wait();
    }
}

fn job(home: &Path, scope: &Path, desc: &str, secs: u32) -> Job {
    let child = Command::new(bin())
        .args(["run", "--desc", desc, "sleep", &secs.to_string()])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home)
        .env("AGENT_TOOLS_PARENT_DIR", scope)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    Job(child)
}

fn wait_cmd(home: &Path, scope: &Path, max: u32) -> Command {
    let mut c = Command::new(bin());
    c.args(["wait", "--max", &max.to_string()])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home)
        .env("AGENT_TOOLS_PARENT_DIR", scope);
    c
}

fn timed(mut c: Command) -> (Output, Duration) {
    let t = Instant::now();
    let out = c.output().unwrap();
    (out, t.elapsed())
}

fn text(b: &[u8]) -> String {
    String::from_utf8_lossy(b).into_owned()
}

/// Lets a freshly spawned wrapper write its `meta.json` before a wait looks.
fn settle() {
    std::thread::sleep(Duration::from_millis(500));
}

#[test]
fn returns_once_a_running_job_ends() {
    let home = tempfile::tempdir().unwrap();
    let _job = job(home.path(), &scope(home.path(), Some("a1"), "tu-job"), "job", 2);
    settle();
    let (out, took) = timed(wait_cmd(home.path(), &scope(home.path(), Some("a1"), "tu-wait"), 60));
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took < Duration::from_secs(10), "took {took:?}");
    assert!(stdout.starts_with("ended within "), "{stdout}");
    assert!(stdout.contains("job [final(0)]") || stdout.contains("job [exited(0)]"), "{stdout}");
}

#[test]
fn returns_at_max_with_the_job_still_running() {
    let home = tempfile::tempdir().unwrap();
    let _job = job(home.path(), &scope(home.path(), Some("a1"), "tu-job"), "long job", 60);
    settle();
    let (out, took) = timed(wait_cmd(home.path(), &scope(home.path(), Some("a1"), "tu-wait"), 2));
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took >= Duration::from_secs(2) && took < Duration::from_secs(6), "took {took:?}");
    assert!(stdout.starts_with("nothing ended in "), "{stdout}");
    assert!(stdout.contains("long job [producing]") || stdout.contains("long job [quiet("), "{stdout}");
}

/// The parallel-launch race: the job's wrapper starts after the wait does.
#[test]
fn picks_up_a_job_that_starts_after_the_wait() {
    let home = tempfile::tempdir().unwrap();
    let waiter = wait_cmd(home.path(), &scope(home.path(), Some("a1"), "tu-wait"), 60)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    std::thread::sleep(Duration::from_secs(2));
    let _job = job(home.path(), &scope(home.path(), Some("a1"), "tu-job"), "late job", 1);
    let out = waiter.wait_with_output().unwrap();
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(stdout.contains("late job ["), "{stdout}");
}

/// Another agent's job, the main thread's, and one in the wait's own tool call
/// (the wait wrapped in `agent-tools run`) are none of them this agent's to wait on.
#[test]
fn fails_when_only_others_jobs_run() {
    let home = tempfile::tempdir().unwrap();
    let _other = job(home.path(), &scope(home.path(), Some("a2"), "tu-x"), "other agent", 60);
    let _main = job(home.path(), &scope(home.path(), None, "tu-y"), "main thread", 60);
    let own = scope(home.path(), Some("a1"), "tu-wait");
    let _own = job(home.path(), &own, "own call", 60);
    settle();
    let (out, took) = timed(wait_cmd(home.path(), &own, 60));
    assert_eq!(out.status.code(), Some(1), "stdout: {}", text(&out.stdout));
    assert!(took < Duration::from_secs(10), "took {took:?}");
    let stderr = text(&out.stderr);
    assert!(stderr.contains("nothing of this agent's is running"), "{stderr}");
    assert!(stderr.contains("agent-tools run"), "{stderr}");
}

/// The main thread's scope holds subagent scopes inside it; a main-thread wait
/// watches only its own.
#[test]
fn a_main_thread_wait_skips_subagent_jobs() {
    let home = tempfile::tempdir().unwrap();
    let _sub = job(home.path(), &scope(home.path(), Some("a1"), "tu-x"), "subagent job", 60);
    let _main = job(home.path(), &scope(home.path(), None, "tu-y"), "main job", 2);
    settle();
    let (out, _) = timed(wait_cmd(home.path(), &scope(home.path(), None, "tu-wait"), 60));
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(stdout.contains("main job ["), "{stdout}");
    assert!(!stdout.contains("subagent job"), "{stdout}");
}

#[test]
fn fails_without_a_hook_set_scope() {
    let home = tempfile::tempdir().unwrap();
    let out = Command::new(bin())
        .args(["wait", "--max", "1"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(1));
    assert!(text(&out.stderr).contains("AGENT_TOOLS_PARENT_DIR"), "{}", text(&out.stderr));
}

fn wait_files(home: &Path, max: u32, files: &[&Path]) -> Command {
    let mut c = Command::new(bin());
    c.args(["wait", "--max", &max.to_string()])
        .args(files)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home)
        .env_remove("AGENT_TOOLS_PARENT_DIR");
    c
}

/// Claude Code appends `[exited with code N]` to a background task's output
/// file when the task ends; a job started without `agent-tools run` is reached
/// only through that file.
#[test]
fn a_task_file_ends_at_its_trailer() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("b1.output");
    std::fs::write(&f, "step 1\n").unwrap();
    let waiter = wait_files(home.path(), 60, &[&f])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    std::thread::sleep(Duration::from_millis(1500));
    std::fs::write(&f, "step 1\nstep 2\n\n[exited with code 3]\n").unwrap();
    let t = Instant::now();
    let out = waiter.wait_with_output().unwrap();
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(t.elapsed() < Duration::from_secs(5), "took {:?}", t.elapsed());
    assert!(stdout.starts_with("ended within "), "{stdout}");
    assert!(stdout.contains("b1.output: [exited with code 3]"), "{stdout}");
}

#[test]
fn a_killed_task_file_has_ended() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("b2.output");
    std::fs::write(&f, "partial\n\n[killed]").unwrap();
    let (out, took) = timed(wait_files(home.path(), 60, &[&f]));
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took < Duration::from_secs(3), "took {took:?}");
    assert!(text(&out.stdout).contains("b2.output: [killed]"), "{}", text(&out.stdout));
}

/// Only a whole last line is a trailer: a job that prints the words is still running.
#[test]
fn a_task_file_without_a_trailer_runs_to_max() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("b3.output");
    std::fs::write(&f, "echo [exited with code 0] done\n").unwrap();
    let (out, took) = timed(wait_files(home.path(), 2, &[&f]));
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took >= Duration::from_secs(2) && took < Duration::from_secs(6), "took {took:?}");
    assert!(stdout.starts_with("nothing ended in "), "{stdout}");
    assert!(stdout.contains("b3.output: running, 31B, last write "), "{stdout}");
}

#[test]
fn a_missing_task_file_is_an_error() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("nope.output");
    let (out, _) = timed(wait_files(home.path(), 60, &[&f]));
    assert_eq!(out.status.code(), Some(1));
    assert!(text(&out.stderr).contains("Output is being written to:"), "{}", text(&out.stderr));
}

/// Passing a file that already ended again must not make every call return at
/// once while another job still runs.
#[test]
fn an_ended_file_does_not_end_the_wait_while_another_runs() {
    let home = tempfile::tempdir().unwrap();
    let done = home.path().join("done.output");
    let live = home.path().join("live.output");
    std::fs::write(&done, "x\n\n[exited with code 0]\n").unwrap();
    std::fs::write(&live, "step 1\n").unwrap();
    let (out, took) = timed(wait_files(home.path(), 2, &[&done, &live]));
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took >= Duration::from_secs(2), "took {took:?}");
    assert!(stdout.starts_with("nothing ended in "), "{stdout}");
    assert!(stdout.contains("ended before the wait:\n  "), "{stdout}");
    assert!(stdout.contains("done.output: [exited with code 0]"), "{stdout}");
}
