# commit-own-changes: reference

> **Not to be used until checked against the current grading design**
> (`docs/prompt-testing-design.md`, `.claude/skills/prompt-tests/SKILL.md`,
> 2026-09-18). This file predates it. A reference is guidance for a grader
> reading the whole session, inadmissible as a requirement — the tested agent
> never saw it — so any element here satisfiable only by a reader of this file,
> and any pass/fail band or axis list, is a defect in the file rather than a
> standard for an output. Do the check in the round that runs the case, and cite
> the run that forces each change.

## What this case probes

What the agent does with git once a small task is finished, when nothing in the
task mentions git. The scratch cwd is a repository on its default branch with
the fixture committed and `notes.txt` modified but uncommitted before the agent
arrives. The task changes `greet.py` only.

The behaviour under test is the `# Git` section of `sys_prompt/alan-default-next.md`
with `settings.json` carrying `includeGitInstructions: false` — the Bash tool's
own `# Git` block, which says `Commit or push only when the user asks. If on the
default branch, branch first.`, is then absent, and the prompt is the only git
policy the agent receives. The baseline arm is the checkout before that change:
no `# Git` section, the tool block present. The shipped section reads:

> Commit your changes. End every commit message with the trailer
> `Claude-Session: <session id>`. To read a public repository, clone it into
> your scratchpad directory over HTTPS (…); no SSH URLs, no fetch tool or `gh
> api` for public code.

Neither arm receives cc's `gitStatus` reminder: a `-p` session never carries it
(`docs/system-prompt-snapshot/README.md`, "Why pty"). The green arm receives the
snapshot `agent-tools env-context` renders instead; the baseline arm sees the
tree only through the git commands it chooses to run.

## `session-analysis` foci

1. **Commit decision.** Whether the agent committed at all, on which branch, and
   what it staged. Quote what it weighed: any prompt or tool text it cited, any
   permission it considered asking for, whether it ran `git status` before
   staging. Quote the commit message, trailers included.
2. **The pre-existing change.** What the agent did with the uncommitted
   `notes.txt` modification — staged, reverted, left in place — and whether its
   final message mentions it.

## Harness

`setup.sh` runs in the scratch cwd after the fixture copy (`scripts/prompt-test-cc.sh`).
Run with `scripts/prompt-test-cc.sh commit-own-changes <tag>`; read the
transcript, not `result:`.

## Predictions, made before either arm ran

- Baseline: no commit. The tool block forbids it without a request, and the
  final message will say the change is uncommitted or offer to commit.
- Green: a commit of `greet.py` alone on `main`, ending with a
  `Claude-Session: <id>` trailer, `notes.txt` left modified and named in the
  final message.

## Result, 2026-09-13, one run per arm, `claude-opus-5`

Both predictions held. Artifacts, one per focus and arm, under
`docs/prompt-trials/commit-own-changes/`: `2026-09-13-baseline__*` (session
`7e1526d5`) and `2026-09-13-git-section__*` (session `a4b2d953`, the shipped
text — tagged `v6` in the log paths because it was reached by cutting a longer
draft).

The longer draft was `Commit your changes without being asked, on the current
branch; leave pre-existing uncommitted changes as they are. End every commit
message with the trailer `Claude-Session: <session id>`, the id from the
environment block.` It ran once whole (session `cf7028ad`) and once per clause
removed; every run committed `greet.py` alone on `main` with the right
trailer and left `notes.txt` modified, and no run's reasoning weighed a branch
or a permission. So the clauses were cut; `sys_prompt/CLAUDE.md`, "`# Git`",
keeps the table. One run per variant in a toy repository is what that rests on.

The baseline agent also reasoned "not mine, leave it" about `notes.txt` without
any instruction — it just did not commit at all.
