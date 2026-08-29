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

/// This test binary's own start-ticks, read the same way `procstat::parse_stat`
/// does (field 22 of `/proc/<pid>/stat`, past the `)` closing `comm`). No
/// `crate::procstat` here: this file is a separate binary with no access to
/// agent-tools's internals, and the test process is the one pid this file can
/// always prove is alive without spawning and babysitting a child.
fn own_start_ticks() -> u64 {
    let pid = std::process::id();
    let stat = std::fs::read_to_string(format!("/proc/{pid}/stat")).unwrap();
    let (_, tail) = stat.rsplit_once(')').unwrap();
    tail.split_whitespace()
        .nth(19)
        .unwrap()
        .parse()
        .expect("starttime is numeric")
}

/// Seed a *live* capture: `wrapper_pid`/`wrapper_started_ticks` name this test
/// process itself, which is alive for as long as the test runs, so
/// `procstat::is_alive` reads it as a live wrapper with nothing reaped.
/// `started` is free to be any fixture time — liveness never reads it.
fn seed_live_capture(
    home: &Path,
    session: &str,
    agent: Option<&str>,
    tuid: &str,
    desc: &str,
    started: &str,
) -> PathBuf {
    let pid = std::process::id();
    let ticks = own_start_ticks();
    let mut dir = home.join(".claude/agent-tools").join(session);
    if let Some(a) = agent {
        dir.push(a);
    }
    dir.push(tuid);
    dir.push(pid.to_string());
    std::fs::create_dir_all(&dir).unwrap();
    let meta = serde_json::json!({
        "wrapper_pid": pid,
        "wrapper_started_ticks": ticks,
        "child_pid": pid,
        "desc": desc,
        "command": ["sleep", "9999"],
        "started_at": started,
        "spawn_error": serde_json::Value::Null,
        "reaped": serde_json::Value::Null,
        "drained_at": serde_json::Value::Null,
    });
    std::fs::write(
        dir.join("meta.json"),
        serde_json::to_string_pretty(&meta).unwrap(),
    )
    .unwrap();
    std::fs::write(dir.join("stdout"), "").unwrap();
    std::fs::write(dir.join("stderr"), "").unwrap();
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
        .args(["ps", "--format", "text", "--session-id", "sid-fresh"])
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
        .args(["ps", "--format", "text", "--all", "--session-id", "sid"])
        .env("HOME", home.path())
        // UTC+9 (POSIX `TZ` offsets are the negative of the zone's offset from
        // UTC), a zone this test host is most likely not already in: on a host
        // that is coincidentally UTC, comparing a Local-converted expectation
        // against a Local-converted rendering agrees by construction even with
        // a bare-UTC formatter bug, which is exactly why that comparison must
        // not be how this is checked.
        .env("TZ", "XXX-9")
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
    // The fixture's stored "2026-05-17T10:00:00Z" in UTC+9: a bare UTC
    // formatter reads "10:00:00" here regardless of the host's own zone,
    // since it never looks at one.
    assert!(s.contains("started: 19:00:00"), "{s}");
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
        .args(["ps", "--format", "text", "--all", "--session-id", "sid"])
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
        .args([
            "ps",
            "--format",
            "text",
            "--all",
            "--session-id",
            "sid",
            "--task",
            "tuid-keep",
        ])
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
        .args([
            "ps",
            "--format",
            "text",
            "--all",
            "--events",
            "--session-id",
            "sid",
        ])
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
        .args(["ps", "--format", "text", "--all", "--session-id", "sid"])
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
        .args([
            "ps",
            "--format",
            "text",
            "--all",
            "--events",
            "--session-id",
            "sid",
        ])
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
        .args(["ps", "--format", "text", "--all", "--session-id", "sid"])
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
        .args(["ps", "--format", "text", "--all", "--session-id", "sid"])
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
    let at = |tuid, pid, desc, started| {
        seed_capture_at(
            home.path(),
            "sid",
            None,
            tuid,
            pid,
            Some(desc),
            Some(0),
            started,
        )
    };
    at("toolu_aaa", 100, "oldest", "2026-05-17T10:00:00Z");
    at("toolu_zzz", 200, "middle", "2026-05-17T11:00:00Z");
    at("toolu_zzz", 300, "newest", "2026-05-17T12:00:00Z");

    let out = agent_tools()
        .args(["ps", "--format", "text", "--all", "--session-id", "sid"])
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
    let pos = |needle: &str| {
        s.find(needle)
            .unwrap_or_else(|| panic!("{needle} missing from: {s}"))
    };
    assert!(
        pos("newest") < pos("middle") && pos("middle") < pos("oldest"),
        "captures must read newest first: {s}"
    );
}

#[test]
fn ps_prints_json_and_withholds_terminal_children_by_default() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(
        home.path(),
        "sid-j",
        None,
        "toolu_a",
        100,
        Some("one"),
        Some(0),
        "x",
    );
    seed_capture(
        home.path(),
        "sid-j",
        None,
        "toolu_a",
        101,
        Some("two"),
        Some(1),
        "y",
    );
    let out = agent_tools()
        .args(["ps", "--session-id", "sid-j"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let v: serde_json::Value =
        serde_json::from_slice(&out.stdout).expect("ps emits json by default");
    assert_eq!(v["session"], "sid-j");
    assert!(
        v["now"].as_str().unwrap().contains('T'),
        "now is an instant: {v}"
    );
    assert_eq!(
        v["live"].as_array().unwrap().len(),
        0,
        "nothing here is running"
    );
    assert_eq!(v["withheld"]["by_key"]["final(0)"], 1);
    assert_eq!(v["withheld"]["by_key"]["final(1)"], 1);
    assert_eq!(v["withheld"]["retrieve_with"], "agent-tools ps --all");
}

#[test]
fn ps_all_brings_the_withheld_children_back() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(
        home.path(),
        "sid-all",
        None,
        "toolu_a",
        100,
        Some("one"),
        Some(0),
        "x",
    );
    let out = agent_tools()
        .args(["ps", "--all", "--session-id", "sid-all"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(
        v["live"].as_array().unwrap().len(),
        0,
        "`live` must not gain children that have finished: {v}"
    );
    let settled = v["settled"].as_array().expect("--all fills settled");
    assert_eq!(settled.len(), 1);
    assert_eq!(settled[0]["name"], "one");
    assert_eq!(settled[0]["key"], "final(0)");
    assert!(settled[0]["ran_s"].is_number());
    assert!(settled[0].get("elapsed_s").is_none());
    assert!(
        v["withheld"]["by_key"].as_object().unwrap().is_empty(),
        "nothing was withheld: {v}"
    );
}

#[test]
fn without_all_there_is_no_settled_array_to_mistake_for_an_empty_one() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(
        home.path(),
        "sid-ns",
        None,
        "toolu_a",
        100,
        Some("one"),
        Some(0),
        "x",
    );
    let out = agent_tools()
        .args(["ps", "--session-id", "sid-ns"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert!(v.get("settled").is_none(), "{v}");
    assert_eq!(v["withheld"]["by_key"]["final(0)"], 1);
}

#[test]
fn ps_text_still_renders_the_human_layout() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(
        home.path(),
        "sid-t",
        None,
        "toolu_a",
        100,
        Some("one"),
        Some(0),
        "x",
    );
    let out = agent_tools()
        .args(["ps", "--format", "text", "--all", "--session-id", "sid-t"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(s.starts_with("session: sid-t"), "{s}");
    assert!(s.contains("one [final(0)]"), "{s}");
}

#[test]
fn the_event_log_is_out_of_the_way_until_asked_for() {
    let home = tempfile::TempDir::new().unwrap();
    let dir = seed_capture(
        home.path(),
        "sid-e",
        None,
        "toolu_a",
        100,
        Some("one"),
        Some(0),
        "x",
    );
    let events = dir.parent().unwrap().join("events.jsonl");
    std::fs::write(
        &events,
        "{\"ts\":\"2026-05-17T10:00:01Z\",\"kind\":\"child_started\",\"data\":{}}\n",
    )
    .unwrap();

    let without = agent_tools()
        .args(["ps", "--all", "--session-id", "sid-e"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(
        !String::from_utf8_lossy(&without.stdout).contains("child_started"),
        "the event log is not what \"what is running\" means"
    );

    let with = agent_tools()
        .args([
            "ps",
            "--format",
            "text",
            "--all",
            "--events",
            "--session-id",
            "sid-e",
        ])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(String::from_utf8_lossy(&with.stdout).contains("child_started"));
}

#[test]
fn ps_never_retires_a_pending_report() {
    let home = tempfile::TempDir::new().unwrap();
    seed_capture(
        home.path(),
        "sid-led",
        None,
        "toolu_a",
        100,
        Some("one"),
        Some(0),
        "x",
    );
    let ledger = home
        .path()
        .join(".claude/agent-tools/sid-led/.reported.json");
    assert!(!ledger.exists());
    agent_tools()
        .args(["ps", "--all", "--session-id", "sid-led"])
        .env("HOME", home.path())
        .output()
        .unwrap();
    assert!(
        !ledger.exists(),
        "ps must not mark anything as told: whether its output reached the agent \
         is not something it can observe"
    );
}

/// `write_capture` renders `started_at` through `fmt_local_hms`: a bare UTC
/// formatter here would read as local and be wrong by the reader's offset,
/// the same hazard every other renderer avoids by going through it.
#[test]
fn ps_text_renders_the_start_in_local_time_not_bare_utc() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid-tz",
        None,
        "tuid",
        70000,
        Some("timed"),
        Some(0),
        "",
    );
    let out = agent_tools()
        .args(["ps", "--format", "text", "--all", "--session-id", "sid-tz"])
        .env("HOME", home.path())
        // See the identical pin in `main_thread_two_captures_under_one_tool_use_id`
        // for why this must be a fixed foreign zone and a literal, not a
        // Local-converted expectation compared against a Local-converted
        // rendering: that agrees with the bug this test exists to catch on
        // any host whose own zone happens to be UTC.
        .env("TZ", "XXX-9")
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
        s.contains("started: 19:00:00"),
        "expected the UTC+9 rendering of the fixture's stored 10:00:00Z: {s}"
    );
}

#[test]
fn a_group_header_counts_what_is_shown_not_what_was_withheld() {
    let home = tempfile::tempdir().unwrap();
    for (pid, name) in [(100, "a"), (101, "b"), (102, "c")] {
        seed_capture(
            home.path(),
            "sid-g",
            None,
            "toolu_a",
            pid,
            Some(name),
            Some(0),
            "x",
        );
    }
    let out = agent_tools()
        .args(["ps", "--format", "text", "--session-id", "sid-g"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    let s = String::from_utf8_lossy(&out.stdout);
    assert!(
        !s.contains("tool-use"),
        "a group with nothing to show is not announced: {s}"
    );
    assert!(
        s.contains("3 settled captures withheld -> agent-tools ps --all"),
        "{s}"
    );
}

/// Mirrors the all-withheld shape above but with one live sibling kept: the
/// header must count only the survivor, not the group's full membership —
/// the same bug as above, on the shape where a naive fix could still pass by
/// counting `captures` when `visible` and `captures` happen to have the same
/// length (there all four are absent; here one is present either way).
#[test]
fn a_group_header_counts_the_live_child_only_when_its_siblings_are_withheld() {
    let home = tempfile::tempdir().unwrap();
    seed_capture(
        home.path(),
        "sid-mix",
        None,
        "toolu_a",
        100,
        Some("a"),
        Some(0),
        "x",
    );
    seed_capture(
        home.path(),
        "sid-mix",
        None,
        "toolu_a",
        101,
        Some("b"),
        Some(0),
        "x",
    );
    seed_capture(
        home.path(),
        "sid-mix",
        None,
        "toolu_a",
        102,
        Some("c"),
        Some(0),
        "x",
    );
    seed_live_capture(
        home.path(),
        "sid-mix",
        None,
        "toolu_a",
        "d-live",
        "2026-05-17T10:00:00Z",
    );

    let out = agent_tools()
        .args(["ps", "--format", "text", "--session-id", "sid-mix"])
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
        s.contains("tool-use toolu_a (1 capture)"),
        "the header must count the one survivor, not the group's four members: {s}"
    );
    assert!(s.contains("d-live"), "{s}");
    assert!(
        s.contains("3 settled captures withheld -> agent-tools ps --all"),
        "{s}"
    );
}

/// Reproduces the exact counterexample: `toolu_bbb`'s group-newest member
/// (its settled capture at 12:00) is newer than `toolu_aaa`'s (its live
/// capture at 11:00), so a sort keyed on group rank ranks `toolu_bbb`'s live
/// child (10:00) ahead of `toolu_aaa`'s (11:00) in the flat `live` array —
/// backwards, since 11:00 is the more recent of the two children this array
/// actually carries. `live` must rank each record by its own start.
#[test]
fn live_is_ordered_by_its_own_start_not_by_a_withheld_siblings_group_rank() {
    let home = tempfile::tempdir().unwrap();
    seed_capture_at(
        home.path(),
        "sid-ord",
        None,
        "toolu_bbb",
        300,
        Some("settled-bbb"),
        Some(0),
        "2026-05-17T12:00:00Z",
    );
    seed_live_capture(
        home.path(),
        "sid-ord",
        None,
        "toolu_bbb",
        "live-bbb",
        "2026-05-17T10:00:00Z",
    );
    seed_capture_at(
        home.path(),
        "sid-ord",
        None,
        "toolu_aaa",
        100,
        Some("settled-aaa"),
        Some(0),
        "2026-05-17T09:00:00Z",
    );
    seed_live_capture(
        home.path(),
        "sid-ord",
        None,
        "toolu_aaa",
        "live-aaa",
        "2026-05-17T11:00:00Z",
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid-ord"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let live = v["live"].as_array().unwrap();
    assert_eq!(live.len(), 2, "{v}");
    assert_eq!(
        live[0]["name"], "live-aaa",
        "the 11:00 live child ranks first, not the sibling in the group with \
         the newer overall (but withheld, settled) member: {v}"
    );
    assert_eq!(live[1]["name"], "live-bbb", "{v}");
}

/// A flat array has no groups to partition by, so `agent_id` must not act as
/// a primary sort key ahead of recency: a subagent's child that started more
/// recently than every main-thread child must still rank above them.
#[test]
fn live_interleaves_a_subagents_child_with_the_main_threads_by_start_time() {
    let home = tempfile::tempdir().unwrap();
    seed_live_capture(
        home.path(),
        "sid-sub",
        None,
        "toolu_main",
        "main-child",
        "2026-05-17T08:00:00Z",
    );
    seed_live_capture(
        home.path(),
        "sid-sub",
        Some("agent-x"),
        "toolu_sub",
        "sub-child",
        "2026-05-17T09:00:00Z",
    );

    let out = agent_tools()
        .args(["ps", "--session-id", "sid-sub"])
        .env("HOME", home.path())
        .env_remove("AGENT_TOOLS_PARENT_DIR")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let v: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    let live = v["live"].as_array().unwrap();
    assert_eq!(live.len(), 2, "{v}");
    assert_eq!(
        live[0]["name"], "sub-child",
        "a subagent's newer child must not sort below every main-thread child: {v}"
    );
    assert_eq!(live[1]["name"], "main-child", "{v}");
}
