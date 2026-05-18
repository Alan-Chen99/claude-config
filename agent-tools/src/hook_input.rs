use serde::Deserialize;

/// PreToolUse payload. `tool_input` is kept as a raw `serde_json::Value` so the
/// pre-hook can pass it through to `updatedInput` unchanged except for fields
/// it intentionally rewrites — Claude Code uses `updatedInput` as a full
/// replacement (queryHelpers.ts), so anything we don't echo back is silently
/// dropped from the executed tool call.
#[derive(Debug, Deserialize)]
pub struct PreToolUseInput {
    pub session_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    pub cwd: String,
    pub tool_name: String,
    pub tool_input: serde_json::Value,
    pub tool_use_id: String,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub struct PostToolUseInput {
    pub session_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    pub tool_name: String,
    pub tool_input: serde_json::Value,
    pub tool_use_id: String,
    #[serde(default)]
    pub tool_response: serde_json::Value,
}

pub fn parse_pre(s: &str) -> anyhow::Result<PreToolUseInput> {
    Ok(serde_json::from_str(s)?)
}

pub fn parse_post(s: &str) -> anyhow::Result<PostToolUseInput> {
    Ok(serde_json::from_str(s)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_main_thread_pre() {
        let json = r#"{
            "session_id": "sid-1",
            "cwd": "/tmp",
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi", "description": "say hi"},
            "tool_use_id": "tuid-1"
        }"#;
        let p = parse_pre(json).unwrap();
        assert_eq!(p.session_id, "sid-1");
        assert!(p.agent_id.is_none());
        assert_eq!(p.tool_input["command"].as_str(), Some("echo hi"));
        assert_eq!(p.tool_input["description"].as_str(), Some("say hi"));
    }

    #[test]
    fn parses_subagent_pre() {
        let json = r#"{
            "session_id": "sid-1",
            "agent_id": "agent-abc",
            "cwd": "/tmp",
            "tool_name": "Monitor",
            "tool_input": {"command": "tail -f log"},
            "tool_use_id": "tuid-2"
        }"#;
        let p = parse_pre(json).unwrap();
        assert_eq!(p.agent_id.as_deref(), Some("agent-abc"));
        assert_eq!(p.tool_name, "Monitor");
        assert!(p.tool_input.get("description").is_none());
    }

    #[test]
    fn parses_post_with_backgrounding() {
        let json = r#"{
            "session_id": "sid-1",
            "tool_name": "Bash",
            "tool_input": {"command": "sleep 9999", "timeout": 5000},
            "tool_use_id": "tuid-3",
            "tool_response": {"backgroundTaskId": "bt-7"}
        }"#;
        let p = parse_post(json).unwrap();
        assert_eq!(p.tool_response["backgroundTaskId"], "bt-7");
        assert_eq!(p.tool_input["timeout"].as_u64(), Some(5000));
    }

    #[test]
    fn preserves_unknown_fields_in_pre_tool_input() {
        // Bash tool gains new fields over time (e.g. dangerouslyDisableSandbox);
        // raw Value parsing guarantees unknown keys survive intact.
        let json = r#"{
            "session_id": "sid-1",
            "cwd": "/tmp",
            "tool_name": "Bash",
            "tool_input": {"command": "x", "future_flag": 42, "nested": {"a": 1}},
            "tool_use_id": "tuid-x"
        }"#;
        let p = parse_pre(json).unwrap();
        assert_eq!(p.tool_input["future_flag"].as_u64(), Some(42));
        assert_eq!(p.tool_input["nested"]["a"].as_u64(), Some(1));
    }
}
