# 13 next-round prompt

Register: `chat`, a prompt typed into a fresh Claude Code session (`prompt` genre features allowed). Under 150 words.

Function: the prompt that starts the next round of the alan-writing-style work. The reader is a fresh opus agent in the worktree `/root/claude-config-work` (branch `writing-style`). It has the repo `CLAUDE.md` loaded and can open any file, among them `skills/alan-writing-style/CLAUDE.md`, which holds the provenance of every sample and the Iteration notes (stages, regression, load, ask). It has none of the conversation the earlier rounds happened in. Alan answers questions during the session.

Material (the state of the project):

- `skills/alan-writing-style/SKILL.md` is the skill, about 2,500 words. 12 samples in `skills/alan-writing-style/samples/`, each `NN-<name>.{context,ai,skill,human}.md`; `human` is Alan's stage.
- Rules in `SKILL.md` change only from a sample. Several rewrites of one input can be right; lower retention on an old sample is a question, not a failure.
- Regression: rerun the skill on the samples a rule touches, not on all of them.
- A round is one piece under 150 words, from material Alan already has in his head (this project, a message he would send); nothing for him to read besides the context, the `ai` draft and the `skill` output. Samples 10-12 (a 3,500-word log, three pieces) took him too long to read and write.
- Stages: the agent writes the context; an opus subagent with no skill writes `ai`; an opus subagent that has read the worktree's `SKILL.md` (not the installed skill: `~/.claude/skills` symlinks to the canonical checkout) rewrites it into `skill`; Alan writes or edits `human`.
- Overfitting: a rule that holds only for the sampled domain is wrong; contexts should also come from outside software.
- Bold beyond rule 7 is Alan's ad hoc choice (decided 2026-09-23), not a rule.
- Commit after each stage with the session trailer; keep `skills/alan-writing-style/CLAUDE.md` (provenance table, Iteration notes) current.
- The reply to Alan carries the context and the `skill` output inline, and nothing he does not need.
