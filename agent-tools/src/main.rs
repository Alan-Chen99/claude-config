use std::env;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

use clap::{Parser, Subcommand};

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
}

/// Resolve the claude-config repository root.
///
/// Priority:
///   1. CLAUDE_CONFIG_ROOT env var (for testing in worktrees)
///   2. Hardcoded default (system-specific)
fn repo_root() -> PathBuf {
    if let Ok(root) = env::var("CLAUDE_CONFIG_ROOT") {
        return PathBuf::from(root);
    }
    // Default location — change per system
    PathBuf::from("/repos/claude-config")
}

fn uv_run(root: &Path, working_dir: &Path, python_args: &[&str], extra_args: &[String]) -> ! {
    let mut cmd = Command::new("uv");
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
    }
}
