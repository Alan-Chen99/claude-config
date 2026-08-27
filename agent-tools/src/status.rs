use chrono::{DateTime, Utc};
use std::fmt;
use std::path::Path;

use crate::core;
use crate::meta::{self, ChildMeta};
use crate::procstat;

/// Longest name a report line carries. `--desc` and the command are the only
/// unbounded fields in a line, and `hook_post::bound` can never select a line
/// larger than the whole report budget: that child's change would be announced
/// as omitted at every delivery point and never actually delivered.
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

/// Returns (bytes, mtime, stat failure other than "not created yet").
///
/// A missing capture file is ordinary: the parent directory exists before the
/// tee opens either stream. Any other stat failure is a real filesystem problem,
/// and reading it as "no output" would understate a child that is in fact busy.
fn file_facts(dir: &Path, name: &str) -> (u64, Option<DateTime<Utc>>, Option<String>) {
    match std::fs::metadata(dir.join(name)) {
        Ok(md) => (md.len(), md.modified().ok().map(DateTime::<Utc>::from), None),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (0, None, None),
        Err(e) => (0, None, Some(format!("{name}: {e}"))),
    }
}

/// Truncate on a char boundary, marking that it happened.
fn cap(name: &str) -> String {
    if name.chars().count() <= NAME_MAX {
        return name.to_string();
    }
    name.chars().take(NAME_MAX).chain(['\u{2026}']).collect()
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
        None => Capture::Split { out: out_bytes, err: err_bytes },
    };
    let last_byte_at = out_mtime.max(err_mtime).max(merged_mtime);
    let stat_errors: Vec<String> =
        [out_err, err_err, merged_err].into_iter().flatten().collect();

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

    Status { key, meta: Some(m), last_byte_at, capture, stat_errors }
}

/// One rendered line: name, key, detail, capture paths.
pub fn render(dir: &Path, s: &Status, now: DateTime<Utc>) -> String {
    let name = s.meta.as_ref().map(|m| m.display_name()).unwrap_or_else(|| dir.display().to_string());
    let name = cap(&name);
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
            notes.push(format!("streams split: {why}"));
        }
    }
    if s.meta.as_ref().is_some_and(|m| m.forward_closed) {
        notes.push("downstream closed".to_string());
    }
    if s.meta.as_ref().is_some_and(|m| m.drain_capped) {
        notes.push("drain capped".to_string());
    }
    if let Some(e) = s.meta.as_ref().and_then(|m| m.capture_error.as_deref()) {
        notes.push(format!("capture failed: {e}"));
    }
    let notes = if notes.is_empty() {
        String::new()
    } else {
        format!(" [{}]", notes.join("; "))
    };
    let (bytes, paths) = s.capture.detail(dir);
    format!("{name} [{}] pid {pid}, {age}, {bytes}{notes}{problems} -> {paths}", s.key)
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
        ChildMeta { wrapper_pid: 0, wrapper_started_ticks: 1, ..base() }
    }

    fn write(dir: &TempDir, m: &ChildMeta) {
        crate::meta::write_meta(dir.path(), m).unwrap();
    }

    #[test]
    fn spawn_failure_wins_over_everything() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.spawn_error = Some("boom".into());
        m.reaped = Some(Reaped { at: Utc::now(), status: 0 });
        write(&d, &m);
        assert!(matches!(derive(d.path(), Utc::now()).key, StatusKey::SpawnFailed(_)));
    }

    #[test]
    fn drained_is_final() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.reaped = Some(Reaped { at: Utc::now(), status: 3 });
        m.drained_at = Some(Utc::now());
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Final(3));
    }

    #[test]
    fn reaped_with_live_wrapper_is_exited() {
        let d = TempDir::new().unwrap();
        let mut m = base();
        m.reaped = Some(Reaped { at: Utc::now(), status: 0 });
        write(&d, &m);
        assert_eq!(derive(d.path(), Utc::now()).key, StatusKey::Exited(0));
    }

    #[test]
    fn reaped_with_dead_wrapper_is_final() {
        let d = TempDir::new().unwrap();
        let mut m = dead();
        m.reaped = Some(Reaped { at: Utc::now(), status: 5 });
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
        m.merge = Some(core::DESTINATIONS_ALREADY_DIFFERED.into());
        m.forward_closed = true;
        // The bound applies only once forwarding has failed, so the two facts
        // are true together or the record describes a run that cannot happen.
        m.drain_capped = true;
        m.capture_error = Some("No space left on device".into());
        write(&d, &m);
        std::fs::write(d.path().join("stdout"), b"x").unwrap();

        let now = Utc::now();
        let line = render(d.path(), &derive(d.path(), now), now);
        assert!(line.contains("downstream closed"), "line: {line}");
        assert!(line.contains("drain capped"), "line: {line}");
        assert!(
            line.contains("capture failed: No space left on device"),
            "line: {line}"
        );
        // The one split that is not a difference from bare: two destinations
        // stayed two, so there is nothing to explain. This is also the shape of
        // every harness that spawns with two pipes, which is why a note here
        // would be on every test line and no production one.
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
            !line.contains("merge"),
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
        assert!(!s.stat_errors.is_empty(), "a non-NotFound stat error must survive");
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

    #[test]
    fn render_caps_the_name_so_a_line_can_always_fit_a_report() {
        // The name is the only unbounded field in a line. A line longer than the
        // whole report budget can never be selected, so its change would be
        // announced as omitted at every delivery point and never delivered.
        let dir = TempDir::new().unwrap();
        let m = ChildMeta { desc: Some("x".repeat(20_000)), ..base() };
        write(&dir, &m);
        let now = Utc::now();
        let line = render(dir.path(), &derive(dir.path(), now), now);
        assert!(line.len() < 1_000, "line is {} bytes: {line}", line.len());
        assert!(line.contains('\u{2026}'), "truncation must be visible: {line}");
        assert!(line.contains("{stdout,stderr}"), "the capture path survives: {line}");
    }
}
