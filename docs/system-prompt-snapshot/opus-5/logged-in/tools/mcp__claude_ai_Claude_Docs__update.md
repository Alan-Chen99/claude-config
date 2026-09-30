# mcp__claude_ai_Claude_Docs__update

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Edit a tab's contents, rename a doc or tab, or change a stored value.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "ref": {
      "type": "object",
      "properties": {
        "object": {
          "type": "string",
          "enum": [
            "project",
            "file",
            "node",
            "utterance",
            "enum"
          ]
        },
        "id": {
          "type": "string"
        }
      },
      "required": [
        "object",
        "id"
      ]
    },
    "engine": {
      "type": "string"
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
        "version": {
          "type": "string"
        }
      },
      "required": [
        "kind",
        "id"
      ]
    },
    "verbose": {
      "type": "boolean"
    },
    "opId": {
      "type": "string"
    },
    "answering": {
      "type": "string",
      "maxLength": 64
    }
  },
  "required": [
    "ref",
    "payload"
  ]
}
```
