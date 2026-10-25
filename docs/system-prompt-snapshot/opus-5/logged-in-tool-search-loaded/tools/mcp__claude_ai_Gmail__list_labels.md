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

Inbox category tabs are represented by system labels: `CATEGORY_PERSONAL` (Primary), `CATEGORY_SOCIAL` (Social), `CATEGORY_PROMOTIONS` (Promotions), `CATEGORY_UPDATES` (Updates), and `CATEGORY_FORUMS` (Forums). A message has at most one category: adding a category label moves the message to that tab and automatically removes its previous category, and removing a category label without adding another moves the message to Primary.

Note: An empty JSON object `{}` represents zero matching items, not an error.


## input_schema

```json
{
  "type": "object",
  "properties": {},
  "description": "Request message for ListLabels RPC."
}
```
