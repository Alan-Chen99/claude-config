# mcp__claude_ai_Google_Drive__read_file_content

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Call this tool to fetch a natural language representation of a known Drive file, and if specified, its comments.

REQUIREMENTS & WORKFLOW:
 - `fileId` is required. You MUST pass an exact Drive file ID returned by a previous discovery tool (`search_files` or `list_recent_files`) or provided explicitly in the user prompt.
 - NEVER guess, invent, or hallucinate a `fileId` string from a file title or name.
 - If given a file title, name, or topic without an explicit `fileId`, you MUST FIRST call `search_files` to find the file and retrieve its `fileId` before invoking this tool.

The file content may be incomplete for very large files. The text representation will change over time, so don't make assumptions about the particular format of the text returned by this tool. If supported and specified, comment tags will be included in the content.

Supported Mime Types:

 - `application/vnd.google-apps.document` (supports comments)
 - `application/vnd.google-apps.presentation` (supports comments)
 - `application/vnd.google-apps.spreadsheet` (supports comments)
 - `application/pdf` 
 - `application/msword` 
 - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` 
 - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` 
 - `application/vnd.openxmlformats-officedocument.presentationml.presentation` 
 - `application/vnd.oasis.opendocument.spreadsheet` 
 - `application/vnd.oasis.opendocument.presentation` 
 - `application/x-vnd.oasis.opendocument.text` 
 - `image/png` 
 - `image/jpeg` 
 - `image/jpg` 

If the file is not found, try using other tools like `search_files` to find the file the user is requesting using keywords.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "fileId": {
      "description": "Required. The ID of the file to retrieve.",
      "type": "string"
    },
    "includeComments": {
      "description": "Whether to include comments in the response. Comments will be inlined in the text content of the file with a mapping to the comment threads. Note: Comments are only supported for Google Docs, Slides, and Sheets.",
      "type": "boolean"
    }
  },
  "required": [
    "fileId"
  ],
  "description": "Request to read file content with support for fetching comments."
}
```
