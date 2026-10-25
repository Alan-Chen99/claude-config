# mcp__claude_ai_Gmail__search_threads

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Lists email threads from the authenticated user's Gmail account.

This tool can filter threads based on a query string and supports pagination. It returns a list of threads, each with its thread `id`, `messageCount` (total messages in the thread), `viewUrl`, and a subset of up to 5 related messages (each with its own message `id`, `viewUrl`, `sender`, recipients, `date`, and `labelIds`). Use this tool to find thread `id`s matching a query before reading full threads or performing actions on matching emails or threads. The `view` parameter controls which additional fields are populated in the returned message subset. By default (or with `THREAD_VIEW_MINIMAL`), it includes `subject` and `snippet`. Use `THREAD_VIEW_METADATA_ONLY` to exclude `subject` and `snippet`. Full message bodies, attachment metadata, and messages beyond the 5-message subset are not returned by this tool; use the 'get_thread' tool with a thread ID to retrieve all messages (and their message IDs) in a thread or to fetch full message bodies. Threads with excluded criteria may still appear in the results. This occurs because Gmail identifies matching messages first. For example, if you search for -is:starred, Gmail will find an entire thread if it contains at least one unstarred message, even if other emails in that same conversation are starred.

To list threads in a specific inbox category tab, use the `category:` operator with `primary`, `social`, `promotions`, `updates`, or `forums` (e.g. `in:inbox category:promotions`).

When filtering by date, `after:` and `before:` both evaluate against midnight (00:00:00) of the specified date (`after:` is inclusive, `before:` is exclusive). To search through a specific day D (or for a date range), set `before:` to the day after (e.g. `after:2026/02/01 before:2026/02/02` for Feb 1, or `after:2026/02/01 before:2026/02/06` for Feb 1–5).

When searching for numbers, a space or dash (`-`) separates numbers while a dot (`.`) is treated as a decimal (e.g., `01.2047-100` is parsed as two numbers: `01.2047` and `100`). To search for hyphenated or dotted identifiers (such as order numbers, tracking IDs, or invoice codes like `INV-12345`), enclose them in double quotes (e.g. "INV-12345" or "01.2047-100") so the dash is not interpreted as a negation operator.

Note: An empty JSON object `{}` represents zero matching items, not an error.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "includeTrash": {
      "description": "Optional. Include threads from TRASH in the results. Defaults to false.",
      "type": "boolean"
    },
    "pageSize": {
      "description": "Optional. The maximum number of threads to return. If unspecified, defaults to 20. The maximum allowed value is 50.",
      "format": "int32",
      "type": "integer"
    },
    "pageToken": {
      "description": "Optional. Page token to retrieve a specific page of results in the list. Leave empty to fetch the first page. This is primarily used for pagination to continue fetching results from where the previous `SearchThreads` call left off, especially when the number of threads matching the query exceeds the `page_size` limit.",
      "type": "string"
    },
    "query": {
      "description": "Optional. A query string to filter the threads. Natural language queries must be pre-converted into Gmail syntax queries to use this tool. If omitted, all threads (excluding spam and trash by default) are listed. Supported Operators by Category: Sender & Recipient: - `from:` — Sent from a specific person. - `to:` — Sent to a specific person. - `cc:` — Specific people in Cc. - `bcc:` — Specific people in Bcc. - `deliveredto:` — Delivered to a specific address. - `list:` — From a specific mailing list. Time & Date: - `after:YYYY/MM/DD` / `newer:YYYY/MM/DD` — Received after a date (evaluates against midnight 00:00:00 of that day, inclusive). - `before:YYYY/MM/DD` / `older:YYYY/MM/DD` — Received before a date (evaluates against midnight 00:00:00 of that day, exclusive; excludes that day). To search through a specific day D (or for a single day D), set `before:` to the day after (for example, `after:2026/02/01 before:2026/02/02` for Feb 1, or `after:2026/02/01 before:2026/02/06` for Feb 1–5). - `older_than:` — Older than a duration (for example, `1y`, `2d`). - `newer_than:` — Newer than a duration. Content: - `subject:` — Words in the subject line. - `has:` — Has specific content types (attachment, drive, youtube, document). - `filename:` — Attachment with a specific name or type. - `\"\"` — Search for an exact word or phrase. (for example, `\"holiday\"`, `\"holiday vacation\"`). Note: Double quotes enforce strict contiguous phrase matching. For topic, discussion, or keyword queries, prefer unquoted keywords (e.g. `partner advertising` instead of `\"partner advertising\"`). - `+` — Match a word exactly. (for example, `+holiday`, `+unicorn`) - `rfc822msgid:` — Specific message ID header. - `AROUND ` — Find words near each other (for example, `holiday AROUND 10 vacation`). Labels & Categories: - `label:` — Under a specific label, matched by its display name (the `name` from `list_labels`), for example `label:wins`. Label IDs such as `Label_123` match nothing. Quote a name that contains spaces (`label:\"Board Prep\"`) or replace its spaces and `/` with `-` (`label:board-prep`). - `category:` — In a category (primary, social, promotions, updates, forums, reservations, purchases). - `in:` — Search in specific labels (archive, snoozed, trash, sent, inbox). For example, `in:trash`, `in:inbox`. Archived and sent messages are included by default; use `-in:archive` and `-in:sent` to exclude them. Drafts are explicitly excluded by default by the tool. Use `in:inbox` to restrict search to the inbox only. - `has:userlabels` — Has any user labels. - `has:nouserlabels` — Does not have any user labels. - `has:*-star` — Specific star colors (if enabled, for example, `has:yellow-star`). - `in:draft` — Search in drafts. -in:draft means exclude drafts from the search results. - `in:sent` — Search in sent messages. - `in:anywhere` — Search across all folders, including Trash. Emails that are spam, confidential, encrypted, or suspicious are still filtered out for security. Status: - `is:` — Search by status (important, starred, unread, read, muted). Size: - `size:` — Specific size in bytes. - `larger:` / `smaller:` — Larger or smaller than a size (for example, `10M` for 10 MB). Logic & Grouping: - `AND` — Match all criteria (default behavior). - `OR` or `{ }` — Match one or more criteria (for example, `from:amy OR from:david`, `{from:amy from:david}`). - `-` (minus) — Exclude criteria (for example, `-movie`). - `( )` — Group multiple search terms (for example, `subject:(dinner film)`). Examples: - `subject:OneMCP Update` - `from:user@example.com` - `to:user2@example.com AND newer_than:7d` - `project proposal has:attachment` - `is:unread -in:draft` A space or a dash (`-`) separates numbers, while a dot (`.`) is treated as a decimal. For example, `01.2047-100` is considered two numbers: `01.2047` and `100`. To search for hyphenated or dotted identifiers (such as order numbers, tracking IDs, or invoice codes like `INV-12345`), enclose them in double quotes (e.g., `\"INV-12345\"` or `\"01.2047-100\"`) so the dash is not interpreted as a negation operator and exact phrase matching is preserved. To prevent overly strict queries, favor concise, keyword-based queries over long subject strings or full sentences. Avoid copying overly detailed subjects from the user prompt verbatim, as this often leads to search misses. Instead, extract the most unique keywords (e.g., subject:amazon \\\"delivery\\\" OR \\\"order\\\" instead of \\\"amazon order\\\"). Use boolean operators to broaden your search coverage. Use OR to search for synonyms or multiple potential senders, and use ( ) for grouping criteria. Note that whitespace between terms acts as an implicit AND.",
      "type": "string"
    },
    "view": {
      "description": "Optional. Controls the fields populated for threads in the thread list. Defaults to `THREAD_VIEW_MINIMAL`. `THREAD_VIEW_MINIMAL` returns `id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`. `THREAD_VIEW_METADATA_ONLY` returns `id`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`.",
      "enum": [
        "THREAD_VIEW_UNSPECIFIED",
        "THREAD_VIEW_METADATA_ONLY",
        "THREAD_VIEW_MINIMAL"
      ],
      "type": "string",
      "x-google-enum-descriptions": [
        "Maps to THREAD_VIEW_MINIMAL for backward compatibility.",
        "Returns `id`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `view_url` (if applicable).",
        "Returns `id`, `snippet`, `subject`, `sender`, `to_recipients`, `cc_recipients`, `bcc_recipients`, `date`, `label_ids`, `view_url` (if applicable)."
      ]
    }
  },
  "description": "Request message for SearchThreads RPC."
}
```
