# mcp__claude-in-chrome__get_page_text

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Extract raw text content from the page, prioritizing article content. Ideal for reading articles, blog posts, or other text-heavy pages. Returns plain text without HTML formatting. If you don't have a valid tab ID, use tabs_context_mcp first to get available tabs.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "tabId": {
      "type": "number",
      "description": "Tab ID to extract text from. Must be a tab in the current group. Use tabs_context_mcp first if you don't have a valid tab ID."
    }
  },
  "required": [
    "tabId"
  ]
}
```
