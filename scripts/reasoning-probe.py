#!/usr/bin/env python3
"""
Probe a reasoning-visible model via OpenRouter with a spec + task pair.

Purpose: opencode-served gpt-5.5 returns heading-only reasoning
summaries regardless of the `reasoning.summary` value sent
(compliance-check-failure-mode round-9 F62 — OpenAI-side override
verified by 400-error probe). Findings that depend on paragraph-level
reasoning content need a different channel. This script talks to
OpenRouter directly with `include_reasoning: true` and picks a
reasoning-visible model (default: `deepseek/deepseek-r1-0528`); the
reasoning trace is returned verbatim in the response.

The script strips YAML frontmatter from the spec before sending
(round-19 F87b: opencode's `{file:...}` template inlines raw file
content into the system prompt, so a spec with probe-context comments
in its frontmatter contaminates the run — F90 quantified the
behavioural cost on gpt-5.5/xhigh at 0→34 tool calls on v7). Strip
here so the raw-API path matches the "clean" system-prompt shape.

Tool definitions match opencode's schema so the model can nominate
tool calls at decision time; this script does NOT execute them.
Reasoning at decision time is the target.

Usage:

    scripts/reasoning-probe.py \\
      [model]                                          # default deepseek/deepseek-r1-0528
      [spec_path]                                      # default framing-ambig-authored-v8.md
      [task_path]                                      # default H17-task.md
      [out_path]                                       # default /tmp/reasoning-probe-out.json

`.env` at repo root supplies `OPENROUTER_API_KEY`.
"""

import json
import os
import sys
import urllib.request
import urllib.error


def load_env():
    """Load OPENROUTER_API_KEY (and any peers) from repo `.env`.

    Resolves relative to this script so `scripts/reasoning-probe.py` runs
    correctly from any cwd, including probe scratch dirs under `/tmp`.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(os.path.dirname(here), ".env")
    if not os.path.exists(env_path):
        # Fallback for the canonical checkout.
        env_path = "/repos/claude-config/.env"
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)


def read_file(path):
    with open(path) as f:
        return f.read()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Execute a bash command in the working directory. "
                "Use for git, ls, ps, cat, grep, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to run"},
                    "description": {"type": "string", "description": "One-line description"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read a file's contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "offset": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
                "required": ["filePath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a regex pattern in files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                    "include": {"type": "string"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "todowrite",
            "description": "Create or update a todo list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["todos"],
            },
        },
    },
]


def strip_frontmatter(spec_raw: str) -> str:
    """Remove YAML frontmatter block (between the first two `---` fences).

    Matches opencode's `agent.load()` disk-load behaviour so probes via
    `{file:...}` do not leak the block into the system prompt (F87b/F90).
    """
    if not spec_raw.startswith("---"):
        return spec_raw
    parts = spec_raw.split("---", 2)
    if len(parts) < 3:
        return spec_raw
    return parts[2].lstrip()


def probe(model, system_prompt, user_message, out_path, extra_headers=None):
    load_env()
    api_key = os.environ["OPENROUTER_API_KEY"]
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 1.0,
        "max_tokens": 8000,
        "reasoning": {"effort": "high"},
        "include_reasoning": True,
    }
    if extra_headers is None:
        extra_headers = {}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/anthropics/claude-code",
            "X-Title": "compliance-check-failure-mode research",
            **extra_headers,
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read().decode())

    with open(out_path, "w") as f:
        json.dump(resp, f, indent=2)

    msg = resp["choices"][0]["message"]
    reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
    content = msg.get("content") or ""
    tool_calls = msg.get("tool_calls") or []
    print(f"=== {model} ===")
    print(f"reasoning chars: {len(reasoning)}")
    print(f"content chars:   {len(content)}")
    print(f"tool_calls:      {len(tool_calls)}")
    for tc in tool_calls[:5]:
        fn = tc.get("function", {})
        print(f"  {fn.get('name')}({fn.get('arguments', '')[:200]})")
    print()
    print("--- reasoning ---")
    print(reasoning[:15000])
    print()
    print("--- content ---")
    print(content[:3000])


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "deepseek/deepseek-r1-0528"
    spec_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "/root/experiment-materials/framing-ambig-authored-v8.md"
    )
    task_path = (
        sys.argv[3] if len(sys.argv) > 3 else "/root/experiment-materials/H17-task.md"
    )
    out_path = sys.argv[4] if len(sys.argv) > 4 else "/tmp/reasoning-probe-out.json"

    spec_body = strip_frontmatter(read_file(spec_path))
    task = read_file(task_path).rstrip()
    probe(model, spec_body, task, out_path)
