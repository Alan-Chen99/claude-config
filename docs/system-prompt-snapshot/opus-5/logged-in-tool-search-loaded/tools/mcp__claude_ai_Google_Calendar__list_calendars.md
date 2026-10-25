# mcp__claude_ai_Google_Calendar__list_calendars

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Returns the calendars this user owns or has subscribed to. These are the calendars that show up in the calendar list if the user opens Google Calendar. This tool returns a subset of all accessible calendars; other calendars shared with the user can be accessed directly by their `calendar_id` (email identifier) without subscribing to them first. Use this tool to resolve calendar identifying data (for example, 'my family calendar') into its corresponding `calendar_id` (email identifier).

## input_schema

```json
{
  "type": "object",
  "properties": {
    "pageSize": {
      "description": "Optional. Max results per page. Default `100`, max `250`.",
      "format": "int32",
      "type": "integer"
    },
    "pageToken": {
      "description": "Optional. Token specifying which result page to return.",
      "type": "string"
    }
  },
  "description": "Request message for ListCalendars."
}
```
