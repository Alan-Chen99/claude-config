# resume-from-summary/

Recovers the transcript behind a session summary, under rules for what the summary is
trusted for. The `SessionStart` hook injects `SKILL.md`'s body after a compaction;
`sys_prompt/alan-default-next.md` names it (`# Context management`); a fresh session has
only its `description`.

## Files

| File | What | When to read |
| --- | --- | --- |
| `SKILL.md` | Rules for reading the summary; skeleton with `--compact-all`; targeted recovery; step back; resume. The hook renders it with `<target>`/`<scratchpad>` filled and drops the one `` `<target>`: `` line | Editing the skill |
| `README.md` | Why the prompt line triggers it and how it was measured; the sizes behind the file and the `grep`; what to re-check after a Claude Code upgrade | Changing the trigger, its prompt line or the skill's first step; after a Claude Code upgrade |
