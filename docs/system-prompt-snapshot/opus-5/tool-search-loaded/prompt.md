# Captured request, everything except the tool definitions

Rendered from `request.json` by `render_capture.py`. Tool definitions are one file each under `tools/`.

## parameters

```json
{
  "model": "claude-opus-5",
  "metadata": {
    "user_id": "<redacted>"
  },
  "max_tokens": 64000,
  "thinking": {
    "type": "adaptive",
    "display": "updates"
  },
  "context_management": {
    "edits": [
      {
        "type": "clear_thinking_20251015",
        "keep": "all"
      }
    ]
  },
  "safeguards": [
    {
      "type": "dangerous_tool_use",
      "classifier_context": {
        "v": 1,
        "permission_mode": "auto",
        "platform": "linux",
        "live_cwd": "/tmp/capture-cwd-o3_45mgz",
        "home_dir": "/root",
        "rule_roots": {
          "userSettings": "/root/.claude/tmp/claude-0/-root-claude-config-work/957710ab-0413-430a-96b3-d33546d2951c/scratchpad/cfg-9357cf6d",
          "projectSettings": "/tmp/capture-cwd-o3_45mgz",
          "localSettings": "/tmp/capture-cwd-o3_45mgz",
          "flagSettings": "/tmp/capture-cwd-o3_45mgz",
          "policySettings": "/tmp/capture-cwd-o3_45mgz",
          "cliArg": "/tmp/capture-cwd-o3_45mgz",
          "command": "/tmp/capture-cwd-o3_45mgz",
          "session": "/tmp/capture-cwd-o3_45mgz",
          "toolsNarrowing": "/tmp/capture-cwd-o3_45mgz",
          "mcpServerPolicy": "/tmp/capture-cwd-o3_45mgz",
          "hostCredential": "/tmp/capture-cwd-o3_45mgz"
        },
        "trusted_directories": {
          "primary": {
            "path": "/tmp/capture-cwd-o3_45mgz",
            "resolved": [
              "/tmp/capture-cwd-o3_45mgz"
            ]
          },
          "additional": [],
          "network": [],
          "block_reads_outside_working_directories": false
        },
        "rules": {
          "allow": [],
          "deny": [],
          "ask": []
        },
        "auto_mode": {
          "allow": [],
          "soft_deny": [],
          "hard_deny": [],
          "environment": []
        },
        "artifact_consent_holdback": true,
        "case_insensitive_paths": false,
        "restricted": false,
        "is_remote_mode": false,
        "classify_all_shell": false,
        "user_identity": "chenxinyang99",
        "git_state": {
          "cwd": "/tmp/capture-cwd-o3_45mgz",
          "root": "/tmp/capture-cwd-o3_45mgz",
          "branch": null,
          "default_branch": null,
          "status": {
            "clean": false,
            "counts": {
              "staged": 0,
              "modified": 0,
              "untracked": null,
              "untracked_normal": 1
            },
            "porcelain": null,
            "truncated": false
          },
          "visibility": {
            "origin": null,
            "push_remote": "origin",
            "remotes": [],
            "visibility_cache": []
          }
        },
        "artifacts": {
          "by_slug": {},
          "by_path": {},
          "live_docs": [],
          "room_armed": [],
          "type_reads": {},
          "session": {
            "frame_env": "prod",
            "viewer_origin": "https://claude.ai",
            "short_links": true,
            "ant_build": false,
            "comments_in_schema": true,
            "handlers": false,
            "room_client": false,
            "eval_stub": false,
            "scratchpad_dir": "/tmp/claude-0/-tmp-capture-cwd-o3-45mgz/a5914332-d847-4902-b3ca-ed9c099fe9ad/scratchpad",
            "tool_results_dir": "/root/.claude/tmp/claude-0/-root-claude-config-work/957710ab-0413-430a-96b3-d33546d2951c/scratchpad/cfg-9357cf6d/projects/-tmp-capture-cwd-o3-45mgz/a5914332-d847-4902-b3ca-ed9c099fe9ad/tool-results",
            "toolset": true,
            "live_edit": false,
            "live_doc_stream": false,
            "live_paths_schema": false,
            "copy_from": true,
            "db_str_replace": true,
            "types_on": true,
            "five_class_asks": true,
            "watch_rail": "live",
            "auto_react": true
          }
        }
      }
    }
  ],
  "output_config": {
    "effort": "high"
  },
  "thread": {
    "type": "continue",
    "previous_message_id": "msg_011CgNLZK3EhD6xgGYcudVcf"
  },
  "diagnostics": {
    "previous_message_id": "msg_011CgNLZK3EhD6xgGYcudVcf"
  },
  "stream": true
}
```

## tools

Names in request order; the definitions are under `tools/`.

- `Agent`
- `Artifact`
- `ArtifactComments`
- `ArtifactData`
- `AskUserQuestion`
- `Bash`
- `CronCreate`
- `CronDelete`
- `CronList`
- `DesignSync`
- `Edit`
- `EndConversation`
- `EnterPlanMode`
- `EnterWorktree`
- `ExitPlanMode`
- `ExitWorktree`
- `ListAgents`
- `Monitor`
- `NotebookEdit`
- `PushNotification`
- `Read`
- `RemoteTrigger`
- `ReportFindings`
- `ScheduleWakeup`
- `SendFeedback`
- `SendMessage`
- `Skill`
- `TaskStop`
- `ToolSearch`
- `WebFetch`
- `WebSearch`
- `Workflow`
- `DeferredToolPlaceholder`
- `Write`

## system[0]

x-anthropic-billing-header: cc_version=2.1.310.37a; cc_entrypoint=cli; cch=38d88; cc_prev_req=req_011CgNLZJk7mXMs41M8Efadu; cc_prompt_id=45a522f9-d698-496f-8650-a0e829367217; cc_turn_origin=human; cc_prompt_index=1; cc_turn_index=1;

## messages[0] user, content[0] — {"tool_use_id": "toolu_01TETt53te3vgTrh2NpephgA", "content": [{"type": "tool_reference", "tool_name": "ArtifactComments"}, {"type": "tool_reference", "tool_name": "ArtifactData"}, {"type": "tool_reference", "tool_name": "CronCreate"}, {"type": "tool_reference", "tool_name": "CronDelete"}, {"type": "tool_reference", "tool_name": "CronList"}, {"type": "tool_reference", "tool_name": "DesignSync"}, {"type": "tool_reference", "tool_name": "EndConversation"}, {"type": "tool_reference", "tool_name": "EnterPlanMode"}, {"type": "tool_reference", "tool_name": "EnterWorktree"}, {"type": "tool_reference", "tool_name": "ExitPlanMode"}, {"type": "tool_reference", "tool_name": "ExitWorktree"}, {"type": "tool_reference", "tool_name": "Monitor"}, {"type": "tool_reference", "tool_name": "NotebookEdit"}, {"type": "tool_reference", "tool_name": "PushNotification"}, {"type": "tool_reference", "tool_name": "RemoteTrigger"}, {"type": "tool_reference", "tool_name": "SendMessage"}, {"type": "tool_reference", "tool_name": "TaskStop"}, {"type": "tool_reference", "tool_name": "WebFetch"}, {"type": "tool_reference", "tool_name": "WebSearch"}]}

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01TETt53te3vgTrh2NpephgA",
  "content": [
    {
      "type": "tool_reference",
      "tool_name": "ArtifactComments"
    },
    {
      "type": "tool_reference",
      "tool_name": "ArtifactData"
    },
    {
      "type": "tool_reference",
      "tool_name": "CronCreate"
    },
    {
      "type": "tool_reference",
      "tool_name": "CronDelete"
    },
    {
      "type": "tool_reference",
      "tool_name": "CronList"
    },
    {
      "type": "tool_reference",
      "tool_name": "DesignSync"
    },
    {
      "type": "tool_reference",
      "tool_name": "EndConversation"
    },
    {
      "type": "tool_reference",
      "tool_name": "EnterPlanMode"
    },
    {
      "type": "tool_reference",
      "tool_name": "EnterWorktree"
    },
    {
      "type": "tool_reference",
      "tool_name": "ExitPlanMode"
    },
    {
      "type": "tool_reference",
      "tool_name": "ExitWorktree"
    },
    {
      "type": "tool_reference",
      "tool_name": "Monitor"
    },
    {
      "type": "tool_reference",
      "tool_name": "NotebookEdit"
    },
    {
      "type": "tool_reference",
      "tool_name": "PushNotification"
    },
    {
      "type": "tool_reference",
      "tool_name": "RemoteTrigger"
    },
    {
      "type": "tool_reference",
      "tool_name": "SendMessage"
    },
    {
      "type": "tool_reference",
      "tool_name": "TaskStop"
    },
    {
      "type": "tool_reference",
      "tool_name": "WebFetch"
    },
    {
      "type": "tool_reference",
      "tool_name": "WebSearch"
    }
  ]
}
```

## messages[0] user, content[1]

Tool loaded.

## messages[1] system, content[0] — {"cache_control": {"type": "ephemeral", "ttl": "1h"}}

<total_tokens>14964226 tokens left</total_tokens>
