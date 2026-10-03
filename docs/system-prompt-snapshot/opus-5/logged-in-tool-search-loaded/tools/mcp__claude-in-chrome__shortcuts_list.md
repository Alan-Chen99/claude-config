# mcp__claude-in-chrome__shortcuts_list

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

List all available shortcuts and workflows (shortcuts and workflows are interchangeable). Returns shortcuts with their commands, descriptions, and whether they are workflows. Use shortcuts_execute to run a shortcut or workflow.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "tabId": {
      "type": "number",
      "description": "Tab ID to list shortcuts from. Must be a tab in the current group. Use tabs_context_mcp first if you don't have a valid tab ID."
    }
  },
  "required": [
    "tabId"
  ]
}
```
