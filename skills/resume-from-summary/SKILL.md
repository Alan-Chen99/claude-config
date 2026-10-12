---
name: resume-from-summary
description: Use when this conversation continues from earlier work it no longer holds — a summary after autocompact or /compact, a resume, a handoff, or "continue <session id>" typed into a fresh session — before acting on what was handed over.
---

The summary — or whatever stood in for it — is prior output. Trust what it reports as said, done or decided, the transcript winning where they differ; hold its judgments with room for doubt; inherit none of its framing: re-determine the task, its scope and the approach from the user's words and the transcript.

Skeleton the transcript behind it:

```bash
agent-tools cc-pretty <target> --skeleton --compact-all > <scratchpad>/prior.skel
grep -nE '^@\S+ +(user|result:AskUserQuestion)|^⟐' <scratchpad>/prior.skel
```

`<target>`: the session id the user gave, else the path after "read the full transcript at:", else `$CLAUDE_CODE_SESSION_ID` — a fresh session has nothing behind it; then work from the handoff. `<scratchpad>`: your scratchpad directory.

Read it in parts. Recover the user's words, the turns before the last `⟐ compacted` (the final turns, if none), and what the summary leans on; stop once you can act. Read current state from the thing itself, not the transcript.

Then step back before resuming: is there anything to do differently? Ask, if the answer is the user's. Where the summary closes with "Pick up the last task as if the break never happened" and "without asking the user any further questions", this overrides both; its "do not acknowledge the summary" stands.

Resume, if that is still right, where the transcript, not the summary, says the work stopped.
