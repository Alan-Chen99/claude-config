use chrono::{DateTime, Utc};
use serde::Serialize;
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use crate::meta::ChildMeta;
use crate::status::{self, StatusKey};

/// The directory name a capture gets when no hook set a scope. It is not a
/// tool-use id and never pretends to be one: `Record::origin` says so, and
/// `tool_use_id` is null.
pub const USER_SHELL: &str = "user-shell";

/// One child's status, in the single shape a report, `ps --json`, and a
/// statusline all read. `build` is the one place that computes it, so a
/// renderer disagreeing with a report about the same child is a compile
/// error — a missing field — rather than a drift between call sites that
/// nothing catches.
#[derive(Debug, Serialize)]
pub struct Record {
    pub name: String,
    /// Raw, unlike `name` and the entries of `notes`: this is the same
    /// ledger identity `status::render` computes its own copy of, and
    /// `status.rs`'s policy for that identity is that a raw string is
    /// harmless to hold in JSON — only a terminal line is a contract. A
    /// consumer that prints `key` to a terminal must route it through
    /// `meta::escape_control` itself, exactly as `render` does before
    /// putting its escaped copy on a line.
    pub key: String,
    pub origin: &'static str, // "tool" | "user-shell"
    pub agent: Option<String>,
    /// `None` for a `!` command: there is no tool use to name.
    pub tool_use_id: Option<String>,
    /// `None` when `meta.json` will not read: there is no wrapper pid to
    /// report in that case, and `0` is a real pid, not a stand-in for that
    /// absence.
    pub wrapper_pid: Option<u32>,
    pub child_pid: Option<u32>,
    /// The wrapper's own start, stamped before the exec is attempted. For
    /// every key but `spawn-failed` that lands within milliseconds of the
    /// child's start; `spawn-failed` has no child to have started, so this
    /// dates the attempt instead, and a null `child_pid` is what tells the
    /// two cases apart.
    pub started_at: Option<DateTime<chrono::Local>>,
    /// Present only while the child is running and clocked; never alongside
    /// `ran_s`. Both are absent when `duration_s` has nothing to report: no
    /// meta was ever read, or the child is terminal with no reap recorded —
    /// `abandoned` and `spawn-failed`, in practice.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub elapsed_s: Option<f64>,
    /// Present only once the child has settled and a reap recorded when;
    /// never alongside `elapsed_s`. Absent for the same two keys `elapsed_s`
    /// is absent for — see `elapsed_s`.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ran_s: Option<f64>,
    pub last_byte_at: Option<DateTime<chrono::Local>>,
    pub last_byte_s: Option<f64>,
    pub bytes: u64,
    /// The real, openable file(s) backing this capture: one path for the
    /// merged shape, two for the split one — never the glob a rendered line
    /// carries, which nothing can `open()`. Always a list, even with one
    /// entry: a consumer that special-cased a bare string against a list
    /// would have to already know the merge decision just to parse this
    /// field, which is the one fact this field exists to carry.
    pub capture: Vec<String>,
    pub notes: Vec<String>,
    /// Stat failures that are not "file not created yet" — see
    /// `Status::stat_errors`. Omitted, not an empty array, on every normal
    /// run: a broken filesystem is the rare exception this field exists to
    /// surface, not a check every reader should have to make.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub stat_errors: Vec<String>,
    /// Whether the session that started this child is gone — a fact about
    /// the session, not about the child. Every record carries it, terminal
    /// ones included, so a child that finished normally hours ago reading
    /// `true` once its session ends is correct, not a leak. The leak is
    /// `Some(true)` on a record whose child is not terminal. `null` means
    /// the record cannot support the question.
    pub orphaned: Option<bool>,
    /// Not serialized: renderers select on it, readers read `key`. `key` is
    /// this same value's `Display`, kept for a Rust caller that wants to
    /// match the enum instead of a second string check that can drift from
    /// that `Display` — the statusline's `~` marker is `StatusKey::is_quiet`,
    /// not `key.starts_with(...)`.
    #[serde(skip)]
    pub status: StatusKey,
    /// Not serialized: renderers select on it, readers read `key`. A JSON
    /// reader tells a settled child from a running one by which array of the
    /// `Envelope` carries the record — `live` or `settled` — not by a field
    /// on the record itself.
    #[serde(skip)]
    pub terminal: bool,
}

impl Record {
    /// Derive one record from a capture directory. `group` is the third path
    /// component — a tool-use id, or `USER_SHELL`.
    pub fn build(dir: &Path, agent: Option<String>, group: &str, now: DateTime<Utc>) -> Record {
        let st = status::derive(dir, now);
        let key = st.key.to_string();
        let terminal = st.is_terminal();
        let duration = st.duration_s(now);
        // `status::name` is the one place that decides what a child is
        // called, cap included. Re-deriving the meta -> display_name ->
        // directory chain here would drop the 200-char cap `render` applies,
        // so the same status core would emit a capped name on one surface
        // and an uncapped one on the other.
        let name = status::name(dir, &st);
        let capture: Vec<String> = st
            .capture
            .paths(dir)
            .iter()
            .map(|p| p.display().to_string())
            .collect();
        // The tee opens a capture file before any byte reaches it, so an
        // mtime can exist with nothing written yet. `render`'s `age` line
        // gates on the byte count for the same reason; a record disagreeing
        // with it here would have a statusline and a report describe one
        // child differently at the same instant.
        let last_byte = (st.capture.bytes() > 0)
            .then_some(st.last_byte_at)
            .flatten();
        let user_shell = group == USER_SHELL;
        Record {
            name,
            key,
            origin: if user_shell { "user-shell" } else { "tool" },
            agent,
            tool_use_id: (!user_shell).then(|| group.to_string()),
            wrapper_pid: st.meta.as_ref().map(|m| m.wrapper_pid),
            child_pid: st.meta.as_ref().and_then(|m| m.child_pid),
            started_at: st
                .meta
                .as_ref()
                .map(|m| m.started_at.with_timezone(&chrono::Local)),
            elapsed_s: (!terminal).then_some(duration).flatten(),
            ran_s: terminal.then_some(duration).flatten(),
            last_byte_at: last_byte.map(|t| t.with_timezone(&chrono::Local)),
            last_byte_s: last_byte.map(|t| ((now - t).num_milliseconds() as f64 / 1000.0).max(0.0)),
            bytes: st.capture.bytes(),
            capture,
            notes: status::notes(&st),
            stat_errors: st.stat_errors.clone(),
            orphaned: st.orphaned(),
            status: st.key.clone(),
            terminal,
        }
    }
}

/// What a delivery could not carry as a full `Record`: the transport has a
/// byte budget and a busy session can hold far more children than that
/// affords. Grouped by key rather than listed by name, so the group itself
/// never grows past what the budget already refused to carry in full.
#[derive(Debug, Serialize)]
pub struct Withheld {
    pub by_key: BTreeMap<String, usize>,
    /// The command that shows every withheld child in full.
    pub retrieve_with: &'static str,
}

impl Default for Withheld {
    // A derived `Default` would give `retrieve_with` an empty string, and
    // `Envelope.withheld` has no `skip_serializing_if`, so a clean envelope
    // — nothing withheld — would carry an unusable command. `retrieve_with`
    // names how to see what this struct is short for; it is not a fact
    // `add` learns, and it holds even when `add` is never called.
    fn default() -> Self {
        Withheld {
            by_key: BTreeMap::new(),
            retrieve_with: "agent-tools ps --all",
        }
    }
}

impl Withheld {
    /// Buckets `spawn-failed` without its message. The message is free text
    /// off the wrapper's own `io::Error`, so keeping it in the key would open
    /// one bucket per child in a field whose whole job is to stay small.
    pub fn add(&mut self, key: &str) {
        let bucket = if key.starts_with("spawn-failed") {
            "spawn-failed".to_string()
        } else {
            key.to_string()
        };
        *self.by_key.entry(bucket).or_insert(0) += 1;
    }
}

/// One session's worth of children, in the shape `ps --json` and a
/// statusline both read.
#[derive(Debug, Serialize)]
pub struct Envelope {
    pub now: DateTime<chrono::Local>,
    pub session: String,
    pub live: Vec<Record>,
    /// Present only under `--all`, so `live` is never padded with a child
    /// that already settled — a field named `live` holding one would make
    /// the single selector every consumer needs into a lie.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub settled: Option<Vec<Record>>,
    pub withheld: Withheld,
}

/// One captured `agent-tools run` invocation on disk, as `ps` finds it.
///
/// It lives here rather than in `ps.rs` because it is the input every
/// renderer takes: the statusline builds records from it too, and a type two
/// modules need does not belong inside one of them.
pub struct Capture {
    pub agent_id: Option<String>,
    pub tool_use_id: String,
    /// Directory holding this capture: `stdout` and `stderr` when the streams were
    /// split, `output` when they were merged, plus `meta.json` either way.
    /// Layout: `<tool_use_id_dir>/<pid>/`.
    pub capture_dir: PathBuf,
    /// `None` when `meta.json` is absent or will not parse. The capture still
    /// exists and `status::derive` still has an answer for it — `abandoned` —
    /// so dropping it here would leave `ps` disagreeing with the report about
    /// whether the child exists at all.
    pub meta: Option<ChildMeta>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, Utc};
    use tempfile::TempDir;

    fn seed(dir: &std::path::Path, reaped: Option<i32>) {
        let now = Utc::now();
        let meta = serde_json::json!({
            "wrapper_pid": 4709u32,
            "wrapper_started_ticks": 1u64,
            "child_pid": 4711u32,
            "desc": "build",
            "command": ["make", "-j8"],
            "started_at": (now - Duration::seconds(191)).to_rfc3339(),
            "spawn_error": serde_json::Value::Null,
            "reaped": reaped.map(|s| serde_json::json!({
                "at": (now - Duration::seconds(60)).to_rfc3339(), "status": s
            })),
            "drained_at": reaped.map(|_| (now - Duration::seconds(60)).to_rfc3339()),
        });
        std::fs::write(dir.join("meta.json"), serde_json::to_vec(&meta).unwrap()).unwrap();
        std::fs::write(dir.join("output"), "hello").unwrap();
    }

    #[test]
    fn a_record_carries_the_facts_a_renderer_needs() {
        let d = TempDir::new().unwrap();
        seed(d.path(), Some(0));
        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert_eq!(v["name"], "build");
        assert_eq!(v["origin"], "tool");
        assert_eq!(v["tool_use_id"], "toolu_x");
        assert_eq!(v["wrapper_pid"], 4709);
        assert_eq!(v["child_pid"], 4711);
        assert_eq!(v["bytes"], 5);
        assert!(v["capture"][0].as_str().unwrap().ends_with("/output"));
        assert!(v["started_at"].as_str().unwrap().contains('T'));
        // `seed` writes no `claude_pid`/`claude_started_ticks` at all — the
        // shape any wrapper that never recorded a session writes — and both
        // fields default on read. A renderer surfaces `orphaned` directly,
        // so a record with nothing to answer the question must carry
        // `null`, not a guess in either direction.
        assert!(
            v["orphaned"].is_null(),
            "no claude_pid was ever recorded for this fixture: {v}"
        );
    }

    /// `seed` writes `wrapper_started_ticks: 1`, which cannot match a live
    /// process, so those fixtures always derive terminal. A live record needs a
    /// wrapper that really is alive: this one.
    #[test]
    fn a_live_record_carries_elapsed_and_no_ran() {
        let d = TempDir::new().unwrap();
        let pid = std::process::id();
        let ticks = crate::procstat::start_ticks(pid).unwrap();
        let meta = serde_json::json!({
            "wrapper_pid": pid,
            "wrapper_started_ticks": ticks,
            "child_pid": pid + 1,
            "desc": "build",
            "command": ["sleep", "9999"],
            "started_at": (Utc::now() - Duration::seconds(191)).to_rfc3339(),
            "spawn_error": serde_json::Value::Null,
            "reaped": serde_json::Value::Null,
            "drained_at": serde_json::Value::Null,
        });
        std::fs::write(
            d.path().join("meta.json"),
            serde_json::to_vec(&meta).unwrap(),
        )
        .unwrap();
        std::fs::write(d.path().join("output"), "hello").unwrap();

        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        assert!(!r.terminal, "a live wrapper with no reap is not terminal");
        let v = serde_json::to_value(&r).unwrap();
        assert!(v["elapsed_s"].as_f64().unwrap() > 190.0, "{v}");
        assert!(
            v.get("ran_s").is_none(),
            "a running child has not `ran` anything yet: {v}"
        );
    }

    #[test]
    fn a_user_shell_record_names_no_tool_use() {
        let d = TempDir::new().unwrap();
        seed(d.path(), Some(0));
        let r = Record::build(d.path(), None, USER_SHELL, Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert_eq!(v["origin"], "user-shell");
        assert!(
            v["tool_use_id"].is_null(),
            "a ! command has no tool use to name"
        );
    }

    #[test]
    fn a_terminal_record_carries_ran_and_no_elapsed() {
        let d = TempDir::new().unwrap();
        seed(d.path(), Some(1));
        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert_eq!(v["key"], "final(1)");
        // `seed`'s reap sits 131s after its start (191s ago to 60s ago): the
        // clock must stop there, not keep running to `now`.
        assert!(
            (v["ran_s"].as_f64().unwrap() - 131.0).abs() < 1.0,
            "the clock must stop at the reap: {v}"
        );
        assert!(
            v.get("elapsed_s").is_none(),
            "a settled child's clock stopped: {v}"
        );
    }

    #[test]
    fn withheld_groups_spawn_failures_without_their_messages() {
        let mut w = Withheld::default();
        w.add("final(0)");
        w.add("final(0)");
        w.add("final(1)");
        w.add("spawn-failed(No such file or directory)");
        w.add("spawn-failed(Permission denied)");
        assert_eq!(w.by_key.get("final(0)"), Some(&2));
        assert_eq!(w.by_key.get("final(1)"), Some(&1));
        assert_eq!(
            w.by_key.get("spawn-failed"),
            Some(&2),
            "free-text messages must not each open a bucket: {:?}",
            w.by_key
        );
        assert_eq!(
            w.retrieve_with, "agent-tools ps --all",
            "the command must hold regardless of what add saw"
        );
    }

    /// The shape every `Command::output()` harness produces, and almost no
    /// production run does — `paths` must still name both real files, not
    /// the `{stdout,stderr}` glob a rendered line carries.
    #[test]
    fn a_split_capture_lists_both_real_paths_not_a_glob() {
        let d = TempDir::new().unwrap();
        let now = Utc::now();
        let meta = serde_json::json!({
            "wrapper_pid": 4709u32,
            "wrapper_started_ticks": 1u64,
            "child_pid": 4711u32,
            "desc": "build",
            "command": ["make", "-j8"],
            "started_at": (now - Duration::seconds(191)).to_rfc3339(),
            "spawn_error": serde_json::Value::Null,
            "reaped": serde_json::json!({
                "at": (now - Duration::seconds(60)).to_rfc3339(), "status": 0
            }),
            "drained_at": (now - Duration::seconds(60)).to_rfc3339(),
        });
        std::fs::write(
            d.path().join("meta.json"),
            serde_json::to_vec(&meta).unwrap(),
        )
        .unwrap();
        // No merged `output` file, so the shape is `Capture::Split`.
        std::fs::write(d.path().join("stdout"), "out").unwrap();
        std::fs::write(d.path().join("stderr"), "err").unwrap();

        let r = Record::build(d.path(), None, "toolu_x", Utc::now());
        assert_eq!(
            r.capture,
            vec![
                d.path().join("stdout").display().to_string(),
                d.path().join("stderr").display().to_string(),
            ],
            "a split capture must list both real paths, not a `{{stdout,stderr}}` glob"
        );
    }

    /// Mirrors `status::tests::a_stat_failure_is_reported_not_read_as_no_output`:
    /// a filesystem problem must reach the pulled record, not just the pushed
    /// line, or a broken capture reads as a healthy idle child on one surface.
    #[test]
    fn a_stat_failure_reaches_the_record_not_just_the_line() {
        let d = TempDir::new().unwrap();
        let not_a_dir = d.path().join("regular_file");
        std::fs::write(&not_a_dir, b"x").unwrap();
        let r = Record::build(&not_a_dir, None, "toolu_x", Utc::now());
        let v = serde_json::to_value(&r).unwrap();
        assert!(
            v["stat_errors"].as_array().is_some_and(|a| !a.is_empty()),
            "a broken filesystem must not read as a healthy idle child: {v}"
        );
    }
}
