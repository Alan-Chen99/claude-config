# Evidence — ralph iterations 16 & 17: the `.ralph/agent/* ≤ 6000 tokens` budget rule

**Focus (one sentence):** Everything in these two sessions that touches the
`.ralph/agent/* ≤ 6000 tokens` budget rule — how the agent measured it,
interpreted it, complied with it, what it cut, moved, or declined to write
because of it, and what that cost or bought.

Facts only. Refs are `@L<n>[i]` = line `n` of the JSONL, `.message.content[i]`
(`[0]` omitted). Recover with
`sed -n '<n>p' <log> | jq -r '.message.content[i].<leaf>'`.

---

## Provenance

| | Session A | Session B |
| --- | --- | --- |
| Log | `/root/.claude/projects/-root-claude-config-work/8cbdf6ab-6a12-408d-94ce-f4e4519efdd3.jsonl` | `/root/.claude/projects/-root-claude-config-work/cdcc1497-803e-4b57-b94f-fdf533aea762.jsonl` |
| Label in brief | ralph loop iteration 16 | ralph loop iteration 17 |
| Lines / size | 440 lines, 1,471,054 B | 678 lines, 1,925,866 B |
| Model | `claude-opus-5` (1M context), reported by `attach:model` as "Opus 5 (1M context)" | same |
| Harness | Claude Code `2.1.269`, `entrypoint: sdk-cli` | same |
| cwd / branch | `/root/claude-config-work`, branch `writing-for-agents2` (git worktree) | same |
| Wall clock | 07:21:10Z → 07:44:53Z, 2026-09-22 | 07:44:54Z → 08:22:14Z, 2026-09-22 |
| Task input | `cat /tmp/.tmpz88Jq7` @L23; 40,225 B, persisted to `tool-results/bm0o1xo3o.txt`, read in 4 `sed` chunks (@L32/@L37/@L44/@L51) | `cat /tmp/.tmpMMjY0I` @L23; 799 lines, read in 4 `sed` chunks (@L39/@L43/@L50/@L54) |
| Tool calls | 65 (63 Bash, 1 Skill, 1 ToolSearch) | 111 (108 Bash, 1 Agent, 1 Monitor, 1 ToolSearch) |
| Assistant output tokens (sum of `usage.output_tokens`) | 100,403 | 126,043 |
| Content blocks | 48 thinking, 4 text, 65 tool_use, 65 tool_result, 163 attachments, 1 user string, 1 system | 68 thinking, 3 text, 111 tool_use, 111 tool_result, 259 attachments, 1 user string, 1 system |
| Git range produced | `0b6d8be4` → `7dec8051` (5 commits) | `7dec8051` → `e13d1097` (6 commits) |

Relationship: B is the next loop iteration after A; B's session opens on a
fresh context and re-reads state from `.ralph/agent/scratchpad.md` as injected
by the harness. B dispatches one foreground subagent at @L552 (`Agent`,
`general-purpose`, `run_in_background: false`); that subagent's own transcript
is not inlined here (its brief concerns claim provenance in two rewritten
`SKILL.md` files, not the budget).

Extraction commands used:
`agent-tools cc-pretty <path> --skeleton` (both logs);
`sed -n '<n>p' <log> | jq -r '.message.content[]|select(.type=="thinking")|.thinking'`
over every line of both logs (48 + 68 blocks dumped to
`scratchpad/th16.txt`, `scratchpad/th17.txt` and read in full);
a full dump of all 176 `tool_use` inputs;
`jq` counts for the manifest; and `git show` / `git diff --numstat` in
`/root/claude-config-work` for text that the session's own tool inputs quote
only partially.

Extractor brief: parent dispatch, `mode: evidence`, focus as stated above.

---

## 1. The rule text, as it reached both sessions

Both iterations received the same loop prompt file. The rule appears once, in a
`# Rules` list inside a `<request added="loop3" from="user" commit="6349fed6">`
block (read by A at @L44/@L51, by B at @L54; quoted here from B @L56's result):

> - `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`. relocation is growth. Cut before add.

Adjacent rules in the same list:

> - All of this repo is mutable including any references and the grading design itself. Non represent user preferences; they represent ideas of prompt-engineering only, and may not be correct.
> - Only semantic claims/reasoning/understanding survive between rounds. Prompt test evidence is not citable across runs. Claims are only valid if you have a hypothesis of why written next to it. …
> - Outside of `/root/claude-config-work/prompt-tests/runs/` and fixtures and code-generated content, total added tokens no more than 50000

Harness text in the same prompt file that also governs `.ralph/agent/`
(section `### 0b. SCRATCHPAD`, and `### GUARDRAILS`):

> **Always append** new entries to the end of the file (most recent = bottom).

> **Context Files** (`.ralph/agent/*.md`) — Research artifacts: … Read when relevant

> ### AVAILABLE CONTEXT FILES
> Context files in `.ralph/agent/` (read if relevant to current work):
> - `.ralph/agent/summary.md`
> - `.ralph/agent/decisions.md`

> 1004. Keep scratchpad concise. If something is not useful for future iterations, don't add it.

Injection shape: the prompt file opens with a single
`<scratchpad path=".ralph/agent/scratchpad.md"> … </scratchpad>` block carrying
the file verbatim (B @L41–@L45; closing tag at @L45 line 74). The file's other
members — `decisions.md`, `memories.md`, `summary.md`, `tasks.jsonl` — are not
inlined in the prompt; both sessions `cat` them from disk. The orientation
section refers to a `<ready-tasks>` block; no such block appears in the prompt
file, and A's `ralph tools task ready` (@L56) returned `No ready tasks`.

Directory contents at A's start (`ls -la .ralph/agent/`, @L58): `decisions.md`
6,764 B, `memories.md` 6,213 B, `memories.md.lock` 0 B, `scratchpad.md` 9,731 B,
`summary.md` 236 B, `tasks.jsonl` 509 B, `tasks.jsonl.lock` 0 B. At B's start
(@L64): `decisions.md` 4,929 B, `memories.md` 6,916 B, `scratchpad.md` 10,249 B,
`summary.md` 236 B, `tasks.jsonl` 509 B, plus the two lock files.

Regex-negatives over both raw logs: `/Cut before add/` matches 3 times in A and
4 in B, and `/cut before add/` once in A — every match is inside a copy of the
rule text itself (the task file, or the persisted `tool-results` copy of it);
no assistant thinking or text block spells the phrase.
`/relocation/` matches 3 times in A and 15 in B; `/relocation-as-growth/` 7 and
11. Every occurrence sits in (a) the rule text, (b) the scratchpad's
`Rounds 1–14` / `History` history block sentence "Round 12: the task's subject
bounds the edit, so relocation-as-growth cannot occur on a writing task", (c) a
memory entry about "`Omit by default`'s relocation harm", (d) B's subagent brief
line "Paraphrase, compression, relocation between sections, and dropped material
are NOT findings", or (e) a Bash `description` field
`"Fix the opencode heading after relocation"` (B @L274). No block applies the
phrase "relocation is growth" to the `.ralph/agent` budget.

---

## 2. Session A (iteration 16) — chronological

### 2.1 Spans before the first budget event

`@L5`–`@L17` attachments: superpowers hook, user string
`"Please read and execute the task in /tmp/.tmpz88Jq7"`, environment, model,
deferred tools, agent listing, skill listing, auto-mode, instructions
(`10,247~tok`), session context, date.
`@L22` text `"I'll read the task file first."`
`@L23`–`@L53`: 5 Bash calls reading the task file in chunks (calls 1–5).
Thinking at `@L31` and `@L36` states the file is large and the rest should be
read.

### 2.2 First measurement — call 6, 07:21:30Z

`@L56[0]` (Bash), a compound orientation command ending in:

```
… && ls -la .ralph/agent/ && agent-tools count-tokens --file <(cat .ralph/agent/*.md) 2>&1 | tail -3
```

`@L58` result ends with the bare number:

```
5878
```

The glob is `*.md`; `tasks.jsonl` (509 B) and the two `.lock` files listed by the
same command's `ls -la` are outside it. No `--api` flag; the local tokenizer
backend answers.

`@L60` thinking (67~tok), verbatim:

> I'm close to the 6000 token limit for `.ralph/agent/*`, so I'll need to trim
> something before adding more. Now I want to check the key files—the CLAUDE.md
> writing-for-other-agents section, the alan-default-next.md block, the
> prompt-tests skill, and the remaining cases.

### 2.3 Planning spans that name the budget

`@L61`–`@L129` (calls 7–17): reads of `sys_prompt/alan-default-next.md`'s
`# Writing for other agents` block, `sys_prompt/CLAUDE.md`,
`.claude/skills/prompt-tests/SKILL.md`, the corpus-ownership grep,
`prompt-tests/general/halve-the-runbook/`, `prompt-tests/runs/README.md`,
`prompt-tests/runs/retirement-policy/` artifacts, and `scripts/prompt-test-cc.sh`.

`@L105` thinking (2,793~tok) is the round's milestone-selection block. Near its
end:

> The task.md, fixture, and README should live under that probe directory, with
> the runner taking it as first arg — I should verify it accepts a path with a
> slash. I also need to check the agent memory file stays under 6000 tokens
> (currently 5878), so I'll need to cut before adding anything.

`@L131` thinking (1,330~tok), on the plan of work:

> Now I lay out the actual plan of work: write the critiques and plan to a
> scratchpad staying under the token budget, build a probe directory with task,
> fixture, and pre-registration README, commit that pre-registration …

`@L132` (call 18) runs `agent-tools count-tokens --api --file
sys_prompt/alan-default-next.md` (result `6438`) and `cat .ralph/agent/summary.md`
(result: the 236-byte file whose body reads `**Status:** Failed: stale loop
detected / **Iterations:** 4 / **Duration:** 23m 52s / … _No scratchpad found._
/ … _No events recorded._ / … `3f73a56c: scratchpad: record iteration 1 commit
range`). The `--api` backend is used on the system prompt, not on `.ralph/agent`.

`@L139` thinking:

> The binary looks fine since no source changes happened after the build, so I
> don't need to rebuild. Now I need to write the scratchpad critiques and plan,
> but I have to trim things down since .ralph/agent is already near the 6000
> token limit at 5878.
>
> I'll compress the "Iteration 15" section into a two-line summary once I write
> up iteration 16, since the detailed info already lives in commit messages and
> the run README. …

### 2.4 Probe launch, then the first scratchpad compression — calls 27–28

`@L141`–`@L173` (calls 19–24): fixture build, pre-registration README, arm
snapshots, two backgrounded `agent-tools run` launches.
`@L180`–`@L192` (calls 25–26): a repair to
`prompt-tests/runs/retirement-policy/README.md`, and an `agent-tools ps` check.

`@L196` thinking, while the arms run:

> While waiting for results, I should draft the scratchpad critiques. The file is
> currently at 9731 bytes and 5878 tokens against a 6000 limit, so I need to trim
> it. The plan is to keep the durable method section, standing contract clauses,
> and objective notes intact since they're high-value, but compress the long
> Iteration 15 section down to a brief summary once Iteration 16 is written up.
> …
> While waiting for the background runs to finish, I'll write the scratchpad
> critique text now for the parts that don't depend on results, then read the
> actual scratchpad file so I can restructure it precisely—collapsing
> "Iteration 15" into the Rounds line and adding the "Iteration 16" section.

`@L197` (call 27), verbatim input:

```
grep -n "^## \|^### " .ralph/agent/scratchpad.md && echo "--- decisions headings ---" && grep -n "^## \|^### " .ralph/agent/decisions.md | tail -20
```

`@L199` result:

```
3:## Where the objective bites
9:## Durable method, reusable across rounds
60:## Standing `(contract)`
107:## Rounds 1–14 — `9f6c03a0` → `0a1f1b6a`
121:## Iteration 15 — `0a1f1b6a` → `73a57146` (+ this commit)
123:### Critique of the rounds that built the case corpus
148:### The round's work
169:### `(instruction)` for iteration 16
--- decisions headings ---
23:## DEC-022 — test the incumbent `Claim less`, then delete it on a null (iter 14, conf 86)
50:## DEC-023 — bind the case corpus to the prompt, delete eleven of fifteen (iter 15, conf 82)
74:## DEC-024 — keep the whole `# Writing for other agents` block on one row of three (iter 15, conf 66)
```

`@L201` (call 28, 07:28:01Z) is the compression. Input (abridged at the point
marked, full text recoverable at the ref):

```python
python3 - <<'PY'
p='.ralph/agent/scratchpad.md'
s=open(p).read()
i=s.index('## Iteration 15 — ')
head=s[:i]
new = '''## Rounds 15 — `0a1f1b6a` → `0b6d8be4`

Bound the case corpus to the prompt: a case is kept only while
`sys_prompt/CLAUDE.md` names it, one grep decides, eleven of fifteen deleted.
Ran `# Writing for other agents` whole against an arm with no block on
`retirement-policy`; the arms parted on one row in the block's favour, so no
deletion shipped. Both arms transcribed the fixture's bare preference as an
incident with a cost it never had.

## Iteration 16 — `0b6d8be4` → (end of round)

### Critique of iteration 15
… [C1 fact; C2 workflow; C3 workflow; C4 workflow, overriding instruction 1] …
'''
open(p,'w').write(head+new)
PY
agent-tools count-tokens --file <(cat .ralph/agent/*.md) | tail -1
```

`@L206` result: `5558`.

**What the 6-line "Rounds 15" paragraph replaced.** Everything from line 121 of
the pre-edit file to EOF — the whole `## Iteration 15` section:
`### Critique of the rounds that built the case corpus` (four entries C1–C4),
`### The round's work` (three paragraphs), and
`### (instruction) for iteration 16` (three numbered items). Measured at
`git show 0b6d8be4:.ralph/agent/scratchpad.md | sed -n '121,200p'`: 58 lines,
≈640 words. Opening of the deleted text, verbatim:

> **C1 (fact).** `retirement-policy`'s keep-note said `sys_prompt/CLAUDE.md`'s
> condition for `Say what ends it` "names a re-run here". Grep: that file named two
> cases and not this one. The condition names a *fixture shape*, which any fixture
> satisfies. A keep argument resting on a citation that does not exist is the
> ratchet's strongest form — it reads as load-bearing and nothing can check it.

and the last deleted item, verbatim:

> 3. Do **not** ship a register line ("should this be a rule at all") on the
>    strength of this round. The failure is measured; that an agent would act on a
>    line addressing it is not, and this node has swallowed five wordings already.

`@L208` thinking:

> I'm tracking my remaining token budget and planning to add the round's work plus
> an instruction section after the results, then check on the runs.

### 2.5 Spans between the compression and the round's close

`@L209`–`@L370` (calls 29–53): waiting on the two probe legs
(`agent-tools ps`, `until` loops, a `Skill: long-bash` load at @L251, a
`pre_output.record` at @L257), reading both delivered `HANDOFF.md` artifacts,
checksumming the two arm prompts, grepping both arms' transcripts, writing the
probe result into `prompt-tests/runs/release-bot-handoff/README.md` (@L342),
replacing a `sys_prompt/CLAUDE.md` paragraph (@L347 prints `1117 chars`; @L354
prints `1117 -> 994`), the corpus grep, deleting the probe directory (@L363), and
amending that commit's message (@L368). None of these blocks names the
`.ralph/agent` budget; the `1117 -> 994` measurement is a character count under a
different standing rule ("a round that ships no prompt edit … may replace [a
paragraph], and the replacement is shorter").

### 2.6 End-of-round housekeeping — calls 54–63, 07:43:08Z–07:44:20Z

`@L375` thinking:

> Now I need to close out the round: update the scratchpad with the round's work,
> add DEC-025 to decisions.md, update memories, commit, and emit — all while
> staying within the token budget of about 440 tokens remaining, so I'll keep
> everything terse.
>
> The one durable method lesson worth capturing is: before writing a clause
> targeting a failure, re-run the failure in a different genre … I'll add that as
> a single line, keep the round-work section minimal, include two instructions …

`@L376` (call 54): `sed -n '74,110p' .ralph/agent/decisions.md` — reads DEC-024's
entry format.

`@L380` (call 55): appends `## DEC-025 — override iteration 15's instruction;
probe the warrant node in a second genre (iter 16, conf 84)` (19 lines, six
labelled fields) to `decisions.md`, and in the same call runs
`ralph tools memory add "Prompt-test genre effect: …"` (one `pattern` memory,
tags `prompt-tests,writing-for-agents`). Result: `Memory stored:
mem-1790062999-53ee`.

`@L384` (call 56): inserts one durable-method paragraph into `scratchpad.md`
after an asserted anchor, and appends `### The round's work` (three paragraphs)
plus `### (instruction) for iteration 17` (two numbered items). Inserted method
paragraph, verbatim:

> **Before writing a clause for a failure, re-run the failure in a second genre.**
> If it disappears there, the target is the genre and not the wording, and a clause
> aimed at the text will compete with the frame rather than replace it. *(iter 16)*

The same call re-measures: result `6538`.

`@L391` thinking:

> I'm over the token budget by about 540 tokens and need to trim content from the
> agent context files, starting with the stale summary.md that still references an
> old failed loop, then checking whether memories.md is contributing excess size.
>
> Since decisions.md just grew with DEC-025, the cheapest cut is likely one of the
> older entries like DEC-022, since their content already lives in git and
> CLAUDE.md — earlier rounds seem to have pruned similarly, leaving only the last
> few decisions. I'll inspect the actual sizes of decisions.md and memories.md to
> prune the oldest decision and any stale memory entries.

`@L392` (call 57), verbatim input:

```
for f in .ralph/agent/*.md; do echo "$f: $(agent-tools count-tokens --file $f | tail -1)"; done; echo "--- decisions ids ---"; grep -n "^## DEC" .ralph/agent/decisions.md; echo "--- memories ---"; grep -c "^" .ralph/agent/memories.md; grep -n "^## \|^- \[mem-" .ralph/agent/memories.md | head -20
```

Result `@L394`:

```
.ralph/agent/decisions.md: 2134
.ralph/agent/memories.md: 1761
.ralph/agent/scratchpad.md: 2572
.ralph/agent/summary.md: 71
```

(2134 + 1761 + 2572 + 71 = 6538, the concatenated total.) The same result lists
DEC-022/023/024/025 and the memories.md headings `## Patterns`, `## Decisions`,
`## Fixes`, `## Context`.

`@L396` (call 58): reads `decisions.md` lines 1–22 (the "Closed, discharged, no
longer re-argued" paragraph) and lines 23–49 (DEC-022 in full).

`@L400` thinking:

> DEC-022 is fully discharged now, so I can fold it into the "Closed" header as a
> single line alongside DEC-001–021, saving roughly 350 tokens. I should also
> compress DEC-023 since the corpus binding is shipped and now a standing rule in
> the skill—also discharged. Let me apply both compressions and re-measure.

`@L401` (call 59), verbatim input:

```python
python3 - <<'PY'
p='.ralph/agent/decisions.md'
s=open(p).read()
i=s.index('## DEC-022 —'); j=s.index('## DEC-024 —')
s = s[:i] + s[j:]
old="Framing bias on all: each fixture was written"
assert s.count(old)==1
s=s.replace(old, """**DEC-022** delete `Claim less` on a null against an arm without it (iter 14, shipped).
**DEC-023** bind the case corpus to the prompt — a case is kept only while
`sys_prompt/CLAUDE.md` names it, eleven of fifteen deleted (iter 15, shipped; the rule
now lives in the prompt-tests skill). Framing bias on all: each fixture was written""")
open(p,'w').write(s)
PY
agent-tools count-tokens --file <(cat .ralph/agent/*.md) | tail -1
```

Result: `5725`.

Deleted by that slice: DEC-022 (27 lines, read at @L398) and DEC-023 (24 lines),
each carrying `**Chosen**`, `**Alternatives**`, `**Reasoning**`,
`**Re-evaluate**`, `**Framing bias**`, `**Independent evaluation**` and a
timestamp. Opening of DEC-022, verbatim:

> ## DEC-022 — test the incumbent `Claim less`, then delete it on a null (iter 14, conf 86)
> - **Chosen**: probe the bullet against an arm without it, and delete it; the
>   pre-registration's Mixed clause withdrawn in the run README as directionless.

Replaced by two sentences inside the pre-existing "Closed, discharged" paragraph.
That paragraph's own standing header, unchanged by this edit:

> Compressed to durable content. Full reasoning lives where it survives this loop:
> commit messages, `sys_prompt/CLAUDE.md` for anything justifying a prompt line,
> and each case's `prompt-tests/runs/<case>/README.md`.

`@L408` thinking:

> That's within the limit, good. I'll leave summary.md alone since it's an
> auto-generated artifact from the summarizer. Now I'm double-checking the
> checklist items are in place …

`@L409` (call 60): `git diff HEAD --stat` (`.ralph/agent/decisions.md | 76
+++…---`, `memories.md | 4 +++`, `scratchpad.md | 32 +++…`), the prompt-unchanged
check, `ls tests/`, and `agent-tools count-tokens --api --file
sys_prompt/alan-default-next.md` → `6438`.

`@L414` (call 61): `check-prompt-coupling.sh`, a `release-bot-handoff` citer
count, and the corpus grep.

`@L419` (call 62): the citer grep plus the state commit. Commit message,
verbatim:

> iter16: scratchpad, decisions, memories
>
> Critiques C1-C4 of iteration 15, the round's work, and two instructions for
> iteration 17. Durable method gains one line: re-run a failure in a second genre
> before writing a clause for it. DEC-025; DEC-022 and DEC-023 compressed into the
> discharged list to stay inside the 6000-token budget (5725).
>
> Claude-Session: 8cbdf6ab-6a12-408d-94ce-f4e4519efdd3

`@L423` (call 63): `sed -i` filling the commit range into the
`## Iteration 16` heading, then `agent-tools count-tokens --file <(cat
.ralph/agent/*.md) | tail -1` → `5733`, then the range commit.

`@L430` (call 64) `ralph emit "work.iteration" …` — the 200-word event summary
does not mention the budget.
`@L434` (call 65) `pre_output.record` turn 2 — `uncertainties` list four items,
none about the budget.

### 2.7 A's final text block (@L438)

Under `## Updates`:

> - `.ralph/agent/*` at 5733 tokens (limit 6000), which required compressing two discharged decisions.

Under `## Required notes`, the entry naming a conflict in the rule set:

> - **instruction issue:** the between-worker contract says "always append" to the
>   scratchpad while the user caps `.ralph/agent/*` at 6000 tokens. Those conflict;
>   the budget wins, and prior rounds already resolved it by compressing. Worth an
>   explicit `(contract)` line if a later round trips on it.

Also in the same list:

> - **context waste:** the injected task file carries three near-identical copies
>   of the ralph memory/task skill text (~2,500 tokens of duplication) that no part
>   of this round used.

---

## 3. Session B (iteration 17) — chronological

### 3.1 State inherited, and where it came from

B's prompt carried `scratchpad.md` as written by A. Its sections, per B's own
`grep -n "^## "` at @L211 (`@L213`):

```
3:## Where the objective bites
9:## Durable method, reusable across rounds
64:## Standing `(contract)`
111:## Rounds 1–14 — `9f6c03a0` → `0a1f1b6a`
125:## Rounds 15 — `0a1f1b6a` → `0b6d8be4`
134:## Iteration 16 — `0b6d8be4` → `8f84fa1e` (+ this commit)
```

The `(instruction)` for iteration 17 that A wrote at @L384 reached B inside that
injected block (B @L45, result lines 63–73):

> ### `(instruction)` for iteration 17
>
> 1. The warrant node is now narrowed, not open. Any further attempt has to fire
>    **while a rules file is being written** — an action, not a disposition asked
>    of the finished text. A sixth wording aimed at the text is out.
> 2. `Omit by default` has no evidence either way from iterations 15 or 16. Both
>    arms here wrote ~4,000 words from a 263-word task and edited three files
>    apiece; that is the bullet's own failure shape and neither round read it,
>    because both excluded counts. Find a categorical reading for it first, then
>    run it — not another count.

### 3.2 First measurements — calls 7 and 8, 07:45:11Z

`@L62` (call 7), tail of a compound orientation command:

```
… && ls -la .ralph/agent/ && agent-tools count-tokens --file .ralph/agent/scratchpad.md 2>&1 | tail -3
```

Result `@L64` ends: `2580`.

`@L66` (call 8), verbatim:

```
for f in .ralph/agent/decisions.md .ralph/agent/memories.md .ralph/agent/summary.md; do echo "=== $f"; agent-tools count-tokens --file $f 2>&1|tail -1; done; echo "=== total"; cat .ralph/agent/*.md | agent-tools count-tokens 2>&1|tail -1
```

Result `@L68`:

```
=== .ralph/agent/decisions.md
1321
=== .ralph/agent/memories.md
1761
=== .ralph/agent/summary.md
71
=== total
5733
```

The per-file loop names three files explicitly and omits `scratchpad.md` (already
measured at @L62); the total pipes `cat .ralph/agent/*.md` into
`agent-tools count-tokens` with no `--file`. `tasks.jsonl` (509 B, listed by the
same call's `ls -la`) is outside the glob.

`@L70` thinking:

> I'm close to the token cap, so I'll need to trim before adding more. Let me
> review the "Writing for other agents" section of CLAUDE.md, the prompt block
> itself, and the current prompt-tests state.

### 3.3 Planning spans that name the budget

`@L71`–`@L150` (calls 9–22): reads of the prompt block, `sys_prompt/CLAUDE.md`,
`prompt-tests/general/`, `halve-the-runbook` task and reference,
`prompt-tests/runs/README.md`, `prompt-tests/CLAUDE.md`, the prompt-tests
`SKILL.md` in three chunks, the ownership grep, `git log` for whether
`halve-the-runbook` was ever run, `retirement-policy`'s README, and
`scripts/prompt-test-cc.sh`.

`@L139` thinking (1,936~tok) contains the round's three critiques. Its C2/C3
material states that iteration 16's handed-forward word/file count came from a
probe iteration 16 deleted:

> For C2, I'm flagging that Iteration 16's word-count claim ("~4,000 words from a
> 263-word task, three files edited") was derived post-hoc from a probe the same
> round deleted, whose transcripts are now gitignored — exactly the kind of
> reading the round's own contract explicitly declares inadmissible, yet it was
> handed forward as premise for the next round without note. I'll mark it as
> motivation only, not evidence.

The same block weighs run cost (graders vs. self-read) under the word "budget";
`@L114` and `@L127` re-derive by `git log` that `halve-the-runbook` had never
been run across 16 rounds and 87 commits.

`@L152` (call 23) measures the two arm prompts with the API backend:
`agent-tools count-tokens --api --file /tmp/arms/a.md` → `6438`, `…/b.md` →
`6395`. `@L156` thinking:

> Arm A comes in at 6438 versus arm B at 6395, with the bullet costing 43 API
> tokens … Now I need to write the pre-registration, commit, and launch, making
> sure to log the critique into the scratchpad while staying within the token
> budget since .ralph/agent is already at 5733.
>
> Before adding anything I need to cut — the scratchpad has "Rounds 1–14,"
> "Rounds 15," and "Iteration 16" sections, so I'll collapse iteration 16's detail
> now that its finding lives in sys_prompt/CLAUDE.md, and compress round 15 too.

### 3.4 The loop-history compression — calls 30–35, 07:49:39Z–07:50:21Z

Both arms were launched at calls 28–29 (@L178/@L184) and ran in the background
through this span.

`@L193` thinking:

> With both agents running, I need to update the scratchpad critique but keep the
> total token budget under control—it's currently at 5733 out of 6000, so I need
> to compress earlier rounds into shorter summaries while adding the iteration 17
> critique and work.
>
> I'm planning to keep the "Where the objective bites" and durable method
> sections, trim outdated entries, collapse rounds 1-16 into a short history
> block, and add iteration 17's critique with instructions for round 18. Let me
> also check memories.md and decisions.md for additional trimming opportunities.

`@L194` (call 30) `cat .ralph/agent/decisions.md`.
`@L198` (call 31) `cat .ralph/agent/memories.md && echo "=== summary ===" && cat
.ralph/agent/summary.md`.

`@L205` thinking:

> summary.md is outdated and misleading with its stale "Failed" status, so I'll
> trim it down to just a pointer rather than keep the full 71 tokens of stale
> content. Now I want to check the other files.

`@L210` thinking:

> Both processes are running now, so I'm drafting the scratchpad critique. I need
> to watch my token budget carefully—current totals are close to the 6000 cap, so
> adding the new decision entry and a couple memories means I'll have to trim
> elsewhere in the scratchpad to stay under budget.
>
> I'm shrinking the summary down near zero and compressing DEC-024, which is now
> discharged, into a one-liner. I'm also condensing the rounds 1-14 history block
> along with rounds 15 and 16 to free up space, then I'll rewrite the tail of
> scratchpad.md programmatically from the rounds marker onward to restructure
> everything.

`@L211` (call 33): the heading grep quoted in §3.1.

`@L215` (call 34) is the compression. Input opens:

```
head -110 .ralph/agent/scratchpad.md > /tmp/sp.md && cat >> /tmp/sp.md <<'EOF'
## History — rounds 1–16, `9f6c03a0` → `7dec8051`
…
EOF
cp /tmp/sp.md .ralph/agent/scratchpad.md && agent-tools count-tokens --file .ralph/agent/scratchpad.md 2>&1|tail -1
```

`head -110` keeps everything up to and including line 110 and drops lines 111 to
EOF — i.e. `## Rounds 1–14` (line 111), `## Rounds 15` (125), and
`## Iteration 16` (134) with its `### Critique of iteration 15`,
`### The round's work` and `### (instruction) for iteration 17`. `git diff
--numstat 7dec8051 37eded6c` records `49` insertions and `74` deletions in
`scratchpad.md`.

The replacement history block, verbatim:

> ## History — rounds 1–16, `9f6c03a0` → `7dec8051`
>
> Detail is in commit messages; anything justifying a prompt line is in
> `sys_prompt/CLAUDE.md`, the durable home and the one to read before touching the
> block. Shipped across the loop: `Say what ends it` added (9); `Omit by default`
> repriced to reach (3) and back to existence (13); the `Claim less` hedge clause
> cut (4) and the whole bullet with it (14); the case corpus bound to the prompt by
> one grep, eleven of fifteen cases deleted (15). Failed candidates: five wordings
> aimed at claim-handling (6–8, 14) — the node is premise **provenance**, not
> wording, and what discharges a premise is an action; one at copy-pricing (12) —
> the task's subject bounds the edit, so relocation-as-growth cannot occur on a
> writing task; one at warrant-transcription (16) — a rules section's heading is
> what flattens a preference, and a clause only competes with the genre. Round 10
> fixed a nine-round harness contamination and voided every arm stored before
> 2026-09-22. Round 15 ran the block whole against an arm with no block: the arms
> parted on one row in the block's favour and `Omit by default` was untouched.

The same `cat >>` adds `## Iteration 17 — 7dec8051 → (this round)` with
`### Critique of prior iterations` (C1, C2, C3) and `### The round's work`
(three lines pointing at `prompt-tests/runs/halve-the-runbook/README.md`).

What the History block replaced (pre-edit lines 111–end, ≈74 lines): the
`## Rounds 1–14` paragraph (15 lines, ending "Round 12: the task's subject bounds
the edit, so relocation-as-growth cannot occur on a writing task."), the
`## Rounds 15` paragraph A wrote at @L201 (8 lines), and A's whole
`## Iteration 16` section (C1–C4, round's work, two instructions).

Result `@L217`: `2261`.

`@L225` (call 35), verbatim input:

```python
python3 - <<'PY'
import re
p='.ralph/agent/decisions.md'
s=open(p).read()
i=s.index('## DEC-024'); j=s.index('## DEC-025')
fold = ("**DEC-024** keep the whole block on one row of three (iter 15) — discharged: iteration 16 ran "
        "the warrant half and iteration 17 the `Omit by default` half. Its pre-registration did not "
        "partition (see scratchpad C2).\n\n")
s = s[:i] + fold + s[j:]
open(p,'w').write(s)
PY
printf '# Loop Summary\n\nStale; regenerated by the loop tooling at fixed-point. Read `scratchpad.md`.\n' > .ralph/agent/summary.md
for f in .ralph/agent/*.md; do echo -n "$f "; agent-tools count-tokens --file $f 2>&1|tail -1; done; echo -n "TOTAL "; cat .ralph/agent/*.md | agent-tools count-tokens 2>&1|tail -1
```

Deleted: DEC-024's 21-line entry (read by B at @L194; opening
`## DEC-024 — keep the whole `# Writing for other agents` block on one row of
three (iter 15, conf 66)` / `- **Chosen**: ship no deletion; hand the
bullet-level isolation to iteration 16.`), replaced by one sentence.

`summary.md` overwritten. Before (`git show 7dec8051:.ralph/agent/summary.md`,
16 lines):

```
# Loop Summary

**Status:** Failed: stale loop detected
**Iterations:** 4
**Duration:** 23m 52s

## Tasks

_No scratchpad found._

## Events

_No events recorded._

## Final Commit

3f73a56c: scratchpad: record iteration 1 commit range
```

After (3 lines):

```
# Loop Summary

Stale; regenerated by the loop tooling at fixed-point. Read `scratchpad.md`.
```

Result `@L227`:

```
.ralph/agent/decisions.md 984
.ralph/agent/memories.md 1761
.ralph/agent/scratchpad.md 2261
.ralph/agent/summary.md 24
TOTAL 5030
```

`@L229` thinking: `5030 total leaves about 970 to spare, that works. Now I'm
checking the arms.`

`@L251` (call 40) commits the three files:

> iter17: critique of 15 and 16, and the loop history compressed
>
> C1 the retirement condition nobody paid for; C2 iteration 15's outcomes do not
> partition and it took the branch that ships no deletion; C3 iteration 16's
> handed-forward count is post-hoc and now uncheckable.
>
> Claude-Session: cdcc1497-803e-4b57-b94f-fdf533aea762

### 3.5 Spans between the compression and the round's close

`@L257`–`@L619` (calls 41–101): an edit to
`.claude/skills/prompt-tests/SKILL.md` relocating a contamination bullet
(@L265/@L269/@L274, described at `@L264` as "a net-zero-size move"), ~25 polling
and waiting calls (`agent-tools ps`, `Monitor` at @L288, four
`agent-tools run --desc "wait" sleep …`), contamination greps over both arms'
transcripts, R1–R4 scoring of the two delivered `SKILL.md` files, one foreground
`Agent` dispatch at @L552, a correction to the run README's deletion clause
(@L374), the prompt edit deleting line 190 of
`sys_prompt/alan-default-next.md` (@L573), the `sys_prompt/CLAUDE.md`
replacement (@L577 prints `233` then `new words: 231`), storing both artifacts
into `prompt-tests/runs/halve-the-runbook/` (@L590), deleting
`prompt-tests/runs/retirement-policy/` (@L601), `pytest` (@L610, `531 passed, 3
skipped`) and the shipping commit (@L619).

`@L568` (call 92) greps for surviving citers of the deleted bullet and excludes
the state directory:

```
grep -rn --include='*.md' "Omit by default" . | grep -v "^./.ralph" | grep -v "prompt-tests/runs/halve-the-runbook"
```

### 3.6 End-of-round housekeeping — calls 102–108, 08:20:35Z–08:21:25Z

`@L623` thinking:

> Now I need to update the state files: the scratchpad results, DEC-026, and
> memories, then check the budget. I'm also considering adding a contract clause
> for the next round — the blind cross-check was decisive since it reversed my own
> reading, so a round's key finding should be reviewed by someone unaware of what's
> being tested, a workflow fix worth formalizing.

`@L624` (call 102) carries an in-script comment stating the trade it makes:

```python
# Contract addition, replacing nothing but paying for itself by cutting a superseded method entry.
old_method = """**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.

"""
assert old_method in s
s = s.replace(old_method, "")
```

The same script inserts a new `(contract)` clause before the
`An (instruction) asserting that work is undone…` clause:

> > **A round's decisive reading is made by a reader that is not the round.** One
> > reader, holding the artifacts relabelled and the criterion, told neither what is
> > being tested nor which arm is which — and its answer is the result, not a check
> > on one already written. Iteration 17's own read of its deciding reading found one
> > of three unsourced claims and missed the one in the arm it would have kept; the
> > blind read reversed the outcome. *(17)*

and appends `### The round's result` (6 lines, pointing at
`prompt-tests/runs/halve-the-runbook/README.md` and `sys_prompt/CLAUDE.md`) plus
`### (instruction) for iteration 18` (two numbered items). Result `@L626`: `2573`.

`@L628` (call 103) appends `## DEC-026 — delete `Omit by default` on a null at
its own named fixture (iter 17, conf 78)` (26 lines) and re-measures. Result
`@L630`:

```
.ralph/agent/decisions.md 1441
.ralph/agent/memories.md 1761
.ralph/agent/scratchpad.md 2573
.ralph/agent/summary.md 24
TOTAL 5799
```

`@L635` thinking:

> I'm still under the memory limit but close to it, so I want to add two new
> memories via the CLI rather than echo/cat, and check whether I need to trim an
> older one to stay under budget — though that particular memory about
> shipped-with-unmeasured-negative-effect still seems valid and worth keeping.
>
> Other candidates for removal are the false-and-checkable belief technique memory
> and the differential probe with two fresh readers memory — the latter now
> overlaps with the blind cross-check clause already baked into the contract, so
> I'll cut it. First let me confirm the ralph CLI is actually available.

`@L636` (call 104): `which ralph; echo "RALPH_BIN=…"; ralph tools memory list
--format quiet | head -5`.

`@L640` (call 105): `ralph tools memory delete mem-1790041345-2f2f && ralph tools
memory add "A round's own read of its deciding criterion is not reliable enough
to decide it. …" -t pattern --tags prompt-tests,test-design && ralph tools memory
add "Omit by default (any content you write has to earn its place) is deleted
from sys_prompt/alan-default-next.md: …" -t decision --tags
sys-prompt,writing-for-agents && echo -n "TOTAL "; cat .ralph/agent/*.md |
agent-tools count-tokens | tail -1`. Result:

```
Memory deleted: mem-1790041345-2f2f
Memory stored: mem-1790065267-fe47
Memory stored: mem-1790065267-1153
TOTAL 6062
```

Deleted memory `mem-1790041345-2f2f`, verbatim (from `git diff 7dec8051
b0304c40 -- .ralph/agent/memories.md`):

> Verify a doc compression with a differential probe, not a review: two fresh
> readers, one per version, same question ('what must you get right, what goes
> wrong if you miss it, would you notice'), no repo access. A reviewer who has read
> both versions knows the answer and cannot see a silently-removed trap. Cost: two
> single-turn subagents. It found one real loss and one contradiction.
> `<!-- tags: docs, verification | created: 2026-09-22 -->`

`@L644` thinking:

> I'm still over budget by about 100 tokens, so I need to cut one more superseded
> memory. I'm weighing between the fixture-design technique from the handover,
> which is still useful but unused recently, versus the note about downstream
> readers not stabilizing baselines, which is a durable lesson partly captured
> elsewhere in the scratchpad's point about buying resolution inside the run.
>
> Since the claim-handling block that fixture technique relates to is now
> essentially closed, I'll cut that one and keep the more central lesson.

`@L645` (call 106): `ralph tools memory delete mem-1790045604-dc10 && echo -n
"TOTAL "; cat .ralph/agent/*.md | agent-tools count-tokens | tail -1` →
`Memory deleted: mem-1790045604-dc10` / `TOTAL 5915`.

Deleted memory `mem-1790045604-dc10`, verbatim:

> To discriminate hedging from verifying in a prompt test, put a FALSE AND
> CHECKABLE belief in the handover: the reporter states something about the repo
> that the fixture refutes in one read. Repeating it as a warning is hedging where
> checking was available; refuting it is verification. Pair it with an
> unexplained-but-load-bearing item as the control in the other direction, so an arm
> that drops everything unretirable also fails. Both directions live in one fixture,
> no second adversarial case needed.
> `<!-- tags: prompt-tests, test-design | created: 2026-09-22 -->`

`@L649` (call 107) commits. Message includes the new contract clause and one
budget line:

> .ralph/agent totals 5,915 tokens.

`@L656` (call 108) fills the commit range into the `## Iteration 17` heading and
commits the range; no re-measurement in this call.
`@L660` (call 109) `ralph emit "work.iteration" …` — the summary lists the new
`(contract)` and the three critiques; it does not mention the budget.
`@L664` and `@L669` (calls 110–111) `pre_output.record`; neither
`uncertainties` list mentions the budget.

### 3.7 B's final text block (@L676)

Under `## Updates`:

> Commit range `7dec8051` → `e13d1097`; tree clean; `work.iteration` emitted.
> `.ralph/agent` at 5,915 tokens.

`## Required notes` contains six entries; none states a budget-rule ambiguity.
Two name prior-iteration information:

> - **instruction issue:** iteration 15's pre-registration claimed its four
>   outcomes partitioned the space; its actual result satisfied two of them, and the
>   round took the one shipping no deletion. Recorded as C2.
> - **instruction issue:** iteration 16 handed forward a word/file count as the next
>   round's premise — a post-hoc reading from a probe it deleted, now uncheckable.
>   Treated as motivation only.

and one repeats A's observation about the injected prompt:

> - **context waste:** the injected task file carries three near-identical ralph
>   skill dumps (`ralph-tools`, `ralph-tools-tasks`, `ralph-tools-memories`) with
>   the memory section duplicated verbatim across two of them.

---

## 4. Measurement ledger (all `count-tokens` invocations, both sessions)

| # | Ref (call ordinal) | Command against `.ralph/agent` | Result |
| --- | --- | --- | --- |
| A1 | @L56 (6/65), 07:21:30Z | `agent-tools count-tokens --file <(cat .ralph/agent/*.md) 2>&1 \| tail -3` | `5878` |
| A2 | @L201 (28/65), 07:28:01Z | same, after the `## Iteration 15` → `## Rounds 15` rewrite | `5558` |
| A3 | @L384 (56/65) | same, after the round's-work + instruction append | `6538` |
| A4 | @L392 (57/65) | `for f in .ralph/agent/*.md; do echo "$f: $(agent-tools count-tokens --file $f \| tail -1)"; done` | decisions `2134`, memories `1761`, scratchpad `2572`, summary `71` |
| A5 | @L401 (59/65) | `--file <(cat .ralph/agent/*.md)`, after the DEC-022/023 fold | `5725` |
| A6 | @L423 (63/65), 07:44:20Z | same, after the heading range edit | `5733` |
| B1 | @L62 (7/111), 07:45:11Z | `agent-tools count-tokens --file .ralph/agent/scratchpad.md 2>&1 \| tail -3` | `2580` |
| B2 | @L66 (8/111) | per-file over decisions/memories/summary, then `cat .ralph/agent/*.md \| agent-tools count-tokens` | `1321` / `1761` / `71`; total `5733` |
| B3 | @L215 (34/111), 07:50:12Z | `--file .ralph/agent/scratchpad.md`, after the `head -110` + History rewrite | `2261` |
| B4 | @L225 (35/111) | per-file over `.ralph/agent/*.md` + `TOTAL` | decisions `984`, memories `1761`, scratchpad `2261`, summary `24`; `TOTAL 5030` |
| B5 | @L624 (102/111), 08:20:35Z | `--file .ralph/agent/scratchpad.md` | `2573` |
| B6 | @L628 (103/111) | per-file + `TOTAL`, after DEC-026 | `1441` / `1761` / `2573` / `24`; `TOTAL 5799` |
| B7 | @L640 (105/111) | `TOTAL`, after 1 memory delete + 2 adds | `6062` |
| B8 | @L645 (106/111), 08:21:0xZ | `TOTAL`, after 1 further memory delete | `5915` |

Non-`.ralph` uses of the same binary in these sessions: A @L132 and A @L409
(`--api --file sys_prompt/alan-default-next.md` → `6438` both times); B @L152
(`--api --file /tmp/arms/a.md` → `6438`, `…/b.md` → `6395`). Every `.ralph`
measurement above uses the default (no-`--api`) backend; every non-`.ralph`
measurement uses `--api`.

Two moments above 6000: A3 (`6538`, thinking at @L391 says "over the token budget
by about 540 tokens") and B7 (`6062`, thinking at @L644 says "still over budget by
about 100 tokens"). Both were followed by a deletion and a re-measure inside the
next two tool calls.

`grep -c 'count-tokens'` over A's raw JSONL returns 22 (includes the rule text,
tool inputs, and echoed results).

---

## 5. Edits to `.ralph/agent/*`, by file

`git diff --numstat` for the three state commits:

| Commit | scratchpad.md | decisions.md | memories.md | summary.md |
| --- | --- | --- | --- | --- |
| `0b6d8be4`→`8f84fa1e` (iter16) | +67 / −55 | +24 / −52 | +4 / −0 | — |
| `7dec8051`→`37eded6c` (iter17, "loop history compressed") | +49 / −74 | +1 / −21 | — | +1 / −15 |
| `37eded6c`→`b0304c40` (iter17 state) | +26 / −3 | +27 / −0 | +8 / −8 | — |

Deletions, in order:

1. **A @L201** — `scratchpad.md`: `## Iteration 15` section (58 lines, ≈640
   words; C1–C4 critiques, three round's-work paragraphs, three numbered
   instructions) replaced by an 8-line `## Rounds 15` paragraph plus a new
   `## Iteration 16` heading and critique.
2. **A @L401** — `decisions.md`: DEC-022 (27 lines) and DEC-023 (24 lines)
   deleted; replaced by two sentences prepended to the existing
   "Closed, discharged, no longer re-argued" paragraph.
3. **B @L215** — `scratchpad.md`: everything from line 111 to EOF (`Rounds 1–14`
   + `Rounds 15` + the whole `Iteration 16` section including its
   `(instruction) for iteration 17`) replaced by a 16-line
   `## History — rounds 1–16` block.
4. **B @L225** — `decisions.md`: DEC-024 (21 lines) folded to one sentence;
   `summary.md` overwritten from 16 lines to 3.
5. **B @L624** — `scratchpad.md`: the durable-method entry *"A prose warning
   inside the thing it warns about does not stop a reader who has read it.
   Convert to a refusal with an escape hatch; the refusal is checkable."*
   deleted, with the in-script comment "replacing nothing but paying for itself
   by cutting a superseded method entry".
6. **B @L640** — `memories.md`: `mem-1790041345-2f2f` (differential-probe
   technique) deleted; two new memories added.
7. **B @L645** — `memories.md`: `mem-1790045604-dc10` (false-and-checkable
   belief technique) deleted.

Additions in the same two sessions: A added one durable-method paragraph, a
`### The round's work` section, a two-item `(instruction)`, DEC-025 (19 lines)
and memory `mem-1790062999-53ee`. B added a `## Iteration 17` section with three
critiques, one `(contract)` clause, a `### The round's result` section, a two-item
`(instruction)`, DEC-026 (26 lines) and memories `mem-1790065267-fe47` /
`mem-1790065267-1153`.

Files inside `.ralph/agent/` never edited or measured by either session:
`tasks.jsonl`, `tasks.jsonl.lock`, `memories.md.lock`. A ran
`ralph tools task ready` once (@L56) and received `No ready tasks`; neither
session ran a `ralph tools task add/ensure`.

---

## 6. Destinations named as holding content that is not in `.ralph/agent/`

Statements written by the sessions themselves, in the files they edited:

- `decisions.md` header paragraph (present before A, unchanged by both):
  "Compressed to durable content. Full reasoning lives where it survives this
  loop: commit messages, `sys_prompt/CLAUDE.md` for anything justifying a prompt
  line, and each case's `prompt-tests/runs/<case>/README.md`."
- B's `## History` block (B @L215): "Detail is in commit messages; anything
  justifying a prompt line is in `sys_prompt/CLAUDE.md`, the durable home and the
  one to read before touching the block."
- A's `### The round's work` (A @L384): "The finding is in
  `sys_prompt/CLAUDE.md`, replacing the `Say what ends it` entry and shorter than
  it…" and "the probe was deleted with the round that wrote it (`git checkout
  0c85bfd1 --`)".
- B's `### The round's result` (B @L624): "Readings, the blind instrument and the
  excluded numbers that argue against the deletion:
  `prompt-tests/runs/halve-the-runbook/README.md`. The semantic claim and the
  re-entry condition are in `sys_prompt/CLAUDE.md`."
- A's commit message `8f84fa1e`: "DEC-025; DEC-022 and DEC-023 compressed into
  the discharged list to stay inside the 6000-token budget (5725)."
- B's commit message `b0304c40`: carries the new `(contract)` clause text in full,
  plus ".ralph/agent totals 5,915 tokens."
- B's commit message `f2bfe695`: carries the run's outcome, the excluded counts
  ("Word count and claim count both favour the bullet and both were excluded as
  readings before launch"), the CLAUDE.md word delta (233 → 231) and the restore
  recipes.

Related edits outside `.ralph/agent/` in the same rounds: A replaced a
`sys_prompt/CLAUDE.md` paragraph (1117 → 994 chars, A @L354); B replaced another
(233 → 231 words, B @L577) and relocated a bullet inside
`.claude/skills/prompt-tests/SKILL.md` (B @L265/@L269/@L274, `11 insertions and
15 deletions` per `@L264` thinking).

---

## 7. Statements about the rule's scope and wording

- **Per-file vs. sum.** Every `.ralph` total in both sessions concatenates or
  sums `.ralph/agent/*.md`. A4 and B4/B6 print per-file numbers whose sum equals
  the concatenated total exactly (A4: 2134+1761+2572+71 = 6538; B4:
  984+1761+2261+24 = 5030). No block in either session states which reading of
  "`.ralph/agent/*` ≤ 6000" is intended, or considers a per-file ceiling.
- **`tasks.jsonl`.** Present in both `ls -la` listings (509 B) and outside the
  `*.md` glob used by every measurement. No thinking or text block mentions it.
- **`summary.md`.** A @L408: "I'll leave summary.md alone since it's an
  auto-generated artifact from the summarizer." — after A4 showed it at 71 tokens
  and after A had already reached 5725. B @L205: "summary.md is outdated and
  misleading with its stale 'Failed' status, so I'll trim it down to just a
  pointer rather than keep the full 71 tokens of stale content." B then rewrote
  it to 24 tokens (B @L225). B's replacement text asserts it is "regenerated by
  the loop tooling at fixed-point".
- **"Always append" vs. the cap.** A's `## Required notes` (@L438): "the
  between-worker contract says 'always append' to the scratchpad while the user
  caps `.ralph/agent/*` at 6000 tokens. Those conflict; the budget wins, and prior
  rounds already resolved it by compressing. Worth an explicit `(contract)` line
  if a later round trips on it." No `(contract)` clause about the budget was
  written in either session; B's one new clause concerns blind reading.
- **Backend.** The rule names `agent-tools count-tokens` with no flag. All
  `.ralph` measurements used the default backend; `--api` appears only on
  `sys_prompt/alan-default-next.md` and the two arm prompts. No block compares
  the two backends or asks which the rule means.
- **"relocation is growth."** See the regex survey in §1: the phrase appears only
  in the rule text; no block applies it to a decision.

---

## 8. Places where a session states it lacks something a prior iteration had

- **B @L114 / @L139 / scratchpad C3 / commit `37eded6c` / `@L676` required
  notes.** Iteration 16's `(instruction)` item 2 — "Both arms here wrote ~4,000
  words from a 263-word task and edited three files apiece" — is recorded by B as
  "a count read off its own arms after they were in, from a probe the same round
  deleted, whose transcripts are gitignored — inadmissible under the round's own
  `(contract)` … and now uncheckable by anyone. Taken as motivation, not as
  evidence." The probe directory was deleted by A at @L363 (`rm -r
  prompt-tests/runs/release-bot-handoff`, recovery sha `0c85bfd1` recorded in the
  commit message and in A's scratchpad text). The count itself was never in
  `.ralph/agent/*`; the sentence citing it was (A @L384, deleted by B @L215).
- **B @L127 / @L139.** B re-derives, by `git log --oneline 6349fed6..7dec8051 --
  prompt-tests/general/halve-the-runbook/` (@L115/@L123), that the case had never
  been run in 16 rounds and 87 commits — only its reference edited twice. The
  `Rounds 1–14` block that A carried does not state this; the retirement
  condition naming the case lived in `sys_prompt/CLAUDE.md`, which B read at
  @L75.
- **A @L105.** A checks by `ls`/`git log` whether the `halve-the-runbook` fixture
  swap the user asked for had already happened, and concludes it had ("that ask
  seems resolved by around iteration 13 or 14").
- **A @L306 / @L316.** A discovers `/tmp/arms` already contained a prior
  iteration's files (`casedir p-a.md p-b.md r1.out r2.out`) and re-verifies both
  arm prompts by md5 before reading results.

---

## 9. Cost and placement

| | Session A | Session B |
| --- | --- | --- |
| Total tool calls | 65 | 111 |
| Calls whose input names `.ralph/agent` or runs `count-tokens`/`ralph tools memory` | 13 (@L56, 132, 197, 201, 376, 380, 384, 392, 396, 401, 409, 419, 423) | 17 (@L62, 66, 152, 194, 198, 211, 215, 225, 251, 568, 624, 628, 636, 640, 645, 649, 656) |
| Measurement calls against `.ralph` | 6 (A1–A6) | 8 (B1–B8) |
| First budget measurement | call 6, 21 s into the session | call 7, 17 s into the session |
| Mid-session compression | calls 27–28 (07:27:47–07:28:01Z), while two probe legs ran in the background | calls 30–35 (07:49:39–07:50:21Z), while two arms ran in the background |
| End-of-round housekeeping | calls 54–63 (07:43:08–07:44:20Z), 10 consecutive calls, ~72 s | calls 102–108 (08:20:35–08:21:25Z), 7 consecutive calls, ~50 s |
| Thinking blocks naming the cap/budget/trim of `.ralph` | 10 (@L60, 105, 131, 139, 196, 208, 375, 391, 400, 408) | 10 (@L70, 156, 193, 205, 210, 224, 229, 623, 635, 644) |
| Session totals crossing 6000 | once (A3 `6538`) | once (B7 `6062`) |
| Final total | `5733` | `5915` |

---

## 10. Coverage manifest

| Block type | Session A | Session B | Treatment |
| --- | --- | --- | --- |
| `thinking` | 48 | 68 | All read in full (dumped per-line via `jq`). Budget-bearing blocks quoted above; the remainder are summarized positively in §2.5 / §3.5 and concern probe design, fixture construction, arm scoring, contamination checks and waiting strategy. |
| `text` | 4 | 3 | All read. A: @L22, @L140 (`"Now building the probe. First the fixture:"`), @L253 (Skill context block for `long-bash`), @L438 (final report, quoted). B: @L22, @L589 (`"Now the run record, artifacts, and the deletion of the record this round retires."`), @L676 (final report, quoted). |
| `tool_use` | 65 | 111 | All 176 inputs read (full dump at ≤330 chars each, plus verbatim retrieval of every `.ralph`-touching input). |
| `tool_result` | 65 | 111 | Read for every `.ralph`-touching call and every `count-tokens` call; results over ~2k~tok that were skimmed structurally rather than quoted: A @L82 (prompt-tests SKILL.md, 5,391~tok), A @L95, A @L103, A @L282/@L319 (two `HANDOFF.md`, ~4.8k~tok each), A @L77 / B @L77 (`sys_prompt/CLAUDE.md` grep, ~3.2k~tok), B @L56 (task file chunk, 4,545~tok), B @L105/@L112, B @L512/@L529 (sentence-diff scripts). None of these name `.ralph/agent`. |
| attachments | 163 | 259 | Dominated by `total_tokens_reminder` (one per turn, 21~tok each) and `hook_additional_context` run-status lines. The prompt-carrying attachments (@L5–@L17 in both) are described in §2.1; the `<scratchpad>` payload is quoted in §1 and §3.1. |
| `system` | 1 | 1 | Harness record, no conversation content. |
| user string | 1 | 1 | `"Please read and execute the task in /tmp/.tmpz88Jq7"` / `…/tmp/.tmpMMjY0I`. |
| Hidden regions | none | none | No `⟐ compacted` or `⟲ rewind` lines in either skeleton. |

Plan drift during extraction: the brief asked for `wc` invocations against
`.ralph/agent/*`; no `wc` was run against those files in either session (A ran
`wc -c` on a persisted tool-result file at @L32; B ran `wc -l` on the task file
at @L39, on `prompt-tests/SKILL.md` at @L99, `wc -w` on the fixture at @L235, on
`notes/workers-bullet-hint-in-fact-position.md` at @L307 and on
`sys_prompt/CLAUDE.md` at @L577). Byte sizes of `.ralph/agent/*` entered both
sessions only through `ls -la` (A @L56, B @L62). A question added mid-extraction:
whether the budget rule's five files are all injected into the iteration prompt —
answered in §1 (only `scratchpad.md` is).
