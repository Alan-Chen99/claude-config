# mcp__claude_ai_Gmail__untrash_message

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Removes a specific message from the Trash in the authenticated user's Gmail account.

To find the message ID, use tools like `search_threads` or `get_thread`.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "messageId": {
      "description": "Required. The ID of the message to remove from Trash.",
      "type": "string"
    }
  },
  "required": [
    "messageId"
  ],
  "description": "Request message for UntrashMessage RPC."
}
```
