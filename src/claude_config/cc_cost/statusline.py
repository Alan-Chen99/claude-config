"""Claude Code status line: cc's statusLine JSON on stdin, rows on stdout.

    ctx │ $total and its split by category │ model │ session name
    cache TTL and state │ plan rate limits │ cost warnings │ session id
    main $ hit miss n/requests $ │ sub×N $ hit miss n/requests $ │ last miss: group cause
    ▶ open tasks                                          only while one runs

Three rows, subagents or not: the status line shares a terminal with the
conversation, and at 25 rows each line is 4% of it. With both groups the third
row is about 120 columns. The tasks row stays a row of its own while a wrapped
run is live: `agent-tools ps --format statusline` budgets 90 columns or more.

The main and sub groups are priced and judged from the session's transcripts
(`session.py`), so both count a miss by the same rule over the whole session.
cc's own `prompt_cache` counts the main thread of the running process alone;
its state, expiry and last-miss cause are still the ones shown.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

from claude_config.cc_cost.pricing import MODELS, base_model
from claude_config.cc_cost.session import Session, Stats, load

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
# Muted: the split is read when looked for, not at a glance. `wr` is both TTLs.
CATEGORIES = [("in", 67), ("out", 133), ("wr", 136), ("rd", 65), ("web", 102)]
# The split without `web`, so "cost split -" and "?" keep the columns after it
SPLIT_WIDTH = 43


def split_of(stats):
    c = stats.cost
    return {"in": c.get("inp", 0), "out": c.get("out", 0), "wr": c.get("w5", 0) + c.get("w1h", 0),
            "rd": c.get("rd", 0), "web": c.get("web", 0)}


def render_split(cost, total, unfinished=0.0):
    """The split as shares of the whole, and the warnings for the warnings row.

    The whole is cc's total plus the `unfinished` responses it never prices
    (interrupted, or still streaming), whose prompts were billed all the same.

    `other` is what cc billed that no transcript under the session dir records:
    its prompt suggestions and away summaries send the whole conversation to the
    main model with `skipTranscript`, and in a long interactive session that is
    a tenth of the cost or more. It never counts above zero: transcripts holding
    more than cc's total by over 1% is not something cc is known to do, so
    `traced` names it in red instead. A `-p --resume` carries the earlier cost
    into cc's total, so a resume alone is not that."""
    traced = sum(cost.values())
    if traced == 0:
        return "cost split -", []
    # cc's total is 0 only before it has counted anything; the transcripts then
    # stand for the whole
    whole = max(total + unfinished, traced)
    shares = {n: cost[n] for n, _ in CATEGORIES if n != "web" or cost["web"] > 0} | {"other": whole - traced}
    colors = dict(CATEGORIES) | {"other": GREY}
    legend = [pad(f"{fg(colors[n], n)} {fg(GREY, f'{round(c / whole * 100)}%')}", len(n) + 5)
              for n, c in shares.items()]
    warn = []
    if total > 0 and (traced - unfinished) / total > 1.01:
        warn.append(fg(RED, f"traced {round((traced - unfinished) / total * 100)}%"))
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
    """Prompt cache state, absent until the first API response."""
    if not pc:
        return f"{lab('cache')} -"
    warm = pc.get("warm") is True
    state = "warm" if warm else "cold"
    if pc.get("expires_at"):
        state += f" until {datetime.fromtimestamp(pc['expires_at']):%H:%M}"
    return f"{lab('cache')} {pad(hi(pc.get('ttl') or ''), 2)} {pad(fg(GREEN if warm else YELLOW, state), 16)}"


def group(label, stats):
    """One group's traced cost and cache record, fixed width so the next group
    starts in the same column in every session: hit ratio, requests that
    missed of all it sent, and what re-writing the lost prefix cost over
    reading it."""
    n = len(stats.misses)
    miss = f"{n}/{stats.requests}"
    hit = "-" if stats.hit_ratio is None else f"{round(stats.hit_ratio * 100)}%"
    return (f"{pad(lab(label), 6)} {pad(hi(f'${stats.total:.2f}'), 7)} {lab('hit')} {pad(hi(hit), 4)} "
            f"{lab('miss')} {pad(fg(YELLOW, miss) if n else hi(miss), 7)} "
            f"{pad(fg(YELLOW, f'${stats.premium:.2f}') if n else hi('$0.00'), 6)}")


def limits(rl):
    """Plan rate limits; cc omits a window it has no current reading for."""
    out = ""
    for label, key in (("5h", "five_hour"), ("7d", "seven_day")):
        w = (rl or {}).get(key)
        if w:
            pct = round(w["used_percentage"])
            out += f"{SEP}{lab(label)} {pad(hi(level(pct)), 4)} {datetime.fromtimestamp(w['resets_at']):%a %H:%M}"
    return out


def agents_row(session: Session, pc) -> str:
    main = Stats.of(session.agents[0].priced)
    subs = session.agents[1:]
    sub = Stats.of([p for a in subs for p in a.priced])
    fields = [group("main", main)] + ([group(f"sub×{len(subs)}", sub)] if subs else [])
    # cc's attribution of a main miss diffs the request it sent, which the
    # transcript cannot, so it names the main thread's cause whenever it has one
    cc_causes = ",".join(((pc or {}).get("last_miss_cause") or {}).get("causes") or [])
    main_cause = cc_causes or (main.last_miss.cause if main.last_miss else "")
    m, s = main.last_miss, sub.last_miss
    if s and (not m or s.response.last_ts > m.response.last_ts):
        fields.append(lab(f"last miss: sub {s.cause}"))
    elif main_cause:
        fields.append(lab(f"last miss: main {main_cause}"))
    return SEP.join(fields)


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
    pc = data.get("prompt_cache")

    warn = []
    agents = None
    if transcript and Path(transcript).is_file():
        # The status line must keep its other rows when the transcripts cannot
        # be priced; the red `?` is the signal and the traceback goes to stderr
        try:
            session = load(Path(transcript))
            priced = [p for a in session.agents for p in a.priced]
            stats = Stats.of(priced)
            split, warn = render_split(split_of(stats), total, stats.unfinished_total)
            unpriced = sorted({p.response.model for p in priced if base_model(p.response.model) not in MODELS})
            if unpriced:
                warn.append(fg(RED, f"unpriced: {','.join(unpriced)}"))
            agents = agents_row(session, pc)
        except Exception:
            traceback.print_exc()
            split = fg(RED, "cost split ?")
            agents = fg(RED, "agents ?")
    else:
        split = fg(RED, "cost split ?")

    # Fixed-width fields first and the variable-length ones last, so each item
    # sits in the same column in every session; cc truncates a row at the
    # terminal's width, so the name is what a narrow window loses. Bold for what
    # is read at every glance, grey for what is read when looked for.
    row1 = (f"{lab('ctx')} {pad(emph(f'{used_k}K {level(pct)}'), 10)}{SEP}"
            f"{pad(lab(f'${total:.4f}'), 8)} {pad(split, SPLIT_WIDTH)}{SEP}{pad(emph(model), 19)}"
            + (f"{SEP}{hi(name)}" if name else ""))
    # Cost warnings follow the fixed-width cache and limits, ahead of the
    # session id, so a narrow window loses the id first. The id, not the
    # transcript's 90-column path: every tool here resolves a session by it.
    row2 = SEP.join([cache_row(pc) + limits(data.get("rate_limits")), *warn,
                     lab(Path(transcript).stem) if transcript else fg(RED, "transcript ?")])
    rows = [row1, row2] + ([agents] if agents else [])
    if data.get("session_id"):
        tasks = tasks_row(data["session_id"])
        if tasks:
            rows.append(tasks)
    print("\n".join(rows))
