---
title: Aiogram handler registration order is load-bearing and plugin compatibility is not guaranteed
date: 2026-06-10
category: architecture-patterns
module: plugins
problem_type: architecture_pattern
component: development_workflow
severity: medium
applies_when:
  - "Enabling, disabling, or reordering plugins in a bot config's plugins['enable'] list"
  - "A Telegram command stops responding after a plugin change, with no error logged"
  - "Adding a new plugin that registers aiogram message handlers"
  - "Debugging why a plugin works alone but not alongside others"
tags: [aiogram, plugins, handler-order, telegram, catch-all, known-limitation]
---

# Aiogram handler registration order is load-bearing and plugin compatibility is not guaranteed

## Context

Plugins register aiogram message handlers at startup, in the order they appear
in the bot config's `plugins['enable']` list (personalidade handlers register
*after* all plugins). Aiogram dispatches each incoming Telegram message to the
**first** handler whose filters match — registration order decides who wins.

This is a historical design problem in the plugin system. Which plugins must
come in which order has always been a guessing game, and some plugin
combinations are simply incompatible. **This is a known, accepted limitation —
it will not be fixed.** This document exists so the constraint is understood,
not so it gets re-discovered (or "fixed") by accident.

## Guidance

- A plugin "not working" on Telegram is often not a bug in the plugin: an
  earlier-registered handler with overlapping filters consumed the message.
  Before debugging plugin code, check the `enable` list order in the bot
  config (`instance/bots/<name>.py`).
- Catch-all handlers are the sharpest case. `echo` registers
  `@dispatcher.message_handler()` with **no filters** — it swallows every
  message that reaches it, so any plugin or personalidade handler registered
  after it never fires. Echo is a testing plugin; no production chatbot is
  expected to enable it.
- When a combination misbehaves, reordering the `enable` list is the
  supported remedy. There is no dependency declaration, priority system, or
  conflict detection — trial and error is the documented workflow.
- Some plugin pairs are incompatible in any order. If reordering doesn't
  resolve it, disable one of them; don't sink time into making them coexist.
- This limitation is Telegram/aiogram-specific. The connector path (XMPP,
  loopback, discord) uses ConnectorManager's command registry plus a single
  default handler — commands are matched by name, so registration order
  doesn't matter there (last `set_default_handler` call wins, which only
  matters if multiple plugins set one).

## Why This Matters

Symptoms of an ordering conflict look exactly like a broken plugin: a command
silently stops answering, nothing errors, nothing logs. Without knowing this
constraint, the natural move is to debug (or rewrite) plugin internals that
are working fine. Knowing it, the first check is cheap: what else is enabled,
and in what order?

It also explains why `src/iacecil/config.py` carries the FIXME: "Some plugins
currently will not work if loaded after others, have to find out which is the
correct order." That FIXME describes a permanent property of the system, not
pending work.

## When to Apply

- A Telegram command or handler stops responding after enabling a new plugin
- Echo (or any unfiltered catch-all handler) is enabled and other plugins go
  silent
- Writing a new plugin: prefer narrow filters (`commands=[...]`,
  content-type, regexp) over bare `message_handler()` so the plugin stays
  order-tolerant
- Reviewing a bot config: treat the `enable` list as ordered, not as a set

## Examples

`echo` swallowing everything registered after it:

```python
## src/plugins/echo.py — no filters: matches every message
@dispatcher.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)
```

With `enable = ["echo", "default", "admin"]`, the `default` and `admin`
command handlers never see a message on Telegram. With
`enable = ["default", "admin", "echo"]`, commands work and echo answers only
what falls through.

## Related

- `CLAUDE.md` — "Handler registration order follows the `enable` list"
- `src/iacecil/config.py` — FIXME comment above the default `plugins` dict
- `docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md`
  — why Telegram envelopes are *not* dispatched through the connector command
  registry (legacy aiogram handlers own Telegram replies)
