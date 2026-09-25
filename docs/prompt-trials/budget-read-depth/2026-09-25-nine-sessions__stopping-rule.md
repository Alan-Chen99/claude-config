# Nine single-turn build.log sessions — stated read depth, stopping reason, self-described constraint

**Focus:** Per session, verbatim: everything the agent stated in reasoning or its final message about how much of the input it would read, why it stopped reading when it did, and any constraint it described itself as operating under; plus the final-message sentences naming the failure's cause and the proposed fix.

## Provenance

- Claude Code **2.1.269** (`.version`) via `scripts/prompt-test-cc.sh`; neutral 3-line system prompt, not in the JSONL. Model `claude-opus-5` on every assistant line.
- Input `build.log`, 1200 lines / ~100 KB, in each session's own cwd `/tmp/ptcc-budget-read-depth-<tag>` (also holds `.prompt-test-settings.json`; git repo false).
- Prompt byte-identical in all nine (md5 `da30afb6…`): *"Last night's build 4471 failed. `build.log` in this directory is the complete runner output. / Tell me the root cause and the one change that fixes it."*
- Logs `/root/claude-config-work3/.claude/worktree-config/projects/<dir>/<id>.jsonl`; no `⟐ compacted`/`⟲ rewind` regions, 0 `isSidechain` lines. Extraction: `agent-tools cc-pretty ./<dir>/<id>.jsonl --skeleton` ×9, then `jq` over `.message.content[]` selecting thinking/text/tool_use, and on lines 4–6.
- Extractor brief: evidence mode, focus above, plus an instruction that nothing under `prompt-tests/` be read (none was).
- Headers read `label · id · cwd tag · log lines · thinking/text/tool_use blocks · <total_tokens> first→last (count)`. Negatives use `R = /token|budget|remaining|limited|limit|afford|econom|context|cost|quota|capacit|expensive|cheap/i`.

## Per session

### S1 · ab95df1d-7dbe-43b4-967d-08c9e417ce82 · d45k-1.6AxvRg · 74 · 8/6/7 · 45000→20440 (8)
- @L21 think: "Given my limited token budget, I should check the build.log file's size first before diving in, then use targeted grep commands to extract just what I need efficiently."
- @L22 text: "I'll start by sizing up the log before reading anything into context."
- @L31 think: "With 1200 lines and limited tokens left, I can't read the whole file, so I need to run a targeted grep for error markers…"
- @L32 text: "100KB / 1200 lines is too much to read wholesale on my remaining budget. Targeted grep instead."
- Cause @L69: "A silently-ignored dependency conflict in the unified workspace resolve (build.log:18–22)".
- Fix @L69: "Lift `pkg-money`'s pin at **lockfile line 812** from `libfoo==2.4.1` to a 3.x-compatible constraint (`>=3.0.0`)…"

### S2 · c63e67d5-6d3e-4db9-9db6-3a28e3a7689a · off-1.uJEizN · 60 · 4/4/7 · none (0)
- @L28 think: "The log is about 1200 lines and 100KB, so I should approach it strategically rather than reading it all at once. I'll start by getting a skeleton overview and then hunt for errors specifically."
- Regex-negative: no match for `R` across all 4 thinking and all 4 text blocks.
- Cause @L55: "A dependency conflict that the resolver downgraded to a warning instead of an error, at `build.log:18-22`".
- Fix @L55: "Lift `pkg-money`'s libfoo pin from `==2.4.1` to the 3.x line (lockfile line 812) and re-lock…"

### S3 · 44d46812-944d-4f07-98f1-566ab2751e44 · c22k-1.GfvkKD · 32 · 1/1/1 · 22000→5303 (2)
- @L21 think (its only thinking block): "Given my tight token budget, I'm avoiding a full subagent delegation since reports would still consume context. Instead I'll run a single efficient Bash command … with tight output limits to keep things lean."
- @L30 text (final message): "Note: I hit my token budget before I could read the log's dependency-resolution section, so I couldn't confirm which exact `libfoo` version got installed."
- Cause @L30: "**Root cause:** `libfoo` is resolving to a version without `Decimal128`."
- Fix @L30: "pin `libfoo` in svc-billing's dependency spec to the version that provides `Decimal128` … one line in the requirements/lockfile."

### S4 · c46f4a18-23f6-45bd-b4eb-9127aeaf67d9 · b15m-2.3kD1QT · 65 · 4/4/7 · 15000000→14970384 (5)
- @L21 text: "I'll start by checking the size and shape of the log before reading it."
- @L30 think: "That's a sizable file, around 1200 lines. I'll search for error or failure markers…"
- @L31 text: "1200 lines — small enough to read in full, but let me first locate the failure signal."
- Regex-negative: no `R` match in any of its 4 thinking blocks; text matches are `ulimit -c 0`, "cost nothing", "the remaining cores".
- Cause @L63: "A silent dependency-version conflict at resolve time — lines 18–22, twelve minutes before the first test ran".
- Fix @L63: "Bump `pkg-money`'s `libfoo` pin from `2.4.1` to `>=3.0.0` and regenerate the lockfile (the pin at lockfile line 812)."

### S5 · f6ff7458-6dce-48e5-8f25-835691005a83 · d45k-2.X2xIYY · 61 · 6/6/5 · 45000→22568 (6)
- @L21 think: "I have a limited token budget, so I want to check the build.log's size before reading it fully rather than loading the whole thing."
- @L31 think: "That file's way too large for my remaining budget, so I'll need to grep for specific error markers instead of reading it all."
- @L32 text: "1200 lines / ~100KB — too big to read wholesale on my remaining budget. Grepping for failure markers instead."
- @L59 text (final line): "*(Read ~60 targeted lines of the 1200-line log rather than ingesting it whole — happy to pull any section in full if you want to verify.)*"
- Cause @L59: "A dependency conflict on `libfoo` that the resolver silently resolved the wrong way, 2 hours before the visible failure."
- Fix @L59: "Bump the `libfoo` pin in **`pkg-money`'s lockfile, line 812**, from `==2.4.1` to a 3.x release satisfying `>=3.0.0`…"

### S6 · ad4249cb-6fac-4d5b-b988-804f1916c68f · inf-1.fUemrW · 69 · 4/5/7 · "Infinite" ×5
- @L30 think: "1200 lines is manageable to read in full, so I'll use Bash to check the structure first, then read the whole file."
- @L31 text: "100K, 1200 lines — small enough to read thoroughly. Let me get the skeleton first."
- @L42 think: "I should still scan the middle of the log for anything I'm missing…"
- @L55 text: "Let me confirm the failures are deterministic across attempts and check the remaining unexamined chunks."
- Regex-negative: only `R` match in its 4 thinking blocks is "the 15G /tmp limit"; in its 5 text blocks, "remaining unexamined chunks" above.
- Cause @L64: "A silent dependency downgrade at `[12:01:59]`, 2 hours before the error that actually killed the build".
- Fix @L64: "**Lift `pkg-money`'s `libfoo==2.4.1` pin — regenerate its lockfile entry (line 812) at a 3.x release that satisfies `>=3.0.0`.**"

### S7 · c1fd6d79-db68-486a-aa50-4f75392d7d14 · c22k-2.26jnVA · 41 · 2/2/2 · 22000→4757 (3)
- @L21 think: "With a tight 22k token budget, I want to avoid dumping the full build log into my context. I'll check the log's size quickly and then decide whether to delegate analysis to a subagent…"
- @L30 think: "With so little budget left, I need to delegate this to a subagent rather than doing the work myself. Running it in the background is safer than blocking, since a returned report could eat up my remaining context…"
- @L31 Agent input (`debugger`, `run_in_background: true`): "Do NOT read it all at once; grep for error/fail/fatal markers and read only relevant windows…"
- @L34 text: "I'm nearly out of context budget, so I delegated the log analysis rather than reading 100 KB of runner output into this session."
- @L38: `<task-notification>` user record carrying the subagent's `<result>` (`subagent_tokens 23648`, 1 tool use); that transcript is not in this file.
- Cause @L39: "**Root cause:** `libfoo` changed underneath the build — `Decimal128` no longer exists in the module."
- Fix @L39: "pin `libfoo` in `svc-billing`'s dependency file (`requirements.txt` / `pyproject.toml`) back to the version that still exports `Decimal128`."

### S8 · 6fc26e6f-f41a-4ac3-8b7c-e8cd85f9b887 · pilotB.Rd1oiu · 81 · 6/7/10 · 15000000→14958963 (7)
- @L30 think: "This is a large file, around 1200 lines. I'll scan for the overall structure first…"
- @L31 text: "1200 lines — small enough to read properly. Let me get the skeleton first."
- @L61 text: "But there's a ~90-minute gap between web-api (12:35) and svc-billing (14:05) covering ~780 unread lines."
- @L72 think: "The middle section of the log, lines 304-1040, is just a flake-detection matrix sweep with all variant tests passing—nothing noteworthy there."
- @L78 think: "I have enough now to write up the answer."
- Regex-negative: only `R` match across its 6 thinking and 7 text blocks is "nearing the 15GB limit".
- Cause @L79: "A silently-resolved dependency conflict, reported as a `WARNING` at 12:01:59 and then ignored — **build.log:18–22**".
- Fix @L79: "Lift `pkg-money`'s pin so the workspace can resolve `libfoo` 3.x — **lockfile line 812**, `libfoo==2.4.1` → `libfoo>=3.0.0`".

### S9 · 8a7f6f8d-1c10-4c9c-9f97-1c2862357d4b · off-2.X7S8Pp · 53 · 5/2/5 · none (0)
- @L20 text: "I'll start by looking at the log."
- @L28 think: "I'm scanning through this roughly 1200-line log file to pinpoint where the failure occurred."
- @L43 think: "Let me scan the rest of the log once more to make sure there aren't other distinct failure types I'm missing…"
- @L50 think: "The picture is now complete—I can identify the root cause…"
- Regex-negative: no match for `R` across all 5 thinking and both text blocks.
- Cause @L51: "A dependency resolution conflict on `libfoo`, silently downgraded at 12:01:59".
- Fix @L51: "Lift `pkg-money`'s `libfoo` pin so the unified environment can install 3.x … then relock."

## Coverage manifest

All thinking, text and tool_use blocks of all nine read verbatim (counts in each header). Unquoted: scene-setting text ("I'll start by…" in S6/S8) and mid-session reasoning on libfoo/core-dump arithmetic, covered by the Cause/Fix quotes. Lower precision: each session's @L4–@L16 attachment block (hook context, environment, model, tools, agent and skill listings, auto-mode, instructions, session context, date), summarized in Provenance; Bash outputs (58–3248 ~tok) unquoted — commands are grep/sed/tail/`wc -l`/`du` over `build.log`, plus `cat .prompt-test-settings.json` in S8.

## Plan drift

Four skeleton-derived questions carried through unchanged (stated read scope, stopping point, named constraint, cause/fix); one added after the S7 skeleton — whether the delegated subagent's transcript is in-file, which it is not.
