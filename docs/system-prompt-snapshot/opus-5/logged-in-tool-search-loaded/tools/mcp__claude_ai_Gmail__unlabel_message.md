# mcp__claude_ai_Gmail__unlabel_message

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Removes one or more labels from a specific message in the authenticated user's Gmail account. To find the message ID, use the `get_thread` tool. If unsure of a user label's ID, use the `list_labels` tool first to discover available labels and their IDs.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "labelIds": {
      "description": "Required. The IDs of the labels to remove. Can be a system label ID (e.g., `INBOX`, `TRASH`, `SPAM`, `STARRED`, `UNREAD`, `IMPORTANT`) or a user-defined label ID. The tool accepts `label_ids` and not label names. Use the `list_labels` tool to get the corresponding label id to a display name for user-defined labels.",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "messageId": {
      "description": "Required. The ID of the message to remove the labels from.",
      "type": "string"
    }
  },
  "required": [
    "messageId",
    "labelIds"
  ],
  "description": "Request message for UnlabelMessage RPC."
}
```
