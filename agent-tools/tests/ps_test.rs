use std::path::{Path, PathBuf};
use std::process::Command;

fn bin() -> String {
    env!("CARGO_BIN_EXE_agent-tools").to_string()
}

fn worktree_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
        .to_path_buf()
}

fn agent_tools() -> Command {
    let mut command = Command::new(bin());
    command.env("CLAUDE_CONFIG_ROOT", worktree_root());
    command
}

/// Seed a capture at `<home>/.claude/agent-tools/<session>/[<agent>/]<tuid>/<wrapper_pid>/`.
/// Writes meta.json (the fact record `run` writes), stdout, stderr. Returns the
/// capture directory.
///
/// `wrapper_started_ticks: 1` cannot match a real process's start time, so the
/// wrapper reads as dead however this machine happens to allocate pids. With a
/// reap recorded that derives to `final(<status>)`; without one, `abandoned`.
/// Either way the fixture's status is fixed, not a race against the test host.
fn seed_capture(
    home: &Path,
    session: &str,
    agent: Option<&str>,
    tuid: &str,
    wrapper_pid: u32,
    desc: Option<&str>,
    exit: Option<i32>,
    stdout: &str,
) -> PathBuf {
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        dir.push(a);
    }
    dir.push(tuid);
    dir.push(wrapper_pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let meta = serde_json::json!({
        "wrapper_pid": wrapper_pid,
        "wrapper_started_ticks": 1,
        "child_pid": wrapper_pid + 1,
        "desc": desc,
        "command": ["echo", desc.unwrap_or("anon")],
        "started_at": "2026-05-17T10:00:00Z",
        "spawn_error": serde_json::Value::Null,
        "reaped": exit.map(|status| {
            serde_json::json!({"at": "2026-05-17T10:00:05Z", "status": status})
        }),
        "drained_at": exit.map(|_| "2026-05-17T10:00:05Z"),
    });
    std::fs::write(
        dir.join("meta.json"),
        serde_json::to_string_pretty(&meta).unwrap(),
    )
    .unwrap();
    std::fs::write(dir.join("stdout"), stdout).unwrap();
    std::fs::write(dir.join("stderr"), "").unwrap();
    dir
}

/// Seed a capture whose `started_at` is `started`, so ordering can be tested.
#[allow(clippy::too_many_arguments)]
fn seed_capture_at(
    home: &Path,
    session: &str,
    agent: Option<&str>,
    tuid: &str,
    wrapper_pid: u32,
    desc: Option<&str>,
    exit: Option<i32>,
    started: &str,
) -> PathBuf {
    let dir = seed_capture(home, session, agent, tuid, wrapper_pid, desc, exit, "");
    let raw = std::fs::read_to_string(dir.join("meta.json")).unwrap();
    let mut meta: serde_json::Value = serde_json::from_str(&raw).unwrap();
    meta["started_at"] = serde_json::Value::String(started.to_string());
    std::fs::write(
        dir.join("meta.json"),
        serde_json::to_string_pretty(&meta).unwrap(),
    )
    .unwrap();
    dir
}

/// Write an events.jsonl line at `<home>/.claude/agent-tools/<session>/[<agent>/]<tuid>/events.jsonl`.
fn append_event(home: &Path, session: &str, agent: Option<&str>, tuid: &str, line: &str) {
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        dir.push(a);
    }
    dir.push(tuid);
    std::fs::create_dir_all(&dir).unwrap();
    let path = dir.join("events.jsonl");
    let prior = std::fs::read_to_string(&path).unwrap_or_default();
    std::fs::write(&path, format!("{prior}{line}\n")).unwrap();
}

#[test]
fn no_state_on_disk_prints_session_and_marker() {
    let home = tempfile::tempdir().unwrap();
    let out = agent_tools()
        .args(["ps", "--session-id", "sid-fresh"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("session: sid-fresh"), "{s}");
    assert!(s.contains("(no state on disk)"), "{s}");
}

#[test]
fn main_thread_two_captures_under_one_tool_use_id() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid1",
        11111,
        Some("probe-a"),
        Some(0),
        "out-a\n",
    );
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid1",
        22222,
        Some("probe-b"),
        Some(1),
        "out-b\n",
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("session: sid"), "{s}");
    assert!(s.contains("agent: _main"), "{s}");
    assert!(s.contains("tool-use tuid1 (2 captures)"), "{s}");
    // Each capture is named by its desc and carries its own derived status,
    // so a listing that merged or dropped one cannot satisfy both lines.
    assert!(s.contains("probe-a [final(0)]"), "{s}");
    assert!(s.contains("probe-b [final(1)]"), "{s}");
    // The wrapper pid is what the capture dir is named for; a report has no
    // room for it, `ps` does.
    assert!(s.contains("wrapper: pid 11111"), "{s}");
    assert!(s.contains("wrapper: pid 22222"), "{s}");
    assert!(s.contains("cmd:     echo probe-a"), "{s}");
    assert!(s.contains("cmd:     echo probe-b"), "{s}");
    assert!(s.contains("started: 10:00:00.000"), "{s}");
}

#[test]
fn subagent_capture_listed_under_subagent_header() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        Some("agent-x"),
        "tuid-sub",
        33333,
        Some("sub-probe"),
        Some(0),
        "sub-out\n",
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("agent: agent-x"), "{s}");
    assert!(s.contains("tool-use tuid-sub (1 capture)"), "{s}");
    assert!(s.contains("sub-probe [final(0)]"), "{s}");
    assert!(s.contains("wrapper: pid 33333"), "{s}");
    // Only meaningful because the assertions above prove the capture was in
    // fact listed: an empty listing would satisfy this line for free.
    assert!(!s.contains("agent: _main"), "leak: {s}");
}

#[test]
fn task_filter_limits_to_one_tool_use_id() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid-keep",
        44444,
        Some("keep"),
        Some(0),
        "k\n",
    );
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid-drop",
        55555,
        Some("drop"),
        Some(0),
        "d\n",
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid", "--task", "tuid-keep"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("tuid-keep"), "{s}");
    // The kept capture must actually be rendered, or the two negatives below
    // would pass on an empty listing.
    assert!(s.contains("keep [final(0)]"), "{s}");
    assert!(s.contains("wrapper: pid 44444"), "{s}");
    assert!(!s.contains("tuid-drop"), "{s}");
    assert!(!s.contains("wrapper: pid 55555"), "{s}");
}

#[test]
fn events_appear_in_chronological_order() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        66666,
        Some("evt"),
        Some(0),
        "e\n",
    );

    // Out-of-order writes: middle, then earliest, then latest.
    append_event(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        r#"{"ts":"2026-05-17T10:00:02Z","kind":"middle","data":{"n":2}}"#,
    );
    append_event(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        r#"{"ts":"2026-05-17T10:00:01Z","kind":"first","data":{"n":1}}"#,
    );
    append_event(
        home.path(),
        "sid",
        None,
        "tuid-evt",
        r#"{"ts":"2026-05-17T10:00:03Z","kind":"last","data":{"n":3}}"#,
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    // Events are collected from the tool_use_id dirs of surviving captures, so
    // the capture has to be listed for the block to appear at all.
    assert!(s.contains("evt [final(0)]"), "{s}");
    // Search inside the events block, not the whole listing: the capture line
    // above it says "last byte Ns ago", which would match the `last` event
    // before the block is even reached.
    let block = s
        .split_once("events (chronological, all captures):")
        .unwrap_or_else(|| panic!("events block missing: {s}"))
        .1;
    let pos_first = block.find("first").expect("first event missing");
    let pos_middle = block.find("middle").expect("middle event missing");
    let pos_last = block.find("last").expect("last event missing");
    assert!(pos_first < pos_middle, "ordering wrong: {s}");
    assert!(pos_middle < pos_last, "ordering wrong: {s}");
}

#[test]
fn ps_shows_status_for_every_child_and_never_consumes_the_ledger() {
    // `ps` is the pull half of the bargain: reports are deduplicated against
    // the ledger and an agent's context can be compacted away, so there has to
    // be one place that shows everything's current status whether or not it was
    // already reported. Reading that must not retire a pending report, so `ps`
    // neither reads nor writes the ledger — it does not even take its lock,
    // which would serialize a read-only listing behind a reporting hook.
    let home = tempfile::tempdir().unwrap();
    // No reap and a wrapper that cannot be alive: abandoned. Nothing will ever
    // push this child's status again, which is exactly why `ps` must show it.
    seed_capture(
        home.path(),
        "sid",
        None,
        "toolu_x",
        7,
        Some("forgotten job"),
        None,
        "",
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("forgotten job [abandoned]"), "{s}");

    let scope = home.path().join(".claude/agent-tools/sid");
    assert!(
        !scope.join(".reported.json").exists(),
        "ps must not write the ledger"
    );
    assert!(
        !scope.join(".reported.lock").exists(),
        "ps must not even open the ledger: `Ledger::open` creates this lock file \
         and takes an exclusive flock on it"
    );
}

/// A record that cannot be parsed costs that record. Failing the whole file
/// instead deletes a tool call's entire history from the one view an agent has
/// after a compaction, and says nothing about having done so.
#[test]
fn a_malformed_event_line_costs_that_line_not_the_file() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid",
        4242,
        Some("seeded"),
        Some(0),
        "",
    );
    append_event(
        home.path(),
        "sid",
        None,
        "tuid",
        r#"{"ts":"2026-05-17T10:00:00Z","kind":"child_started","data":{"child_pid":4243}}"#,
    );
    append_event(home.path(), "sid", None, "tuid", "this line is not json");
    append_event(
        home.path(),
        "sid",
        None,
        "tuid",
        r#"{"ts":"2026-05-17T10:00:05Z","kind":"child_exit","data":{"exit_code":0}}"#,
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.contains("child_started"), "surviving event missing: {s}");
    assert!(s.contains("child_exit"), "surviving event missing: {s}");
    assert!(
        s.contains("1 unreadable event line"),
        "the loss must be counted and stated: {s}"
    );
}

/// `hook-post` derives `abandoned` for a capture whose meta cannot be read and
/// reports it. `ps` is the documented recovery path after a compaction, so the
/// child the report just called terminal must not be the one child `ps` cannot
/// look up.
#[test]
fn a_capture_without_meta_is_shown_rather_than_dropped() {
    let home = tempfile::tempdir().unwrap();
    let dir = home.path().join(".claude/agent-tools/sid/tuid/999999");
    std::fs::create_dir_all(&dir).unwrap();

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(
        s.contains("999999") && s.contains("[abandoned]"),
        "ps must show the capture it cannot describe, with its derived key: {s}"
    );
}

/// Agents routinely wrap large heredoc scripts, and `ps` is the recovery path
/// the prompt names after a compaction. Rendering the whole command puts a
/// six-figure line into the tool result that carries it.
#[test]
fn a_long_command_is_capped_on_the_ps_line() {
    let home = tempfile::tempdir().unwrap();
    let long = "x".repeat(5000);
    seed_capture(
        home.path(),
        "sid",
        None,
        "tuid",
        4242,
        Some(&long),
        Some(0),
        "",
    );
    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    let longest = s.lines().map(|l| l.chars().count()).max().unwrap_or(0);
    assert!(
        longest <= 2100,
        "longest ps line is {longest} chars; a wrapped script must not reach the output whole"
    );
    assert!(
        s.contains('\u{2026}'),
        "a truncated command must say it was truncated: {s}"
    );
}


/// `ps` is read after a compaction, through a tool result that truncates. What
/// started most recently is what the agent is still acting on, so it must be at
/// the top rather than wherever the tool-use identifier happened to sort.
#[test]
fn captures_are_ordered_newest_first() {
    let home = tempfile::tempdir().unwrap();
    // Identifier order and time order disagree: the alphabetically first
    // tool-use holds the oldest capture.
    seed_capture_at(home.path(), "sid", None, "toolu_aaa", 100, Some("oldest"), Some(0), "2026-05-17T10:00:00Z");
    seed_capture_at(home.path(), "sid", None, "toolu_zzz", 200, Some("middle"), Some(0), "2026-05-17T11:00:00Z");
    seed_capture_at(home.path(), "sid", None, "toolu_zzz", 300, Some("newest"), Some(0), "2026-05-17T12:00:00Z");

    let out = agent_tools()
        .args(["ps", "--session-id", "sid"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let s = String::from_utf8_lossy(&out.stdout);
    let pos = |needle: &str| s.find(needle).unwrap_or_else(|| panic!("{needle} missing from: {s}"));
    assert!(
        pos("newest") < pos("middle") && pos("middle") < pos("oldest"),
        "captures must read newest first: {s}"
    );
}
