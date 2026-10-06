# mcp__claude-in-chrome__form_input

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Set values in form elements using element reference ID from the read_page tool. If you don't have a valid tab ID, use tabs_context_mcp first to get available tabs.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "ref": {
      "type": "string",
      "description": "Element reference ID from the read_page tool (e.g., \"ref_1\", \"ref_2\")"
    },
    "value": {
      "type": [
        "string",
        "boolean",
        "number"
      ],
      "description": "The value to set. For checkboxes use boolean, for selects use option value or text, for other inputs use appropriate string/number"
    },
    "tabId": {
      "type": "number",
      "description": "Tab ID to set form value in. Must be a tab in the current group. Use tabs_context_mcp first if you don't have a valid tab ID."
    },
    "action_summary": {
      "type": "string",
      "description": "A few words saying what this form fill does on the page and to what, for example 'Sets the delivery date to 29 September'. State the effect only, and accurately: no reasons, nothing about what you were asked or allowed to do, no passwords or other secrets."
    }
  },
  "required": [
    "ref",
    "value",
    "tabId"
  ]
}
```
