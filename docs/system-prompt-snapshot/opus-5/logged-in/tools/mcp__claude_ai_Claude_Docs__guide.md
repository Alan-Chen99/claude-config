# mcp__claude_ai_Claude_Docs__guide

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Docs guides: topic.instructions repeats the server instructions. Read it only if your client dropped them. Also topic.<name>, refusal.<code>. After a doc's birth → ["topic.index"].

## input_schema

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "description": "topic.<name> (instructions, index, editing, tabs, comments, charts, chart-definition, diagram, uploads, sharing, skill) or refusal.<code>; several per call is fine."
    }
  }
}
```
