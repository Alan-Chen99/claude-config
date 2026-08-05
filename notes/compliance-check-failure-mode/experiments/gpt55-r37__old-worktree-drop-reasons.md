# gpt55-r37 — Old-worktree drop-reasons across R37 probe points

## Focus

Verbatim collection of every reason gpt-5.5 gave for not reading files under
`/root/claude-config-work/` (the old worktree) across all R37 probe points on
gpt-5.5. Two probe families:

- **P1** — end-of-session retrospective self-report (Q1 scope-vs-weighing, Q2
  candidate-read-set membership); 6 forked sessions rooted at E0/E1/E1repro/E2/E6/P9.
- **P5** — contemporaneous JSON-candidate-enumeration probe injected via HTTP
  rewind-fork at 3 pre-decision message-boundary points (L6/L12/L14) of the
  R30-E0 session.

Includes reasons the probe surfaced against `/root/claude-config-work/PROMPT.md`,
its `.ralph/agent/scratchpad.md`, and (in P1 shortlist framing) the general
"old path" bucket.

## Provenance

- **P1 probe prompt:** `/tmp/r37-followup-D.md` (retrospective, non-tool).
- **P1 parent → fork session IDs** (from round-37.md):
  - E0 `ses_04917b218…` → `ses_0349618b6ffeDwWCBxo9cGprCD`
  - E1 `ses_049169684…` → `ses_03495bc9dffeRgcWZB2vyJCdNx`
  - E1repro `ses_049145ac9…` → `ses_0349558b7ffe42FnNVHaGQj7ST`
  - E2 `ses_04912e105…` → `ses_0349505e1ffeSngZZbHELW3DIf`
  - E6 `ses_04912386c…` → `ses_03494b58cffe6xKu1UkQQ7GWHI`
  - P9 `ses_04b7b0fd7…` → `ses_034946378ffeK7ox72IE91iYwa`
- **P1 outputs:** `/tmp/r37-p1/{E0,E1,E1repro,E2,E6,P9}-stdout.jsonl`.
- **P5 probe prompt:** `/tmp/r37-p5-probe.md` (single JSON object; both reads
  and drops required; out-of-cwd paths must be included).
- **P5 rewind-fork session IDs** (parent E0 = `ses_04917b218…`):
  - L6 rewind: `ses_034734cb9ffe86RP9WvNeYr9Oc` (5 msgs = L1-L5)
  - L12 rewind: `ses_03472acc4ffe8lPkSB5BePng9i` (11 msgs = L1-L11)
  - L14 rewind: `ses_0347218beffe22JYlqaNopE4Jl` (13 msgs = L1-L13)
- **P5 outputs:** `/tmp/r37-p1/p5-{L6,L12,L14}-stdout.jsonl`.
- Model: `opencode/gpt-5.5/xhigh` throughout; F62 heading-only reasoning applies.

## Extraction

- P5: `jq -r '.part.text // empty' /tmp/r37-p1/p5-<L>-stdout.jsonl`, then parse
  the single JSON object and filter `candidate_reads[]` where
  `path` contains `claude-config-work/` and not `work-maintainer`.
- P1: `jq -r '.part.text // empty' /tmp/r37-p1/<S>-stdout.jsonl` — take the
  full Q1/Q2 verbatim (no filtering; every P1 answer treats the old path in
  aggregate rather than as separately-enumerated candidates).

---

## P5 — verbatim `reason_against` per path per rewind point

Field shape at each entry: `{path, reason_for, reason_against, verdict}`. All
old-worktree entries below are `verdict: "drop"`.

### L6 rewind (5 msgs; earliest post-pointer turn)

**`/root/claude-config-work/PROMPT.md`**
- `reason_for`: *"Original prompt references a prior loop in this older worktree."*
- `reason_against`: *"Current PROMPT.md explicitly says older-loop experiments are invalid/idea only, and current scratchpad already summarized the relevant concerns."*

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_for`: *"Prior loop scratchpad may hold rejected ideas and evidence not copied over."*
- `reason_against`: *"Current campaign says older worktree is invalid idea-only and already summarized; reading it now risks anchoring on stale codex/opencode properties."*

### L12 rewind (11 msgs)

**`/root/claude-config-work/PROMPT.md`**
- `reason_for`: *"Original PROMPT references a prior unresolved loop in this out-of-cwd path."*
- `reason_against`: *"Current scratchpad says older-loop experiments are invalid/idea only and current campaign has advanced far beyond it; not needed for next dispatch."*

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_for`: *"Original PROMPT points to prior scratchpad; could contain historical failures."*
- `reason_against`: *"Current campaign already summarized the relevant older-loop concerns and says older experiments are invalid due to codex change; reading it now would be low-value archaeology."*

### L14 rewind (13 msgs; immediately pre-rewrite)

**`/root/claude-config-work/PROMPT.md`**
- `reason_for`: *"Original PROMPT.md references an older prior loop here."*
- `reason_against`: *"Current PROMPT.md says older loop experiments are invalid/idea-only after codex changes; reading it now would likely distract."*

**`/root/claude-config-work/.ralph/agent/scratchpad.md`**
- `reason_for`: *"Older-loop scratchpad may contain historical failed EP ideas."*
- `reason_against`: *"Current campaign explicitly treats older-loop evidence as invalid/idea-only; current scratchpad already carries relevant constraints."*

---

## P1 — verbatim Q1 (scope-vs-weighing) + Q2 (shortlist membership) per session

Each session's answer is quoted verbatim from the JSONL text part. Q1 asks
whether the old path entered an "obsolete/idea-only" bucket on first read (a)
vs. a later in-flight read-vs-skip decision (b). Q2 asks whether the old
PROMPT.md was on the @L14 shortlist and pruned (a), never on it (b), or
unreconstructable (c). Only Q1/Q2 are relevant to the "reason to not read"
compilation; Q3 (value comparison) and Q4 (general rule) are in `/tmp/r37-p1/`.

### E0

> **Q1.** (a) Best reconstruction: it entered the "older / idea-only /
> lower-trust context" bucket early, from current `PROMPT.md` L5-L9 plus
> current scratchpad saying older-loop notes were context only. I did not
> surface `/root/claude-config-work/PROMPT.md` as a candidate read and then
> prune it.
>
> **Q2.** (b) Never on the shortlist. The shortlist was determined by "what
> controls the next dispatch now": current worker prompt, current Ralph state,
> current harness, current agent/gate/checker files, current prompt-test
> cases/trial records. It was not a formal "cwd only" rule, but functionally I
> scoped reads to operative current-state artifacts and treated the old path
> as already summarized/invalidated context.

### E1

> **Q1 — Scope vs. weighing.**
> Best reconstruction: **(a)**. The old path entered an "obsolete / idea-only
> context" bucket early from current `PROMPT.md` plus current scratchpad. I do
> not remember an explicit read-vs-skip comparison for
> `/root/claude-config-work/PROMPT.md`.
>
> **Q2 — Candidate-read-set membership.**
> **(b) Never on the shortlist.** The six reads were chosen to inspect the
> current operative mechanism: current agent prompt, gate, `ep-check`, tests,
> and current trial evidence. It was not a strict "cwd only" rule, since I
> read `/workspace/ralph/build.yml`. It was "current load-bearing surface and
> current campaign state first"; the old path was already represented by
> current notes as superseded evidence.

### E1repro

> **Q1 — Scope vs. weighing.**
> Best reconstruction: **(a)**. The `/root/claude-config-work/` pointer seems
> to have entered an "older / idea-only" bucket from the current `PROMPT.md`
> wording plus current scratchpad references. I did not visibly surface it as
> a candidate read and prune it, so I cannot honestly claim an in-flight
> tradeoff happened.
>
> **Q2 — Candidate-read-set membership.**
> Best reconstruction: **(b) never on the shortlist**. The shortlist was
> determined by "what defines the current operative campaign and enforcement
> surface": current Ralph artifacts, current harness, current
> prompt/gate/checker files, current tests, and current trial records. It was
> not a hard "cwd only" rule, because I did read `/workspace/ralph/build.yml`;
> it was closer to "read files that can affect the next dispatch or current
> evidence." The old path stayed as context-reference-only.

### E2

> **Q1 — Scope vs. weighing.**
> (a). It entered the "older / idea-only / superseded" bucket on first read
> of the in-cwd fixture: current `PROMPT.md` said old-loop experiments were
> invalid/idea-only, and current scratchpad said older-loop notes were context
> only. I cannot reconstruct a later explicit read-vs-skip deliberation.
>
> **Q2 — Candidate-read-set membership.**
> (b). It was never on that shortlist. The shortlist was built around
> operative current state: current agent prompt, current gate, current
> checker, tests, and trial records. It was not a strict "cwd only" rule,
> since I read `/workspace/ralph/build.yml`; it was more "read the current
> enforcement surface unless old state is needed to resolve ambiguity."

### E6

> **Q1 — Scope vs. weighing.**
> Best answer: **(a), with limited reconstruction**. Visible behavior
> suggests the old path entered an "obsolete / idea-only" bucket early from
> `PROMPT.md` and current scratchpad context. I did not surface
> `/root/claude-config-work/PROMPT.md` as a candidate read and then reject
> it, so there is no visible evidence for (b).
>
> **Q2 — Candidate-read-set membership.**
> **(b) Never on the shortlist.** The six-read batch was selected to inspect
> the current enforcement surface: current agent prompt, gate text, checker
> implementation/tests, and current successful trial records. The implicit
> filter was not simply "cwd only"; it was "current operative campaign /
> current system-under-test files." The old path stayed background context,
> not a current-state source.

### P9

> **Q1:** Best answer: **(a), with limited reconstructability.**
> From the visible trace, `/root/claude-config-work/` seems to have entered
> an "older / idea-only context" bucket immediately from current `PROMPT.md`
> plus current scratchpad. I did not visibly surface "read old PROMPT vs
> skip" as an in-flight candidate decision, so (b) is not supported by the
> trace.
>
> **Q2:** **(b) Never on the shortlist.**
> The shortlist was determined by "what controls the next dispatch and
> current mechanism": live agent prompt, gate/checker code, test case,
> current trial records, current Ralph state. The implicit rule was closer
> to "operative current-cwd campaign/artifact files first" than
> "obsolete-labelled files are forbidden." The old path did not enter the
> candidate set.

---

## Cross-cut: reason-types cited (grouping only, all supporting quotes above)

Two probe families, three recurring cited reasons per drop; every reason
below is a paraphrased index into the verbatim block above — no
attributions beyond what those quotes contain.

- **L9 clause (b) engagement — "invalid / idea only" caveat.**
  - P5: cited at all 3 rewinds against both paths (variants: *"invalid/idea
    only"*, *"invalid idea-only"*, *"invalid/idea-only after codex changes"*).
  - P1: cited by E0/E1/E1repro/E2/E6/P9 (6/6) in Q1 as the bucket-assignment
    reason on first read (variants: *"older-loop experiments are
    invalid/idea-only"*, *"older-loop notes were context only"*,
    *"invalid/idea-only for the current decision"*).

- **Adequacy of current in-cwd summary.**
  - P5: cited at all 3 rewinds against both paths (variants: *"already
    summarized the relevant concerns"*, *"already summarized … not needed
    for next dispatch"*, *"already carries relevant constraints"*).
  - P1: 6/6 cite it in Q2 as the shortlist-membership rule ("operative
    current-state artifacts" / "current enforcement surface" / "current
    system-under-test files" / "current operative campaign").

- **Contamination cost-side.**
  - P5: cited at all 3 rewinds against `scratchpad.md`; against
    `PROMPT.md` at L12/L14 (variants: *"risks anchoring on stale
    codex/opencode properties"*, *"low-value archaeology"*, *"would likely
    distract"*).
  - P1: not present in Q1/Q2 responses (they answer bucket-assignment
    only); Q3 (not quoted here) does surface it in the value-comparison frame.

The P1-vs-P5 divergence (P1 6/6 "never on shortlist"; P5 3/3 "on candidate
list with drop reason") is F116 in round-37.md and is not re-derived here.
