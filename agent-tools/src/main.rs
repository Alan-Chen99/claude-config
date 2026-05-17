use std::env;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

use clap::{Parser, Subcommand};

mod hook_input;

#[derive(Parser)]
#[command(name = "agent-tools")]
struct Cli {
    #[command(subcommand)]
    command: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Run a skill script: agent-tools skill <module.entry> [args...]
    Skill {
        /// Python module path (e.g. do.do, alan_coding_style.coding_style)
        module: String,
        /// Arguments forwarded to the skill script
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Pretty-print a Claude Code JSONL session log
    CcPretty {
        /// Arguments forwarded to cc-pretty
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Extract sub-agent workflow summary from a session log
    CcWorkflow {
        /// Arguments forwarded to cc-workflow-extract
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// pre_output script used in output styles
    #[command(name = "pre_output.record")]
    PreOutputRecord {
        /// JSON argument (accepted and discarded)
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
}

/// Resolve the claude-config repository root.
///
/// Priority:
///   1. CLAUDE_CONFIG_ROOT env var (for testing in worktrees)
///   2. Derived from ~/.claude/skills symlink target (parent of target)
fn repo_root() -> PathBuf {
    if let Ok(root) = env::var("CLAUDE_CONFIG_ROOT") {
        return PathBuf::from(root);
    }
    // Derive from ~/.claude/skills symlink — its target is <repo_root>/skills
    let claude_dir = PathBuf::from(env::var("HOME").expect("HOME not set")).join(".claude");
    let skills_link = claude_dir.join("skills");
    let target = std::fs::read_link(&skills_link)
        .unwrap_or_else(|e| panic!("cannot read symlink {}: {e}", skills_link.display()));
    target
        .parent()
        .unwrap_or_else(|| panic!("symlink target {} has no parent", target.display()))
        .to_path_buf()
}

/// Derive the venv path for a project root: ~/.claude/venvs/<basename>/
fn venv_path(root: &Path) -> PathBuf {
    let home = env::var("HOME").expect("HOME not set");
    let name = root
        .file_name()
        .unwrap_or_else(|| panic!("root {} has no basename", root.display()));
    Path::new(&home).join(".claude/venvs").join(name)
}

fn uv_run(root: &Path, working_dir: &Path, python_args: &[&str], extra_args: &[String]) -> ! {
    let mut cmd = Command::new("uv");
    // --project already specifies the venv; inherited VIRTUAL_ENV from the
    // shell may point to a different worktree and triggers a noisy warning.
    cmd.env_remove("VIRTUAL_ENV");
    cmd.env("UV_PROJECT_ENVIRONMENT", venv_path(root));
    cmd.arg("run").arg("--project").arg(root);
    for a in python_args {
        cmd.arg(a);
    }
    cmd.args(extra_args);
    cmd.current_dir(working_dir);
    let err = cmd.exec();
    eprintln!("agent-tools: exec uv failed: {err}");
    std::process::exit(1);
}

fn main() {
    let cli = Cli::parse();
    let root = repo_root();

    match cli.command {
        Cmd::Skill { module, args } => {
            let full_module = format!("skills.{module}");
            uv_run(
                &root,
                &root.join("skills/scripts"),
                &["python3", "-m", &full_module],
                &args,
            );
        }
        Cmd::CcPretty { args } => {
            uv_run(
                &root,
                &root,
                &["python3", "-m", "claude_config.cc_pretty.main"],
                &args,
            );
        }
        Cmd::CcWorkflow { args } => {
            uv_run(
                &root,
                &root,
                &["python3", "-m", "claude_config.cc_workflow.extract"],
                &args,
            );
        }
        Cmd::PreOutputRecord { args } => {
            uv_run(
                &root,
                &root,
                &["python3", "-m", "claude_config.pre_output.record"],
                &args,
            );
        }
    }
}
