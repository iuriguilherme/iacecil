# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Platform layer

### Bot
One configured assembly of a Personalidade, an enabled plugin set, and platform credentials, named by its configuration entry. A bot's name keys its per-chat storage and its operator Log Sinks; one running process may host several bots, each with its own connector set.

### Connector
A platform adapter that gives a Bot presence on one chat platform (Telegram, XMPP, Discord, Matrix, loopback). Implements connect, listen, send and disconnect; owns its platform's delivery policy (message splitting at the platform's length limit, failure handling) and decides which conversations it will answer (see Authorized conversation). Each connector declares its own activation rule — which credential fields its config section must carry — so adding a platform requires no loader changes. A failing connector is marked down without stopping its siblings.

### Authorized conversation
A conversation a Bot is allowed to *reply* in, as distinct from one it merely *observes*. Direct messages are always authorized; group conversations are authorized only when listed in the Connector's configured channel allowlist.

Observation and response are separate concerns: every message a Connector can see becomes a Neutral Record regardless of authorization, but a reply is produced only for an authorized conversation. Each Connector judges authorization for its own platform — a direct message is recognized in platform-specific ways (no group/guild, a two-member room, a non-group message type) — so the policy lives in the Connector, not in the Plugin or Personalidade that generates the reply text.

### Envelope
The platform-neutral representation of one inbound or outbound message. Carries a normalized core (platform, sender, conversation, text, reply reference, tags, the platform's native message id, timestamp) plus a raw native platform object and an extra dict as escape hatches; the core never inspects the escape hatches and they are never persisted.

### Log Sink
An operator-configured destination that receives the bot's own log records as chat messages on any active Connector — for example, one platform's errors routed to a private group on another platform. A sink filters by level, logger-name prefix and tags; delivery is buffered until the sink's connector has connected, and records produced while delivering are dropped to prevent self-feedback.

### Personalidade
A personality module that decides what text the bot says, independent of platform. Exposes envelope-safe commands (its connector-facing surface) and legacy platform handlers (its Telegram-facing surface). One personalidade is configured per bot.
*Avoid:* persona, personality module

### Plugin
An independent feature module that adds message handlers to the bot, activated per bot through an ordered enable list. A plugin may expose a Telegram-facing surface, a connector-facing surface for the other platforms, or both; a plugin lacking a surface for some connector is skipped there with a warning rather than failing.

On Telegram, the enable list's order is load-bearing: the first matching handler wins, so a plugin with broad filters can starve every plugin and Personalidade handler registered after it. Which orderings work is discovered by trial and error, and some plugin combinations are incompatible in any order — an accepted limitation. All plugin handlers register before the Personalidade's handlers.

## Identity and persistence

### Person
The canonical identity of one human across platforms. Maps one or more (platform, native id) pairs to a single record; created automatically on first contact from an unseen platform identity, and mergeable when two records turn out to be the same human.

### Neutral Record
The persisted form of one Envelope: only normalized fields (platform, refs, text, direction, native message id, timestamp) — never live platform objects. Inbound and outbound messages both produce one, so a conversation round-trip is reconstructable from storage alone.

### Chat Store
Per-conversation message storage keyed by Bot, Connector and conversation, with every path component encoded to be valid and collision-free on any filesystem. Holds Neutral Records; deduplicates by native message id only when the platform supplied one. Succeeds the telegram-only per-chat storage, which remains readable as legacy data.
