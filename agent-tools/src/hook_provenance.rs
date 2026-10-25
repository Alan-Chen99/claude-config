//! Records the launch configuration into the session transcript, out of the
//! model's context.
//!
//! A session's behaviour is read back off its JSONL long after the launcher
//! that produced it has moved on. What the transcript already carries is the
//! *delivered* treatment — `total_tokens_reminder` attachments, a
//! `prompt_snapshot` holding the system prompt — and what it does not carry is
//! which configuration produced it: the arm a launcher drew, the set of arms it
//! drew from, the settings that fixed the compaction stratum. Reconstructing
//! that from a repository at analysis time fails exactly when it matters, while
//! the launcher is uncommitted and being edited between sessions.
//!
//! The channel is a plain-stdout hook on an event whose stdout Claude Code
//! records but never converts for the API. Measured on 2.1.269: a `command`
//! hook exiting 0 with non-JSON stdout yields an `attachment` record of subtype
//! `hook_success` carrying `content` (trimmed) and `stdout` (raw); for
//! `SessionStart`, `UserPromptSubmit` and `UserPromptExpansion` the record also
//! gains a `rendered` array turning it into a `<system-reminder>`, and for
//! every other event `rendered` is absent — the conversion arm returns nothing
//! (`chunk-j0tbz6ra.js:204316`, marker `hook success: `). Every event but those
//! three is therefore a
//! write-only channel into the transcript, which is what this wants: a reader
//! can find the configuration, and the session under measurement never sees it.
//!
//! Stdout that parses as hook JSON lands in `stdout` with `content` empty and is
//! acted on, so the block is deliberately plain text.
//!
//! Wired on `PostToolUse`, `PostToolUseFailure` and `Stop`, because no one of
//! them covers a session: `Stop` does not fire when a turn is interrupted
//! (`chunk-tqjdehqd.js:3185`, marker `Stop hook cancelled (abort or stream
//! teardown)`), the two tool events never fire in a session
//! that calls no tool, and a failed call reaches only the second of them.
//! Whichever arrives first writes the record; the sentinel makes every later
//! invocation a stat and an exit.
//!
//! The sentinel is per Claude Code process within a session, not per session.
//! A resume keeps the session id and appends to the same transcript from a new
//! process that its launcher configured afresh — `claude.sh` draws its trial
//! arm again — so a record per session would label every resumed stretch with
//! the configuration of the process before it. Observed under v1, which kept
//! one: `7da642fa`'s only record reads `off`, and 52 `<total_tokens>` markers
//! follow its `SessionStart:resume`.
//!
//! The launchers are read when the record is written, not when the process
//! started, and a `/clear` hours into a process writes the new session's
//! record then. A launcher modified since the process started is flagged on
//! its line rather than presented as what ran.
//!
//! `PreToolUse` would fire marginally earlier and is deliberately not used: a
//! `PreToolUse` hook's exit code is a permission verdict, so any way of exiting
//! 2 there denies the tool call. That is not hypothetical — `clap` exits 2 for
//! an unrecognized subcommand, and `~/.claude/settings.json` is a symlink into
//! the checkout, live the moment a merge lands and before `install.sh` has
//! rebuilt the binary. On these events the same skew costs an error message
//! instead of a session that cannot run a tool.
//!
//! This hook never exits non-zero. Clap and root resolution run before it and
//! exit 2 on that same skew or a root mismatch, which on `Stop` keeps the turn
//! from ending, so `settings.json` wires it `|| true`. A failure to record
//! provenance must not be silent either, since an unlabelled session is the
//! defect this exists to prevent, so failures are reported into the block
//! itself under `errors:`.

use anyhow::Result;
use std::collections::BTreeMap;
use std::fmt::Write as _;
use std::fs;
use std::io::{ErrorKind, Read, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, SystemTime};

use serde::Deserialize;

/// Bumped when the block's shape changes, so a reader can tell which grammar a
/// record follows rather than inferring it from which fields happen to be there.
/// v1: one record per session. v2: one per process, with a `process:` line,
/// and launchers flagged when modified after the process started.
const FORMAT: &str = "v2";

/// Name of the sentinel inside the session's agent-tools state directory,
/// suffixed `.<pid>-<start ticks>` when the process is known.
const SENTINEL: &str = "launch-provenance";

/// Above this, a source file is named and its size reported instead of being
/// emitted. Every file this reads is hand-written config in the low kilobytes;
/// the cap exists so a path that unexpectedly resolves to something enormous
/// cannot push a session's whole transcript around.
const SOURCE_BYTE_CAP: u64 = 64 * 1024;

/// Environment a launcher can set that changes how a session behaves or how its
/// transcript must be stratified. Prefix match, so a variable a future Claude
/// Code release adds is recorded without this list being edited.
const ENV_PREFIXES: [&str; 4] = ["CLAUDE", "ANTHROPIC_", "KIMI_", "ZAI_"];

/// Variables outside those prefixes that still decide something. The two
/// `DISABLE_*COMPACT` names silently return a session to the model window,
/// which moves the compaction stratum; the proxy and Node variables decide
/// whether the session's requests were intercepted, i.e. whether a per-request
/// record exists to cross-check this one against.
const ENV_EXACT: [&str; 8] = [
    "DISABLE_AUTO_COMPACT",
    "DISABLE_COMPACT",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "IS_SANDBOX",
    "NODE_EXTRA_CA_CERTS",
    "NODE_OPTIONS",
    "NO_PROXY",
];

/// Final underscore-separated word of a name that makes its value a credential.
/// Matched as a whole word rather than as a substring, because
/// `CLAUDE_CODE_MAX_CONTEXT_TOKENS` ends in `TOKENS` and is a window size that
/// has to stay readable.
const SECRET_WORDS: [&str; 6] = [
    "CREDENTIAL",
    "CREDENTIALS",
    "KEY",
    "PASSWD",
    "PASSWORD",
    "SECRET",
];

/// `TOKEN` singular only — see `SECRET_WORDS`.
const SECRET_WORD_TOKEN: &str = "TOKEN";

/// The union of every hook payload this answers. `Stop` carries no `agent_id`
/// and a tool event carries one only inside a subagent; every field past the
/// session id is optional, so one struct parses any of the three and a shape
/// change to one event cannot break the others.
#[derive(Debug, Deserialize)]
struct Payload {
    session_id: String,
    #[serde(default)]
    agent_id: Option<String>,
    #[serde(default)]
    hook_event_name: Option<String>,
    #[serde(default)]
    cwd: Option<String>,
}

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf)?;
    let payload: Payload = match serde_json::from_str(&buf) {
        Ok(p) => p,
        // Without a session id there is no sentinel to claim, so emitting would
        // repeat the block on every tool call of every session. Say why, once
        // per invocation, on the stream that does not become a record.
        Err(e) => {
            eprintln!("agent-tools hook-provenance: unparseable hook payload: {e}");
            return Ok(());
        }
    };

    // A subagent's hook_success records land in the subagent's own transcript
    // file, where a reader looking for the session's configuration would not
    // find them. The main thread reaches this too, and writes the record there.
    if payload.agent_id.is_some() {
        return Ok(());
    }

    let mut errors: Vec<String> = Vec::new();
    let process = current_process();
    let sentinel = match &process {
        Ok(p) => format!("{SENTINEL}.{}-{}", p.pid, p.start_ticks),
        Err(e) => {
            errors.push(format!(
                "process: {e}; recorded once per session, so a resumed session's new process records nothing"
            ));
            SENTINEL.to_string()
        }
    };
    let session_dir = match crate::paths::state_root() {
        Ok(root) => Some(root.join(&payload.session_id)),
        Err(e) => {
            errors.push(format!("sentinel: {e}"));
            None
        }
    };
    if let Some(dir) = session_dir {
        match claim_sentinel_in(&dir, &sentinel) {
            Sentinel::Claimed => {}
            Sentinel::AlreadyHeld => return Ok(()),
            // Emitting anyway is the loud failure: the block still reaches the
            // transcript, possibly more than once, and says what stopped the
            // sentinel — which a reader can see. Staying silent would lose the
            // session's label to an unreported filesystem error.
            Sentinel::Failed(e) => errors.push(format!("sentinel: {e}")),
        }
    }

    let cwd = payload
        .cwd
        .clone()
        .or_else(|| std::env::current_dir().ok().map(|p| p.display().to_string()))
        .unwrap_or_else(|| "(unknown)".into());
    let process = process.ok();
    let block = render(
        &payload,
        &cwd,
        process.as_ref(),
        &launcher_chain(
            std::env::var("CLAUDE_SH_LAUNCHERS").ok().as_deref(),
            process.as_ref().map(|p| p.started),
        ),
        recorded_env(std::env::vars()),
        &settings_sources(Path::new(&cwd)),
        &mut errors,
    );
    let mut stdout = std::io::stdout().lock();
    stdout.write_all(block.as_bytes())?;
    stdout.flush()?;
    Ok(())
}

struct Process {
    pid: u32,
    start_ticks: u64,
    started: SystemTime,
}

/// The Claude Code process this hook runs under. Claude Code exports its own
/// pid to hooks as `CLAUDE_PID`; the start ticks tell it apart from a later
/// process given the same pid, which a container restart makes likely.
fn current_process() -> Result<Process, String> {
    let raw = std::env::var("CLAUDE_PID").map_err(|e| format!("CLAUDE_PID: {e}"))?;
    let pid: u32 = raw
        .parse()
        .map_err(|e| format!("CLAUDE_PID={raw:?}: {e}"))?;
    let start_ticks = crate::procstat::start_ticks(pid).map_err(|e| format!("{e:#}"))?;
    Ok(Process {
        pid,
        start_ticks,
        started: start_time(start_ticks)?,
    })
}

/// Boot time plus the start ticks. `/proc/stat` gives boot time in whole
/// seconds, so the result can be up to a second early, and a launcher modified
/// in the second before its process started can be flagged.
fn start_time(start_ticks: u64) -> Result<SystemTime, String> {
    let stat = fs::read_to_string("/proc/stat").map_err(|e| format!("/proc/stat: {e}"))?;
    let btime: u64 = stat
        .lines()
        .find_map(|l| l.strip_prefix("btime "))
        .ok_or("/proc/stat has no btime line")?
        .trim()
        .parse()
        .map_err(|e| format!("/proc/stat btime: {e}"))?;
    // SAFETY: sysconf reads a system constant and has no preconditions.
    let hz = unsafe { libc::sysconf(libc::_SC_CLK_TCK) };
    if hz <= 0 {
        return Err(format!("sysconf(_SC_CLK_TCK) returned {hz}"));
    }
    Ok(SystemTime::UNIX_EPOCH
        + Duration::from_secs(btime)
        + Duration::from_millis(start_ticks * 1000 / hz as u64))
}

enum Sentinel {
    Claimed,
    AlreadyHeld,
    Failed(std::io::Error),
}

/// `create_new` is the whole mechanism: two hooks racing for the same session
/// resolve in the kernel, and exactly one of them renders.
///
/// Takes the directory rather than reading `HOME` for it, so a test can drive
/// the decision without `set_var` — which is process-global and would race
/// every other test thread, this binary's `paths` tests included.
fn claim_sentinel_in(dir: &Path, name: &str) -> Sentinel {
    if let Err(e) = fs::create_dir_all(dir) {
        return Sentinel::Failed(e);
    }
    match fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(dir.join(name))
    {
        Ok(_) => Sentinel::Claimed,
        Err(e) if e.kind() == ErrorKind::AlreadyExists => Sentinel::AlreadyHeld,
        Err(e) => Sentinel::Failed(e),
    }
}

/// Assembles the block from values already gathered. No environment read
/// happens in here, for the same reason `claim_sentinel_in` takes a path.
fn render(
    payload: &Payload,
    cwd: &str,
    process: Option<&Process>,
    launchers: &[Launcher],
    env: BTreeMap<String, String>,
    settings: &[PathBuf],
    errors: &mut Vec<String>,
) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "<launch-provenance {FORMAT}>");
    let _ = writeln!(out, "session:  {}", payload.session_id);
    let _ = writeln!(
        out,
        "recorded: {} (hook {})",
        local_rfc3339(SystemTime::now()),
        payload.hook_event_name.as_deref().unwrap_or("?")
    );
    match process {
        Some(p) => {
            let _ = writeln!(
                out,
                "process:  pid {}, started {}",
                p.pid,
                local_rfc3339(p.started)
            );
        }
        None => {
            let _ = writeln!(out, "process:  unknown (see errors)");
        }
    }
    let _ = writeln!(out, "cwd:      {cwd}");

    let _ = writeln!(out, "launchers:");
    if launchers.is_empty() {
        // Not a defect: a bare `claude` sets nothing, and that is itself the
        // answer to which configuration ran.
        let _ = writeln!(out, "  (none — CLAUDE_SH_LAUNCHERS unset)");
    }
    for (i, l) in launchers.iter().enumerate() {
        let flag = if l.modified_after_start {
            " (modified after this process started: its text below may not be what ran)"
        } else {
            ""
        };
        let _ = writeln!(out, "  {}. {} {}{flag}", i + 1, l.path.display(), l.revision);
    }

    let _ = writeln!(out, "env:");
    for (name, value) in &env {
        let _ = writeln!(out, "  {name}={value}");
    }

    let _ = writeln!(out, "settings:");
    if settings.is_empty() {
        let _ = writeln!(out, "  (none found)");
    }
    for (i, p) in settings.iter().enumerate() {
        let _ = writeln!(out, "  {}. {}", i + 1, p.display());
    }

    for l in launchers {
        emit_source(&mut out, &l.path, None, errors);
    }
    for p in settings {
        emit_source(&mut out, p, Some(redact_json), errors);
    }

    if !errors.is_empty() {
        let _ = writeln!(out, "errors:");
        for e in errors.iter() {
            let _ = writeln!(out, "  - {e}");
        }
    }
    let _ = writeln!(out, "</launch-provenance {FORMAT}>");
    out
}

fn local_rfc3339(t: SystemTime) -> String {
    chrono::DateTime::<chrono::Local>::from(t).to_rfc3339_opts(chrono::SecondsFormat::Secs, false)
}

struct Launcher {
    path: PathBuf,
    revision: String,
    modified_after_start: bool,
}

/// Each launcher appends its own resolved path to `CLAUDE_SH_LAUNCHERS` before
/// handing off, so the variable is the chain in the order it ran. Nothing else
/// can supply it: every launcher here ends in `exec`, which replaces the shell,
/// leaving no process for a hook to walk back to. The same `exec` keeps the pid,
/// so the process's start time is when its first launcher began, and a
/// launcher whose mtime is later than that changed after it ran. With no start
/// time nothing is flagged, and the `process:` line says why.
fn launcher_chain(raw: Option<&str>, started: Option<SystemTime>) -> Vec<Launcher> {
    let raw = match raw {
        Some(v) => v,
        None => return Vec::new(),
    };
    raw.split(':')
        .filter(|s| !s.is_empty())
        .map(|s| {
            let path = PathBuf::from(s);
            let revision = git_revision(&path);
            // An unreadable launcher gets its own section saying so below.
            let modified_after_start = match (started, fs::metadata(&path).and_then(|m| m.modified())) {
                (Some(start), Ok(mtime)) => mtime > start,
                _ => false,
            };
            Launcher {
                path,
                revision,
                modified_after_start,
            }
        })
        .collect()
}

/// `<short sha> clean|dirty`, where dirty is about this file alone rather than
/// the whole tree: an unrelated edit elsewhere in the checkout does not make the
/// launcher unrecoverable from history, and an edit to the launcher does.
fn git_revision(file: &Path) -> String {
    let dir = match file.parent() {
        Some(d) => d,
        None => return "git:(no parent dir)".into(),
    };
    let head = match git(dir, &["rev-parse", "--short", "HEAD"]) {
        Some(h) => h,
        None => return "git:(not a repository)".into(),
    };
    match git(
        dir,
        &["status", "--porcelain", "--", &file.display().to_string()],
    ) {
        Some(s) if s.is_empty() => format!("git:{head} clean"),
        Some(_) => format!("git:{head} dirty"),
        None => format!("git:{head} (status unavailable)"),
    }
}

fn git(dir: &Path, args: &[&str]) -> Option<String> {
    let out = Command::new("git")
        .arg("-C")
        .arg(dir)
        .args(args)
        .output()
        .ok()?;
    if !out.status.success() {
        return None;
    }
    Some(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

/// Sorted so two sessions' blocks diff against each other line by line.
fn recorded_env<I: Iterator<Item = (String, String)>>(vars: I) -> BTreeMap<String, String> {
    vars.filter(|(name, _)| is_recorded_name(name))
        .map(|(name, value)| {
            let value = if is_secret_name(&name) {
                redacted(&value)
            } else {
                value
            };
            (name, value)
        })
        .collect()
}

fn is_recorded_name(name: &str) -> bool {
    ENV_PREFIXES.iter().any(|p| name.starts_with(p)) || ENV_EXACT.contains(&name)
}

/// The length survives redaction because a credential that changed length
/// between sessions is a configuration change, and one that did not is not.
fn redacted(value: &str) -> String {
    format!("<redacted len={}>", value.len())
}

fn is_secret_name(name: &str) -> bool {
    let last = name.rsplit('_').next().unwrap_or(name).to_ascii_uppercase();
    last == SECRET_WORD_TOKEN || SECRET_WORDS.contains(&last.as_str())
}

/// Every settings file Claude Code could have read that exists: the managed
/// file, the user-scope one under `CLAUDE_CONFIG_DIR`, and the project files of
/// `cwd` and each of its ancestors. Which of them won is a question this block
/// does not answer and does not need to — recording all of them is what makes
/// the answer derivable later, and a path that is present but never read costs
/// one labelled section.
fn settings_sources(cwd: &Path) -> Vec<PathBuf> {
    let mut out: Vec<PathBuf> = Vec::new();
    let mut push = |p: PathBuf| {
        if p.is_file() && !out.contains(&p) {
            out.push(p);
        }
    };

    push(PathBuf::from("/etc/claude-code/managed-settings.json"));

    let config_dir = std::env::var("CLAUDE_CONFIG_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/".into())).join(".claude")
        });
    push(config_dir.join("settings.json"));
    push(config_dir.join("settings.local.json"));

    let mut ancestors: Vec<&Path> = cwd.ancestors().collect();
    ancestors.reverse();
    for dir in ancestors {
        push(dir.join(".claude/settings.json"));
        push(dir.join(".claude/settings.local.json"));
    }
    out
}

/// A labelled verbatim section, optionally passed through a transform that
/// rewrites what must not be recorded. An unreadable or oversized file gets a
/// section saying so rather than being dropped, so a reader never has to decide
/// whether a missing section means absent or unread.
fn emit_source(
    out: &mut String,
    path: &Path,
    transform: Option<fn(&str) -> (String, bool)>,
    errors: &mut Vec<String>,
) {
    let size = match fs::metadata(path) {
        Ok(m) => m.len(),
        Err(e) => {
            errors.push(format!("{}: {e}", path.display()));
            let _ = writeln!(out, "--- source: {} (unreadable: {e}) ---", path.display());
            return;
        }
    };
    if size > SOURCE_BYTE_CAP {
        let _ = writeln!(
            out,
            "--- source: {} (skipped: {size} bytes over the {SOURCE_BYTE_CAP}-byte cap) ---",
            path.display()
        );
        return;
    }
    let text = match fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => {
            errors.push(format!("{}: {e}", path.display()));
            let _ = writeln!(out, "--- source: {} (unreadable: {e}) ---", path.display());
            return;
        }
    };
    let (body, note) = match transform {
        Some(f) => {
            let (body, changed) = f(&text);
            (body, if changed { " (secret-valued keys redacted)" } else { "" })
        }
        None => (text, ""),
    };
    let _ = writeln!(out, "--- source: {}{note} ---", path.display());
    out.push_str(&body);
    if !body.ends_with('\n') {
        out.push('\n');
    }
}

/// Replaces the string value of every credential-named key, at any depth, and
/// reports whether anything was replaced. A file that does not parse as JSON is
/// returned unchanged: settings files here are hand-edited and a broken one is
/// itself worth recording verbatim.
fn redact_json(text: &str) -> (String, bool) {
    let mut value: serde_json::Value = match serde_json::from_str(text) {
        Ok(v) => v,
        Err(_) => return (text.to_string(), false),
    };
    let mut changed = false;
    walk_redact(&mut value, &mut changed);
    match serde_json::to_string_pretty(&value) {
        Ok(s) => (s, changed),
        Err(_) => (text.to_string(), false),
    }
}

fn walk_redact(value: &mut serde_json::Value, changed: &mut bool) {
    match value {
        serde_json::Value::Object(map) => {
            for (key, v) in map.iter_mut() {
                if is_secret_name(key) {
                    if let serde_json::Value::String(s) = v {
                        *s = redacted(s);
                        *changed = true;
                        continue;
                    }
                }
                walk_redact(v, changed);
            }
        }
        serde_json::Value::Array(items) => {
            for v in items.iter_mut() {
                walk_redact(v, changed);
            }
        }
        _ => {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn payload() -> Payload {
        Payload {
            session_id: "sid-1".into(),
            agent_id: None,
            hook_event_name: Some("PreToolUse".into()),
            cwd: Some("/nonexistent-cwd-for-test".into()),
        }
    }

    #[test]
    fn a_window_size_ending_in_tokens_is_not_a_credential() {
        assert!(!is_secret_name("CLAUDE_CODE_MAX_CONTEXT_TOKENS"));
        assert!(!is_secret_name("MAX_THINKING_TOKENS"));
    }

    #[test]
    fn credential_named_variables_are_recognized() {
        for name in [
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "CLAUDE_CODE_MESSAGING_TOKEN",
            "ZAI_API_KEY",
            "KIMI_API_KEY",
        ] {
            assert!(is_secret_name(name), "{name} must be treated as a credential");
        }
    }

    #[test]
    fn a_recorded_credential_keeps_its_length_and_loses_its_value() {
        let env = recorded_env(
            [
                ("ANTHROPIC_AUTH_TOKEN".to_string(), "sk-super-secret".to_string()),
                (
                    "CLAUDE_CODE_TOTAL_TOKENS_REMINDER".to_string(),
                    "padded-countdown".to_string(),
                ),
            ]
            .into_iter(),
        );
        assert_eq!(env["ANTHROPIC_AUTH_TOKEN"], "<redacted len=15>");
        assert!(!env["ANTHROPIC_AUTH_TOKEN"].contains("secret"));
        assert_eq!(env["CLAUDE_CODE_TOTAL_TOKENS_REMINDER"], "padded-countdown");
    }

    #[test]
    fn only_configuration_variables_are_recorded() {
        let env = recorded_env(
            [
                ("CLAUDE_CODE_TMPDIR".to_string(), "/t".to_string()),
                ("ANTHROPIC_BASE_URL".to_string(), "https://x".to_string()),
                ("IS_SANDBOX".to_string(), "1".to_string()),
                ("HOME".to_string(), "/root".to_string()),
                ("AGENT_TOOLS_PARENT_DIR".to_string(), "/x".to_string()),
            ]
            .into_iter(),
        );
        assert!(env.contains_key("CLAUDE_CODE_TMPDIR"));
        assert!(env.contains_key("ANTHROPIC_BASE_URL"));
        assert!(env.contains_key("IS_SANDBOX"));
        assert!(!env.contains_key("HOME"));
        assert!(!env.contains_key("AGENT_TOOLS_PARENT_DIR"));
    }

    /// The launchers' own bookkeeping reaches the record through the `CLAUDE`
    /// prefix and is named nowhere in the recording code, so narrowing that
    /// prefix would silently stop recording which configuration a session ran
    /// and whether the launcher drew it. `scripts/claude.sh` is the writer.
    #[test]
    fn launcher_bookkeeping_reaches_the_record() {
        for name in [
            "CLAUDE_SH_LAUNCHERS",
            "CLAUDE_SH_TOKENS_REMINDER_SOURCE",
            "CLAUDE_SH_VERSION",
        ] {
            assert!(is_recorded_name(name), "{name} must reach the record");
            assert!(!is_secret_name(name), "{name} must keep its value");
        }
    }

    #[test]
    fn json_redaction_reaches_a_nested_env_block() {
        let (out, changed) = redact_json(
            r#"{"env":{"ANTHROPIC_AUTH_TOKEN":"sk-abc","CLAUDE_CODE_FORK_SUBAGENT":"0"},
                "autoCompactWindow":400000}"#,
        );
        assert!(changed);
        assert!(!out.contains("sk-abc"));
        assert!(out.contains("<redacted len=6>"));
        assert!(out.contains("\"CLAUDE_CODE_FORK_SUBAGENT\": \"0\""));
        assert!(out.contains("400000"));
    }

    #[test]
    fn settings_without_credentials_are_emitted_unmarked() {
        let (out, changed) = redact_json(r#"{"model":"opus"}"#);
        assert!(!changed);
        assert!(out.contains("opus"));
    }

    #[test]
    fn unparseable_settings_are_kept_verbatim() {
        let (out, changed) = redact_json("{not json");
        assert!(!changed);
        assert_eq!(out, "{not json");
    }

    fn rendered(launchers: &[Launcher], env: BTreeMap<String, String>) -> String {
        let mut errors = Vec::new();
        render(
            &payload(),
            "/nonexistent-cwd-for-test",
            None,
            launchers,
            env,
            &[],
            &mut errors,
        )
    }

    /// The reader greps for the opening tag; a block that cannot be delimited
    /// cannot be extracted from a transcript.
    #[test]
    fn the_block_is_delimited_and_names_its_format() {
        let block = rendered(&[], BTreeMap::new());
        assert!(block.starts_with(&format!("<launch-provenance {FORMAT}>\n")));
        assert!(block.ends_with(&format!("</launch-provenance {FORMAT}>\n")));
        assert!(block.contains("session:  sid-1"));
        assert!(block.contains("(hook PreToolUse)"));
    }

    /// An unset chain is the ordinary state of a session started by bare
    /// `claude`, and has to read as an answer rather than as a missing field.
    #[test]
    fn an_absent_launcher_chain_is_stated_rather_than_omitted() {
        assert!(launcher_chain(None, None).is_empty());
        assert!(rendered(&[], BTreeMap::new()).contains("(none — CLAUDE_SH_LAUNCHERS unset)"));
    }

    /// The chain is what separates a `kimi.sh` session from a plain one, and
    /// the order is which script ran first.
    #[test]
    fn the_launcher_chain_keeps_its_order() {
        let chain = launcher_chain(Some("/repo/scripts/kimi.sh:/repo/scripts/claude.sh"), None);
        assert_eq!(chain.len(), 2);
        assert_eq!(chain[0].path, PathBuf::from("/repo/scripts/kimi.sh"));
        assert_eq!(chain[1].path, PathBuf::from("/repo/scripts/claude.sh"));
        let block = rendered(&chain, BTreeMap::new());
        assert!(block.contains("1. /repo/scripts/kimi.sh"));
        assert!(block.contains("2. /repo/scripts/claude.sh"));
    }

    /// The arm the session drew is the one value the whole record exists for.
    #[test]
    fn the_env_section_carries_the_drawn_arm() {
        let env = recorded_env(
            [(
                "CLAUDE_CODE_TOTAL_TOKENS_REMINDER".to_string(),
                "padded-countdown".to_string(),
            )]
            .into_iter(),
        );
        assert!(rendered(&[], env)
            .contains("  CLAUDE_CODE_TOTAL_TOKENS_REMINDER=padded-countdown\n"));
    }

    #[test]
    fn a_source_file_over_the_cap_is_named_rather_than_emitted() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("big.json");
        fs::write(&path, "x".repeat(SOURCE_BYTE_CAP as usize + 1)).unwrap();
        let mut out = String::new();
        let mut errors = Vec::new();
        emit_source(&mut out, &path, None, &mut errors);
        assert!(out.contains("skipped:"));
        assert!(!out.contains("xxxx"));
        assert!(errors.is_empty());
    }

    #[test]
    fn an_unreadable_source_reports_itself_in_both_places() {
        let mut out = String::new();
        let mut errors = Vec::new();
        emit_source(
            &mut out,
            Path::new("/nonexistent/settings.json"),
            Some(redact_json),
            &mut errors,
        );
        assert!(out.contains("unreadable:"));
        assert_eq!(errors.len(), 1);
    }

    #[test]
    fn a_claimed_sentinel_turns_every_later_invocation_into_a_no_op() {
        let tmp = tempfile::tempdir().unwrap();
        let dir = tmp.path().join("sentinel-test-session");
        assert!(matches!(claim_sentinel_in(&dir, SENTINEL), Sentinel::Claimed));
        assert!(matches!(claim_sentinel_in(&dir, SENTINEL), Sentinel::AlreadyHeld));
        assert!(matches!(claim_sentinel_in(&dir, SENTINEL), Sentinel::AlreadyHeld));
    }

    /// Settings sources are addressed by path; a `cwd` deep in a checkout must
    /// reach the project file above it, not only its own directory.
    #[test]
    fn project_settings_above_cwd_are_found() {
        let tmp = tempfile::tempdir().unwrap();
        let project = tmp.path().join("repo");
        let deep = project.join("a/b/c");
        fs::create_dir_all(deep.join(".claude")).unwrap();
        fs::create_dir_all(project.join(".claude")).unwrap();
        fs::write(project.join(".claude/settings.json"), "{}").unwrap();
        let found = settings_sources(&deep);
        assert!(found.contains(&project.join(".claude/settings.json")));
    }
}
