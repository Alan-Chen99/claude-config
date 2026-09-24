# Evidence: `.ralph/agent/*` 6000-token ceiling — iterations 18 and 19

Focus: everything in these two sessions that touches the `.ralph/agent/*`
6000-token size rule — how the agent measured it, read it, worked within it,
what text it removed or moved elsewhere because of it, and what that removal
cost or gained.

## Provenance

**Session A (iteration 18)**
- Path: `/root/.claude/projects/-root-claude-config-work/08ce9bfe-bac1-4a3e-aa24-a57e4937f576.jsonl`
- 508 lines, model `claude-opus-5`
- Working directory: `/root/claude-config-work`
- Task input: `/tmp/.tmpVxHFJr` (read via `cat` at @L23, contents include `.ralph/agent/*` and the ralph-tools skill blocks)
- Harness: Claude Code, `--system-prompt-file` launch (attach blocks present: environment, model, skill_listing, instructions, session_context, date)
- Extraction commands: `agent-tools cc-pretty <path> --skeleton`, `agent-tools cc-pretty <path> --skeleton --show-all`, `sed -n '<n>p' <path> | jq -r '.message.content[]...'`
- Extractor brief: session-analysis evidence-mode dispatch, focus as stated above.

**Session B (iteration 19)**
- Path: `/root/.claude/projects/-root-claude-config-work/9bb51163-bc6a-40ff-babb-f68670a9edfc.jsonl`
- 782 lines, model `claude-opus-5`
- Working directory: `/root/claude-config-work`
- Task input: `/tmp/.tmpsyA0cm`
- Harness: same as session A
- Extraction commands: `agent-tools cc-pretty <path> --skeleton --show-all --agent` (chunked to two files, `/tmp/cc-pretty-9bb51163-1.txt`, `/tmp/cc-pretty-9bb51163-2.txt`), then targeted `sed -n '<n>p' <path> | jq -r ...` per ref.
- Relationship to session A: session B is the next loop iteration; it reads session A's git commits and `.ralph/agent/*` file state as its starting point (no direct session-to-session dispatch; state is passed via the repo, not via Agent tool).

Both sessions are single-agent (no subagent dispatch touches `.ralph/agent/*`; session A does dispatch two `Agent` blind-reader subagents at @L265 and @L362, but those read files under `/tmp/blind.*`, unrelated to `.ralph/agent/*`).

---

## Iteration 18 (session A)

### First measurement — mid-session orientation, @L125–129

Command (@L125):
```
ls -la .ralph/agent/ && agent-tools count-tokens --file .ralph/agent/scratchpad.md 2>&1 | tail -2 && for f in .ralph/agent/*.md; do echo "$f: $(agent-tools count-tokens --file $f 2>/dev/null | tail -1)"; done
```
Result (@L127):
```
total 44
-rw-r--r-- 1 root root  5401 Sep 22 08:20 decisions.md
-rw-r--r-- 1 root root  7412 Sep 22 08:21 memories.md
-rw-r--r-- 1 root root     0 Sep 22 00:47 memories.md.lock
-rw-r--r-- 1 root root 10310 Sep 22 08:21 scratchpad.md
-rw-r--r-- 1 root root    93 Sep 22 07:50 summary.md
-rw-r--r-- 1 root root   509 Sep 22 04:57 tasks.jsonl
-rw-r--r-- 1 root root     0 Sep 22 00:34 tasks.jsonl.lock
2583
.ralph/agent/decisions.md: 1441
.ralph/agent/memories.md: 1877
.ralph/agent/scratchpad.md: 2583
.ralph/agent/summary.md: 24
```
Sum of the four `*.md` files named: 1441+1877+2583+24 = 5925. `tasks.jsonl` is **not** counted (the glob is `.ralph/agent/*.md`, which excludes the `.jsonl` file and both `.lock` files).

Thinking @L129 (14~tok, before the command executes): "I should look at the entire file to get the full p…" (orientation, not budget-specific).
Thinking @L129 (50~tok, after the result): "I'm close to the token limit, around 5925, so I need to cut content before adding anything new to the scratchpad. Let me check decisions.md and memories.md first to see what's already recorded there."

This is the first point in the session where a `.ralph/agent` count is read against the ceiling, and the agent explicitly frames it as "cut before adding."

### Scratchpad edit 1 — @L163–165: adds iteration-17 summary + iteration-18 critique/milestone text

Python script rewrites `.ralph/agent/scratchpad.md`, inserting after locating `"## Iteration 17 —"`:
- A one-paragraph "## Iteration 17" summary.
- A full "## Iteration 18" section: "### Critique of prior iterations" (C1, C2, C3 — see full text in git commit `b22b7411`, quoted below), "### Why this milestone", "### The round's work".

Result (@L165): `agent-tools count-tokens --file .ralph/agent/scratchpad.md` → **2644** (up from 2583).

### Scratchpad edit 2 — @L167–173: compress "History — rounds 1–16" to pay for edit 1

Thinking @L167: "I'm running tight against the length limit, so I need to trim the durable method section further, cutting entries that now overlap with contract lines already captured elsewhere. I'll keep the short, load-bearing ones... The safest cut is the 'History — rounds 1–16' paragraph, since it's largely duplicated by CLAUDE.md and commit messages, and the user's rule says outdated info belongs only in git history — so I'll compress that section hard."

Command (@L168) replaces the `## History — rounds 1–16` section. Full removed text (from `git show b22b7411`):
```
Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`, the durable home and the one to read before touching the
block. Shipped across the loop: `Say what ends it` added (9); `Omit by default`
repriced to reach (3) and back to existence (13); the `Claim less` hedge clause
cut (4) and the whole bullet with it (14); the case corpus bound to the prompt by
one grep, eleven of fifteen cases deleted (15). Failed candidates: five wordings
aimed at claim-handling (6–8, 14) — the node is premise **provenance**, not
wording, and what discharges a premise is an action; one at copy-pricing (12) —
the task's subject bounds the edit, so relocation-as-growth cannot occur on a
writing task; one at warrant-transcription (16) — a rules section's heading is
what flattens a preference, and a clause only competes with the genre. Round 10
fixed a nine-round harness contamination and voided every arm stored before
2026-09-22. Round 15 ran the block whole against an arm with no block: the arms
parted on one row in the block's favour and `Omit by default` was untouched.
```
Replaced with:
```
Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped across the loop: `Say what ends it` (9); the case corpus
bound to the prompt by one grep, eleven of fifteen cases deleted (15). Deleted:
`Omit by default` (13, 17), `Claim less` (4, 14). Seven candidate wordings failed
(3–8, 12, 14, 16). Round 10 fixed a nine-round harness contamination and voided
every arm stored before 2026-09-22.
```
The same diff (per `git show b22b7411`) also deletes the entirety of the old
"## Iteration 17" critique section (its own C1/C2/C3, ~500 words covering the
`halve-the-runbook` retirement-condition ratchet, an outcome-classification
override, and an inadmissible-evidence point) and the old "### The round's
result" section, replacing them with the shorter iteration-17/18 text from
edit 1 above.

Result: `agent-tools count-tokens --file .ralph/agent/scratchpad.md` → **2504**.
Commit `b22b7411` ("iter18: critique of 16 and 17, and the round's reason for
existing") follows immediately in the same command, with commit-message body
restating C1/C2/C3 in compressed form (quoted in full at @L168 tool input) and
trailer `Claude-Session: 08ce9bfe-bac1-4a3e-aa24-a57e4937f576`.

### Second full-budget tally and decisions.md/memories.md pass — @L430–462

Thinking @L430: "I'm tallying the token budget across scratchpad, decisions, and memories, and realize the total is running about 400 over — so I need to trim something. I'll cut the corpus-binding memory entry since that rule is now already captured in the shipped skill, making it redundant. Now I'm also deleting the older --hide-cmdline memory since it's superseded by the new naming rule that lives durably in the skill, and I'll compress the 'Closed, discharged' block in decisions to recover the rest of the savings. I need to use the memory-delete CLI tool rather than manual file edits, per the rule against using echo/cat for memory writes."

Command @L431: `ralph tools memory delete mem-1790061545-2f77 && ralph tools memory delete mem-1790058735-2e30 && echo deleted` — both deleted successfully (@L433).

Command @L438 adds three new memories via `ralph tools memory add` (not `echo`/`cat`):
1. "A claim-handling reading saturates when the fixture's handover STATES the gap..." (tags `pattern, prompt-tests, test-design, writing-for-agents`)
2. "A null from a saturated baseline bounds the FIXTURE, not the clause..." (tags `pattern, prompt-tests, test-design`)
3. "A probe directory sharing a word with its own fixture is found by the tested agent's ordinary search..." (tags `fix, prompt-tests, contamination`)

Same command tail: `for f in .ralph/agent/memories.md; do echo -n "$f: "; agent-tools count-tokens --file $f; done` → **2097**.

Thinking @L442: "Memories are now at 2097, up 220, pushing the total to 6066 — over budget. I need to trim decisions.md more aggressively, compressing the closed block down to around 1100 before adding the new DEC-027 entry, and leave some room for scratchpad growth too. Still over budget even after that. The real fix is gutting the 'closed, discharged, no longer re-argued' block — those old decision summaries (DEC-001–024) are already captured in git and CLAUDE.md, so per the rule that outdated info belongs in git history only, I can cut them to a few lines. Similarly DEC-025 and DEC-026 are discharged and can shrink to one line each, leaving DEC-027 as the only fully detailed entry. That should bring decisions.md down to roughly 330 tokens and the total to about 5105, well within range."

Command @L443: `cat > .ralph/agent/decisions.md <<'EOF' ...` — rewrites the whole file: a one-paragraph "**Closed.** DEC-001–026, rounds 1–17" summary (replacing the previous itemized entries) plus the new "DEC-027 — ship no prompt edit; keep the preamble and withdraw outcome 2's second half" entry in full (Chosen/Alternatives/Reasoning/Re-evaluate/Framing bias/Independent evaluation/Reversibility fields).

Result (@L445): `agent-tools count-tokens --file .ralph/agent/decisions.md` → **753** (down from 1441 at session start).

### Third scratchpad edit and running per-file tally — @L450–457

Command @L450 replaces the "### The round's work" section (previously naming `prompt-tests/runs/inherited-project/README.md`) with a longer "### The round's work and result" section, plus a new "`(contract)` added" block (the null-as-saturated-not-finding rule) and a new "`(instruction)` for iteration 19" list (3 items, including item 3 forecasting round 20 as a cleanup round).

Same command's tail: `agent-tools count-tokens --file .ralph/agent/scratchpad.md; for f in .ralph/agent/*.md; do echo -n "$f "; agent-tools count-tokens --file $f; done | awk '{s+=$2; print} END {print "TOTAL", s}'`

Result (@L452):
```
2880   (scratchpad total after this edit)
.ralph/agent/decisions.md 753
.ralph/agent/memories.md 2097
.ralph/agent/scratchpad.md 2880
.ralph/agent/summary.md 24
TOTAL 5754
```
Thinking @L454: "Good, under the length limit. The contract I added in the round section should really live in the Standing contract block at the top for coherence... I also need to record the ending commit hash for this round — currently it shows the starting commit — so I'll do a final commit after moving the contract line."

Command @L455 moves the `(contract)` block from the round section into the "Standing contract" block near the top of the file, appending `*(18)*` as a provenance tag. Result (@L457): scratchpad.md → **2881** (net +1 from the move).

### Task/commit and final total — @L459–476

Command @L459 creates a ralph task (`loop3:iter18`) and commits (`git commit -q -m "iter18: scratchpad, decisions, memories ..."`), with the commit body stating: `.ralph/agent total: 5754 tokens.` and trailer `Claude-Session: <id>`. Commit hash: `2a6bf912`.

Command @L474 updates the scratchpad's own iteration-18 heading from `(this round)` to the actual ending commit hash (`2a6bf912`), then commits again as `5c185783`... actually the commit at @L474 produces `5c185783 iter18: commit range e13d1097 -> end of round`. (This is the pattern iteration 19's episode later calls "the budget line stops being self-referential" — updating a heading that names a commit hash, after the fact, is itself a file edit, though iteration 18 did not re-check the token total after this specific edit.)

### Final self-report (stop-hook text, @L503)

States: "`.ralph/agent` total 5754 tokens (limit 6000), after compressing the decision journal and deleting two memories now durable in the prompt-tests skill." Also, under "Required notes" → "context waste": "the task file's four embedded ralph skill blocks (~2,400 words on memory/task CLI usage) repeat each other almost verbatim — `ralph-tools` contains the whole of `ralph-tools-memories` and most of `ralph-tools-tasks`." (Not acted on within this session; re-surfaced verbatim in iteration 19's own "Required notes", see below.)

### Iteration 18 measurement-scope summary

- Iteration 18's own count-tokens commands only ever glob `.ralph/agent/*.md` (once) or explicitly name the four `.md` files (all other calls). `tasks.jsonl` (509 bytes at session start) is never included in any iteration-18 total. Lock files (`memories.md.lock`, `tasks.jsonl.lock`, both 0 bytes) are never globbed either.
- The rule as given to the agent (per the dispatching brief) reads `.ralph/agent/*` — a bare glob with no extension filter. Iteration 18's commands (`*.md`) do not match that literal wording; they are narrower.
- Iteration 18's final reported number is **5754** (sum of decisions.md 753 + memories.md 2097 + scratchpad.md 2881 [measured at 2880/2881 depending on edit] + summary.md 24).

---

## Iteration 19 (session B)

### Orientation reads @L82–120 (skill/prompt reads, not yet budget-specific)

The session reads `sys_prompt/CLAUDE.md`'s "Writing for other agents" section, `prompt-tests/general/retirement-policy/`, the `prompt-tests` skill, and the corpus-ownership grep, before reaching the `.ralph/agent` measurement.

### First measurement — @L121–125: full-glob total including tasks.jsonl, exceeds ceiling

Command (@L121):
```
for f in .ralph/agent/*.md .ralph/agent/*.jsonl; do echo -n "$f: "; agent-tools count-tokens --file "$f" 2>/dev/null || echo ERR; done; echo "=== total:"; cat .ralph/agent/*.md .ralph/agent/*.jsonl > /tmp/ralphall.txt 2>/dev/null; agent-tools count-tokens --file /tmp/ralphall.txt
```
Result (@L123):
```
.ralph/agent/decisions.md: 753
.ralph/agent/memories.md: 2097
.ralph/agent/scratchpad.md: 2890
.ralph/agent/summary.md: 24
.ralph/agent/tasks.jsonl: 358
=== total:
6122
```
This is the first count in either session that globs `.ralph/agent/*.jsonl` alongside `*.md`, and the first to include `tasks.jsonl`'s token cost (358) in the total. It reports **6122**, over the 6000 ceiling — 368 more than iteration 18's self-reported 5754, and this discrepancy is not because the files grew between iteration 18's final commit and this read (`decisions.md` 753, `memories.md` 2097 match iteration 18's own numbers exactly; `scratchpad.md` differs slightly, 2890 vs 2881, from iteration 18's subsequent commit-range-hash edit) but chiefly because `tasks.jsonl` (358 tokens) was never counted by iteration 18.

Thinking @L125: "6122 tokens exceeds the 6000-token budget rule for `.ralph/agent/*` — that's a concrete violation from iteration 18 I need to flag and fix. I should check tasks.jsonl and memories, which have grown to 358 and 2097 tokens respectively, to see where to trim."

### Historical re-measurement across commits — @L138–142

Command (@L138) checks out `.ralph/agent/{scratchpad,memories,decisions,summary}.md` and `tasks.jsonl` at three shas (`e13d1097` = end of iter17, `7dec8051` = end of iter16, `HEAD` = current) via `git show <sha>:<path>`, concatenates, and counts each:

Result (@L140): `e13d1097: 6118`  `7dec8051: 5926`  `HEAD: 6122`

This is the full-glob-including-tasks.jsonl measure applied retroactively: it shows iteration 16 ended under budget (5926), but **iteration 17 already ended over budget (6118)**, and iteration 18 grew it further to 6122 — by this counting method, neither of the two prior rounds' own self-reported numbers (which, per iteration 18's session, used the narrower `*.md`-only glob) caught the breach.

Thinking @L142 (long block): identifies this as "C1" for the round's required critique — "a hard user budget unmeasured and breached for two rounds" — and separately notes as a candidate second critique that iteration 18 withdrew a claim from `sys_prompt/CLAUDE.md` but left the "identical claim" standing in `.ralph/agent/memories.md` (`mem-…-53ee`, "auto-injected into every later round's context"). Also raises, then sets aside for lack of concreteness, a broader worry that the repo's total footprint (a separate 50,000-token budget, "outside runs/fixtures", unrelated to the `.ralph/agent` 6000 ceiling) may not be shrinking even as this one block gets trimmed.

### 50,000-token repo-budget check (separate from the 6000 `.ralph/agent` ceiling) — @L143–159

Commands @L143–@L155 compute added/deleted lines since the loop's base commit `9f6c03a0`, excluding `prompt-tests/runs` and `*/fixture/*`, then token-count the added lines: **18006** (@L155) net-added-lines count printed at that step; thinking @L159 states "I've used 17,917 of the 50,000 token budget, about 36% after 18 rounds." This is a distinct, separate budget (total repo growth) from the `.ralph/agent/*` 6000-token ceiling that is this artifact's focus; it is not re-measured again in this session and does not affect the `.ralph/agent` trimming that follows.

### Critique written to scratchpad, first draft — @L178

Command @L178 rewrites `.ralph/agent/scratchpad.md` (via `head -130` + `cat >>`), adding a "## Iteration 19" section with "### Critique of prior iterations" — full text:

> **C1 (workflow — a hard user budget unmeasured and breached for two rounds).**
> `.ralph/agent/*` ≤ 6000 tokens is a user rule, and nothing in the loop ever ran
> the command that checks it. Measured now: 5926 at 16's end, 6118 at 17's, 6122 at
> 18's. Both rounds grew the directory past the ceiling while writing about the
> danger of unbounded documentation. The rule's own words — *relocation is growth,
> cut before add* — were the round-13 method note, applied to everything except the
> file it was written in. Cut here, and the check is now a `(contract)` line with
> the command in it, because a rule with no command is what let two rounds miss it.
>
> **C2 (fact — a claim withdrawn from one file and left standing in the file the
> next round actually reads).** 18's own C2 established that 16's *the genre
> supplies the frame and a prompt clause only competes with it* rests on a
> saturated baseline, and deleted the paragraph from `sys_prompt/CLAUDE.md`. The
> same conclusion survived verbatim in `.ralph/agent/memories.md`
> (`mem-…-53ee`), which is auto-injected into every later round's context — so the
> withdrawal reached the file a round consults deliberately and missed the one it
> cannot avoid. Memory deleted here. The contract's citer-sweep covers renames of
> things a document points at, not claims; extended below.
>
> **C3 (workflow — a probe promoted to a permanent case with no round deciding
> to).** 18's record opens *A probe*, and the skill it had just edited says a probe
> lives entirely in `prompt-tests/runs/<probe>/` so that one `rm -r` ends it. The
> round instead put `task.md`, `fixture/` and `reference-solution.md` into
> `prompt-tests/general/inherited-project/` and then named that path in two
> `sys_prompt/CLAUDE.md` retirement conditions, which makes the ownership grep keep
> it indefinitely. Added without approval, removable only by a human or by a round
> that retires the preamble: the objective's own ratchet, built by the round whose
> milestone was the ratchet. The case is not deleted — the conditions genuinely
> need it — but no later round should read its existence as a promotion argument,
> and the `(contract)` below stops the record half of it recurring.

(C1 directly names the rule's own text, "relocation is growth, cut before add",
as itself the round-13 method note, and observes it was "applied to everything
except the file it was written in" — i.e. the rule text lived inside
`.ralph/agent/*` and was itself never weighed against its own ceiling until now.)

Followed by "### Why this milestone" (`Say what ends it` is the only shipped line never isolated) — this section is about the round's prompt-test milestone, not the token budget.

Thinking @L172 (before this edit): "I'm going to trim the bulky iteration 18 section d…" (planning the compression that produced the shortened "## Iterations 17–18" summary paragraph replacing iteration 18's own separately-written iteration-17/18 sections).

Result (@L180): `184 /tmp/sp-new.md` (line count only; no token count taken yet at this step).

### Contract-block edits — @L185–199

Thinking @L185: "I need to add contract amendments covering budget checks, probe record directory cleanup tied to claims in CLAUDE.md, and withdrawal sweeps of .ralph/agent/. Since the contract section sits within the head -130 range, I'll insert these as a separate edit afterward." Commands @L186–197 read and restructure the "Standing `(contract)`" block (no token count taken between these edits).

### Memory delete + budget re-check — @L201–205

Command @L202: `ralph tools memory delete mem-1790062999-53ee 2>&1 | tail -3...` — deletes the memory named in C2. Result (@L204): `Memory deleted: mem-1790062999-53ee --- 0 5938` (the `5938` figure appears to be a running scratchpad-or-partial total taken as part of this compound command).

Thinking @L206: "Still under budget but I'll trim more later — I'll..." — proceeds to build the `retirement-policy` fixture/pre-registration and launch the round's two test arms (@L215–L465), which is the round's prompt-test work, not `.ralph/agent` budget work; no `.ralph/agent` count-tokens calls occur during the arm-launch-and-wait span (@L215–L659).

### Post-run write-up begins — @L648–678

Text @L648: "Now the memories, decision entry, and budget."

Command @L649: `ralph tools memory delete mem-1790061552-775e` — deletes another memory (the one C2 originally targeted was `53ee`; this is a second, separate deletion tied to the round's own result, per decisions.md's DEC-028 "Alternatives" language about outcome 4/register).

Commands @L653, @L657: `ralph tools memory add` (two new memories: one about "Where 'Say what ends it' reaches", one about a round-15 claim's status) — via the CLI tool, not `echo`/`cat`.

Command @L664: rewrites `.ralph/agent/decisions.md` — collapses "DEC-001–026, rounds 1–17" to "DEC-001–027, rounds 1–18" (one line, folding the previous DEC-027 entry into the "Closed" summary) and appends a new, fully detailed "DEC-028 — keep `Say what ends it`; its predicted harm was looked for and is not there" entry (Chosen/Alternatives/Reasoning/Re-evaluate/Framing bias/Independent evaluation/Reversibility). Result (@L666): rewrite succeeds ("ok"); no immediate token count taken.

Command @L668: appends to `.ralph/agent/scratchpad.md` a "### The round's work and result" section (test-arm outcome narrative) and an "`(instruction)` for iteration 20" list — including, as item 3: *"`.ralph/agent/*` was over the user's 6000-token ceiling for two rounds. The command is now in the contract. Run it before committing."*

Immediately after (same command block): `cat .ralph/agent/* > /tmp/ra.txt && agent-tools count-tokens --file /tmp/ra.txt` → **6756**. This is the first count in the session using the bare `.ralph/agent/*` glob (matching the rule's literal wording) rather than `*.md`/`*.jsonl` name-lists, and it now includes both `.lock` files (0 tokens each) alongside all five content files.

### Over-budget by ~800 tokens — trimming pass 1: per-file breakdown and tasks.jsonl pruning — @L675–688

Thinking @L675: "I'm over budget by about 800 tokens and looking for what to trim — pruning closed entries from tasks.jsonl seems safe since it's not 'creating' tasks, but I want to check if there's a proper tool command for pruning rather than editing the file directly. I should also check memories.md, since additions and deletions there may roughly balance out, and consider trimming the lengthy DEC-028 entry in decisions.md. The scratchpad's critique section is long but required this round, so I'll leave it and measure each file's actual size before deciding what to cut."

Command @L676: `for f in .ralph/agent/*; do echo -n "$f: "; agent-tools count-tokens --file "$f"; done; ralph tools task --help ...`

Result (@L678):
```
.ralph/agent/decisions.md: 863
.ralph/agent/memories.md: 2156
.ralph/agent/memories.md.lock: 0
.ralph/agent/scratchpad.md: 3208
.ralph/agent/summary.md: 24
.ralph/agent/tasks.jsonl: 505
.ralph/agent/tasks.jsonl.lock: 0
```

Thinking @L680: "There's no delete option for tasks, and 505 tokens of closed tasks is wasteful against a 6000 budget, so I should close my task first then prune the file down to only what matters using a safe filtering approach that preserves the format rather than echo/cat. Actually, a better target is the scratchpad itself since it's the biggest file at 3208 tokens and I control it directly..."

Command @L681 closes the ralph task (`ralph tools task close task-1790067717-106e`), then runs a Python script directly filtering `.ralph/agent/tasks.jsonl` to keep only its last row (asserting all remaining rows are `closed`/`failed` first) — `tasks.jsonl` (harness-managed, no CLI delete) is pruned by hand-written Python, not through `ralph tools task`. Result (@L683): "kept 1 of 3"; `agent-tools count-tokens --file .ralph/agent/tasks.jsonl` → **185** (down from 505).

Commands @L686–688: verify the pruned `tasks.jsonl` still parses and that `ralph tools task show <id>` still reads the closed task correctly (confirms the CLI is not broken by the direct-file edit); notes as a "tool issue" that `ralph tools task list` reports "No tasks found" when only closed tasks exist (a UI quirk, not a data-loss confirmation — `task show` and `task list --status closed` both still find it).

### Trimming pass 2: scratchpad "Durable method" and critique compression — @L690–696

Thinking @L690: proceeds to cut the scratchpad's "Durable method" section and critique text.

Command @L691: a multi-part Python replace on `.ralph/agent/scratchpad.md`, cutting/shortening five separate passages:
1. Removes entirely: `"**A pre-registered outcome names the channel it is read from**, and a pre-registered *reading* can be wrong. Withdrawing beats honouring."`
2. Shortens the "Categorical or it is not evidence" durable-method bullet (drops the "issued an imperative or not" example, compresses "Hardest where..." to "Hardest to hold where...").
3. Shortens "When an instruction exists to compensate for a harness, fix the harness" — drops the trailing clause "— the ratchet, reproduced inside the tool meant to police it."
4. Shortens the just-written C1 (the one quoted in full above) — drops the sentence about "relocation is growth, cut before add" being "the round-13 method note, applied to everything except the file it was written in", replacing with a terser restatement of the same three numbers (5926/6118/6122) and the contract-line fix.
5. Shortens C2 and C3 similarly (minor wording compression, same content).

Result: `cat .ralph/agent/*.md .ralph/agent/*.jsonl > /tmp/ra.txt && agent-tools count-tokens --file /tmp/ra.txt` → **6248** (@L696).

### Trimming pass 3: contract paragraph + History section merge — @L698–701

Thinking @L698: "Still 248 words over, so I need to trim further—merging the history sections for rounds 1-16 with iterations 17-18, and cutting the contract's probe-deletion paragraph since that reasoning now lives in the skill itself."

Command @L699: cuts the standing-contract "A probe's own directory is deleted by the round that wrote it" paragraph down to two sentences (dropping the detailed account of the two records that forced the rule, replacing with "Reasoning and the two records that forced it: the prompt-tests skill."); shortens the "The compression rule" bullet; merges the scratchpad's separate "## History — rounds 1–16" and "## Iterations 17–18" sections into one "## History — rounds 1–18" section.

Result: **6040** (@L701).

### Trimming pass 4: decisions.md DEC-028 compression — @L706–708

Command @L706: shortens DEC-028's "Alternatives" and "Reasoning" bullets in `.ralph/agent/decisions.md` (drops some parenthetical detail, e.g. "asked about register with no idea what was under test" → dropped; "the one thing here that a round could both falsify and remove" restated more tersely).

Result: **5988** (@L708) — first time in the session's own tally the total drops under 6000.

### Cross-check: two counting methods agree — @L710–713

Thinking @L710: "5988 is under the 6000 limit, tight but workable. I should double check the contract command that globs the agent directory contents actually works correctly, since it needs to handle lock files without breaking on subdirectories."

Command @L711: `cat .ralph/agent/* 2>/dev/null | agent-tools count-tokens --file /dev/stdin` → **5988** — confirms the bare `.ralph/agent/*` glob piped through `/dev/stdin` gives the same total as the explicit `*.md .*jsonl` file-list method used in the prior trimming passes.

### First commit — @L715–717

Command @L715 updates the scratchpad heading: `"## Iteration 19 — `5c185783` → (see final commit)"` → `"## Iteration 19 — `5c185783` → `HEAD` (this commit); `.ralph/agent/*` 5988 tokens"` — i.e. the scratchpad's own section heading now states the measured total (5988) as text inside the very file being measured.

Commits (`git commit -q -m "iter19: scratchpad, decisions, memories, and the .ralph budget back under its ceiling\n\n...6122 -> 5988, and the command that checks it is now a contract line...\n\nClaude-Session: 9bb51163-bc6a-40ff-babb-f68670a9edfc"`). Commit hash: **`90b87539`**.

### Second commit and the self-reference surfaces — @L719–729

Thinking @L719: checks prompt-file diff, full round diffstat, and a separate 50,000-token added-lines re-check (18006, unrelated to the 6000 ceiling).

Command @L727 updates the scratchpad heading again — because the just-created commit hash (`90b87539`) needed to be recorded as the round's actual ending commit, per the loop's convention (seen identically in iteration 18 at @L474) of a follow-up "commit range" commit:
`"## Iteration 19 — `5c185783` → `HEAD` (this commit); `.ralph/agent/*` 5988 tokens"` → `"## Iteration 19 — `5c185783` → `90b87539` + this commit; `.ralph/agent/*` 5988 tokens"`.

Commits as `git commit -q -m "iter19: commit range 5c185783 -> end of round\n\nClaude-Session: ..."`. Commit hash: **`7f54493f`**.

Same command's tail re-measures: `cat .ralph/agent/* 2>/dev/null | agent-tools count-tokens --file /dev/stdin` → **6010** — over the ceiling again, because inserting the commit hash and "+ this commit" text into the heading (an edit made in order to keep the heading's stated commit range accurate) added enough characters to the file being measured to push the file's own token count above 6000; the "5988 tokens" figure now written inside the file is also stale (the actual count is 6010, not 5988).

### The fix: moving the number out of the counted files — @L731–732

Thinking @L731: "I'm back over the token budget by 10 after that last commit, so I need to trim the heading. The stale '5988 tokens' figure needs updating to reflect the actual current count since the contract requires an accurate number there. Actually, stating the token count in the scratchpad itself creates a self-reference problem — writing the number changes the count. Better to put the number in the commit message instead, per the contract wording about ending under the ceiling and reporting it, and just shorten the heading in the scratchpad."

Command @L732 makes two replacements:
1. Heading: `"## Iteration 19 — `5c185783` → `90b87539` + this commit; `.ralph/agent/*` 5988 tokens"` → `"## Iteration 19 — `5c185783` → `7f54493f` + this commit"` (drops the token-count clause from the heading entirely).
2. The standing-contract line itself (the one C1 had proposed adding) is rewritten:
   - Before: `"> **The round ends under the user's `.ralph/agent/*` ceiling and says the number.** `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` — under 6000. It sat over for two rounds because no line named a command. *(19)*"`
   - After: `"> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in its last commit message** — not in a file here, where writing it changes it. `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000. It sat over for two rounds because no line named a command. *(19)*"`

Result: `cat .ralph/agent/* 2>/dev/null | agent-tools count-tokens --file /dev/stdin` → **6015** (@L734) — the replacement contract-line wording is itself slightly longer than the original ("with the number in its last commit message — not in a file here, where writing it changes it" adds more characters than "and says the number"), so this specific fix-for-self-reference edit did not by itself bring the total down; it stayed over budget.

### Trimming pass 5 (post-self-reference-fix) — @L736–745

Command @L736: shortens four unrelated "Durable method" bullets (retirement-condition wording, "clause no fixture can exercise", "test the lines already shipped", "a criterion written from the shape of the failure") — none are budget-rule text; general scratchpad compression. Result: **6002** (@L738).

Command @L743: shortens the "Buy resolution inside the run" durable-method bullet. Result: **6003** (@L745) — thinking @L747 notes "That actually lengthened it," i.e. this particular edit's replacement text was one token longer than the original despite being intended as a cut.

### Trimming pass 6: opening paragraph — @L748–754

Command @L752 rewrites the scratchpad's opening "## Where the objective bites" section (drops the heading, folds the paragraph text into a shorter unheaded paragraph: "The objective's sharpest clause is... the rest follows from that ratchet. Carry **what retires this line** into every decision."). Result: **5995** (@L754).

### Final commit — @L756–757

```
git add -A && git commit -q -m "iter19: commit range, and the budget line stops being self-referential

Stating the token count inside .ralph/agent/ changes the count it states; the
number goes in the round's last commit message instead. cat .ralph/agent/* |
agent-tools count-tokens --file /dev/stdin = 5995, under the user's 6000.

Claude-Session: 9bb51163-bc6a-40ff-babb-f68670a9edfc"
```
Post-commit re-check: `cat .ralph/agent/* 2>/dev/null | agent-tools count-tokens --file /dev/stdin` → **5995** (unchanged by the commit itself, confirming committing does not alter working-tree file bytes).

### Final self-report (stop-hook text, @L780)

"## Evidence" code block includes: `$ cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` → `5995            # was 6122, user ceiling 6000`.

"## Summary": "...three ratchets closed (probe records delete themselves, a staged diff's header was leaking the case name, the `.ralph` budget is back under its ceiling with a command that checks it)."

"## Required notes":
- "instruction issue: the ralph tools skill says 'NEVER use echo/cat to write tasks', and `ralph tools task` has no delete — so 505 tokens of closed tasks could not be pruned through the CLI against the user's hard 6000-token ceiling. Pruned with a format-preserving Python filter and verified the tool still reads the file."
- "tool issue: `ralph tools task list` with no flag reports 'No tasks found' when only closed tasks exist, which reads as a corrupted file."
- "context waste: the injected task prompt carries three overlapping ralph-tools skill dumps (~2000 tokens), largely duplicate." (Restates, in shortened form, iteration 18's identical final-report note about the task-file's duplicated ralph-skill blocks — iteration 18 said "~2,400 words... four embedded... blocks"; iteration 19 says "~2000 tokens... three overlapping... dumps". Neither session acts on this observation by editing the task-generation source; both only note it.)
- "unexpected change: I deleted two round-15 memories, one of which this round's run contradicts on register — that is a reversal of a prior iteration's finding, not just a trim."

---

## Cross-session comparison: measurement scope

| | Iteration 18 | Iteration 19 |
|---|---|---|
| Glob(s) used | `.ralph/agent/*.md` (once); explicit `.md` filenames (all other calls) | `.ralph/agent/*.md .ralph/agent/*.jsonl` (first call); bare `.ralph/agent/*` (later calls, via `cat .ralph/agent/*` piped to `count-tokens --file /dev/stdin`, and via `for f in .ralph/agent/*`) |
| `tasks.jsonl` counted? | No | Yes (358 tokens at session start; pruned to 185 by hand-edited Python, since `ralph tools task` has no delete) |
| `.lock` files counted? | No (glob excludes them by never being named) | Yes, by the bare-`*` glob, but both measure 0 tokens |
| Final self-reported total | 5754 | 5995 (after fixing a 6010 breach caused by the commit-range heading edit) |
| Same repo state (`decisions.md`, `memories.md`), iteration-19's own re-measurement of iteration-18's end state | — | 6122 (bare-glob-with-tasks.jsonl method), vs. iteration 18's self-reported 5754 — a 368-token gap attributed by iteration 19 to the uncounted `tasks.jsonl` plus a small scratchpad-heading delta |
| Rule's literal wording (`.ralph/agent/*`) matched by the command used | No (narrower than the rule) | Yes, by the later commands in the session; the session's own C1 critique explicitly names this gap: "nothing in the loop ever ran the command that checks it" |

## Content moved to another destination, and stated reason

- Iteration 18: two memories deleted (`mem-1790061545-2f77`, `mem-1790058735-2e30`) because "that rule is now already captured in the shipped skill, making it redundant" / "superseded by the new naming rule that lives durably in the skill" (thinking @L430) — i.e. content moved from `.ralph/agent/memories.md` to `.claude/skills/prompt-tests/SKILL.md` (the skill edit itself occurs earlier in the session, at @L322/@L353, before the memory deletions).
- Iteration 18: `decisions.md`'s DEC-001–024 itemized entries collapsed into one summary sentence, on the stated ground (thinking @L442) that "those old decision summaries... are already captured in git and CLAUDE.md, so per the rule that outdated info belongs in git history only, I can cut them to a few lines."
- Iteration 19: memory `mem-1790062999-53ee` deleted because its content ("the genre supplies the frame...") had already been withdrawn from `sys_prompt/CLAUDE.md` by iteration 18 but "survived verbatim" in the memory file (C2, @L178). Two more memories (`mem-1790061552-775e` and one other, round-15-era) deleted during the post-run write-up (@L649), one of them because "this round's run contradicts on register" (@L780, "unexpected change").
- Iteration 19: the token-count number itself is relocated out of `.ralph/agent/scratchpad.md` and into the git commit message ("with the number in its last commit message — not in a file here, where writing it changes it", @L732) — the one instance in either session of content being moved specifically because of self-reference with the ceiling's own counted-file set, rather than for ordinary space-saving.
- Iteration 19: `tasks.jsonl` pruned from 3 rows to 1 by direct Python file edit (not via `ralph tools task`, which "has no delete") — content (2 closed-task records) is deleted outright, not relocated.

## Cost/gain of the iteration-19 self-reference fix specifically

- The heading edit that stated "5988 tokens" (@L715, commit `90b87539`) was itself invalidated by the very next edit in the same round (@L727, commit `7f54493f`, which updated the commit-hash portion of the same heading), pushing the true count from 5988 to 6010 — i.e., the stated number became wrong one commit after it was written.
- The fix (moving the number to the commit message, and rewriting the standing-contract line to say so) did not itself reduce the token count — the rewritten contract-line wording is longer than the original ("with the number in its last commit message — not in a file here, where writing it changes it" vs. "and says the number"), and the total rose to 6015 immediately after this specific edit (@L734), requiring three further, unrelated compression passes (@L736, @L743, @L752) to bring the total to 5995 before the final commit.
- Net effect: the ceiling-reporting mechanism changed from "state the number in the scratchpad heading" (self-referential, went stale within one commit) to "state the number in the commit message body" (commit messages are immutable once made, so a later edit to tracked files cannot invalidate a number already written to a past commit message) — bought at the cost of the rewritten contract-sentence's extra length, absorbed by cutting other scratchpad text.

## Manifest / coverage note

Both sessions' thinking and text blocks were read in full via targeted `sed`/`jq` extraction at every ref identified from the `--skeleton --show-all` render (session A: 508 lines; session B: 782 lines, rendered via `--agent` chunking into two files covering @L1–@L781). A `grep -i "6000|budget|ceiling|relocation is growth|cut before add|self-referen|count-tokens"` sweep over every thinking/text block in both sessions' full JSONL was run to confirm no additional budget-related reasoning block was missed beyond what is quoted/summarized above. Tool inputs/outputs not concerning `.ralph/agent/*` (the two blind-reader `Agent` dispatches, the prompt-test arm launches and their transcripts, the `sys_prompt/CLAUDE.md` and `prompt-tests/` skill edits themselves) are described only where they intersect the budget narrative (e.g., memory deletions tied to a skill edit) and are otherwise out of scope for this focus.
