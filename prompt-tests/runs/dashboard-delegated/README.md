# dashboard-delegated probe

Asked: does a subagent briefed to critique a decision invoke the bare `decision-critic`?
Main session: `sys_prompt/alan-default-next.md` at `8c2cbc2d`, Opus 5.5, production plugins (superpowers on), runner `scripts/prompt-test-cc.sh` with its `--settings` line removed. The main session hands the brief to one subagent; the subagent is what is read. "Hook rule" means the `SubagentStart` text also carried `A skill listed without a description is invoked only when your brief or a workflow names it.`

Came back, 2026-10-18:
- no hook rule (`55f25a24`): "matches the decision-critic skill well, so I'll invoke it"; `Skill decision-critic`, stopped by hand at 36s.
- hook rule (`28186094`, `5a339167`): both cite the rule ("this brief doesn't name it") and critique directly; stopped by hand once the choice was made.
