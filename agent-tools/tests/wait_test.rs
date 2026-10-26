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

fn inbox(home: &Path, agent: &str) -> PathBuf {
    home.join(".claude/agent-tools/sid").join(agent).join(".inbox")
}

fn queue_message(home: &Path, agent: &str, from: &str) {
    use std::io::Write;
    let path = inbox(home, agent);
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    let mut f = std::fs::OpenOptions::new().create(true).append(true).open(path).unwrap();
    writeln!(f, "{}\t{from}", chrono::Utc::now().to_rfc3339()).unwrap();
}

/// SendMessage never cuts a subagent's running call short, so the wait is
/// what lets a message queued for it arrive without waiting out the bound.
#[test]
fn a_message_queued_during_the_wait_ends_it() {
    let home = tempfile::tempdir().unwrap();
    let _job = job(home.path(), &scope(home.path(), Some("a1"), "tu-job"), "job", 60);
    settle();
    let waiter = wait_cmd(home.path(), &scope(home.path(), Some("a1"), "tu-wait"), 60)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    std::thread::sleep(Duration::from_millis(1500));
    queue_message(home.path(), "a1", "main");
    let t = Instant::now();
    let out = waiter.wait_with_output().unwrap();
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(t.elapsed() < Duration::from_secs(3), "took {:?}", t.elapsed());
    assert!(stdout.starts_with("a message from main, queued "), "{stdout}");
    assert!(stdout.contains(" ago, arrives with this result\nnothing ended in "), "{stdout}");
    assert!(stdout.contains("job [producing]") || stdout.contains("job ["), "{stdout}");
}

/// One queued while the agent generated the call is delivered when this call
/// returns, so the wait returns at once rather than sit on it.
#[test]
fn a_message_queued_before_the_wait_ends_it_at_once() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("b9.output");
    std::fs::write(&f, "step 1\n").unwrap();
    queue_message(home.path(), "a1", "a2b3");
    queue_message(home.path(), "a1", "main");
    let mut c = wait_files(home.path(), 60, &[&f]);
    c.env("AGENT_TOOLS_PARENT_DIR", scope(home.path(), Some("a1"), "tu-wait"));
    let (out, took) = timed(c);
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took < Duration::from_secs(3), "took {took:?}");
    assert!(stdout.starts_with("2 messages, the last from main queued "), "{stdout}");
    assert!(stdout.contains("b9.output: running, 7B"), "{stdout}");
}

#[test]
fn another_agents_message_does_not_end_the_wait() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("b10.output");
    std::fs::write(&f, "step 1\n").unwrap();
    queue_message(home.path(), "a2", "main");
    let mut c = wait_files(home.path(), 2, &[&f]);
    c.env("AGENT_TOOLS_PARENT_DIR", scope(home.path(), Some("a1"), "tu-wait"));
    let (out, took) = timed(c);
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took >= Duration::from_secs(2), "took {took:?}");
    assert!(stdout.starts_with("nothing ended in "), "{stdout}");
}

/// One assistant record as Claude Code writes it to a transcript, carrying
/// the cache write split by lifetime.
fn assistant(agent: Option<&str>, w5m: u64, w1h: u64) -> String {
    let mut r = serde_json::json!({
        "type": "assistant",
        "message": {"usage": {"cache_creation": {
            "ephemeral_5m_input_tokens": w5m, "ephemeral_1h_input_tokens": w1h}}}
    });
    if let Some(a) = agent {
        r["agentId"] = serde_json::json!(a);
    }
    r.to_string()
}

fn transcript(home: &Path, rel: &str, records: &[String]) {
    let p = home.join(".claude/projects/-tmp-proj").join(rel);
    std::fs::create_dir_all(p.parent().unwrap()).unwrap();
    std::fs::write(p, records.join("\n") + "\n").unwrap();
}

fn print_bound(home: &Path, agent: Option<&str>, call_timeout_ms: Option<u64>, max: Option<u32>) -> String {
    let mut c = Command::new(bin());
    c.args(["wait", "--print-bound"])
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home)
        .env_remove("CLAUDE_CONFIG_DIR")
        .env_remove("AGENT_TOOLS_CALL_TIMEOUT_MS")
        .env("AGENT_TOOLS_PARENT_DIR", scope(home, agent, "tu-wait"));
    if let Some(ms) = call_timeout_ms {
        c.env("AGENT_TOOLS_CALL_TIMEOUT_MS", ms.to_string());
    }
    if let Some(m) = max {
        c.args(["--max", &m.to_string()]);
    }
    let out = c.output().unwrap();
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    text(&out.stdout)
}

#[test]
fn the_bound_follows_the_latest_cache_write() {
    let home = tempfile::tempdir().unwrap();
    let h = home.path();
    // The newest write decides: an hour cache after a 5-minute one.
    transcript(h, "sid/subagents/agent-a1.jsonl", &[assistant(Some("a1"), 900, 0), assistant(Some("a1"), 0, 0), assistant(Some("a1"), 0, 700)]);
    assert_eq!(print_bound(h, Some("a1"), None, None), "3000\n");
    // A record not the agent's own, such as one a fork carries over, is ignored.
    transcript(h, "sid/subagents/agent-a2.jsonl", &[assistant(Some("a2"), 500, 0), assistant(None, 0, 9000)]);
    assert_eq!(print_bound(h, Some("a2"), None, None), "240\n");
    // A workflow's agent sits one directory down.
    transcript(h, "sid/subagents/workflows/wf_1/agent-a3.jsonl", &[assistant(Some("a3"), 0, 40)]);
    assert_eq!(print_bound(h, Some("a3"), None, None), "3000\n");
    // A main thread keeps 4 minutes on its hour cache: its background agents'
    // reports reach it only when the call returns, and nothing announces them.
    transcript(h, "sid.jsonl", &[assistant(None, 0, 3108)]);
    assert_eq!(print_bound(h, None, None, None), "240\n");
    // Nothing written yet, as before an agent's first response is recorded.
    transcript(h, "sid/subagents/agent-a4.jsonl", &[r#"{"type":"user","message":{"content":"go"}}"#.to_string()]);
    assert_eq!(print_bound(h, Some("a4"), None, None), "240\n");
}

/// A missing transcript keeps the 5-minute bound and says why, so a layout
/// change in a Claude Code release shows instead of passing unnoticed.
#[test]
fn a_missing_transcript_is_reported() {
    let home = tempfile::tempdir().unwrap();
    std::fs::create_dir_all(home.path().join(".claude/projects/-tmp-proj")).unwrap();
    let out = print_bound(home.path(), Some("a9"), None, None);
    assert!(out.starts_with("240\nnote: waited as for a 5-minute cache, as its lifetime is unknown: no transcript sid/subagents/**/agent-a9.jsonl"), "{out}");
}

#[test]
fn the_bound_stays_inside_the_calls_own_timeout() {
    let home = tempfile::tempdir().unwrap();
    let h = home.path();
    transcript(h, "sid/subagents/agent-a1.jsonl", &[assistant(Some("a1"), 0, 700)]);
    assert_eq!(print_bound(h, Some("a1"), Some(3_600_000), None), "3000\n");
    assert_eq!(print_bound(h, Some("a1"), Some(300_000), None), "280\n");
    assert_eq!(print_bound(h, Some("a1"), Some(120_000), Some(240)), "100\n");
    assert_eq!(print_bound(h, Some("a1"), None, Some(30)), "30\n");
}

/// The call is moved to the background at its timeout, so a wait under the
/// default 120 s returns before then even with no `--max`.
#[test]
fn a_wait_returns_before_its_call_times_out() {
    let home = tempfile::tempdir().unwrap();
    let f = home.path().join("b11.output");
    std::fs::write(&f, "step 1\n").unwrap();
    let mut c = Command::new(bin());
    c.arg("wait")
        .arg(&f)
        .env("CLAUDE_CONFIG_ROOT", worktree_root())
        .env("HOME", home.path())
        .env("AGENT_TOOLS_CALL_TIMEOUT_MS", "23000")
        .env_remove("AGENT_TOOLS_PARENT_DIR");
    let (out, took) = timed(c);
    let stdout = text(&out.stdout);
    assert!(out.status.success(), "stderr: {}", text(&out.stderr));
    assert!(took >= Duration::from_secs(3) && took < Duration::from_secs(7), "took {took:?}");
    assert!(stdout.starts_with("nothing ended in 3s"), "{stdout}");
}
