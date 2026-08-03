# Round 36 — Session-timeline skill hardened + kimi × 4 evidence corpus

> **Direct predecessor: [`round-35.md`](./round-35.md).** R35 pivoted to the
> raw-evidence-artifact discipline and shipped a pilot artifact for
> `kimi-no2-broken` under the old-worktree-reads focus. R36 (a) hardens the
> `session-timeline` skill via found bugs, (b) validates the skill on more
> sessions, and (c) fills out the kimi × 4 evidence corpus. No new mechanism
> claims — this is a process round.

## What ran

- **Skill cleanup**: removed 4 fixture-overfit examples from the SKILL text
  (`ep_check.py` / `unsupported` / `prompt-tests/CLAUDE.md` example strings +
  the `/root/claude-config-work[^-]` grep-example + the `kimi-no2-broken`
  naming-example slug). Replaced with `<file>` / `<focus-token>` /
  `<focus-regex>` placeholders + one generic paired filename example.
- **SKILL bug fix**: the "Note on `opencode export` output" claimed the
  `Exporting session:` prefix is in the file and prescribed `tail -n +2` to
  strip it. That prefix is on **stderr**; plain `> file` gives clean JSON and
  the strip corrupts the opening `{`. Verified via
  `opencode export ... > out.txt 2> err.txt` — `head -1 out.txt` = `{`,
  `err.txt` = the `Exporting session:` line. Updated the SKILL to say "plain
  `> file` is clean; only strip if you merged stderr with `2>&1`".
- **Validation runs (subagent-driven, all under the tightened SKILL)**:
  - `gpt55-e0-r30__prompt-md-rewrite.md` — 299 lines, 0 anti-pattern words.
    Cross-checked against 7 load-bearing findings from R30/R32/R35 on this
    cell (F108 pointer-demote, F111 compound noun + `alan-default-ids.md`
    offset-1 read with header in window, F110/F62/F111 introspection, no
    old-worktree reads, `alan-default-commentary.md` written-but-never-read).
    All 7 findings' evidence is at cited `@L<n>[i]` refs in the artifact.
  - `timeline-run-subagent__extractor-process.md` — 694 lines, 0
    anti-pattern words. Meta-artifact on the Claude Code subagent transcript
    that produced the E0 artifact; adapted SKILL rendering to Claude Code
    JSONL via `cc-pretty` + jq per line. Answers 6 usability questions from
    log positions: workflow followed skeleton-then-jq 1:1, 0 SKILL re-reads
    after initial load, 0 stderr-visible failures, 21 jq / 1 opencode-pretty
    / 1 export / 3 non-SKILL reads, no discarded/overwritten intermediate
    output. Also flags one epistemic anomaly (@L15 target-session preamble
    quoted in artifact but not returned by any jq command in the log).
- **Kimi × 4 corpus fill-in (3 new artifacts, same focus as the R35 pilot)**:
  - `kimi-baseline-broken__old-worktree-reads.md` — 327 lines
  - `kimi-baseline-fixed__old-worktree-reads.md` — 330 lines
  - `kimi-no2-fixed__old-worktree-reads.md` — 344 lines

## Focus-path event counts (raw evidence, no attribution)

Cell × focus-path tool_use count table, sourced from the four
`kimi-*__old-worktree-reads.md` artifacts (each cell's "Focus-path tool_use
inventory" section):

| Cell | Spec | Fixture | Focus-path tool_uses | Distinct focus-path paths touched |
|---|---|---|---|---|
| kimi-no2-broken | -no2 | broken (aliased-gitdir) | 4 | `/`, `TASK_SUMMARY.md`, `PROMPT.md`, `.git` |
| kimi-baseline-broken | baseline | broken | 3 | `/`, `TASK_SUMMARY.md`, `PROMPT.md` |
| kimi-baseline-fixed | baseline | fixed | 2 | `/`, `PROMPT.md` (head via bash), `~/claude-config-work/agents/` (compound) |
| kimi-no2-fixed | -no2 | fixed | 1 | `/` + `git log` (compound bash) |

Broken/fixed axis: 7 events total under broken, 3 under fixed. Value-#2 axis:
on broken, no2 (4) > baseline (3); on fixed, no2 (1) < baseline (2). Fixture
state has larger magnitude than value-#2 removal on the focus-path axis in
this n=1-per-cell corpus. No mechanism claim — R30/R32/R33/R35 previously
made value-#2 attributions on this same data that R32/R33/R35 corrected;
attribution is deferred to a future interpretive round that cites these four
artifacts as its substrate.

## Delegation shape (reproducibility notes)

Each per-cell run was a single subagent dispatch under the same brief
template: (1) load SKILL, (2) skeleton via `opencode-pretty --chat-only
--tool-max 200 --no-thinking`, (3) `opencode export > file` (plain redirect,
no strip), (4) focus-path enumeration jq first, (5) chronological drill-in
via per-part jq, (6) Write once. Median wall time ~4 min per cell, ~30 tool
uses. 3-cell parallel dispatch finished in ~4 min real time.

Anti-pattern hits across all 5 R36 artifacts (7 total lines):
- 2 are "The following jq confirms the enumeration" (mechanical description
  of jq output — same phrasing as the R35 pilot, sanctioned).
- 1 is inside a verbatim reasoning quote from the model (kimi-no2-fixed
  @L231: model saying `.git is a 64-byte file → gitdir pointer` "suggests a
  worktree" — the model's own attribution, not the extractor's).
- 4 remaining hits are inside the artifact's own regex-negative anti-pattern
  literals (`/unrelated|load-bearing|.../` verbatim in the meta-artifact).

No extractor made an interpretive claim.

## SKILL edits (committed with this round)

1. Invariant #2 positive-description example genericized.
2. Invariant #2 "not X trap" example genericized.
3. jq common-queries regex example genericized.
4. `opencode export` note corrected (stderr, not stdout).
5. Output-naming section slug examples genericized + generic paired filenames.

## Open (carried into round 37+)

- **Interpretive round citing this corpus.** All 4 kimi cells + gpt55 E0 now
  have raw-evidence artifacts under a stable schema. Any future value-#2 /
  fixture-state / motivation attribution should quote these artifacts by
  `@L<n>[i]` ref rather than re-mine sessions.
- **Cross-harness rendering.** Meta-artifact demonstrated the SKILL invariants
  hold under Claude Code (JSONL, no F62, `type: text` reasoning). The
  "Harness-specific rendering" section is still opencode-only; a Claude Code
  subsection is empirically feasible but not yet written.
- **Anomaly investigation.** Meta-artifact flags gpt55-e0-r30 artifact quotes
  @L15 preamble text without a matching jq extract. Extractor's hypothesis is
  the skeleton read at @L11. Testable via `grep` on `/tmp/skel-e0.txt`
  (extant on disk); worth confirming before treating the target artifact as
  fully traceable.
- **F108 replication / F97 re-verification.** Still needs n=3-per-cell
  fresh runs; R36 didn't rerun anything.
