use anyhow::{bail, Context, Result};
use std::env;
use std::path::{Path, PathBuf};

/// Root of all agent-tools state: ~/.claude/agent-tools
pub fn state_root() -> Result<PathBuf> {
    let home = env::var("HOME").context("HOME not set")?;
    Ok(PathBuf::from(home).join(".claude/agent-tools"))
}

/// Compute task_dir from identifiers. `agent_id == None` means main-thread.
pub fn task_dir_for(session_id: &str, agent_id: Option<&str>, task_id: &str) -> Result<PathBuf> {
    let mut p = state_root()?.join(session_id);
    if let Some(a) = agent_id {
        p.push(a);
    }
    p.push(task_id);
    Ok(p)
}

/// Read AGENT_TOOLS_TASK_ID env var as an absolute path.
pub fn task_dir_from_env() -> Result<PathBuf> {
    let v = env::var("AGENT_TOOLS_TASK_ID")
        .context("AGENT_TOOLS_TASK_ID is not set")?;
    let p = PathBuf::from(&v);
    if !p.is_absolute() {
        bail!("AGENT_TOOLS_TASK_ID must be an absolute path, got: {v}");
    }
    Ok(p)
}

/// Recover (session_id, Option<agent_id>, task_id) from a task_dir path
/// rooted at state_root().
pub fn parse_task_dir(task_dir: &Path) -> Result<(String, Option<String>, String)> {
    let root = state_root()?;
    let rel = task_dir.strip_prefix(&root).with_context(|| {
        format!(
            "task_dir {} is not under state root {}",
            task_dir.display(),
            root.display()
        )
    })?;
    let parts: Vec<_> = rel.components().map(|c| c.as_os_str().to_string_lossy().to_string()).collect();
    match parts.as_slice() {
        [sid, tid] => Ok((sid.clone(), None, tid.clone())),
        [sid, aid, tid] => Ok((sid.clone(), Some(aid.clone()), tid.clone())),
        _ => bail!("task_dir must have 2 or 3 components under state root, got: {rel:?}"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builds_main_thread_path() {
        std::env::set_var("HOME", "/h");
        let p = task_dir_for("sid", None, "tid").unwrap();
        assert_eq!(p, PathBuf::from("/h/.claude/agent-tools/sid/tid"));
    }

    #[test]
    fn builds_subagent_path() {
        std::env::set_var("HOME", "/h");
        let p = task_dir_for("sid", Some("aid"), "tid").unwrap();
        assert_eq!(p, PathBuf::from("/h/.claude/agent-tools/sid/aid/tid"));
    }

    #[test]
    fn parses_main_thread() {
        std::env::set_var("HOME", "/h");
        let (s, a, t) = parse_task_dir(Path::new("/h/.claude/agent-tools/sid/tid")).unwrap();
        assert_eq!(s, "sid");
        assert_eq!(a, None);
        assert_eq!(t, "tid");
    }

    #[test]
    fn parses_subagent() {
        std::env::set_var("HOME", "/h");
        let (s, a, t) = parse_task_dir(Path::new("/h/.claude/agent-tools/sid/aid/tid")).unwrap();
        assert_eq!(s, "sid");
        assert_eq!(a.as_deref(), Some("aid"));
        assert_eq!(t, "tid");
    }

    #[test]
    fn rejects_non_state_dir() {
        std::env::set_var("HOME", "/h");
        assert!(parse_task_dir(Path::new("/somewhere/else")).is_err());
    }
}
