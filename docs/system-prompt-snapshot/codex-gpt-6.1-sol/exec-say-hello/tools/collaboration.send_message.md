# collaboration.send_message

Send a message to an existing agent. The message will be delivered promptly. Does not trigger a new turn.

```json
{
  "type": "function",
  "name": "send_message",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "Message text to queue on the target agent.",
        "encrypted": true
      },
      "target": {
        "type": "string",
        "description": "Relative or canonical task name to message (from spawn_agent)."
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
