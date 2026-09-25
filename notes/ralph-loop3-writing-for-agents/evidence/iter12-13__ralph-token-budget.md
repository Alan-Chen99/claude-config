# Evidence: `.ralph/agent/*` 6000-token budget rule — iterations 12 and 13

Focus: everything in these two sessions that touches the `.ralph/agent/*`
6000-token size rule — how the agent measured it, read it, worked within it,
what text it removed or moved elsewhere because of it, and what that removal
cost or gained.

## Provenance

**Session 1 (iteration 12)**
- Path: `/root/.claude/projects/-root-claude-config-work/06fa1252-7e72-4d2c-aea5-635ce38ed752.jsonl`
- 488 lines, model `claude-opus-5`
- Working directory: `/root/claude-config-work`
- Task input: `/tmp/.tmp4L7vJA` (a Ralph-loop task file, read via `cat` at @L23, then
  `sed -n '200,520p'` / `sed -n '520,870p'` of the harness's own copy of the
  session log at @L37/@L44 — the task file embeds the current
  `.ralph/agent/scratchpad.md`, `<ready-tasks>`, and a `ralph-tools-memories-skill`
  block documenting `ralph tools memory` usage and the Decision Journal template)
- Agent prompt source: `sys_prompt/alan-default-next.md` via `scripts/claude.sh`
  (system-prompt-file harness); `<EXTREMELY_IMPORTANT>` superpowers hook context at @L5
- Git: repo at `0f32e2ef` (iteration-11 end) at session start; ends at `d3607d7f`
- Final commit touching `.ralph/agent`: `da9f03c9 "iter12: scratchpad, decisions, memories"`

**Session 2 (iteration 13)**
- Path: `/root/.claude/projects/-root-claude-config-work/b52a94fd-7631-4e2e-aa2d-a57a8363c9bc.jsonl`
- 473 lines, model `claude-opus-5`
- Working directory: `/root/claude-config-work`
- Task input: `/tmp/.tmprsQy3j`, 788 lines, embeds `<scratchpad path=".ralph/agent/scratchpad.md">`
  containing iteration 12's rewritten scratchpad.md verbatim, and (at line 159 of
  the rendered task file, read via @L46's `sed`) the literal rule text:
  `` - `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`. relocation is growth. Cut before add. ``
- Git: repo starts at `d3607d7f` (iteration-12 end); ends after commit `3ecc2668`
- Final commit touching `.ralph/agent`: `3ecc2668 "iter13: scratchpad, decisions, memories"`

**Extraction commands used**: `agent-tools cc-pretty <path> --skeleton` (redirected
to file, since piped output triggered the harness's own truncation-and-persist
behavior); `sed -n '<n>p' <file> | jq -r '.message.content[].thinking|.text|.input.command|.content'`
per referenced line; `grep -n -i -E "count-tokens|ralph|6000|token|budget|scratchpad\.md|decisions\.md|memories\.md|summary\.md|tasks\.jsonl"` over both skeletons to locate candidate lines before reading them verbatim.

**Extractor context**: dispatched in evidence mode by a parent session, focus as
stated above.

## Rule as literally stated (source text, iteration-13 task file)

```
- `.ralph/agent/*` ≤ 6000 tokens by `agent-tools count-tokens`. relocation is growth. Cut before add.
```

This sits in a "# Rules" section of `/root/claude-config-work/PROMPT.md` alongside a
separate, differently-scoped rule: "Outside of
`/root/claude-config-work/prompt-tests/runs/` and fixtures and code-generated
content, total added tokens no more than 50000." The 6000-token rule is stated
once per session (inside the injected task file), not restated inside
`.ralph/agent/scratchpad.md` itself in either session (the scratchpad's own
"Durable method" section carries paraphrases — see below — not the rule text).

## Session 1 (iteration 12) — chronological

### Early planning: first budget mention (@L36, before any file is opened)

@L36 thinking (23~tok): "This looks like a 'ralph' loop task, so I should keep
reading to understand the full context." — no budget content yet, but this is
where the agent starts reading the harness task file that carries the rule.

### First per-file counts (@L61–@L64, early)

Command (@L61):
```
for f in .ralph/agent/decisions.md .ralph/agent/summary.md; do echo "=== $f ==="; cat "$f"; done 2>&1 | head -120; echo "===tokens==="; agent-tools count-tokens --file .ralph/agent/decisions.md; agent-tools count-tokens --file .ralph/agent/summary.md
```
Result (@L63) prints the full text of `decisions.md` (DEC-001 through DEC-016)
and, after `===tokens===`, decisions.md's and summary.md's token counts
(summary.md's tail shows `71`). `summary.md`'s content is a harness-generated
stub: `# Loop Summary / **Status:** Failed: stale loop detected / **Iterations:**
4 / ... / _No scratchpad found._ / _No events recorded._ / **Final Commit:**
3f73a56c: scratchpad: record iteration 1 commit range`.

@L68 thinking (150~tok): "I'm tallying up the token counts across the agent's
scratchpad, decisions, and summary files, then checking memories next."

### Memories read + counted (@L112–@L119)

Command (@L112): `cat .ralph/agent/memories.md | head -60; echo "===tok==="; agent-tools count-tokens --file .ralph/agent/memories.md`
Result (@L117): full memories.md content (11 entries under Patterns/Decisions/Fixes)
followed by `1788`.

@L119 thinking (77~tok): "Tallying up the .ralph/agent totals, I'm at about 5701
of 6000, cutting it close **depending on whether tasks.jsonl counts toward that
budget**." (verbatim clause on scope ambiguity — the rule's glob `.ralph/agent/*`
literally matches `tasks.jsonl` and the two `.lock` files, but the agent notes
uncertainty about whether to include it.)

### Full per-file sum, including `tasks.jsonl` (@L134–@L141)

Command (@L134):
```
ls -la .ralph/agent/ && for f in .ralph/agent/*.md .ralph/agent/tasks.jsonl; do printf "%s " "$f"; agent-tools count-tokens --file "$f"; done
```
Result (@L139):
```
total 44
-rw-r--r-- 1 root root  4617 ... decisions.md
-rw-r--r-- 1 root root  6781 ... memories.md
-rw-r--r-- 1 root root     0 ... memories.md.lock
-rw-r--r-- 1 root root 10242 ... scratchpad.md
-rw-r--r-- 1 root root   236 ... summary.md
-rw-r--r-- 1 root root   509 ... tasks.jsonl
-rw-r--r-- 1 root root     0 ... tasks.jsonl.lock
.ralph/agent/decisions.md 1245
.ralph/agent/memories.md 1788
.ralph/agent/scratchpad.md 2597
.ralph/agent/summary.md 71
.ralph/agent/tasks.jsonl 193
```
(Sum with tasks.jsonl: 5894; sum of `.md` files only: 5701 — matching @L119's
"about 5701" estimate made before this exact count was run.) `.lock` files (0
bytes) are listed by `ls -la` but never separately counted or summed.

@L141 thinking (620~tok): "I'm right at the token budget, so I need to trim
aggressively before adding anything new — compressing the iteration 10 and 11
narrative down to just the durable method and standing contracts, dropping the
run-by-run details." Also plans a new prompt-tests fixture ("where-the-bytes-go")
unrelated to the budget rule.

### Scratchpad append (@L143) — text added, not yet a rewrite

Full command appends a new "## Iteration 12" section to `.ralph/agent/scratchpad.md`
via `cat >>`. This section contains a critique (C1–C4) of iteration 11 and quotes
`sys_prompt/CLAUDE.md`'s own text on the reach-pricing bullet:

> `sys_prompt/CLAUDE.md` has said since iteration 3, and still says, that `Omit
> by default`'s reach wording *"moves detail out of the loaded file and writes
> more of it in total, against an objective that asks documentation not grow
> unbounded — relocation is growth"*, and iteration 6 narrowed it to the
> creation case.

This is the session's only occurrence of the literal phrase "relocation is
growth" — quoted as a description of what `sys_prompt/CLAUDE.md` (not
`.ralph/agent/*`) already says, in the context of critiquing a *different*
growth-related prompt bullet (about documentation reach-pricing), not the
`.ralph/agent/*` 6000-token rule itself. No `agent-tools count-tokens` call
follows this append in this block (git commit follows directly, see @L151).

### Unrelated middle section (@L150–@L461)

@L150–@L461 covers building and running a `where-the-bytes-go` prompt-test
fixture (three arms probing whether reach-pricing wording causes content
relocation), reading its results, and — in a separate thread (@L258–@L387) —
trimming `sys_prompt/CLAUDE.md` toward a 7417-token target unrelated to
`.ralph/agent`. That sys_prompt trimming loop repeats the same "count → still
over → cut a section → recount" pattern seen for `.ralph/agent` (13 rounds of
`python3` edits to `sys_prompt/CLAUDE.md` interleaved with 1-line
`agent-tools count-tokens` results: 7630→7574→7550→7593→7521→7503→7488→7434→
7424→7423→7409→7413 final), but it is a different file governed by a different,
un-stated 7417-token target mentioned only in the agent's own thinking (not
quoted from PROMPT.md in the material read). It is not part of the
`.ralph/agent/*` rule.

### End-of-round housekeeping: over budget at 6609, brought down to 5830/5834 (@L388–@L479)

@L388 thinking (446~tok): "I need to update decisions.md, memories, and
scratchpad now. Though I technically met the token cap, the process cost three
rounds of trimming and one real deletion of a methodological guard, which is
worth recording as an observed inefficiency... I'm keeping an eye on the agent
budget — it's grown to around 5894 total after adding a critique section, so I
should check whether it needs compressing."

Command (@L389): `for f in .ralph/agent/*.md .ralph/agent/tasks.jsonl; do printf "%s "; agent-tools count-tokens --file "$f"; done`
Result (@L391):
```
.ralph/agent/decisions.md 1245
.ralph/agent/memories.md 1788
.ralph/agent/scratchpad.md 3312
.ralph/agent/summary.md 71
.ralph/agent/tasks.jsonl 193
```
Sum = 6609 (decisions.md+memories.md+scratchpad.md+summary.md+tasks.jsonl =
1245+1788+3312+71+193). **This is the point in session 1 where the measured
total is above 6000** (6609 > 6000).

@L393 thinking (197~tok): "I'm over budget at 6609, so I need to trim things
down significantly. I'll compress iterations 1-11 heavily in the scratchpad,
keeping just the durable method and standing contracts, then add iteration 12's
work; I also need to shrink decisions.md while adding DEC-018, and refresh
memories by dropping stale ones and adding a couple new ones."

**Scratchpad full rewrite** (@L394, `cat > .ralph/agent/scratchpad.md <<'EOF' ...`):
replaces the entire file. Removed relative to the pre-rewrite version: run-by-run
iteration 1–11 detail (kept only as one summary paragraph: "Detail is in commit
messages... Shipped: `Omit by default` repriced by reach (3)..."); the
iteration-12 critique section is kept but shortened (C1–C4 condensed from the
@L143 append's fuller wording — e.g. C3's "given the condition it lacked" phrase
dropped, C2's "may spend its milestone" phrasing shortened). Added: a "Standing
`(contract)`" bullet capping future no-edit rounds' additions to
`sys_prompt/CLAUDE.md` (see decisions section below) and an `(instruction)` for
iteration 13 (delete `where-the-bytes-go` unless re-run; pick between the reach
clause and the "justify or delete each case" user ask). Result: `2406` tokens
(down from 3312 pre-rewrite, i.e. this file alone dropped by 906).

**Decisions full rewrite** (@L401, `cat > .ralph/agent/decisions.md <<'EOF' ...`):
compresses DEC-001–017 into one "Closed, discharged, no longer re-argued"
paragraph (each decision reduced to a parenthetical, e.g. "**DEC-016** — kill the
copy-pricing line on its mechanism: new facts ride into a rewrite, so 'before
adding a copy' names an act that never occurs"), then adds two new full entries,
DEC-018 (keep `Omit by default` after adversarial testing) and DEC-019
(paragraph-local no-growth rule for `sys_prompt/CLAUDE.md`, replacing iteration
9's whole-file token cap). Result: `1044` (down from 1245 pre-rewrite, despite
two new decisions being added — net −201).

**Memory add** (@L408, three `ralph tools memory add` calls; result @L410 lists
memory IDs) adds three new pattern/decision memories (the relocation-does-not-occur
finding; the "shipped line with unmeasured harm outranks new candidates" finding;
the "a pre-registered reading can be wrong" finding).

**Memories recount** (@L412): `agent-tools count-tokens --file .ralph/agent/memories.md` → `2239`.

@L416 thinking (154~tok): "Adding up my memory budget, I'm just under 6000
tokens but it's tight, so I should trim a stale memory to make room for
iteration 13. I'm weighing whether to drop the cleanup-sweep memory since its
lesson about grepping for digits feels fairly niche now... I'll go ahead and
delete just the cleanup-sweep memory."

**Memory delete + full-scope recount** (@L417):
```
ralph tools memory delete mem-1790038068-1b54 && for f in .ralph/agent/*.md .ralph/agent/tasks.jsonl; do printf "%s "; agent-tools count-tokens --file "$f"; done | awk '{print; s+=$2} END {print "TOTAL", s}'
```
Deleted memory's text (from the earlier full-file read, @L117): "Cleanup sweeps
that search for citation PATHS leave the NUMBERS behind. 6349fed6 removed ~53
run citations and left '6 of 8', '9 of 9', '2.2x in both arms' unsourced in the
grader-injected file. A number is not a path; grep for digits-plus-'of', not for
directory names."
Result (@L422):
```
.ralph/agent/decisions.md 1044
.ralph/agent/memories.md 2116
.ralph/agent/scratchpad.md 2406
.ralph/agent/summary.md 71
.ralph/agent/tasks.jsonl 193
TOTAL 5830
```

@L424 thinking (125~tok): "That's within the limit. Now I realize I deleted
`restated-cap` without sweeping the tree for citers as the standing contract
requires..." — triggers a separate contract check, not itself a budget action,
but surfaces a memory-content problem (see next).

**Citer sweep finds stale case-name reference inside memories.md** (@L425 grep,
result @L427): `.ralph/agent/memories.md:18` cites the deleted `restated-cap`
prompt-test case by name inside a memory's text. @L429 thinking (201~tok): "I
found that the memories file cites a deleted case, 'restated-cap,' in its
content... I should edit that memory to strip out the case name while keeping
the underlying measurement note intact." (Separately in this same thinking block
the agent notices `docs/prompt-trials/` as an unrelated stale-artifact directory
— not part of `.ralph/agent` and not acted on for budget.)

**Memory delete+replace to strip the citation** (@L442):
```
ralph tools memory delete mem-1790056284-4f2f >/dev/null && ralph tools memory add "Documentation restatement grows by ACCRETION, not addition: ... Measured two arms on a fixture stating one fact in four documents of differing character. ..." -t pattern --tags prompt-tests,writing-for-agents >/dev/null && grep -c restated-cap .ralph/agent/memories.md; echo "---budget---"; git diff --numstat 6349fed6..HEAD -- . ':(exclude)prompt-tests/runs' ':(exclude)prompt-tests/general/*/fixture' ':(exclude).ralph' | awk '{a+=$1; d+=$2} END {print "added lines", a, "deleted", d}'
```
The replacement memory drops "Measured on restated-cap, two arms" in favor of
"Measured two arms on a fixture stating one fact in four documents of differing
character" — same finding, case name removed. Result (@L444): `grep -c` returns
`0` (citation gone); separately reports the (unrelated) 50000-added-token rule's
own tally: "added lines 1978 deleted 6967" against the 50000 additions cap
outside `runs/`/fixtures/`.ralph`.

### Final commit and end-of-session recount (@L467–@L486)

Commit message (@L467) states the resulting size directly: `".ralph/agent at
5830 of 6000."` and records the contract amendment (paragraph-local no-growth
rule) as the round's process finding.

Final recount (@L475):
```
agent-tools count-tokens --file sys_prompt/CLAUDE.md && for f in .ralph/agent/*.md .ralph/agent/tasks.jsonl; do agent-tools count-tokens --file "$f"; done | awk '{s+=$1} END {print "ralph total", s}' && git log --oneline 0f32e2ef..HEAD
```
Result (@L477): `7413` (sys_prompt/CLAUDE.md) then `ralph total 5834` (this
count differs from the commit message's 5830 by 4 tokens — taken after the
`sed -i` edit at @L471 which updated the scratchpad's own iteration-12 heading
from a placeholder commit hash to the real one, adding a few characters).

Final report text (@L486) restates: `` `sys_prompt/CLAUDE.md`  → 7413   (was
7417) `` in its "Evidence" code block, and under "Updates" states the DEC-019
contract amendment in full. Does not separately restate the `.ralph/agent`
5834/6000 figure in the final report prose (it is in the commit message only).

## Session 2 (iteration 13) — chronological

### Task file carries forward iteration 12's scratchpad verbatim (@L34)

Result of `cat` on the task file (788 lines) contains `<scratchpad
path=".ralph/agent/scratchpad.md">` wrapping the exact text iteration 12 wrote
at its @L394 rewrite (confirmed identical section-by-section, including the
"Standing `(contract)`" bullets and the iteration-12 critique/instruction
sections).

### Rule text located in the task file (@L46)

`sed`-derived rendering of the task file's "# Rules" section (read at @L46, full
text captured above under "Rule as literally stated"), including the adjacent,
differently-scoped 50000-added-token rule and the Decision Journal / memory-tool
usage documentation (confidence thresholds, `ralph tools memory add/search/prime`
examples) — these are harness/skill instructions about *how* to write to
`.ralph/agent/decisions.md` and memories, not the size rule itself.

### First iteration-13 per-file count (@L129–@L131), `.md`-only scope

Command (@L129): `ls -la .ralph/agent/ && for f in .ralph/agent/*.md; do echo -n "$f: "; agent-tools count-tokens --file "$f" 2>&1 | tail -1; done`

This command's glob is `.ralph/agent/*.md` — it does **not** include
`tasks.jsonl`, unlike several of iteration 12's equivalent commands (@L134,
@L389, @L475, @L417) which explicitly appended `.ralph/agent/tasks.jsonl` to the
loop.

Result (@L131):
```
total 44
-rw-r--r-- 1 root root 3961 ... decisions.md
-rw-r--r-- 1 root root 8265 ... memories.md
-rw-r--r-- 1 root root 9729 ... scratchpad.md
-rw-r--r-- 1 root root  236 ... summary.md
-rw-r--r-- 1 root root  509 ... tasks.jsonl
.ralph/agent/decisions.md: 1044
.ralph/agent/memories.md: 2111
.ralph/agent/scratchpad.md: 2415
.ralph/agent/summary.md: 71
```
(decisions.md's 1044 matches iteration 12's end-of-session value exactly;
memories.md 2111 and scratchpad.md 2415 are close to, but not identical to,
iteration 12's final in-session values of 2116/2406 — the small deltas reflect
edits iteration 12 made after those last counts, e.g. the @L471 `sed -i` on the
scratchpad heading.)

@L133 thinking (590~tok): "I'm tight on token budget, so I need to keep
additions minimal." — precedes designing a new prompt-test fixture
("two-homes"); the rest of this thinking block is fixture design, not
`.ralph/agent` content.

### Middle of session: unrelated case-deletion and sys_prompt work (@L165–@L323)

@L170–@L177: deletes the `where-the-bytes-go` prompt-test run/case per
iteration 12's instruction (`git rm -r -q prompt-tests/runs/where-the-bytes-go
prompt-tests/...`), confirmed clean via `grep -rn 'where-the-bytes-go'`
(@L172 result: only self-references in `.ralph/agent/scratchpad.md:139` and the
run's own README, both expected).
@L310–@L319: edits `sys_prompt/CLAUDE.md` and the prompt itself
(`sys_prompt/alan-default-next.md`), counted separately (`CLAUDE.md now: 7412
CLAUDE.md before: 7413`) — not `.ralph/agent`.
@L320–@L322 greps `.ralph/agent/scratchpad.md` for the phrase "priced by
reach"/"by reach" (result: line 19, the "Price a document by reach before size"
durable-method bullet) as part of checking whether that bullet's wording needs
correcting given the round's finding — a content-accuracy check, not a
budget check.

### End-of-round housekeeping: over budget twice, brought down from 6370 → 6046 → 6004 → 5953 (@L349–@L410)

@L349 thinking (47~tok): "I need to trim the token budget across decisions,
memories, and scratchpad to stay under 6000 total, so I'll compress the
scratchpad while keeping the durable method and contract intact."

**Scratchpad full rewrite** (@L350, `cat > .ralph/agent/scratchpad.md <<'EOF' ...`):
Removed from the "Durable method" section: the "(iter 12)" tags on now-absorbed
bullets, and (per the later @L401 edit, see below) eventually the "Price a
document by reach before size" bullet's expanded form. Added: a new bullet ("A
line that names a consideration does not deliver the conclusion it argues for
... Measured twice on `Omit by default`'s reach wording"), a bullet on
pre-registered exclusions ("A pre-registered exclusion binds hardest when the
excluded number turns out to be the only one favouring your prior"), a bullet
("A clause no fixture can exercise is not an open question; it is a deletion
candidate with an outstanding test"), a new contract line ("An `(instruction)`
asserting that work is undone states the command that shows it"), and a fresh
"## Iteration 13" section (critique C1–C4 of iteration 12, the round's
`two-homes` work, and an `(instruction)` for iteration 14). Iterations 1–11
detail is compressed further into "## Iterations 1–12" (one paragraph). Result:
`2267` (down from 2415 pre-rewrite).

@L358 thinking (52~tok): "The scratchpad shrank to 2267 from 2415, bringing..."

**Decisions append** (@L363, `cat >> .ralph/agent/decisions.md <<'EOF' ...`):
appends DEC-020 (cut the reach wording, conf 76) and DEC-021 (delete
`platform-portability` case rather than repair its justification, conf 70) —
this is an addition, not a rewrite, and grows the file.

**Full-scope recount, `.md`-only** (@L367):
```
tot=0; for f in .ralph/agent/*.md; do n=$(agent-tools count-tokens --file "$f" | tail -1); echo "$f: $n"; tot=$((tot+n)); done; echo "TOTAL: $tot / 6000"
```
Result (@L369):
```
.ralph/agent/decisions.md: 1693
.ralph/agent/memories.md: 2339
.ralph/agent/scratchpad.md: 2267
.ralph/agent/summary.md: 71
TOTAL: 6370 / 6000
```
**This total (6370) is above 6000** — the first over-budget measurement in
session 2. (This sum excludes `tasks.jsonl`; had `tasks.jsonl`'s ~193 tokens from
the prior session been added, the total would be higher still — `tasks.jsonl`
was not independently recounted in this session.)

@L374 thinking (130~tok): "I'm over budget by 370, so I need to cut before
adding anything new — decisions.md grew by 649 and memories.md by 228, so I'll
trim there. I'm looking for old DEC entries whose re-evaluate conditions have
fired or that are now superseded, like DEC-018 on testing the incumbent."

**Decisions edited via Python (collapse DEC-018)** (@L379): a `python3` script
replaces the full DEC-018 block (5 lines: Chosen/Alternatives/Reasoning/Re-evaluate/
Framing-bias/Independent-evaluation) with a 4-line collapsed form: "## DEC-018 —
keep `Omit by default` after adversarial testing (iter 12, conf 84) — **half
superseded by DEC-020** / - Kept on measurement that the relocation harm it
shipped with cannot occur on a writing task. Its re-evaluate condition — a
fixture with two live destinations of different reach — fired at iteration 13
and the reach half went. The existence pricing it endorsed stands." Also
shortens the DEC-007 mention in the "Closed, discharged" paragraph from a
3-line description to "**DEC-007** — price by reach (iter 3), **reversed by
DEC-020**."
Recount (same command block) result (@L381):
```
.ralph/agent/decisions.md: 1369
.ralph/agent/memories.md: 2339
.ralph/agent/scratchpad.md: 2267
.ralph/agent/summary.md: 71
TOTAL: 6046 / 6000
```
**Still above 6000** (6046).

@L383 thinking (22~tok): "Still 46 over the limit, so I need to cut a memory —
let me scan for one that's stale."

**Memory list + inspect** (@L384/@L386, @L389/@L391): lists all 16 memory IDs
with truncated content; @L388 thinking (76~tok): "One memory entry is now
outdated since a later iteration showed the reach arm added more, so I need to
correct rather than just delete it... I'm leaning toward removing a different
entry instead, one about downstream readers not needing that detail." (This
"leaning" is not what the agent ends up doing — see next.) `ralph tools memory
show mem-1790057525-82a3` (@L389) displays the full text of the memory the
agent ultimately deletes: "Pricing what an agent writes (Omit by default,
either wording) suppresses a second copy and suppresses unrequested
imperatives; it does NOT cause relocation... No arm relocated anything - the
task's subject bounds the edit, so relocation-as-growth is a cleanup-task
hazard only." — this memory's claim ("does NOT cause relocation... suppresses a
second copy") is contradicted by session 13's own DEC-020 finding (the reach
arm in `two-homes` reached three code files a documentation task never named).

**Memory delete+replace** (@L396):
```
ralph tools memory delete mem-1790057525-82a3 ... && ralph tools memory add "Pricing what an agent writes suppresses unrequested additions, but only the EXISTENCE wording does so cleanly. Two fixtures: existence-priced arm edited no code and said why; unpriced arm added one or two imperatives to auto-loaded files; the REACH-priced arm was worst, editing three code files a documentation task never named, because reach reasoning argues 'put it where the reader will be'. No arm ever relocated anything -- the task's subject bounds the edit." -t pattern --tags sys-prompt,writing-for-agents ... && tot=0; for f in .ralph/agent/*.md; do n=$(agent-tools count-tokens --file "$f" | tail -1); tot=$((tot+n)); done; echo "TOTAL: $tot / 6000"
```
Result (@L398): `Memory deleted: mem-1790057525-82a3 / Memory stored:
mem-1790058772-3394 / TOTAL: 6004 / 6000`. **Still above 6000** (6004), though
by only 4.

@L400 thinking (67~tok): "I'm a few tokens over budget, so I need to trim the
scratchpad slightly. Rather than cutting the line about rubrics not being able
to score outcomes shaped by failure, since that's still useful, I'll just
shorten the entry about pricing a document by reach before size."

**Final scratchpad trim** (@L401): a `python3` script deletes one paragraph
outright (no replacement text) from `.ralph/agent/scratchpad.md`:
```
**Price a document by reach before size** — as an editor deciding what to cut.
Note this is not the same act as a *prompt line* telling an agent to price by
reach, which iteration 13 measured and cut.
```
Recount (same command) result (@L403): `TOTAL: 5953 / 6000` — first
under-6000 total in session 2's end-of-round pass.

@L405 thinking (82~tok): "Good, 5953 out of 6000 tokens used. I should
double-check whether prompt-tests documentation still lists cases needing
platform-portability removal, sweep once more, and confirm git is clean after
committing — then finalize scratchpad.md with the iteration number and the
starting/ending commit range as the contract requires."

### Final commit and report (@L410, @L450, final text block)

Commit message (@L410) states: "`.ralph/agent/* at 5953/6000 tokens: DEC-018
collapsed to its superseded half and one memory replaced rather than added.`"

Final report text (last assistant text block) restates under "Updates": "Event
published: `work.iteration`. Tree clean. `.ralph/agent/*` at 5953/6000 tokens
(cut before adding: DEC-018 collapsed, one memory replaced not added)." No
separate `.ralph/agent`-only `agent-tools count-tokens` call appears after
@L403 in this session (the emit call at @L450 does not recompute the budget).

## `summary.md` and `tasks.jsonl` — read-only status confirmed by grep

A search for any `cat >`/`cat >>` (or equivalent write) command targeting
`.ralph/agent/summary.md` in either session's full command history returns no
match; the only appearances of `summary.md` in either transcript are inside
`for f in .ralph/agent/*.md ...` count loops and the one-off `cat` read at
session 1's @L61. Its token count (71) is identical every time it is measured,
in both sessions. `tasks.jsonl` is likewise never rewritten by either session; it
is only read via `wc`/`count-tokens` loops, and only in session 1's loops that
explicitly append it to the glob (@L134, @L389, @L417, @L475) — session 2's
equivalent loops (@L129, @L367, @L379, @L396, @L401) all use `.ralph/agent/*.md`
and never separately count `tasks.jsonl`.

## Rough cost: tool-call count for this housekeeping

- Session 1 (iteration 12): 488 JSONL lines total, 132 assistant turns. A
  command-text search over all Bash tool inputs for `count-tokens`, `ralph tools
  memory`, or a `.ralph/agent` path match returns 33 matching Bash calls (this
  includes the two reads of decisions.md/summary.md/memories.md early, the
  count-and-recount loop at end-of-round, and the `ralph tools memory
  add`/`delete` calls; it excludes the unrelated `sys_prompt/CLAUDE.md` trimming
  loop and the `where-the-bytes-go` fixture work). The end-of-round housekeeping
  block specifically (@L388 thinking through the final commit at @L467) spans
  roughly lines 388–478 of a 488-line file — i.e., the last ~2% of session
  lines but a concentrated run of 8 `agent-tools count-tokens`/sum calls plus 5
  `ralph tools memory` add/delete calls plus 2 full-file rewrites (scratchpad,
  decisions).
- Session 2 (iteration 13): 473 JSONL lines total, 127 assistant turns. Same
  search returns 20 matching Bash calls. The end-of-round block (@L349 thinking
  through the final commit at @L410) spans roughly lines 349–410 of a 473-line
  file, containing 3 full sum-and-recount loops (6370 → 6046 → 6004 → 5953), one
  full scratchpad rewrite, one decisions.md append, one decisions.md
  Python-script edit, one memory list, one memory show, one memory delete+add,
  and one final Python-script paragraph deletion.
- In both sessions, the housekeeping block sits at the end of the round,
  immediately before the final `git add -A .ralph && git commit` and the
  `ralph emit`/final-report text block; no budget-related command appears
  earlier than roughly the first quarter of either session (session 1's first
  count is @L61 of 488; session 2's first count is @L129 of 473, though the
  rule text itself is read once, early, at @L46).

## What was NOT found

- Neither session runs a bare `wc` (word count) call against any `.ralph/agent`
  file as a stand-in for `agent-tools count-tokens`; every size check in both
  sessions uses `agent-tools count-tokens --file <path>`, matching the rule's
  named tool.
- Neither session concatenates all `.ralph/agent/*` files into one buffer and
  runs `agent-tools count-tokens` once; both always sum per-file counts
  (`agent-tools count-tokens --file X` called once per file, results added via
  shell arithmetic `awk`/`$((...))`), so the recorded total is a sum of
  independently-tokenized files rather than one tokenization of the
  concatenation.
- No content from `.ralph/agent/*` in either session is moved into
  `sys_prompt/CLAUDE.md`, a skill file, `notes/`, or `prompt-tests/` as a
  stated consequence of the 6000-token rule specifically — content that leaves
  `.ralph/agent/scratchpad.md` or `decisions.md` in both sessions is either
  deleted outright (the cleanup-sweep memory in session 1; the "Price a
  document by reach before size" expanded paragraph in session 2) or condensed
  in place (iteration narratives compressed into shorter paragraphs of the same
  file), not relocated to another destination file. The literal phrase
  "relocation is growth" appears only inside `.ralph/agent/scratchpad.md`
  itself (added by session 1's @L143 append and carried through both sessions'
  rewrites), quoting `sys_prompt/CLAUDE.md`'s separate reach-pricing bullet — it
  is not applied by either session as a description of moving content out of
  `.ralph/agent/*`.
