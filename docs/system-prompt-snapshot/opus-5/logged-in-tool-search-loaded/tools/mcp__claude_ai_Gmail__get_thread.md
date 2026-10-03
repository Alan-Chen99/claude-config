# mcp__claude_ai_Gmail__get_thread

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Retrieves a specific email thread from the authenticated user's Gmail account, including its `viewUrl` and a list of its messages (each with their own `viewUrl`).

Note: This tool does not support retrieving drafts. Any draft messages within a thread are omitted. To view drafts, use the `list_drafts` tool instead.

The optional `messageFormat` parameter controls the format of the messages returned. By default (or with `FULL_CONTENT`), it returns the full content of messages. We recommend using `PLAIN_TEXT`, which returns the plain text body without the HTML body. Use `MINIMAL` to include only subject and snippet (excluding body). Use `METADATA_ONLY` to include only basic metadata (message ID, thread ID, viewUrl, labels, timestamp, and size estimate).


## input_schema

```json
{
  "type": "object",
  "properties": {
    "messageFormat": {
      "description": "Optional. Specifies the format of the messages returned within the thread. Defaults to `FULL_CONTENT`. We recommend using `PLAIN_TEXT` to prevent context exhaustion. Note: `MINIMAL` format returns `id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`. `METADATA_ONLY` format returns `id`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`. `FULL_CONTENT` returns `id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `attachment_ids`, `plaintext_body`, `html_body`, `attachments`. `PLAIN_TEXT` returns `id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `attachment_ids`, `plaintext_body`, `attachments` (without `html_body`). `RAW` format is not supported here.",
      "enum": [
        "MESSAGE_FORMAT_UNSPECIFIED",
        "MINIMAL",
        "FULL_CONTENT",
        "METADATA_ONLY",
        "PLAIN_TEXT",
        "RAW"
      ],
      "type": "string",
      "x-google-enum-descriptions": [
        "Defaults to FULL_CONTENT.",
        "Returns `id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `view_url` (if applicable). Omits `plaintext_body`, `html_body`, `attachment_ids`, `attachments`.",
        "Returns all message fields (`id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `attachment_ids`, `plaintext_body`, `html_body`, `attachments`, `view_url`) if applicable.",
        "Returns `id`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `view_url` (if applicable). Omits `subject`, `snippet`, `plaintext_body`, `html_body`, `attachment_ids`, `attachments`.",
        "Returns all information in `MINIMAL` plus `plaintext_body`, `attachment_ids`, and `attachments` (if applicable). If plain text body is not available, converts the HTML body to plain text/markdown. Omits `html_body`.",
        "Returns the raw MIME message content."
      ]
    },
    "threadId": {
      "description": "Required. The unique identifier of the thread to fetch.",
      "type": "string"
    }
  },
  "required": [
    "threadId"
  ],
  "description": "Request message for GetThread RPC."
}
```
