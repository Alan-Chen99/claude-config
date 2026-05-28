use std::env;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

use clap::{Parser, Subcommand};

mod capture;
mod events;
mod hook_input;
mod hook_post;
mod hook_pre;
mod meta;
mod opencode;
mod paths;
mod ps;
mod run;
mod signals;

#[derive(Parser)]
#[command(name = "agent-tools")]
struct Cli {
    /// Override the claude-config root directory (e.g., point at a worktree).
    /// Takes precedence over CLAUDE_CONFIG_ROOT and the ~/.claude/skills symlink.
    /// Place before the subcommand to avoid ambiguity with subcommand args
    /// (subcommands capture trailing args verbatim). Has no effect on
    /// subcommands that don't resolve the repo root (run, hook-pre, hook-post, ps).
    #[arg(long, global = true, value_name = "PATH")]
    root: Option<PathBuf>,

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
    /// Pretty-print one MITM intercept log file (~/.claude/requests-log/<session>/NNNN.json)
    #[command(name = "cc-pretty-intercept")]
    CcPrettyIntercept {
        /// Arguments forwarded to cc-pretty-intercept
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Extract sub-agent workflow summary from a session log
    CcWorkflow {
        /// Arguments forwarded to cc-workflow-extract
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Claude Code ntfy notification hook
    #[command(name = "ntfy-hook")]
    NtfyHook {
        /// Arguments forwarded to claude_config.ntfy_hook
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Wrap a command inside an active wrap-task (for pipeline capture).
    Run {
        #[arg(long)]
        desc: Option<String>,
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        cmd: Vec<String>,
    },
    /// PreToolUse hook for Bash and Monitor.
    #[command(name = "hook-pre")]
    HookPre,
    /// PostToolUse hook for Bash and Monitor.
    #[command(name = "hook-post")]
    HookPost,
    /// pre_output script used in output styles
    #[command(name = "pre_output.record")]
    PreOutputRecord {
        /// JSON argument (accepted and discarded)
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// No-op prompt gate used by opencode agent instructions
    #[command(name = "opencode.gate")]
    OpencodeGate {
        /// Arguments accepted and discarded
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// Count tokens via Anthropic count_tokens API: agent-tools count-tokens [--model M] [--file P] [TEXT]
    #[command(name = "count-tokens")]
    CountTokens {
        /// Arguments forwarded to claude_config.count_tokens
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// List or filter live tasks for this session.
    Ps {
        #[arg(long)]
        task: Option<String>,
        #[arg(long = "session-id")]
        session_id: Option<String>,
    },
    /// Print the '# Environment' block (cwd, git, platform, shell, OS) for SessionStart hooks.
    #[command(name = "env-context")]
    EnvContext,
    /// Launch opencode with claude-config .env mappings.
    Opencode {
        /// Arguments forwarded to opencode
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
}

/// Resolve the claude-config repository root.
///
/// Priority:
///   1. --root CLI flag (highest, for ad-hoc override in a worktree)
///   2. CLAUDE_CONFIG_ROOT env var (persistent override, e.g. exported in a shell)
///   3. Derived from ~/.claude/skills symlink target (parent of target)
fn repo_root(cli_root: Option<PathBuf>) -> PathBuf {
    if let Some(root) = cli_root {
        return root;
    }
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
    // The MITM intercept proxy (scripts/intercept) only forwards api.anthropic.com
    // and lacks a trusted CA path for uv's PyPI fetches. If uv needs to resolve
    // or install packages on venv update, going through the intercept fails TLS.
    // Strip HTTPS_PROXY so uv talks to PyPI directly.
    cmd.env_remove("HTTPS_PROXY");
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

    match cli.command {
        Cmd::Run { desc, cmd } => {
            let code = tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(run::run(desc, cmd));
            match code {
                Ok(c) => std::process::exit(c),
                Err(e) => {
                    eprintln!("agent-tools run: {e:#}");
                    std::process::exit(2);
                }
            }
        }
        Cmd::HookPre => {
            if let Err(e) = hook_pre::run() {
                eprintln!("agent-tools hook-pre: {e:#}");
                std::process::exit(1);
            }
            std::process::exit(0);
        }
        Cmd::HookPost => {
            if let Err(e) = hook_post::run() {
                eprintln!("agent-tools hook-post: {e:#}");
                std::process::exit(1);
            }
            std::process::exit(0);
        }
        Cmd::Ps { task, session_id } => {
            if let Err(e) = ps::run(task, session_id) {
                eprintln!("agent-tools ps: {e:#}");
                std::process::exit(1);
            }
        }
        Cmd::OpencodeGate { args: _ } => std::process::exit(0),
        cmd => {
            let root = repo_root(cli.root);
            match cmd {
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
                Cmd::CcPrettyIntercept { args } => {
                    uv_run(
                        &root,
                        &root,
                        &["python3", "-m", "claude_config.cc_pretty_intercept.main"],
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
                Cmd::NtfyHook { args } => {
                    uv_run(
                        &root,
                        &root,
                        &["python3", "-m", "claude_config.ntfy_hook"],
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
                Cmd::CountTokens { args } => {
                    uv_run(
                        &root,
                        &root,
                        &["python3", "-m", "claude_config.count_tokens"],
                        &args,
                    );
                }
                Cmd::EnvContext => {
                    let cwd = env::current_dir().unwrap_or_else(|e| panic!("cannot read cwd: {e}"));
                    uv_run(
                        &root,
                        &cwd,
                        &["python3", "-m", "claude_config.env_context"],
                        &[],
                    );
                }
                Cmd::Opencode { args } => opencode::run(&root, &args),
                Cmd::HookPre => unreachable!(),
                Cmd::HookPost => unreachable!(),
                Cmd::Run { .. } => unreachable!(),
                Cmd::Ps { .. } => unreachable!(),
                Cmd::OpencodeGate { .. } => unreachable!(),
            }
        }
    }
}
