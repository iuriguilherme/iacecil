# Discord Connector Integration & Echo Plugin Verification Plan

## Problem Frame
The Discord connector is implemented but its integration with the `echo` plugin and the `connectors_v3` runner is unverified. Current implementation hardcodes response logic ("addressed to bot") in the connector, violating the separation of concerns where plugins should decide what to answer.

### Scope boundary
- **Goals:** 
  - Fix Discord connector to correctly route messages to `ConnectorManager`.
  - Ensure `echo` plugin works via `add_envelope_handlers`.
  - Delegate authorization (which channels to answer) to the config/handler layer.
  - Document configuration for production (Docker/connectors_v3).
  - Verify with unit tests and live smoke test.
- **Non-goals:**
  - Renaming `connectors_v3` back to `connectors`.
  - Implementing full command support if not required for echo.

## Requirements
- R1. `echo` plugin replies to DMs.
- R2. `echo` plugin replies to authorized guild channels.
- R3. Bot observes and persists ALL messages (authorized or not) without replying to unauthorized ones.
- R4. Authorization mechanism is configurable and delegated (Telegram-style).
- R5. Document production setup (tokens, intents, server auth).
- R6. Preserve connector isolation and Telegram arbitration.

## Context & Research
### Relevant Code and Patterns
- `src/iacecil/connectors/discord.py`: Existing connector.
- `src/iacecil/connectors/__init__.py`: `ConnectorManager` and plugin loading logic.
- `src/plugins/echo.py`: Generic `add_envelope_handlers` implementation.
- `instance/bots/default.py`: Config structure (Discord section).

### Institutional Learnings
- Discord requires `intents.message_content` to see text.
- Separation of observation (persistence) and response (plugin logic) is required.

## Key Technical Decisions
- **Decision 1: Authorization Mechanism**: Use a `channels` list in the `discord` config section (similar to Telegram's `users` lists) to define which channels are "authorized" for responding.
- **Decision 2: Remove Hardcoded Gate**: Remove `_addressed_to_bot` check from `discord.py` to allow all messages to reach `ConnectorManager` for persistence.
- **Decision 3: Handler-Side Filtering**: Modify `echo_envelope` or `ConnectorManager.dispatch` to respect authorization. Since `echo_envelope` is generic, I'll add a check in `ConnectorManager.dispatch` that queries the connector for authorization before calling the handler.

## Implementation Units
- U1. **Fix Discord Connector (Observation)**
  - **Goal:** Ensure every message is dispatched to the manager regardless of "addressed to bot".
  - **Files:** Modify `src/iacecil/connectors/discord.py`.
  - **Approach:** 
    - Remove `_addressed_to_bot` call in `_on_message`.
    - Implement `is_authorized(envelope)` method in `Connector` class that checks `self.config.get('channels')`.
  - **Test scenarios:** Mock `on_message` with various guild/DM messages, verify `manager.dispatch` is called.

- U2. **Implement Authorization Gating in Dispatcher**
  - **Goal:** Only reply in authorized channels or DMs.
  - **Files:** Modify `src/iacecil/connectors/__init__.py`.
  - **Approach:** 
    - In `dispatch()`, after persistence, check if `connector.is_authorized(envelope)` before executing the handler.
    - Ensure DMs are always authorized by default (per requirements).

- U3. **Configuration Update**
  - **Goal:** Update `DefaultBotConfig` and examples.
  - **Files:** `src/iacecil/config.py` (only if safe, otherwise `instance/bots/default.py` for local testing). *Note: Requirements say DO NOT edit `src/iacecil/config.py` defaults.*
  - **Correction:** I will document the need for `channels` list in `instance/bots/<name>.py`.

- U4. **Documentation**
  - **Goal:** Document production setup.
  - **Files:** Create `docs/connectors/discord.md`.

## Test Scenarios
- **Unit Test (DM):** Mock Discord DM -> Verify persistence -> Verify Echo reply.
- **Unit Test (Authorized Guild Channel):** Mock Authorized Channel message -> Verify persistence -> Verify Echo reply.
- **Unit Test (Unauthorized Guild Channel):** Mock Unauthorized Channel message -> Verify persistence -> Verify NO Echo reply (but verify persistence).

## Risks & Dependencies
- **Risk:** Discord API changes or rate limits.
- **Dependency:** Real Discord token for live verification.
- **Dependency:** `discord.py` installed.
