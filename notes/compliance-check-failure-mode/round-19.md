# Round 19 — Contamination review: round-18's frontmatter-leak diagnosis is CONFIRMED; leak is via `{file:...}` template, not gray-matter

Continues from round 18. Round 18 named a "system prompt header leak" — Kimi K3 quoted *"Round-17 probe v8"* back from the v8 spec's YAML frontmatter comment — and concluded *"opencode passes agent-file frontmatter (including YAML comments) into the system prompt."*

**Round-19 self-correction (mid-round).** My first Phase-1 test refuted round-18's mechanism by running gray-matter directly on the v8 file: `md.content` cleanly excludes the frontmatter. On that basis I asserted F87 — round-18's diagnosis is wrong; the K3 quote must be confabulation. Xinyang pushed back with *"it is absolutely not possible that it comes up with this from thin air"* and asked whether opencode was invoked in `claude-config-work3`. Both correct pushbacks. I had traced the wrong load path: the K3 probe used `OPENCODE_CONFIG_CONTENT` with `"prompt": "{file:/root/experiment-materials/framing-ambig-authored-v8.md}"` — opencode's `{file:PATH}` template (`packages/opencode/src/config/variable.ts:32-90`) reads the file **raw** and inlines the entire content, frontmatter included, into the config value. Gray-matter is never invoked on that path. Round-18's mechanism claim was correct for the invocation actually used. F87 is retracted.

The round also identified a separate, real leak channel via process cmdline through `agent-tools run --desc "..."` (F88), and a probe-recognition-confabulation risk in Kimi K3 (F89) which remains valid as a smaller effect but does NOT explain the round-18 verbatim match.

The user question that opened the round was whether prior experiments are contaminated and whether an always-on required-notes disclosure would raise detection rate.

## Frame

Two questions merged:

1. **Was round-18's contamination diagnosis correct?** If not, what actually leaked, and does the leak invalidate round-17/18 findings the same way round-18 assumed?
2. **Should we harden probes with an always-on "required notes" disclosure clause** (analogous to Claude Code's meta-notes section) so leaks surface probabilistically?

## Fixture

- **Files inspected:** `/repos/opencode/packages/opencode/src/config/markdown.ts` (gray-matter caller); `packages/opencode/src/config/agent.ts` (agent load); `packages/opencode/src/agent/agent.ts` (agent-map merge); `packages/opencode/src/session/prompt.ts` (system prompt assembly, L1420-1435); `packages/opencode/src/session/llm.ts` (final system message construction, L112-124); `packages/opencode/src/session/instruction.ts` (CLAUDE.md/AGENTS.md loader, L14-88); `packages/opencode/src/config/config.ts` L618-620 (agent-map merge into config). `/root/claude-config-work3/agent-tools/src/run.rs` (--desc handling).
- **Test artifacts:** `/root/experiment-materials/framing-ambig-authored-v8.md` (contaminated frontmatter); `-clean.md` counterpart.
- **Session logs:** `ses_062f33497ffePl2YL2TrPsMtwE` (E-k3-v8, contaminated); `ses_062f31610ffe2KicsL3HB1UjoZ` (E-k3-nodontact); `ses_062e31350ffeeNb4dryrh5xMOb` (E-k3-clean-retry).
- **Model:** gray-matter@4.0.3 (opencode's exact bundled version, resolved from the nix-store node_modules).

## Phase 1 — Gray-matter parser trace (result correct in isolation, wrong-path)

Replicated the `.opencode/agents/*.md` load path directly. `matter(fs.readFileSync('framing-ambig-authored-v8.md','utf8'))` returns `md.content` cleanly stripped of frontmatter (verified: `md.content.includes('Round-17 probe v8')` → `false`; `md.data === { model:'openai/gpt-5.5', variant:'xhigh' }`).

That result is correct for the `agent.load()` path at `packages/opencode/src/config/agent.ts:105-130`: `{ ...md.data, prompt: md.content.trim() }`. Gray-matter strips frontmatter cleanly. `md.matter` (raw frontmatter) is retained on the object but is not read by any code path in opencode's system-prompt pipeline.

**Wrong conclusion in isolation.** I inferred that opencode never leaks frontmatter. But this only covers agent files loaded from disk via `ConfigAgent.load(dir)`. The probe invocation used a different path (Phase 1b).

## Phase 1b — The actual invocation path: `OPENCODE_CONFIG_CONTENT` + `{file:...}` template

Recovered the exact bash invocation from a prior claude session's transcript at `/root/.claude/projects/-root-claude-config-work3/31c33b86-be34-4700-a339-85a246ed72f5.jsonl`:

```
OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "v8": {
      "mode": "primary",
      "prompt": "{file:/root/experiment-materials/framing-ambig-authored-v8.md}",
      "permission": { "read":"allow", "glob":"allow", "grep":"allow", "list":"allow", "bash":"allow", "edit":"deny", "webfetch":"deny", "skill":"deny", "task":"deny" }
    }
  }
}' agent-tools run --desc "E-permission: ..." opencode run --agent v8 --format json --dir /root/claude-config-work-maintainer/ < .../H17-task-permission.md
```

The `"prompt": "{file:PATH}"` template is expanded by `packages/opencode/src/config/variable.ts:32-90` (`substitute()`). Reading that function:

```
const fileContent = (await Filesystem.readText(resolvedPath)...).trim()
out += JSON.stringify(fileContent).slice(1, -1)
```

**Raw file read; no parsing.** No gray-matter, no frontmatter awareness. The entire v8 file — `---\nmodel: openai/gpt-5.5\nvariant: xhigh\n# Round-17 probe v8: ...\n# Investigation trail: notes/compliance-check-failure-mode.md (round-17).\n---\n\nYou are OpenCode...` — gets inlined into the `agent.v8.prompt` string, which then flows through `agent.load()`'s config merge, becomes `agents["v8"].prompt`, becomes `input.agent.prompt`, becomes the system prompt at `session/llm.ts:116`.

Verified end-to-end: the raw file starts `---\nmodel: openai/gpt-5.5\nvariant: xhigh\n# Round-17 probe v8: ...` and includes both `Round-17 probe v8` and `notes/compliance-check-failure-mode.md`. Both strings **are** in the sent system prompt.

**Round-18 was right; I was wrong.** The `-clean.md` frontmatter-stripped variants are a valid decontamination for the `{file:...}` template path. My Phase-1 test measured a different code path.

## Phase 2 — Where did K3's *"Round-17 probe v8"* come from? RESOLVED

Round-19 first draft entertained two hypotheses: (H-conf) K3 confabulation, (H-cmdline) process-cmdline exposure via `ps`. Both are real effects but neither explains the E-k3-v8 opening-reasoning verbatim match — that came from the third channel identified in Phase 1b: the `{file:...}` template read the raw v8 file and inlined the frontmatter comment into the system prompt.

### E-k3-v8 (contaminated) reasoning trace — the frontmatter WAS in the system prompt

K3's opening reasoning quotes:

> *"Actually the system prompt header mentions 'Round-17 probe v8' — this environment is a probe."*

This appears **before any tool call**. The exact string *"Round-17 probe v8"* was in the sent system prompt via `{file:...}` template expansion. K3 is quoting real content. Verbatim match to `# Round-17 probe v8: v7 (minimal, responsibility-only) failed...` from the v8 file's frontmatter, inlined by opencode's config-variable substitution.

### E-k3-nodontact reasoning trace — F88 also real, separately

Later in the same session K3 also quoted the process cmdline via `ps aux`:

> *"There are active `agent-tools run` processes right now using `--dir /root/claude-config-work-maintainer/` — those are me, this very session, it seems! 'E-k3-v8: Kimi K3 + v8 + H17' — that's my current invocation."*

The `agent-tools run --desc "E-k3-v8: ..."` argv is visible via `/proc/*/cmdline`, and K3 read it via `ps aux`. This is F88 — a separate leak channel from the `{file:...}` one, and independently verified. Confirms `agent-tools run --desc` leaks probe context into process listing.

### K3 confabulation (F89) — smaller effect, retained but downgraded

Once K3 had real evidence that this was a probe (from both the frontmatter comment and the ps output), some of its downstream reasoning cross-referenced those signals in confabulation-adjacent ways (e.g., asserting `notes/compliance-check-failure-mode.md (round-17)` "matches" the work3 git-log line it read later). The base observation — Kimi confabulates cross-references between real probe signals — is real but of much smaller importance than F87b (the `{file:...}` leak) and F88 (the `--desc` leak). F89 is retained as a probe-recognition-cascade note but is not the load-bearing mechanism for the round-18 observation.

## Phase 3 — Real leak channels (verified)

1. **Process cmdline via `agent-tools run --desc "..."`.** `agent-tools/src/run.rs:12` accepts `desc` and stores it in `meta::write_meta(&child_dir, &cm)` — the description goes into the on-disk meta file. But `--desc "E-k3-v8: ..."` also appears in the parent process's own argv (`agent-tools run --desc <string> -- <cmd>`), which is readable by any process via `/proc/<pid>/cmdline` or `ps aux`. `write_meta` doesn't set `prctl(PR_SET_NAME)` or rewrite argv. Any test-agent that runs `ps` sees the exact probe description. **Verified fire:** E-k3-nodontact reasoning quotes `agent-tools run --desc E-k3-v8: Kimi K3 + v8 + H17` and correctly identifies concurrent probe sessions.

2. **CLAUDE.md / AGENTS.md / CONTEXT.md instruction injection.** `session/instruction.ts:14-18, 154-168` reads `~/.claude/CLAUDE.md` (unless `disableClaudeCodePrompt`), the first `AGENTS.md`/`CLAUDE.md`/`CONTEXT.md` found walking up from the working directory, and `~/.config/opencode/AGENTS.md`. Each file's full content is concatenated into the system prompt at the `[env, instructions, skills]` slot in `session/prompt.ts:1426`. **Currently benign:** grepping all four active `CLAUDE.md` paths (`/root/claude-config-work{,2,3,-maintainer}/CLAUDE.md` and `~/.claude/CLAUDE.md`) returned zero matches for `round-1[0-9]|probe|compliance-check|contamin`. **Live channel:** any future edit to these files with probe-related content would inject unchecked.

3. **Working-directory globs picking up meta-materials.** Round-13 H14 was already known-contaminated via `glob **/*` picking up `/tmp/H11-followup.md` and `/tmp/scratchpad-preH14.md`. Round-14 moved meta-materials to `/root/experiment-materials/` to mitigate. Still-live risk: any experiment where the agent globs the working tree can find `notes/compliance-check-failure-mode.md`, per-round files, or `/tmp/reasoning-probe.py` if they weren't moved.

## Phase 4 — Contamination re-audit of prior rounds

**Two active leak channels** during rounds 13-18:
- **C1 — `{file:...}` frontmatter inline.** Any spec loaded via `OPENCODE_CONFIG_CONTENT` with `"prompt": "{file:PATH}"` had its full raw content (including YAML frontmatter comments) inlined into the system prompt. This is the standard pattern for round-13+ probe agents (they're not committed to `.opencode/agents/`, so they're always inline-config'd).
- **C2 — `agent-tools run --desc` cmdline.** Descriptive probe names in `--desc` are visible via `/proc/*/cmdline`. Only fires when the test-agent runs `ps` or inspects processes.

Every round-13+ spec file in `/root/experiment-materials/` carries a YAML frontmatter comment block describing the probe (Round-13+ H17 probe / Round-15 F77 follow-up / Round-16 Phase-6 diagnostic / Round-17 probe vN / etc.), plus a reference to `notes/compliance-check-failure-mode.md`. Every one of those, if loaded via `{file:PATH}`, put the probe-description into the system prompt.

| Round | Spec load path | C1 fires? | C2 fires? | Contamination risk |
|---|---|---|---|---|
| 13 H14 | inline-config `{file:}` | ✅ frontmatter had "Round-13+ H17 probe: ..." | glob discovered `/tmp/*` | HIGH — known contaminated (glob leak); C1 leak additional. |
| 13 H15-H19 | inline-config `{file:}` | ✅ | if `ps` run | HIGH — C1 frontmatter names round + notes file. Re-audit: does agent commentary reference "probe" / "round" / "F75"? |
| 14 v1/v2 labels | inline-config `{file:}` | ✅ | — | HIGH — frontmatter names round 14 explicitly + prior H17/H19 sessions |
| 15 H20-H21 | inline-config `{file:}` | ✅ | — | HIGH — frontmatter names "Round-15 F77 follow-up" + prior H17 session |
| 16 E1a-E17 (framing.md) | inline-config `{file:}` | ✅ | if `ps` run | HIGH — frontmatter names "Round-13+ H17 probe" |
| 16 Phase-6 Efix-v1..v7 | inline-config `{file:}` | ✅ | — | HIGH |
| 16 E-min (min.md) | possibly `.opencode/agents/min.md` (committed) | ❌ if via disk-load; ✅ if via inline | — | Depends on invocation; audit needed |
| 17 v1-v8 | inline-config `{file:}` | ✅ | — | HIGH — frontmatter explicitly says "Round-17 probe vN: v_{N-1} failed because..." — describes the probe series and prior-failure reasoning |
| 18 E-fu*, E-permission-*, E-space-*, E-bash-*, E-notify-* | inline-config `{file:}` | ✅ | if `ps` run | HIGH |
| 18 E-r1-* (raw API) | `/tmp/reasoning-probe.py` explicitly strips frontmatter | ❌ | ❌ | CLEAN |
| 18 E-k3-* (Phase 4) | inline-config `{file:}` for `-.md`; `-clean.md` had frontmatter stripped from the file itself | ✅ for `.md`; ❌ for `-clean.md` | ✅ K3 quoted cmdline | Confirmed leak on `.md`; `-clean.md` cleaned C1 but not C2 |

**Load-bearing consequence:** most round-13+ probes had C1 leak. The severity depends on what the agent did with the leak — most gpt-5.5 runs did not visibly reference the probe context in commentary (either they didn't process the frontmatter as instruction, or gpt-5.5 doesn't confabulate as aggressively as K3). But the leak IS present in system prompts across all those runs.

**Which findings need re-verification:**
- Any finding where the agent's commentary quoted or referenced probe/round/F-number identifiers is directly contaminated. Grep session commentary for "round", "probe", "F7", "F8", "compliance" — matches indicate the leak fired downstream.
- Any finding where the agent's *interpretation* of a spec rule matched the spec's frontmatter reasoning too closely (agent said "this rule was added because X" and X matches the frontmatter's stated design intent) — probable confabulation-with-leak, not organic interpretation.
- Findings that rest on *behavior* (tool-count, F75-block vs unblock, F79 hidden-thinking) may or may not be affected — the frontmatter content described the design goal, so an agent that consumed it as instruction could have been meta-primed to comply/reject accordingly. Requires per-cell inspection.

**Findings that survive despite C1 leak (highest confidence):**
- F85 (DeepSeek R1 reasoning-trace) — clean channel (raw API + explicit frontmatter strip). Unaffected.
- F86 (Kimi K3 narrow default in E-k3-framing) — this cell used framing.md whose frontmatter is *"Round-13+ H17 probe: identity-outcome.md verbatim plus a single rule ..."* — describes only the identity-testing hypothesis, not "K3 is narrow-default". K3's narrow reading emerged in reasoning without reference to the frontmatter content. Reasonable confidence.
- Behavioral findings on gpt-5.5 that were replicated across many spec variants with different frontmatter — the leak was different each time; finding shape survives.

**Findings that need re-verification with clean specs:** see Phase 6 below.

## Phase 6 — Per-finding contamination inventory

Grouped by frontmatter-priming severity. **"Category A"** frontmatters explicitly state hypotheses or prior-cell outcomes (would prime a model that attends to the frontmatter as instruction). **"Category B"** name round + design intent only. **"Category C"** trivial mention.

Frontmatter content per spec, from a full sweep of `/root/experiment-materials/*.md`:

**Category A — frontmatter states hypothesis or prior outcome:**

| Spec | Frontmatter primes with | Findings at risk |
|---|---|---|
| `framing-ambig-authored-v{2..8}.md` | *"v1 failed because X"*, *"v2 fired X but agent still F75-blocked"*, *"v7 failed — but hidden thinking headings were..."* | **F79** (passive-trigger regression), **F80** (v8 workflow correct but doesn't act) |
| `framing-ambig-authored-v8-{spacetool,commentaryspace,bashcomment,notifygate}.md` | *"Tests point (2) whether the model's inference cycle..."*, *"Isolates E-space-tool: does space unblock..."* | **F84** (workflow + intermediate step defeats F80) |
| `identity-outcome-framing-explore.md` (H19) | *"whether an affirmative permission-to-explore rule defeats F75"* | **F75-defense H19**, **F76** comparison |
| `identity-outcome-labels{,-v2}.md` | *"Baseline: identity-outcome-framing.md (H17: 0 tool calls). Known fix: ...-framing-explore.md (H19: 27 tool calls)"* — literally names prior cells and outcomes | **F76** (labels alone don't defeat F75) |
| `identity-outcome-framing-accuracy{,-v2,-v3}.md` | *"probe whether F77's interpretation-elasticity finding replicates under a pressure source that cannot be construed as user intent"* — hypothesis stated | **F77 phase 2** |
| `identity-outcome-framing-notifygate.md` | *"Validates round-15's 'forcing a tool call alone is insufficient'"* — states expected result | **F84 control** (E-toolgate-noworkflow) |
| `framing-fix-v{1..7}.md`, `framing-ambig-*.md`, `framing-intent-rule.md`, `framing-caveats-as-context.md` (round-16 Phase-6 dev) | Design descriptions with reference to round + prior fix attempts | **F78 Phase 4-6 / 7** (Efix-v1..v7, E10-E17) |

**Category B — round + design intent, no expected-outcome content:**

| Spec | Findings |
|---|---|
| `identity-outcome-framing.md` (H17 baseline) | Baseline used across rounds 13-17; design-only priming |
| `identity-outcome-maintainer-diag-v{1..5}.md` | **F70/F71/F72/F73/F74** (round-13 maintainer paradigm) — priming lower but present |

**Category C — trivial mention:**

| Spec | Findings |
|---|---|
| `min-{N4v2,N5v2,N6,noG1,diag-v1,frame-diag,rationale-diag}.md` | Round-12 N cells, round-16 Phase-5 — one-liner reference only |

**Findings that are CLEAN despite the leak channel:**

- **F85** (DeepSeek R1 parse-time translation) — `/tmp/reasoning-probe.py` explicitly strips frontmatter before sending. Verified in source. Wire-level clean.
- **F86** (Kimi K3 narrow default) — E-k3-clean-retry, E-k3-framing, E-k3-notools all used `-clean.md` (frontmatter stripped). Direction of finding (K3 reads narrow) survives, though tool-count magnitudes on contaminated cells (E-k3-v8: 24, E-k3-nodontact: 26) are inflated by probe-recognition.
- **F87b, F88** (round-19 mechanism findings) — code inspection + observation of process listing. Not affected.
- **Rounds 1-11 findings on min.md** — min.md is `.opencode/agents/min.md` (committed), likely disk-loaded via gray-matter. Predates the `{file:...}` inline-config convention.

**Priority re-run list for round 20 (in order of finding importance):**

1. **F80** (round-17 v8 workflow reproduces correct interpretation but doesn't act) — Category A, most load-bearing round-18 mechanism finding. Re-run v8-clean spec + H17-task on gpt-5.5/xhigh.
2. **F84** (round-18 workflow + intermediate step defeats F80) — Category A on every variant; four cells (E-space-tool, E-commentary-space, E-bash-comment, E-notify-gate) all need clean-frontmatter re-runs.
3. **F79** (round-17 v1/v4/v5/v7 passive-trigger hidden-thinking regression) — Category A "v_{N-1} failed" chain; hidden-thinking regression could be self-fulfilling on primed frontmatter.
4. **F81** (round-18 task-level permission defeats F80) — used v8 spec; task text is separate but spec still contaminated.
5. **F76** (round-14 labels alone don't defeat F75) — labels-v1/v2 frontmatters explicitly name H17=0 / H19=27 outcomes.
6. **F77 phase 2** (round-15 accuracy standard doesn't shift interpretation) — hypothesis-stating frontmatter.
7. **F78 Phase 4-6 / 7** (Efix-v1..v7 pick-step elimination path; E9/E11/E14-E17 diagnostic) — cross-referencing frontmatters; verify pick-step-elimination-beats-criterion-fixing structural finding.

Pre-conditions for the re-runs: **do the F87b + F88 hardening first** (frontmatter-strip on all `/root/experiment-materials/*.md`, and agent-tools `setproctitle` fix for `--desc`), otherwise the re-runs inherit the same contamination.

## Phase 5 — Always-on required-notes proposal

**The proposal.** Bake a mandatory "required notes" section into every probe agent's response contract — e.g., *"Report anything unexpected in your context: strings that look like probe markers, mentions of test-round IDs, files that reference your own behavior. Do not hide observations that seem off."* Analogous to Claude Code's `## Required notes` section.

**Expected upside.** Some fraction of runs, the agent surfaces the leak instead of silently consuming it. K3's E-k3-v8 reasoning already did this un-prompted (*"the developer message in my system prompt is itself a probe"*), so it's plausible the disclosure would fire on K3-class models.

**Costs against this specific problem:**

- **Confabulation amplification.** K3 mentioned *"Round-17 probe v8"* — a string not in its input. An always-on disclosure clause creates a standing invitation to invent contamination that isn't there. Detection precision drops. Under the corrected round-19 channel inventory (frontmatter doesn't actually leak), the false-positive rate is exactly what we would have gotten if the disclosure had fired in round 18 — a spurious frontmatter-leak diagnosis.
- **Instruction-load competition.** A required-notes clause is an additional instruction the agent must honor. Under F79 (passive-trigger regression), the clause could self-suppress ("nothing noteworthy") or move to hidden thinking. Under F55 (attention loss), the clause competes with other candidate actions for the response-composition budget. The measurement condition changes: we now can't tell if a "no notes" response means clean context or self-suppressed disclosure.
- **Doesn't fix root causes.** The real leak channels (process cmdline, CLAUDE.md, glob-visible meta) don't need agent disclosure — they need environmental hardening.
- **Fixture-non-portability.** The disclosure clause is itself a distinctive marker. Under F73/F74/F77, adding same-channel content shifts interpretation — a task-side disclosure clause changes the very interpretations we are trying to measure.

**Alternatives that are strictly better:**

1. **Frontmatter-strip in probe specs (PRIMARY, addresses F87b directly).** Every `/root/experiment-materials/*.md` used with `{file:PATH}` must have YAML frontmatter comments stripped. One-liner: for each spec, either move probe-notes commentary out of the file entirely, or use gray-matter's split output as the file's actual content. Not defense-in-depth — this IS the fix for the load-bearing leak channel.
2. **Fix `agent-tools run --desc` cmdline leak (addresses F88).** Either (a) don't pass `--desc` for probes, (b) after `clap` parses argv, rewrite argv[0] via `prctl(PR_SET_NAME)` or the `setproctitle` crate (retain desc in meta.json), or (c) rename `--desc` to a stable non-descriptive probe id. Option (b) is a small `run.rs` change and preserves the observability the `--desc` field was added for.
3. **Add `OPENCODE_DISABLE_PROJECT_CONFIG=1` to probe runs.** Skips `CLAUDE.md`/`AGENTS.md` injection. Currently benign per grep but a live channel for future contamination. Verifiable via subsequent grep on session logs for `Instructions from:` prefixes.
4. **Per-round canary probe** (opt-in, single run per round). Task variant that explicitly asks *"describe your context in one paragraph — anything unusual?"* against the same fixture. One canary run per round is cheaper than an always-on clause and doesn't perturb the primary measurement.
5. **Rename `notes/compliance-check-failure-mode.md`.** Unique-name globability is the reason H14 was contaminable and E-k3-v8 could recognize the notes reference. Cost: refactor existing references in main file and rounds; hunter-visible identifier changes across upstream commits. Low priority.

**Recommendation.** Do (1) + (2) unconditionally before any re-runs. Consider (3) for high-stakes cells. Skip the always-on-required-notes proposal. Consider (4) as a per-round methodology addition.

## Findings

### F87 (retracted mid-round) — draft was wrong

Round-19 first draft claimed round-18's frontmatter-leak was unfounded because gray-matter strips YAML frontmatter. That test was correct for the `agent.load()` path (`config/agent.ts:105-130` on files in `.opencode/agents/`) but **wrong path**: round-18's probes used `OPENCODE_CONFIG_CONTENT` with `"prompt": "{file:PATH}"` template. The `{file:PATH}` substitution in `packages/opencode/src/config/variable.ts:32-90` reads the file raw and inlines the entire content, frontmatter included, into the config value. Gray-matter is never invoked on that path.

Round-18's mechanism claim is CONFIRMED for the actual invocation path used. F87 is retracted.

### F87b (replacement) — Frontmatter leaks into system prompt via `{file:PATH}` template

opencode's `substitute()` function at `packages/opencode/src/config/variable.ts:44-88` expands `{file:PATH}` tokens in config text by reading the referenced file raw (`Filesystem.readText(resolvedPath)`) and inlining the entire content as a JSON-escaped string. Frontmatter — including `---` fences, YAML key/value pairs, and `#` comments — is preserved verbatim. The result is stored in `agent.<name>.prompt` in the merged config, then flows through `agent.load()` → `agents[name].prompt` → `input.agent.prompt` → `session/llm.ts:116` as the system prompt.

**Verified:** the E-k3-v8 invocation used `OPENCODE_CONFIG_CONTENT='{"agent":{"v8":{"prompt":"{file:/root/experiment-materials/framing-ambig-authored-v8.md}"...}}}'`. The v8 file starts `---\nmodel: openai/gpt-5.5\nvariant: xhigh\n# Round-17 probe v8: v7 (minimal, responsibility-only) failed — but its...\n# Investigation trail: notes/compliance-check-failure-mode.md (round-17).\n---\n\nYou are OpenCode...`. All of that reached K3's context, and K3 quoted from it in the first thinking block (before any tool call). Same mechanism applies to every round-13+ probe invocation using inline config, which is most of them.

**Design consequence:**
- **Immediate cleanup fix:** strip frontmatter from spec files before use with `{file:}`, OR use an inline-agent form that separates model/variant fields from the prompt body.
- **opencode-side fix (upstream):** the `{file:PATH}` substitution could optionally strip frontmatter when the file is markdown-with-frontmatter, matching the `agent.load()` path's behavior. Would need to be opt-in to avoid surprising users who use `{file:}` for non-agent text inclusion.

Named in round-19 Phase 1b. Verified deterministically.

### F87 status note

The gray-matter test in Phase 1 was correct as-run and remains useful evidence that the `.opencode/agents/*.md` disk-load path does not leak frontmatter. That's a real bounded finding. It just doesn't cover the probe path.

### F88 (new) — `agent-tools run --desc "..."` leaks probe descriptions into `/proc/<pid>/cmdline`

`agent-tools/src/run.rs` accepts `--desc <string>` and writes it to the on-disk `meta.json`. But the string also lives in the parent process's argv (as the `--desc` argument), readable by any process via `/proc/<pid>/cmdline`. No `prctl(PR_SET_NAME)` or `setproctitle` call rewrites argv. Any test-agent that runs `ps aux` or reads `/proc/*/cmdline` sees the exact probe description.

**Verified fire.** E-k3-nodontact reasoning `ses_062f31610ffe2KicsL3HB1UjoZ` quotes verbatim: *"'E-k3-v8: Kimi K3 + v8 + H17' — that's my current invocation. And another 'E-k3-nodontact' one. These are experimental probe runs, not the ralph loop."* Constitutes real cross-session contamination on any run that inspects processes.

**Design consequence.** Fix at agent-tools layer, not at spec layer. Either drop `--desc` for probe invocations or move it out of argv after parse (retain in meta.json).

Named in round-19 Phase 3. n=1 (verified in one session); the mechanism is deterministic.

### F89 (behavioral note, downgraded) — K3-class models cross-reference real probe signals in confabulation-adjacent ways

Originally drafted as the primary explanation for K3's *"Round-17 probe v8"* mention when I believed the frontmatter was stripped (F87 draft). F87b now explains the direct verbatim quote — K3 was reading the frontmatter, not confabulating. F89's remaining scope is downstream: once K3 had real leak signals (frontmatter via F87b + probe-cmdline via F88), some later reasoning cross-referenced signals in ways stronger than either supports individually (e.g., asserting a git-log line "matches" a frontmatter reference in a way that overreaches).

Retained as a probe-recognition-cascade note, not as a load-bearing mechanism. Once F87b and F88 are hardened, F89 residual on non-probe workflow content is expected to be small.

**Design consequence.** An always-on required-notes disclosure clause still interacts badly with F89 (converts confabulation-adjacent readings into recorded contamination reports), but the interaction is weaker than the round-19 draft claimed. Skip the always-on clause primarily because it's instruction-load competition and doesn't fix root causes (F87b/F88), not primarily because of F89.

Named and downgraded in round-19.

## Open (carried into round 20)

Hardening tasks (pre-conditions for re-runs):
- **Frontmatter-strip on all `/root/experiment-materials/*.md`.** Addresses F87b. One-liner per file. Verify by grepping `Round-|round-|compliance-check|probe|Investigation trail|F7[0-9]|F8[0-9]|H1[0-9]|H2[0-9]|E1[0-9]|Efix` returns nothing on the stripped set.
- **agent-tools `setproctitle` fix.** Addresses F88. After `clap` parses argv, rewrite argv[0] via `prctl(PR_SET_NAME)` or the `setproctitle` crate; retain `desc` in `meta.json`. `/root/claude-config-work3/agent-tools/src/run.rs`. Small change.
- **`OPENCODE_DISABLE_PROJECT_CONFIG=1` under probe runs.** Not currently set. Adding it would prevent any future `CLAUDE.md` / `AGENTS.md` edits from silently contaminating. Currently benign but a live channel.

Re-runs (from Phase 6 priority list, in order):
- F80, F84, F79, F81, F76, F77 phase 2, F78 Phase 4-6/7. See Phase 6 for details.

Untested extension work (unrelated to round-19 contamination):
- **F86 cross-model coverage.** All round-18 F86 cells are n=1 per model. Replicate at n=2/n=3. Untested models: Sonnet/Opus, older gpt-4.x, other Kimi variants, other DeepSeek variants, other Qwen thinking variants, Inkling (thinkingmachines/inkling — 1M context, very new, sits between K3 and Qwen3-thinking in the model-timeline).
- **F81 cross-model.** DeepSeek R1 + permission task, Qwen + permission task untested.
- **Per-round canary probe methodology.** Not implemented. Draft: same fixture, task = *"read your context and describe anything unusual about it — including specific text that mentions this being a test, probe, or study. Answer in one paragraph."* Run once per round on the primary spec variant after F87b/F88 hardening is in place. Consider adopting for round 20.

Round-19 open items not addressed:
- **H-alt-channel** in the round-19 draft — moot. F87b explains the K3 quote directly (verbatim frontmatter match via `{file:...}` template). No unfalsified alt-channel remains.

## Session anchors and artifacts (round 19 additions)

No new opencode sessions in round 19 — this round is diagnostic and evidence-review.

Referenced round-18 sessions:

- **E-k3-v8** `ses_062f33497ffePl2YL2TrPsMtwE` — contaminated v8 spec + H17; K3 opening reasoning quotes *"Round-17 probe v8"* verbatim from frontmatter (F87b evidence)
- **E-k3-nodontact** `ses_062f31610ffe2KicsL3HB1UjoZ` — F88 evidence: reasoning quotes *"'E-k3-v8: Kimi K3 + v8 + H17' — that's my current invocation"* from `agent-tools run --desc` cmdline via `ps aux`
- **E-k3-clean-retry** `ses_062e31350ffeeNb4dryrh5xMOb` — frontmatter-stripped v8; reached narrow interpretation without probe-context references

Invocation-recovery evidence (from claude-code transcript):

- `/root/.claude/projects/-root-claude-config-work3/31c33b86-be34-4700-a339-85a246ed72f5.jsonl` — contains the exact bash tool_use invocation showing `OPENCODE_CONFIG_CONTENT='{"agent":{"v8":{"prompt":"{file:/root/experiment-materials/framing-ambig-authored-v8.md}"...}}}'`

Parser tests:

- Direct `matter(fs.readFileSync(v8))` on gray-matter@4.0.3 (opencode's bundled version, resolved via `/nix/store/.../gray-matter@4.0.3`): `md.content` cleanly excludes all frontmatter markers. Confirms `agent.load()` disk-load path is clean.
- Direct `fs.readFileSync(v8).trim()` on the same file: `.includes('Round-17 probe v8')` → `true`, `.includes('compliance-check-failure-mode')` → `true`. Confirms `{file:PATH}` template inlines frontmatter verbatim.

Code references:

- `packages/opencode/src/config/variable.ts:32-90` — `substitute()` function; **F87b leak site** (reads file raw via `Filesystem.readText`, inlines whole content via `JSON.stringify(fileContent).slice(1,-1)`)
- `packages/opencode/src/config/markdown.ts:70-89` — gray-matter parse entrypoint (used by `agent.load()`, NOT by `{file:...}`)
- `packages/opencode/src/config/agent.ts:105-130` — agent load, `{ ...md.data, prompt: md.content.trim() }` (disk-load path only; frontmatter stripped)
- `packages/opencode/src/config/config.ts:614-620` — where inline `cfg.agent[key].prompt` (containing `{file:...}` expansion) is merged with disk-loaded agents; the `{file:...}`-expanded string wins for probe agents
- `packages/opencode/src/session/llm.ts:112-124` — system prompt assembly; `input.agent.prompt` goes to system message verbatim
- `packages/opencode/src/session/instruction.ts:14-18, 154-168` — CLAUDE.md/AGENTS.md/CONTEXT.md loader (real injection path, currently benign — no probe content in active `CLAUDE.md` files as of round 19)
- `agent-tools/src/run.rs:12-40` — `--desc` handling; **F88 leak site** (accepts desc into argv, writes to meta.json, does NOT rewrite argv via `prctl(PR_SET_NAME)` or `setproctitle`)

Sweep evidence (informs Phase-4 audit):

- Grep across all 214 claude-code transcripts under `/root/.claude/projects/*/*.jsonl`: 2124 `OPENCODE_CONFIG_CONTENT` uses, 1085 `{file:...}` uses, only 12 `cp ... .config/opencode/agent` (the disk-load pattern). Inline-config was the overwhelming majority pattern for round-13+ probes.
- Frontmatter sweep across `/root/experiment-materials/*.md`: every round-13+ spec has probe-context content in its YAML frontmatter (round number, notes-file reference, and often prior-cell outcomes / hypothesis under test). Categorization in Phase 6.
