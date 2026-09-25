//! Launch Claude Code against this checkout's config without installing it.
//!
//! Four things decide whether a session actually exercises this checkout: the
//! `agent-tools` binary its hooks invoke, the `settings.json` that registers
//! those hooks, the system prompt that teaches the agent to read what they
//! emit, and the output style that carries `pre_output.record`. Wire three of
//! the four and the session looks healthy while testing the installed
//! checkout's behaviour, so each is wired here from one place.
//!
//! Isolation runs through `CLAUDE_CONFIG_DIR`, which relocates every config
//! read Claude Code performs. Layering this checkout's settings on top of the
//! installed ones instead would double-register every hook: settings sources
//! are unioned rather than overridden, so `hook-pre` and `hook-post` would each
//! run twice per tool call.

use anyhow::{bail, Context, Result};
use std::fs;
use std::os::unix::fs::{symlink, PermissionsExt};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

/// What `install.sh` symlinks into `~/.claude`, sourced from this checkout, so
/// the session is what installing this checkout would give.
const FROM_CHECKOUT: [&str; 5] = [
    "agents",
    "conventions",
    "output-styles",
    "skills",
    "statusline.sh",
];

/// Machine state rather than checkout state. Shared with the real config so the
/// session keeps its credentials, its environment `CLAUDE.md`, and the plugins
/// already installed.
const FROM_REAL_CONFIG: [&str; 3] = ["CLAUDE.md", ".credentials.json", "plugins"];

pub fn run(root: &Path, known_subcommands: &[String], args: Vec<String>) -> Result<()> {
    refuse_installed_checkout(root)?;

    let cfg = root.join(".claude/worktree-config");
    assemble(root, &cfg)?;

    // A UserPromptSubmit hook that exits non-zero blocks the turn outright, so
    // a settings file naming a subcommand this build does not have produces a
    // session that starts clean and then refuses every prompt. Fail here
    // instead, while the operator is still looking at a terminal.
    assert_wired_subcommands(&cfg.join("settings.json"), known_subcommands)?;

    // The binary is wired to this checkout by `relink` below; the Python half
    // is wired by the venv's editable install, and those are set independently.
    // A venv whose editable path was seeded from another checkout keeps serving
    // that checkout's `claude_config` -- so the hooks, `agent-tools
    // pre_output.record` and `count-tokens` run code this checkout does not
    // contain, with no error anywhere and a session that looks healthy. `uv run`
    // does not repair it: the install is current by name and version.
    assert_python_half(root)?;

    // The strings the hooks emit and the strings the prompt teaches the agent
    // to recognize are coupled by nothing but this check. Drift breaks
    // recognition without breaking a test, which is exactly the defect a test
    // session is least able to reveal.
    let coupling = root.join("scripts/check-prompt-coupling.sh");
    if coupling.is_file() {
        let status = Command::new(&coupling)
            .status()
            .with_context(|| format!("running {}", coupling.display()))?;
        if !status.success() {
            bail!("{} failed", coupling.display());
        }
    }

    let exe = std::env::current_exe().context("resolving current executable")?;
    let bin_dir = cfg.join("bin");
    fs::create_dir_all(&bin_dir)
        .with_context(|| format!("creating {}", bin_dir.display()))?;
    relink(&exe, &bin_dir.join("agent-tools"))?;

    // Hook commands, the output style's `pre_output.record`, and the agent's
    // own `agent-tools run` calls all name the binary bare and resolve it
    // through PATH, so one directory in front redirects every caller at once.
    let path = match std::env::var_os("PATH") {
        Some(p) => format!("{}:{}", bin_dir.display(), p.to_string_lossy()),
        None => bin_dir.display().to_string(),
    };

    // `claude.sh` resolves its own real path to pick the system prompt, so
    // invoking this checkout's copy by path loads this checkout's prompt.
    let launcher = root.join("scripts/claude.sh");
    if !launcher.is_file() {
        bail!("{} does not exist", launcher.display());
    }
    let err = Command::new(&launcher)
        .args(&args)
        .env("PATH", path)
        .env("CLAUDE_CONFIG_ROOT", root)
        .env("CLAUDE_CONFIG_DIR", &cfg)
        .exec();
    bail!("exec {} failed: {err}", launcher.display());
}

/// Fail when the venv's `claude_config` resolves outside `root/src`.
fn assert_python_half(root: &Path) -> Result<()> {
    let venv = crate::venv_path(root);
    let python = venv.join("bin/python");
    if !python.is_file() {
        // No venv yet; `uv run` builds one from this project on first use.
        return Ok(());
    }
    let out = Command::new(&python)
        .args([
            "-c",
            "import claude_config,pathlib;print(pathlib.Path(claude_config.__file__).resolve().parent.parent)",
        ])
        .output()
        .with_context(|| format!("running {}", python.display()))?;
    if !out.status.success() {
        bail!(
            "{} cannot import claude_config; run `UV_PROJECT_ENVIRONMENT={} uv sync --project {}`",
            python.display(),
            venv.display(),
            root.display()
        );
    }
    let served = PathBuf::from(String::from_utf8_lossy(&out.stdout).trim().to_string());
    let expected = root.join("src");
    if !crate::same_dir(&served, &expected) {
        bail!(
            "{} serves claude_config from another checkout\n  serving: {}\n  expected: {}\nRepair it with: UV_PROJECT_ENVIRONMENT={} uv sync --project {} --reinstall-package claude-config",
            venv.display(),
            served.display(),
            expected.display(),
            venv.display(),
            root.display()
        );
    }
    Ok(())
}

/// Launching the installed checkout's own config is what `claude.sh` already
/// does, so answering that request here would produce a session indistinguishable
/// from a normal one — the silent wrong-checkout result this subcommand exists to
/// make impossible. `repo_root` cannot catch it: a binary whose compiled root is
/// the installed root satisfies every assertion it makes.
fn refuse_installed_checkout(root: &Path) -> Result<()> {
    let default_root = match crate::installed_default_root() {
        Ok(r) => r,
        // No installed config to be confused with.
        Err(_) => return Ok(()),
    };
    if crate::same_dir(&default_root, root) {
        bail!(
            "{} is the installed config; `agent-tools claude` launches a checkout that is not \
             installed. Use claude.sh for this one.",
            root.display()
        );
    }
    Ok(())
}

fn assemble(root: &Path, cfg: &Path) -> Result<()> {
    fs::create_dir_all(cfg).with_context(|| format!("creating {}", cfg.display()))?;
    // The directory holds a link to the real credentials file.
    fs::set_permissions(cfg, fs::Permissions::from_mode(0o700))
        .with_context(|| format!("restricting {}", cfg.display()))?;

    for name in FROM_CHECKOUT {
        let src = root.join(name);
        if src.exists() {
            relink(&src, &cfg.join(name))?;
        }
    }

    // Copied rather than linked: Claude Code rewrites `settings.json` in place
    // when the model or theme changes mid-session, and a link would land those
    // writes on the checkout's tracked file. Recopied on every launch so an
    // edit to the checkout's settings is never tested one revision behind.
    let settings = root.join("settings.json");
    fs::copy(&settings, cfg.join("settings.json"))
        .with_context(|| format!("copying {}", settings.display()))?;

    let real = real_config_dir()?;
    for name in FROM_REAL_CONFIG {
        let src = real.join(name);
        if src.exists() {
            relink(&src, &cfg.join(name))?;
        }
    }

    // Onboarding state, trusted-directory records, and caches. Seeded once and
    // then left alone: Claude Code rewrites this file continuously, and
    // recopying would discard whatever the session accumulated.
    let seeded = cfg.join(".claude.json");
    if !seeded.exists() {
        let src = real
            .parent()
            .unwrap_or(Path::new("/"))
            .join(".claude.json");
        if src.is_file() {
            fs::copy(&src, &seeded)
                .with_context(|| format!("seeding {}", seeded.display()))?;
        }
    }
    Ok(())
}

/// `$HOME/.claude` specifically, never `CLAUDE_CONFIG_DIR`: the entries taken
/// from here are the machine's, and a nested launch must not source them from
/// another session's private config directory.
fn real_config_dir() -> Result<PathBuf> {
    let home = std::env::var_os("HOME").context("HOME not set")?;
    Ok(PathBuf::from(home).join(".claude"))
}

fn relink(src: &Path, dst: &Path) -> Result<()> {
    match fs::remove_file(dst) {
        Ok(()) => {}
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
        Err(e) => return Err(e).with_context(|| format!("replacing {}", dst.display())),
    }
    symlink(src, dst)
        .with_context(|| format!("linking {} -> {}", dst.display(), src.display()))
}

/// Every `agent-tools <sub>` a settings file wires must exist in this build.
fn assert_wired_subcommands(settings: &Path, known: &[String]) -> Result<()> {
    let raw = fs::read_to_string(settings)
        .with_context(|| format!("reading {}", settings.display()))?;
    let parsed: serde_json::Value = serde_json::from_str(&raw)
        .with_context(|| format!("parsing {}", settings.display()))?;

    for sub in wired_subcommands(&parsed) {
        if !known.iter().any(|k| *k == sub) {
            bail!(
                "{} wires `agent-tools {sub}`, which this build does not have",
                settings.display()
            );
        }
    }
    Ok(())
}

/// Collect the subcommand named by every hook command of the form
/// `agent-tools <sub> ...`, at any depth, so a new hook event never escapes the
/// check by sitting somewhere the walk did not look.
fn wired_subcommands(v: &serde_json::Value) -> Vec<String> {
    let mut out = Vec::new();
    walk(v, &mut out);
    out.sort();
    out.dedup();
    return out;

    fn walk(v: &serde_json::Value, out: &mut Vec<String>) {
        match v {
            serde_json::Value::Object(map) => {
                for (key, val) in map {
                    if key == "command" {
                        if let Some(s) = val.as_str() {
                            if let Some(sub) = named_subcommand(s) {
                                out.push(sub);
                            }
                        }
                    }
                    walk(val, out);
                }
            }
            serde_json::Value::Array(items) => items.iter().for_each(|i| walk(i, out)),
            _ => {}
        }
    }
}

/// The subcommand in `agent-tools <sub> ...`, when the command starts with the
/// binary's bare name. A command that merely mentions `agent-tools` further
/// along is some other program's argument and names no subcommand of ours.
fn named_subcommand(command: &str) -> Option<String> {
    let rest = command.trim_start().strip_prefix("agent-tools ")?;
    let sub = rest.split_whitespace().next()?;
    Some(sub.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn names_the_subcommand_of_a_leading_invocation() {
        assert_eq!(
            named_subcommand("agent-tools hook-post"),
            Some("hook-post".to_string())
        );
        assert_eq!(
            named_subcommand("  agent-tools env-context"),
            Some("env-context".to_string())
        );
        assert_eq!(
            named_subcommand("agent-tools ntfy-hook --action notify"),
            Some("ntfy-hook".to_string())
        );
    }

    #[test]
    fn ignores_commands_that_only_mention_the_binary() {
        assert_eq!(named_subcommand("jq -c '.tool_input'"), None);
        assert_eq!(named_subcommand("echo agent-tools hook-post"), None);
        assert_eq!(named_subcommand("agent-tools"), None);
    }

    #[test]
    fn walks_every_depth_of_a_settings_document() {
        let v: serde_json::Value = serde_json::from_str(
            r#"{"hooks":{
                 "PostToolUse":[{"matcher":"","hooks":[{"command":"agent-tools hook-post"}]}],
                 "UserPromptSubmit":[{"hooks":[{"command":"agent-tools hook-prompt"}]},
                                     {"hooks":[{"command":"agent-tools ntfy-hook --action cancel"}]}],
                 "PreToolUse":[{"hooks":[{"command":"jq -c '.x'"}]}]}}"#,
        )
        .unwrap();
        assert_eq!(
            wired_subcommands(&v),
            vec![
                "hook-post".to_string(),
                "hook-prompt".to_string(),
                "ntfy-hook".to_string()
            ]
        );
    }

    #[test]
    fn an_unknown_wired_subcommand_is_rejected() {
        let dir = tempfile::tempdir().unwrap();
        let settings = dir.path().join("settings.json");
        fs::write(
            &settings,
            r#"{"hooks":{"Stop":[{"hooks":[{"command":"agent-tools nosuchsub"}]}]}}"#,
        )
        .unwrap();

        let known = vec!["hook-post".to_string()];
        let err = assert_wired_subcommands(&settings, &known).unwrap_err();
        assert!(
            err.to_string().contains("agent-tools nosuchsub"),
            "error names the missing subcommand: {err}"
        );

        let known = vec!["nosuchsub".to_string()];
        assert!(assert_wired_subcommands(&settings, &known).is_ok());
    }
}
