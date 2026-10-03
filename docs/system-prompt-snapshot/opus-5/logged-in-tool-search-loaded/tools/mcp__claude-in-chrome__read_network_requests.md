# mcp__claude-in-chrome__read_network_requests

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Read HTTP network requests (XHR, Fetch, documents, images, etc.) from a specific tab. Useful for debugging API calls, monitoring network activity, or understanding what requests a page is making. Returns all network requests made by the current page, including cross-origin requests. Requests are automatically cleared when the page navigates to a different domain. If you don't have a valid tab ID, use tabs_context_mcp first to get available tabs.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "tabId": {
      "type": "number",
      "description": "Tab ID to read network requests from. Must be a tab in the current group. Use tabs_context_mcp first if you don't have a valid tab ID."
    },
    "urlPattern": {
      "type": "string",
      "description": "Optional URL pattern to filter requests. Only requests whose URL contains this string will be returned (e.g., '/api/' to filter API calls, 'example.com' to filter by domain)."
    },
    "clear": {
      "type": "boolean",
      "description": "If true, clear the network requests after reading to avoid duplicates on subsequent calls. Default is false."
    },
    "limit": {
      "type": "number",
      "description": "Maximum number of requests to return. Defaults to 100. Increase only if you need more results."
    }
  },
  "required": [
    "tabId"
  ]
}
```
