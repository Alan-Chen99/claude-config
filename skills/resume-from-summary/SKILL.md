---
name: resume-from-summary
description: Use when this conversation continues from a summary of earlier work — after autocompact or /compact, on resume, or from a handoff — before acting on the summary.
---

# Resume from a summary

A summary is lossy: it paraphrases the user, drops the reasons behind
decisions, and can call half-done work done. The transcript it was written from
is still on disk; recover from it before you act.

## 1. Skeleton, before anything else

```bash
agent-tools cc-pretty <target> --skeleton --compact-all > <scratchpad>/prior.skel; wc -l <scratchpad>/prior.skel
grep -nE '^@\S+ +(user|result:AskUserQuestion)|^⟐' <scratchpad>/prior.skel
```

- `<target>`: the transcript the summary was written from: the path after
  "read the full transcript at:", or the session id or path a handoff names.
  With neither, after a compaction of this session, `"$CLAUDE_CODE_SESSION_ID"`
  (compaction keeps the id); otherwise ask the user.
- `--compact-all`: without it you get only the current leg, which opens with
  the summary you already have.
- The skeleton is one line per content block (ref, type, size, preview) and
  reaches 100k tokens on a long session, so it goes to a file. The `grep` maps
  every user message, answer and `⟐ compacted` boundary; read the rest of the
  file in parts, around what you need.

## 2. Dig where the summary is thin

The skeleton's `recover:` header line extracts any ref verbatim. Recover:

- the user's messages and answers: the requests, corrections and approvals the
  summary paraphrases;
- the turns before the last `⟐ compacted` line: the work in flight;
- whatever the summary leans on (an error, a decision, a number) before you
  build on it.

Stop once you can act: everything recovered fills the context the compaction
just freed. Read files from disk, not from the transcript: they may have
changed since.

## 3. Resume

Pick up where the transcript, not the summary, says the work stopped. Where
they disagree, act on the transcript and name the difference in your next
report.
