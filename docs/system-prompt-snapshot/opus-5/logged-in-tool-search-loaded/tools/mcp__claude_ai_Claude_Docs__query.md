# mcp__claude_ai_Claude_Docs__query

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

List a tab's or a doc's comment history (threads, replies, resolves).

## input_schema

```json
{
  "type": "object",
  "properties": {
    "container": {
      "type": "object",
      "properties": {
        "kind": {
          "type": "string"
        },
        "id": {
          "type": "string"
        },
        "version": {
          "type": "string"
        }
      },
      "required": [
        "kind",
        "id"
      ]
    },
    "object": {
      "type": "string",
      "enum": [
        "utterance"
      ]
    },
    "payload": {
      "anyOf": [
        {
          "type": "object"
        },
        {
          "type": "string"
        }
      ]
    }
  }
}
```
