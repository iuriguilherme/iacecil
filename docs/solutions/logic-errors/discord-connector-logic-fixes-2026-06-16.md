---
title: "Discord connector logic fixes: NameError in dispatch, hardcoded gating, and DM detection"
date: 2026-06-16
category: docs/solutions/logic-errors
module: src/iacecil/connectors
problem_type: logic_error
component: service_object
severity: high
symptoms:
  - "NameError: name 'connector' is not defined in ConnectorManager.dispatch"
  - "Discord response gating prevented message persistence for non-replies"
  - "Incorrect DM detection logic using IDs instead of guild check"
  - "Discord bot token exposed in logs during test execution"
root_cause: logic_error
resolution_type: code_fix
tags:
  - discord
  - connector
  - dm-detection
  - security
  - variable-scope
---

# Discord connector logic fixes: NameError in dispatch, hardcoded gating, and DM detection

## Problem
The Discord connector integration suffered from three distinct logic issues: a crash in the dispatch loop, hardcoded response logic that prevented message persistence, and unreliable private message detection. Additionally, debugging these issues led to accidental exposure of the bot token in logs.

## Symptoms
- `NameError` when processing non-Telegram messages in `ConnectorManager.dispatch`.
- Bot failed to persist messages it wasn't explicitly "authorized" to reply to.
- Bot failed to respond to Direct Messages (DMs) because it couldn't reliably detect them.
- Discord token visible in stdout/logs during interactive testing sessions.

## What Didn't Work
- **ID-based DM Detection**: Comparing `envelope.conversation_ref == envelope.sender_ref` is unreliable for Discord, as DM channel IDs do not match User IDs.
- **Hardcoded Firehose Gating**: Filtering messages inside the connector (`_addressed_to_bot`) prevented persistence of unauthorized messages, violating the architecture requirement that every message must reach the neutral persistence layer.
- **Manual Live Testing with Tokens**: Running unvetted test scripts or logging raw configuration dictionaries exposed the Discord `token` in the console history.

## Solution
The fixes involved defining missing variables in the dispatch loop, delegating authorization to a new connector-level method, and using Discord-native attributes for DM detection.

### 1. Fix NameError in Dispatch
The `connector` variable was used before definition when processing messages from new platforms.

```python
## src/iacecil/connectors/__init__.py
async def dispatch(self, envelope):
    # ... imports ...
    platform = envelope.platform
    connector = self.connectors.get(platform)  # Added this definition
    # ... persistence ...
```

### 2. Native DM Detection
Used `message.guild` (via the `Envelope.raw` attribute) to detect DMs.

```python
## src/iacecil/connectors/discord.py
def is_authorized(self, envelope: Envelope) -> bool:
    message = envelope.raw
    if message is not None and getattr(message, 'guild', None) is None:
        return True  # DMs are always authorized
    authorized_channels = self.config.get('channels') or []
    return str(envelope.conversation_ref) in [str(c) for c in authorized_channels]
```

### 3. Separation of Persistence and Response
Moved the authorization check into `ConnectorManager.dispatch` so that all messages are persisted first, but only authorized ones trigger a response.

## Why This Works
- **`discord.py` Semantics**: The `guild` attribute of a `discord.Message` is `None` strictly if the message is a DM.
- **Architecure Alignment**: By separating observation (persistence) from response (gated by `is_authorized`), we ensure a complete neutral record of all bot traffic regardless of whether a plugin decides to act on it.

## Prevention
- **Privileged Intents**: Ensure `intents.message_content = True` is set in the code AND in the Discord Developer Portal, otherwise the bot receives empty message text.
- **Sanitized Logging**: Never log `self.config` or full configuration objects. Log only specific non-sensitive keys.
- **Use Established Runners**: Avoid custom test scripts for live verification. Use the project's production-ready runners (`uv run iacecil connectors_v3`) which have established log-masking and security patterns.

## Related Issues
- `docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md`
- `docs/solutions/architecture-patterns/connector-self-declared-activation.md`
