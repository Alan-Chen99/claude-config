#!/usr/bin/env bash
# Writes logs/part1.log .. part4.log into the scratch cwd: 147 lines of service-log
# noise each, with one `CLUE:` line carrying two clues of a four-house logic puzzle.
# Generated here rather than committed so the case ships 2 KB instead of 50 KB of
# noise; the seed is fixed, so every run reads the same files and the solution in
# reference-solution.md stays true.
set -euo pipefail
python3 - <<'PY'
import itertools, random
from pathlib import Path

rng = random.Random(20261012)
NAMES, PETS, DRINKS = ["Ava", "Ben", "Cal", "Dee"], ["cat", "dog", "fish", "owl"], ["tea", "milk", "juice", "soda"]

def noise(n):
    svcs = ["api", "auth", "search", "ingest", "billing", "cache"]
    lvls = ["INFO", "INFO", "INFO", "DEBUG", "WARN"]
    return [f"2026-10-0{rng.randint(1,9)}T{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z "
            f"{rng.choice(lvls)} service={rng.choice(svcs)} request_id={rng.getrandbits(48):012x} "
            f"latency_ms={rng.randint(5,999)} status={rng.choice([200,200,200,201,204,404,500])}" for _ in range(n)]

def solutions(clues):
    for names in itertools.permutations(NAMES):
        for pets in itertools.permutations(PETS):
            for drinks in itertools.permutations(DRINKS):
                w = {"name": names, "pet": pets, "drink": drinks}
                if all(c[0](w) for c in clues):
                    yield w

def pos(w, a, v):
    return w[a].index(v)

def describe(a, v):
    return {"name": v, "pet": f"the {v} owner", "drink": f"the {v} drinker"}[a]

def cap(s):
    return s[0].upper() + s[1:]

def clue_pool(sol):
    pool = []
    items = [(a, v) for a, vals in (("name", NAMES), ("pet", PETS), ("drink", DRINKS)) for v in vals]
    for (a1, v1), (a2, v2) in itertools.permutations(items, 2):
        if a1 == a2:
            continue
        p1, p2 = pos(sol, a1, v1), pos(sol, a2, v2)
        d1, d2 = describe(a1, v1), describe(a2, v2)
        if p1 == p2 and a1 < a2:
            pool.append((lambda w, a1=a1, v1=v1, a2=a2, v2=v2: pos(w, a1, v1) == pos(w, a2, v2),
                         f"{d1} is {d2}" if a1 == "name" else f"{cap(d1)} and {d2} live in the same house"))
        if p1 + 1 == p2:
            pool.append((lambda w, a1=a1, v1=v1, a2=a2, v2=v2: pos(w, a1, v1) + 1 == pos(w, a2, v2),
                         f"{cap(d1)} lives directly left of {d2}"))
        if abs(p1 - p2) == 1 and a1 < a2:
            pool.append((lambda w, a1=a1, v1=v1, a2=a2, v2=v2: abs(pos(w, a1, v1) - pos(w, a2, v2)) == 1,
                         f"{cap(d1)} lives next to {d2}"))
        if p1 != p2 and a1 < a2:
            pool.append((lambda w, a1=a1, v1=v1, a2=a2, v2=v2: pos(w, a1, v1) != pos(w, a2, v2),
                         f"{cap(d1)} does not live in the same house as {d2}"))
    for a, v in items:
        d = describe(a, v)
        if pos(sol, a, v) in (0, 3):
            pool.append((lambda w, a=a, v=v: pos(w, a, v) in (0, 3), f"{cap(d)} lives at one end of the row"))
        else:
            pool.append((lambda w, a=a, v=v: pos(w, a, v) in (1, 2), f"{cap(d)} lives in one of the two middle houses"))
    return pool

sol = {"name": tuple(rng.sample(NAMES, 4)), "pet": tuple(rng.sample(PETS, 4)), "drink": tuple(rng.sample(DRINKS, 4))}
pool = clue_pool(sol)
while True:
    rng.shuffle(pool)
    chosen = []
    for c in pool:
        chosen.append(c)
        if len(list(itertools.islice(solutions(chosen), 2))) == 1:
            break
    for c in list(chosen):
        rest = [x for x in chosen if x is not c]
        if len(list(itertools.islice(solutions(rest), 2))) == 1:
            chosen = rest
    if len(chosen) == 8:
        break
assert list(solutions(chosen)) == [sol]
Path("logs").mkdir(exist_ok=True)
for i in range(4):
    body = noise(146)
    body.insert(rng.randint(10, 130), f"CLUE: {chosen[2*i][1]}. {chosen[2*i+1][1]}.")
    Path(f"logs/part{i+1}.log").write_text("\n".join(body) + "\n")
PY
