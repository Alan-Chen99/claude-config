# collaboration.wait_agent

Wait for a mailbox update from any live agent, including queued messages and final-status notifications. The wait also ends early when new user input is steered into the active turn. Does not return the content; returns either a summary of which agents have updates (if any), an interruption summary for steered input, or a timeout summary if no activity arrives before the deadline.

```json
{
  "type": "function",
  "name": "wait_agent",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "timeout_ms": {
        "type": "number",
        "description": "Timeout in milliseconds. Defaults to 30000, min 10000, max 3600000."
      }
    },
    "additionalProperties": false
  }
}
```
