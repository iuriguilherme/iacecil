# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Platform layer

### Connector
A platform adapter that gives the bot presence on one chat platform (Telegram, XMPP, loopback). Implements connect, listen, send and disconnect; owns its platform's delivery policy (message splitting, failure handling). A connector activates only when its bot config section carries credentials, and a failing connector is marked down without stopping its siblings.

### Envelope
The platform-neutral representation of one inbound or outbound message. Carries a normalized core (platform, sender, conversation, text, reply reference, tags) plus a raw native platform object and an extra dict as escape hatches; the core never inspects the escape hatches and they are never persisted.

### Personalidade
A personality module that decides what text the bot says, independent of platform. Exposes envelope-safe commands (its connector-facing surface) and legacy platform handlers (its Telegram-facing surface). One personalidade is configured per bot.
*Avoid:* persona, personality module

## Identity and persistence

### Person
The canonical identity of one human across platforms. Maps one or more (platform, native id) pairs to a single record; created automatically on first contact from an unseen platform identity, and mergeable when two records turn out to be the same human.
