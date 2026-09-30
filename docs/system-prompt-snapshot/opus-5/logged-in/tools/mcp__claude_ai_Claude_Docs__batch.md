# mcp__claude_ai_Claude_Docs__batch

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Create a doc, or apply several operations to one doc atomically.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "batch": {
      "type": "array"
    },
    "container": {
      "type": "object",
      "properties": {
        "kind": {
          "type": "string"
        },
        "id": {
          "type": "string"
        },
        "create": {
          "type": "object"
        }
      },
      "required": [
        "kind"
      ]
    },
    "verbose": {
      "type": "boolean"
    },
    "opId": {
      "type": "string"
    }
  }
}
```
