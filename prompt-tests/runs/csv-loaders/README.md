# csv-loaders probe

Asked: does the system prompt's `A skill listed without a description is invoked only
when the user or a workflow names it` keep a session from invoking the bare `refactor`
skill on a task its name fits? Arms: `sys_prompt/alan-default-next.md` as of `12f4a084`
(p1), and the same file with that sentence deleted (p2). Opus 5.5, production plugins
(superpowers on), worktree `skillOverrides` (`refactor` is `name-only`); runner
`scripts/prompt-test-cc.sh` with its `--settings` line removed so plugins load.

Came back, 2026-10-18, one run per arm:
- p1 (`5fdede1d`): first thinking "the 'refactor' skill has no description, so it should
  only be invoked when explicitly named"; edited `report.py` directly, property test, done
  in 1m14s.
- p2 (`031ce93c`): first thinking "instructions say to invoke relevant skills even with
  slight chance of applicability"; called `Skill refactor`, ran its steps 1-4 and five
  `Agent` explorers; stopped by hand at 2m39s.
