# XMPP MUC Echo Support Plan

**Target repo:** iacecil
**Date:** 2026-06-16

## Problem Frame

The XMPP bot currently only responds to direct messages (`chat` or `normal` message types). The user wants the bot to support Multi-User Chat (MUC) chatrooms and run the `echo` plugin there, similar to how the Discord connector currently filters and replies in authorized channels. 

The `echo` plugin is already platform-agnostic (it registers a default envelope handler that echoes text). The issue is that the XMPP connector does not load the XEP-0045 plugin for MUC support, does not join configured channels, does not dispatch `groupchat` messages, and does not authorize or route messages back to MUCs correctly.

---

## Requirements

- R1. The XMPP connector must load the XEP-0045 (MUC) plugin upon connection.
- R2. The XMPP connector must automatically join the channels specified in its `channels` configuration list on session start.
- R3. The connector must dispatch incoming `groupchat` messages to the manager.
- R4. The connector must not dispatch its own messages in a groupchat (avoiding infinite echo loops).
- R5. The connector must restrict responses to DMs and explicitly authorized `channels` (same as Discord).
- R6. Outbound replies must use the correct message type (`groupchat` for chatrooms, `chat` for DMs).

---

## Scope Boundaries

- This plan only implements MUC support for the XMPP connector.
- Advanced MUC administration (kicking, banning, role management) is deferred to follow-up work.
- It relies on the existing default echo handler in `echo.py` without modifying it.

---

## Key Technical Decisions

- **XEP-0045 Registration:** `slixmpp` provides native MUC support via the `xep_0045` plugin. We will register it in `Connector.connect()`.
- **Authorization Check:** We will override `is_authorized()` in `xmpp.Connector`, mimicking the logic in `discord.py` so that only DMs and explicitly configured MUCs are allowed to process commands or echoes.
- **Message Type Routing:** We will inspect the incoming envelope's raw message type (`groupchat` vs `chat`) when sending a response in `Connector.send()`, ensuring the reply has the correct `mtype`.
- **Own Message Filtering:** In `groupchat`, our own messages appear with `msg['mucnick']` or `msg['from'].resource` matching the nickname we used to join. We will use `msg['from'].resource == self.boundjid.user` or the plugin's `ourNicks` dict to filter them.

---

## Implementation Units

- U1. **XMPP Connector MUC Support**

**Goal:** Allow XMPP connector to join MUCs, authorize channels, and dispatch/reply to `groupchat` messages.

**Requirements:** R1, R2, R3, R4, R5, R6

**Files:**
- Modify: `src/iacecil/connectors/xmpp.py`
- Test: `tests/test_xmpp.py`

**Approach:**
- In `Connector.connect()`, add `self.bot.register_plugin('xep_0045')`.
- In `XMPPBot.start()`, iterate over `self.connector.config.get('channels', [])` and call `self.plugin['xep_0045'].join_muc(room_jid, self.boundjid.user)`.
- In `XMPPBot.message()`, allow `msg['type'] in ('chat', 'normal', 'groupchat')`.
- Add own-message filtering for groupchats: `if msg['type'] == 'groupchat' and msg['from'].resource == self.boundjid.user: return`.
- In `Connector.send()`, determine outbound `mtype` from `envelope.raw['type']` if available, otherwise default to `'chat'`.
- Override `is_authorized(self, envelope: Envelope) -> bool` in `Connector`: if `envelope.raw['type'] != 'groupchat'`, return `True`. Otherwise, return `envelope.conversation_ref` is in configured channels.

**Patterns to follow:**
- `discord.py`'s `is_authorized` logic for channel filtering.

**Test scenarios:**
- Happy path: Bot receives `groupchat` message from another user -> dispatches Envelope with `platform='xmpp'`.
- Edge case: Bot receives `groupchat` message from itself (same nick) -> ignores it.
- Happy path: `Connector.is_authorized` returns True for DM.
- Happy path: `Connector.is_authorized` returns True for MUC listed in config.
- Error path: `Connector.is_authorized` returns False for MUC not listed in config.
- Happy path: `Connector.send` uses `mtype='groupchat'` when Envelope originates from a `groupchat` message.

**Verification:**
- XMPP connector connects, joins configured MUCs, and echoes messages from other users in those MUCs while ignoring its own messages and unauthorized MUCs.

---

## System-Wide Impact

- **Interaction graph:** Enhances the XMPP platform capabilities without altering the core envelope or manager flow.
- **Unchanged invariants:** `echo.py` and other plugins remain unaware of platform-specific message types; they just receive an `Envelope`.

---

## Operational Notes

- Operators will need to ensure their Slixmpp installation supports `xep_0045` (it does by default).
- Operators must list desired MUC JIDs in the `channels` list under the `xmpp` section of `instance/bots/<botname>.py`.
