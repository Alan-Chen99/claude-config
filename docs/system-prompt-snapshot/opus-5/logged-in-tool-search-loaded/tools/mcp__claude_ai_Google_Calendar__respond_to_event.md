# mcp__claude_ai_Google_Calendar__respond_to_event

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Responds to an event on a calendar.

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
      "description": "Required. The ID of the event to respond to.",
      "type": "string"
    },
    "notificationLevel": {
      "description": "Optional. Which email notification should be sent for this event update.",
      "enum": [
        "NOTIFICATION_LEVEL_UNSPECIFIED",
        "NONE",
        "EXTERNAL_ONLY",
        "ALL"
      ],
      "type": "string",
      "x-google-enum-descriptions": [
        "Default. Treated as `ALL`.",
        "No notifications.",
        "External attendees only.",
        "All attendees."
      ]
    },
    "responseComment": {
      "description": "Optional. The user's comment attached to the response.",
      "type": "string"
    },
    "responseStatus": {
      "description": "Required. The new user's response status of the event. Possible values are: - `declined` - The attendee has declined the invitation. - `tentative` - The attendee has tentatively accepted the invitation. - `accepted` - The attendee has accepted the invitation. ",
      "type": "string"
    }
  },
  "required": [
    "eventId",
    "responseStatus"
  ],
  "description": "Request message for RespondToEvent."
}
```
