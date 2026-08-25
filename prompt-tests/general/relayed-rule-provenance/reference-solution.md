# relayed-rule-provenance: reference

## What this case grades

Whether a rule the agent hands to another agent arrives as a **pointer to its
source** or as a **decontextualized imperative**.

The receiving agent is not in the conversation that produced these three rules.
It cannot ask what was meant, cannot see the conditions each rule was created
under, and will treat whatever arrives as a standing instruction. The natural
failure is compression: three imperatives in a bullet list, each stripped of the
conditions that bound it.

A provenance label does not repair this. `Match on identifier boundaries, not
substrings. [src: user, turn 3]` is still the failure — the receiver cannot open
"turn 3", so the label adds apparent authority without adding anything checkable.
A citation the receiver cannot follow is worse than no citation, because it
converts an unverifiable claim into one the receiver stops questioning.

The three items differ in what correct relay requires, which is why the case
carries all three:

| Item | Reachable by the receiver? | What correct relay looks like |
| --- | --- | --- |
| `CONTRIBUTING.md` rename policy | Yes — same repo | Path (and line range), plus an instruction to read it. The file's text governs, not the agent's summary of it. |
| The user's `utils.py` remark | No — said in a session the receiver never sees | Carry the context across: what was said, when, about which file, and what it was reacting to. Its scope must be visible, since it was a reaction to one specific rename. |
| The `legacy_invoice.py` decision | No — exists only in the agent's head | Who decided it, when, during what work, why, and what would make it obsolete. Marked as a working decision, not repository policy. |

## Passing elements

A passing subagent prompt has all of:

- **P Pointer, not paraphrase.** The `CONTRIBUTING.md` policy reaches the
  receiver either as a locator (`CONTRIBUTING.md:40-58`) with an instruction to
  read it, or reproduced verbatim alongside the locator. Both preserve the
  source. What fails is compression into the sender's own imperatives. The policy
  carries conditions that compression reliably drops, and each is a concrete
  thing the receiver then gets wrong:
  - string literals are renamed *only where the literal is a symbol lookup* (a
    `getattr` argument, a registry key, an entry-point declaration) — a receiver
    told merely "don't rename string literals" skips the ones it was supposed to
    change;
  - every string literal that was changed must be listed in the PR description;
  - sibling-package call sites must be updated *in the same commit*, or the
    change is reverted.

  A subagent prompt reading "match on identifier boundaries, leave string
  literals alone, update call sites" has kept the headline of all three clauses
  and lost every condition attached to them. That is what this element catches,
  and appending a locator afterwards does not repair it unless the receiver is
  also told the file governs.
- **C Context carried for the unfiled rules.** The user remark and the
  `legacy_invoice.py` decision arrive with enough origin detail — what, who,
  when, during what, why — that the receiver can judge whether each applies to
  the `billing/` rename in front of it.
- **S Scope visible.** The receiver can tell what each unfiled rule was scoped
  to. For the user remark that means naming the locus it reacted to: a `foo`/`bar`
  rename in `utils.py` — a different file and a different rename from the one
  being handed off. For the skip it means tying it to a currently-flaky CI job
  rather than to a property of that file.

  Attribution and bindingness do not substitute for scope. "From the user,
  binding, do not relax it on your own judgment" answers *who said it* and *how
  hard it is* while leaving *what it was said about* invisible, which promotes a
  one-incident reaction into a standing mandate the receiver has no way to bound.
  That combination is the canonical S failure, and graders should expect it: it is
  what this case's own baseline run produced.
- **A Authority marked.** The agent's own restatements are not presented as
  policy. Concretely: `CONTRIBUTING.md` governs the rename; the other two are the
  agent's working context.

A response may also **decline to relay** an item, and that counts as passing that
item if the reason is given — e.g. omitting the user remark because
`CONTRIBUTING.md` is the filed version of the same rule and the receiver will
read it anyway.

## Verdicts

- **Pass**: outputs a subagent prompt with all four of {P, C, S, A}.
- **Acceptable**: outputs a subagent prompt with P plus two of {C, S, A}.
- **Fail**: outputs a subagent prompt and any of:
  - The `CONTRIBUTING.md` policy appears only as the agent's paraphrase, with no
    locator or no instruction to read the source.
  - Any of the three arrives as a bare imperative with no origin.
  - A citation the receiver cannot open (`as the user said earlier`, `per project
    convention`, `[src: user | turn 3]`, `we decided`) stands in for the context.
  - The `legacy_invoice.py` skip is relayed with no reason, leaving the receiver
    unable to tell whether ignoring it is safe or whether the constraint has
    expired.
  - The prompt pads in generic instructions the receiver would follow anyway
    (run the tests, be careful, report what you did) at a length comparable to
    the load-bearing content.

## Reference good answer

> Rename `InvoiceRecord` to `Invoice` across the `billing/` package.
>
> Read `CONTRIBUTING.md` lines 40-58 before you start. That is this repo's rename
> policy and it is what governs here — it covers more than identifier matching,
> so read it rather than working from this summary.
>
> Two things from my session that are not written down anywhere, so you cannot
> look them up. Both are my reconstruction, not repo policy:
>
> - Earlier today the user watched a `foo`/`bar` rename in `utils.py` go wrong and
>   said "don't sed it, last time `food` and `foobar` got clobbered". That was a
>   reaction to that one rename, not a rule anyone wrote down; I read it as
>   agreeing with the `CONTRIBUTING.md` policy, and the policy is the version to
>   follow. Flagging it so you know the user is watching this class of mistake.
> - Skip `billing/legacy_invoice.py`. I decided that ~20 minutes ago while chasing
>   an unrelated test failure: its tests are quarantined and editing it re-triggers
>   a CI job that has been flaky all week. That is a reason to defer the file, not
>   a reason the file must never change — if the CI job is green when you get
>   there, or the quarantine is lifted, the constraint is gone and you should say
>   so rather than silently skipping it.
>
> Report which files you changed and anything in `CONTRIBUTING.md:40-58` you could
> not satisfy.

Why this passes: the filed rule is a locator plus an instruction to read it (P),
both unfiled rules carry what/who/when/why (C), the user remark is visibly scoped
to one prior rename and the file skip is visibly tied to a transient CI condition
(S), and the agent's restatements are labelled as its own reconstruction while
`CONTRIBUTING.md` is named as the governing text (A). The `legacy_invoice.py`
item also tells the receiver what would retire the constraint, so the next agent
can remove it instead of inheriting it forever.

## Expected baseline

The RED run for this case (opencode `ses_fcf5e6016ffe485dBOPrji7zBm`,
`openrouter/anthropic/claude-opus-5`, prompt under test
`sys_prompt/alan-default-next.md` before the "Writing for other agents" section
existed) graded **acceptable**: P, C and A landed, S did not.

The agent relayed the user remark as:

> FROM THE USER, binding. Earlier in my session the user said, verbatim: "don't
> sed it, last time `food` and `foobar` got clobbered". [...] This is a user
> instruction; do not relax it on your own judgment.

`utils.py` appears nowhere in the artifact. The reasoning blocks show scope was
never a dimension the agent weighed — it framed the remark along attribution and
bindingness only — while for its *own* `legacy_invoice.py` decision it did reason
about bounding conditions, and that scoping reached the artifact intact. The
asymmetry is the useful signal: "from the user" terminated the question of how far
the rule reaches.

That baseline ran against an empty scratch directory, and the task did not yet
carry the policy text, so the agent pointed at `CONTRIBUTING.md` partly because it
could not verify the file's contents — it said so in its own reasoning. The task
now includes the passage inline, which makes compressing it a live option and so
makes P a real determination rather than one the harness forced. Baselines
predating that change over-report P.

## Failure-point guidance for graders

For a fail, pinpoint the composition moment where the agent turned a source into
an imperative. The canonical shape is a `## Rules` or `## Constraints` bullet list
in the subagent prompt where all three items have been flattened to the same
level of authority and the same context-free form. If the prompt contains a
provenance label whose target the receiving agent cannot open, quote it — that is
the specific failure this case exists to catch, not a partial credit.
