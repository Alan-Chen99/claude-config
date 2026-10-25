# mcp__claude_ai_Gmail__list_drafts

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Lists draft emails from the authenticated user's Gmail account, optionally filtered by a query string.

Note: An empty JSON object `{}` represents zero matching items, not an error.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "pageSize": {
      "description": "Optional. The maximum number of drafts to return. If unspecified, defaults to 20. The maximum allowed value is 50.",
      "format": "int32",
      "type": "integer"
    },
    "pageToken": {
      "description": "Optional. A token received from a previous `list_drafts` call to retrieve the next page of results. Leave empty to fetch the first page. This is primarily used for pagination to continue fetching results from where the previous `ListDraft` call left off, especially when the number of drafts matching the query exceeds the `page_size` limit.",
      "type": "string"
    },
    "query": {
      "description": "Optional. A query string to filter the drafts. Natural language queries must be pre-converted into Gmail compatible syntax queries to use this tool. If omitted, all drafts (excluding spam and trash by default) are listed. The tool inherently only searches for drafts. Supported Operators by Category: Sender & Recipient: - `from:` — Sent from a specific person. - `to:` — Sent to a specific person. - `cc:` — Specific people in Cc. - `bcc:` — Specific people in Bcc. - `deliveredto:` — Delivered to a specific address. - `list:` — From a specific mailing list. Time & Date: - `after:YYYY/MM/DD` / `newer:YYYY/MM/DD` — Received after a date (evaluates against midnight 00:00:00 of that day, inclusive). - `before:YYYY/MM/DD` / `older:YYYY/MM/DD` — Received before a date (evaluates against midnight 00:00:00 of that day, exclusive; excludes that day). To search through a specific day D (or for a single day D), set `before:` to the day after (for example, `after:2026/02/01 before:2026/02/02` for Feb 1, or `after:2026/02/01 before:2026/02/06` for Feb 1–5). - `older_than:` — Older than a duration (for example, `1y`, `2d`). - `newer_than:` — Newer than a duration. Content: - `subject:` — Words in the subject line. - `has:` — Has specific content types (attachment, drive, youtube, document). - `filename:` — Attachment with a specific name or type. - `\"\"` — Search for an exact word or phrase. (for example, `\"holiday\"`, `\"holiday vacation\"`). - `+` — Match a word exactly. (for example, `+holiday`, `+unicorn`) - `rfc822msgid:` — Specific message ID header. - `AROUND ` — Find words near each other (for example, `holiday AROUND 10 vacation`). Labels & Categories: - `label:` — Under a specific label, matched by its display name (the `name` from `list_labels`), for example `label:wins`. Label IDs such as `Label_123` match nothing. Quote a name that contains spaces (`label:\"Board Prep\"`) or replace its spaces and `/` with `-` (`label:board-prep`). - `category:` — In a category (primary, social, promotions, updates, forums, reservations, purchases). - `in:` — Search in specific labels (archive, snoozed, trash, sent, inbox, important, starred). For example, `in:trash`, `in:inbox`. Note: Drafts, archived, and sent messages are included by default; use `-in:draft`, `-in:archive`, and `-in:sent` to exclude them. Use `in:inbox` to restrict search to the inbox only. - `has:userlabels` — Has any user labels. - `has:nouserlabels` — Does not have any user labels. - `has:*-star` — Specific star colors (if enabled, for example, `has:yellow-star`). Status: - `is:` — Search by status (important, starred, unread, read, muted). Size: - `size:` — Specific size in bytes. - `larger:` / `smaller:` — Larger or smaller than a size (for example, `10M` for 10 MB). Logic & Grouping: - `AND` — Match all criteria (default behavior). - `OR` or `{ }` — Match one or more criteria (for example, `from:amy OR from:david`, `{from:amy from:david}`). - `-` (minus) — Exclude criteria (for example, `-movie`). - `( )` — Group multiple search terms (for example, `subject:(dinner film)`). Examples: - `subject:OneMCP Update` - `from:gduser1@workspacesamples.dev` - `to:gduser2@workspacesamples.dev AND newer_than:7d` - `project proposal has:attachment` - `is:unread` A space or a dash (`-`) separates numbers, while a dot (`.`) is treated as a decimal. For example, `01.2047-100` is considered two numbers: `01.2047` and `100`. To search for hyphenated or dotted identifiers (such as order numbers, tracking IDs, or invoice codes like `INV-12345`), enclose them in double quotes (e.g., `\"INV-12345\"` or `\"01.2047-100\"`) so the dash is not interpreted as a negation operator and exact phrase matching is preserved. Note: If we want to ensure all drafts for the query are returned, we can paginate the results by making repeated calls to the tool until the response contains an empty list of drafts.",
      "type": "string"
    },
    "view": {
      "description": "Optional. Controls the fields populated for drafts in the draft list. Defaults to returning metadata only (`id`, `thread_id`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`). Set to `DRAFT_VIEW_FULL` to include `subject` and `plaintext_body` content.",
      "enum": [
        "DRAFT_VIEW_UNSPECIFIED",
        "DRAFT_VIEW_METADATA_ONLY",
        "DRAFT_VIEW_FULL"
      ],
      "type": "string",
      "x-google-enum-descriptions": [
        "Unspecified view. Defaults to DRAFT_VIEW_METADATA_ONLY.",
        "Returns metadata only (`id`, `thread_id`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`) (if applicable); omits `subject` and `plaintext_body` content.",
        "Returns full draft content, including `subject` and `plaintext_body` in addition to draft metadata (if applicable)."
      ]
    }
  },
  "description": "Request message for ListDrafts RPC."
}
```
