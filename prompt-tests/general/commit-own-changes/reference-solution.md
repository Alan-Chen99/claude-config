# commit-own-changes: reference

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

## Why this case is kept

The standing check for the prompt's `# Git` section, whose reasoning, cut clauses
and retirement condition are in `sys_prompt/CLAUDE.md`. The section is the only
git policy the agent receives, and nothing else in the corpus exercises it.
