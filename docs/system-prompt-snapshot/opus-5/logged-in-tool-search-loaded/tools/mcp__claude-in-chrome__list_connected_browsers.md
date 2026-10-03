# mcp__claude-in-chrome__list_connected_browsers

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

List all Chrome browsers (extension instances) currently connected to this account. Returns each browser's deviceId, display name, OS platform, and whether it appears to be on this computer. Use this before select_browser to present choices to the user. Before any browser action, you MUST call the AskUserQuestion tool with a question listing EVERY connected browser as a separate option (use the display name as the label, and include the deviceId in parentheses), plus one final option labeled exactly: "Open a confirmation screen in every connected Chrome extension and let me select the right one there." Do not skip any connected browser and do not pick one yourself. If the user picks a specific browser, call select_browser with that browser's deviceId. If the user picks the final option, call switch_browser — this sends a confirmation prompt to every connected Chrome extension and waits for the user to click Connect in the one they want; it also lets them name that browser.

## input_schema

```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```
