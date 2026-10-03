# mcp__claude_ai_Gmail__list_labels

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Lists all labels available in the authenticated user's Gmail account. Use this tool to discover the `id` of a label before calling `label_thread`, `unlabel_thread`, `label_message`, or `unlabel_message`. Note: the system labels, `DRAFT` and `SENT`, cannot be set on messages and are read only.

Note: An empty JSON object `{}` represents zero matching items, not an error.


## input_schema

```json
{
  "type": "object",
  "properties": {},
  "description": "Request message for ListLabels RPC."
}
```
