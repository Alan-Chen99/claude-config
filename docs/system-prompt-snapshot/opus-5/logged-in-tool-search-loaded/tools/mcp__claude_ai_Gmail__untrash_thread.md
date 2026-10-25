# mcp__claude_ai_Gmail__untrash_thread

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Removes an entire thread from the Trash in the authenticated user's Gmail account.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "threadId": {
      "description": "Required. The ID of the thread to remove from Trash.",
      "type": "string"
    }
  },
  "required": [
    "threadId"
  ],
  "description": "Request message for UntrashThread RPC."
}
```
