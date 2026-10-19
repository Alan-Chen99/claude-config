# collaboration.followup_task

Send a follow-up task to an existing non-root target agent and trigger a turn if it is idle. If the target is already running, deliver the task promptly at message boundaries while sampling, or after the pending tool call completes.

```json
{
  "type": "function",
  "name": "followup_task",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "Message text to send to the target agent.",
        "encrypted": true
      },
      "target": {
        "type": "string",
        "description": "Agent id or canonical task name to send a follow-up task to (from spawn_agent)."
      }
    },
    "required": [
      "target",
      "message"
    ],
    "additionalProperties": false
  }
}
```
