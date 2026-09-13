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

It originates nothing and interprets nothing. Every message, reaction and topic
in the chat is some agent's send that it forwarded, and no field of an update
carries meaning to it — updates are bytes to be recorded, not data to be routed.
Routing, correlation and topic choice all happen in agent scripts reading the
log.

This is why the proxy has no behaviour of its own to document, configure, or
reason about, and it is what keeps the log a faithful record of who did what. It
also means the API's semantics stay the agent's concern: the design takes no
position on what any field means, so it cannot be wrong about one.

**Why a proxy rather than a client library.** A library wrapping `sendMessage`
must decide how to represent failure, and every such decision is an abstraction
the caller has to learn and the author has to keep faithful. A pass-through proxy
has no such decision to make: an agent composes an ordinary Bot API request and
reads back Telegram's own JSON, including its own errors, verbatim. Flood control,
`REACTION_INVALID`, `message thread not found` — each arrives as itself. Less to
document, less to drift, and nothing between the agent and the real thing.

**Why a Unix socket rather than a port.** The participants are containers with
separate network namespaces, so a port number is not an address: `18420` names a
different socket in each namespace that reads it, and a file recording it cannot
say which one a reader should dial. Whoever won the lock would decide who could
send, and the losers would meet connection-refused while the drain and the log
both reported a healthy channel — *a down channel looking like a slow human*,
the failure this design exists to prevent, re-entering through the boundary.

A path has no such ambiguity. The socket sits in the shared state directory
beside the lock and the log, so a participant that can see the channel's state
can reach the process holding it: "the channel is up" and "I can send" become
one fact rather than two that can disagree. It keeps the token off every network
interface, and it works in either direction — proxy on the host serving
containers, or proxy in a container serving its siblings and the host — with no
address to configure for either.

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

**Limits are diagnosed, not absorbed.** The proxy does no rate limiting, no
pacing and no retrying. Flood control, `retry_after`, and any cap on topics or
messages reach the agent that provoked them, as the error Telegram sent.

Absorbing them would be the wrong trade twice over. A proxy-level retry has no
idea whether the call still matters, whether the human has since answered, or
whether the workflow is looping — it can only delay blindly, which converts a
diagnosable fault into latency. And traffic heavy enough to trip flood control is
itself the finding: at human-in-the-loop volumes it should not happen, so pacing
it would hide a defect rather than fix one. The agent that hit the limit is the
only party with the context to decide whether to back off, restructure, or stop.

This also retires limits as a design question. An unknown ceiling that announces
itself at runtime, to a party equipped to interpret it, is not something the
design needs to know in advance.

### The log

A single append-only JSONL file carrying inbound updates, outbound calls with
their responses, and errors. It is the only read interface. Sessions never query
the proxy for history.

**Errors are logged, not just returned.** A failed call's response is logged like
any successful one — an error is a response. More importantly the proxy logs its
*own* faults: a `getUpdates` failure, a 409 meaning another poller has seized the
stream, a write failure, its own startup and shutdown.

This is what finally separates the two states a waiting workflow otherwise cannot
tell apart. Until now a watcher could observe only "answer" or "no answer yet",
and a broken channel looked exactly like a human who had not replied — the
failure shape this design keeps running into. With the channel's own faults in
the same stream, a watcher can distinguish *no answer yet* from *the channel is
down*, and act differently. The human gains the same visibility, from the same
file, without being told separately.

It also means propagation and durability are not in tension. An error still
reaches the caller verbatim, per "Limits are diagnosed, not absorbed"; logging it
additionally means the fault survives a script that crashed before reading it, or
an agent that never looked.

One constraint follows: log error *transitions*, not occurrences. A stolen stream
makes every subsequent poll fail, and recording each one at poll rate would bury
the log in identical lines. The interesting events are entering and leaving a
failing state.

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

**The drain does nothing else.** Poll, append, flush, advance. It does not react,
does not interpret, does not decide what an update means. Everything else —
reacting, replying, creating topics — is an agent's send, passing through the
proxy like any other call.

The motive is blast radius. The drain is the one component no other component can
replace, because it holds the only cursor and the 409 measurement means a
replacement cannot simply be started alongside it. Any work it takes on is work
that can kill it, and a dead drain reaches a waiting workflow as *"the human has
not answered yet"* — indistinguishable from a slow human, which is the failure
this design exists to prevent. So its failure surface is held to two cases:
network errors on `getUpdates`, which it retries, and failure to durably record
an update, which is fatal because continuing past it would silently drop a human's
answer.

This was learned by crashing a probe drain that *did* react. It died on
`400 MESSAGE_ID_INVALID` reacting to a chat-migration service message — after the
append had succeeded, so the durability ordering above held and all six records
survived. A cosmetic call took down the channel, which is the whole argument for
keeping such calls out of the drain rather than merely wrapping them in a
`try`.

Reactability is type-specific and unpredictable: `new_chat_members` accepted a
reaction while both migration service messages returned `MESSAGE_ID_INVALID`.
Agent scripts that react will meet this, and should — a script crashing on it is
loud, local, and harms nothing else.

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

**Acknowledgement is the agent's act, not the proxy's.** The session that was
waiting reacts to the human's message from its own script, once it has read it.
The proxy never reacts — reacting is an ordinary send like any other, made by
whoever has something to assert.

A reaction is a good carrier for this because it is replaceable and adds no
message to the chat, so it generates no notification and no log noise.

**Why the proxy must not react.** A proxy-side acknowledgement could only ever
mean "durably logged", which is not the question a human is asking. They want to
know whether the thing that was waiting has their answer. Worse, a proxy-side
reaction would *mask* the one failure that matters: if the proxy marks every
inbound message as seen, then a message that was logged but never picked up by
any session looks identical to one that was acted on. The human reads
acknowledgement as progress and stops watching. Leaving the reaction to the agent
makes the absence of one informative — an unreacted message is a message nobody
has taken.

This also keeps the proxy free of behaviour that has to be specified and learned.
Reactions become a thing agents do, on their own judgement, with the same API
surface as everything else — consistent with the reasons for choosing a
pass-through proxy in the first place.

## Chat layout

Threading needs a chat that supports topics. Three layouts provide one, and they
are **not a code branch**: all use the same primitives — a chat id, a thread id,
and `createForumTopic`. The layout is configuration.

| Layout | Status | Setup required | Threading | Notes |
| --- | --- | --- | --- | --- |
| Supergroup forum | **Verified working** | Human creates a supergroup, enables Topics, adds the bot as admin | `message_thread_id` | Mature — forums arrived in Bot API 6.3 (2022-11-05). An admin bot receives all messages regardless of privacy mode, so no reply gymnastics. |
| DM with topic mode | **Blocked** | BotFather: enable **Threaded mode** (see below) | `message_thread_id` | Bot API 9.3 (2025-12-31), newest and least proven. Lives in the existing DM, so no new chat. |
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

**The DM layout's setting is called "Threaded mode", not "topics".** This
terminology gap costs real time — searching BotFather for "topics" finds nothing.
`core.telegram.org/api/forum` states it verbatim: *"Bots can also behave like
forums if Threaded mode is enabled via @botfather, this mode is especially useful
for AI chatbots"*. The companion option is named *"Disallow users to create new
threads"*, and it is what `allows_users_to_create_topics` reports. Enabling
Threaded mode is what sets `has_topics_enabled`.

Telegram documents no menu path for it. The standard navigation for bot settings
is `/mybots → select bot → Bot Settings → …`, which is verbatim-confirmed for
other settings but not for this one; the submenu name is unverified. Look for
"Threads", not "Topics".

**The supergroup layout needs two human actions, and they are easy to conflate:**
enabling Topics on the group, and granting the bot the Manage Topics right. The
bot's *default* admin rights do not settle the second — defaults apply only at
promotion, and the bot cannot repair its own rights afterwards
(`promoteChatMember` on itself returns `can't promote self`). `createForumTopic`
distinguishes the two: `the chat is not a forum` means Topics is off,
`not enough rights to create a topic` means the right is missing, and a returned
`ForumTopic` means both are done.

**A forum's General topic is not addressable**, so a conversation becomes
routable only once a topic has been created for it. This is why the Manage Topics
right is a prerequisite rather than a nicety: without it a bot can still post and
react in the forum, but every message lands in one undifferentiated stream.

**Enabling Topics migrates the chat and changes its id.** The test group was
created as `group` id `-5480670982` and became `supergroup` id
`-1004384191085`; the old id is now dead, returning `group chat was upgraded to a
supergroup chat`. Any stored chat id must therefore follow `migrate_to_chat_id`
rather than being treated as stable.

**Privacy mode is not the relevant control here.** Disabling it
(`can_read_all_group_messages: true`) governs what a *non-admin* bot receives in
groups; an admin bot already receives everything —
*"Privacy mode is enabled by default for all bots, except bots that were added to
a group as admins (bot admins always receive all messages)"*. It is also
per-membership, not retroactive: *"the bot will need to be re-added to the group
for this change to take effect"*. So for an admin bot it is redundant, and
disabling it after the bot joined has no effect on that group either way. It
matters only as insurance against a future demotion.

## Crossing the container boundary

The channel is shared by several containers and by the host they run on. Three
properties make that work. Each was measured on this machine — rootless Docker,
slirp4netns, ext4 bind mounts — on 2026-09-13, rather than assumed.

**One directory, seen under different names.** A container's home is a bind
mount of a host directory, so the state directory is the same inode from either
side: `stat` reported `dev=64513 ino=669888` identically from two containers.
Only the spelling of the path differs, which is why the directory is named by an
environment variable and never derived from `$HOME`. A home-derived default
would resolve somewhere different in each participant, and each would then take
its own lock and start its own drain.

**`flock` crosses the boundary.** A lock held by a process in one container
blocked a process in another on the same bind-mounted file. So *exactly one
drain* — enforced locally because Telegram will not enforce it — covers every
container and the host, and not merely one container's process table.

**A Unix socket crosses it too.** A server bound to a socket in a shared
directory was reached by a client in a different container, through that
container's own path to it. AF_UNIX resolves to an inode, and a bind mount is
the same inode.

**What bounds all three.** They are properties of one kernel and one local
filesystem. Where the filesystem is not local — NFS, virtiofs, a Docker Desktop
bind mount from macOS — the socket does not carry, and the log's own guarantee
is already void: `open(2)` states that `O_APPEND` *"may lead to corrupted files
on NFS filesystems if more than one process appends data to a file at once"*,
which is precisely this design's access pattern. The socket therefore forfeits
no portability the log has not already spent.

The one constraint the socket adds by itself is path length. `sun_path` holds
108 bytes including its terminator — measured: 107 binds, 108 does not — far
below `PATH_MAX`, so a state directory deep enough to break the socket still
opens the log without complaint. The proxy checks the budget at bind and names
it, because the kernel's own `AF_UNIX path too long` names neither the path nor
the limit.

**Identity.** The socket is mode 0600, matching the log, so every participant
must present the same uid. That holds here because every container maps uid 0 to
one host uid. Where it stops holding, the log becomes unreadable at the same
moment the socket becomes unreachable — a coherent failure rather than a partial
one where a session can read answers it has no way to acknowledge.

## Prerequisites

- **One shared state directory**, named by `TELEGRAM_HITL_STATE_DIR` and mounted
  into every participating container. It carries the lock, the socket, the log
  and the offset, and it has no default — see "Crossing the container boundary"
  for why guessing one is what allows a second drain.
- **Exactly one drain.** The 409 measurement makes this the system's central
  invariant. The other two Telegram integrations installed on this machine (the
  first-party `telegram` plugin and `telegram-bot-skill`) each start their own
  poller and will silently steal the stream. They must not run concurrently with
  this proxy.
- **A chat layout**, per the table above. Each step below needs a human, because
  the Bot API can neither create a chat (only `createChatInviteLink` and
  `createChatSubscriptionInviteLink` exist) nor raise the bot's own rights.
  For the supergroup layout that means two steps, both done for
  `claude-channel-group` (`-1004384191085`): enable **Topics** on the group, and
  grant the bot **Manage Topics** in that group's admin settings. `getChat`
  reporting `is_forum` and `getChatMember` reporting `can_manage_topics: true`
  confirm each; `createForumTopic` succeeding confirms both.

## The skill

The second component is a skill, because the first deliberately knows nothing.
Since the proxy neither interprets updates nor smooths over errors, everything an
agent needs to work the channel correctly is knowledge, not API surface — and
knowledge has to live somewhere a fresh session will read.

It carries the working rules (how to pick or create a topic, how to wait, when to
react) and the Bot API traps that cost real time to find. Those traps are not
design content and are deliberately absent from this spec, but they must not be
lost, so they are enumerated here as the skill's scope:

- `message_thread_id` carries *either* a reply-chain id or a forum-topic id
  (`message.d.ts:11`); `is_topic_message` is the discriminator. Keying on the
  former alone files ordinary replies as topics, and both ids come from the same
  per-chat counter, so the wrong value is not out of range.
- Reactability is type-specific and unpredictable — `new_chat_members` accepts a
  reaction, chat-migration service messages return `MESSAGE_ID_INVALID`.
- The reaction alphabet is fixed, and excludes the obvious checkmark.
- A forum's General topic cannot be addressed by thread id.
- Enabling Topics migrates a group to a supergroup and changes its chat id; the
  old id then returns `group chat was upgraded to a supergroup chat`, and
  `migrate_to_chat_id` is the forwarding pointer.
- Reading a file that is being appended to needs care in Python, which yields
  partial final lines where a shell `read` loop does not.

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

**The supergroup layout is verified end-to-end.** In `claude-channel-group`
(`-1004384191085`, `is_forum: true`), with the bot an administrator holding
`can_manage_topics: true`: `createForumTopic` returned
`{message_thread_id: 6, name: "research: alpha", icon_color: 7322096}`; a second
topic was created independently; sends addressed with `message_thread_id` came
back `thread=6, is_topic_message=true`; `editForumTopic` renamed a topic;
reactions worked inside a topic; and human replies in two different threads
arrived correctly discriminated. Topic routing is measured, not inferred.

One item remains open, by choice rather than obstruction: **the DM layout is
unverified.** BotFather's Threaded mode was not located, `has_topics_enabled` is
`false`, and `createForumTopic` against the DM returns `the chat is not a forum`.
Since the layouts are the same code path and the supergroup one works, this
blocks nothing.

Topic caps and rate limits are deliberately *not* listed here. Fifteen
consecutive `createForumTopic` calls and fifteen `deleteForumTopic` calls showed
no throttling and no `retry_after`, but that bounds nothing — the burst was kept
small on purpose. It does not need bounding: per "Limits are diagnosed, not
absorbed", a ceiling that announces itself at runtime is not a gap in the design.
