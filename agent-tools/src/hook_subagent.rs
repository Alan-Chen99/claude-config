use anyhow::{Context, Result};
use std::io::{Read, Write};

/// The categories a subagent is asked to report, each pinned to
/// `conventions/agent-responses.md` by `scripts/check-prompt-coupling.sh`. The
/// glosses are shorter than that file's, because this text is spent once per
/// subagent spawn and the file is there for an agent that wants the long form.
const CATEGORIES: [&str; 8] = [
    // PROMPT-COUPLED
    "manual action needed: something only the caller or user can do",
    // PROMPT-COUPLED
    "suspected user mistake: the brief, the files or an assumption looks wrong",
    // PROMPT-COUPLED
    "hidden challenge: a non-obvious problem you had to solve",
    // PROMPT-COUPLED
    "corrected mistake: an error you made and later fixed",
    // PROMPT-COUPLED
    "instruction issue: an instruction that conflicts, is missing, or misleads",
    // PROMPT-COUPLED
    "tool issue: a tool that errored, misled you, or forced a workaround",
    // PROMPT-COUPLED
    "context waste: what you read that was irrelevant or already known",
    // PROMPT-COUPLED
    "unexpected change: anything you changed beyond what was asked",
];

/// The closing sentence reconciles the ask with the definitions in `agents/`
/// that permit nothing outside their own structure; each of those carries a
/// notes slot for it.
// PROMPT-COUPLED
const ASK: &str = "End your report with a `## Required notes` block. Bullet only what \
applies, and write \"none\" when nothing does:";

const CLOSING: &str = "Your caller sees your report and nothing else of your context, so an \
item you leave out is lost. Where your instructions fix an output format that permits nothing \
else, use the notes slot that format provides.";

fn additional_context() -> String {
    let bullets: Vec<String> = CATEGORIES.iter().map(|c| format!("- {c}")).collect();
    format!("{ASK}\n\n{}\n\n{CLOSING}", bullets.join("\n"))
}

/// SubagentStart hook. The block is the same for every agent type, so the
/// payload is drained and not parsed: no field's value could change the answer,
/// and a shape change upstream therefore cannot break this.
///
/// Claude Code starts the subagent anyway when this hook fails — measured on
/// 2.1.269, a hook exiting 1 left the spawn untouched and the agent ran without
/// the block. A failure here costs a report its notes, never a subagent.
pub fn run() -> Result<()> {
    let mut buf = String::new();
    std::io::stdin().read_to_string(&mut buf)?;
    let mut stdout = std::io::stdout().lock();
    writeln!(
        stdout,
        "{}",
        serde_json::json!({
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": additional_context()
            }
        })
    )
    .context("write hook output")?;
    stdout.flush().context("flush hook output")?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rendered() -> serde_json::Value {
        serde_json::from_str(
            &serde_json::json!({
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStart",
                    "additionalContext": additional_context()
                }
            })
            .to_string(),
        )
        .unwrap()
    }

    /// Claude Code rejects the whole output when `hookEventName` names another
    /// event, and the subagent then starts with no block and no error.
    #[test]
    fn names_the_event_it_answers() {
        assert_eq!(
            rendered()["hookSpecificOutput"]["hookEventName"].as_str(),
            Some("SubagentStart")
        );
    }

    /// The ask is markdown inside a JSON string; a backtick or quote that broke
    /// the encoding would reach the subagent mangled.
    #[test]
    fn survives_json_encoding() {
        assert_eq!(
            rendered()["hookSpecificOutput"]["additionalContext"].as_str(),
            Some(additional_context().as_str())
        );
    }

    #[test]
    fn every_category_reaches_the_subagent() {
        let ctx = additional_context();
        for category in CATEGORIES {
            assert!(ctx.contains(category), "{category} is missing from the ask");
        }
        assert_eq!(ctx.matches("\n- ").count(), CATEGORIES.len());
    }

    /// The block's heading is what the parent's prompt tells it to fold in, so
    /// the subagent has to be asked for that exact heading.
    #[test]
    fn asks_for_the_heading_the_parent_looks_for() {
        assert!(additional_context().contains("## Required notes"));
    }

    /// Spent once per subagent spawn. `doc-budget.toml` prices the `.md`
    /// tree; this block is not `.md`, so it is pinned here -- in characters,
    /// since the Rust suite has no tokenizer. 856 when pinned.
    #[test]
    fn the_ask_stays_inside_its_size_budget() {
        assert!(additional_context().chars().count() <= 1000);
    }
}
