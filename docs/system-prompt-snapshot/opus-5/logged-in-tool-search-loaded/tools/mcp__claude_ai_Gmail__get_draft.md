# mcp__claude_ai_Gmail__get_draft

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Retrieves a specific draft email from the authenticated user's Gmail account by ID, including its `viewUrl` for viewing and editing in the Gmail Web UI.

The optional `messageFormat` parameter controls the format of the draft returned. Use `MINIMAL` to return snippet and key headers, `METADATA_ONLY` to exclude snippet, subject, and body, `FULL_CONTENT` for the complete draft, or `RAW` for the raw MIME message content.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "draftId": {
      "description": "Required. The unique identifier of the draft to fetch.",
      "type": "string"
    },
    "messageFormat": {
      "description": "Optional. Specifies the format of the draft returned. Defaults to `FULL_CONTENT`.",
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
    }
  },
  "required": [
    "draftId"
  ],
  "description": "Request message for GetDraft RPC."
}
```
