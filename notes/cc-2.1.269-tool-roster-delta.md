# The 2.1.269 tool roster, against 2.1.235

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

**14 upfront tools**, `SendFeedback` and the 13 below, plus one `DeferredToolPlaceholder`
entry flagged `defer_loading: true` (13 + placeholder in
`sonnet-5/default`'s first capture, `notes/cc-2.1.269-upfront-roster-flag-flicker.md`; its
re-capture matches the batch).

Against 2.1.235, by set difference across all three branches: **added** `SendFeedback` only;
the **deferred list did not change**. `SendFeedback`'s description (3,467 chars) is byte-identical across models.

Of 2.1.235's 13 upfront tools plus the placeholder, **nine are byte-for-byte unchanged** in
both models: `AskUserQuestion`, `Read`, `Edit`, `Write`, `ScheduleWakeup`, `Skill`,
`ToolSearch`, `ReportFindings`, `DeferredToolPlaceholder` — by rendering the 2.1.235
`request.json` files into this layout and diffing `tools/` (description and `input_schema`)
with zero output. The remaining five (description chars, 2.1.235 -> 2.1.269):

| Tool | Sonnet 5 | Opus 5 | What changed |
|---|---|---|---|
| `Artifact` | 12,564 -> 25,099 | same bytes | New capabilities documented inline: comments, a shared database (get/list/query/set/update/str_replace/batch), asset upload, multi-file listing, publish watching. **Schema too**: 13 new properties (`files, root, writes, field, old_str, new_str, replace_all, if_version, as_level, icon, prompt, path, pin`), 11 more reworded, `action` gaining `read, watch, unwatch, status, resume_replies, list_types, list_files, read_file, delete, pin, unpin` and `db_op` gaining `str_replace, batch` |
| `Workflow` | 19,290 -> 3,480 | same bytes | Authoring detail moved to a new on-demand `workflow-authoring` skill; the description covers only when to call it (explicit opt-in via "ultracode" or direct request) and the `meta`/`phase`/`pipeline` shape |
| `Bash` | 10,067 -> 10,078 | 1,043 -> 1,315 | Hardcoded attribution text (`Co-Authored-By:` / `🤖 Generated with`) replaced by a pointer to a system-reminder, sonnet's only edit; opus's short form also gained the long form's sentence discouraging `cat/head/tail/sed/awk/echo` for dedicated tools. **Schema too**: the `description` parameter gained `"Say what the command does in plain words: do not echo the command's text, its flags, or file paths - the user reads this description, often without seeing the command."` |
| `ListAgents` | 749 -> 777 | same | Gained `"the teammates on your team"` in the list of who you can `SendMessage` to |
| `Agent` | 7,081 unchanged | 1,811 unchanged | **Schema only**: the `model` parameter takes precedence over "the configured default subagent model" as well as the agent definition's frontmatter, and an omitted `model` "inherits from the parent unless a default subagent model is configured". That default is `CLAUDE_CODE_SUBAGENT_MODEL` (`f9()`, `src/chunk-dbb93264.js:103699`), which upstream's changelog demotes from override to default at 2.1.251 and pairs at 2.1.257 with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, which ignores per-spawn and agent-definition models alike |

`Bash`, `Agent`, `Read`, `Edit`, `Write` keep a materially shorter opus description;
`AskUserQuestion` stays the one where opus's is longer (1,531 sonnet / 1,786 opus).

`tools_total_tokens` (from `summary.json`, exact): 35,834 for every sonnet-5 variant / 30,283
(opus-5) / 36,155 (opus-4-7) / 30,287 (fable-5 and opus-4-8 — 4 tokens above opus-5 on
byte-identical text, tokenizer-boundary noise). `default`'s first capture read 33,878 with
`SendFeedback` missing. 2.1.235: 31,221 (sonnet) / 25,546 (opus-5) / 31,542 (opus-4-7) — the
rise is `Artifact` growing by ~12,500 chars outweighing `Workflow` shrinking by ~15,800.

## Tools — deferred

The 5-family's 18:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

Opus 4.7 gets 21: the same list minus `EndConversation`, plus `TaskCreate`, `TaskGet`,
`TaskList`, `TaskUpdate`. Opus 4.8 gets the 5-family's 18, `EndConversation` included: its
`[4,8]` clears `EndConversation`'s opus floor exactly
(`notes/cc-2.1.269-upfront-roster-flag-flicker.md`).

By direct grep of the 2.1.269 capture, the Bash description still says `NEVER use the TaskCreate
or Agent tools` (commit example) and `DO NOT use the TaskCreate or Agent tools` (PR example):
on the 5-family models both name a tool absent from every list; on opus-4-7, where
`TaskCreate` is still deferred, they have a referent. Opus-4-7's block 2 still carries `"Use
TaskCreate to plan and track work"`; sonnet's block 2 has no such line.
