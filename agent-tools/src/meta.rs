use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

/// Reap facts, written as one unit so time and status can never disagree.
#[derive(Debug, Serialize, Deserialize, Clone, Copy)]
pub struct Reaped {
    pub at: DateTime<Utc>,
    pub status: i32,
}

/// Durable facts about one `agent-tools run` invocation. Never a status:
/// status is derived at read time (see `status.rs`).
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChildMeta {
    pub wrapper_pid: u32,
    pub wrapper_started_ticks: u64,
    /// None when the command could not be exec'd.
    pub child_pid: Option<u32>,
    pub desc: Option<String>,
    pub command: Vec<String>,
    pub started_at: DateTime<Utc>,
    pub spawn_error: Option<String>,
    pub reaped: Option<Reaped>,
    pub drained_at: Option<DateTime<Utc>>,
}

impl ChildMeta {
    /// Name for reports and `ps`: the `--desc` string, else the command.
    /// A report must never render an empty name.
    ///
    /// Control characters are escaped: both consumers are line-oriented, so a
    /// newline here splits one child across two lines and the second reads as a
    /// status line for a child that does not exist.
    pub fn display_name(&self) -> String {
        let raw = match &self.desc {
            Some(d) if !d.trim().is_empty() => d.clone(),
            _ => self.command.join(" "),
        };
        escape_control(&raw)
    }
}

/// Escape control characters so a value cannot break a line-oriented display or
/// emit terminal escape sequences of its own.
pub fn escape_control(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c.is_control() => out.push_str(&format!("\\x{:02x}", c as u32)),
            c => out.push(c),
        }
    }
    out
}

/// Write meta atomically: write to <path>.tmp then rename.
pub fn write_meta(dir: &Path, meta: &ChildMeta) -> Result<()> {
    fs::create_dir_all(dir).with_context(|| format!("mkdir {}", dir.display()))?;
    let final_path = dir.join("meta.json");
    let tmp_path = dir.join("meta.json.tmp");
    let json = serde_json::to_vec_pretty(meta)?;
    fs::write(&tmp_path, &json).with_context(|| format!("write {}", tmp_path.display()))?;
    fs::rename(&tmp_path, &final_path)
        .with_context(|| format!("rename {} -> {}", tmp_path.display(), final_path.display()))?;
    Ok(())
}

pub fn read_meta(dir: &Path) -> Result<ChildMeta> {
    let bytes = fs::read(dir.join("meta.json"))
        .with_context(|| format!("read {}/meta.json", dir.display()))?;
    Ok(serde_json::from_slice(&bytes)?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn sample() -> ChildMeta {
        ChildMeta {
            wrapper_pid: 42,
            wrapper_started_ticks: 987654,
            child_pid: Some(43),
            desc: Some("probe".into()),
            command: vec!["echo".into(), "hi".into()],
            started_at: chrono::Utc::now(),
            spawn_error: None,
            reaped: None,
            drained_at: None,
        }
    }

    #[test]
    fn roundtrip_preserves_facts() {
        let dir = TempDir::new().unwrap();
        write_meta(dir.path(), &sample()).unwrap();
        let back = read_meta(dir.path()).unwrap();
        assert_eq!(back.wrapper_pid, 42);
        assert_eq!(back.wrapper_started_ticks, 987654);
        assert_eq!(back.child_pid, Some(43));
        assert!(back.reaped.is_none());
    }

    #[test]
    fn reap_carries_time_and_status_together() {
        let dir = TempDir::new().unwrap();
        let mut m = sample();
        m.reaped = Some(Reaped { at: chrono::Utc::now(), status: 3 });
        write_meta(dir.path(), &m).unwrap();
        assert_eq!(read_meta(dir.path()).unwrap().reaped.unwrap().status, 3);
    }

    #[test]
    fn spawn_failure_needs_no_child_pid() {
        let dir = TempDir::new().unwrap();
        let mut m = sample();
        m.child_pid = None;
        m.spawn_error = Some("No such file or directory".into());
        write_meta(dir.path(), &m).unwrap();
        assert_eq!(read_meta(dir.path()).unwrap().child_pid, None);
    }

    #[test]
    fn atomic_write_leaves_no_tmp() {
        let dir = TempDir::new().unwrap();
        write_meta(dir.path(), &sample()).unwrap();
        assert!(dir.path().join("meta.json").exists());
        assert!(!dir.path().join("meta.json.tmp").exists());
    }

    #[test]
    fn display_name_escapes_control_characters() {
        // Both consumers are line-oriented. A newline here splits one child
        // across two lines, and the second reads as a status line for a child
        // that does not exist.
        let m = ChildMeta {
            desc: Some("evil\n  injected [final(0)] pid 1".into()),
            ..sample()
        };
        let name = m.display_name();
        assert!(!name.contains('\n'), "name: {name}");
        assert!(
            name.contains("evil\\n  injected"),
            "the newline is shown, not obeyed: {name}"
        );
    }
}
