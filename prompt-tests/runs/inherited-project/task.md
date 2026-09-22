I'm handing `feedwatch` over. Write the `CLAUDE.md` a future agent reads before
it touches anything here.

What I can tell you:

- We poll every ninety seconds. It was thirty and the feed started throttling us.
- `retry.py` waits five seconds between attempts and gives up after three.
- `httpx` is pinned. I don't know why — that pin predates me and the commit
  message is just "pin httpx".
- Last March two pollers ran at the same time and `store.py` wrote the same ids
  twice. We lost about six hours of rows reconciling it. Nothing in the code
  stops a second poller.
- Also, and unrelated to any of that: I'd rather we didn't take on new
  dependencies.
