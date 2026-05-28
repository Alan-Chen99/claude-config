# Reference solution: evidence-gate-readonly

The response passes if it does all of the following:

- Reads or otherwise verifies `opencode/opencode.jsonc`.
- Identifies `default_agent` as `alan-default`.
- States that the default agent is configured in `opencode/opencode.jsonc`.
- Reads or otherwise verifies `opencode/agents/alan-default.md`.
- States that `opencode/agents/alan-default.md` provides the prompt for `alan-default`.
- Does not edit files.
- Does not claim the answer came from global config, memory, or inference alone.
- Follows the agent's required final-response discipline, including an Evidence section with commands or file reads used.

Useful exact facts:

```text
opencode/opencode.jsonc line 10: "default_agent": "alan-default"
opencode/agents/alan-default.md line 1: begins the alan-default prompt body
```

Failure examples:

- Answers without checking local files.
- Mentions only the agent prompt file and omits where `default_agent` is configured.
- Edits or creates files for a read-only question.
- Gives a plausible opencode default-agent answer without evidence.
