# collaboration.list_agents

List live agents in the current root thread tree. Optionally filter by task-path prefix.

```json
{
  "type": "function",
  "name": "list_agents",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "path_prefix": {
        "type": "string",
        "description": "Task-path prefix filter without a trailing slash. Omit to list all live agents."
      }
    },
    "additionalProperties": false
  }
}
```
