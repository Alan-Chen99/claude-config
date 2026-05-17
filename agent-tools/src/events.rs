use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs::OpenOptions;
use std::io::Write;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct Event {
    pub ts: DateTime<Utc>,
    pub kind: String,
    pub data: serde_json::Value,
}

/// Append a single event line to <dir>/events.jsonl. Opens with O_APPEND so it
/// is safe against concurrent writers on the same file.
pub fn append(dir: &Path, kind: &str, data: serde_json::Value) -> Result<()> {
    let path = dir.join("events.jsonl");
    let evt = Event {
        ts: Utc::now(),
        kind: kind.into(),
        data,
    };
    let mut line = serde_json::to_vec(&evt)?;
    line.push(b'\n');
    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .with_context(|| format!("open append {}", path.display()))?;
    f.write_all(&line)
        .with_context(|| format!("write {}", path.display()))?;
    Ok(())
}

/// Read all events from <dir>/events.jsonl in chronological order.
pub fn read_all(dir: &Path) -> Result<Vec<Event>> {
    let path = dir.join("events.jsonl");
    if !path.exists() {
        return Ok(vec![]);
    }
    let bytes = std::fs::read_to_string(&path)?;
    let mut out = Vec::new();
    for line in bytes.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line)?);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn append_creates_file_and_writes_one_line() {
        let dir = TempDir::new().unwrap();
        append(dir.path(), "task_started", serde_json::json!({"pid": 1})).unwrap();
        let evts = read_all(dir.path()).unwrap();
        assert_eq!(evts.len(), 1);
        assert_eq!(evts[0].kind, "task_started");
        assert_eq!(evts[0].data["pid"], 1);
    }

    #[test]
    fn append_preserves_order() {
        let dir = TempDir::new().unwrap();
        append(dir.path(), "a", serde_json::json!({})).unwrap();
        append(dir.path(), "b", serde_json::json!({})).unwrap();
        append(dir.path(), "c", serde_json::json!({})).unwrap();
        let evts = read_all(dir.path()).unwrap();
        let kinds: Vec<&str> = evts.iter().map(|e| e.kind.as_str()).collect();
        assert_eq!(kinds, vec!["a", "b", "c"]);
    }

    #[test]
    fn read_missing_file_returns_empty() {
        let dir = TempDir::new().unwrap();
        let evts = read_all(dir.path()).unwrap();
        assert_eq!(evts.len(), 0);
    }
}
