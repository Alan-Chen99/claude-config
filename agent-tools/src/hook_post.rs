use anyhow::{Context, Result};
use std::fs;
use std::io::Read;
use std::path::Path;

use crate::hook_input;
use crate::meta::ChildMeta;
use crate::paths;

pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf).context("read stdin")?;

    let input = match hook_input::parse_post(&buf) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("agent-tools hook-post: parse error: {e:#}");
            return Ok(());
        }
    };

    if input.tool_name != "Bash" && input.tool_name != "Monitor" {
        return Ok(());
    }

    let parent_dir = paths::parent_dir_for(
        &input.session_id,
        input.agent_id.as_deref(),
        &input.tool_use_id,
    )?;

    let captures = list_captures(&parent_dir);
    let bg = bg_notice(&input);

    if captures.is_empty() && bg.is_none() {
        return Ok(());
    }

    let mut parts: Vec<String> = Vec::new();
    if !captures.is_empty() {
        let listing: Vec<String> = captures.iter().map(format_capture).collect();
        parts.push(format!(
            "[agent-tools] captures from this Bash call: {}",
            listing.join("; "),
        ));
    }
    if let Some(b) = bg {
        parts.push(b);
    }

    let out = serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": parts.join(" ")
        }
    });
    println!("{}", serde_json::to_string(&out)?);
    Ok(())
}

struct Capture {
    dir: std::path::PathBuf,
    desc: Option<String>,
}

fn list_captures(parent_dir: &Path) -> Vec<Capture> {
    if !parent_dir.is_dir() {
        return Vec::new();
    }
    let rd = match fs::read_dir(parent_dir) {
        Ok(r) => r,
        Err(_) => return Vec::new(),
    };
    let mut out = Vec::new();
    for entry in rd.flatten() {
        let p = entry.path();
        if !p.is_dir() {
            continue;
        }
        let desc = fs::read_to_string(p.join("meta.json"))
            .ok()
            .and_then(|s| serde_json::from_str::<ChildMeta>(&s).ok())
            .and_then(|c| c.desc);
        out.push(Capture { dir: p, desc });
    }
    out.sort_by(|a, b| a.dir.cmp(&b.dir));
    out
}

fn format_capture(c: &Capture) -> String {
    match &c.desc {
        Some(d) => format!("{} → {}/{{stdout,stderr}}", d, c.dir.display()),
        None => format!("{}/{{stdout,stderr}}", c.dir.display()),
    }
}

fn bg_notice(input: &hook_input::PostToolUseInput) -> Option<String> {
    let bg_task_id = input.tool_response.get("backgroundTaskId").and_then(|v| v.as_str())?;
    let auto = input.tool_response.get("assistantAutoBackgrounded").and_then(|v| v.as_bool()).unwrap_or(false);
    let user = input.tool_response.get("backgroundedByUser").and_then(|v| v.as_bool()).unwrap_or(false);
    let cause = if auto {
        "assistant-mode auto-background (KAIROS)".to_string()
    } else if user {
        "user manually backgrounded (Ctrl+B)".to_string()
    } else {
        let limit = input.tool_input.timeout.unwrap_or(120_000);
        format!("timeout ({limit}ms limit hit)")
    };
    Some(format!(
        "BACKGROUNDED: Command was involuntarily backgrounded. Cause: {cause}. \
         Process is still running (task_id: {bg_task_id}). \
         To kill it: use TaskStop tool with task_id {bg_task_id}."
    ))
}
