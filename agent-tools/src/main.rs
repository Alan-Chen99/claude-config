use std::env;
use std::fs;
use std::io;
use std::os::unix::fs::MetadataExt;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::Command;

use clap::{CommandFactory, Parser, Subcommand};

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

mod background;
mod capture;
mod claude;
mod core;
mod events;
mod hook_input;
mod hook_post;
mod hook_pre;
mod hook_prompt;
mod ledger;
mod meta;
mod opencode;
mod paths;
mod procname;
mod procstat;
mod ps;
mod psrecord;
mod run;
mod signals;
mod status;
mod statusline;

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
        /// "Process identity: `comm` (default) vs `--hide-cmdline` (opt-in)".
        #[arg(long)]
        hide_cmdline: bool,
        /// Bytes captured after the downstream closed before the read end is
        /// dropped. Unset means the production default; the two entry points
        /// never carry their own, or they can disagree about the one case the
        /// bound exists for.
        ///
        /// Nobody running a command has a reason to turn this. It is here
        /// because `drain_capped` reaches `meta.json` only through `run`, so a
        /// test that the bound is recorded would otherwise have to drive the
        /// 256 MiB default to see it, and would not be written.
        #[arg(long)]
        drain_cap_bytes: Option<u64>,
        /// Return as soon as the child has started, then detach. Exit 0 means
        /// started, not succeeded: the child's own status reaches the caller
        /// through the status channel and nowhere else.
        #[arg(long)]
        background: bool,
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        cmd: Vec<String>,
    },
    /// Run a command through the passthrough core with no scope, ledger or hooks.
    /// Exists so passthrough behaviour can be differenced against the bare command.
    /// Not taught by the system prompt: use `run` for anything that needs reporting.
    #[command(name = "run-core")]
    RunCore {
        #[arg(long)]
        capture_dir: std::path::PathBuf,
        /// Bytes captured after the downstream closed before the read end is
        /// dropped. Unset means the production default; the two entry points
        /// never carry their own, or they can disagree about the one case the
        /// bound exists for.
        #[arg(long)]
        drain_cap_bytes: Option<u64>,
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        cmd: Vec<String>,
    },
    /// PreToolUse hook for Bash and Monitor.
    #[command(name = "hook-pre")]
    HookPre,
    /// PostToolUse hook for Bash and Monitor.
    #[command(name = "hook-post")]
    HookPost,
    /// UserPromptSubmit hook: carries pending run status changes into a user turn.
    #[command(name = "hook-prompt")]
    HookPrompt,
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
    /// List tasks for this session. JSON by default, with a settled
    /// capture's detail withheld unless asked for: most captures in a long
    /// session are already finished, and printing all of them costs far more
    /// of a size-limited tool result than the ones still running are worth.
    Ps {
        #[arg(long)]
        task: Option<String>,
        #[arg(long = "session-id")]
        session_id: Option<String>,
        #[arg(long, value_enum, default_value_t = ps::PsFormat::Json)]
        format: ps::PsFormat,
        /// Include captures whose fate is already settled. Off by default:
        /// what is running is what a reader is still acting on.
        #[arg(long)]
        all: bool,
        /// Include the chronological event log. Off by default: on a real
        /// session it was more than half the output, and it answers a
        /// different question than what is running.
        #[arg(long)]
        events: bool,
    },
    /// Launch Claude Code against this checkout's config without installing it.
    Claude {
        /// Arguments forwarded to claude
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
    /// SessionStart hook: reads the hook payload on stdin, emits the
    /// hookSpecificOutput envelope carrying `# Environment` and
    /// `# Scratchpad Directory`. Not usable interactively — it waits on stdin.
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
    /// Exercise `background::detach` once and print what the parent learned.
    ///
    /// Hidden, because it is not a thing to run: it exists so the fork's
    /// process-level properties can be tested at all. `tests/` drives it —
    /// `background.rs` explains why none of those properties is reachable from
    /// a `#[cfg(test)]` module.
    #[command(name = "background-probe", hide = true)]
    BackgroundProbe {
        /// Which property the detached half exercises.
        mode: String,
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
        if !same_dir(&env_root, &build_root) {
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
    let default_root = canonicalize_root(&default_root, "default skills root");

    if !same_dir(&default_root, &build_root) {
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

/// The config directory whose `skills` link names the checkout this process
/// should belong to. `CLAUDE_CONFIG_DIR` relocates every config read Claude
/// Code performs, so inside a session launched against one checkout's config
/// the binary answering that session's hooks has to be that checkout's binary;
/// reading `$HOME/.claude` there would let the installed build serve the
/// session unremarked, which is the silent wrong-checkout result this whole
/// assertion exists to prevent.
fn claude_config_dir() -> Result<PathBuf, String> {
    if let Some(dir) = env::var_os("CLAUDE_CONFIG_DIR") {
        if !dir.is_empty() {
            return Ok(PathBuf::from(dir));
        }
    }
    let home = env::var_os("HOME").ok_or_else(|| "HOME not set".to_string())?;
    Ok(PathBuf::from(home).join(".claude"))
}

pub(crate) fn installed_default_root() -> Result<PathBuf, String> {
    let claude_dir = claude_config_dir()?;
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

/// Directory identity, not path spelling. One directory can be reachable under
/// more than one path — a bind mount serves the same tree under two names, and
/// `canonicalize` resolves symlinks but not mounts — so comparing strings calls
/// two names for one checkout two different roots and rejects a binary built
/// from the installed checkout under its other name.
pub(crate) fn same_dir(a: &Path, b: &Path) -> bool {
    match (fs::metadata(a), fs::metadata(b)) {
        (Ok(a), Ok(b)) => a.dev() == b.dev() && a.ino() == b.ino(),
        _ => false,
    }
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

/// Take the detached wrapper off the caller's descriptors.
///
/// stdout and stderr go to `/dev/null`, and the quieter of the two reasons is
/// the worse one. A forked child inherits fd 1 and fd 2 as the very open file
/// description the caller is using — measured: parent and detached child both
/// showing fd 1 on one pipe object — so a caller reading to EOF, which is
/// Claude Code's Bash tool, `Command::output` and `$(...)` alike, waits for
/// this process rather than for the parent that already answered it, and
/// `--background` returns no sooner than a foreground run. The louder reason is
/// that anything written here afterwards lands in the middle of whatever the
/// caller ran next. The wrapped command's own bytes are unaffected: they go to
/// the capture, which is the whole record of a backgrounded run. This process's
/// own later failures are not in that record — `main` prints them, and past
/// this point nobody reads them — so a backgrounded run that fails after its
/// child started shows up as `abandoned` and says no more than that.
///
/// stdin is left alone unless it is a terminal, so `< file` and heredocs still
/// feed the child — measured: a heredoc reaches a `setsid` child that reads it
/// after the parent has moved on. A terminal is replaced, because a detached
/// process must not read one: it has left the foreground process group, and the
/// read would stop it with `SIGTTIN`.
///
/// Failing is loud rather than best-effort, and the caller is still blocking
/// when it fails, so the reason can still reach it. A partial redirect is a
/// failure too: fd 2 left on the caller's pipe holds it open exactly as fd 1
/// would.
fn detach_std_fds() -> anyhow::Result<()> {
    use std::os::fd::AsRawFd;

    let devnull = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .open("/dev/null")
        .map_err(|e| anyhow::anyhow!("open /dev/null: {e}"))?;

    let point_at_devnull = |target: i32| -> anyhow::Result<()> {
        // SAFETY: `dup2` is safe to call for any two integers; it is `unsafe`
        // only as a raw FFI declaration. The source is a descriptor this scope
        // owns and the target is one of this process's own standard three.
        if unsafe { libc::dup2(devnull.as_raw_fd(), target) } == -1 {
            return Err(anyhow::anyhow!(
                "point fd {target} at /dev/null: {}",
                io::Error::last_os_error()
            ));
        }
        Ok(())
    };
    point_at_devnull(libc::STDOUT_FILENO)?;
    point_at_devnull(libc::STDERR_FILENO)?;
    // SAFETY: as above. `isatty` answers 0 for a closed descriptor too, which
    // is the right answer here: there is nothing to take this process off.
    if unsafe { libc::isatty(libc::STDIN_FILENO) } == 1 {
        point_at_devnull(libc::STDIN_FILENO)?;
    }
    Ok(())
}

/// Subcommand names `settings.json` may wire a hook to.
///
/// Hidden subcommands are excluded. `get_subcommands` yields them too, so
/// taking the list unfiltered widens what a settings file is allowed to name
/// every time a hidden one is added — a decision nobody makes and nobody sees.
/// A hook wired to `background-probe` is a mistake worth the loud failure
/// `assert_wired_subcommands` gives it.
fn wireable_subcommands() -> Vec<String> {
    Cli::command()
        .get_subcommands()
        .filter(|c| !c.is_hide_set())
        .map(|c| c.get_name().to_string())
        .collect()
}

fn main() {
    let cli = Cli::parse();
    let root = repo_root();

    match cli.command {
        Cmd::Run {
            desc,
            hide_cmdline,
            drain_cap_bytes,
            background,
            cmd,
        } => {
            // Ahead of the runtime, and that ordering is the whole reason this
            // arm is shaped this way: a tokio runtime's worker threads do not
            // cross `fork`, and `detach` refuses to fork a process that has
            // started any thread at all rather than hand the child an address
            // space where a departed thread still holds a lock. Anything added
            // above this line that starts a thread turns `--background` into a
            // hard failure — which is the good outcome, and the one that guard
            // buys.
            let mut reporter = None;
            if background {
                match background::detach() {
                    // The child said it started, and saying so is all that is
                    // left for this process to do.
                    background::Detached::Parent(Ok(line)) => {
                        println!("{line}");
                        std::process::exit(0);
                    }
                    // Not a promise that nothing is running. The report is
                    // made after the child exists — `on_spawn` in run.rs argues
                    // why that order is the right one — so a wrapper killed in
                    // between leaves this caller reading an empty pipe while the
                    // child it spawned runs on, reparented to init in the
                    // wrapper's own session. `agent-tools ps` is where to check.
                    background::Detached::Parent(Err(e)) => {
                        eprintln!("agent-tools: run: {e:#}");
                        std::process::exit(2);
                    }
                    // Detached, in a session of its own, holding the one channel
                    // back to a caller that is still blocking on it.
                    background::Detached::Child(r) => {
                        if let Err(e) = detach_std_fds() {
                            // Reported rather than shrugged off: a wrapper that
                            // cannot leave the caller's descriptors is not
                            // backgrounded at all — the caller's read ends when
                            // this process does, which is the wait the flag
                            // exists to remove — and it presents as a hang
                            // rather than as a failure. The caller is still
                            // listening here, so it can be told instead.
                            r.failed(&e);
                        }
                        reporter = Some(r);
                    }
                }
            }
            let code = tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(run::run(desc, hide_cmdline, drain_cap_bytes, reporter, cmd));
            match code {
                Ok(c) => std::process::exit(c),
                Err(e) => {
                    // `agent-tools: `, not the `agent-tools <sub>: ` the
                    // other subcommands' arms spell. This print and
                    // `run-core`'s are the only two a caller can meet *after*
                    // it has already seen its command's output:
                    // `core::run_core` raises its wait failure with the tees
                    // running, `run::run` passes it through, and it lands
                    // here. The system prompt promises the agent that a line
                    // beginning `agent-tools:` is the wrapper's own rather
                    // than its command's, which is the only thing separating
                    // the two once they share a stream. The arms that can fail
                    // only before a child exists never interleave with command
                    // output, so the inconsistency is deliberate — except
                    // `run::run`'s own empty-command check, which reaches this
                    // print before any child exists and keeps the prefix
                    // anyway. Harmless: nothing else is writing to stderr at
                    // that point for it to be confused with, and the promise
                    // runs one way — a line beginning `agent-tools:` is the
                    // wrapper's, not that every wrapper line begins one.
                    // `scripts/check-prompt-coupling.sh` pins the prompt's
                    // half of that promise and `capture.rs`'s five
                    // diagnostics; these two carry it uncovered, which is why
                    // the reason lives here.
                    eprintln!("agent-tools: run: {e:#}");
                    std::process::exit(2);
                }
            }
        }
        Cmd::RunCore {
            capture_dir,
            drain_cap_bytes,
            cmd,
        } => {
            if cmd.is_empty() {
                eprintln!("agent-tools run-core: no command supplied after --");
                std::process::exit(2);
            }
            let outcome = tokio::runtime::Builder::new_multi_thread()
                .enable_all()
                .build()
                .unwrap()
                .block_on(core::run_core(
                    &cmd,
                    &capture_dir,
                    drain_cap_bytes,
                    core::Destination::Caller,
                    |_, _| {},
                    |_| {},
                ));
            match outcome {
                Ok(o) => std::process::exit(o.exit_code),
                Err(e) => {
                    // Prefixed `agent-tools:` for the reason `Cmd::Run`'s arm
                    // spells out: reachable with the tees already running, so a
                    // caller can meet it after its command's own output. The
                    // no-command print above cannot — it fires before a child
                    // exists — so it keeps the subcommand-qualified form.
                    eprintln!("agent-tools: run-core: {e}");
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
        Cmd::HookPrompt => {
            if let Err(e) = hook_prompt::run() {
                eprintln!("agent-tools hook-prompt: {e:#}");
                std::process::exit(1);
            }
            std::process::exit(0);
        }
        Cmd::Ps {
            task,
            session_id,
            format,
            all,
            events,
        } => {
            if let Err(e) = ps::run(task, session_id, format, all, events) {
                eprintln!("agent-tools ps: {e:#}");
                std::process::exit(1);
            }
        }
        Cmd::Claude { args } => {
            let known = wireable_subcommands();
            if let Err(e) = claude::run(&root, &known, args) {
                eprintln!("agent-tools claude: {e:#}");
                std::process::exit(1);
            }
            std::process::exit(0);
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
        // Reached with this binary's whole prologue behind it — `Cli::parse`
        // and `repo_root`, neither of which starts a thread — and no setup of
        // its own. That is not incidental: `detach` forks only from a
        // single-threaded process, so a probe that forks has measured the
        // startup every subcommand shares, rather than a tidier path arranged
        // for the test.
        Cmd::BackgroundProbe { mode } => background::probe(&mode),
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
            Cmd::HookPrompt => unreachable!(),
            Cmd::Run { .. } => unreachable!(),
            Cmd::RunCore { .. } => unreachable!(),
            Cmd::Ps { .. } => unreachable!(),
            Cmd::OpencodeGate { .. } => unreachable!(),
            Cmd::MinGate { .. } => unreachable!(),
            Cmd::Claude { .. } => unreachable!(),
            Cmd::BackgroundProbe { .. } => unreachable!(),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The list guards which subcommands `settings.json` may wire a hook to,
    /// so a hidden one leaking into it silently widens that surface.
    #[test]
    fn a_hidden_subcommand_is_not_wireable_from_settings() {
        let wireable = wireable_subcommands();
        assert!(
            wireable.iter().any(|s| s == "hook-post"),
            "an ordinary subcommand stays wireable: {wireable:?}"
        );
        assert!(
            !wireable.iter().any(|s| s == "background-probe"),
            "a hidden subcommand must not be wireable: {wireable:?}"
        );
    }
}
