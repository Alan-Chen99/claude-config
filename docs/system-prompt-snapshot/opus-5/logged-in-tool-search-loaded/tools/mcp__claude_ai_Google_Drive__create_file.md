# mcp__claude_ai_Google_Drive__create_file

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Call this tool to create or upload a File to Google Drive.

If uploading content, prefer `textContent` for text content. For non-UTF8 contents, use the `base64Content` field and base64 encode the data to set on that field.

Returns a single File object upon successful creation.

The following Google first-party mime types can be created without providing content:

 - `application/vnd.google-apps.document` 
 - `application/vnd.google-apps.spreadsheet` 
 - `application/vnd.google-apps.presentation` 

Folders can be created by setting the mime type to `application/vnd.google-apps.folder`.

When uploading content, the `contentMimeType` field is required and should match the type of the content being uploaded.

By default, supported content will be converted to Google first-party mime types.

To disable conversions for first-party mime types, set `disableConversionToGoogleType` to true.


## input_schema

```json
{
  "type": "object",
  "properties": {
    "base64Content": {
      "description": "Optional. The base64 encoded content to upload. It's an error to set this and `textContent`.",
      "type": "string"
    },
    "content": {
      "deprecated": true,
      "description": "Deprecated: Use `base64Content` or `textContent` instead. The content of the file encoded as base64. The content field should always be base64 encoded regardless of the mime type of the file.",
      "type": "string"
    },
    "contentMimeType": {
      "description": "The mime type of the content being uploaded. Required when any type of content is provided.",
      "type": "string"
    },
    "disableConversionToGoogleType": {
      "description": "Set to true to retain the passed in content mime type and not convert to a Google type. For example, without this a `text/plain` content mime type will be converted to to `application/vnd.google-apps.document`. Has no effect for types that do not have a Google equivalent.",
      "type": "boolean"
    },
    "inheritedPermissionsDisabled": {
      "description": "Set to true to disable inherited permissions on the created folder, restricting access to only users with direct permissions on the folder.",
      "type": "boolean"
    },
    "mimeType": {
      "deprecated": true,
      "description": "Deprecated: DO NOT USE!! Set `contentMimeType` instead.",
      "type": "string"
    },
    "parentId": {
      "description": "The parent id of the file.",
      "type": "string"
    },
    "textContent": {
      "description": "Optional. The (UTF-8) text content to upload. It's an error to set this and `base64Content`.",
      "type": "string"
    },
    "title": {
      "description": "Required. The title of the file.",
      "type": "string"
    }
  },
  "required": [
    "title"
  ],
  "description": "Request to upload a file."
}
```
