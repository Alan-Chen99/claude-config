# Nine sessions, one 1200-line `build.log`: read bounds and line coverage

**FOCUS:** For each session, every tool call that ingested any part of `build.log` — the
command verbatim, the line/byte bound it chose (`head -N`, `tail -N`, `sed -n 'A,Bp'`, Read
`limit`, unbounded `cat`/`grep` with no `head`), the order of those calls, and which line
ranges of the file the session therefore saw.

## Provenance

- Harness: Claude Code 2.1.269 (`.version`, every record), via `scripts/prompt-test-cc.sh`. Model `claude-opus-5`; S7's subagent `claude-sonnet-5`. Agent prompt: neutral 3-line system prompt, caller-supplied, absent from the JSONL; no other output-affecting setting appears in-log.
- Input: `build.log`, 1200 lines / 99697 bytes, md5 `526bbcdc0900b2de2c2b2fea69da0e8a`, identical in all nine cwds.
- User prompt, identical in all nine: "Last night's build 4471 failed. `build.log` in this directory is the complete runner output. Tell me the root cause and the one change that fixes it."
- Fixture: cwd = each session's own `/tmp/ptcc-budget-read-depth-<slug>`, holding `build.log` and `.prompt-test-settings.json`; no git repo; `grep -c '"isCompactSummary"'` = 0 in all nine logs.
- Logs: `/root/claude-config-work3/.claude/worktree-config/projects/-tmp-ptcc-budget-read-depth-<slug>/<id>.jsonl`. Extraction: `agent-tools cc-pretty <path> --skeleton`; `jq` over `.message.content[]` per `thinking`/`text`/`tool_use`; `sed -n '<n>p' … | jq` per named result; unnumbered pipelines replayed on the live `build.log` under `awk '{print NR"\t"$0}'`.
- Extractor: evidence mode, focus supplied verbatim by the dispatching parent. S7 dispatches a background `Agent` at `@L31`; its log is inlined as S7sub.

```
S      id                 cwd-slug         turns calls tools        tokens-left-first→last
S1     ab95df1d           d45k-1.6AxvRg    8     7     Bash         45000→20440
S2     c63e67d5           off-1.uJEizN     5     7     Bash         (none)
S3     44d46812           c22k-1.GfvkKD    2     1     Bash         22000→5303
S4     c46f4a18           b15m-2.3kD1QT    5     7     Bash         15000000→14970384
S5     f6ff7458           d45k-2.X2xIYY    6     5     Bash         45000→22568
S6     ad4249cb           inf-1.fUemrW     5     7     Bash         Infinite
S7     c1fd6d79           c22k-2.26jnVA    4     2     Bash+Agent   22000→4757
S7sub  a0a84867ccd4b8547  (S7's cwd)       2     1     Bash         22000→3232
S8     6fc26e6f           pilotB.Rd1oiu    7     10    Bash         15000000→14958963
S9     8a7f6f8d           off-2.X7S8Pp     6     5     Bash         (none)
```

Turns = unique `.message.id`. No session used `Read`; none ran `cat build.log`.

## Conventions

One line per call in call order; `@L` = JSONL line; `B` = the literal `build.log`; `→` marks
the lines emitted. `[agg]` = call pipes all 1200 lines through `wc`/`grep -c`/`grep -oE`/`sort|uniq -c`,
emitting counts, sums or normalised shapes only. `…` elides `echo '=== label ==='` separators,
trailing `awk`/`tr`/`sed` formatters, and alternations past ~8 branches; `|` and `&&` appear unspaced; bounds are verbatim.
Recover full text: `sed -n '<n>p' <log> | jq -r '.message.content[].input.command'`. Call 1
everywhere is `ls -la` + `wc -l B` `[agg]` — S1 `@L23`, S2 `@L21`, S4 `@L22`, S5 `@L23` (`wc -lc`),
S6 `@L22`, S7 `@L22`, S8 `@L22`, S9 `@L21`; S3 folds it in; S4/S6/S8 add `du -h B`.

## Per session

S1 (7 Bash)
```
@L33 grep -n -iE "error|fail|fatal|cannot|denied|…|Exception" B|head -40|cut -c1-180
     →1042-1065,1075-1076,1099,1101-1113
@L39 grep -n -i "libfoo" B|grep -v "has no attribute"|cut -c1-200   [nohead;5hits] →18-22
@L45 … sed -n '1,30p' B|cut -c1-160&&… grep -n -i "pkg-money" B|grep -v "requires libfoo"|head -12|cut -c1-160
     →1-30 ; 10,49-53,309,321,333,345,357,369
@L53 … grep -nE "[0-9]+ (failed|passed)" B|cut -c1-140&&… tail -12 B|cut -c1-160
     →[nohead]105,127,149,171,193,215,237,259,281,303,1075,1098,1134,1177 ; 1189-1200
@L59 … grep -c "core: write" B&&grep -oE "at [0-9]+M" B|…&&… grep -nE "disk|space|df |ci-cores|retry:" B|grep -v "core: write"|head -10|cut -c1-170
     →[agg] ; 17,54-58,172,193,1076-1077
@L64 grep -c "^\[.*\] core:" B&&grep -oE "\(([0-9]+)M\)|at [0-9]+M" B|…   [agg]
∪=113/1200(9%): 1-30,49-58,105,127,149,171-172,193,215,237,259,281,303,309,321,333,345,357,369,1042-1065,1075-1077,1098-1099,1101-1113,1134,1177,1189-1200
```

S2 (7 Bash)
```
@L29 grep -n -iE "error|fail|fatal|exception|…|panic" B|head -80
     →1042-1065,1075-1076,1099,1101-1124,1134-1135,1142,1144-1167,1177-1178
@L32 sed -n '1,60p' B   →1-60
@L37 grep -n -E "WARNING|WARN|NOTICE|retry:|libfoo|Decimal128" B|grep -v "AttributeError"|head -60
     →[15hits] 18-22,54-58,172,193,1099,1142,1185
@L40 sed -n '1178,1200p' B   →1178-1200
@L48 grep -nE "passed|failed|collected|: ok|SKIP" B|grep -vE "AttributeError|FAILED \["|head -60
     →[30hits] 84,105-106,127-128,…,281-282,303,1041,1075,1083,1098-1100,1134,1142-1143,1177
@L51 sed -n '1020,1045p' B&&… grep -n -E "df:|core:|/tmp" B|head -20
     →1020-1045 ; 1076-1082,1135-1141,1178-1183
∪=220/1200(18%): 1-60,84,105-106,127-128,149-150,171-172,193-194,215-216,237-238,259-260,281-282,303,1020-1065,1075-1083,1098-1124,1134-1167,1177-1200
```

S3 (1 Bash)
```
@L22 wc -l B&&grep -n -i -E "error|fail|fatal|cannot|not found|exit code" B|head -40
     →1042-1065,1075-1076,1099,1101-1113
∪=40/1200(3%)
```
Final text `@L30`: "I hit my token budget before I could read the log's dependency-resolution section, so I couldn't confirm which exact `libfoo` version got installed."

S4 (7 Bash)
```
@L32 grep -n -iE "error|fail|fatal|exception|…|not found" B|head -80
     →91,113,135,…,1030 [every-20-22],1042-1065,1072,1075-1076,1090,1099,1101-1104
@L35 sed -n '1,60p' B   →1-60
@L44 grep -n "FAILED" B|sed 's/.*pytest //'|…|head -20 + grep -nE "Error|error:|Exception" B|…|head -20
     →[agg] [37-FAILED-lines;prefixes-stripped]
@L47 sed -n '1095,1200p' B   →1095-1200
@L55 grep -niE "commit|rev |bump|pyproject|lockfile|libfoo|…|ci-cores" B|grep -viE "AttributeError|…core: /tmp"|head -40
     →[30hits] 2,5-16,18-22,1076,1135,1178,1186-1194
@L58 … grep -nE "passed in|failed," B   [nohead] →105,127,…,303,1075,1098-1099,1134,1177
     + grep -oE "\(([0-9]+)M\)" B|…   [agg]
∪=251/1200(20%): 1-60,91,105,113,127,135,149,157,171,179,193,201,215,223,237,245,259,267,281,289,303,310,330,350,370,390,410,430,450,470,490,510,530,550,570,590,610,630,650,670,690,710,730,750,770,790,810,830,850,870,890,910,930,950,970,990,1010,1030,1042-1065,1072,1075-1076,1090,1095-1200
```

S5 (5 Bash)
```
@L33 grep -nE "ERROR|FATAL|error:|Error:|FAIL|failed|…|##\[error\]" B|head -40
     →1042-1065,1075,1099,1101-1114
@L39 grep -niE "libfoo" B|grep -viE "no attribute"|head -30   [5hits] →18-22
@L45 … grep -niE "pkg-money|lockfile|pin|Decimal128 (was|added)|2\.4\.1|3\.0\.0" B|grep -viE "no attribute"|head -20&&… grep -niE "passed in|failed,|BUILD|SUMMARY|result" B|tail -20
     →5-16,19-21,49-53,80-83 ; 105,127,…,303,1075,1098-1099,1134,1177,1200
@L54 sed -n '1,4p;22,30p' B&&… grep -niE "commit|git|branch|merge|changed|bump" B|head -8
     →1-4,22-30 ; 2
∪=92/1200(7%): 1-16,18-30,49-53,80-83,105,127,149,171,193,215,237,259,281,303,1042-1065,1075,1098-1099,1101-1114,1134,1177,1200
```
Final text closes: "*(Read ~60 targeted lines of the 1200-line log rather than ingesting it whole …)*"

S6 (7 Bash)
```
@L32 … sed -n '1,60p' B&&… tail -80 B   →1-60 ; 1121-1200
@L35 … grep -niE 'error|fail|fatal|exception|…|exit code' B|head -80   →same-80-refs-as-S4@L32
@L44 … sed -E 's/^\[[0-9:]+\] //; s/[0-9]+/N/g' B|sort|uniq -c|sort -rn|head -60
     →[agg];1200-lines-normalised-to-60-shapes
@L47 … grep -niE 'libfoo|decimal128|pkg-money|pin|lockfile|resolver|conflict' B&&… grep -niE 'df:|disk|space|/tmp|clean|…|core dump' B|grep -vE 'core: /tmp/ci-cores/pytest'|head -40
     →first-grep-unbounded;153-numbered-lines: 5-22,49-53,309-1029 every 12,1043-1065 odd,1076,1083-1098,1102-1124 odd,1135,1145-1167 odd,1178,1186-1195,1199
@L56 … grep -E 'FAILED' B|sed -E '…'|sort|uniq -c&&…|sort -u|wc -l   [agg]
@L59 … sed -n '1066,1100p' B&&… sed -n '1125,1144p' B   →1066-1100 ; 1125-1144
∪=320/1200(26%): 1-60,91,113,135,157,179,201,223,245,267,289,309-310,321,330,333,345,350,357,369-370,381,390,393,405,410,417,429-430,441,450,453,465,470,477,489-490,501,510,513,525,530,537,549-550,561,570,573,585,590,597,609-610,621,630,633,645,650,657,669-670,681,690,693,705,710,717,729-730,741,750,753,765,770,777,789-790,801,810,813,825,830,837,849-850,861,870,873,885,890,897,909-910,921,930,933,945,950,957,969-970,981,990,993,1005,1010,1017,1029-1030,1042-1104,1106,1108,1110,1112,1114,1116-1118,1120-1200
```

S7 (2 calls). `@L31` `Agent`, `subagent_type: "debugger"`, `description: "Find root cause in build.log"`, `run_in_background: true`; `prompt` verbatim:

> Analyze /tmp/ptcc-budget-read-depth-c22k-2.26jnVA/build.log (1200 lines, runner output for failed build 4471). Do NOT read it all at once; grep for error/fail/fatal markers and read only relevant windows. Determine the single root cause (distinguish it from downstream cascading errors) and the one concrete change that fixes it. Reply in under 120 words: root cause (with the log line number that proves it), then the exact fix (file + change if identifiable).

Tool result = **async-launch notice**, not a report: "Async agent launched successfully. …
You will be notified automatically when it completes." The report arrived at `@L38` as a
`<task-notification>` user record (`<status>completed</status>`, `<subagent_tokens>23648`,
`<tool_uses>1`) carrying the subagent's 2-sentence `<result>`. ∪=0/1200(0%) in the main session.

S7sub (1 Bash, `claude-sonnet-5`)
```
@L11 grep -niE 'error|fail|fatal' /tmp/…-c22k-2.26jnVA/build.log|head -80
     →1042-1065,1075-1076,1099,1101-1124,1134-1135,1142,1144-1167,1177-1178   ∪=80/1200(6%)
```

S8 (10 Bash)
```
@L32 cat .prompt-test-settings.json&&… sed -n '1,60p' B   →1-60
@L35 … grep -n -E '^(\[|#|=|-{3,}|##)|^\S+:$|…|^==>' B|head -80   →1-80
@L41 grep -n -iE 'error|fail|fatal|traceback|…|WARNING|warn' B|head -100
     →11,18-22,54-58,90-91,112-113,…,589-590 [100lines;all≤590]
@L44 … tail -80 B   →1121-1200
@L53 grep -c 'FAILED' B (37) + grep -oE '(AttributeError|…)[^[]*' B|… + grep 'FAILED' B|…   [agg]
@L56 … grep -E 'passed|failed' B|grep -E ': [0-9]+ (failed|passed)'   [no-n;nohead;14lines]
     →105,127,…,303,1075,1098,1134,1177
     + grep -nE 'df:|disk|truncat|ci-cores to|writing core' B|head -20   →1076,1135,1178,1186-1194
@L62 … sed -n '290,320p' B&&… sed -n '1040,1080p' B   →290-320 ; 1040-1080
@L65 … sed -n '290,1075p' B|grep -vE 'test_variant (PASSED|FAILED)'|head -60
     →sed-feeds-290-1075;head-60-emits-49-source-lines: 290-303,1041-1075
@L74 grep -oE '\(([0-9]+)M\)' B|… + grep -oE 'truncated at ([0-9]+)M' B|… + grep -oE 'pytest-[0-9]+-[0-9]+\.core' B|…   [agg]
∪=328/1200(27%): 1-80,90-91,105,112-113,127,134-135,149,156-157,171-193,200-201,215,222-223,237,244-245,259,266-267,281,288-320,322,329-330,334,346,349-350,358,369-370,382,389-390,394,406,409-410,418,429-430,442,449-450,454,466,469-470,478,489-490,502,509-510,514,526,529-530,538,549-550,562,569-570,574,586,589-590,1040-1080,1098,1121-1200
```
Text `@L61`, before `@L65`: "a ~90-minute gap between web-api (12:35) and svc-billing (14:05) covering ~780 unread lines."

S9 (5 Bash)
```
@L29 grep -n -iE "error|fail|fatal|cannot|unable|…|exit code" B|head -80   →same-80-refs-as-S4@L32
@L33 sed -n '1,90p' B    →1-90
@L40 sed -n '1066,1200p' B    →1066-1200
@L44 … grep -vE "PASSED|^\[[0-9:]+\] build |^\[[0-9:]+\] core: |AttributeError" B|grep -vE "resolve: (svc|pkg|adapters|cli|web)"&&… grep -E ": [0-9]+ (failed|passed)" B
     →both-unbounded;no-n;88-source-lines (1-4,17-23,84,105-106,…,1195-1200) + 14 (105-1177)
∪=316/1200(26%): 1-91,105-106,113,127-128,135,149-150,157,171-172,179,193-194,201,215-216,223,237-238,245,259-260,267,281-282,289,303,310,330,350,370,390,410,430,450,470,490,510,530,550,570,590,610,630,650,670,690,710,730,750,770,790,810,830,850,870,890,910,930,950,970,990,1010,1030,1041-1200
```

## Coverage manifest

Assistant blocks (thinking/text/tool_use), all read in full: S1 8/6/7, S2 4/4/7, S3 1/1/1,
S4 4/4/7, S5 6/6/5, S6 4/5/7, S7 2/2/2, S7sub 1/1/1, S8 6/7/10, S9 5/2/5. Every `build.log`
call's output was read for line numbers; the five over 2k~tok (S4 `@L49`, S6 `@L34`, `@L49`,
S8 `@L43`, S9 `@L42`) were skimmed structurally into line-number sets. Pre-turn attachments
`@L4`-`@L16` (hook supplement, environment, model, deferred tools, agent and skill listings,
auto-mode, instructions, session context, date, token reminder) are structurally identical
across sessions; reminder values are tabulated above. Final `text` blocks: S1/S2/S4/S5/S6/S8/S9
quote lines 18-22; S3 points at "~1000"; S7 `@L39` cites 1043; S7 `@L34` announces delegation.
