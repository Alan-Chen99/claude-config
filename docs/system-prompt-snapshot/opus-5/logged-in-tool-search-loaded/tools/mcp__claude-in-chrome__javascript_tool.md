# mcp__claude-in-chrome__javascript_tool

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Execute JavaScript code in the context of the current page. The code runs in the page's context and can interact with the DOM, window object, and page variables. Returns the result of the last expression or any thrown errors. If you don't have a valid tab ID, use tabs_context_mcp first to get available tabs.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "description": "Must be set to 'javascript_exec'"
    },
    "text": {
      "type": "string",
      "description": "The JavaScript code to execute. Evaluated in the page context with REPL semantics: top-level `await` works, and the result of the last expression is returned automatically — write the expression you want (e.g. `window.myData.value`, or `await fetch(url).then(r=>r.json())`) rather than `return ...`. You can access and modify the DOM, call page functions, and interact with page variables."
    },
    "tabId": {
      "type": "number",
      "description": "Tab ID to execute the code in. Must be a tab in the current group. Use tabs_context_mcp first if you don't have a valid tab ID."
    }
  },
  "required": [
    "action",
    "text",
    "tabId"
  ]
}
```
