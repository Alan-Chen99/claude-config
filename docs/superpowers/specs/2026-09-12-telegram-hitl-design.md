# Telegram human-in-the-loop for concurrent sessions

A Telegram channel through which any number of concurrent, ad-hoc Claude Code
sessions ask a human questions and read the answers, hours later if need be.
Measured against the live Bot API with `@claude_channel_bot` (id `8818446392`)
from 2026-09-12. Using it: `skills/telegram-hitl/SKILL.md`; the listener's
guarantees: that directory's `README.md`.

## Problem

The first-party `telegram` plugin SIGTERMs the incumbent poller;
`telegram-bot-skill` keeps a cwd-relative PID file, one session per chat and no
durable log; Claude Code's channel plumbing carries no session id. None serves
an unbounded, unnamed, changing set of sessions, none able to evict another.

## Measured constraints

- **Inbound is exclusive, and the incumbent loses.** Of two concurrent
  `getUpdates` long-polls, the *first* got `409 Conflict`. Exclusion must be
  local, before the network, and probing a token with `getUpdates` evicts its
  user.
- **Outbound needs no coordination.** Five concurrent `sendMessage` calls all
  succeeded.
- **Reactions acknowledge, from a fixed alphabet.** 👀 👍 🙏 🤔 🔥 ⚡ work, ✅ and
  📝 return `REACTION_INVALID`, an empty array clears. `new_chat_members`
  accepts one; chat-migration service messages return `MESSAGE_ID_INVALID`.
- **A reply carries the message it answers** under `reply_to_message`.
- **The update subscription is sticky.** A poll naming no `allowed_updates`
  keeps the token's last list — this bot held `["message", "callback_query"]`,
  `telegram-bot-skill`'s list, on 2026-10-14 — the default omits
  `message_reaction`, `message_reaction_count` and `chat_member`, and Telegram
  drops an unlisted update as it happens. The drain names every type on every
  poll (`drain.ALLOWED_UPDATES`).

## Architecture

**The proxy**, one process under an exclusive `flock`, holds the token, owns the
single `getUpdates` drain, forwards sends from any number of sessions and logs
both directions. It originates and interprets nothing: routing, correlation and
topic choice happen in agent scripts reading the log.

- *Pass-through, not a library*: an agent sends an ordinary Bot API request and
  reads Telegram's own answer, errors included.
- *A Unix socket, not a port*: a port names a different socket in each
  container's network namespace; the socket beside the lock and the log makes
  "the channel is up" and "I can send" one fact.
- *A denylist*: `getUpdates`, `setWebhook`, `deleteWebhook`, `close`, `logOut`
  break the drain or the token. A future method that breaks it passes until
  listed, accepted because failing closed blocks legitimate work.
- *Limits are diagnosed, not absorbed*: no pacing or retry; flood control
  reaches the agent that provoked it, the only party that knows whether the call
  still matters.

**The log**, one append-only JSONL file, is the only read interface: inbound
updates, outbound calls with responses, refusals, and the proxy's own faults as
transitions, so a waiter tells *no answer yet* from *channel down*. It is the
topic registry too, as the Bot API has no `getForumTopics`. An update is fsynced
before the next poll carries the advanced offset; an update Telegram forgot
before it reached disk is the only irrecoverable loss.

**The drain does nothing else**: poll, append, flush, advance. A probe drain
that reacted died on `MESSAGE_ID_INVALID` from a migration service message, and
a dead drain reads as a slow human.

## Reading, acknowledging, topics

Reading is at-least-once; the acknowledgement is the agent's reaction, never the
printer's position. Waits read the file, not a blocking proxy endpoint, so a
proxy restart is invisible to a waiter. The proxy never reacts: its
acknowledgement could only mean "logged", and would make a message nobody took
look acted on. The agent picks or creates the topic; any fixed thread-to-session
rule is wrong for some workflow.

## Chat layout

| Layout | Status | Threading |
| --- | --- | --- |
| Supergroup forum, bot an admin | **Verified**: `claude-channel-group` (`-1004384191085`) | `message_thread_id` |
| DM with topic mode | **Blocked**: BotFather's "Threaded mode" (look for "Threads") not found | `message_thread_id` |
| DM with reply-threading | Works, no setup | `reply_to_message` |

One code path serves all three. Threaded mode sets `has_topics_enabled`;
`can_manage_topics` does not. The supergroup needs two human actions, enabling
Topics and granting the bot Manage Topics (defaults apply only at promotion);
`createForumTopic` answers `the chat is not a forum`, `not enough rights to
create a topic`, or a `ForumTopic`. Enabling Topics changes the chat id (follow
`migrate_to_chat_id`). The General topic has no thread id. An admin bot receives
every message whatever its privacy mode.

## Crossing the container boundary

Measured 2026-09-13, rootless Docker with ext4 bind mounts: the state directory
is one inode under different paths from host and containers, `flock` excludes
across them, and its Unix socket is reachable from each. So one environment
variable names it; a `$HOME`-derived path gives each participant its own lock
and drain. NFS, virtiofs or a Docker Desktop mount breaks the socket, and on NFS
concurrent `O_APPEND` writers may corrupt the log (`open(2)`). `sun_path` caps
the socket path at 107 bytes. Socket and log are 0600: one uid for every
participant.

## Prerequisites

- One shared `TELEGRAM_HITL_STATE_DIR`, no default, mounted into every
  participant.
- Exactly one drain: the `telegram` plugin and `telegram-bot-skill` each poll the
  token and must not run alongside the proxy.
- A chat layout a human set up; the Bot API creates neither chats nor its own
  rights. `getChat` `is_forum` and `getChatMember` `can_manage_topics: true`
  confirm it.

## Excluded and open

Excluded: exactly-once claiming (re-reading is idempotent), a question ledger
(replies carry the question), token pooling (probing a token evicts its user),
static per-session assignment (the population is unbounded). Open: the DM
layout, which blocks nothing. Topic caps are not listed: fifteen consecutive
`createForumTopic`/`deleteForumTopic` calls met no throttling, and a limit
announces itself at runtime.
