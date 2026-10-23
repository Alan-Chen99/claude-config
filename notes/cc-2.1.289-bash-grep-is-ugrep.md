# Claude Code's Bash `grep` and `find` are its bundled ugrep and bfs (2.1.289)

Measured 2026-10-23 on the native 2.1.289 build. Agents keep reporting "grep here is ugrep" as a
tool issue; this is what it is, what it breaks, and what answers it.

## Mechanism

The shell snapshot appends two functions after the user's profile and functions (snapshot comment
`Shadow find/grep with embedded bfs/ugrep (ant-native only)`), so a user-defined `grep` loses.
They re-exec the `claude` binary under another `argv0`:

- `grep` → `ugrep -G --ignore-files --hidden -I --exclude-dir=.git` (and `.svn .hg .bzr .jj .sl`).
  An argument matching a ugrep-only option shape (`-*-config*`, `-[Zz]*`, `--null`, …) falls
  back to `command grep`.
- `find` → `bfs -S dfs -regextype findutils-default`.

The gate is on unless `CLAUDE_CODE_ENTRYPOINT=local-agent` or the host's search-tools opt-in is
set, and the opt-in is computed from the CLI: `Grep` or `Glob` named in `--tools` or
`--allowedTools` (`replaceSearchToolsOptIn`); no settings key reaches it. `claude -p
--allowedTools Grep` measured: `type -t grep` prints `file`, Grep and Glob are in the roster;
without the flag, `function`. While on, the
Grep and Glob tools leave the roster and cc's prompt says "`find` or `grep` via the Bash tool".
The same snapshot aliases `rg` to cc's bundled ripgrep when no `rg` is on `PATH`, so `rg` exists
in every cc Bash shell.

Only a direct shell call reaches the functions: `timeout grep`, `xargs grep`, `find -exec grep`
and any script run as a subprocess get `/usr/bin/grep`.

## What breaks

Fixture: a 200-line UTF-8 file, a gitignored file, a hidden file, a file with `\xff\xfe` and no
NUL byte.

| Case | `grep` (ugrep) | `command grep` (GNU 3.11) | `rg` 15.1.0 |
|---|---|---|---|
| `-oE '.{0,N}X.{0,N}'`, N ≥ 45 | exit 2, `exceeds complexity limits` on stderr, stdout empty; `LC_ALL=C` no help; N = 40 works | works; N = 3000 ran over a minute at 800 MB and was killed | works; N = 1200 in 0.06 s |
| one-sided `.{0,300}X` | works | works | works |
| file with invalid UTF-8, or a NUL | exit 1, no output (`-I` treats it as binary) | `binary file matches` | invalid UTF-8: prints the line; NUL under `-r`: skipped, `-uuu` finds it |
| gitignored file under `-r` | skipped silently | found | skipped; `-uu` finds it |
| hidden file | found | found | skipped; `--hidden` finds it |
| BRE alternation `'a\|b'` | works | works | exit 1, no match: rg is ERE-style, `'a\|b'` there is a literal `\|` |
| BRE `\(\)` | exit 2, `empty (sub)expression` | matches | — |
| `find -newermt '-10 minutes'` | bfs: `Invalid timestamp` | GNU find accepts it | — |

The failing cases are loud only on stderr: behind `2>/dev/null` or a `| head` they read as
"no match", and the invalid-UTF-8 and gitignore skips are silent at any verbosity.

## Incidence

A scan of `~/.claude/projects/**/*.jsonl` for assistant-written `ugrep`: 272 blocks (111 text,
111 thinking, 50 tool inputs) in 87 sessions, 2026-05-20 to 2026-10-23, 177 of them in October.
In 63 of the 83 sessions with such text or thinking, the 440 characters around the mention name
the complexity limit or a `{0,N}` pattern; the usual workaround is Python. Silent ones: `repos-dotfiles`
`e8f08840` @L172 (`2>/dev/null` hid the error), `workspace` `4f7af5a9` @L371 (a bad-UTF-8 file
returned nothing). Some reports blame ugrep for shell behaviour GNU grep shares: a path beginning
`-root-…` parsed as an option, an unmatched glob passed literally.

`bfs`: 5 sessions' assistant text names it with the relative `-newermt` case.

## Answer

The always-loaded user memory, `/workspace/docker/claude-home-CLAUDE.<profile>.md` (both host
copies, `/workspace` commit `d7eef6eb`), reads: "Search file contents with `rg`. Claude Code's
Bash `grep` is its bundled ugrep, which rejects patterns like `.{0,50}x.{0,50}` and silently skips
some files; `command grep` is GNU grep." It reaches main sessions and every subagent type that
loads CLAUDE.md; Explore does not (2 of the 87 sessions). cc's own prompt still says "search with
grep and find"; the reason in the line outweighs it. Six `claude -p` runs (Opus 5.5), three asking
for 150-character context around a term in a UTF-8 file and three for the count of lines naming
either of two words, searched with `rg` (five) or `command grep` (one); all three counts were
right. A longer wording (`1c8f453f`) also gave rg's ERE syntax and skip flags and named bfs, and
scored the same: of 251 logged `rg` calls none used BRE `\|` alternation, and 27 already passed
`-uu`/`--hidden` unprompted.

The mechanical route is `--allowedTools Grep` on the launcher: GNU `grep`/`find` back in Bash and
the ripgrep-backed Grep and Glob tools back in the roster, at those two tool definitions' cost on
every request (about 1.6 KB of prompt source plus schemas in the 2.1.88 source), and only for
sessions started with the flag.

Retire the memory line when `type grep` in a cc Bash shell prints no function.
