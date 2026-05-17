use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Meta {
    Task(TaskMeta),
    Child(ChildMeta),
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TaskMeta {
    pub session_id: String,
    pub agent_id: Option<String>,
    pub task_id: String,
    pub tool: String,
    pub tool_use_id: String,
    pub desc: Option<String>,
    pub cwd: String,
    pub pid: Option<u32>,
    pub started_at: Option<DateTime<Utc>>,
    pub ended_at: Option<DateTime<Utc>>,
    pub exit_code: Option<i32>,
    pub silence_threshold_ms: u64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChildMeta {
    pub parent_task_dir: String,
    pub child_id: u32,
    pub desc: Option<String>,
    pub command: Vec<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub ended_at: Option<DateTime<Utc>>,
    pub exit_code: Option<i32>,
}

/// Write meta atomically: write to <path>.tmp then rename.
pub fn write_meta(dir: &Path, meta: &Meta) -> Result<()> {
    fs::create_dir_all(dir).with_context(|| format!("mkdir {}", dir.display()))?;
    let final_path = dir.join("meta.json");
    let tmp_path = dir.join("meta.json.tmp");
    let json = serde_json::to_vec_pretty(meta)?;
    fs::write(&tmp_path, &json).with_context(|| format!("write {}", tmp_path.display()))?;
    fs::rename(&tmp_path, &final_path)
        .with_context(|| format!("rename {} -> {}", tmp_path.display(), final_path.display()))?;
    Ok(())
}

pub fn read_meta(dir: &Path) -> Result<Meta> {
    let bytes = fs::read(dir.join("meta.json"))
        .with_context(|| format!("read {}/meta.json", dir.display()))?;
    Ok(serde_json::from_slice(&bytes)?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn roundtrip_task_meta() {
        let dir = TempDir::new().unwrap();
        let m = Meta::Task(TaskMeta {
            session_id: "sid".into(),
            agent_id: None,
            task_id: "tid".into(),
            tool: "Bash".into(),
            tool_use_id: "tuid".into(),
            desc: Some("d".into()),
            cwd: "/tmp".into(),
            pid: None,
            started_at: None,
            ended_at: None,
            exit_code: None,
            silence_threshold_ms: 30_000,
        });
        write_meta(dir.path(), &m).unwrap();
        let back = read_meta(dir.path()).unwrap();
        match back {
            Meta::Task(t) => {
                assert_eq!(t.task_id, "tid");
                assert_eq!(t.silence_threshold_ms, 30_000);
            }
            _ => panic!("expected Task"),
        }
    }

    #[test]
    fn roundtrip_child_meta() {
        let dir = TempDir::new().unwrap();
        let m = Meta::Child(ChildMeta {
            parent_task_dir: "/x".into(),
            child_id: 42,
            desc: None,
            command: vec!["echo".into(), "hi".into()],
            started_at: None,
            ended_at: None,
            exit_code: None,
        });
        write_meta(dir.path(), &m).unwrap();
        let back = read_meta(dir.path()).unwrap();
        match back {
            Meta::Child(c) => {
                assert_eq!(c.child_id, 42);
                assert_eq!(c.command, vec!["echo".to_string(), "hi".into()]);
            }
            _ => panic!("expected Child"),
        }
    }

    #[test]
    fn atomic_write_leaves_no_tmp() {
        let dir = TempDir::new().unwrap();
        let m = Meta::Task(TaskMeta {
            session_id: "sid".into(),
            agent_id: None,
            task_id: "tid".into(),
            tool: "Bash".into(),
            tool_use_id: "tuid".into(),
            desc: None,
            cwd: "/tmp".into(),
            pid: None,
            started_at: None,
            ended_at: None,
            exit_code: None,
            silence_threshold_ms: 30_000,
        });
        write_meta(dir.path(), &m).unwrap();
        assert!(dir.path().join("meta.json").exists());
        assert!(!dir.path().join("meta.json.tmp").exists());
    }
}
