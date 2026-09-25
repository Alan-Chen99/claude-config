# The three log front-ends share one CLI surface and one pipeline

`cc-pretty`, `opencode-pretty` and `cc-pretty-intercept` read three formats and
answer the same questions about them. Two of them had converged: `opencode-pretty`
calls `add_shared_args` and `run_pipeline`, so every flag `cc-pretty` grows it
gets for free. `cc-pretty-intercept` had its own argparse block and its own
render loop, and had drifted.

Measured on 2026-09-25, before the change:

| | cc-pretty | opencode-pretty | cc-pretty-intercept |
| --- | --- | --- | --- |
| Long flags | 15 | 15 + `--from-file` | 6 |
| `add_shared_args` | yes | yes | no |
| `run_pipeline` | yes | yes | no |

Absent from the intercept renderer: `--agent`, `--chat-only`, `--color`,
`--compact-all`, `--compact-leg`, `--no-progress`, `--show-all`, `--show-rewound`,
`--show-usage`, `--skeleton`, `--validate-only`.

## What the drift cost, beyond the flags

The intercept renderer drove `Renderer`'s private block methods directly, passing
a `.json` path as the `log_path` the renderer builds recovery recipes from. Three
defects followed, each reproduced against
`~/.claude/requests-log/4082bccb-76f8-4bc2-b485-a11ef94272a1/0018.json`:

- **Every recovery recipe failed.** A truncated block printed
  `sed -n '1p' <file>.json | jq -r '.message.content[0].content'`. A capture is
  one pretty-printed object, not JSONL, and its shape is `.request.messages[k]`,
  not `.message`. Run verbatim: `jq: parse error: Unfinished JSON term at EOF`,
  exit 5.
- **Every ref was `@L1`.** `_render_message` and `_render_response` both took
  `lineno=1`. That file emitted 29 `@L1`, 9 `@L1[2]`, 4 `@L1[1]` — refs collided
  across messages and with the response, and no legend was printed to say what
  they meant.
- **Colors leaked into pipes.** No `detect_color`; ANSI unless `--no-color`.

## Where the capture's regions live in the record model

A capture holds two things cc's record model has no type for: the API `system`
prompt and the `tools` definitions. They become `SystemRecord`s under `api_`
subtypes — `api_system` (one per part), `api_tools`, plus `api_error`,
`api_refusal` and `api_transport_error` for a call that failed.

`is_model_visible` treats any `api_` subtype as visible. cc's own system records
are bookkeeping and hidden by default; these are the opposite — the system prompt
is the most model-visible content a capture has. `--chat-only` still drops them,
which is what that flag is for.

`render_system`'s fallback arm prints a header and drops the body, so these get
their own arm: truncated against `--tool-max`, with a ref and a recovery hint
like any other addressable block. `render_skeleton` already handled
`SystemRecord` generically and needed no new arm.

`--no-system` and `--no-tools` survive as the only front-end-only flags, applied
during conversion rather than at render time — a dropped region then costs no ref
numbers and the remaining refs stay contiguous.

## Addressing a record that is not a line

cc and opencode both number records so the ref locates them: line `n` of the
JSONL, message `n` of the export. A capture's records are spread across four
named top-level regions, so `@L7` alone locates nothing.

The converter therefore returns `jq_paths: dict[int, str]` alongside the records
— the jq address it assigned each one — which reaches `recovery_cmd` through
`PipelineInput` and `Renderer`. `recovery_cmd` raises rather than guessing when
an intercept ref arrives without an address: a wrong recipe reads as truth.

The per-family jq leaves (`.input` vs `.state.input`, `.content` vs
`.message.content`) moved out of the call sites into one `_LEAVES` table keyed by
`source_family(log_path)`. Three families is where the inline ternaries stopped
paying.

## Two defects this surfaced in the shared renderer

Both were reachable from cc JSONL too, and both dropped content silently:

- An assistant message whose `content` is a bare string — an API prefill, and
  `Message.content` is typed `str | list` — rendered as an empty turn, because
  `content_blocks()` yields `[]` for one. `render_assistant_turn` and
  `render_skeleton` now have a string arm.
- `render_system` received no `lineno`, so no system record could carry a ref.

## Out of scope

Id resolution. `docs/superpowers/specs/2026-09-17-cc-pretty-id-or-path-design.md`
decided captures keep taking paths — a different store with a different key, and
`cc-render-coverage` dispatches on the `.jsonl` extension. That holds: the
positional argument is the one place the three front-ends still differ, and
`--from-file` exists only because `opencode-pretty`'s positional is an id.

## Tests

`tests/test_pretty_parity.py` pins the surface itself: every front-end accepts
every shared flag, no front-end carries an unlisted private flag, and the three
`--tool-max` defaults (200 / 2000 / 4000) are pinned so a change is a decision.
Drift is otherwise silent — a front-end that stops calling `add_shared_args`
passes every other test in the suite.

`tests/test_cc_pretty_intercept.py` drives `main()` end-to-end against captures
on disk, and executes every recovery recipe the render emits with `jq`, asserting
each exits 0 and extracts something. A recipe that does not run is worse than no
recipe.

`cc-render-coverage` now renders captures through `run_pipeline` rather than
reconstructing a render from private helpers, so it exercises the shipping path.
400 real captures: clean.
