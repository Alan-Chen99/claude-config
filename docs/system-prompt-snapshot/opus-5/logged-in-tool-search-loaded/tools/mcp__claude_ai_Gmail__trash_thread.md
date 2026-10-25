# mcp__claude_ai_Gmail__trash_thread

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Moves an entire thread to the Trash (soft delete) in the authenticated user's Gmail account. This operation affects all messages currently in the thread.

This is the default tool (along with `trash_message`) when a user asks to 'delete', 'remove', or 'get rid of' an email or thread without explicitly requesting permanent, irreversible deletion. Use `trash_thread` when trashing a thread, even if it currently contains only 1 message. Trashing at the thread level ensures all current messages in the thread are moved to Trash.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "threadId": {
      "description": "Required. The ID of the thread to move to Trash.",
      "type": "string"
    }
  },
  "required": [
    "threadId"
  ],
  "description": "Request message for TrashThread RPC."
}
```
