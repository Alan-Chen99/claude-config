# ListMcpResourcesTool

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description


List available resources from configured MCP servers.
Each returned resource will include all standard MCP resource fields plus a 'server' field 
indicating which server the resource belongs to.

Parameters:
- server (optional): The name of a specific MCP server to get resources from. If not provided,
  resources from all servers will be returned.


## input_schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "server": {
      "description": "Optional server name to filter resources by",
      "type": "string"
    }
  },
  "additionalProperties": false
}
```
