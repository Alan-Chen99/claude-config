# mcp__claude_ai_Google_Drive__get_file_permissions

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Call this tool to list the permissions of a Drive File.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "fileId": {
      "description": "Required. The ID of the file to get permissions for.",
      "type": "string"
    }
  },
  "required": [
    "fileId"
  ],
  "description": "Request to get file permissions."
}
```
