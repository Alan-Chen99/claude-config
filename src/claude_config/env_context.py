#!/usr/bin/env python3
"""Print the '# Environment' block (cwd, git, platform, shell, OS).

When cc runs with --system-prompt-file, it stops emitting the default
'# Environment' block. Inject this module's output via a SessionStart hook
returning {"hookSpecificOutput": {"hookEventName": "SessionStart",
"additionalContext": <stdout>}} so cc still sees the block while keeping
the system prompt itself static and fully cacheable.

The output matches cc's no-model env variant (decompiled v2.1.143,
function Yp5 in src/globals/13.js), without model-name or knowledge-cutoff
lines.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys


def detect_shell() -> str:
    shell = os.environ.get("SHELL", "unknown")
    if "zsh" in shell:
        return "zsh"
    if "bash" in shell:
        return "bash"
    return shell


def is_git_repo() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def uname_sr() -> str:
    # Mirrors cc's os.type() + ' ' + os.release() (uname -sr on POSIX).
    return f"{platform.system()} {platform.release()}"


def build_env_section() -> str:
    items = [
        f"Primary working directory: {os.getcwd()}",
        f"Is a git repository: {str(is_git_repo()).lower()}",
        f"Platform: {sys.platform}",
        f"Shell: {detect_shell()}",
        f"OS Version: {uname_sr()}",
    ]
    bullets = "\n".join(f" - {item}" for item in items)
    header = "# Environment\nYou have been invoked in the following environment: "
    return f"{header}\n{bullets}"


def main() -> int:
    print(build_env_section())
    return 0


if __name__ == "__main__":
    sys.exit(main())
