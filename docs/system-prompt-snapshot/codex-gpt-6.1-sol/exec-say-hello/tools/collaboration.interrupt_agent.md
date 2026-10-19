# collaboration.interrupt_agent

Interrupt an agent's current turn, if any, and return its previous status. The agent remains available for messages and follow-up tasks.

```json
{
  "type": "function",
  "name": "interrupt_agent",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "target": {
        "type": "string",
        "description": "Agent id or canonical task name to interrupt (from spawn_agent)."
      }
    },
    "required": [
      "target"
    ],
    "additionalProperties": false
  }
}
```
