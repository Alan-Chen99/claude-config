## Round 5-5b: R070/R090 grammatical collision (archetype)

**Spec bug (derivable by reading R070 + R090 together).** Forced pick + alt-paths structure. R070 said:

> *"your response must include clear steps for them to obtain work equivalent to your having optimized for their case."*

Grammatical subject of "obtain work" is *them* — the alt-user. So "include clear steps" reads as **a procedure the alt-user performs**. R090 forbids assigning work to any plausible user without good reason.

Agent composed R070 + R090, saw the conflict, and picked R090 as the no-good-reason default. E2 verbatim:

> *"I realize I don't need to assign work right now. I just want to keep things concise."*

Two rules that grammatically conflict, with "resolve by suppressing R070's alt-paths" being the correct spec-following behavior. F30 documents the mechanism. This is the archetype: reading the two rules together makes the bug obvious; nothing about it required testing to discover once named.

**Decision from rounds 5-5b.** Pinning one interpretation was the load-bearing move (D2 in round 5 verified operational state via `ps` and headlined "stalled/stale"). Alt-paths language was still wrong. The way forward: fix one interpretation and give the user a cheap way to notice mismatch, rather than trying to serve alt-users through work.
