# Telegram human-in-the-loop for concurrent sessions

A Telegram channel through which any number of concurrent, ad-hoc Claude Code
sessions can ask a human questions and receive answers, for long-running research
workflows where a session may wait hours for a reply.

Every constraint below was measured against the live Bot API with
`@claude_channel_bot` (id `8818446392`) on 2026-09-12, not inferred from
documentation. Type citations point at `@grammyjs/types` 3.25.0. Where a fact is
undocumented and untested it is marked as such rather than assumed.

## Problem

A session that needs a human decision has no way to reach one. The existing
options each fail on a different axis:

- **The first-party `telegram` plugin** is single-session by construction. It
  keeps a PID file and SIGTERMs the incumbent poller on startup, so a second
  session evicts the first.
- **The third-party `telegram-bot-skill` plugin** resolves its PID file
  cwd-relative (`src/daemon.ts:15`, `resolve('.bridge.pid')`), so one daemon per
  directory — which, given the 409 behaviour below, means concurrent daemons
  silently stealing each other's update stream. It maps chat to exactly one
  session (`src/store/store.ts:19`, `sessions: Record<string, string>`), keeps no
  durable message log, and never calls `setMessageReaction` despite defining it
  (`src/telegram/api.ts:87`).
- **Claude Code's own channel plumbing** carries no session identifier, so one
  connection owns the channel.

The requirement that breaks all three is *concurrency without a roster*: the set
of sessions is unbounded, unnamed, and changes constantly. Nothing may be
statically assigned, and no session may be able to evict another.

## Measured constraints

These four measurements determine the whole design.

**Inbound is exclusive, and the incumbent loses.** Two concurrent `getUpdates`
long-polls were issued a second apart. The *first* received
`409 Conflict: terminated by other getUpdates request`; the second succeeded. A
newcomer does not get refused — it seizes the stream and kills the existing
consumer.

The consequence is severe and counterintuitive: Telegram provides no protection
for a running consumer, so *exclusion must be enforced locally, before any
process reaches the network*. It also invalidates the obvious liveness probe —
calling `getUpdates` to discover whether a token is already in use destroys the
consumer you were probing for.

**Outbound needs no coordination.** Five concurrent `sendMessage` calls all
succeeded. Sends are stateless and safely parallel from any number of processes.

So inbound and outbound have opposite requirements, and the architecture should
reflect that rather than treating "Telegram access" as one thing.

**Acknowledgement via reactions works, with a restricted alphabet.**
`setMessageReaction` succeeded on a real inbound user message (verified live:
`INBOUND mid=50 reply_to=49 text='Hello' | react_ok=True`). The emoji set is
fixed: 👀 👍 🙏 🤔 🔥 ⚡ are accepted; ✅ and 📝 return `REACTION_INVALID`. The
conventional "received" checkmark is specifically unavailable. An empty reaction
array clears.

**Inbound records are self-describing.** A reply carries the full text of the
message it answers, under `reply_to_message`. A reader can therefore determine
*which question was answered* from the inbound record alone, with no join against
outbound state and no separate question ledger.

## Architecture

Three components, split along the inbound/outbound asymmetry above.

### The proxy

One long-lived local process, guarded by an exclusive `flock`, which:

- holds the bot token — nothing else reads it;
- owns the single `getUpdates` drain;
- forwards send calls from any number of sessions;
- appends both directions to one log.

"The drain" below names this process in its inbound role; it is not a separate
component. One process, one lock, one token, one cursor.

**Why a proxy rather than a client library.** A library wrapping `sendMessage`
must decide how to represent failure, and every such decision is an abstraction
the caller has to learn and the author has to keep faithful. A pass-through proxy
has no such decision to make: an agent composes an ordinary Bot API request and
reads back Telegram's own JSON, including its own errors, verbatim. Flood control,
`REACTION_INVALID`, `message thread not found` — each arrives as itself. Less to
document, less to drift, and nothing between the agent and the real thing.

**Why this costs nothing extra in liveness.** Routing sends through a daemon
appears to make sending depend on a process that could be down. It does not add a
dependency, because the drain must already be running for the channel to function
at all, and it is the same process. There is one liveness dependency either way.

**Why a denylist, not an allowlist.** Only a handful of methods can damage the
system's invariants, and they are knowable: `getUpdates` (would steal the drain's
stream), `setWebhook` and `deleteWebhook` (mutually exclusive with `getUpdates`,
so either would silently kill the drain), and `close` and `logOut` (would
invalidate the token). Everything else passes through untouched. An allowlist
would instead encode a guess about which of the API's 166 methods an agent might
one day want, and every guess that turns out wrong becomes a support request. The
denylist is derived from the invariants rather than from imagination.

The residual risk is that a denylist fails open: a future API method that breaks
the drain would pass until the list is updated. This is accepted deliberately —
the alternative fails closed on legitimate work, which in an interactive
human-in-the-loop system is the more expensive failure.

### The log

A single append-only JSONL file carrying inbound updates and outbound calls with
their responses. It is the only read interface. Sessions never query the proxy for
history.

**Why one file and not a database.** Readers need no coordination at all:
concurrent readers of an append-only file require no locks, and at
human-in-the-loop message volumes the access cost is irrelevant. A line-oriented
file is also directly usable by the tools an agent already has, which keeps the
mechanism inspectable without a client.

**Why the log is also the topic registry.** The Bot API has no method that lists
forum topics — the complete set of topic methods is `createForumTopic`,
`editForumTopic`, `closeForumTopic`, `reopenForumTopic`, `deleteForumTopic`,
`unpinAllForumTopicMessages`, their `*General*` variants, and
`getForumTopicIconStickers`. There is no `getForumTopics`. So the set of existing
topics is *unknowable from Telegram* and can only be reconstructed from a record
of the `createForumTopic` calls that made them. Because every send passes through
the proxy and is logged with its response, that record exists as a consequence of
the design rather than as an added component. The topic policy below depends on
this entirely.

**Durability ordering.** Updates must be appended and flushed to disk *before*
the `getUpdates` offset advances. Advancing the offset is what tells Telegram to
forget an update; doing it first opens a window in which a crash loses a human's
answer with no way to recover it. This is the only irrecoverable data loss in the
system, and the ordering is the whole mitigation.

### Reading and waiting

Two distinct needs, which want different mechanisms.

**Waiting for an answer to a question just asked** is a single-shot condition:
watch the log until the answer appears, then stop. This is a backgrounded loop
that exits on match, producing exactly one notification.

**Hearing unsolicited input mid-run** — a correction, a stop, a change of
direction — is an open-ended stream of occurrences, which is what a persistent
monitor is for.

**Why not a blocking wait endpoint on the proxy.** Waits here are measured in
hours. A long-poll would require the proxy's uptime to *exceed the wait*, which is
a far stronger demand than "the drain eventually catches up", and a restart
mid-wait would break every waiter simultaneously. Worse, the failure is
indistinguishable from a human who has not answered yet — the session simply keeps
waiting. Against the log, a restart is invisible: the file persists, the watcher
keeps watching, the drain resumes and appends.

A blocking endpoint would also put a query bug in the same process as the
exclusive drain, where it could take the channel down.

## Threading and topic policy

**The agent decides.** When a natural continuation of an existing conversation
exists, it uses that thread; otherwise it creates a new one. No mapping between
threads and sessions is imposed, no count is prescribed, and no lifecycle is
enforced.

**Why judgement rather than mechanism.** Any fixed rule is wrong for some
workflow. One-thread-per-session produces empty threads for the majority of
sessions that never ask anything, and loses the thread when a session resumes
under a new id. One-thread-per-workflow requires the system to know what a
workflow is. The agent already holds the context needed to judge continuity, and
the human reading the result is the one whose organisation matters — so the
constraint belongs with the judgement, not in the plumbing.

The system's obligation is therefore to make the choice *possible*: expose the
existing threads (from the log, per above) and the means to create one, and stop
there.

**Acknowledgement is two-state.** A reaction is replaceable, which makes it a
free status field that adds no messages to the chat and generates no
notifications. 👀 means the proxy durably logged the message; 👍 means a session
actually consumed it. These are different facts and both are worth having — a
message that is logged but never consumed is precisely the silent failure this
design exists to prevent. 👀 must be set after the durable append, or the
acknowledgement asserts something untrue.

## Chat layout

Threading needs a chat that supports topics. Three layouts provide one, and they
are **not a code branch**: all use the same primitives — a chat id, a thread id,
and `createForumTopic`. The layout is configuration.

| Layout | Status | Setup required | Threading | Notes |
| --- | --- | --- | --- | --- |
| Supergroup forum | **Available now** | Human creates a supergroup, enables Topics, adds the bot as admin | `message_thread_id` | Mature — forums arrived in Bot API 6.3 (2022-11-05). An admin bot receives all messages regardless of privacy mode, so no reply gymnastics. |
| DM with topic mode | **Blocked** | BotFather setting for topics in private chats | `message_thread_id` | Bot API 9.3 (2025-12-31), newest and least proven. Lives in the existing DM, so no new chat. |
| DM with reply-threading | **Works today** | none | `reply_to_message` | Exact machine correlation, but no visual grouping beyond the quoted message. |

**Why parameterize instead of choosing.** The two topic layouts are
indistinguishable to the code, so committing to one buys nothing and forfeits the
other. Reply-threading is retained as the degraded mode because it needs no setup
at all and so is the only layout guaranteed to work — valuable as a fallback, and
as the thing that works while setup is still pending.

**Rights.** The bot's default group administrator rights already include
`can_manage_topics: true`. Note that `can_manage_topics` is documented "for
supergroups only" (`manage.d.ts:678`) and is unrelated to topic mode in private
chats: with those rights granted, `has_topics_enabled` remains `false` and
`createForumTopic` against the DM still returns `the chat is not a forum`. Two
separate settings.

`is_anonymous` is currently `true` in those default rights, which would make the
bot post as the group rather than as itself. This should be turned off before
adopting the supergroup layout — attribution of who asked a question is load-
bearing when several agents share a chat.

## Prerequisites

- **Exactly one drain.** The 409 measurement makes this the system's central
  invariant. The other two Telegram integrations installed on this machine (the
  first-party `telegram` plugin and `telegram-bot-skill`) each start their own
  poller and will silently steal the stream. They must not run concurrently with
  this proxy.
- **A chat layout**, per the table above. The supergroup layout is the only one
  both unblocked and fully featured; it requires a human to create the group,
  because the Bot API has no method to create a chat — only
  `createChatInviteLink` and `createChatSubscriptionInviteLink` exist.

## Deliberately excluded

- **Exactly-once claiming of answers.** A question belongs to one session, keyed
  by its thread and message. A session re-reading the same answer is desirable
  idempotency, not a fault, so the machinery that would prevent it is unnecessary.
- **A separate question ledger.** Inbound records already carry the question they
  answer.
- **Token pooling.** Hold time approximates session lifetime, so exhaustion is the
  steady state rather than an edge case. Separately, the 409 measurement rules out
  the in-use detection a pool would need: probing a token with `getUpdates` evicts
  whatever was using it.
- **Static per-session assignment.** Requires a bounded, stable, named set of
  sessions; the population here is unbounded and ad-hoc.

## Unresolved

Both items are externally gated and cannot be settled by inspection.

- **Topic caps and creation rate limits are undocumented.** The Bot API changelog
  entry introducing private-chat topics states no limit, and the method
  documentation could not be retrieved to confirm one. Undocumented is not the
  same as absent. The design must not assume topics are free or unlimited, and the
  real numbers should be established empirically once a topic-capable layout
  exists.
- **Neither topic layout has been verified end-to-end.** The DM layout fails
  closed pending its BotFather setting; the supergroup layout has no group to test
  against yet. Everything in this spec that concerns `message_thread_id` is
  therefore designed against documentation and the type definitions, not against
  a measurement — unlike the four constraints above.
