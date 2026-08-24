use std::env;
use std::io;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

use clap::{Parser, Subcommand};

/// Printed to stdout by `agent-tools opencode.gate`. Coupled to
/// `opencode/agents/alan-default-ids.md` step 4/5 wording — see agent-tools CLAUDE.md
/// "Prompt-coupled strings" table.
const GATE_STDOUT: &str = "\
(R060) Consider any mistakes or problems you may have made — across the work you did, the draft output, and your identification of the task and user motivations — and take further action or revise accordingly. The items below are reminders to check specific rules; they are not a complete checklist.

(R060-G1) Check the big picture you identified. If it is smaller than the codebase you are working on, it's almost certainly too small: what you do has a broader impact.
(R060-G2) Insufficient verification or overconfidence is a mistake.
(R060-G3) An omission — something you failed to do or surface — is a mistake, not only an incorrect action.
(R060-G4) Check R043: if your chosen interpretation is wrong, would the user be able to cleanly reject your work without doing difficult verification or judgment? If not, make rejection cheaper.
(R060-G5) WARNING: a common failure point is noticing problems INSIDE your chosen frame but missing problems CAUSED BY your framing. What concrete things might your draft fail to address because you framed the task one way rather than another? Name those.
(R060-G6) Check R090 — what are implicit work assigned to user?
(R060-G7) For your draft's main claim, what does your evidence actually show (not what it suggests), and where does the draft go beyond it? Identify one or more unrun tool calls (read, grep, glob, bash, webfetch) that would discriminate, OR weaken the claim to only what evidence has shown.

If this surfaced new work or a revision, do it and re-enter the gate at the next version. Otherwise send the final response.
";

/// Printed to stdout by `agent-tools min.gate`. Coupled to
/// `opencode/agents/min.md` step 4/5/6 wording AND to the body rules
/// R002 (big-picture optimization target) / R043 (cheap-rejection
/// transparency) / R090 (no implicit work-assignment) which G1/G4/G6
/// point at — see agent-tools CLAUDE.md "Prompt-coupled strings" table.
///
/// The min gate is the deliberately-thin counterpart to `opencode.gate`. It
/// numbers the umbrella rule (R060 — consider mistakes) and uses
/// pointer-style guidance: items reference rules defined in the agent
/// prompt body rather than restating them, so the gate is a reminder list
/// rather than a complete checklist. Reframed in round 7 of the
/// compliance-check failure-mode investigation (see
/// `notes/compliance-check-failure-mode.md`): cites moved from
/// G3→R070 / G5→R090 to G1→R002 / G4→R043 / G6→R090 after R070/G080
/// were dissolved into the big-picture optimization target.
const MIN_GATE_STDOUT: &str = "\
(R060) Consider any mistakes or problems you may have made — across the work you did, the draft output, and your identification of the task and user motivations — and take further action or revise accordingly. The items below are reminders to check specific rules; they are not a complete checklist.

(R060-G1) Check the big picture you identified. If it is smaller than the codebase you are working on, it's almost certainly too small: what you do has a broader impact.
(R060-G2) Insufficient verification or overconfidence is a mistake.
(R060-G3) An omission — something you failed to do or surface — is a mistake, not only an incorrect action.
(R060-G4) Check R043: if your chosen interpretation is wrong, would the user be able to cleanly reject your work without doing difficult verification or judgment? If not, make rejection cheaper.
(R060-G5) WARNING: a common failure point is noticing problems INSIDE your chosen frame but missing problems CAUSED BY your framing. What concrete things might your draft fail to address because you framed the task one way rather than another? Name those.
(R060-G6) Check R090 — what are implicit work assigned to user?

If this surfaced new work or a revision, do it and re-enter the gate at the next version. Otherwise send the final response.
";

mod capture;
mod events;
mod hook_input;
mod hook_post;
mod hook_pre;
mod meta;
mod opencode;
mod paths;
mod procname;
mod procstat;
mod ps;
mod run;
mod signals;
mod status;

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
        /// Overwrite /proc/self/cmdline to hide --desc and the wrapped
        /// command from peer processes reading `ps aux` /
        /// `/proc/*/cmdline`. Opt-in because the default cmdline is
        /// load-bearing for debugging; only enable for probe /
        /// contamination-sensitive work. See agent-tools CLAUDE.md
        /// "`--desc` argv hiding (F88)".
        #[arg(long)]
        hide_cmdline: bool,
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
    /// No-op prompt gate used by the diagnostic `min` agent.
    /// Thinner counterpart to `opencode.gate`; see MIN_GATE_STDOUT.
    #[command(name = "min.gate")]
    MinGate {
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
    /// Pretty-print an opencode session
    #[command(name = "opencode-pretty")]
    OpencodePretty {
        /// Arguments forwarded to opencode-pretty
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
}

/// Resolve the claude-config repository root from the binary's build root.
///
/// `CLAUDE_CONFIG_ROOT` is an assertion, not an override: if present it must
/// match this binary's compiled root. When running a worktree build distinct
/// from the installed default, it must be present so test harnesses fail loudly
/// instead of silently exercising a stale binary/root pairing.
fn repo_root() -> PathBuf {
    let build_root = canonicalize_root(compiled_root(), "compiled claude-config root");

    if let Some(env_root) = env::var_os("CLAUDE_CONFIG_ROOT") {
        let env_root_raw = PathBuf::from(env_root);
        let env_root = canonicalize_root(&env_root_raw, "CLAUDE_CONFIG_ROOT");
        if env_root != build_root {
            root_error(format!(
                "CLAUDE_CONFIG_ROOT does not match this agent-tools binary\n  binary root: {}\n  CLAUDE_CONFIG_ROOT: {}\nRebuild or invoke the agent-tools binary from the matching checkout.",
                build_root.display(),
                env_root.display()
            ));
        }
        return build_root;
    }

    let default_root = installed_default_root().unwrap_or_else(|err| {
        root_error(format!(
            "CLAUDE_CONFIG_ROOT is unset and the installed default root could not be determined: {err}\n  binary root: {}\nSet CLAUDE_CONFIG_ROOT={} when running this binary from a worktree.",
            build_root.display(),
            build_root.display()
        ));
    });
    let default_root = canonicalize_root(&default_root, "default ~/.claude/skills root");

    if default_root != build_root {
        root_error(format!(
            "CLAUDE_CONFIG_ROOT is required for this non-default agent-tools binary\n  binary root: {}\n  default root: {}\nSet CLAUDE_CONFIG_ROOT={} and retry.",
            build_root.display(),
            default_root.display(),
            build_root.display()
        ));
    }

    build_root
}

fn compiled_root() -> &'static Path {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("agent-tools/ should have a parent")
}

fn installed_default_root() -> Result<PathBuf, String> {
    let home = env::var_os("HOME").ok_or_else(|| "HOME not set".to_string())?;
    let claude_dir = PathBuf::from(home).join(".claude");
    let skills_link = claude_dir.join("skills");
    let target = std::fs::read_link(&skills_link)
        .map_err(|e| format!("cannot read symlink {}: {e}", skills_link.display()))?;
    let target = if target.is_absolute() {
        target
    } else {
        skills_link
            .parent()
            .expect("skills symlink has a parent")
            .join(target)
    };
    let root = target
        .parent()
        .ok_or_else(|| format!("symlink target {} has no parent", target.display()))?;
    Ok(root.to_path_buf())
}

fn canonicalize_root(path: impl AsRef<Path>, label: &str) -> PathBuf {
    let path = path.as_ref();
    std::fs::canonicalize(path).unwrap_or_else(|e| {
        root_error(format!(
            "cannot canonicalize {label} {}: {e}",
            path.display()
        ));
    })
}

fn root_error(message: String) -> ! {
    eprintln!("agent-tools: {message}");
    std::process::exit(2);
}

/// Drain stdin into the void. Mirrors `cat > /dev/null` from the original
/// shell gate (`gate-frame.sh`). Required so the heredoc input the prompt
/// instructs the agent to send actually has a reader; without it, the gate
/// binary races to exit before the caller finishes writing and the caller
/// observes EPIPE (see opencode_test.rs heredoc tests under full-suite
/// parallel load).
fn drain_stdin() {
    let _ = io::copy(&mut io::stdin().lock(), &mut io::sink());
}

/// Derive the venv path for a project root: ~/.claude/venvs/<basename>/
fn venv_path(root: &Path) -> PathBuf {
    let home = env::var("HOME").expect("HOME not set");
    let name = root
        .file_name()
        .unwrap_or_else(|| panic!("root {} has no basename", root.display()));
    Path::new(&home).join(".claude/venvs").join(name)
}

/// Exec `uv run --project <root> <python_args...> <extra_args...>`.
///
/// The child inherits the caller's cwd so relative-path arguments the user
/// passes on the command line (e.g. `agent-tools count-tokens --file foo.txt`)
/// resolve against where the user actually invoked agent-tools, not the
/// claude-config repo root. `uv --project` locates the venv, so cwd never
/// needs to move to `root` for uv itself.
///
/// `extra_pythonpath` is prepended to `PYTHONPATH` for cases like
/// `agent-tools skill <mod>` where `python3 -m skills.<mod>` needs
/// `<root>/skills/scripts` on `sys.path` for module resolution.
fn uv_run(
    root: &Path,
    extra_pythonpath: Option<&Path>,
    python_args: &[&str],
    extra_args: &[String],
) -> ! {
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
    if let Some(extra) = extra_pythonpath {
        let mut combined = extra.as_os_str().to_owned();
        if let Some(existing) = env::var_os("PYTHONPATH") {
            if !existing.is_empty() {
                combined.push(":");
                combined.push(&existing);
            }
        }
        cmd.env("PYTHONPATH", combined);
    }
    cmd.arg("run").arg("--project").arg(root);
    for a in python_args {
        cmd.arg(a);
    }
    cmd.args(extra_args);
    let err = cmd.exec();
    eprintln!("agent-tools: exec uv failed: {err}");
    std::process::exit(1);
}

fn main() {
    let cli = Cli::parse();
    let root = repo_root();

    match cli.command {
        Cmd::Run { desc, hide_cmdline, cmd } => {
            let code = tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(run::run(desc, hide_cmdline, cmd));
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
        Cmd::OpencodeGate { args: _ } => {
            drain_stdin();
            print!("{GATE_STDOUT}");
            std::process::exit(0);
        }
        Cmd::MinGate { args: _ } => {
            drain_stdin();
            print!("{MIN_GATE_STDOUT}");
            std::process::exit(0);
        }
        cmd => match cmd {
            Cmd::Skill { module, args } => {
                let full_module = format!("skills.{module}");
                let skills_scripts = root.join("skills/scripts");
                uv_run(
                    &root,
                    Some(&skills_scripts),
                    &["python3", "-m", &full_module],
                    &args,
                );
            }
            Cmd::CcPretty { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.cc_pretty.main"],
                    &args,
                );
            }
            Cmd::CcPrettyIntercept { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.cc_pretty_intercept.main"],
                    &args,
                );
            }
            Cmd::CcWorkflow { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.cc_workflow.extract"],
                    &args,
                );
            }
            Cmd::NtfyHook { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.ntfy_hook"],
                    &args,
                );
            }
            Cmd::PreOutputRecord { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.pre_output.record"],
                    &args,
                );
            }
            Cmd::CountTokens { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.count_tokens"],
                    &args,
                );
            }
            Cmd::EnvContext => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.env_context"],
                    &[],
                );
            }
            Cmd::Opencode { args } => opencode::run(&root, &args),
            Cmd::OpencodePretty { args } => {
                uv_run(
                    &root,
                    None,
                    &["python3", "-m", "claude_config.opencode_pretty.main"],
                    &args,
                );
            }
            Cmd::HookPre => unreachable!(),
            Cmd::HookPost => unreachable!(),
            Cmd::Run { .. } => unreachable!(),
            Cmd::Ps { .. } => unreachable!(),
            Cmd::OpencodeGate { .. } => unreachable!(),
            Cmd::MinGate { .. } => unreachable!(),
        },
    }
}
