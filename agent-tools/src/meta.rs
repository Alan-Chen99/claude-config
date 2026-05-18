use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChildMeta {
    pub child_id: u32,
    pub desc: Option<String>,
    pub command: Vec<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub ended_at: Option<DateTime<Utc>>,
    pub exit_code: Option<i32>,
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

    #[test]
    fn roundtrip_child_meta() {
        let dir = TempDir::new().unwrap();
        let m = ChildMeta {
            child_id: 42,
            desc: Some("probe".into()),
            command: vec!["echo".into(), "hi".into()],
            started_at: None,
            ended_at: None,
            exit_code: None,
        };
        write_meta(dir.path(), &m).unwrap();
        let back = read_meta(dir.path()).unwrap();
        assert_eq!(back.child_id, 42);
        assert_eq!(back.desc.as_deref(), Some("probe"));
        assert_eq!(back.command, vec!["echo".to_string(), "hi".into()]);
    }

    #[test]
    fn atomic_write_leaves_no_tmp() {
        let dir = TempDir::new().unwrap();
        let m = ChildMeta {
            child_id: 7,
            desc: None,
            command: vec!["true".into()],
            started_at: None,
            ended_at: None,
            exit_code: None,
        };
        write_meta(dir.path(), &m).unwrap();
        assert!(dir.path().join("meta.json").exists());
        assert!(!dir.path().join("meta.json.tmp").exists());
    }
}
