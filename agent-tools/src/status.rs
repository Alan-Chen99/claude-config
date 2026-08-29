use chrono::{DateTime, Utc};
use std::fmt;
use std::path::Path;

use crate::core;
use crate::meta::{self, ChildMeta};
use crate::procstat;

/// Longest name a report line carries, so `hook_post::bound` can never select a
/// line larger than the whole report budget: that child's change would be
/// announced as omitted at every delivery point and never actually delivered.
///
/// The name is capped because it is the field a caller chooses. It is not the
/// only unbounded one — `merge`, `capture_error` and `spawn_error` all reach a
/// line from `meta.json` at whatever length the record holds. They are escaped
/// rather than capped, since every producer is a wrapper-authored `io::Error`
/// or one of `decide_merge`'s own literals, so length is bounded in practice
/// while a hand-edited record's newlines are not. `agent-tools/CLAUDE.md`,
/// "Report lines", carries the same enumeration.
const NAME_MAX: usize = 200;

/// Quiet thresholds, ascending. Configuration, not contract.
pub const QUIET_BUCKETS: &[(i64, &str)] = &[(30, "30s"), (300, "5m"), (1800, "30m"), (7200, "2h")];

/// What the capture directory holds. The merge decision fixes the shape: one
/// `output` file when the child's two streams shared a destination, `stdout`
/// and `stderr` when they did not. A line describing the other shape reports
/// zero bytes for a child that is producing, and points the reader at files
/// that were never opened.
///
/// `core::Merge` is the decision this records: it fixes how many files a run
/// opens, and this is how many a reader finds.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Capture {
    /// One file, `output`.
    Merged(u64),
    /// Two files, `stdout` and `stderr`.
    Split { out: u64, err: u64 },
}

impl Capture {
    /// What the child has written, however many files hold it.
    pub fn bytes(&self) -> u64 {
        match *self {
            Capture::Merged(n) => n,
            Capture::Split { out, err } => out + err,
        }
    }

    /// The byte counts a line carries, and the capture paths it ends with.
    fn detail(&self, dir: &Path) -> (String, String) {
        match *self {
            Capture::Merged(n) => (format!("output={n}B"), format!("{}/output", dir.display())),
            Capture::Split { out, err } => (
                format!("out={out}B err={err}B"),
                format!("{}/{{stdout,stderr}}", dir.display()),
            ),
        }
    }
}

/// A child's status. The rendered form is both the ledger identity that decides
/// whether something is reported twice and text quoted in the system prompt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StatusKey {
    SpawnFailed(String),
    Producing,
    Quiet(&'static str),
    Exited(i32),
    Final(i32),
    Abandoned,
}

impl fmt::Display for StatusKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StatusKey::SpawnFailed(e) => write!(f, "spawn-failed({e})"),
            StatusKey::Producing => write!(f, "producing"),
            StatusKey::Quiet(b) => write!(f, "quiet({b})"),
            StatusKey::Exited(c) => write!(f, "exited({c})"),
            StatusKey::Final(c) => write!(f, "final({c})"),
            StatusKey::Abandoned => write!(f, "abandoned"),
        }
    }
}

impl StatusKey {
    /// Terminal keys end watching: the child's fate is settled and cannot change.
    /// The set is the 2026-08-26 spec's, not a second definition — `ps` selects
    /// live children by the negation of this, and the report ranks by it.
    pub fn is_terminal(&self) -> bool {
        match self {
            StatusKey::SpawnFailed(_) | StatusKey::Final(_) | StatusKey::Abandoned => true,
            StatusKey::Producing | StatusKey::Quiet(_) | StatusKey::Exited(_) => false,
        }
    }
}

/// A child's current status: the key that decides reporting, plus the detail
/// rendered alongside it.
pub struct Status {
    pub key: StatusKey,
    pub meta: Option<ChildMeta>,
    pub last_byte_at: Option<DateTime<Utc>>,
    pub capture: Capture,
    /// Stat failures that are not "file not created yet". Surfaced in the
    /// rendered line so a filesystem problem cannot pass for an idle child.
    pub stat_errors: Vec<String>,
}

impl Status {
    pub fn is_terminal(&self) -> bool {
        self.key.is_terminal()
    }

    /// How long the child has run: to `now` while it is live, to the reap once it
    /// is terminal. A settled child's clock has stopped, and a duration that kept
    /// growing after it would describe waiting, not running.
    ///
    /// `None` when there is nothing to measure. Two shapes have nothing: a
    /// capture whose `meta.json` will not read, and a terminal status with no
    /// reap. `abandoned` is the second: the wrapper vanished without observing an
    /// end, so the child may still be running, and any number here would assert an
    /// end nobody saw. `spawn-failed` is the second too, for the opposite reason —
    /// nothing ran. A status without a duration is not a missing answer; it is the
    /// answer.
    pub fn duration_s(&self, now: DateTime<Utc>) -> Option<f64> {
        let m = self.meta.as_ref()?;
        let end = match (self.is_terminal(), m.reaped) {
            (true, Some(r)) => r.at,
            (true, None) => return None,
            // Live, whether or not a reap exists. `exited` has one and is still
            // open: the child is gone but the drain is not, so the capture can
            // still grow. Testing `reaped` here instead of the key would freeze
            // that child at its reap for however long a descendant holds the
            // inherited pipes.
            (false, _) => now,
        };
        Some(((end - m.started_at).num_milliseconds() as f64 / 1000.0).max(0.0))
    }
}

/// Returns (bytes, mtime, stat failure other than "not created yet").
///
/// A missing capture file is ordinary: the parent directory exists before the
/// tee opens either stream. Any other stat failure is a real filesystem problem,
/// and reading it as "no output" would understate a child that is in fact busy.
fn file_facts(dir: &Path, name: &str) -> (u64, Option<DateTime<Utc>>, Option<String>) {
    match std::fs::metadata(dir.join(name)) {
        Ok(md) => (
            md.len(),
            md.modified().ok().map(DateTime::<Utc>::from),
            None,
        ),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (0, None, None),
        Err(e) => (0, None, Some(format!("{name}: {e}"))),
    }
}

/// Truncate on a char boundary, marking that it happened.
pub(crate) fn cap_to(s: &str, max: usize) -> String {
    if s.chars().count() <= max {
        return s.to_string();
    }
    s.chars().take(max).chain(['\u{2026}']).collect()
}

fn cap(name: &str) -> String {
    cap_to(name, NAME_MAX)
}

/// A duration a reader takes in without arithmetic. Seconds below a minute,
/// minutes and zero-padded seconds below an hour, hours and zero-padded minutes
/// above. Never a bare float: `191.7s` makes a reader do the division that this
/// is here to have already done.
pub fn fmt_duration(secs: f64) -> String {
    let s = secs.max(0.0).round() as i64;
    if s < 60 {
        format!("{s}s")
    } else if s < 3600 {
        format!("{}m{:02}s", s / 60, s % 60)
    } else {
        format!("{}h{:02}m", s / 3600, (s % 3600) / 60)
    }
}

/// The local rendering of an instant, for a time read in the terminal it was
/// printed to. A UTC instant rendered with no zone reads as local: a reader
/// correlating it against `date` is wrong by the offset with nothing on the
/// line saying so. The conversion is here rather than at each display site so
/// that no site can render the instant raw.
pub fn fmt_local_hms(t: DateTime<Utc>) -> String {
    t.with_timezone(&chrono::Local)
        .format("%H:%M:%S")
        .to_string()
}

/// The stamp a pushed report carries in its header. Local, with the offset,
/// because a report line outlives the terminal it was printed to and is re-read
/// after a compaction, when nothing else on the line says when "4s ago" was.
pub fn fmt_local_stamp(t: DateTime<Utc>) -> String {
    t.with_timezone(&chrono::Local)
        .format("%H:%M:%S %z")
        .to_string()
}

fn largest_bucket(age_secs: i64) -> Option<&'static str> {
    QUIET_BUCKETS
        .iter()
        .rev()
        .find(|(secs, _)| age_secs >= *secs)
        .map(|(_, label)| *label)
}

/// Derive the current status of one capture directory. Total: every input
/// combination yields exactly one key. Rows are evaluated in order.
pub fn derive(dir: &Path, now: DateTime<Utc>) -> Status {
    let (out_bytes, out_mtime, out_err) = file_facts(dir, "stdout");
    let (err_bytes, err_mtime, err_err) = file_facts(dir, "stderr");
    let (merged_bytes, merged_mtime, merged_err) = file_facts(dir, "output");
    // A merged run opens `output` and nothing else, so the file that is there
    // names the shape. Before any tee has opened one there is nothing to name,
    // and the two-file form is what a line has always carried.
    let capture = match merged_mtime {
        Some(_) => Capture::Merged(merged_bytes),
        None => Capture::Split {
            out: out_bytes,
            err: err_bytes,
        },
    };
    let last_byte_at = out_mtime.max(err_mtime).max(merged_mtime);
    let stat_errors: Vec<String> = [out_err, err_err, merged_err]
        .into_iter()
        .flatten()
        .collect();

    let Ok(m) = meta::read_meta(dir) else {
        // A capture that cannot be described is never silently dropped.
        return Status {
            key: StatusKey::Abandoned,
            meta: None,
            last_byte_at,
            capture,
            stat_errors,
        };
    };

    let key = if let Some(e) = m.spawn_error.clone() {
        StatusKey::SpawnFailed(e)
    } else {
        let alive = procstat::is_alive(m.wrapper_pid, m.wrapper_started_ticks);
        match (m.drained_at.is_some(), m.reaped, alive) {
            (true, Some(r), _) => StatusKey::Final(r.status),
            (_, Some(r), true) => StatusKey::Exited(r.status),
            (_, Some(r), false) => StatusKey::Final(r.status),
            // Drained without a reap cannot be produced by run.rs; treat the
            // corrupt record the same as a wrapper that vanished.
            (_, None, false) => StatusKey::Abandoned,
            (_, None, true) => {
                let anchor = last_byte_at.unwrap_or(m.started_at);
                let age = (now - anchor).num_seconds().max(0);
                match largest_bucket(age) {
                    Some(b) => StatusKey::Quiet(b),
                    None => StatusKey::Producing,
                }
            }
        }
    };

    Status {
        key,
        meta: Some(m),
        last_byte_at,
        capture,
        stat_errors,
    }
}

/// The name a report line — or a group in a collapsed report line — identifies
/// a child by: its `--desc`, capped and escaped, or the capture directory when
/// no meta could be read at all.
///
/// A shared function rather than two call sites computing it separately. A
/// `--desc` is free text and `escape_control` does not touch `[`, so recovering
/// a name by re-splitting an already-rendered line at " [" cuts a desc like
/// `build [stage 2]` at its own bracket; reading it once here and passing it
/// along is what keeps a child's name the same everywhere it is shown.
pub fn name(dir: &Path, s: &Status) -> String {
    let raw = s
        .meta
        .as_ref()
        .map(|m| m.display_name())
        .unwrap_or_else(|| dir.display().to_string());
    cap(&raw)
}

/// One rendered line: name, key, detail, capture paths.
pub fn render(dir: &Path, s: &Status, now: DateTime<Utc>) -> String {
    let name = name(dir, s);
    // The capture files are created when the tee opens them, so an mtime exists
    // before any byte does. Byte counts, not mtime, decide whether output happened.
    let age = match s.last_byte_at {
        Some(t) if s.capture.bytes() > 0 => {
            format!("last byte {}s ago", (now - t).num_seconds().max(0))
        }
        _ => "no output".to_string(),
    };
    let problems = if s.stat_errors.is_empty() {
        String::new()
    } else {
        format!(" [stat failed: {}]", s.stat_errors.join("; "))
    };
    let pid = s
        .meta
        .as_ref()
        .and_then(|m| m.child_pid)
        .map(|p| p.to_string())
        .unwrap_or_else(|| "-".into());
    // Everything that explains a difference from bare, so `final(0)` never sits
    // beside a capture that stopped growing an hour ago. Empty on a clean run,
    // which is nearly every run: these lines land in every tool result, and a
    // note that is always there stops being read.
    let mut notes: Vec<String> = Vec::new();
    // A split says something only when the caller's own two descriptors reached
    // one destination and the rule declined anyway: then the capture is two
    // files where one would have been faithful, and the interleaving between
    // them is gone. When the descriptors provably reached two destinations,
    // bare kept them apart too and there is nothing to explain — and that is
    // the shape every `Command::output()` harness has, so noting it would put a
    // note on every line of every test run while production, which merges, got
    // none. `s.capture` is where the shape is known, read off the files that
    // exist; `meta.merge` supplies only the condition.
    if let (Capture::Split { .. }, Some(why)) =
        (&s.capture, s.meta.as_ref().and_then(|m| m.merge.as_deref()))
    {
        if why != core::DESTINATIONS_ALREADY_DIFFERED {
            notes.push(format!("streams split: {}", meta::escape_control(why)));
        }
    }
    if s.meta.as_ref().is_some_and(|m| m.forward_closed) {
        notes.push("downstream closed".to_string());
    }
    if s.meta.as_ref().is_some_and(|m| m.drain_capped) {
        notes.push("drain capped".to_string());
    }
    if let Some(e) = s.meta.as_ref().and_then(|m| m.capture_error.as_deref()) {
        notes.push(format!("capture failed: {}", meta::escape_control(e)));
    }
    let notes = if notes.is_empty() {
        String::new()
    } else {
        format!(" [{}]", notes.join("; "))
    };
    let (bytes, paths) = s.capture.detail(dir);
    // The key carries `spawn_error`, the last of this line's four fields to
    // come off the record, and it is bounded here rather than in `derive`: the
    // raw string is the ledger identity, which is JSON and holds a newline
    // harmlessly, while a line is a contract. Escaping the whole rendered key
    // rather than the one variant carrying text is what stops a later variant
    // reopening this. A record read off disk is not trustworthy input, whatever
    // this process's own producers put there.
    let key = meta::escape_control(&s.key.to_string());
    // Start and duration, in the two shapes the spec fixes: a live child is
    // still accumulating and says so with `+`; a terminal one reports the total
    // it finished with.
    let timing = match (s.meta.as_ref(), s.duration_s(now)) {
        (Some(m), Some(d)) if s.is_terminal() => Some(format!(
            "started {}, ran {}",
            fmt_local_hms(m.started_at),
            fmt_duration(d)
        )),
        (Some(m), Some(d)) => Some(format!(
            "started {} (+{})",
            fmt_local_hms(m.started_at),
            fmt_duration(d)
        )),
        // A terminal child with no duration: `abandoned`, where the wrapper
        // vanished before observing an end, and `spawn-failed`, where nothing
        // ran to have one. Neither has a span to report, and a number here
        // would assert one. The record's start is what there is.
        (Some(m), None) => Some(format!("started {}", fmt_local_hms(m.started_at))),
        // No meta to read a start from.
        (None, _) => None,
    };
    // The separator lives here, not in the arms: an arm that returned its own
    // trailing `, ` would let the next arm added omit it and splice `started
    // 12:00:00` onto the age with nothing between them.
    let timing = timing.map_or(String::new(), |t| format!("{t}, "));
    format!("{name} [{key}] pid {pid}, {timing}{age}, {bytes}{notes}{problems} -> {paths}")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::meta::{ChildMeta, Reaped};
    use chrono::{Duration, Utc};
    use tempfile::TempDir;

    fn base() -> ChildMeta {
        ChildMeta {
            wrapper_pid: std::process::id(),
            wrapper_started_ticks: crate::procstat::start_ticks(std::process::id()).unwrap(),
            child_pid: Some(999_999),
            desc: Some("t".into()),
            command: vec!["true".into()],
            started_at: Utc::now(),
            spawn_error: None,
            reaped: None,
            drained_at: None,
            merge: None,
            forward_closed: false,
            drain_capped: false,
            capture_error: None,
        }
    }

    fn dead() -> ChildMeta {
        // pid 0 has no /proc entry, so liveness is false.
        ChildMeta {
            wrapper_pid: 0,
            wrapper_started_ticks: 1,
            ..base()
        }
    }

    fn write(dir: &TempDir, m: &ChildMeta) {
        crate::meta::write_meta(dir.path(), m).unwrap();
    }

    #[test]
    fn spawn_failure_wins_over_everything() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.spawn_error = Some("boom".into());
        m.reaped = Some(Reaped {
            at: Utc::now(),
            status: 0,
        });
        write(&d, &m);
        assert!(matches!(
            derive(d.path(), Utc::now()).key,
            StatusKey::SpawnFailed(_)
        ));
    }

    #[test]
    fn drained_is_final() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.reaped = Some(Reaped {
            at: Utc::now(),
            status: 3,
        });
        m.drained_at = Some(Utc::now());
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Final(3));
    }

    #[test]
    fn reaped_with_live_wrapper_is_exited() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.reaped = Some(Reaped {
            at: Utc::now(),
            status: 0,
        });
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Exited(0));
    }

    #[test]
    fn reaped_with_dead_wrapper_is_final() {
        let d = TempDir::new().unwrap();
        let mut m = dead();
        m.reaped = Some(Reaped {
            at: Utc::now(),
            status: 5,
        });
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Final(5));
    }

    #[test]
    fn unreaped_with_dead_wrapper_is_abandoned() {
        let d = TempDir::new().unwrap();
        write(&d, &dead());
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Abandoned);
    }

    #[test]
    fn unreadable_meta_is_abandoned() {
        let d = TempDir::new().unwrap();
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Abandoned);
    }

    #[test]
    fn recent_output_is_producing() {
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("stdout"), b"hi").unwrap();
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Producing);
    }

    #[test]
    fn quiet_picks_the_largest_crossed_bucket() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.started_at = Utc::now() - Duration::seconds(4000);
        write(&d, &m);
        // No capture files at all: measured from started_at, 4000s ago.
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Quiet("30m"));
    }

    #[test]
    fn bucket_boundaries_are_inclusive() {
        // An anchor exactly on a boundary is quiet, never producing.
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.started_at = Utc::now() - Duration::seconds(30);
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Quiet("30s"));
    }

    #[test]
    fn drained_without_a_reap_never_invents_a_status() {
        let d = TempDir::new().unwrap();
        let mut m = dead();
        m.drained_at = Some(Utc::now());
        m.reaped = None;
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Abandoned);
    }

    #[test]
    fn render_says_no_output_when_nothing_was_written() {
        // The capture file exists from the moment the tee opens it, so its mtime
        // predates any byte. A line claiming a "last byte" next to out=0B is a
        // contradiction the reader has to resolve.
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("stdout"), b"").unwrap();
        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(line.contains("no output"), "line: {line}");
        assert!(!line.contains("last byte"), "line: {line}");
    }

    #[test]
    fn render_names_the_child_its_key_and_its_bytes() {
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("stdout"), b"hello").unwrap();
        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(line.contains("[producing]"), "line: {line}");
        assert!(line.contains("out=5B"), "line: {line}");
        assert!(line.contains("last byte"), "line: {line}");
    }

    #[test]
    fn a_merged_capture_is_not_reported_silent_while_it_is_producing() {
        // A merged run writes `output` and never opens `stdout` or `stderr`.
        // Reading only the two split names finds nothing, falls back to
        // `started_at` as the anchor, and keys a streaming child as quiet.
        // Here `started_at` is old enough to reach the 30m bucket, so the key
        // is decided by whether the merged file's mtime is seen at all.
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.started_at = Utc::now() - Duration::seconds(4000);
        write(&d, &m);
        std::fs::write(d.path().join("output"), b"hello").unwrap();

        let now = Utc::now();
        let s = derive(d.path(), now);
        assert_eq!(s.key, StatusKey::Producing, "the merged file is the anchor");
        assert_eq!(s.capture, Capture::Merged(5));

        let line = render(d.path(), &s, now);
        assert!(line.contains("output=5B"), "line: {line}");
        assert!(line.contains("last byte"), "line: {line}");
        assert!(!line.contains("no output"), "line: {line}");
    }

    #[test]
    fn a_line_names_only_capture_files_that_are_there() {
        let d = TempDir::new().unwrap();
        write(&d, &base());
        std::fs::write(d.path().join("output"), b"x").unwrap();
        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(
            line.ends_with(&format!("{}/output", d.path().display())),
            "line: {line}"
        );
        assert!(
            !line.contains("{stdout,stderr}"),
            "a merged run opens neither: {line}"
        );
    }

    #[test]
    fn a_difference_from_bare_is_readable_beside_the_key() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.merge = Some("not both writable".into());
        m.forward_closed = true;
        // The bound applies only once forwarding has failed, so the two facts
        // are true together or the record describes a run that cannot happen.
        m.drain_capped = true;
        m.capture_error = Some("No space left on device".into());
        write(&d, &m);
        std::fs::write(d.path().join("stdout"), b"x").unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        // The whole bracket group, not one `contains` per note: the prompt
        // promises this order, and a `contains` per note holds whichever order
        // `render` emits them in, so swapping two `notes.push` blocks would
        // leave every note present and this test green. The bounding spaces
        // make this the group's entire content rather than a substring of it.
        let segment = " [streams split: not both writable; downstream closed; drain capped; \
             capture failed: No space left on device] ";
        assert!(line.contains(segment), "line: {line}");

        // The one split that is not a difference from bare: two destinations
        // stayed two, so there is nothing to explain. This is also the shape of
        // every harness that spawns with two pipes, which is why a note here
        // would be on every test line and no production one. What remains
        // closes up in the same order.
        m.merge = Some(core::DESTINATIONS_ALREADY_DIFFERED.into());
        write(&d, &m);
        let line = render(d.path(), &derive(d.path(), now), now);
        let segment =
            " [downstream closed; drain capped; capture failed: No space left on device] ";
        assert!(line.contains(segment), "line: {line}");
        assert!(
            !line.contains("streams split"),
            "a split that kept nothing apart explains nothing: {line}"
        );
    }

    #[test]
    fn a_split_that_lost_the_interleaving_is_noted() {
        // The rule declined to merge two descriptors that did reach one
        // destination: the capture is two files where one would have been
        // faithful, and the order between them is gone. That is the split the
        // note exists for, and it is the one no harness produces by accident.
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.merge = Some("same file, but not both appending".into());
        write(&d, &m);
        std::fs::write(d.path().join("stdout"), b"x").unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(
            line.contains("streams split: same file, but not both appending"),
            "line: {line}"
        );
    }

    #[test]
    fn a_clean_run_carries_no_notes() {
        // Nearly every run is this one, and these lines land in every tool
        // result: a note that is always there stops being read.
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.merge = Some("both appending, same file".into());
        write(&d, &m);
        std::fs::write(d.path().join("output"), b"x").unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(
            !line.contains("streams split"),
            "a merged run explains nothing: {line}"
        );
        // The status key is bracketed too, so counting is what distinguishes a
        // clean line from one carrying notes. Blunt on purpose: a note added
        // unconditionally fails here rather than in the field.
        assert_eq!(
            line.matches('[').count(),
            1,
            "the key is the only bracketed segment: {line}"
        );
    }

    #[test]
    fn a_stat_failure_is_reported_not_read_as_no_output() {
        // A path component that is a regular file yields ENOTDIR, which is not
        // NotFound and must not be collapsed into "this child wrote nothing".
        let d = TempDir::new().unwrap();
        let not_a_dir = d.path().join("regular_file");
        std::fs::write(&not_a_dir, b"x").unwrap();
        let now = Utc::now();
        let s = derive(&not_a_dir, now);
        assert!(
            !s.stat_errors.is_empty(),
            "a non-NotFound stat error must survive"
        );
        assert!(render(&not_a_dir, &s, now).contains("stat failed"));
    }

    #[test]
    fn key_strings_are_stable_ledger_identities() {
        assert_eq!(StatusKey::Producing.to_string(), "producing");
        assert_eq!(StatusKey::Quiet("5m").to_string(), "quiet(5m)");
        assert_eq!(StatusKey::Exited(2).to_string(), "exited(2)");
        assert_eq!(StatusKey::Final(0).to_string(), "final(0)");
        assert_eq!(StatusKey::Abandoned.to_string(), "abandoned");
    }

    #[test]
    fn render_keeps_one_child_on_one_line() {
        // A multi-line `bash -c` script with no --desc is enough to reach this.
        let dir = TempDir::new().unwrap();
        let m = ChildMeta {
            desc: None,
            command: vec!["bash".into(), "-c".into(), "echo first\necho second".into()],
            ..base()
        };
        write(&dir, &m);
        let now = Utc::now();
        let line = render(dir.path(), &derive(dir.path(), now), now);
        assert!(!line.contains('\n'), "rendered over two lines: {line}");
    }

    /// A `meta.json` written by hand, carrying a newline and an ANSI sequence
    /// in every field a line takes from the record: the name, and the
    /// `spawn_error`, `merge`, and `capture_error` strings. One such record
    /// made `agent-tools ps` emit a second physical line, reading as a status
    /// line for a child that does not exist. No field here is child-controlled
    /// — every producer is a wrapper-authored `io::Error`, an anyhow chain, or
    /// one of `decide_merge`'s static conditions — but a record read off disk
    /// is not trustworthy input, and a malformed one costs that record, not the
    /// history. All four fields in one test, because a field left plain here is
    /// a field nothing covers.
    #[test]
    fn a_hand_written_record_cannot_forge_a_second_line() {
        let d = TempDir::new().unwrap();
        // pid 0 has no /proc entry, so nothing here depends on a live wrapper.
        // No capture file is written either, so the shape is `Capture::Split` —
        // which is what the `merge` note needs in order to be rendered at all.
        std::fs::write(
            d.path().join("meta.json"),
            r#"{
              "wrapper_pid": 0,
              "wrapper_started_ticks": 1,
              "child_pid": 4242,
              "desc": "probe\n  forged [final(0)] pid 3\u001b[31m",
              "command": ["true"],
              "started_at": "2026-08-26T12:00:00Z",
              "spawn_error": "boom\n  forged [final(0)] pid 1\u001b[31m",
              "reaped": null,
              "drained_at": null,
              "merge": "same file\n  forged [final(0)] pid 4\u001b[31m",
              "capture_error": "no space\n  forged [final(0)] pid 2\u001b[31m"
            }"#,
        )
        .unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(!line.contains('\n'), "rendered over two lines: {line}");
        assert!(
            !line.contains('\u{1b}'),
            "an escape sequence reached the terminal: {line}"
        );
        assert!(
            line.contains("probe\\n  forged"),
            "the name is shown, not obeyed: {line}"
        );
        assert!(
            line.contains("boom\\n  forged"),
            "the spawn error is shown, not obeyed: {line}"
        );
        assert!(
            line.contains("streams split: same file\\n  forged"),
            "the merge condition is shown, not obeyed: {line}"
        );
        assert!(
            line.contains("no space\\n  forged"),
            "the capture error is shown, not obeyed: {line}"
        );
    }

    #[test]
    fn render_caps_the_name_so_a_line_can_always_fit_a_report() {
        // The name is the only unbounded field in a line. A line longer than the
        // whole report budget can never be selected, so its change would be
        // announced as omitted at every delivery point and never delivered.
        let dir = TempDir::new().unwrap();
        let m = ChildMeta {
            desc: Some("x".repeat(20_000)),
            ..base()
        };
        write(&dir, &m);
        let now = Utc::now();
        let line = render(dir.path(), &derive(dir.path(), now), now);
        assert!(line.len() < 1_000, "line is {} bytes: {line}", line.len());
        assert!(
            line.contains('\u{2026}'),
            "truncation must be visible: {line}"
        );
        assert!(
            line.contains("{stdout,stderr}"),
            "the capture path survives: {line}"
        );
    }

    #[test]
    fn a_live_child_measures_to_now() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        let now = Utc::now();
        m.started_at = now - Duration::seconds(191);
        write(&dir, &m);
        let st = derive(dir.path(), now);
        assert!(
            !st.is_terminal(),
            "a live wrapper with no reap is not terminal"
        );
        let d = st.duration_s(now).expect("a started child has a duration");
        assert!((d - 191.0).abs() < 1.0, "duration was {d}");
    }

    #[test]
    fn a_terminal_child_measures_to_its_reap_not_to_now() {
        let dir = TempDir::new().unwrap();
        let mut m = dead();
        let started = Utc::now() - Duration::seconds(4020);
        m.started_at = started;
        m.reaped = Some(Reaped {
            at: started + Duration::seconds(242),
            status: 1,
        });
        m.drained_at = Some(started + Duration::seconds(242));
        write(&dir, &m);
        let now = Utc::now();
        let st = derive(dir.path(), now);
        assert!(
            st.is_terminal(),
            "a drained, reaped, dead wrapper is terminal"
        );
        let d = st.duration_s(now).expect("a reaped child has a duration");
        assert!(
            (d - 242.0).abs() < 1.0,
            "the clock must stop at the reap, got {d}"
        );
    }

    #[test]
    fn a_draining_child_measures_to_now_not_to_its_reap() {
        // `exited` is the only key where a reap exists and the status is not
        // settled: the child is gone, the wrapper is still draining, and a
        // descendant holding the inherited pipes can stretch that out
        // indefinitely. The clock stops because the status is terminal, not
        // because a reap was recorded -- branch on `m.reaped` instead and this
        // child's duration freezes at a few seconds while the task stays open.
        let d = TempDir::new().unwrap();
        let mut m = base();
        let started = Utc::now() - Duration::seconds(600);
        m.started_at = started;
        m.reaped = Some(Reaped {
            at: started + Duration::seconds(5),
            status: 0,
        });
        m.drained_at = None;
        write(&d, &m);
        let now = Utc::now();
        let st = derive(d.path(), now);
        assert_eq!(st.key, StatusKey::Exited(0));
        assert!(!st.is_terminal(), "a draining capture can still grow");
        let secs = st.duration_s(now).expect("a started child has a duration");
        assert!(
            (secs - 600.0).abs() < 1.0,
            "a draining child is still open, got {secs}"
        );
    }

    #[test]
    fn an_abandoned_child_has_no_duration_because_nothing_observed_an_end() {
        // The wrapper vanished without recording a reap, so this child's fate is
        // unknown -- it may still be running. A duration here would grow without
        // bound under a key that says the watching is over.
        let d = TempDir::new().unwrap();
        let mut m = dead();
        m.started_at = Utc::now() - Duration::seconds(4020);
        m.reaped = None;
        m.drained_at = None;
        write(&d, &m);
        let now = Utc::now();
        let st = derive(d.path(), now);
        assert_eq!(st.key, StatusKey::Abandoned);
        assert_eq!(st.duration_s(now), None);
    }

    #[test]
    fn a_child_with_no_meta_has_no_duration() {
        let dir = TempDir::new().unwrap();
        let st = derive(dir.path(), Utc::now());
        assert_eq!(st.key, StatusKey::Abandoned);
        assert_eq!(st.duration_s(Utc::now()), None);
    }

    #[test]
    fn every_key_is_classified_as_terminal_or_not() {
        assert!(StatusKey::Final(0).is_terminal());
        assert!(StatusKey::Abandoned.is_terminal());
        assert!(StatusKey::SpawnFailed("x".into()).is_terminal());
        assert!(!StatusKey::Producing.is_terminal());
        assert!(!StatusKey::Quiet("30s").is_terminal());
        assert!(!StatusKey::Exited(0).is_terminal());
    }

    #[test]
    fn a_duration_reads_at_a_glance() {
        assert_eq!(fmt_duration(4.0), "4s");
        assert_eq!(fmt_duration(59.4), "59s");
        assert_eq!(fmt_duration(191.0), "3m11s");
        assert_eq!(fmt_duration(242.0), "4m02s");
        assert_eq!(fmt_duration(3720.0), "1h02m");
        assert_eq!(fmt_duration(0.0), "0s");
        // Rounding runs before the tier is chosen. Choosing the tier from the
        // unrounded seconds instead passes every assertion above and renders
        // these two as `60s` and `60m00s`.
        assert_eq!(fmt_duration(59.6), "1m00s");
        assert_eq!(fmt_duration(3599.6), "1h00m");
    }

    #[test]
    fn a_live_line_carries_its_start_and_how_long_so_far() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        let now = Utc::now();
        m.started_at = now - Duration::seconds(191);
        write(&dir, &m);
        let st = derive(dir.path(), now);
        let line = render(dir.path(), &st, now);
        assert!(line.contains("started "), "line: {line}");
        assert!(line.contains("(+3m11s), "), "line: {line}");
        assert!(!line.contains("ran "), "a live child has not `ran`: {line}");
    }

    #[test]
    fn a_terminal_line_says_how_long_it_ran() {
        let dir = TempDir::new().unwrap();
        let mut m = dead();
        let started = Utc::now() - Duration::seconds(4020);
        m.started_at = started;
        m.reaped = Some(Reaped {
            at: started + Duration::seconds(242),
            status: 1,
        });
        m.drained_at = Some(started + Duration::seconds(242));
        write(&dir, &m);
        let now = Utc::now();
        let st = derive(dir.path(), now);
        let line = render(dir.path(), &st, now);
        assert!(line.contains("ran 4m02s, "), "line: {line}");
        assert!(
            !line.contains("(+"),
            "a terminal child has no running total: {line}"
        );
    }

    /// The start time must be the local rendering of the stored instant, not the
    /// UTC one wearing local clothes.
    #[test]
    fn a_rendered_start_is_local_time() {
        let dir = TempDir::new().unwrap();
        let mut m = base();
        let started = Utc::now() - Duration::seconds(30);
        m.started_at = started;
        write(&dir, &m);
        let now = Utc::now();
        let st = derive(dir.path(), now);
        let line = render(dir.path(), &st, now);
        let expected = started
            .with_timezone(&chrono::Local)
            .format("%H:%M:%S")
            .to_string();
        assert!(
            line.contains(&format!("started {expected}")),
            "line {line} did not carry the local start {expected}"
        );
    }

    #[test]
    fn an_abandoned_line_still_says_when_it_started() {
        let dir = TempDir::new().unwrap();
        let mut m = dead();
        let started = Utc::now() - Duration::seconds(4020);
        m.started_at = started;
        m.reaped = None;
        m.drained_at = None;
        write(&dir, &m);
        let now = Utc::now();
        let st = derive(dir.path(), now);
        assert_eq!(st.key, StatusKey::Abandoned);
        let line = render(dir.path(), &st, now);
        let expected = started
            .with_timezone(&chrono::Local)
            .format("%H:%M:%S")
            .to_string();
        assert!(
            line.contains(&format!("started {expected}")),
            "line: {line}"
        );
        assert!(!line.contains("ran "), "nothing observed an end: {line}");
        assert!(
            !line.contains("(+"),
            "a settled child is not accumulating: {line}"
        );
    }

    /// A header stamp is re-read after a compaction, so it carries the offset
    /// that an in-line time leaves out.
    #[test]
    fn a_header_stamp_carries_the_offset_an_in_line_time_omits() {
        let t = Utc::now();
        let stamp = fmt_local_stamp(t);
        let hms = fmt_local_hms(t);
        let offset = stamp
            .strip_prefix(&format!("{hms} "))
            .unwrap_or_else(|| panic!("stamp {stamp} does not extend the in-line time {hms}"));
        assert!(
            offset.len() == 5
                && (offset.starts_with('+') || offset.starts_with('-'))
                && offset[1..].chars().all(|c| c.is_ascii_digit()),
            "stamp {stamp} carried {offset} where a signed four-digit offset belongs"
        );
    }
}
