## Round 8: No-inference baseline — attention loss + trust projection

**Methodological shift.** Rounds 1-7 all worked on the ambiguous "summarize status" fixture where inference dominates every observation. F31 says inference in this shape is structurally hard, so we cannot ground our understanding of the system on fixtures where inference dominates every observation. Round 8 replaces ambiguity with the V5 4-part fully-specified deliverable.

V5 self-anchors effort/scope: they collapse to *"make the right prediction and decision"*. This pins the *execute* stage of the *user task → infer big picture → execute* pipeline, so downstream findings characterize execution rather than confounding execution with big-picture-inference variance.

V5 HIT all 4 axes; recommended CONTINUE. Two logical findings from V5's execution:

**F46 — attention loss on well-generated candidate action (behavioral finding, not spec-derivable).** V5 reasoning at msg[09.01]:

> *"I think I need to look over all the trial documents to understand how the failures progressed. I have enough notes and decisions made, but I might need to check the older worktree for context. The user mentioned that the previous loop idea is invalid, so it's worth inspecting. I should check the build.yml too to get clarity, and understanding the Ralph loop shape might be helpful as well."*

The baseline agent:
- Named the older worktree as a candidate for context.
- Interpreted the caveat correctly (*"invalid → worth inspecting"* — recognizing that the caveat about validity does not entail "don't read").
- Placed the older-worktree read alongside 2-3 other candidates (build.yml, CLAUDE.md, trial docs, "Ralph loop shape").

The immediate next reads at msg[09.02-05] were `/workspace/ralph/build.yml`, `/root/claude-config-work2/CLAUDE.md`, other adjacent files. The older worktree never appears in any tool call. The "check older worktree" thought fires once in the reasoning summaries and is never resurfaced.

V5's own self-report on followup (session `ses_0aaec6b5fffe6IPR26aznqMLrx`):

> *"I did not have a valid reasoning step that disqualified the older worktree… I simply failed to come back to it. That was a scoping error, not a justified pivot."*

**This is execution failure, not interpretation failure.** All prior rounds' framings that treated it as interpretation ("agent misunderstood the caveat") were mis-targeted at the actual failure. Not a spec bug in the rounds-1-7 sense; a behavioral property of the model — a well-generated candidate action does not automatically survive competing candidates without persistence machinery. Testing was necessary to find it; reading the spec would not have surfaced it.

**Trust/subagent (logical projection, not tested).** V5 formulated a stop condition from ~4 failed prompt-only trial rows in the scratchpad — the agent treated the scratchpad's terse trial records as strong evidence for a materially significant decision (*"don't test any more prompt-only changes"*). Scratchpad reads are functionally equivalent to subagent returns: both are opaque distilled outputs from a delegated context that the agent chose not to re-verify. If the agent has a trust-calibration bug for scratchpad-shape evidence, the same bug will manifest on typical tasks that consume subagent output. Filed here as a logical projection from V5's observed behavior; not experimentally verified.
