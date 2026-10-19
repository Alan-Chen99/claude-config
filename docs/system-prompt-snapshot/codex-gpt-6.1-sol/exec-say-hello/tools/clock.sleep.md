# clock.sleep

Pause execution for a specified duration. The sleep ends early when new input arrives for the active turn. Returns the elapsed wall-clock time.

```json
{
  "type": "function",
  "name": "sleep",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "duration_ms": {
        "type": "number",
        "description": "How long to sleep in milliseconds. Must be between 1 and 43200000."
      }
    },
    "required": [
      "duration_ms"
    ],
    "additionalProperties": false
  }
}
```
