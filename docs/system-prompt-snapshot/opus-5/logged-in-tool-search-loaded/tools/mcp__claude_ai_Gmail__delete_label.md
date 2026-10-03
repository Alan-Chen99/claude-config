# mcp__claude_ai_Gmail__delete_label

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Deletes a label in the authenticated user's Gmail account.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "labelId": {
      "description": "Required. The ID of the label to delete.",
      "type": "string"
    }
  },
  "required": [
    "labelId"
  ],
  "description": "Request message for DeleteLabel RPC."
}
```
