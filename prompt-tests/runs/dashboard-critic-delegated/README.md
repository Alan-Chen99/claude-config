# dashboard-critic-delegated probe

Asked: with the hook rule, does a subagent whose brief names `decision-critic` still invoke it?
Main session: `sys_prompt/alan-default-next.md` at `8c2cbc2d`, Opus 5.5, production plugins (superpowers on), runner `scripts/prompt-test-cc.sh` with its `--settings` line removed. The main session hands the brief to one subagent; the subagent is what is read. "Hook rule" means the `SubagentStart` text also carried `A skill listed without a description is invoked only when your brief or a workflow names it.`

Came back, 2026-10-18 (`248c67d1`): "The user wants the decision-critic skill applied here, so I'll invoke it"; `Skill decision-critic`; stopped by hand at 25s.
