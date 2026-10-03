# mcp__claude_ai_Google_Drive__copy_file

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Call this tool to copy an existing File in Google Drive.
The tool allows specifying a new title and a parent folder for the copy.
If the title is not specified, the copy title will be 'Copy of {original title}'.
If the parent folder is not specified, the copy will be created in the same folder as the original file, unless the requesting user does not have write access to that folder, in which case the copy will be created in the user's root folder.Returns the newly created File object upon successful copying.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "fileId": {
      "description": "Required. The ID of the file to copy.",
      "type": "string"
    },
    "parentId": {
      "description": "The parent id of the newly created file. If empty, the file will be created with the same parent as the original file.",
      "type": "string"
    },
    "title": {
      "description": "The title of the newly created file. If empty, the title will be 'Copy of {original file title}'.",
      "type": "string"
    }
  },
  "required": [
    "fileId"
  ],
  "description": "Request to copy a file."
}
```
