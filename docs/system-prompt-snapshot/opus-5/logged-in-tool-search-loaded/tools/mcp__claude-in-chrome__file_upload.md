# mcp__claude-in-chrome__file_upload

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Upload one or multiple files to a file input element on the page. Do not click on file upload buttons or file inputs — clicking opens a native file picker dialog that you cannot see or interact with. Instead, use read_page or find to locate the file input element, then use this tool with its ref to upload files directly. Only files the user has shared with this session (attachments, the session's outputs/uploads folders, or folders the user has connected) can be uploaded; other paths will be rejected. The combined size of all files in a single call must stay under 10 MB.

## input_schema

```json
{
  "type": "object",
  "properties": {
    "paths": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Absolute paths to the files to upload. Each path must be a file the user has shared with this session."
    },
    "ref": {
      "type": "string",
      "description": "Element reference ID of the file input from read_page or find tools (e.g., \"ref_1\", \"ref_2\")."
    },
    "tabId": {
      "type": "number",
      "description": "Tab ID where the file input is located. Use tabs_context_mcp first if you don't have a valid tab ID."
    }
  },
  "required": [
    "paths",
    "ref",
    "tabId"
  ]
}
```
