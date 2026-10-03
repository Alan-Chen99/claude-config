# mcp__claude_ai_Gmail__unmark_thread_spam

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Unmarks an entire thread as Spam in the authenticated user's Gmail account.

If unsure of the thread ID, use the `search_threads` tool first.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "threadId": {
      "description": "Required. The ID of the thread to unmark as Spam.",
      "type": "string"
    }
  },
  "required": [
    "threadId"
  ],
  "description": "Request message for UnmarkThreadSpam RPC."
}
```
