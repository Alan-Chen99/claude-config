use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct PreToolUseInput {
    pub session_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    pub cwd: String,
    pub tool_name: String,
    pub tool_input: ToolInput,
    pub tool_use_id: String,
}

#[derive(Debug, Deserialize)]
pub struct PostToolUseInput {
    pub session_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    pub tool_name: String,
    pub tool_input: ToolInput,
    pub tool_use_id: String,
    #[serde(default)]
    pub tool_response: serde_json::Value,
}

#[derive(Debug, Deserialize)]
pub struct ToolInput {
    pub command: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub timeout: Option<u64>,
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
        assert_eq!(p.tool_input.command, "echo hi");
        assert_eq!(p.tool_input.description.as_deref(), Some("say hi"));
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
        assert!(p.tool_input.description.is_none());
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
        assert_eq!(p.tool_input.timeout, Some(5000));
    }
}
