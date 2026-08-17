# session-analysis: skeleton-first reading protocol + merged skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every rendered block in cc-pretty/opencode-pretty a source-true, documented path to its raw string; add a `--skeleton` block-map mode; merge `session-timeline` + `diagnose-session` into one `session-analysis` skill built on a skeleton → batched-extraction reading protocol.

**Architecture:** Spec at `docs/superpowers/specs/2026-08-12-session-analysis-skeleton-design.md`. Both tools share `cc_pretty.main.run_pipeline` / `cc_pretty.render.Renderer`. opencode conversion (`opencode_pretty/convert.py`) tags each synthesized block with `_pi` (source part index) so refs survive dropped parts. A new `render_skeleton` in `render.py` emits one line per block with ref, size, jq leaf, preview, plus hidden-region markers carrying reveal flags. The merged skill documents the protocol and three modes.

**Tech Stack:** Python 3.14, pydantic, pytest, argparse. No new dependencies.

**Environment (worktree!):** This repo is worktree `/root/claude-config-work3` of `/repos/claude-config`. The installed `agent-tools` (`~/.local/bin/agent-tools`) points at the CANONICAL repo — it will NOT exercise worktree code. Use:
- Tests: `uv run pytest tests/test_opencode_pretty.py tests/test_cc_pretty_render.py -q` (run from `/root/claude-config-work3`)
- CLI smoke: `CLAUDE_CONFIG_ROOT=/root/claude-config-work3 ./agent-tools/target/release/agent-tools <subcommand>`

---

### Task 1: convert.py — source-true part indices (`_pi`, `_out_len`)

opencode conversion drops parts (`step-start`, `step-finish`, `patch`, `file`), shifting block positions away from the export's `parts[]` indices. Tag every synthesized block with `_pi` (its source part index) and every tool_use block with `_out_len` (its output char count, for the skeleton's `out:` column). `_Base` in parse.py has `extra: "allow"`, so these survive pydantic validation and are readable via `getattr(block, "_pi", None)`.

**Files:**
- Modify: `src/claude_config/opencode_pretty/convert.py` (`_build_assistant_blocks`, `_collect_user_text`, `_make_user_record` and its caller)
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_opencode_pretty.py`:

```python
# ─── Source-true part indices (_pi / _out_len) ──────────────────────────────


def test_export_to_records_tags_blocks_with_source_part_index() -> None:
    records, _ = export_to_records(sample_export())
    asst = records[1][0]
    blocks = asst.message.content_blocks()
    # parts: [step-start(0), reasoning(1), text(2), tool(3), step-finish(4),
    #         unknown(5)] — rendered blocks must keep the export's indices.
    assert getattr(blocks[0], "_pi") == 1  # thinking (reasoning part)
    assert getattr(blocks[1], "_pi") == 2  # text part
    assert getattr(blocks[2], "_pi") == 3  # tool_use part
    assert getattr(blocks[2], "_out_len") == len("file contents here")
    result_blocks = records[2][0].message.content_blocks()
    assert getattr(result_blocks[0], "_pi") == 3  # result refs the tool part


def test_export_to_records_tags_user_record_with_first_text_part_index() -> None:
    records, _ = export_to_records(sample_export())
    user_rec = records[0][0]
    assert getattr(user_rec, "_pi") == 0  # sole text part at index 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_opencode_pretty.py -q -k "source_part_index or first_text_part_index"`
Expected: FAIL — `getattr(...) == None` assertions.

- [ ] **Step 3: Implement**

In `src/claude_config/opencode_pretty/convert.py`, replace `_build_assistant_blocks` with:

```python
def _build_assistant_blocks(
    parts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (content_blocks, tool_result_blocks) for an assistant message.

    content_blocks are emitted on the AssistantRecord (in part order).
    tool_result_blocks go on a follow-up synthetic UserRecord so cc-pretty's
    renderer pairs each ``◀ result`` with its preceding ``▶ tool_use``.

    Every block carries ``_pi`` — the index of the export part it came from.
    Dropped parts (step-start/step-finish/patch/file/...) would otherwise
    shift the renderer's enumeration index away from the jq path the legend
    promises (``.messages[n-1].parts[i]``). Tool blocks also carry
    ``_out_len`` (output char count) for the skeleton's ``out:`` column.
    """
    content: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for pi, part in enumerate(parts):
        typ = part.get("type")
        if typ == "reasoning":
            text = part.get("text", "")
            if text:
                content.append({"type": "thinking", "thinking": text, "_pi": pi})
        elif typ == "text":
            text = part.get("text", "")
            if text:
                content.append({"type": "text", "text": text, "_pi": pi})
        elif typ == "tool":
            call_id = part.get("callID", "") or part.get("id", "")
            name = part.get("tool", "tool")
            state = part.get("state") if isinstance(part.get("state"), dict) else {}
            status = state.get("status")
            out_len = 0
            if status == "completed":
                out_text = str(state.get("output", ""))
                out_len = len(out_text)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": call_id,
                    "content": out_text,
                    "is_error": False,
                    "_pi": pi,
                })
            elif status == "error":
                out_text = str(state.get("error", ""))
                out_len = len(out_text)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": call_id,
                    "content": out_text,
                    "is_error": True,
                    "_pi": pi,
                })
            content.append({
                "type": "tool_use",
                "id": call_id,
                "name": name,
                "input": state.get("input", {}),
                "_pi": pi,
                "_out_len": out_len,
            })
        # step-start / step-finish / snapshot / patch / agent / subtask /
        # retry / file: not rendered. They're either bookkeeping or carry
        # signal we don't have a slot for in the cc-pretty record types.
    return content, results
```

Replace `_collect_user_text` with:

```python
def _collect_user_text(parts: list[dict[str, Any]]) -> tuple[str, int]:
    """Flatten user-message parts; return (text, first text part index).

    Multi-part user inputs in opencode are usually a text body plus optional
    file attachments. We render the text and tag each file with a brief
    pointer line; cc-pretty's user-input renderer just emits this verbatim.

    The part index lets the user message's ref point at its first text part
    so the documented jq path (``.messages[n-1].parts[i].text``) resolves to
    the visible text. Multi-text-part messages lose per-part granularity —
    the flattening predates refs; documented limitation.
    """
    chunks: list[str] = []
    first_text_pi = 0
    seen_text = False
    for pi, part in enumerate(parts):
        typ = part.get("type")
        if typ == "text":
            text = part.get("text", "")
            if text:
                if not seen_text:
                    first_text_pi = pi
                    seen_text = True
                chunks.append(text)
        elif typ == "file":
            label = part.get("filename") or part.get("url") or "file"
            mime = part.get("mime") or "?"
            chunks.append(f"[attached {mime}: {label}]")
    return "\n\n".join(chunks), first_text_pi
```

Update the user-record caller in `export_to_records`:

```python
            user_text, user_pi = _collect_user_text(parts)
            rec = _make_user_record(
                session_id=session_id,
                msg_id=m_id,
                parent_id=parent_id,
                ts=ts,
                content=user_text,
                part_idx=user_pi,
                extra=common_meta,
            )
```

Update `_make_user_record` — add the `part_idx` parameter and `_pi` field:

```python
def _make_user_record(
    *,
    session_id: str,
    msg_id: str,
    parent_id: str | None,
    ts: str,
    content: str,
    part_idx: int,
    extra: dict[str, Any],
) -> Record:
    return parse_record({
        "type": "user",
        "uuid": msg_id,
        "parentUuid": parent_id,
        "sessionId": session_id,
        "timestamp": ts,
        "_pi": part_idx,
        "message": {
            "role": "user",
            "content": content,
        },
        **extra,
    })
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_opencode_pretty.py -q`
Expected: all PASS (new two + existing — `_pi` extras don't change record counts).

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/opencode_pretty/convert.py tests/test_opencode_pretty.py
git commit -m "opencode-pretty: tag converted blocks with source part index (_pi, _out_len)"
```

---

### Task 2: render.py — ref resolution, recovery commands, two-line legend

Primitives everything else uses: `block_ref` (source-true ref), `recovery_cmd` (exact shell command for a block), `legend_lines` (per-harness ref+leaf documentation), and a three-way `render_legend` (cc file / opencode session / opencode `--from-file`).

**Files:**
- Modify: `src/claude_config/cc_pretty/render.py` (`render_legend` area)
- Test: `tests/test_cc_pretty_render.py`

- [ ] **Step 1: Write the failing tests**

Update the import block at the top of `tests/test_cc_pretty_render.py` to include the new names:

```python
from claude_config.cc_pretty.render import (
    C,
    Renderer,
    block_ref,
    fmt_ref,
    legend_lines,
    recovery_cmd,
    render_legend,
    separator,
    trunc,
)
```

Append:

```python
# ─── block_ref / recovery_cmd / legend_lines (direct-str access) ────────────


def test_block_ref_prefers_source_part_index_when_present() -> None:
    class _B:
        pass
    b = _B()
    b._pi = 3
    assert block_ref(b, 2, 0) == "@L2[3]"
    assert block_ref(_B(), 2, 0) == "@L2"      # no _pi → enumeration index
    assert block_ref(_B(), 2, 1) == "@L2[1]"


def test_recovery_cmd_opencode_session() -> None:
    cmd = recovery_cmd("opencode://ses_abc", 5, 3, ".state.output")
    assert cmd == (
        "opencode export ses_abc > /tmp/oc-ses_abc.json && "
        "jq -r '.messages[4].parts[3].state.output' /tmp/oc-ses_abc.json"
    )


def test_recovery_cmd_opencode_from_file() -> None:
    cmd = recovery_cmd("opencode-file:///tmp/x.json", 5, 3, ".text")
    assert cmd == "jq -r '.messages[4].parts[3].text' /tmp/x.json"


def test_recovery_cmd_cc_block_and_record_level() -> None:
    assert recovery_cmd("/tmp/s.jsonl", 57, 0, ".content") == (
        "sed -n '57p' /tmp/s.jsonl | jq -r '.message.content[0].content'"
    )
    assert recovery_cmd("/tmp/s.jsonl", 12, None, ".message.content") == (
        "sed -n '12p' /tmp/s.jsonl | jq -r '.message.content'"
    )


def test_legend_lines_cover_every_block_type_per_harness() -> None:
    cc = "\n".join(legend_lines("/tmp/s.jsonl"))
    for token in (".thinking", ".text", ".input", ".content",
                  ".message.content", ".attachment.content", "sed -n"):
        assert token in cc, token
    oc = "\n".join(legend_lines("opencode://ses_x"))
    for token in (".text", ".state.input", ".state.output",
                  "opencode export ses_x"):
        assert token in oc, token
    oc_file = "\n".join(legend_lines("opencode-file:///tmp/x.json"))
    assert "opencode export" not in oc_file
    assert "jq -r" in oc_file and "/tmp/x.json" in oc_file
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cc_pretty_render.py -q -k "block_ref or recovery_cmd or legend_lines"`
Expected: FAIL — `ImportError: cannot import name 'block_ref'`.

- [ ] **Step 3: Implement**

In `src/claude_config/cc_pretty/render.py`, replace `render_legend` with the following (keep `fmt_ref` unchanged above it):

```python
def _resolve_idx(block: object, enum_idx: int) -> int:
    """Source-true block index: opencode ``_pi`` when present, else enum index."""
    pi = getattr(block, "_pi", None)
    return pi if isinstance(pi, int) else enum_idx


def block_ref(block: object, lineno: int, enum_idx: int) -> str:
    """Ref for a content block, source-true across harnesses.

    opencode conversion tags each block with ``_pi`` — the index of the part
    in the exported message it came from — because dropped parts
    (step-start/step-finish/...) would otherwise shift the enumeration index
    away from the jq path the legend promises. cc-pretty blocks have no
    ``_pi``; their enumeration index already matches ``.message.content[i]``.
    """
    return fmt_ref(lineno, _resolve_idx(block, enum_idx))


def _is_opencode_path(log_path: str) -> bool:
    return log_path.startswith(("opencode://", "opencode-file://"))


def recovery_cmd(log_path: str, lineno: int, block_idx: int | None, leaf: str) -> str:
    """Exact shell command printing the raw string behind a ref.

    ``block_idx`` is the source-true block/part index (see :func:`block_ref`);
    ``None`` means the leaf addresses the whole record (cc user string input,
    attachments). ``leaf`` is the jq path suffix appended after the block
    selector (e.g. ``.state.output``, ``.content``).
    """
    if log_path.startswith("opencode://"):
        sid = log_path[len("opencode://"):]
        f = f"/tmp/oc-{sid}.json"
        path = f".messages[{lineno - 1}].parts[{block_idx or 0}]{leaf}"
        return f"opencode export {sid} > {f} && jq -r '{path}' {f}"
    if log_path.startswith("opencode-file://"):
        src = log_path[len("opencode-file://"):]
        path = f".messages[{lineno - 1}].parts[{block_idx or 0}]{leaf}"
        return f"jq -r '{path}' {src}"
    if block_idx is None:
        return f"sed -n '{lineno}p' {log_path} | jq -r '{leaf}'"
    return (f"sed -n '{lineno}p' {log_path} | "
            f"jq -r '.message.content[{block_idx}]{leaf}'")


def legend_lines(log_path: str) -> list[str]:
    """The two hint lines documenting refs + recovery for this log source."""
    if log_path.startswith("opencode://"):
        sid = log_path[len("opencode://"):]
        return [
            "# refs @L<n>[i] = .messages[n-1].parts[i] (i=0 omitted) · "
            "leafs: reasoning/text/user .text · tool .state.input/.state.output",
            f"# recover: opencode export {sid} > /tmp/oc-{sid}.json "
            f"&& jq -r '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-{sid}.json",
        ]
    if log_path.startswith("opencode-file://"):
        src = log_path[len("opencode-file://"):]
        return [
            "# refs @L<n>[i] = .messages[n-1].parts[i] (i=0 omitted) · "
            "leafs: reasoning/text/user .text · tool .state.input/.state.output",
            f"# recover: jq -r '.messages[<n-1>].parts[<i>]<leaf>' {src}",
        ]
    return [
        "# refs @L<n>[i] = line n, .message.content[i] (i=0 omitted) · "
        "leafs: thinking .thinking · text .text · ▶ .input · ◀ result .content · "
        "◀ context .text · user .message.content · attach .attachment.content",
        f"# recover: sed -n '<n>p' {log_path} | jq -r '<path>'",
    ]


def render_legend(log_path: str) -> str:
    """Two-line hint header documenting how to recover raw content behind refs.

    Printed once at the top of the full render (and reused as the skeleton
    header's recipe lines). ``opencode export`` truncates its stdout at ~64KB
    on a pipe, so the session recipe redirects to a file first — a bare
    ``opencode export ... | jq ...`` silently loses everything past the
    first pipe buffer.
    """
    return "\n".join(f"{C.HINT}{line}{C.RESET}" for line in legend_lines(log_path))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_cc_pretty_render.py tests/test_opencode_pretty.py -q`
Expected: all PASS — including existing legend tests (they assert substrings that still hold).

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/cc_pretty/render.py tests/test_cc_pretty_render.py
git commit -m "cc-pretty: block_ref/recovery_cmd/legend_lines — per-harness direct-str paths"
```

---
### Task 3: render.py — refs on every block + truncation hints

Full render currently refs only tool calls/results/context/attachments. Add refs to thinking headers, text blocks, and user-input headers; add an exact recovery command under any block truncated by `--tool-max`/`--truncate-input`.

**Files:**
- Modify: `src/claude_config/cc_pretty/render.py` (`_render_thinking`, `_render_tool_use`, `_render_tool_result`, `_render_context_text`, `render_user_input`, `render_assistant_turn`, `render_attachment`)
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_opencode_pretty.py`:

```python
# ─── Full-render refs + truncation hints ────────────────────────────────────


def test_full_render_refs_are_source_true_on_every_block_type() -> None:
    output = render(sample_export())
    # thinking header carries the TRUE part index (step-start part shifted it)
    assert "╭─ thinking" in output and "@L2[1]" in output
    # text block marker line
    assert "── text @L2[2] ──" in output
    # tool_use AND its result both reference the tool part @L2[3]
    assert "▶ read" in output and "@L2[3]" in output
    # user input header carries a ref
    user_line = next(l for l in output.splitlines() if l.startswith("┌ User"))
    assert "@L1" in user_line


def test_truncated_tool_result_prints_exact_recovery_command() -> None:
    export = sample_export()
    export["messages"][1]["parts"][3]["state"]["output"] = "y" * 5000
    output = render(export, tool_max=100)
    assert (
        "…full: opencode export ses_1234567890abcdef > "
        "/tmp/oc-ses_1234567890abcdef.json && jq -r "
        "'.messages[1].parts[3].state.output' /tmp/oc-ses_1234567890abcdef.json"
    ) in output


def test_untruncated_blocks_print_no_hint() -> None:
    output = render(sample_export())
    assert "…full:" not in output


def test_truncated_tool_input_hint_points_at_state_input() -> None:
    export = sample_export()
    export["messages"][1]["parts"][3]["state"]["input"] = {"prompt": "x" * 500}
    output = render(export, tool_max=100, truncate_input=True)
    assert "…full:" in output and ".state.input'" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_opencode_pretty.py -q -k "source_true_on_every or recovery_command or no_hint or state_input"`
Expected: FAIL — no `@L2[1]` thinking ref, no `── text` marker, no `…full:` lines.

- [ ] **Step 3: Implement**

In `src/claude_config/cc_pretty/render.py`:

**3a.** Add a `_hint` method to `Renderer` (right after `__init__`):

```python
    def _hint(self, lineno: int, block_idx: int | None, leaf: str) -> str:
        """Dim recovery line printed under a truncated block."""
        cmd = recovery_cmd(self.log_path, lineno, block_idx, leaf)
        return f"    {C.DIM}…full: {cmd}{C.RESET}"
```

**3b.** Replace `_render_thinking`:

```python
    def _render_thinking(self, block: ThinkingBlock, lineno: int, block_idx: int) -> str:
        prefix = C.THINKING + "  │ " + C.RESET
        body = textwrap.indent(block.thinking, prefix, predicate=lambda _: True)
        ref = block_ref(block, lineno, block_idx)
        return (
            f"{C.THINKING}  ╭─ thinking ─────────────{C.RESET}  "
            f"{C.DIM}{ref}{C.RESET}\n"
            f"{body}\n"
            f"{C.THINKING}  ╰─────────────────────────────────────{C.RESET}"
        )
```

**3c.** Replace `_render_tool_use`:

```python
    def _render_tool_use(self, block: ToolUseBlock, lineno: int, block_idx: int) -> str:
        inp = block.input
        inp_str = fmt_tool_input(inp) if isinstance(inp, dict) else str(inp)

        if block.id:
            self._tool_id_to_name[block.id] = block.name

        ref = block_ref(block, lineno, block_idx)
        lines = [f"{C.TOOL}  ▶ {block.name}{C.RESET}  {C.DIM}{ref}{C.RESET}"]
        lines.append(ind(trunc(inp_str, self.tool_input_max), "    "))
        if len(inp_str) > self.tool_input_max:
            leaf = ".state.input" if _is_opencode_path(self.log_path) else ".input"
            lines.append(self._hint(lineno, _resolve_idx(block, block_idx), leaf))
        return "\n".join(lines)
```

**3d.** Replace `_render_tool_result`:

```python
    def _render_tool_result(self, block: ToolResultBlock, lineno: int, block_idx: int,
                            tur: str | ToolUseResultDict | None = None) -> str:
        tool_name = self._tool_id_to_name.get(block.tool_use_id, "")
        name_suffix = f" ({tool_name})" if tool_name else ""

        label_color = C.ERROR if block.is_error else C.RESULT
        label = f"✗ error{name_suffix}" if block.is_error else f"◀ result{name_suffix}"

        content = block.content
        truncated = False

        if isinstance(content, list):
            parts = []
            for sub in content:
                if sub.get("type") == "text":
                    t = sub.get("text", "")
                else:
                    t = str(sub)
                truncated = truncated or len(t) > self.tool_output_max
                parts.append(trunc(t, self.tool_output_max))
            body = "\n".join(parts)
        else:
            truncated = len(content) > self.tool_output_max
            body = trunc(content, self.tool_output_max)

        ref = block_ref(block, lineno, block_idx)
        lines = [
            f"{label_color}  {label}{C.RESET}  {C.DIM}{ref}{C.RESET}",
            ind(body, "    "),
        ]

        if truncated:
            leaf = ".state.output" if _is_opencode_path(self.log_path) else ".content"
            lines.append(self._hint(lineno, _resolve_idx(block, block_idx), leaf))

        if isinstance(tur, ToolUseResultDict):
            if tur.stderr:
                lines.append(f"    {C.DIM}stderr: {trunc(tur.stderr, 100)}{C.RESET}")
        elif isinstance(tur, str) and tur:
            lines.append(f"    {C.DIM}{trunc(tur, 120)}{C.RESET}")

        return "\n".join(lines)
```

**3e.** Replace `_render_context_text` (context blocks are TextBlocks — their raw string lives at `.text`, NOT `.content`):

```python
    def _render_context_text(self, text: str, lineno: int, block_idx: int) -> str:
        ref = fmt_ref(lineno, block_idx)
        lines = [
            f"{C.RESULT}  ◀ context{C.RESET}  {C.DIM}{ref}{C.RESET}",
            ind(trunc(text, self.tool_output_max), "    "),
        ]
        if len(text) > self.tool_output_max:
            lines.append(self._hint(lineno, block_idx, ".text"))
        return "\n".join(lines)
```

**3f.** Replace `render_user_input`:

```python
    def render_user_input(self, records: list[tuple[UserRecord, int]], ts: str) -> str:
        lines: list[str] = []
        first = True
        for rec, lineno in records:
            # opencode conversion tags the record with _pi (first text part
            # index) so the ref resolves to .messages[n-1].parts[pi].text.
            pi = getattr(rec, "_pi", None)
            ref = fmt_ref(lineno, pi if isinstance(pi, int) else 0)
            if first:
                lines.append(
                    f"{C.USER}┌ User{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}  "
                    f"{C.DIM}{ref}{C.RESET}"
                )
                first = False
            else:
                lines.append(f"  {C.DIM}── {ref} ──{C.RESET}")
            if isinstance(rec.message.content, str):
                lines.append(ind(rec.message.content, "  "))
        return "\n".join(lines)
```

**3g.** In `render_assistant_turn`, replace the body loop:

```python
        body: list[str] = []
        for rec, lineno in records:
            for bi, block in enumerate(rec.message.content_blocks()):
                if isinstance(block, ThinkingBlock):
                    if self.show_thinking:
                        body.append(self._render_thinking(block, lineno, bi))
                    else:
                        ref = block_ref(block, lineno, bi)
                        body.append(
                            f"{C.THINKING}  [thinking: {len(block.thinking)} chars]"
                            f"{C.RESET}  {C.DIM}{ref}{C.RESET}"
                        )
                elif isinstance(block, TextBlock):
                    body.append(
                        f"{C.DIM}  ── text {block_ref(block, lineno, bi)} ──{C.RESET}"
                    )
                    body.append(ind(block.text, "  "))
                elif isinstance(block, ToolUseBlock):
                    if self.chat_only:
                        continue
                    body.append(self._render_tool_use(block, lineno, bi))
```

**3h.** In `render_attachment`, `hook_additional_context` branch, replace the final two lines:

```python
            truncated_body = trunc(body, self.tool_output_max)
            lines = [header, ind(truncated_body, "  ")]
            if len(body) > self.tool_output_max:
                lines.append(self._hint(lineno, None, ".attachment.content"))
            return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_opencode_pretty.py tests/test_cc_pretty_render.py -q`
Expected: all PASS. (Existing assertions still hold: `test_render_tool_use_has_ref_and_no_toolu_id`'s `"sed -n" not in out` passes because the short input isn't truncated; `[thinking:` prefix unchanged.)

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/cc_pretty/render.py tests/test_opencode_pretty.py
git commit -m "cc-pretty: refs on every block + exact recovery hint under truncated blocks"
```

---

### Task 4: Marker reveal hints (rewind + compaction)

Hidden regions must self-document how to reveal them. Rewind markers gain `reveal: --show-rewound` when hidden; compaction markers gain `reveal: --compact-all or --compact-leg <n>` when their section is hidden by the current selection.

**Files:**
- Modify: `src/claude_config/cc_pretty/main.py` (`find_compaction_boundaries` results, marker call site)
- Modify: `src/claude_config/cc_pretty/render.py` (`render_rewind_marker`, `render_compaction_marker`)
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_opencode_pretty.py`:

```python
# ─── Marker reveal hints ────────────────────────────────────────────────────


def test_rewind_marker_prints_reveal_hint_when_hidden() -> None:
    export = sample_export()
    export["info"]["revert"] = {"messageID": "msg_001_user"}
    output = render(export)
    assert "⟲ rewind" in output
    assert "reveal: --show-rewound" in output


def test_rewind_marker_omits_reveal_hint_when_shown() -> None:
    export = sample_export()
    export["info"]["revert"] = {"messageID": "msg_001_user"}
    output = render(export, show_rewound=True)
    assert "⟲ rewind" in output
    assert "reveal: --show-rewound" not in output


def test_compaction_marker_prints_reveal_hint_when_leg_hidden() -> None:
    output = render(_add_compaction(sample_export()))
    assert "reveal: --compact-all or --compact-leg 0" in output


def test_compaction_marker_omits_reveal_hint_with_compact_all() -> None:
    output = render(_add_compaction(sample_export()), compact_all=True)
    assert "⟐ compacted" in output
    assert "reveal: --compact" not in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_opencode_pretty.py -q -k "reveal_hint"`
Expected: FAIL — no `reveal:` lines exist yet.

- [ ] **Step 3: Implement**

**3a.** In `src/claude_config/cc_pretty/main.py`, `find_compaction_boundaries`: add `"prev_start": prev_start` to the result dict:

```python
        results.append({
            "idx": boundary_idx,
            "section_num": bi + 1,
            "prev_start": prev_start,
            "prev_records": prev_end - prev_start,
            "prev_first_ts": fmt_ts(first_ts),
            "prev_last_ts": fmt_ts(last_ts),
            "prev_n_user": n_user,
            "prev_n_assistant": n_assistant,
            "tokens_before": last_tokens,
            "tokens_after": new_tokens,
        })
```

**3b.** In `src/claude_config/cc_pretty/render.py`, replace `render_rewind_marker`:

```python
    def render_rewind_marker(
        self, count: int, first_ts: str, last_ts: str,
        n_user: int, n_assistant: int, hidden: bool,
    ) -> str:
        time_range = f"{first_ts}\u2013{last_ts}" if first_ts != last_ts else first_ts
        turns = f"{n_user} user, {n_assistant} assistant"
        status = f"{count} records hidden" if hidden else f"{count} records shown above"
        out = (
            f"{C.REWIND}\f⟲ rewind{C.RESET}\n"
            f"{C.DIM}  {turns}  {time_range}  ({status}){C.RESET}"
        )
        if hidden:
            out += f"\n{C.DIM}  reveal: --show-rewound{C.RESET}"
        return out
```

**3c.** Replace `render_compaction_marker`:

```python
    def render_compaction_marker(
        self, section_num: int, prev_records: int,
        prev_first_ts: str, prev_last_ts: str,
        prev_n_user: int, prev_n_assistant: int,
        tokens_before: int, tokens_after: int,
        section_hidden: bool,
    ) -> str:
        time_range = (
            f"{prev_first_ts}\u2013{prev_last_ts}"
            if prev_first_ts != prev_last_ts else prev_first_ts
        )
        header = f"{C.SYSTEM}\f⟐ compacted{C.RESET}"
        prev_summary = (
            f"  section {section_num}: "
            f"{prev_n_user} user, {prev_n_assistant} assistant  "
            f"{time_range}  ({prev_records} records)"
        )
        token_info = ""
        if tokens_before or tokens_after:
            parts = []
            if tokens_before:
                parts.append(f"{tokens_before:,}tok")
            if tokens_after:
                parts.append(f"{tokens_after:,}tok")
            arrow = " → ".join(parts)
            token_info = f"\n{C.DIM}  context: {arrow}{C.RESET}"
        out = f"{header}\n{C.DIM}{prev_summary}{C.RESET}{token_info}"
        if section_hidden:
            out += (
                f"\n{C.DIM}  reveal: --compact-all or "
                f"--compact-leg {section_num - 1}{C.RESET}"
            )
        return out
```

**3d.** In `src/claude_config/cc_pretty/main.py` `run_pipeline`, update the compaction-marker call site to compute `section_hidden`:

```python
        if i in compaction_markers:
            cb = compaction_markers[i]
            print(separator())
            print(r.render_compaction_marker(
                section_num=cb["section_num"],
                prev_records=cb["prev_records"],
                prev_first_ts=cb["prev_first_ts"],
                prev_last_ts=cb["prev_last_ts"],
                prev_n_user=cb["prev_n_user"],
                prev_n_assistant=cb["prev_n_assistant"],
                tokens_before=cb["tokens_before"],
                tokens_after=cb["tokens_after"],
                section_hidden=all(
                    j in compact_hidden for j in range(cb["prev_start"], i)
                ),
            ))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_opencode_pretty.py tests/test_cc_pretty_render.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/cc_pretty/main.py src/claude_config/cc_pretty/render.py tests/test_opencode_pretty.py
git commit -m "cc-pretty: rewind/compaction markers carry reveal hints for hidden regions"
```

---

### Task 5: `--skeleton` density mode

**Folded review follow-ups (from Tasks 3-4 reviews) — apply FIRST as their own commit:**
1. Remove the redundant local `from claude_config.cc_pretty.parse import ToolResultBlock` inside `test_cc_tool_result_truncation_hint_uses_sed_and_content_leaf` (it is imported at module top).
2. Add compact-leg pin tests to tests/test_opencode_pretty.py: `render(_add_compaction(sample_export()), compact_leg=1)` → `reveal: --compact` present; `compact_leg=0` → `reveal: --compact` absent.
3. Guard the vacuous-true case: run_pipeline call site becomes `section_hidden=cb["prev_records"] > 0 and all(...)`; mirror the same `cb["prev_records"] > 0 and` guard in `render_skeleton`'s marker computation (3a below).
Commit: `cc-pretty: review follow-ups — compact-leg pins, zero-record section guard`.

New DENSITY flag: one line per content block (ref, type, ~tok size, jq leaf, preview) plus hidden-region marker lines, with a header carrying identity, the size heuristic, and the recovery recipe. Flags reorganized into argparse axis groups so `--help` documents the spec.

**Files:**
- Modify: `src/claude_config/cc_pretty/render.py` (new `render_skeleton` + helpers)
- Modify: `src/claude_config/cc_pretty/main.py` (`add_shared_args` regrouped + `--skeleton`, `run_pipeline` branch, module docstring)
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_opencode_pretty.py`:

```python
# ─── Skeleton density ───────────────────────────────────────────────────────


def test_skeleton_renders_one_line_per_block_with_refs_sizes_leafs() -> None:
    export = sample_export()
    # Long reasoning text so we can prove the skeleton shows previews, not bodies.
    export["messages"][1]["parts"][1]["text"] = "deep thought " * 100
    output = render(export, skeleton=True)
    lines = output.splitlines()
    assert lines[0].startswith("# skeleton: parser-work")
    assert any("~tok" in l and "sizes" in l for l in lines[:3])
    assert any(l.startswith("@L1") and "user" in l and ".text" in l
               and '"please inspect this"' in l for l in lines)
    # reasoning at TRUE part index 1 (step-start occupies part 0)
    assert any(l.startswith("@L2[1]") and "reasoning" in l for l in lines)
    assert any(l.startswith("@L2[2]") and "text" in l for l in lines)
    assert any(l.startswith("@L2[3]") and "tool:read" in l
               and ".state.input/.state.output" in l
               and "/tmp/example.txt" in l for l in lines)
    # full bodies must NOT appear — skeleton is previews only
    assert "deep thought deep thought deep thought deep thought deep thought" \
        not in output


def test_skeleton_marks_hidden_regions_with_reveal_flags() -> None:
    output = render(_add_compaction(sample_export()), skeleton=True)
    assert "⟐ compacted · section 1" in output
    assert "reveal: --compact-all or --compact-leg 0" in output
    assert "please inspect this" not in output  # hidden leg: no block lines


def test_skeleton_compact_all_lists_every_leg_without_reveal() -> None:
    output = render(_add_compaction(sample_export()),
                    skeleton=True, compact_all=True)
    assert '"please inspect this"' in output
    assert "reveal: --compact" not in output


def test_cli_rejects_chat_only_and_skeleton_together(tmp_path) -> None:
    export_file = tmp_path / "export.json"
    export_file.write_text(json.dumps(sample_export()))
    proc = _run_cli(export_file, "--chat-only", "--skeleton")
    assert proc.returncode == 2
    assert "not allowed with argument" in proc.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_opencode_pretty.py -q -k "skeleton"`
Expected: FAIL — `make_args(skeleton=True)` sets the attribute but `run_pipeline` has no skeleton branch, so the render lacks the `# skeleton:` header.

- [ ] **Step 3: Implement**

**3a.** In `src/claude_config/cc_pretty/render.py`, add the import and append the skeleton section at the end of the file:

```python
from collections.abc import Callable  # top of file, with the other imports
```

```python
# ─── Skeleton (one line per block) ───────────────────────────────────────────

def _tok(s: str) -> int:
    """~token estimate for the skeleton size column (chars/4 heuristic)."""
    return len(s) // 4


def _preview(s: str, width: int = 50) -> str:
    one = " ".join(s.split())
    if len(one) > width:
        return one[:width] + "…"
    return one


def _tool_target(inp: Any) -> str:
    """Short target summary for a tool line (filePath, command, ...)."""
    if not isinstance(inp, dict):
        return _preview(str(inp), 60)
    for key in ("filePath", "command", "pattern", "path", "name",
                "description", "prompt"):
        val = inp.get(key)
        if isinstance(val, str) and val:
            return _preview(val, 60)
    return _preview(json.dumps(inp), 60)


def render_skeleton(
    records: list[tuple[Record, int]],
    *,
    log_path: str,
    compact_hidden: set[int],
    hidden_for_rewind: set[int],
    compaction_markers: dict[int, dict],
    rewind_markers: dict[int, dict],
    record_visible: Callable[[Record], bool],
) -> str:
    """One line per content block + hidden-region markers with reveal hints.

    The skeleton is a block map: every line names its ref, approx size, and
    jq leaf so a reader can plan ~10k-token batches and extract exactly those
    blocks with one jq/sed command (see skills/session-analysis).
    Bookkeeping records (progress, snapshots, queue ops, ...) are skipped;
    --show-all surfaces model-invisible attachments/system lines.
    """
    oc = _is_opencode_path(log_path)
    tool_id_to_name: dict[str, str] = {}
    lines: list[str] = []

    # Header: identity + size heuristic + the shared legend recipe lines.
    first = records[0][0] if records else None
    slug = getattr(first, "slug", "") or ""
    if not slug and not oc:
        slug = log_path.rsplit("/", 1)[-1]
    cwd = getattr(first, "cwd", "") or ""
    model = ""
    for rec, _ in records:
        m = getattr(getattr(rec, "message", None), "model", "")
        if m:
            model = m
            break
    n_units = len({ln for _, ln in records}) if oc else (records[-1][1] if records else 0)
    unit = "msgs" if oc else "lines"
    head = f"# skeleton: {slug} · {n_units} {unit}"
    if model:
        head += f" · {model}"
    if cwd:
        head += f" · {cwd}"
    lines.append(head)
    lines.append("# sizes: ~tok ≈ chars/4 (batch-planning heuristic)")
    lines.extend(legend_lines(log_path))

    def emit(ref: str, label: str, size: str, leaf: str, preview: str) -> None:
        lines.append(
            f"{ref:<10} {label:<18} {size:<20} {leaf:<26} {preview}".rstrip()
        )

    def rewind_line(m: dict) -> str:
        line = f"⟲ rewind · {m['count']} records"
        line += " hidden · reveal: --show-rewound" if m["hidden"] else " shown above"
        return line

    for i, (rec, lineno) in enumerate(records):
        if i in compaction_markers:
            cb = compaction_markers[i]
            hidden = (cb["prev_records"] > 0 and
                      all(j in compact_hidden
                          for j in range(cb["prev_start"], cb["idx"])))
            line = (f"⟐ compacted · section {cb['section_num']} "
                    f"({cb['prev_records']} records)")
            if hidden:
                line += (f" hidden · reveal: --compact-all or "
                         f"--compact-leg {cb['section_num'] - 1}")
            lines.append(line)
        if i in rewind_markers:
            lines.append(rewind_line(rewind_markers[i]))
        if i in compact_hidden or i in hidden_for_rewind:
            continue
        if not record_visible(rec):
            continue

        if isinstance(rec, AssistantRecord):
            for bi, block in enumerate(rec.message.content_blocks()):
                ref = block_ref(block, lineno, bi)
                if isinstance(block, ThinkingBlock):
                    emit(ref, "reasoning" if oc else "thinking",
                         f"{_tok(block.thinking)}~tok",
                         ".text" if oc else ".thinking",
                         f'"{_preview(block.thinking)}"')
                elif isinstance(block, TextBlock):
                    emit(ref, "text", f"{_tok(block.text)}~tok", ".text",
                         f'"{_preview(block.text)}"')
                elif isinstance(block, ToolUseBlock):
                    if block.id:
                        tool_id_to_name[block.id] = block.name
                    inp_str = (fmt_tool_input(block.input)
                               if isinstance(block.input, dict)
                               else str(block.input))
                    if oc:
                        out_len = getattr(block, "_out_len", 0)
                        size = f"in:{_tok(inp_str)} out:{out_len // 4}~tok"
                        leaf = ".state.input/.state.output"
                    else:
                        size = f"in:{_tok(inp_str)}~tok"
                        leaf = ".input"
                    emit(ref, f"tool:{block.name}", size, leaf,
                         _tool_target(block.input))

        elif isinstance(rec, UserRecord):
            if isinstance(rec.message.content, str):
                pi = getattr(rec, "_pi", None)
                ref = fmt_ref(lineno, pi if isinstance(pi, int) else 0)
                emit(ref, "user", f"{_tok(rec.message.content)}~tok",
                     ".text" if oc else ".message.content",
                     f'"{_preview(rec.message.content)}"')
            else:
                for bi, block in enumerate(rec.message.content_blocks()):
                    ref = block_ref(block, lineno, bi)
                    if isinstance(block, ToolResultBlock):
                        name = tool_id_to_name.get(block.tool_use_id, "")
                        label = f"result:{name}" if name else "result"
                        content = block.content
                        text = (
                            "".join(
                                s.get("text", "") for s in content
                                if isinstance(s, dict) and s.get("type") == "text"
                            )
                            if isinstance(content, list) else str(content)
                        )
                        emit(ref, label, f"{_tok(text)}~tok",
                             ".state.output" if oc else ".content",
                             f'"{_preview(text)}"')
                    elif isinstance(block, TextBlock):
                        # cc context block — raw string at .text, not .content
                        emit(ref, "context", f"{_tok(block.text)}~tok",
                             ".text", f'"{_preview(block.text)}"')

        elif isinstance(rec, AttachmentRecord):
            a = rec.attachment
            body = a.content
            text = ("\n\n".join(str(x) for x in body)
                    if isinstance(body, list) else str(body or ""))
            emit(fmt_ref(lineno), f"attach:{a.type}",
                 f"{_tok(text)}~tok" if text else "",
                 ".attachment.content" if text else "",
                 f'"{_preview(text)}"' if text else "")

        elif isinstance(rec, SystemRecord):
            if rec.subtype == "compact_boundary":
                continue  # the ⟐ marker line above already covers it
            content = getattr(rec, "content", "") or ""
            emit(fmt_ref(lineno), f"system:{rec.subtype}",
                 f"{_tok(content)}~tok" if content else "",
                 ".content" if content else "",
                 f'"{_preview(content)}"' if content else "")
        # Progress / snapshots / queue ops / last-prompt / permission-mode:
        # bookkeeping — intentionally no skeleton lines.

    tail = len(records)
    if tail in rewind_markers:
        lines.append(rewind_line(rewind_markers[tail]))

    return "\n".join(lines)
```

**3b.** In `src/claude_config/cc_pretty/main.py`, replace the whole `add_shared_args` function with the axis-grouped version:

```python
def add_shared_args(parser: argparse.ArgumentParser, *, default_tool_max: int = 200) -> None:
    """Attach the cc-pretty / opencode-pretty shared options to ``parser``.

    Flags are organized in four orthogonal axes — a command picks at most one
    value per axis, so any combination's meaning is predictable:

      SELECTION    which records participate
      DENSITY      view mode (mutually exclusive)
      BODY-DETAIL  per-block detail within the default full-render density
      OUTPUT       where/how the render is emitted

    Front-ends still own the positional argument(s) that point at the data
    source (a JSONL path for cc-pretty, a session ID for opencode-pretty).
    ``default_tool_max`` lets front-ends pick a different default truncation
    budget without redefining the argument.
    """
    sel = parser.add_argument_group("SELECTION (which records)")
    sel.add_argument(
        "--compact-all",
        action="store_true",
        help="Show all compaction legs (default: only last leg)",
    )
    sel.add_argument(
        "--compact-leg",
        type=int,
        default=None,
        metavar="N",
        help="Show only compaction leg N (1-indexed; 0 = pre-compact section)",
    )
    sel.add_argument(
        "--show-rewound",
        action="store_true",
        help="Show rewound conversation branches (hidden by default)",
    )
    sel.add_argument(
        "--show-all",
        action="store_true",
        help="Show all records including non-model content "
        "(hooks, progress, system metadata)",
    )
    sel.add_argument(
        "--no-progress",
        action="store_true",
        help="Hide progress records when --show-all is used",
    )

    den = parser.add_argument_group("DENSITY (view mode — pick at most one)")
    denx = den.add_mutually_exclusive_group()
    denx.add_argument(
        "--chat-only",
        action="store_true",
        help="Show only user prompts and assistant messages — drop tool "
        "calls, tool results, system records, and attachments. Assistant "
        "turns that contain only tool_use blocks are skipped entirely.",
    )
    denx.add_argument(
        "--skeleton",
        action="store_true",
        help="One line per content block: ref, type, ~tok size, jq leaf, "
        "preview — a block map for targeted jq/sed extraction. Hidden "
        "regions appear as marker lines with their reveal flags.",
    )

    body = parser.add_argument_group(
        "BODY-DETAIL (only within the default full-render density)")
    body.add_argument(
        "--tool-max",
        type=int,
        default=default_tool_max,
        help=f"Max chars for tool output (default: {default_tool_max}). "
        "Tool input is shown in full unless --truncate-input is set.",
    )
    body.add_argument(
        "--truncate-input",
        action="store_true",
        help="Also truncate tool input to --tool-max chars (full by default)",
    )
    body.add_argument(
        "--no-thinking",
        action="store_true",
        help="Collapse thinking blocks to single-line summary",
    )
    body.add_argument(
        "--show-usage",
        action="store_true",
        help="Show per-turn usage block "
        "(in/out/cached/cache_create tokens). Hidden by default — opt in "
        "when debugging cache-hit rates or cost regressions.",
    )

    out = parser.add_argument_group("OUTPUT")
    color_group = out.add_mutually_exclusive_group()
    color_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors (default: auto-detect — colors on for "
        "TTYs, off when piped or when NO_COLOR is set)",
    )
    color_group.add_argument(
        "--color",
        action="store_true",
        help="Force ANSI colors even when stdout is not a TTY (e.g. piping "
        "to `less -R`)",
    )
    out.add_argument(
        "--agent",
        action="store_true",
        help="Agent-friendly output: if small enough, print directly; "
        "otherwise write chunk files to /tmp and print paths. "
        "Implies --no-color.",
    )
    out.add_argument(
        "--validate-only",
        action="store_true",
        help="Parse all records through pydantic schema without rendering; "
        "exit 1 on errors (cc-pretty only — opencode-pretty validates eagerly).",
    )
```

(Spec deviation: the density conflict exits 2 via argparse's mutually-exclusive group — same convention as the existing `--color`/`--no-color` pair — instead of a custom exit 1.)

**3c.** In `run_pipeline`, add the skeleton branch right after the rewind-marker computation, before the `# ── Session header` comment, and indent the existing header + render loop + tail-flush + final `print(separator())` under `else:`:

```python
    # ── Skeleton density short-circuits the full render ────────────────
    if args.skeleton:
        record_visible = (lambda _rec: True) if args.show_all else is_model_visible
        print(render_skeleton(
            records,
            log_path=inp.log_path,
            compact_hidden=compact_hidden,
            hidden_for_rewind=hidden_for_rewind,
            compaction_markers=compaction_markers,
            rewind_markers=rewind_markers,
            record_visible=record_visible,
        ))
    else:
        # ── Session header (first visible record) ───────────────────────
        # ... existing header block, render loop, tail rewind flush, and
        # final print(separator()) — all indented one level under else ...
```

Update the render.py import in main.py:

```python
from claude_config.cc_pretty.render import C, Renderer, fmt_ts, render_skeleton, separator
```

**3d.** Update the module docstring of `src/claude_config/cc_pretty/main.py` — replace the usage paragraph:

```python
"""Pretty-print a Claude Code JSONL session log to stdout.

Usage: cc-pretty <session.jsonl> [--skeleton | --chat-only]
                                 [--tool-max N] [--truncate-input]
                                 [--color | --no-color] [--no-thinking]
                                 [--show-rewound] [--show-all]
                                 [--compact-all] [--compact-leg N]
                                 [--agent]

Flags form four orthogonal axes (see --help): SELECTION (which records),
DENSITY (full render / --skeleton / --chat-only), BODY-DETAIL (within full
render), OUTPUT. Every rendered block carries an @L<n>[i] ref; the legend
at the top documents how to recover the raw string behind any ref.

Color output is auto-detected: on when stdout is a TTY, off when piped or
when NO_COLOR is set (https://no-color.org). --color forces it on (e.g.
piping to `less -R`), --no-color forces it off.

By default, only the last leg (after the last compaction boundary) is shown.
Rewound conversation branches are collapsed to a single marker, and records
not presented to the model (raw hook execution, progress, system metadata,
permission-mode state) are hidden.  Model-visible attachment records — most
importantly hook_additional_context, which carries the <system-reminder> text
emitted by SessionStart / PostToolUse / etc. hooks — are shown by default.
Use --show-all to surface the bookkeeping records as well.

This module also exposes :func:`add_shared_args` and :func:`run_pipeline` so
other front-ends (e.g. opencode-pretty) can wire the same CLI surface and
rendering loop on top of a different data source.
"""
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_opencode_pretty.py tests/test_cc_pretty_render.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/cc_pretty/main.py src/claude_config/cc_pretty/render.py tests/test_opencode_pretty.py
git commit -m "cc-pretty+opencode-pretty: --skeleton density mode, axis-grouped --help"
```

---
### Task 6: opencode `--from-file` recipes + `--agent` guidance line

With `--from-file`, hints/legend must reference the saved export (no re-export). The `--agent` chunk listing drops "Read all N files in parallel" and points at the skeleton protocol.

**Files:**
- Modify: `src/claude_config/opencode_pretty/main.py` (log_path construction)
- Modify: `src/claude_config/cc_pretty/main.py` (`emit_agent_output`)
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_opencode_pretty.py`:

```python
# ─── --from-file recipes / --agent guidance ─────────────────────────────────


def test_cli_from_file_legend_references_file_not_export(tmp_path) -> None:
    export_file = tmp_path / "export.json"
    export_file.write_text(json.dumps(sample_export()))
    proc = _run_cli(export_file)
    assert proc.returncode == 0
    assert "opencode export ses_" not in proc.stdout
    assert "jq -r" in proc.stdout and str(export_file) in proc.stdout


def test_emit_agent_output_chunk_listing_drops_parallel_reads(
    capsys, monkeypatch,
) -> None:
    from claude_config.cc_pretty.main import emit_agent_output
    monkeypatch.setenv("BASH_MAX_OUTPUT_LENGTH", "100")  # limit becomes 80
    emit_agent_output("y" * 500, "pytest-agent")
    out = capsys.readouterr().out
    assert "Read all" not in out
    assert "--skeleton" in out
    assert "/tmp/pytest-agent-1.txt" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_opencode_pretty.py -q -k "from_file_legend or agent_output"`
Expected: FAIL — legend still prints the export recipe under `--from-file`; chunk listing still says "Read all".

- [ ] **Step 3: Implement**

**3a.** In `src/claude_config/opencode_pretty/main.py`, replace the log_path construction:

```python
    session_id = meta.get("session_id") or args.session_id
    if args.from_file:
        # Hints/legend reference the saved export directly — no re-export.
        log_path = f"opencode-file://{args.from_file}"
    else:
        log_path = f"opencode://{session_id}"
```

**3b.** In `src/claude_config/cc_pretty/main.py`, replace the tail of `emit_agent_output`:

```python
    n = len(infos)
    print(f"Rendered {len(output):,} chars, {len(lines)} lines across {n} files.")
    print("Chunk files (read selectively):")
    for path, chars, start, end in infos:
        print(f"  {path} ({chars:,} chars, lines {start}-{end})")
    print("Prefer --skeleton + targeted jq/sed extraction per ref over "
          "reading every chunk — see skills/session-analysis.")
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_opencode_pretty.py tests/test_cc_pretty_render.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/claude_config/opencode_pretty/main.py src/claude_config/cc_pretty/main.py tests/test_opencode_pretty.py
git commit -m "opencode-pretty: --from-file hints reference the file; --agent drops parallel-reads guidance"
```

---

### Task 7: Smoke-verify both tools on real logs

No automated test — manual verification with exact commands. Any mismatch = fix before proceeding.

- [ ] **Step 1: Full suite green**

```bash
cd /root/claude-config-work3 && uv run pytest tests/ -q
```
Expected: all PASS.

- [ ] **Step 2: opencode skeleton + ref resolution on a real session**

```bash
cd /root/claude-config-work3
CLAUDE_CONFIG_ROOT=/root/claude-config-work3 ./agent-tools/target/release/agent-tools opencode-pretty ses_00b8f9b93ffevaivD0NyDMnuau --skeleton | head -30
```
Expected: `# skeleton:` header, `# sizes:`, two `# refs`/`# recover` lines, then block lines with refs/leafs/previews.

Then verify one ref end-to-end — pick any `tool:` line from the output (say `@L4[3] tool:read`) and confirm the jq path resolves to the same tool:

```bash
opencode export ses_00b8f9b93ffevaivD0NyDMnuau > /tmp/oc-skel-check.json
jq -r '.messages[3].parts[3].tool' /tmp/oc-skel-check.json
jq -r '.messages[3].parts[3].state.input' /tmp/oc-skel-check.json | head -3
```
Expected: tool name matches the skeleton line; input prints. (Adjust indices to an actual tool line from the skeleton output.)

- [ ] **Step 3: cc-pretty skeleton + ref resolution on a real JSONL**

```bash
CC_JSONL=$(ls -t /root/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
echo "$CC_JSONL"
CLAUDE_CONFIG_ROOT=/root/claude-config-work3 ./agent-tools/target/release/agent-tools cc-pretty "$CC_JSONL" --skeleton --compact-all --show-rewound | head -30
```
(If no CC jsonl exists, write a 3-line fixture to /tmp/cc-fixture.jsonl: a user record, an assistant record with a thinking + text + tool_use block, a user record with a tool_result block.)

Then verify one block ref:

```bash
# pick a tool line from the skeleton, e.g. @L57[2] tool:Bash:
sed -n '57p' "$CC_JSONL" | jq -r '.message.content[2].name'   # prints the tool name
```
Expected: name matches the skeleton line.

- [ ] **Step 4: Full render smoke (humans still use it)**

```bash
CLAUDE_CONFIG_ROOT=/root/claude-config-work3 ./agent-tools/target/release/agent-tools opencode-pretty ses_00b8f9b93ffevaivD0NyDMnuau --tool-max 300 | head -40
```
Expected: two-line legend at top; thinking headers carry refs; `── text @L… ──` markers; truncated blocks end with `…full: opencode export … jq -r …` lines; user headers carry `@L…`.

- [ ] **Step 5: Commit (only if fixes were needed)**

```bash
git add -A src tests
git commit -m "fix: smoke-test corrections for skeleton/refs"
```

---

### Task 8: Create `skills/session-analysis/`, delete old skill dirs

Assemble the merged skill. New prose is given verbatim below; carried sections are moved from the two existing files with the noted edits.

**Files:**
- Create: `skills/session-analysis/SKILL.md`
- Create: `skills/session-analysis/CLAUDE.md`
- Create: `skills/session-analysis/README.md`
- Delete: `skills/session-timeline/` (SKILL.md, CLAUDE.md)
- Delete: `skills/diagnose-session/` (SKILL.md, CLAUDE.md, README.md)

- [ ] **Step 1: Write `skills/session-analysis/SKILL.md`**

Frontmatter:

```markdown
---
name: session-analysis
description: use only if invoked by user or workflow
---
```

Section order and sources (carry = move text over, applying the noted edits; NEW = verbatim text below):

1. `# Session Analysis` title + NEW intro paragraph:

```markdown
Analyze one or more logged agent sessions — opencode exports or Claude Code
JSONL — through a shared skeleton-first reading protocol. Three modes:
**evidence** (a focus-directed raw-evidence artifact, facts only),
**question** (evidence artifact + a synthesized answer in the response), and
**diagnose** (a findings report surfacing items the agent did not
self-report).
```

2. `## Invocation` — CARRY from session-timeline/SKILL.md "Invocation", replacing "a session-timeline run" → "a session-analysis run".

3. `## Modes` — CARRY the intro paragraph + "### question mode" + "### evidence mode" unchanged. Append NEW subsection:

```markdown
### diagnose mode

- Input: log path (`*.jsonl`) or opencode session id.
- Produces: a findings report (see "Mode: diagnose" below), returned in the
  response prose.
- Must be named explicitly (`mode: diagnose` or "diagnose this session") —
  the no-mode default for direct invocation stays question mode.
```

4. `## For parents dispatching this skill` — CARRY from session-timeline, replacing "read this SKILL.md" reference target mentions of the skill name as needed (no path change — same filename).

5. NEW `## Reading protocol` — verbatim:

````markdown
## Reading protocol

All modes read the log the same way. Never render a full high-precision
pretty file as reading substrate.

1. **Skeleton.** Run the skeleton command and read it fully:
   - opencode: `agent-tools opencode-pretty <session-id> --skeleton`
     (add `--from-file <export.json>` when a saved export already exists —
     hints then reference that file)
   - Claude Code: `agent-tools cc-pretty <file.jsonl> --skeleton`

   One line per content block: `@L<n>[i]` ref, type, approx size
   (`~tok` ≈ chars/4), the jq leaf, and a short preview.
2. **Hidden regions.** `⟐ compacted` / `⟲ rewind` skeleton lines mark
   content the default selection hides; each carries its `reveal:` flag. If
   the focus may touch hidden content, re-run the skeleton with that flag —
   refs stay identical. Harness asymmetry: a cc JSONL contains every line
   (sed/jq bypass all hiding); an opencode export contains all compaction
   legs but only uncleaned rewind tails (opencode deletes abandoned tails on
   the next prompt).
3. **Plan batches.** Group adjacent blocks totaling ≤ ~10k tokens (size
   column). Key blocks may be read out of order first (e.g. a
   known-decisive reasoning block).
4. **Extract one batch with one command** naming exactly those refs:
   - opencode: `opencode export <id> > /tmp/oc-<id>.json` once, then
     `jq '.messages[9:25]' /tmp/oc-<id>.json` for a message range (0-based
     slice: `.messages[a:b]` covers refs `@L(a+1)`..`@Lb`), or
     `jq -r '.messages[<n-1>].parts[<i>]<leaf>' /tmp/oc-<id>.json` for one
     block. Never pipe `opencode export` into jq directly — stdout truncates
     at ~64KB on a pipe; redirect to a file first.
   - cc: `sed -n '10,25p' <file>.jsonl` for a line range, or
     `sed -n '<n>p' <file>.jsonl | jq -r '.message.content[<i>]<leaf>'` for
     one block (user inputs: `jq -r '.message.content'`; attachments:
     `jq -r '.attachment.content'`).
5. **Think before fetching more.** Assess the batch's relevance to the
   focus/question/findings, then plan the next batch.
6. **Coverage sweep.** End with all blocks read. Required: every reasoning
   block, every text block, every tool input. Tool OUTPUT is optional —
   except when a later reasoning/text block references it: then go back and
   read/explore/understand the referenced part.
````

6. `## Harness notes` — CARRY from session-timeline's "Harness-specific rendering" section with these edits:
   - Drop the "Two-tool workflow" paragraph and the old "**Skeleton**" command block (superseded by the Reading protocol).
   - Keep: the `opencode export` stderr/stdout pitfall note, the reference-convention paragraph (now guaranteed by the tools), the exported JSON schema, the common jq queries, DB location, channels-within-a-message, F62, compound bash, metadata-only reads.
   - Rename the section heading to `## Harness notes`; keep `### opencode`.
   - Append NEW subsection:

```markdown
### claude-code

One JSONL line per record. `@L<n>[i]` = line `n`, `.message.content[i]`.
Tool calls sit on assistant lines (`.message.content[i].input`); results sit
on the following user line (`.message.content[i].content`). Thinking blocks:
`.message.content[i].thinking`. User string input: `.message.content` (no
index). Hook/attachment records: `.attachment.content`. Rewound lines and
pre-compaction legs stay in the file — sed/jq extraction bypasses all
pretty-side hiding.
```

7. `## Mode: evidence` — CARRY session-timeline's "Invariants", "Extractor judgment", "Provenance requirements", "Anti-patterns", "Output location and naming" sections (as subsections). One edit: in "Extractor judgment", replace the "Workflow." bullet's "Iterative skeleton → drill-in scales well; all-at-once flooding context does not." with "Follow the Reading protocol above."

8. `## Mode: diagnose` — CARRY diagnose-session's content as subsections with these edits:
   - Intro sentence (Post-hoc analysis… self-reporting) as the lead-in.
   - Step 1 ("Render and read the log") is REPLACED by a pointer: "Read the log via the Reading protocol above."
   - Steps 2-5 carried as subsections ("Construct the timeline", "Scan for findings", "Check existing Required notes", "Produce the report").
   - Rendered-marker wording must be generalized to raw extraction (the protocol reads raw JSON, not pretty output):
     - workflow-dropout row: "Detection now leans on the timeline (above) and the rendered NEXT-STEP window (cc-pretty preserves a ~200-char window around `NEXT STEP` in mid-text)" → "Detection leans on the timeline (above) and on `NEXT STEP` directives visible in extracted skill-script text".
     - "scan `╭─ thinking ─` sections" → "scan reasoning/thinking blocks".
     - Rules rule 1 "Read thinking blocks." keep; the `╭─ thinking ─` marker phrasing → "reasoning/thinking blocks".
   - Rules: carry all EXCEPT rule 4 ("Do NOT use subagents…") — DELETE it. Renumber.

- [ ] **Step 2: Write `skills/session-analysis/CLAUDE.md`**

```markdown
# session-analysis/

Session log analysis over opencode exports and Claude Code JSONL:
skeleton-first reading protocol with evidence, question, and diagnose modes.

## Files

| File        | What                                            | When to read                   |
| ----------- | ----------------------------------------------- | ------------------------------ |
| `SKILL.md`  | Skill definition, reading protocol, modes       | Using or invoking this skill   |
| `README.md` | Design rationale and limitations                | Understanding the approach     |
```

- [ ] **Step 3: Write `skills/session-analysis/README.md`**

CARRY `skills/diagnose-session/README.md` (design rationale, detection tiers, limitations, relationship to self-reporting) with these edits:
- Title: `# session-analysis`.
- Add after the intro: "This skill merges the former `diagnose-session` (findings reports) and `session-timeline` (evidence artifacts) skills into one skeleton-first workflow."
- Limitations: replace "Pick the matching renderer … per Step 1 of the SKILL." with "Both harnesses are read via the shared skeleton-first reading protocol (see SKILL.md)."
- Limitations: drop "Token-limited: very long conversations may need chunked reading" (the protocol IS the chunking strategy).

- [ ] **Step 4: Delete the old skill dirs**

```bash
git rm -r skills/session-timeline skills/diagnose-session
```

- [ ] **Step 5: Commit**

```bash
git add skills/session-analysis
git commit -m "skills: merge session-timeline + diagnose-session into session-analysis"
```

---

### Task 9: Agent wrapper rename + reference updates

**Files:**
- Rename: `agents/session-timeline.md` → `agents/session-analysis.md` (edit content)
- Modify: `skills/CLAUDE.md` (table rows)
- Modify: `skills/diagnose-workflow/SKILL.md` ("Relationship to diagnose-session")
- Modify: `skills/diagnose-workflow/README.md` (line 46)
- Modify: `.claude/skills/prompt-tests/SKILL.md` (grader brief)
- Modify: `CLAUDE.md` (repo root — agent-tools flag lists)
- Modify: `docs/opencode-system-prompt/build-self-reported.md` (line ~220)
- Modify: `notes/compliance-check-failure-mode.md` (two links)

- [ ] **Step 1: Rename + rewrite the agent wrapper**

```bash
git mv agents/session-timeline.md agents/session-analysis.md
```

Replace its full content with:

```markdown
---
name: session-analysis
description: Evidence extraction and session-log analysis over opencode sessions and Claude Code JSONL logs. Use when you need raw factual evidence about one or more sessions for later analysis. Always operates in evidence mode when dispatched by a parent. IMPORTANT: before dispatching this agent, read skills/session-analysis/SKILL.md so you know what the artifact contains and how to phrase the focus.
tools: Read, Bash, Grep, Glob, Write
---

You extract factual evidence from agent session logs into a compressed
artifact. You are the writer of the evidence layer. Downstream readers
(including the parent that dispatched you) draw conclusions from what you
record — you do not draw them.

## Workflow

Invoke the `session-analysis` skill via the Skill tool and follow it
literally.

## Mode

When dispatched by a parent, operate in **evidence mode** — always. The
parent's brief supplies:

- session ID(s) or log path(s)
- a description of what's important (focus, question to be answered later, or
  evaluation criterion)

If the brief lacks a focus or the session ID(s), ask the parent before
starting.

## Response

Return:

- `evidence_path`: absolute path to the artifact you wrote
- One paragraph summarizing what the artifact contains

Do not inline the artifact body — the parent reads it from the path.
```

- [ ] **Step 2: `skills/CLAUDE.md` table**

Replace the two rows:

```markdown
| `diagnose-session/`   | Post-hoc conversation log analysis        | Surfacing unreported items from session logs |
| `session-timeline/`   | Focus-directed extraction of opencode session content into raw evidence artifacts | Building the evidence layer for interpretive rounds; separates "what's in the log" from "what it means" |
```

with:

```markdown
| `session-analysis/`   | Session log analysis: skeleton-first reading protocol; evidence artifacts, question answers, diagnose reports | Analyzing agent session logs (opencode exports or Claude Code JSONL) |
```

- [ ] **Step 3: `skills/diagnose-workflow/SKILL.md`**

Retitle `## Relationship to diagnose-session` → `## Relationship to session-analysis`. In the table, replace every `diagnose-session` cell mention with `session-analysis` (diagnose mode). Replace the final two lines:

```markdown
For comprehensive diagnosis, use both:
1. `/diagnose-workflow` first — get the structural picture
2. `/diagnose-session` second — get content-level findings
```

with:

```markdown
For comprehensive diagnosis, use both:
1. `/diagnose-workflow` first — get the structural picture
2. `session-analysis` in diagnose mode second — get content-level findings
```

- [ ] **Step 4: `skills/diagnose-workflow/README.md`**

Line 46: `Use `diagnose-session` for content-level analysis.` → `Use `session-analysis` (diagnose mode) for content-level analysis.`

- [ ] **Step 5: `.claude/skills/prompt-tests/SKILL.md` grader brief**

Replace the brief's first two sentences (the "Read the session log with `agent-tools cc-pretty <FILE> --agent` … read every chunk file it lists." part) with:

```markdown
   > Read the session log with the session-analysis skill's reading
   > protocol: `agent-tools cc-pretty <FILE> --skeleton` (Claude Code JSONL)
   > or `agent-tools opencode-pretty <session> --skeleton` (opencode), then
   > extract batches per the protocol, **including all thinking/reasoning
   > blocks**. Run the `session-analysis` skill in **diagnose mode** over
   > the log. First check for
```

Leave "cheating/contamination using the rules in this skill…" and everything after unchanged, except:
- "**Full diagnose-session report** inlined." → "**Full diagnose report** inlined."
- "Outstanding problematic behavior in the diagnose-session report" → "…in the diagnose report".

- [ ] **Step 6: Repo root `CLAUDE.md`**

In the `agent-tools/` section, both CLI-surface descriptions: add `--skeleton` to the mirrored flag list (cc-pretty entry and the opencode-pretty entry's "Mirrors cc-pretty's CLI surface (`--tool-max`, …)" list).

- [ ] **Step 7: `docs/opencode-system-prompt/build-self-reported.md`**

Around line 220 there is a `diagnose-session` mention; update it to `session-analysis` (diagnose mode), preserving surrounding prose.

- [ ] **Step 8: `notes/compliance-check-failure-mode.md` links**

Two links target `../skills/session-timeline/SKILL.md` (lines ~177 and ~355). Repoint both to `../skills/session-analysis/SKILL.md`, label `[session-analysis]` with a parenthetical "(formerly `session-timeline`)". Prose mentions of the historical skill name elsewhere in notes/ stay untouched.

- [ ] **Step 9: Verify no dangling references**

```bash
cd /root/claude-config-work3
grep -rn "diagnose-session\|session-timeline" --include="*.md" skills/ agents/ .claude/ CLAUDE.md docs/opencode-system-prompt/ | grep -v "formerly"
```
Expected: no output except the historical-name note inside `skills/session-analysis/README.md` (which intentionally names both predecessor skills).

- [ ] **Step 10: Commit**

```bash
git add agents/ skills/ .claude/skills/prompt-tests/ CLAUDE.md docs/opencode-system-prompt/ notes/compliance-check-failure-mode.md
git commit -m "session-analysis: rename agent wrapper, update all references"
```

---

### Task 10: Reading-protocol smoke test + final verification

Verify the merged skill's documented commands actually work end-to-end (technique-skill application test), then run everything.

- [ ] **Step 1: Skeleton → batch extraction works as documented (opencode)**

```bash
cd /root/claude-config-work3
CLAUDE_CONFIG_ROOT=/root/claude-config-work3 ./agent-tools/target/release/agent-tools opencode-pretty ses_00b8f9b93ffevaivD0NyDMnuau --skeleton > /tmp/skel-check.txt
head -6 /tmp/skel-check.txt
opencode export ses_00b8f9b93ffevaivD0NyDMnuau > /tmp/oc-proto.json
jq '.messages[0:3] | length' /tmp/oc-proto.json        # prints 3 (slice covers @L1..@L3)
# pick one reasoning ref from /tmp/skel-check.txt and extract its direct string:
jq -r '.messages[1].parts[1].text' /tmp/oc-proto.json | head -3
```
Expected: slice length 3; the reasoning text matches the skeleton preview at that ref.

- [ ] **Step 2: Skeleton → batch extraction works as documented (cc)**

```bash
CC_JSONL=$(ls -t /root/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
CLAUDE_CONFIG_ROOT=/root/claude-config-work3 ./agent-tools/target/release/agent-tools cc-pretty "$CC_JSONL" --skeleton --compact-all > /tmp/skel-cc.txt
head -6 /tmp/skel-cc.txt
sed -n '1,3p' "$CC_JSONL" | jq -r '.type'
# pick one block ref from /tmp/skel-cc.txt and extract its direct string per the legend
```
Expected: refs resolve to the named content. (If no CC jsonl exists, use the Task 7 fixture.)

- [ ] **Step 3: Reveal-flag deviation works**

From `/tmp/skel-check.txt` or `/tmp/skel-cc.txt`: if a `⟐ compacted` or `⟲ rewind` line appears, re-run the skeleton with its printed `reveal:` flag and confirm the hidden block lines appear. If the session has no hidden regions, force one: cc — pick any jsonl with a compact_boundary; opencode — the revert-state fixture in the test suite already covers it; note the result.

- [ ] **Step 4: Full test suite + repo checks**

```bash
cd /root/claude-config-work3 && uv run pytest tests/ -q && git status --short
```
Expected: all PASS; clean tree (everything committed).

- [ ] **Step 5: Final commit (if anything changed)**

```bash
git add -A && git commit -m "session-analysis: protocol smoke-test fixes"
```

---

## Self-review notes (plan author)

- Spec coverage: flags axes (T5) · skeleton format (T5) · full-render path upgrades (T1-T4, T6) · merged skill + protocol (T8) · reference updates (T9) · testing (T1-T7, T10).
- Deliberate spec deviation: `--chat-only --skeleton` conflict exits 2 via argparse (consistent with `--color`/`--no-color`), not exit 1.
- Type consistency: `_pi` / `_out_len` (Task 1) consumed by `block_ref`/`_resolve_idx` (Task 2), renderer (Task 3), skeleton (Task 5). `prev_start` (Task 4) consumed by Tasks 4+5. `record_visible` predicate injected from `run_pipeline` (Task 5) so `is_model_visible` stays in main.py with no circular import.
- Known accepted limitation: opencode multi-text-part user messages ref the first text part only (conversion flattens; documented in code).
