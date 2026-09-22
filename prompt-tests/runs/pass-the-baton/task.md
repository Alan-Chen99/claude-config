I'm handing `dispatch` over before I go on leave on Friday. It's the worker that
takes rows out of the `outbox` table and posts them to Truxel, our shipping
vendor.

What I'd tell you over coffee:

- It wakes up every five minutes and takes whatever's waiting.
- If Truxel is unhappy it backs off and tries again — three attempts — then
  leaves the row where it is and picks it up next cycle.
- The 2am batch is the big one. If it's still going at 3 something is wrong.
- Twice this year I've had to stop it halfway through and start it again. Once
  the box was rebooted under it, once I'd deployed a bad build. Both times I
  just started it back up.
- The one thing customers notice is a parcel going out twice. It hasn't
  happened to us, but it's the one that costs real money.

Write the page whoever picks this up reads at 2am when it has gone wrong: what
it does, what to look at, and what to do about it. Call it `OPERATIONS.md`.
