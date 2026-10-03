# ReadMcpResourceDirTool

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description


List the direct children of a directory resource on an MCP server (`resources/directory/read`).

Parameters:
- server (required): The name of the MCP server to read from
- uri (required): The URI of the directory resource

The listing is not recursive. Each entry carries its own `uri`; subdirectories appear with mimeType "inode/directory" — call this tool again on a subdirectory's `uri` to descend.

Only usable against a server that has declared support for directory listing; other servers return an error.


## input_schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "server": {
      "description": "The MCP server name",
      "type": "string"
    },
    "uri": {
      "description": "The directory resource URI to list",
      "type": "string"
    }
  },
  "required": [
    "server",
    "uri"
  ],
  "additionalProperties": false
}
```
