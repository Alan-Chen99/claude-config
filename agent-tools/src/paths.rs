use anyhow::{bail, Context, Result};
use std::env;
use std::path::{Path, PathBuf};

use crate::psrecord;

/// Root of all agent-tools state: ~/.claude/agent-tools
pub fn state_root() -> Result<PathBuf> {
    let home = env::var("HOME").context("HOME not set")?;
    Ok(PathBuf::from(home).join(".claude/agent-tools"))
}

/// Compute the parent dir for `agent-tools run` captures within this tool
/// call. `agent_id == None` means main-thread.
pub fn parent_dir_for(session_id: &str, agent_id: Option<&str>, task_id: &str) -> Result<PathBuf> {
    let mut p = state_root()?.join(session_id);
    if let Some(a) = agent_id {
        p.push(a);
    }
    p.push(task_id);
    Ok(p)
}

/// Read AGENT_TOOLS_PARENT_DIR env var as an absolute path.
pub fn parent_dir_from_env() -> Result<PathBuf> {
    let v = env::var("AGENT_TOOLS_PARENT_DIR").context("AGENT_TOOLS_PARENT_DIR is not set")?;
    let p = PathBuf::from(&v);
    if !p.is_absolute() {
        bail!("AGENT_TOOLS_PARENT_DIR must be an absolute path, got: {v}");
    }
    Ok(p)
}

/// The two environment inputs that decide where a `run` publishes, reduced
/// to the decision alone: no environment read happens in here, on purpose.
/// `cargo test` runs every test in this binary on parallel threads, and
/// `std::env::set_var`/`remove_var` are process-global — a test that mutated
/// `AGENT_TOOLS_PARENT_DIR` or `CLAUDE_CODE_SESSION_ID` to drive this
/// decision would race every other thread reading them, this file's own
/// `HOME`-setting tests included. Taking both as arguments removes the
/// mutation instead of merely scheduling around it.
///
/// A hook-set `AGENT_TOOLS_PARENT_DIR` wins whenever it parses as an
/// absolute path, origin `"tool"`. A present value that fails to parse is
/// never treated as absent: a hook ran and set something the wrapper cannot
/// use, and that needs a reader looking at what the hook set, not a
/// fallback that quietly publishes elsewhere while reporting success.
///
/// Only a truly absent `AGENT_TOOLS_PARENT_DIR` falls back to
/// `CLAUDE_CODE_SESSION_ID`, landing on `<state_root>/<session>/user-shell`
/// (`psrecord::USER_SHELL`), same origin. Nothing here can tell a bare `!`
/// command apart from a subagent whose PreToolUse hook misfired: both run in
/// a shell exporting the same session id, and the one variable that would
/// separate them — a hook-set `AGENT_TOOLS_PARENT_DIR`, which for a subagent
/// also carries its agent id — is exactly the variable missing in both
/// cases. `user-shell` names only the fact this function actually knows,
/// that no hook set a scope, rather than guessing which of the two caused
/// it. The misattributed case still surfaces rather than vanishing: a
/// subagent's orphaned child is picked up by the main thread's own scan
/// instead of sitting unwatched under a scope nobody polls — a mistaken
/// owner beats no owner at all.
///
/// Neither variable set fails, naming both routes: no hook ran to set the
/// first, and the second — which every Claude Code shell carries whether or
/// not a hook ran — is absent too.
fn scope_from(
    parent_dir: Option<&str>,
    session_id: Option<&str>,
    state_root: &Path,
) -> Result<(PathBuf, &'static str)> {
    if let Some(v) = parent_dir {
        let p = PathBuf::from(v);
        if !p.is_absolute() {
            bail!(
                "AGENT_TOOLS_PARENT_DIR must be an absolute path, got: {v}\n\
                 A hook (agent-tools hook-pre) set this value, so the value itself \
                 needs fixing rather than the hook's installation."
            );
        }
        return Ok((p, "tool"));
    }
    match session_id {
        Some(sid) => Ok((
            state_root.join(sid).join(psrecord::USER_SHELL),
            psrecord::USER_SHELL,
        )),
        None => bail!(
            "neither AGENT_TOOLS_PARENT_DIR nor CLAUDE_CODE_SESSION_ID is set.\n\
             The PreToolUse hook (agent-tools hook-pre) sets the first; Claude Code \
             exports the second into every shell it runs, hook or no hook.\n\
             If you see this from inside a Claude Code Bash tool, the hook is not \
             installed."
        ),
    }
}

/// `scope_from`'s environment-reading shell: looks up the two variables and
/// `state_root()`'s `HOME`, then delegates the actual decision. Kept to
/// exactly that, so the decision stays reachable without touching the
/// environment — see `scope_from`.
pub fn scope_for_run() -> Result<(PathBuf, &'static str)> {
    let root = state_root()?;
    scope_from(
        env::var("AGENT_TOOLS_PARENT_DIR").ok().as_deref(),
        env::var("CLAUDE_CODE_SESSION_ID").ok().as_deref(),
        &root,
    )
}

/// Recover (session_id, Option<agent_id>, task_id) from a parent_dir path
/// rooted at state_root().
pub fn parse_parent_dir(task_dir: &Path) -> Result<(String, Option<String>, String)> {
    let root = state_root()?;
    let rel = task_dir.strip_prefix(&root).with_context(|| {
        format!(
            "task_dir {} is not under state root {}",
            task_dir.display(),
            root.display()
        )
    })?;
    let parts: Vec<_> = rel
        .components()
        .map(|c| c.as_os_str().to_string_lossy().to_string())
        .collect();
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
        let p = parent_dir_for("sid", None, "tid").unwrap();
        assert_eq!(p, PathBuf::from("/h/.claude/agent-tools/sid/tid"));
    }

    #[test]
    fn builds_subagent_path() {
        std::env::set_var("HOME", "/h");
        let p = parent_dir_for("sid", Some("aid"), "tid").unwrap();
        assert_eq!(p, PathBuf::from("/h/.claude/agent-tools/sid/aid/tid"));
    }

    #[test]
    fn parses_main_thread() {
        std::env::set_var("HOME", "/h");
        let (s, a, t) = parse_parent_dir(Path::new("/h/.claude/agent-tools/sid/tid")).unwrap();
        assert_eq!(s, "sid");
        assert_eq!(a, None);
        assert_eq!(t, "tid");
    }

    #[test]
    fn parses_subagent() {
        std::env::set_var("HOME", "/h");
        let (s, a, t) = parse_parent_dir(Path::new("/h/.claude/agent-tools/sid/aid/tid")).unwrap();
        assert_eq!(s, "sid");
        assert_eq!(a.as_deref(), Some("aid"));
        assert_eq!(t, "tid");
    }

    #[test]
    fn rejects_non_state_dir() {
        std::env::set_var("HOME", "/h");
        assert!(parse_parent_dir(Path::new("/somewhere/else")).is_err());
    }

    // `scope_from` is pure, so every case below passes its inputs as
    // arguments rather than mutating `AGENT_TOOLS_PARENT_DIR` or
    // `CLAUDE_CODE_SESSION_ID` — the two are read by every thread this
    // binary's test run puts on the same process, and setting either would
    // race the others rather than merely risk a slow test.

    #[test]
    fn a_hook_set_scope_wins_even_with_a_session_id_present() {
        let root = PathBuf::from("/h/.claude/agent-tools");
        let (dir, origin) = scope_from(
            Some("/h/.claude/agent-tools/sid/tid"),
            Some("other-sid"),
            &root,
        )
        .unwrap();
        assert_eq!(dir, PathBuf::from("/h/.claude/agent-tools/sid/tid"));
        assert_eq!(origin, "tool");
    }

    #[test]
    fn with_no_hook_the_session_id_gives_a_user_shell_scope() {
        let root = PathBuf::from("/h/.claude/agent-tools");
        let (dir, origin) = scope_from(None, Some("sid-9"), &root).unwrap();
        assert_eq!(
            dir,
            PathBuf::from("/h/.claude/agent-tools/sid-9/user-shell")
        );
        assert_eq!(origin, psrecord::USER_SHELL);
    }

    #[test]
    fn with_neither_set_the_error_names_both_routes() {
        let root = PathBuf::from("/h/.claude/agent-tools");
        let e = scope_from(None, None, &root).unwrap_err().to_string();
        assert!(e.contains("AGENT_TOOLS_PARENT_DIR"), "{e}");
        assert!(e.contains("CLAUDE_CODE_SESSION_ID"), "{e}");
    }

    /// A rejected `AGENT_TOOLS_PARENT_DIR` must never fall back to
    /// `user-shell`: a hook that ran and set something unusable needs a
    /// reader looking at that hook, and silently publishing to the
    /// session's shell scope while reporting success would hide exactly the
    /// breakage this case exists to catch.
    #[test]
    fn a_relative_hook_set_scope_is_rejected_not_demoted_to_user_shell() {
        let root = PathBuf::from("/h/.claude/agent-tools");
        let e = scope_from(Some("relative/path"), Some("sid-9"), &root)
            .unwrap_err()
            .to_string();
        assert!(e.contains("absolute"), "{e}");
        assert!(e.contains("relative/path"), "{e}");
        assert!(
            !e.contains("is not set"),
            "the variable is set; blaming absence misdirects the reader: {e}"
        );
    }

    /// The same rejection holds with no session id to fall back to either —
    /// a malformed hook-set value is never absent, so it never reaches the
    /// fallback branch at all.
    #[test]
    fn a_relative_hook_set_scope_is_rejected_even_with_no_session_id() {
        let root = PathBuf::from("/h/.claude/agent-tools");
        let e = scope_from(Some("relative/path"), None, &root)
            .unwrap_err()
            .to_string();
        assert!(e.contains("absolute"), "{e}");
        assert!(e.contains("relative/path"), "{e}");
    }
}
