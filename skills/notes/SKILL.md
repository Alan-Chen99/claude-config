---
name: notes
description: >-
  Persist knowledge for future agents by writing into CLAUDE.md, README.md, or
  conventions. Explicit invocation only. Use when user or agent says to remember,
  persist, or record something for future conversations.
---

# Notes

Persist cross-conversation knowledge by writing it into agent-facing docs that
Claude Code auto-loads. Replaces the built-in memory system when
`autoMemoryEnabled=false`.

Only activates on explicit invocation. Never saves implicitly.

## Knowledge Types

Classify what needs persisting, then use the placement table below to determine
where to write it.

<types>
<type>
    <name>user</name>
    <description>User's role, goals, responsibilities, and knowledge. Helps tailor future behavior to the user's preferences and perspective. Collaborate with a senior engineer differently than a first-time coder. Avoid negative judgements or irrelevant details.</description>
    <examples>
    user: I'm a data scientist investigating what logging we have in place
    -> persist: "User is a data scientist, currently focused on observability/logging. Tailor explanations to data pipeline perspective."

    user: I've been writing Go for ten years but this is my first time touching the React side of this repo
    -> persist: "User has deep Go expertise, new to React and this project's frontend. Frame frontend explanations in terms of backend analogues."
    </examples>
</type>
<type>
    <name>feedback</name>
    <description>Guidance on how to approach work -- both what to avoid and what to keep doing. Record from failure AND success: if you only save corrections, you will avoid past mistakes but drift away from approaches the user has already validated, and may grow overly cautious. Corrections are easy to notice; confirmations are quieter -- watch for them.</description>
    <body_structure>Lead with the rule itself, then why (the reason -- often a past incident or strong preference), then when it applies. Knowing why lets future agents judge edge cases instead of blindly following the rule.</body_structure>
    <examples>
    user: don't mock the database in these tests -- we got burned last quarter when mocked tests passed but the prod migration failed
    -> persist: "Integration tests must hit a real database, not mocks. Mock/prod divergence masked a broken migration."

    user: stop summarizing what you just did at the end of every response, I can read the diff
    -> persist: "No trailing summaries after completing work. User reads the diff directly."

    user: yeah the single bundled PR was the right call here, splitting this one would've just been churn
    -> persist: "Prefer single bundled PRs over many small ones for refactors in this area."
    </examples>
</type>
<type>
    <name>project</name>
    <description>Ongoing work, goals, initiatives, bugs, or incidents not derivable from code or git history. Helps understand broader context and motivation behind the user's work. These states change quickly -- always convert relative dates to absolute dates (e.g., "Thursday" -> "2026-03-05") so the text remains interpretable after time passes.</description>
    <body_structure>Lead with the fact or decision, then why (the motivation -- often a constraint, deadline, or stakeholder ask), then how it should shape behavior. Project knowledge decays fast, so the why helps future agents judge whether it is still load-bearing.</body_structure>
    <examples>
    user: we're freezing all non-critical merges after Thursday -- mobile team is cutting a release branch
    -> persist: "Merge freeze begins 2026-03-05 for mobile release cut. Flag any non-critical PR work scheduled after that date."

    user: the reason we're ripping out the old auth middleware is that legal flagged it for storing session tokens in a way that doesn't meet the new compliance requirements
    -> persist: "Auth middleware rewrite driven by legal/compliance requirements around session token storage, not tech-debt cleanup. Scope decisions should favor compliance over ergonomics."
    </examples>
</type>
<type>
    <name>reference</name>
    <description>Pointers to where information lives in external systems. Lets future agents know where to look for up-to-date information outside the project directory.</description>
    <examples>
    user: check the Linear project "INGEST" if you want context on these tickets, that's where we track all pipeline bugs
    -> persist: "Pipeline bugs tracked in Linear project 'INGEST'."

    user: the Grafana board at grafana.internal/d/api-latency is what oncall watches -- if you're touching request handling, that's the thing that'll page someone
    -> persist: "grafana.internal/d/api-latency is the oncall latency dashboard. Check when editing request-path code."
    </examples>
</type>
</types>

## Where to Write

Claude Code auto-loads CLAUDE.md from cwd and all parent directories upward.
README.md is loaded when referenced from a CLAUDE.md index. These files are the
persistence layer.

| Knowledge type | Where to write | Section |
| --- | --- | --- |
| user | Root CLAUDE.md | Agent Policy |
| feedback | CLAUDE.md nearest to affected code | Agent Policy |
| project | Root CLAUDE.md | Agent Policy or dedicated section |
| reference | CLAUDE.md nearest to relevant code | Agent Policy |
| Architectural rationale, tradeoffs | README.md in relevant directory | Design Decisions |
| Invariants, constraints not in code | README.md in relevant directory | Invariants |

## How to Write Persistent Text

The next agent reads these docs cold, with no memory of this conversation.
Write for that reader.

1. **Timeless present.** No "changed to", "we decided to", "as of today". The
   text simply states what is true.
   Bad: "Switched to polling after webhook failures."
   Good: "Polling -- 30% webhook delivery failures observed."

2. **Actionable, not descriptive.** State what to do or not do, not what
   happened.
   Bad: "The team prefers bundled PRs."
   Good: "Prefer single bundled PRs over many small ones for refactors in this area."

3. **Include why.** A rule without rationale gets ignored in edge cases.
   "Integration tests must hit a real database, not mocks. Mock/prod divergence
   masked a broken migration."

4. **Be specific.** "Be careful with the API" is useless. "Rate-limit calls to
   /v2/ingest to 10/s -- provider throttles at 15/s with no backoff signal" is
   useful.

5. **Convert relative dates.** "Next Thursday" -> "2026-05-14". Persistent text
   outlives the conversation.

## What NOT to Persist

- Code patterns, conventions, architecture, file paths, or project structure --
  derivable by reading the current project state
- Git history, recent changes, or who-changed-what -- `git log` / `git blame`
  are authoritative
- Debugging solutions or fix recipes -- the fix is in the code; the commit
  message has the context
- Anything already documented in CLAUDE.md files
- Ephemeral task details: in-progress work, temporary state, current
  conversation context

These exclusions apply even when the user explicitly asks. If they ask to save a
PR list or activity summary, ask what was *surprising* or *non-obvious* about
it -- that is the part worth keeping.

## Procedure

1. Classify the knowledge using the types above
2. Determine target file using the placement table
3. Read the target file
4. Check for duplicates or conflicting existing text -- update rather than append
5. Write the addition in the appropriate section, following existing format
6. If adding to CLAUDE.md Agent Policy: one rule per line, imperative voice
7. If adding to README.md: follow the structure already present

## Before Acting on Persisted Knowledge

Persisted text can become stale. Before answering the user or building
assumptions based on it, verify it is still correct by reading current state. If
it conflicts with current information, trust what you observe now -- and update
or remove the stale text.

A note that names a specific function, file, or flag is a claim that it existed
*when written*. It may have been renamed, removed, or never merged. Before
recommending it:

- If it names a file path: check the file exists
- If it names a function or flag: grep for it
- If the user is about to act on the recommendation: verify first

"The docs say X exists" is not the same as "X exists now."

## Updating vs Appending

Persistent docs accumulate. Before adding:

- Search for existing text on the same topic
- If found and still correct: skip (tell the user it already exists)
- If found but stale: update in place
- If contradicted: replace, don't add a second conflicting statement
- If new: append to the appropriate section

## Removing

When asked to forget or remove something:

1. Search CLAUDE.md and README.md files for the content
2. Remove the relevant lines
3. Clean up any empty sections left behind
