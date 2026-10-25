# mcp__claude_ai_Google_Calendar__get_event

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Returns a single event on the given calendar.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "calendarId": {
      "description": "Optional. ID of the calendar containing the event. Email address - can be resolved using `list_calendars`. Default: primary calendar.",
      "type": "string"
    },
    "eventId": {
      "description": "Required. Event ID. Can be resolved using `list_events` or `search_events`.",
      "type": "string"
    }
  },
  "required": [
    "eventId"
  ],
  "description": "Request message for GetEvent."
}
```
