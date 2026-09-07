# `agent-tools count-tokens` — local tokenizer by default

Supersedes the backend choice in
[`2026-05-17-agent-tools-count-tokens-design.md`](./2026-05-17-agent-tools-count-tokens-design.md);
the input-resolution rules (positional > `--file` > stdin, mutual exclusion,
bare-integer stdout) carry over unchanged.

## Problem

`count-tokens` reached the Anthropic `count_tokens` endpoint on every
invocation, which made it need a credential and a network round-trip to answer
a question that is purely local.

The credential is the sharper half. `claude_config.config.load()` resolves
`ENV_FILE` relative to the module (`parents[2]`), so in a git worktree it looks
for that worktree's own `.env` — which is gitignored and absent. The subcommand
therefore failed outright in every worktree:

```
$ CLAUDE_CONFIG_ROOT=/root/claude-config-work3 agent-tools count-tokens "hello world"
KeyError: 'ANTHROPIC_TOKEN_COUNT_API_KEY'
```

## Solution

Count locally by default with a vendored tokenizer; keep the API behind `--api`.

```
agent-tools count-tokens [--api] [--model MODEL] [--file PATH] [TEXT]
```

- No flags: the vendored Qwen3.8 tokenizer. Offline, no credential.
- `--api`: the previous behaviour, unchanged.
- `--model`: the Claude model for `--api`, default `claude-opus-4-7`. Passing it
  without `--api` is an error.

### Tokenizer choice

`Qwen/Qwen3.8-27B` at revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`,
Apache-2.0, ungated, 248,077 tokenizer entries.

Sampled vocabulary sizes across the current generation of open-weight models
show no convergence to standardise on — K2-Horizon 250,624, Qwen3.8 248,320,
Nanbeige4.2 166,144, Ling-3.0 157,184, GLM-5.3 154,880, Spark-X2.5 131,072,
DeepSeek-V4 129,280, Hy4 120,832 (each model's `config.json`; that figure is the
padded embedding dimension, so it runs slightly above the tokenizer's own entry
count). Qwen3.8 sits at the top of that range, carries a permissive licence,
needs no HuggingFace authentication, and is the base other vendors fork —
`ornith-ai/Ornith-1.5-35B-A3B` reports `model_type: qwen3_5_moe` with the same
248,320.

### The two backends do not measure the same thing

This is the load-bearing property of the design and the reason no reconciliation
is attempted.

The API returns `input_tokens` for a whole request, so it carries a per-message
envelope of ~11 tokens: `"hello world"` is 2 locally and 14 over the API.

The tokenizers then diverge on top of that. Measured against
`messages.count_tokens` on `claude-opus-4-7`, with the envelope subtracted:

| content | Claude | Qwen3.8 | delta |
| --- | --- | --- | --- |
| deeply indented code | 1152 | 931 | −19% |
| minified JSON | 905 | 703 | −22% |
| base64 blob | 1315 | 991 | −25% |
| emoji / accented Latin | 529 | 397 | −25% |
| English prose | 169 | 109 | −36% |
| Russian | 216 | 114 | −47% |
| Japanese | 241 | 126 | −48% |
| Chinese | 289 | 114 | −61% |

The gap is not a deficiency in the open-source tokenizers — Claude's current one
is the coarse party. On `sys_prompt/alan-default-next.md`, Opus 5 and Sonnet 5
both report 10,002 and Opus 4.7 reports 10,007, while Haiku 4.5's older
tokenizer reports 7,113 — next door to Qwen3.8's 6,654. The bundled
`claude-api` skill states the same independently: "the Opus 4.7 tokenizer uses
~1×–1.35× as many tokens."

Because the ratio moves with content type, no scale factor converts one backend
into the other. Both therefore report raw, and `--help`, `CLAUDE.md` and this
spec say so; a count is comparable only to others from the same backend.

### Delivery: vendored, not fetched

The tokenizer ships in the repo at
`src/claude_config/tokenizer_data/qwen3_8_27b.json` (12.8 MB raw; ~5.4 MB as a
git blob, 3.6 MB in the built wheel). Vendoring keeps the default hermetic:
offline, identical across worktrees and container rebuilds, and unaffected by a
HuggingFace outage. Placing it inside the package means hatchling ships it and
`importlib.resources` finds it regardless of the invoking directory.

`PROVENANCE.json` sits beside it recording source, revision, sha256, byte
length and vocabulary size. `_count_local` verifies the digest on every run: a
swapped or truncated tokenizer would otherwise keep emitting plausible numbers.

## Files

| File | Change |
| --- | --- |
| `src/claude_config/tokenizer_data/qwen3_8_27b.json` | New. Vendored tokenizer. |
| `src/claude_config/tokenizer_data/PROVENANCE.json` | New. Source, revision, sha256, sizes. |
| `src/claude_config/count_tokens.py` | `--api` flag; `_count_local` / `_count_api` split; digest check; epilog documenting the backend gap. `anthropic` and dotenv now import only on the `--api` path. |
| `pyproject.toml` | Add `tokenizers>=0.22.1`. |
| `agent-tools/src/main.rs` | Subcommand doc comment; `disable_help_flag = true`. |
| `agent-tools/tests/count_tokens_test.rs` | Local-default and `--model`-without-`--api` cases; key-missing case moves behind `--api`; help case asserts forwarding. |
| `tests/test_count_tokens.py` | New. Pinned counts, provenance integrity, corruption failure. |
| `CLAUDE.md` | Rewrite the subcommand entry; document re-vendoring. |
| `notes/compliance-check-failure-mode.md` | Pin the ≤18k budget to `--api`. |
| `docs/opencode-system-prompt/trials/2026-08-23-handoff-confidence-v3-both-arms.md` | Mark the 878 figure as API-measured. |

`--help` is forwarded to the Python parser rather than answered by clap. Clap
would list the flags from the subcommand doc comment and look almost identical,
while dropping the epilog that warns the backends differ. The other pass-through
subcommands keep clap's help; machinery invokes those, and a person types this
one.

## Consequence for existing measurements

Every token figure recorded in `docs/` and `notes/` predates this change and was
taken against the API. Two live citations are pinned to `--api` so they keep
meaning what they meant; historical plan and spec documents describing the old
single-backend tool are left alone rather than retrofitted.

`notes/compliance-check-failure-mode.md` shows why pinning matters: its "≤18k
tokens" whole-file budget measures 20,938 through `--api` and 13,796 locally, so
leaving the bare command in place would have silently licensed roughly 50% more
content. Pinning it also surfaced that the file is already over its own budget
at 20,938; that overrun predates this change and is left for its maintainer,
with the stale "sits ~18k" claim corrected to the measured figure.

## Testing

Rust (`agent-tools/tests/count_tokens_test.rs`), all with
`ANTHROPIC_TOKEN_COUNT_API_KEY` removed and `PYTHON_DOTENV_DISABLED=1` so no
credential resolves even from the canonical checkout:

1. `--help` reaches the Python parser — asserted via epilog text, not flag names.
2. Default backend succeeds with no credential and prints a positive integer.
3. Default backend reads `--file` with no credential.
4. `--file /nonexistent` still fails loudly.
5. `--file X TEXT` still rejected as mutually exclusive.
6. `--model` without `--api` is rejected.
7. `--api` with no key still fails loudly naming the key.

Python (`tests/test_count_tokens.py`): vendored file matches its recorded digest
and byte length; provenance pins a 40-hex-character revision; four known strings
have pinned counts; empty input counts 0, proving no special tokens are added;
stdin and `--file` agree; a one-bit corruption raises with "does not match its
recorded digest".

The API backend is exercised manually rather than in CI, since it needs a
credential and network: `--api --file sys_prompt/alan-default-next.md` → 10,007,
and `--api --model claude-opus-5 --file sys_prompt/alan-default-next.md` → 10,002.
Both cite a file this change does not touch; citing `CLAUDE.md`, which it does
edit, would have made the numbers unreproducible the moment they were written.

## Acceptance criteria

1. `agent-tools count-tokens "hello world"` prints `2` with no credential and no network.
2. `agent-tools count-tokens --api --file CLAUDE.md` prints the API count where a key resolves.
3. `agent-tools count-tokens --model claude-opus-5 x` exits non-zero.
4. `agent-tools count-tokens --help` shows the backends epilog.
5. A corrupted vendored tokenizer raises rather than returning a number.
6. `cargo test --test count_tokens_test` and `pytest tests/test_count_tokens.py` pass.
