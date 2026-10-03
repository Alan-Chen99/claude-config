# mcp__claude-in-chrome__tabs_context_mcp

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Get context information about the current MCP tab group. Returns all tab IDs inside the group if it exists. CRITICAL: You must get the context at least once before using other browser automation tools so you know what tabs exist. Each new conversation should create its own new tab (using tabs_create_mcp) rather than reusing existing tabs, unless the user explicitly asks to use an existing tab.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "createIfEmpty": {
      "type": "boolean",
      "description": "Creates a new MCP tab group if none exists, creates a new Window with a new tab group containing an empty tab (which can be used for this conversation). If a MCP tab group already exists, this parameter has no effect."
    }
  },
  "required": []
}
```
