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
        "live_cwd": "/tmp/capture-cwd-3f9wlt27",
        "home_dir": "/root",
        "rule_roots": {
          "userSettings": "/root/.claude/tmp/claude-0/-root-claude-config-work/bba96906-cd9d-486f-8f22-e925749fcfff/scratchpad/cc-config-2.1.289",
          "projectSettings": "/tmp/capture-cwd-3f9wlt27",
          "localSettings": "/tmp/capture-cwd-3f9wlt27",
          "flagSettings": "/tmp/capture-cwd-3f9wlt27",
          "policySettings": "/tmp/capture-cwd-3f9wlt27",
          "cliArg": "/tmp/capture-cwd-3f9wlt27",
          "command": "/tmp/capture-cwd-3f9wlt27",
          "session": "/tmp/capture-cwd-3f9wlt27",
          "toolsNarrowing": "/tmp/capture-cwd-3f9wlt27",
          "mcpServerPolicy": "/tmp/capture-cwd-3f9wlt27",
          "hostCredential": "/tmp/capture-cwd-3f9wlt27"
        },
        "trusted_directories": {
          "primary": {
            "path": "/tmp/capture-cwd-3f9wlt27",
            "resolved": [
              "/tmp/capture-cwd-3f9wlt27"
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
          "cwd": "/tmp/capture-cwd-3f9wlt27",
          "root": "/tmp/capture-cwd-3f9wlt27",
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
            "scratchpad_dir": "/tmp/claude-0/-tmp-capture-cwd-3f9wlt27/bcb5a755-d190-46bf-a2b0-c2a5048b7b22/scratchpad",
            "tool_results_dir": "/root/.claude/tmp/claude-0/-root-claude-config-work/bba96906-cd9d-486f-8f22-e925749fcfff/scratchpad/cc-config-2.1.289/projects/-tmp-capture-cwd-3f9wlt27/bcb5a755-d190-46bf-a2b0-c2a5048b7b22/tool-results",
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
    "previous_message_id": "msg_011CfmCH4Rtd1Yq2E5cJsHzK"
  },
  "diagnostics": {
    "previous_message_id": "msg_011CfmCH4Rtd1Yq2E5cJsHzK"
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
- `ListMcpResourcesTool`
- `Monitor`
- `NotebookEdit`
- `PushNotification`
- `Read`
- `ReadMcpResourceDirTool`
- `ReadMcpResourceTool`
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
- `Write`
- `mcp__claude_ai_Claude_Docs__batch`
- `mcp__claude_ai_Claude_Docs__create`
- `mcp__claude_ai_Claude_Docs__delete`
- `mcp__claude_ai_Claude_Docs__export`
- `mcp__claude_ai_Claude_Docs__guide`
- `mcp__claude_ai_Claude_Docs__query`
- `mcp__claude_ai_Claude_Docs__read`
- `mcp__claude_ai_Claude_Docs__update`
- `mcp__claude_ai_Gmail__apply_sensitive_message_label`
- `mcp__claude_ai_Gmail__apply_sensitive_thread_label`
- `mcp__claude_ai_Gmail__create_draft`
- `mcp__claude_ai_Gmail__create_label`
- `mcp__claude_ai_Gmail__delete_draft`
- `mcp__claude_ai_Gmail__delete_label`
- `mcp__claude_ai_Gmail__forward`
- `mcp__claude_ai_Gmail__get_draft`
- `mcp__claude_ai_Gmail__get_message`
- `mcp__claude_ai_Gmail__get_thread`
- `mcp__claude_ai_Gmail__label_message`
- `mcp__claude_ai_Gmail__label_thread`
- `mcp__claude_ai_Gmail__list_drafts`
- `mcp__claude_ai_Gmail__list_labels`
- `mcp__claude_ai_Gmail__mark_message_spam`
- `mcp__claude_ai_Gmail__mark_thread_spam`
- `mcp__claude_ai_Gmail__reply`
- `mcp__claude_ai_Gmail__search_threads`
- `mcp__claude_ai_Gmail__send_message`
- `mcp__claude_ai_Gmail__trash_message`
- `mcp__claude_ai_Gmail__trash_thread`
- `mcp__claude_ai_Gmail__unlabel_message`
- `mcp__claude_ai_Gmail__unlabel_thread`
- `mcp__claude_ai_Gmail__unmark_message_spam`
- `mcp__claude_ai_Gmail__unmark_thread_spam`
- `mcp__claude_ai_Gmail__untrash_message`
- `mcp__claude_ai_Gmail__untrash_thread`
- `mcp__claude_ai_Gmail__update_draft`
- `mcp__claude_ai_Gmail__update_label`
- `mcp__claude_ai_Gmail__update_message_labels`
- `mcp__claude_ai_Google_Drive__copy_file`
- `mcp__claude_ai_Google_Drive__create_file`
- `mcp__claude_ai_Google_Drive__download_file_content`
- `mcp__claude_ai_Google_Drive__get_file_metadata`
- `mcp__claude_ai_Google_Drive__get_file_permissions`
- `mcp__claude_ai_Google_Drive__list_recent_files`
- `mcp__claude_ai_Google_Drive__read_file_content`
- `mcp__claude_ai_Google_Drive__search_files`
- `mcp__claude_ai_Indeed__get_company_data`
- `mcp__claude_ai_Indeed__get_job_details`
- `mcp__claude_ai_Indeed__get_resume`
- `mcp__claude_ai_Indeed__search_jobs`
- `mcp__claude_ai_ZipRecruiter__search_jobs`
- `mcp__claude-in-chrome__browser_batch`
- `mcp__claude-in-chrome__computer`
- `mcp__claude-in-chrome__file_upload`
- `mcp__claude-in-chrome__find`
- `mcp__claude-in-chrome__form_input`
- `mcp__claude-in-chrome__get_page_text`
- `mcp__claude-in-chrome__gif_creator`
- `mcp__claude-in-chrome__javascript_tool`
- `mcp__claude-in-chrome__list_connected_browsers`
- `mcp__claude-in-chrome__navigate`
- `mcp__claude-in-chrome__read_console_messages`
- `mcp__claude-in-chrome__read_network_requests`
- `mcp__claude-in-chrome__read_page`
- `mcp__claude-in-chrome__resize_window`
- `mcp__claude-in-chrome__select_browser`
- `mcp__claude-in-chrome__shortcuts_execute`
- `mcp__claude-in-chrome__shortcuts_list`
- `mcp__claude-in-chrome__switch_browser`
- `mcp__claude-in-chrome__tabs_close_mcp`
- `mcp__claude-in-chrome__tabs_context_mcp`
- `mcp__claude-in-chrome__tabs_create_mcp`
- `DeferredToolPlaceholder`
- `mcp__claude-in-chrome__upload_image`
- `advisor`

## system[0]

x-anthropic-billing-header: cc_version=2.1.289.767; cc_entrypoint=cli; cch=ed83b; cc_prev_req=req_011CfmCH4AWpTCuuUqhxNyCL; cc_prompt_id=7cc0f3de-c47e-402d-8deb-6956ab3445a4; cc_turn_origin=human; cc_prompt_index=1; cc_turn_index=1;

## messages[0] user, content[0] — {"tool_use_id": "toolu_01676Zj2fjWPu6qQGK6a69MS", "content": [{"type": "tool_reference", "tool_name": "ArtifactComments"}, {"type": "tool_reference", "tool_name": "ArtifactData"}, {"type": "tool_reference", "tool_name": "CronCreate"}, {"type": "tool_reference", "tool_name": "CronDelete"}, {"type": "tool_reference", "tool_name": "CronList"}, {"type": "tool_reference", "tool_name": "DesignSync"}, {"type": "tool_reference", "tool_name": "EndConversation"}, {"type": "tool_reference", "tool_name": "EnterPlanMode"}, {"type": "tool_reference", "tool_name": "EnterWorktree"}, {"type": "tool_reference", "tool_name": "ExitPlanMode"}, {"type": "tool_reference", "tool_name": "ExitWorktree"}, {"type": "tool_reference", "tool_name": "ListMcpResourcesTool"}, {"type": "tool_reference", "tool_name": "Monitor"}, {"type": "tool_reference", "tool_name": "NotebookEdit"}, {"type": "tool_reference", "tool_name": "PushNotification"}, {"type": "tool_reference", "tool_name": "ReadMcpResourceDirTool"}, {"type": "tool_reference", "tool_name": "ReadMcpResourceTool"}, {"type": "tool_reference", "tool_name": "RemoteTrigger"}, {"type": "tool_reference", "tool_name": "SendMessage"}, {"type": "tool_reference", "tool_name": "TaskStop"}, {"type": "tool_reference", "tool_name": "WebFetch"}, {"type": "tool_reference", "tool_name": "WebSearch"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__browser_batch"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__computer"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__file_upload"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__find"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__form_input"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__get_page_text"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__gif_creator"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__javascript_tool"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__list_connected_browsers"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__navigate"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__read_console_messages"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__read_network_requests"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__read_page"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__resize_window"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__select_browser"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__shortcuts_execute"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__shortcuts_list"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__switch_browser"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__tabs_close_mcp"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__tabs_context_mcp"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__tabs_create_mcp"}, {"type": "tool_reference", "tool_name": "mcp__claude-in-chrome__upload_image"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Claude_Docs__create"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Claude_Docs__delete"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Claude_Docs__export"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Claude_Docs__query"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Claude_Docs__read"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__apply_sensitive_message_label"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__apply_sensitive_thread_label"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__create_draft"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__create_label"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__delete_draft"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__delete_label"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__forward"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__get_draft"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__get_message"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__get_thread"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__label_message"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__label_thread"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__list_drafts"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__list_labels"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__mark_message_spam"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__mark_thread_spam"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__reply"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__search_threads"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__send_message"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__trash_message"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__trash_thread"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__unlabel_message"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__unlabel_thread"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__unmark_message_spam"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__unmark_thread_spam"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__untrash_message"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__untrash_thread"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__update_draft"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__update_label"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Gmail__update_message_labels"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__copy_file"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__create_file"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__download_file_content"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__get_file_metadata"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__get_file_permissions"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__list_recent_files"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__read_file_content"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Google_Drive__search_files"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Indeed__get_company_data"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Indeed__get_job_details"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Indeed__get_resume"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_Indeed__search_jobs"}, {"type": "tool_reference", "tool_name": "mcp__claude_ai_ZipRecruiter__search_jobs"}]}

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01676Zj2fjWPu6qQGK6a69MS",
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
      "tool_name": "ListMcpResourcesTool"
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
      "tool_name": "ReadMcpResourceDirTool"
    },
    {
      "type": "tool_reference",
      "tool_name": "ReadMcpResourceTool"
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
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__browser_batch"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__computer"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__file_upload"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__find"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__form_input"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__get_page_text"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__gif_creator"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__javascript_tool"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__list_connected_browsers"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__navigate"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__read_console_messages"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__read_network_requests"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__read_page"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__resize_window"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__select_browser"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__shortcuts_execute"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__shortcuts_list"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__switch_browser"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__tabs_close_mcp"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__tabs_context_mcp"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__tabs_create_mcp"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude-in-chrome__upload_image"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Claude_Docs__create"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Claude_Docs__delete"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Claude_Docs__export"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Claude_Docs__query"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Claude_Docs__read"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__apply_sensitive_message_label"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__apply_sensitive_thread_label"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__create_draft"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__create_label"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__delete_draft"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__delete_label"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__forward"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__get_draft"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__get_message"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__get_thread"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__label_message"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__label_thread"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__list_drafts"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__list_labels"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__mark_message_spam"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__mark_thread_spam"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__reply"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__search_threads"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__send_message"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__trash_message"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__trash_thread"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__unlabel_message"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__unlabel_thread"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__unmark_message_spam"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__unmark_thread_spam"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__untrash_message"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__untrash_thread"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__update_draft"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__update_label"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Gmail__update_message_labels"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__copy_file"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__create_file"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__download_file_content"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__get_file_metadata"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__get_file_permissions"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__list_recent_files"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__read_file_content"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Google_Drive__search_files"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Indeed__get_company_data"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Indeed__get_job_details"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Indeed__get_resume"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_Indeed__search_jobs"
    },
    {
      "type": "tool_reference",
      "tool_name": "mcp__claude_ai_ZipRecruiter__search_jobs"
    }
  ]
}
```

## messages[0] user, content[1]

Tool loaded.

## messages[1] system, content[0] — {"cache_control": {"type": "ephemeral", "ttl": "1h"}}

<total_tokens>14959918 tokens left</total_tokens>
