#!/usr/bin/env python3
"""Claude Code status line: reads cc's statusLine JSON on stdin, prints three rows.

Stdlib only: cc runs it with whatever `python3` its PATH finds.
"""

import json
import re
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

# cc renders every row dimmed and prefixes each row with all the escape codes
# of the rows above it, so styles here only ever change the foreground (closed
# by 39, never 0) or the intensity (22 first, since bold and faint share it,
# then back to faint): a full reset would undim the rest of the row and leak
# into the next. Labels are grey as well as dimmed because libvterm (Emacs
# vterm) has no faint attribute and shows cc's dimming as plain text.
RED, YELLOW, GREEN, GREY = 203, 220, 114, 244
ANSI = re.compile(r"\x1b\[[\d;]*m")


def fg(color, s):
    return f"\x1b[38;5;{color}m{s}\x1b[39m"


def hi(s):
    return f"\x1b[22m{s}\x1b[2m"


def emph(s):
    return f"\x1b[22;1m{s}\x1b[22;2m"


def lab(s):
    return fg(GREY, s)


def pad(s, width):
    """Pads on the right, so a label stays beside its value."""
    return s + " " * max(0, width - len(ANSI.sub("", s)))


def level(pct):
    """A usage percentage, yellow from 50, red from 80."""
    s = f"{pct}%"
    return fg(RED, s) if pct >= 80 else fg(YELLOW, s) if pct >= 50 else s


SEP = f" {lab('│')} "

# cc 2.1.289's model catalog `pricing_tiers`, $/Mtok. Per-model prices rather
# than ratios: cache read is 0.05x input on opus-5-5 but 0.1x elsewhere, and a
# session mixes models.
TIERS = {
    "t2_10": dict(inp=2, out=10, w5=2.5, w1h=4, rd=0.2),
    "t3_15": dict(inp=3, out=15, w5=3.75, w1h=6, rd=0.3),
    "t5_25": dict(inp=5, out=25, w5=6.25, w1h=10, rd=0.5),
    "t15_75": dict(inp=15, out=75, w5=18.75, w1h=30, rd=1.5),
    "t10_50": dict(inp=10, out=50, w5=12.5, w1h=20, rd=1),
    "t10_50r": dict(inp=10, out=50, w5=12.5, w1h=20, rd=0.25),
    "t4_20r": dict(inp=4, out=20, w5=5, w1h=8, rd=0.2),
    "h35": dict(inp=0.8, out=4, w5=1, w1h=1.6, rd=0.08),
    "h45": dict(inp=1, out=5, w5=1.25, w1h=2, rd=0.1),
}
MODELS = {
    "claude-3-5-haiku": "h35", "claude-haiku-4-5": "h45",
    "claude-3-5-sonnet": "t3_15", "claude-3-7-sonnet": "t3_15",
    "claude-sonnet-4-0": "t3_15", "claude-sonnet-4-5": "t3_15", "claude-sonnet-4-6": "t3_15",
    "claude-sonnet-5": "t2_10", "claude-sonnet-5-5": "t2_10",
    "claude-opus-4-0": "t15_75", "claude-opus-4-1": "t15_75",
    "claude-opus-4-5": "t5_25", "claude-opus-4-6": "t5_25", "claude-opus-4-7": "t5_25",
    "claude-opus-4-8": "t5_25", "claude-opus-5": "t5_25", "claude-opus-5-5": "t4_20r",
    "claude-fable-5": "t10_50", "claude-fable-5-1": "t10_50r",
    "claude-mythos-5": "t10_50", "claude-mythos-5-1": "t10_50r",
}
# Fast mode doubles every rate on the models that offer it
FAST = {"claude-opus-4-8": 2, "claude-opus-5": 2, "claude-opus-5-5": 2}
WEB_SEARCH = 0.01
# Muted: the split is read when looked for, not at a glance
CATEGORIES = [("in", 67), ("out", 133), ("wr", 136), ("rd", 65), ("web", 102)]
# The split without `web`, so "cost split -" and "?" keep the columns after it
SPLIT_WIDTH = 32


def responses(transcript):
    """Usage of each API response in the transcript and every transcript under
    its session dir (subagents, workflows), keyed by message id: one response
    is logged once per content block, each line carrying the same usage."""
    seen = {}
    files = [transcript, *sorted(transcript.with_suffix("").rglob("*.jsonl"))]
    for f in files:
        lines = f.read_bytes().splitlines()
        for i, line in enumerate(lines):
            # Cheap filter: most lines are tool results with no usage
            if b'"usage"' not in line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # cc may be mid-append to the last line; anything else is corrupt
                if i == len(lines) - 1:
                    continue
                raise
            msg = rec.get("message")
            if rec.get("type") == "assistant" and isinstance(msg, dict) and msg.get("usage") and msg.get("id"):
                seen[msg["id"]] = (msg.get("model") or "", msg["usage"])
    return seen.values()


def cost_split(transcript):
    """Dollars per category, and the model ids missing from MODELS (priced as
    cc prices an unknown model, at tier_5_25)."""
    cost = dict.fromkeys((name for name, _ in CATEGORIES), 0.0)
    unpriced = set()
    for model, u in responses(transcript):
        cw = u.get("cache_creation_input_tokens") or 0
        w1h = min((u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0, cw)
        inp, out, rd = (u.get(k) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens"))
        if inp + out + cw + rd == 0:
            continue  # `<synthetic>` records: cc-written errors, never billed
        model = re.sub(r"-\d{8}$", "", model)
        if model not in MODELS:
            unpriced.add(model)
        p = TIERS[MODELS.get(model, "t5_25")]
        k = (1.1 if u.get("inference_geo") == "us" else 1) * (FAST.get(model, 1) if u.get("speed") == "fast" else 1) / 1e6
        cost["in"] += inp * p["inp"] * k
        cost["out"] += out * p["out"] * k
        cost["wr"] += ((cw - w1h) * p["w5"] + w1h * p["w1h"]) * k
        cost["rd"] += rd * p["rd"] * k
        cost["web"] += ((u.get("server_tool_use") or {}).get("web_search_requests") or 0) * WEB_SEARCH
    return cost, sorted(unpriced)


def render_split(cost, total):
    """The split, and the warnings for row 3. `traced` is the
    split's sum over cc's total, shown when they differ by over 1%: below 100,
    cc billed calls whose usage no transcript under the session dir records;
    above, the transcripts hold usage cc's total does not count. A `-p --resume`
    carries the earlier cost into cc's total, so a resume alone reads 100%."""
    total_split = sum(cost.values())
    if total_split == 0:
        return "cost split -", []
    shown = [(n, c) for n, c in CATEGORIES if n != "web" or cost["web"] > 0]
    legend = [pad(f"{fg(color, name)} {fg(GREY, f'{round(cost[name] / total_split * 100)}%')}", len(name) + 5)
              for name, color in shown]
    warn = []
    if total > 0 and abs(total_split / total - 1) > 0.01:
        warn.append(fg(RED, f"traced {round(total_split / total * 100)}%"))
    return " ".join(legend), warn


def tasks_row(session):
    """Open tasks. `ps` prints nothing when nothing is running, so the row
    appears only when there is something to say. A failure must be visible: an
    empty line and a broken one are otherwise identical, and silence reads as
    "nothing is running". The timeout, because every row shares one 5000 ms
    budget; 2s is far above what this costs even with a hundred captures."""
    try:
        r = subprocess.run(["agent-tools", "ps", "--format", "statusline", "--session-id", session],
                           capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return fg(RED, "▶ ?")
    return r.stdout.rstrip("\n") if r.returncode == 0 else fg(RED, "▶ ?")


def cache_row(pc):
    """Prompt cache, absent until the first API response."""
    if not pc:
        return f"{lab('cache')} -"
    warm = pc.get("warm") is True
    state = "warm" if warm else "cold"
    if pc.get("expires_at"):
        state += f" until {datetime.fromtimestamp(pc['expires_at']):%H:%M}"
    hit = pc.get("hit_ratio")
    hit = "-" if hit is None else f"{round(hit * 100)}%"
    misses = pc.get("misses") or 0
    miss = f"{misses}/{pc.get('requests', '')}"
    row = (f"{lab('cache')} {pad(hi(pc.get('ttl') or ''), 2)} {pad(fg(GREEN if warm else YELLOW, state), 16)}"
           f"{SEP}{lab('hit')} {pad(hi(hit), 4)}"
           f"{SEP}{lab('miss')} {pad(fg(YELLOW, miss) if misses else hi(miss), 7)}")
    causes = (pc.get("last_miss_cause") or {}).get("causes") or []
    return row + (f" {lab(f'(last: {','.join(causes)})')}" if causes else "")


def limits(rl):
    """Plan rate limits; cc omits a window it has no current reading for."""
    out = ""
    for label, key in (("5h", "five_hour"), ("7d", "seven_day")):
        w = (rl or {}).get(key)
        if w:
            pct = round(w["used_percentage"])
            out += f"{SEP}{lab(label)} {pad(hi(level(pct)), 4)} {datetime.fromtimestamp(w['resets_at']):%a %H:%M}"
    return out


def main():
    data = json.load(sys.stdin)
    model = (data.get("model") or {}).get("display_name") or "?"
    # Absent on models without reasoning effort, where the model name stands alone
    effort = (data.get("effort") or {}).get("level")
    if effort:
        model += f" ({effort})"
    # Absent until cc auto-names the session after its first prompt, or /rename
    name = data.get("session_name")
    ctx = data.get("context_window") or {}
    pct = round(ctx.get("used_percentage") or 0)
    # Context size is the last call's prompt plus its reply: what the next call
    # starts from, unlike the session totals cc also sends
    used_k = sum((ctx.get("current_usage") or {}).get(k) or 0 for k in
                 ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")) // 1000
    total = (data.get("cost") or {}).get("total_cost_usd") or 0
    transcript = data.get("transcript_path")

    warn = []
    if transcript and Path(transcript).is_file():
        # The status line must keep its other rows when the transcript cannot
        # be priced; the red `?` is the signal and the traceback goes to stderr
        try:
            cost, unpriced = cost_split(Path(transcript))
            split, warn = render_split(cost, total)
            if unpriced:
                warn.append(fg(RED, f"unpriced: {','.join(unpriced)}"))
        except Exception:
            traceback.print_exc()
            split = fg(RED, "cost split ?")
    else:
        split = fg(RED, "cost split ?")

    # Fixed-width fields first and the variable-length ones last, so each item
    # sits in the same column in every session; cc truncates a row at the
    # terminal's width, so the name is what a narrow window loses. Bold for what
    # is read at every glance, grey for what is read when looked for.
    row1 = (f"{lab('ctx')} {pad(emph(f'{used_k}K {level(pct)}'), 10)}{SEP}"
            f"{pad(lab(f'${total:.4f}'), 8)} {pad(split, SPLIT_WIDTH)}{SEP}{pad(emph(model), 19)}"
            + (f"{SEP}{hi(name)}" if name else ""))
    # Cost warnings lead row 3 rather than follow the split, which would push
    # the model and name off their columns whenever one appears
    row3 = SEP.join([*warn, lab(transcript) if transcript else fg(RED, "transcript ?")])
    rows = [row1, cache_row(data.get("prompt_cache")) + limits(data.get("rate_limits")), row3]
    if data.get("session_id"):
        tasks = tasks_row(data["session_id"])
        if tasks:
            rows.append(tasks)
    print("\n".join(rows))


if __name__ == "__main__":
    main()
