# The 2.1.269 tool roster, against 2.1.235

> **Dated record.** Claude Code **2.1.269**, one account, one capture session
> (2026-09-11, re-derived 2026-09-30). Every figure and `src/chunk-*.js` citation
> is that build's: do not re-pin them, re-measure. The artifacts are
> `docs/system-prompt-snapshot/<model-id>/<variant>/`, whose `README.md` carries
> the capture procedure.

**14 upfront tools** plus one `DeferredToolPlaceholder` entry flagged `defer_loading: true`
(13 + placeholder in `sonnet-5/default`'s first capture — see `notes/cc-2.1.269-upfront-roster-flag-flicker.md`; the
re-capture on disk agrees with every other capture in the batch):

```
Agent, Artifact, AskUserQuestion, Bash, Edit, ListAgents, Read,
ReportFindings, ScheduleWakeup, SendFeedback, Skill, ToolSearch, Workflow,
Write
```

Against 2.1.235: **added** `SendFeedback` only — a set difference across all three branches,
not a count; the **deferred list did not change at all** (same 18 names for the 5-family, same
21 for opus-4-7). `SendFeedback`'s description (3,467 chars) is byte-identical across models.

Of the 13 upfront tools plus the placeholder that existed in 2.1.235, **nine are byte-for-byte
unchanged** in both models: `AskUserQuestion`, `Read`, `Edit`, `Write`, `ScheduleWakeup`,
`Skill`, `ToolSearch`, `ReportFindings`, `DeferredToolPlaceholder` — by rendering the 2.1.235
`request.json` files into this layout and diffing `tools/` with zero output. A tool counts as
changed when its `description` or its `input_schema` moved; `Agent` moved on the schema side
only, and the per-tool files render both. The remaining five:

| Tool | Sonnet 5 description | Opus 5 description | What changed |
|---|---|---|---|
| `Artifact` | 12,564 -> 25,099 | 12,564 -> 25,099 | New capabilities documented inline: comments, a shared database (get/list/query/set/update/str_replace/batch), asset upload, multi-file listing, publish watching. **Schema too**: 13 new properties (`files`, `root`, `writes`, `field`, `old_str`, `new_str`, `replace_all`, `if_version`, `as_level`, `icon`, `prompt`, `path`, `pin`), 11 more reworded, `action` gaining `read`, `watch`, `unwatch`, `status`, `resume_replies`, `list_types`, `list_files`, `read_file`, `delete`, `pin`, `unpin` and `db_op` gaining `str_replace`, `batch` |
| `Workflow` | 19,290 -> 3,480 | 19,290 -> 3,480 | Authoring detail moved out to a new `workflow-authoring` skill (loaded on demand); the tool description now covers only when to call it (explicit opt-in via "ultracode" or direct request) and the `meta`/`phase`/`pipeline` shape |
| `Bash` | 10,067 -> 10,078 | 1,043 -> 1,315 | Hardcoded attribution text (`Co-Authored-By:` / `🤖 Generated with`) replaced by a pointer to a system-reminder (see below) — sonnet's net change is small because that's the only edit; opus's short form also gained a sentence sonnet's long form already had, discouraging `cat`/`head`/`tail`/`sed`/`awk`/`echo` in favor of dedicated tools. **Schema too**: the `description` parameter gained `"Say what the command does in plain words: do not echo the command's text, its flags, or file paths - the user reads this description, often without seeing the command."` |
| `ListAgents` | 749 -> 777 | 749 -> 777 | Gained `"the teammates on your team"` in the list of who you can `SendMessage` to |
| `Agent` | 7,081 unchanged | 1,811 unchanged | **Schema only**: the `model` parameter now takes precedence over "the configured default subagent model" as well as over the agent definition's frontmatter, and an omitted `model` "inherits from the parent unless a default subagent model is configured". That default is the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable (`f9()`, `src/chunk-dbb93264.js:103699`, `let e = a.CLAUDE_CODE_SUBAGENT_MODEL`), which upstream's own changelog demotes from override to default at 2.1.251 and pairs at 2.1.257 with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, which ignores per-spawn and agent-definition models alike. Neither is set in this repo |

`Artifact` and `Workflow` remain byte-identical between sonnet and opus; `Bash`, `Agent`,
`Read`, `Edit`, `Write` remain the tools with a materially shorter opus description;
`AskUserQuestion` remains the one exception where opus's is longer (1,531 sonnet / 1,786 opus).

`tools_total_tokens` (from `summary.json`, exact): 35,834 for every sonnet-5 variant / 30,283
(opus-5) / 36,155 (opus-4-7) / 30,287 (fable-5 and opus-4-8 — 4 tokens above opus-5 on
byte-identical text, tokenizer-boundary noise). `default`'s first capture read 33,878 with
`SendFeedback` missing. 2.1.235: 31,221 (sonnet) / 25,546 (opus-5) / 31,542 (opus-4-7) — the
rise is `Artifact` growing by ~12,500 chars outweighing `Workflow` shrinking by ~15,800.

## Tools — deferred (18 / 21, unchanged from 2.1.235)

Named in a system-reminder, schemas not loaded. 5-family models:

```
CronCreate, CronDelete, CronList, DesignSync, EndConversation, EnterPlanMode,
EnterWorktree, ExitPlanMode, ExitWorktree, Monitor, NotebookEdit,
PushNotification, RemoteTrigger, SendMessage, TaskOutput, TaskStop, WebFetch,
WebSearch
```

Opus 4.7 gets 21: the same list minus `EndConversation`, plus `TaskCreate`, `TaskGet`,
`TaskList`, `TaskUpdate` — identical to 2.1.235, membership checked by set diff. Opus 4.8 gets
18, with `EndConversation` included, same as the 5-family — consistent with the
version-threshold mechanism in `notes/cc-2.1.269-upfront-roster-flag-flicker.md` (`claude-opus-4-8` parses to `[4,8]`, which
clears `opus`'s `[4,8]` floor exactly, where `claude-opus-4-7`'s `[4,7]` does not).

The Bash tool description still says `NEVER use the TaskCreate or Agent tools` (commit example)
and `DO NOT use the TaskCreate or Agent tools` (PR example) verbatim — confirmed present in the
2.1.269 capture by direct grep. On the 5-family models both still name a tool absent from every
list; on opus-4-7 `TaskCreate` is still deferred, so there the instruction still has a
referent. Opus-4-7's block 2 still carries `"Use TaskCreate to plan and track work"`, confirmed
verbatim; sonnet's block 2 has no such line.

