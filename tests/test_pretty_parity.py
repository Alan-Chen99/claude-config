"""The three session-log front-ends expose one CLI surface.

`cc-pretty`, `cc-pretty-intercept` and `opencode-pretty` read three different
formats but answer the same questions about them, so a reader who learned the
flags on one uses them on the next. Drift is silent — a front-end that stops
calling `add_shared_args`, or grows a private flag that means something else
elsewhere, still passes every other test in the suite. These pin the surface
itself.

`--from-file` is the one legitimate asymmetry: cc-pretty and cc-pretty-intercept
take their file as the positional argument, and opencode-pretty's positional is
a session id, so only it needs a way to name a file instead.
"""

from __future__ import annotations

import argparse
import io
import re
from contextlib import redirect_stdout

import pytest

from claude_config.cc_pretty.main import add_shared_args
from claude_config.cc_pretty.main import main as cc_main
from claude_config.cc_pretty_intercept.main import main as intercept_main
from claude_config.opencode_pretty.main import main as opencode_main

FRONT_ENDS = {
    "cc-pretty": cc_main,
    "cc-pretty-intercept": intercept_main,
    "opencode-pretty": opencode_main,
}

# Regions only an API payload has; the other two formats hold no system prompt,
# tool schema or HTTP envelope to show.
INTERCEPT_ONLY = {"--no-system", "--no-tools", "--show-http"}
OPENCODE_ONLY = {"--from-file"}


def flags_of(main) -> set[str]:
    """Every long flag a front-end accepts, read off its own --help."""
    buf = io.StringIO()
    with redirect_stdout(buf), pytest.raises(SystemExit):
        main(["--help"])
    return set(re.findall(r"--[a-z][a-z-]+", buf.getvalue()))


def shared_flags() -> set[str]:
    parser = argparse.ArgumentParser(add_help=False)
    add_shared_args(parser)
    return {
        opt
        for action in parser._actions
        for opt in action.option_strings
        if opt.startswith("--")
    }


@pytest.mark.parametrize("name", sorted(FRONT_ENDS))
def test_every_front_end_accepts_the_whole_shared_surface(name) -> None:
    missing = shared_flags() - flags_of(FRONT_ENDS[name])
    assert not missing, f"{name} is missing {sorted(missing)}"


@pytest.mark.parametrize("name", sorted(FRONT_ENDS))
def test_no_front_end_invents_a_flag_outside_the_shared_surface(name) -> None:
    extra = flags_of(FRONT_ENDS[name]) - shared_flags() - {"--help"}
    allowed = {
        "cc-pretty": set(),
        "cc-pretty-intercept": INTERCEPT_ONLY,
        "opencode-pretty": OPENCODE_ONLY,
    }[name]
    assert extra == allowed, (
        f"{name} accepts {sorted(extra)}; the surface allows {sorted(allowed)}. "
        f"A new front-end-only flag belongs in add_shared_args unless the other "
        f"two formats genuinely have nothing for it to name."
    )


def test_the_shared_surface_is_the_documented_one() -> None:
    """A flag dropped from add_shared_args disappears from all three at once."""
    assert shared_flags() == {
        "--agent", "--chat-only", "--color", "--compact-all", "--compact-leg",
        "--no-color", "--no-progress", "--no-thinking", "--show-all",
        "--show-rewound", "--show-usage", "--skeleton", "--tool-max",
        "--truncate-input", "--validate-only",
    }


@pytest.mark.parametrize(
    "name,expected",
    # Each format's bodies have a different typical size: a cc tool result is
    # usually small, a capture holds whole system prompts, an opencode tool
    # output is a whole file read. Pinned so a change is a decision.
    [("cc-pretty", 200), ("cc-pretty-intercept", 2000), ("opencode-pretty", 4000)],
)
def test_tool_max_defaults_differ_on_purpose(name, expected) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf), pytest.raises(SystemExit):
        FRONT_ENDS[name](["--help"])
    assert f"(default: {expected})" in buf.getvalue()
