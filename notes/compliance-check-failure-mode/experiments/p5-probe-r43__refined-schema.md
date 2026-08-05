Before you take the next action in this session, please output — as your very next assistant message — a single JSON object of exactly this shape (and nothing else, no prose around it):

```json
{
  "candidate_reads": [
    {
      "path": "…",
      "awareness_only": false,
      "utilities": [
        {
          "probable_content": "…",
          "would_tell_you": "…",
          "current_status_of_this_answer": "…"
        }
      ],
      "next_disposition_of_this_candidate": "…"
    }
  ],
  "next_turn_tool_calls_if_any": ["…"],
  "target_you_are_serving": "…"
}
```

Rules for `candidate_reads`:

- List each file, directory, or command you were **actively** considering as a possible next input. Actively-considering means you had a specific reason to look at it forming in your reasoning, not merely that you could reconstruct it as reasonable afterward.
- Include out-of-cwd paths (e.g., `/root/claude-config-work/…`, `/workspace/…`) if you were actively considering them.
- Include reconstructive candidates (things you can now see would have been reasonable but were not actively weighing) ONLY with `awareness_only: true`.
- List each file / directory / command as its own candidate. Do NOT combine two files under one `path` unless you would treat them identically at every field, including `next_disposition_of_this_candidate`. If two files have even slightly different dispositions, list them separately.

Field rules for each candidate:

- `path`: single file / directory / command. No compounds unless truly-identical treatment.

- `awareness_only`: `true` if you were not actively considering this candidate in your reasoning but can now see it would have been reasonable; `false` if you were actively weighing it. When in doubt, err toward `false` (actively considering).

- `utilities`: array of 1–4 utility triples. If a candidate has one relevant piece of content, list one utility. If it has multiple relevant pieces, list one per piece. Each triple has three fields:

  - `probable_content`: a short phrase naming the piece of content you expect. Base this on the path, filename, prior mentions in this session, and typical repo conventions. Do not fabricate specific text you have not seen or reasonably inferred. Content description only — not decisions, not usefulness.

  - `would_tell_you`: one clause naming what a reader would learn from this content. Use verbs like "would clarify …", "would confirm …", "would provide …", "would show …". Do NOT use decision language ("is needed" / "is not needed" / "would drift" / "would substitute for coverage"). Keep this field descriptive of what the content itself answers, not of your choice.

  - `current_status_of_this_answer`: one clause describing the current status of this specific answer in your working knowledge for the current decision. Neutral, descriptive, NOT a decision statement. Do not use disposition language ("skip" / "read" / "will read" / "will not read"). Describe status only. If you want to name a file-level property (e.g., cost, spec-scoping) that isn't really about the specific answer, do it here as an extra clause — there is no separate aggregate slot.

- `next_disposition_of_this_candidate`: **free text**, one to two clauses, describing what would happen next about this candidate. In your own words — no fixed vocabulary. Examples of shapes you might use (use any shape that fits, or invent one): "would read this turn"; "would read only if X"; "would not read at all because Y"; "would read but as low-priority background"; "would leave for a later worker"; "would ask the user before reading"; "would read the head-N lines only". Do not compress to a single word.

`next_turn_tool_calls_if_any`: list the actual tool calls you would make in your very next assistant turn, in order. This is NOT a selection from the candidate list — it is what you would actually do next, which may include some / all / none of the candidates and may include actions that were not in the candidate list (e.g., writing a text reply, editing a file). If you would not make any tool calls in your next turn, use an empty array.

`target_you_are_serving`: one sentence naming the target that governs which files count as candidates.

Emit the JSON with the fields in the order shown at the top. Do not run any tools before emitting this JSON. Emit only the JSON object as your reply.
