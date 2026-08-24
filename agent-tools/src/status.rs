use chrono::{DateTime, Utc};
use std::fmt;
use std::path::Path;

use crate::meta::{self, ChildMeta};
use crate::procstat;

/// Quiet thresholds, ascending. Configuration, not contract.
pub const QUIET_BUCKETS: &[(i64, &str)] = &[(30, "30s"), (300, "5m"), (1800, "30m"), (7200, "2h")];

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

pub struct Status {
    pub key: StatusKey,
    pub meta: Option<ChildMeta>,
    pub last_byte_at: Option<DateTime<Utc>>,
    pub out_bytes: u64,
    pub err_bytes: u64,
}

fn file_facts(dir: &Path, name: &str) -> (u64, Option<DateTime<Utc>>) {
    match std::fs::metadata(dir.join(name)) {
        Ok(md) => (md.len(), md.modified().ok().map(DateTime::<Utc>::from)),
        Err(_) => (0, None),
    }
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
    let (out_bytes, out_mtime) = file_facts(dir, "stdout");
    let (err_bytes, err_mtime) = file_facts(dir, "stderr");
    let last_byte_at = out_mtime.max(err_mtime);

    let Ok(m) = meta::read_meta(dir) else {
        // A capture that cannot be described is never silently dropped.
        return Status { key: StatusKey::Abandoned, meta: None, last_byte_at, out_bytes, err_bytes };
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

    Status { key, meta: Some(m), last_byte_at, out_bytes, err_bytes }
}

/// One rendered line: name, key, detail, capture paths.
pub fn render(dir: &Path, s: &Status, now: DateTime<Utc>) -> String {
    let name = s.meta.as_ref().map(|m| m.display_name()).unwrap_or_else(|| dir.display().to_string());
    let age = match s.last_byte_at {
        Some(t) => format!("last byte {}s ago", (now - t).num_seconds().max(0)),
        None => "no output".to_string(),
    };
    let pid = s
        .meta
        .as_ref()
        .and_then(|m| m.child_pid)
        .map(|p| p.to_string())
        .unwrap_or_else(|| "-".into());
    format!(
        "{name} [{}] pid {pid}, {age}, out={}B err={}B -> {}/{{stdout,stderr}}",
        s.key,
        s.out_bytes,
        s.err_bytes,
        dir.display()
    )
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
        // An anchor exactly on a boundary is quiet, never producing. The spec
        // called this out after review found the two definitions disagreed.
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
    fn key_strings_are_stable_ledger_identities() {
        assert_eq!(StatusKey::Producing.to_string(), "producing");
        assert_eq!(StatusKey::Quiet("5m").to_string(), "quiet(5m)");
        assert_eq!(StatusKey::Exited(2).to_string(), "exited(2)");
        assert_eq!(StatusKey::Final(0).to_string(), "final(0)");
        assert_eq!(StatusKey::Abandoned.to_string(), "abandoned");
    }
}
