# mcp__claude_ai_Google_Calendar__search_events

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Searches events on the user's primary calendar using semantic search.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "pageSize": {
      "description": "Optional. Maximum number of entries returned on one result page.",
      "format": "int32",
      "type": "integer"
    },
    "pageToken": {
      "description": "Optional. Token specifying which result page to return.",
      "type": "string"
    },
    "query": {
      "description": "Required. Query string to search for events (case-insensitive).",
      "type": "string"
    }
  },
  "required": [
    "query"
  ],
  "description": "Request message for SearchEvents."
}
```
