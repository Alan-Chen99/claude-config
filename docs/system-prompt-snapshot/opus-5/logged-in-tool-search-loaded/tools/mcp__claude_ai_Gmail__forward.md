# mcp__claude_ai_Gmail__forward

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Forwards a specific email message in the authenticated user's Gmail account. Optional comments can be added before the forwarded message using `forwardText` for plain text (do NOT format with Markdown) or `htmlBody` for rich HTML. Additional attachments can be included via the `attachments` field (in addition to any attachments on the original message), but the combined size cannot exceed 25MB. Set `includeSignature` to true to append the user's configured Gmail web signature to the forwarded message.

Returns a Message object with the `id`, `threadId`, and `labelIds` fields populated.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "attachments": {
      "description": "Optional. New attachments to include in the forwarded email, in addition to any attachments already present on the original message. The combined size of attachments in the message cannot exceed 25MB. If you need to send files larger than 25MB, upload the file to Drive first and then insert the Drive link into `forward_text` or `html_body`.",
      "items": {
        "$ref": "#/$defs/Attachment"
      },
      "type": "array"
    },
    "bcc": {
      "description": "Optional. The blind carbon copy recipients of the email. Each string MUST be a valid plain email address (e.g., \"user@example.com\").",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "cc": {
      "description": "Optional. The carbon copy recipients of the email. Each string MUST be a valid plain email address (e.g., \"user@example.com\").",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "forwardText": {
      "description": "Optional. Plain text comments to add before the forwarded message. Do NOT format this field with Markdown (such as headers `#`, bold `**`, bullet points `*`, or tables `|`). If formatted rich text is desired, use `html_body` instead. If `html_body` is also provided, this field is treated as the plain-text alternative.",
      "type": "string"
    },
    "htmlBody": {
      "description": "Optional. The HTML content of the comments to add before the forwarded message. If provided, this will be used as the rich-text version of the forward comments. Use this field (with valid HTML tags such as ` `, ` ",
      "type": "string"
    },
    "includeSignature": {
      "description": "Optional. Whether to append the user's configured Gmail web signature to the forwarded message. Defaults to false.",
      "type": "boolean"
    },
    "messageId": {
      "description": "Required. The unique identifier of the message to forward. A specific `message_id` is required to forward, which can be obtained by retrieving the thread via `get_thread`.",
      "type": "string"
    },
    "to": {
      "description": "Optional. The primary recipients of the email. Each string MUST be a valid plain email address (e.g., \"user@example.com\").",
      "items": {
        "type": "string"
      },
      "type": "array"
    }
  },
  "required": [
    "messageId"
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
  "description": "Request message for Forward RPC."
}
```
