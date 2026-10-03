# mcp__claude_ai_Gmail__delete_draft

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Deletes a draft email in the authenticated user's Gmail account using its draft ID.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "draftId": {
      "description": "Required. The unique identifier of the draft to delete.",
      "type": "string"
    }
  },
  "required": [
    "draftId"
  ],
  "description": "Request message for DeleteDraft RPC."
}
```
