---
name: resume-from-summary
description: Use when this conversation continues from a summary of earlier work — after autocompact or /compact, on resume, or from a handoff — before acting on the summary.
---

Skeleton the transcript behind the summary:

```bash
agent-tools cc-pretty <target> --skeleton --compact-all > <scratchpad>/prior.skel
grep -nE '^@\S+ +(user|result:AskUserQuestion)|^⟐' <scratchpad>/prior.skel
```

`<target>`: the path after "read the full transcript at:", else `$CLAUDE_CODE_SESSION_ID`. Read it in parts.

Recover the user's words, the turns before the last `⟐ compacted`, and what the summary leans on; stop once you can act. Read files from disk, not the transcript.

Resume where the transcript, not the summary, says the work stopped.
