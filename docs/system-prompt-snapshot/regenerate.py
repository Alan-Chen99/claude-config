#!/usr/bin/env python3
"""Regenerate system prompt snapshots by running capture.py for each variant.

Output: <model-id>/<variant>/{request.json, summary.json, prompt.md, tools/<Name>.md}

`request.json` is the artifact of record. `prompt.md` and `tools/` are rendered
from it by `render_capture.py`, which exists so that the diff between two
releases can be read -- see that module for why the split falls where it does.

The directory is named for the model id the captured request actually carried,
minus its `claude-` prefix, not for the alias passed to `--model`. Aliases are
repointed as models ship -- `opus` meant claude-opus-4-6 in the 2.1.143 capture
and claude-opus-5 in this one -- so an alias-named directory silently changes
meaning between captures while its path stays put.

Which system prompt a capture receives follows from the model's registry entry.
2.1.269 serves the compressed `# Harness` prompt to every model whose entry
declares the `lean_prompt` capability -- claude-opus-5, claude-opus-4-8,
claude-fable-5, claude-fable-5-1, claude-mythos-5-1 -- and the older
multi-section one to everything else, including every sonnet, every haiku and
claude-opus-4-7. The gate is `Ij()` (chunk-tnzzwz8r.js:6593), consumed as `d` in
`ow()` (chunk-dbb93264.js:69199), which picks `ORo()` over the multi-section
builders. The same switch shortens every tool description, via `$A()`.
Capturing both prompts therefore requires two model ids, not a flag.

Usage:
    ./regenerate.py                            # all variants, default model (sonnet)
    ./regenerate.py default                    # just one variant
    ./regenerate.py custom-output-style        # just one (prefix match)
    ./regenerate.py --model claude-opus-4-7    # different model
    ./regenerate.py --list                     # show available variants
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Token counting must bypass any inherited MITM proxy from the parent shell.
# capture.py is invoked as a subprocess; we strip the proxy env so it inherits
# clean and re-sets HTTPS_PROXY only for the spawned claude child.
for _k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
    os.environ.pop(_k, None)

import anthropic
from claude_config.config import load as _load_env

import render_capture

_load_env()

SCRIPT_DIR = Path(__file__).resolve().parent
CAPTURE = SCRIPT_DIR / "capture.py"

CUSTOM_PROMPT = "You are a custom assistant."

# Each variant: (claude_args, capture_flags)
# claude_args: flags passed to claude CLI
# capture_flags: flags consumed by capture.py (--capture-output-style, etc.)
VARIANTS: dict[str, dict] = {
    # --- output style variants (no CLI flags) ---
    "default": {
        "claude_args": [],
        "capture_flags": ["--capture-output-style", "default"],
    },
    "custom-output-style": {
        "claude_args": [],
        "capture_flags": ["--capture-output-style", "Explanatory"],
    },
    # --- CLI flag variants ---
    "system-prompt": {
        "claude_args": ["--system-prompt", CUSTOM_PROMPT],
        "capture_flags": ["--capture-output-style", "default"],
    },
    "system-prompt-file": {
        "claude_args": None,  # temp file, handled specially
        "capture_flags": ["--capture-output-style", "default"],
    },
    "append": {
        "claude_args": ["--append-system-prompt", CUSTOM_PROMPT],
        "capture_flags": ["--capture-output-style", "default"],
    },
    # --- subagent capture ---
    "subagent": {
        "claude_args": [],
        "capture_flags": ["--capture-output-style", "default", "--subagent"],
    },
}


_DEFERRED_INTRO = "The following deferred tools"
_TOOL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def extract_deferred_tools(data: dict) -> list[str]:
    """Tool names listed in the deferred-tools reminder.

    The reminder shares one text block with the agent-type and skill listings,
    and sonnet wraps each in <system-reminder> tags while opus emits them bare.
    Neither delimiter is dependable, so the listing is bounded by shape: the
    names run one per line directly under the intro sentence and stop at the
    first line that is not a bare identifier.
    """
    names: list[str] = []
    for msg in data.get("messages", []):
        content = msg.get("content", [])
        # A system-role message carries its reminders as a bare string; user
        # and assistant messages carry a list of typed blocks.
        blocks = [{"text": content}] if isinstance(content, str) else content
        for block in blocks:
            lines = block.get("text", "").splitlines()
            for i, line in enumerate(lines):
                if not line.lstrip("<").startswith(_DEFERRED_INTRO):
                    continue
                section = []
                for candidate in lines[i + 1:]:
                    if not _TOOL_NAME_RE.match(candidate.strip()):
                        break
                    section.append(candidate.strip())
                if not section:
                    raise RuntimeError(
                        "Deferred-tools reminder listed no tool names; the "
                        f"format changed: {lines[i:i + 4]!r}"
                    )
                names.extend(section)
    return names


def model_dir(model_id: str) -> str:
    """Directory name for a captured model id: `claude-opus-5` -> `opus-5`."""
    return model_id[len("claude-"):] if model_id.startswith("claude-") else model_id


def run_variant(name: str, variant: dict, model: str) -> bool:
    print(f"\n{'='*60}")
    print(f"  {model} / {name}")
    print(f"{'='*60}")

    claude_args = variant["claude_args"]
    capture_flags = variant.get("capture_flags", [])
    tmp_prompt_file = None

    if claude_args is None:
        tmp_prompt_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="prompt-", delete=False
        )
        tmp_prompt_file.write(CUSTOM_PROMPT)
        tmp_prompt_file.close()
        claude_args = ["--system-prompt-file", tmp_prompt_file.name]

    try:
        result = subprocess.run(
            [
                sys.executable, str(CAPTURE),
                "--capture-model", model,
                *capture_flags,
                *claude_args,
            ],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            # capture.py budgets 130s + 90s per extra subagent for the pty
            # alone, then counts tokens per block and per tool over the main
            # request plus every subagent request — one API call each.
            timeout=600 if "--subagent" in capture_flags else 90,
        )
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT", file=sys.stderr)
        return False
    finally:
        if tmp_prompt_file:
            Path(tmp_prompt_file.name).unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(f"  {result.stderr.strip()}", file=sys.stderr)
        return False

    cap_dir = SCRIPT_DIR / "capture-output"
    request_src = cap_dir / "request.json"

    if not request_src.exists():
        print(f"  FAILED: capture-output missing", file=sys.stderr)
        return False

    data = json.loads(request_src.read_text())
    req_model_id = data.get("model")
    if not req_model_id:
        print("  FAILED: captured request names no model", file=sys.stderr)
        return False
    out_dir = SCRIPT_DIR / model_dir(req_model_id) / name
    print(f"  -> {out_dir.relative_to(SCRIPT_DIR)}/")

    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(request_src, out_dir / "request.json")
    render_capture.write_capture(data, out_dir)

    # One directory per subagent, holding the same files as the variant itself,
    # so `render_capture.py --tree` and a reader reach them the same way.
    sub_src = cap_dir / "subagents"
    n_subagents = 0
    if sub_src.exists() and sub_src.is_dir():
        sub_dst = out_dir / "subagents"
        if sub_dst.exists():
            shutil.rmtree(sub_dst)
        for req in sorted(sub_src.glob("*-request.json")):
            n = req.name.split("-")[0]
            one = sub_dst / n
            one.mkdir(parents=True)
            shutil.copy2(req, one / "request.json")
            shutil.copy2(sub_src / f"{n}-summary.json", one / "summary.json")
            render_capture.render_file(one / "request.json")
            n_subagents += 1

    # summary.json is this script's own, not capture.py's: token counts via the
    # free Anthropic count_tokens API, and the deferred-tool roster.
    sys_blocks = [s for s in data.get("system", []) if s.get("type") == "text"]
    tools = data.get("tools", [])
    req_model = req_model_id

    def _strip_cc(obj):
        if isinstance(obj, dict):
            return {k: _strip_cc(v) for k, v in obj.items() if k != "cache_control"}
        elif isinstance(obj, list):
            return [_strip_cc(x) for x in obj]
        return obj

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"])
    _base_msg = [{"role": "user", "content": "x"}]
    base_tokens = client.messages.count_tokens(
        model=req_model, messages=_base_msg
    ).input_tokens

    sys_tokens = client.messages.count_tokens(
        model=req_model, messages=_base_msg, system=_strip_cc(data.get("system", []))
    ).input_tokens - base_tokens

    tools_tokens = 0
    if tools:
        r_no_tools = client.messages.count_tokens(
            model=req_model, messages=_base_msg, system=_strip_cc(data.get("system", []))
        ).input_tokens
        r_with_tools = client.messages.count_tokens(
            model=req_model, messages=_base_msg,
            system=_strip_cc(data.get("system", [])), tools=_strip_cc(tools)
        ).input_tokens
        tools_tokens = r_with_tools - r_no_tools

    deferred = extract_deferred_tools(data)
    # Since 2.1.235 `tools` also carries a single DeferredToolPlaceholder entry
    # flagged defer_loading; it stands in for the whole deferred set rather than
    # being a tool the model can call, so it is not counted as upfront.
    upfront = [t["name"] for t in tools if not t.get("defer_loading")]
    placeholder = [t["name"] for t in tools if t.get("defer_loading")]

    summary = {
        "model": req_model,
        "system_blocks": len(sys_blocks),
        "system_tokens": sys_tokens,
        "tools_upfront": upfront,
        "tools_upfront_count": len(upfront),
        "tools_deferred_placeholder": placeholder,
        "tools_deferred": deferred,
        "tools_deferred_count": len(deferred),
        "tools_total_tokens": tools_tokens,
        "has_output_style": any("Output Style" in s.get("text", "") for s in sys_blocks),
        "has_doing_tasks": any("Doing tasks" in s.get("text", "") for s in sys_blocks),
        "subagent_count": n_subagents,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"  prompt.md         ({sys_tokens:,} system tokens)")
    print(f"  tools/            ({len(tools)} file(s))")
    print(f"  summary.json      ({len(upfront)} upfront, {len(deferred)} deferred)")
    if n_subagents:
        print(f"  subagents/        ({n_subagents} subagent capture(s))")

    if result.stderr:
        for line in result.stderr.strip().splitlines():
            print(f"  {line}")

    return True


def resolve_name(arg: str) -> str:
    if arg in VARIANTS:
        return arg
    matches = [k for k in VARIANTS if k.startswith(arg)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Ambiguous prefix '{arg}': {matches}", file=sys.stderr)
        sys.exit(1)
    print(f"Unknown variant '{arg}'. Available: {list(VARIANTS.keys())}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    argv = sys.argv[1:]

    if "--list" in argv or "-l" in argv:
        for name in VARIANTS:
            print(f"  {name}")
        return

    model = "sonnet"
    if "--model" in argv:
        idx = argv.index("--model")
        model = argv[idx + 1]
        argv = argv[:idx] + argv[idx + 2:]

    positional = [a for a in argv if not a.startswith("-")]
    targets = [resolve_name(a) for a in positional] if positional else list(VARIANTS)

    ok, fail = 0, 0
    for name in targets:
        if run_variant(name, VARIANTS[name], model):
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed (requested model: {model})")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
