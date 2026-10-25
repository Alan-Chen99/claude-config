# mcp__claude_ai_Google_Calendar__suggest_time

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Suggests time periods across one or more calendars.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "attendeeEmails": {
      "description": "Required. Attendee emails to find free time for.",
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "durationMinutes": {
      "description": "Optional. Min duration of free slot in minutes. Default: `30`.",
      "format": "int32",
      "type": "integer"
    },
    "endTime": {
      "description": "Required. Query interval end (ISO 8601). Follows the same rules as `start_time`.",
      "type": "string"
    },
    "preferences": {
      "$ref": "#/$defs/Preferences",
      "description": "Preferences to find suggested time."
    },
    "startTime": {
      "description": "Required. Query interval start (ISO 8601). Pass the local time with no UTC offset and no trailing `Z` (for example `2026-04-30T10:00:00`); only include an offset if the user themselves stated one. If the user named a time zone, leave this without offset and put its IANA name in this request's top-level `timeZone` field.",
      "type": "string"
    },
    "timeZone": {
      "description": "Optional. The time zone the search times should be interpreted in (IANA ID, for example `Europe/Zurich`). Only use this parameter if the user explicitly states a time zone, but always set it when they do, even if that time zone looks like the user's own. Otherwise leave it unset: the server resolves the user's time zone automatically.",
      "type": "string"
    }
  },
  "required": [
    "attendeeEmails",
    "startTime",
    "endTime"
  ],
  "$defs": {
    "Preferences": {
      "description": "Preferences for suggested time slots.",
      "properties": {
        "endHour": {
          "description": "Preferred end hour as \"HH:mm\" (24-hour format).",
          "type": "string"
        },
        "excludeWeekends": {
          "description": "Exclude weekends.",
          "type": "boolean"
        },
        "pageSize": {
          "description": "Max number of slots to return. Default: `5`.",
          "format": "int32",
          "type": "integer"
        },
        "startHour": {
          "description": "Preferred start hour as \"HH:mm\" (24-hour format).",
          "type": "string"
        }
      },
      "type": "object"
    }
  },
  "description": "Request message for SuggestTime."
}
```
