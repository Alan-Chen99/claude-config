# SubagentHandback

## attributes

```json
{
  "eager_input_streaming": true
}
```

## description

Deliver your final report to the agent that spawned you (your caller). Use it once, for that hand-off only: when your work is complete, call SubagentHandback({message: <your full report>}). The call ends your run, so do everything else first and put everything your caller needs in that one report. It is not a messaging channel: do not use it for progress updates or questions.

Only a report delivered through SubagentHandback reaches your caller; plain text you write at the end of your run is NOT delivered. There is no recipient parameter: the report can only go to your caller.

## input_schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "message": {
      "description": "Your full report for your caller",
      "type": "string"
    }
  },
  "required": [
    "message"
  ],
  "additionalProperties": false
}
```
