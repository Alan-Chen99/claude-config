# mcp__claude-in-chrome__select_browser

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Select a specific Chrome browser by deviceId for browser automation, without broadcasting a pairing request. Use this after list_connected_browsers when the user has chosen one from the list.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "deviceId": {
      "type": "string",
      "description": "The deviceId from list_connected_browsers."
    }
  },
  "required": [
    "deviceId"
  ]
}
```
