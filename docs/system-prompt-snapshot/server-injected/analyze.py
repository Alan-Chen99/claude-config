"""Split each recitation into: what precedes the operator text, the operator text (fidelity check), the tail."""

import difflib
import json
import sys
from pathlib import Path

ns = {}
exec(Path(__file__).with_name("probe.py").read_text().split("TOOLS = {")[0], ns)
OPERATOR = ns["OPERATOR"]
FIRST, LAST = OPERATOR.split("\n")[0], OPERATOR.split("\n")[-1]

for f in sys.argv[1:]:
    rec = json.loads(Path(f).read_text())
    resp = rec["response"]
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    name = Path(f).stem
    status = f"{name}: stop={resp.get('stop_reason')} blocks={[b.get('type') for b in resp.get('content', [])]}"
    if "=====BEGIN=====" not in text:
        print(status, "NO BEGIN MARKER; first 300 chars:", repr(text[:300]))
        continue
    body = text.split("=====BEGIN=====\n", 1)[1]
    ended = "\n=====END=====" in body
    body = body.split("\n=====END=====", 1)[0]
    i = body.find(FIRST)
    j = body.find(LAST, i)
    if i < 0 or j < 0:
        print(status, f"operator text not found (first@{i}, last@{j})")
        continue
    pre, op, tail = body[:i], body[i : j + len(LAST)], body[j + len(LAST) :]
    exact = op == OPERATOR
    print(status, f"ended={ended} pre={pre!r} operator_exact={exact} tail_chars={len(tail)}")
    if not exact:
        sm = difflib.SequenceMatcher(a=OPERATOR, b=op, autojunk=False)
        for tag, a0, a1, b0, b1 in sm.get_opcodes():
            if tag != "equal":
                print(f"    {tag}: sent {OPERATOR[a0:a1]!r} -> recited {op[b0:b1]!r}  (at sent char {a0})")
    Path(f).with_suffix(".tail.txt").write_text(tail)
