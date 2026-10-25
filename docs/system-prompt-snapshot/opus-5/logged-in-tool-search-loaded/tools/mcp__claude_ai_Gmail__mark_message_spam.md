# mcp__claude_ai_Gmail__mark_message_spam

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Marks a specific message as Spam in the authenticated user's Gmail account.

To find the message ID, use the `get_thread` tool.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "messageId": {
      "description": "Required. The ID of the message to mark as Spam.",
      "type": "string"
    }
  },
  "required": [
    "messageId"
  ],
  "description": "Request message for MarkMessageSpam RPC."
}
```
