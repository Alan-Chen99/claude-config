# mcp__claude_ai_Gmail__label_message

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Adds one or more labels to a specific message in the authenticated user's Gmail account.

To find the message ID, use the `get_thread` tool. If unsure of a user label's ID, use the `list_labels` tool first to discover available labels and their IDs.
To move a message to a different inbox category tab, add the target `CATEGORY_*` label (e.g. `CATEGORY_PERSONAL` for Primary); Gmail automatically removes the previous category.
To move a specific message to Trash or mark it as Spam, please use the `trash_message` or `mark_message_spam` tool instead.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "labelIds": {
      "description": "Required. The IDs of the labels to add. Can be a system label ID (e.g., `INBOX`, `STARRED`, `UNREAD`, `IMPORTANT`) or a user-defined label ID. The tool accepts `label_ids` and not label names. Use the `list_labels` tool to get the corresponding label id to a display name for user-defined labels.",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "messageId": {
      "description": "Required. The ID of the message to add the labels to.",
      "type": "string"
    }
  },
  "required": [
    "messageId",
    "labelIds"
  ],
  "description": "Request message for LabelMessage RPC."
}
```
