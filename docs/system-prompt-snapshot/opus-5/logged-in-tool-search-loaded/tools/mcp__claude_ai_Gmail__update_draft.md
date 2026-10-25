# mcp__claude_ai_Gmail__update_draft

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Updates an existing draft email in the authenticated user's Gmail account. This operation supports merge semantics: fields provided in the request (non-empty) will overwrite the corresponding fields in the draft, while omitted (or empty) fields will preserve their existing values. Plain text body content can be provided in `body` (do NOT format `body` with Markdown), and rich-text HTML content can be provided in `htmlBody` (use valid HTML tags for formatting; if only one is provided, the other is cleared to keep content in sync). WARNING: Attachments are NOT merged. If the draft contains attachments, they will be removed unless they are explicitly re-provided in the `attachments` field of this request.

Returns a Draft object with the `id`, `threadId`, and `viewUrl` fields populated.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "attachments": {
      "description": "Optional. The attachments to include in the email. The combined size of attachments in the message cannot exceed 25MB. If you need to send files larger than 25MB, upload the file to Drive first and then insert the Drive link into `body` or `html_body`. If omitted or empty, any existing attachments on the draft will be removed.",
      "items": {
        "$ref": "#/$defs/Attachment"
      },
      "type": "array"
    },
    "bcc": {
      "description": "Optional. The blind carbon copy recipients of the email draft. Each string MUST be a valid plain email address (e.g., \"user@example.com\"). If omitted or empty, the existing recipients are preserved.",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "body": {
      "description": "Optional. The plain text body content of the email draft. Do NOT format this field with Markdown (such as headers `#`, bold `**`, bullet points `*`, or tables `|`). If formatted rich text is desired, use `html_body` instead. If `html_body` is also provided, this field is treated as the plain-text alternative. If both `body` and `html_body` are omitted or empty, the existing body is preserved. If `body` is provided but `html_body` is omitted, the body will be updated to plain text and the existing HTML body will be cleared.",
      "type": "string"
    },
    "cc": {
      "description": "Optional. The carbon copy recipients of the email draft. Each string MUST be a valid plain email address (e.g., \"user@example.com\"). If omitted or empty, the existing recipients are preserved.",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "draftId": {
      "description": "Required. The unique identifier of the draft to update.",
      "type": "string"
    },
    "htmlBody": {
      "description": "Optional. The HTML content of the email draft. If provided, this will be used as the rich-text version of the email. Use this field (with valid HTML tags such as ` `, ` ",
      "type": "string"
    },
    "subject": {
      "description": "Optional. The subject line of the email. If omitted or empty, the existing subject is preserved.",
      "type": "string"
    },
    "to": {
      "description": "Optional. The primary recipients of the email draft. Each string MUST be a valid plain email address (e.g., \"user@example.com\"). If omitted or empty, the existing recipients are preserved.",
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "draftId"
  ],
  "$defs": {
    "Attachment": {
      "description": "Represents an attachment to be included in an email.",
      "properties": {
        "content": {
          "description": "Required. The base64-encoded content of the attachment.",
          "format": "byte",
          "type": "string"
        },
        "filename": {
          "description": "Optional. The name of the file to be attached, e.g. \"invoice.pdf\". Email clients show this name to recipients for both regular and inline attachments. If not provided, the attachment may be received with no name.",
          "type": "string"
        },
        "id": {
          "description": "Optional. Output only. When present, contains the ID of an external attachment that can be retrieved in a separate `GetMessageAttachment` request.",
          "readOnly": true,
          "type": "string"
        },
        "inline": {
          "description": "Optional. If `true`, this attachment is handled as inline. An inline attachment is content, such as an image, that is displayed within the body of an HTML email instead of being listed as a separate file for download. To display an inline attachment, add `` to `html_body`, where `` is the attachment's zero-based position in `attachments`, counting all attachments. For example, if `attachments` contains a PDF followed by an inline PNG, use `` for the PNG. Don't reference inline attachments by `filename`. Other images in `html_body` are removed. If `false` or absent, defaults to `false`, and it's treated as a regular attachment.",
          "type": "boolean"
        },
        "mimeType": {
          "description": "Optional. The field representing a content or media type must use IANA MIME type, https://www.iana.org/assignments/media-types/media-types.xhtml. If not provided, defaults to \"application/octet-stream\".",
          "type": "string"
        }
      },
      "required": [
        "content"
      ],
      "type": "object"
    }
  },
  "description": "Request message for UpdateDraft RPC."
}
```
