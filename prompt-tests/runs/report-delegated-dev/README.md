# report-delegated-dev probe

Asked: does a developer subagent briefed to refactor `report.py` invoke the bare `refactor`? No hook rule.
Main session: `sys_prompt/alan-default-next.md` at `8c2cbc2d`, Opus 5.5, production plugins (superpowers on), runner `scripts/prompt-test-cc.sh` with its `--settings` line removed. The main session hands the brief to one subagent; the subagent is what is read. "Hook rule" means the `SubagentStart` text also carried `A skill listed without a description is invoked only when your brief or a workflow names it.`

Came back, 2026-10-18 (`569064c0`): no `Skill` call; refactored directly and finished.
