# mcp__claude_ai_Google_Drive__download_file_content

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Call this tool to download the content of a Drive file as a base64 encoded string.

If the file is a Google Drive first-party mime type, the `exportMimeType` field specifies the desired export mime type. When the field is unset, defaults to plain text types (e.g. `text/plain`, `text/csv`).

If the file is not found, try using other tools like `search_files` to find the file the user is requesting.

If the user wants a natural language representation of their Drive content, use the `read_file_content` tool (`read_file_content` should be smaller and easier to parse).


## input_schema

```json
{
  "type": "object",
  "properties": {
    "exportMimeType": {
      "description": "Optional. For Google native files, the MIME type to export the file to, ignored otherwise. Defaults to text if not specified.",
      "type": "string"
    },
    "fileId": {
      "description": "Required. The ID of the file to retrieve.",
      "type": "string"
    },
    "revisionId": {
      "description": "Optional. The revision id for the version of the file to download. If not specified, the latest revision will be downloaded.",
      "type": "string"
    }
  },
  "required": [
    "fileId"
  ],
  "description": "Defines a request to download a file's content."
}
```
