# mcp__claude-in-chrome__switch_browser

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Send a connection request to every Chrome browser with the extension installed and wait (up to 2 minutes) for the user to click 'Connect' in the one they want to use. The user can name the browser when they connect. Use this when the user wants to pick the browser themselves from inside Chrome rather than choosing from a list; otherwise prefer select_browser with a known deviceId.

## input_schema

```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```
