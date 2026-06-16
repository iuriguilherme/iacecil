---
date: 2026-06-14
topic: aiogram-3-architecture-v3
---

# Implementation Plan: Aiogram 3 "Telegram V3" Architecture

## Summary

This plan outlines the "Telegram V3" architecture for `ia.cecil`, migrating to aiogram 3 while following the Strangler Fig pattern. It implements a `ContextMiddleware` for dependency injection, replaces global state (`Dispatcher.get_current()`), supports configurable multibot polling, and introduces a new bot class to ensure the new path is idiomatic while leaving legacy files unchanged.

---

## Problem Frame

The project's migration to aiogram 3 resulted in broken code due to the removal of `Dispatcher.get_current()`. Several plugins and core callbacks are now failing. We need an idiomatic aiogram 3 architecture that supports the project's requirement for multiple bots via long polling. Due to the Python package namespace conflict (aiogram 2 and 3 both use the `aiogram` package), we assume aiogram 3 is the primary library version and the legacy code path remains in place primarily for reference and "commented-out" safety as requested, acknowledging it may not be functional until its imports/methods are fixed.

---

## Requirements

**Architecture & Isolation**
- R1. **Isolation**: The new architecture MUST be implemented in new files/directories (e.g., `src/iacecil/connectors/telegram_v3.py`, `src/iacecil/controllers/aiogram_v3/`).
- R2. **New Bot Class**: A new bot class (e.g., `IACecilBotV3`) MUST be created to handle aiogram 3 specifics, leaving the legacy `IACecilBot` unchanged.
- R3. **Functional Namespaces**: Prefer descriptive naming (e.g., `aiogram_v3` or `modern`) over hardcoded version suffixes where possible, though `v3` is used here for clarity during migration.

**Features & Integration**
- R4. **Dependency Injection**: Use aiogram 3 middlewares to inject `manager` and `bot_config` into handler context (data dictionary).
- R5. **Configurable Connectivity**: Add a configuration flag to choose between long polling and webhooks (no server implementation in this phase).
- R6. **Plugin Compatibility**: Update the plugin loader to support `add_handlers_v3(router: Router)`.
- R7. **Registry Arbitration**: The `ConnectorManager` MUST exclude both `telegram` and `telegram_v3` platforms from generic command registry dispatch to prevent duplicate responses.

**Process & Transition**
- R8. **Preserve Legacy**: Shared files (like `quart_app/__init__.py`) must keep legacy logic commented out for other agents, even if it is currently non-functional under aiogram 3.

---

## Scope Boundaries

- **Deferred**: Webhook server implementation (configuration flag only).
- **Deferred**: Full migration of all 20+ plugins (only proof-of-concept/priority plugins first).
- **Explicit Non-Goal**: Modifying `src/iacecil/controllers/aiogram_bot/` or `src/iacecil/connectors/telegram.py`.
- **Constraint**: Simultaneous runtime coexistence of aiogram 2 and 3 libraries is not supported due to namespace conflict.

---

## Context & Research

### Relevant Code and Patterns

- `src/iacecil/connectors/base.py`: The `BaseConnector` interface to follow.
- `src/iacecil/controllers/aiogram_bot/bot.py`: The exception handling logic to reimplement in the new bot class.
- `src/iacecil/controllers/aiogram_bot/callbacks.py`: The logic to refactor away from `Dispatcher.get_current()`.

---

## Key Technical Decisions

- **Middleware-based DI**: Use a global middleware to pass the manager/config, ensuring all handlers (even in nested routers) have context via the `data` dictionary.
- **Context Accessor for Utilities**: Implement a thin global registry or `ContextVar` to allow utility functions (like logging) to safely access the active `ConnectorManager` when running within a handler task.
- **Strangler Fig Implementation**: Create `telegram_v3.py` as an opt-in connector.
- **Dispatcher/Bot Relationship**: Use a single Dispatcher where possible, or isolated Dispatcher/Bot pairs if needed for strict configuration separation, managed via the `ConnectorManager`.

---

## Implementation Units

- U1. **Core Controller V3 Setup**
  - **Goal**: Create the `aiogram_v3` controller namespace with the new bot class, exception parity, and DI middleware.
  - **Files**:
    - Create: `src/iacecil/controllers/aiogram_v3/__init__.py`
    - Create: `src/iacecil/controllers/aiogram_v3/bot.py`
    - Create: `src/iacecil/controllers/aiogram_v3/middlewares.py`
    - Create: `src/iacecil/controllers/aiogram_v3/callbacks.py` (Refactored from legacy)
  - **Tasks**:
    - Implement `IACecilBotV3` with ported flood control and exception handling logic (mapping to aiogram 3 exception types).
    - Implement `ContextMiddleware` injecting `manager` and `bot_config`.
  - **Test**: `tests/test_aiogram_v3_core.py`

- U2. **Telegram V3 Connector**
  - **Goal**: Implement the new `telegram_v3` connector using the modern architecture.
  - **Files**:
    - Create: `src/iacecil/connectors/telegram_v3.py`
  - **Test**: `tests/test_telegram_v3_connector.py`

- U3. **Connector Manager & Plugin Loader Update**
  - **Goal**: Update `load_plugin` to support `add_handlers_v3` and fix arbitration.
  - **Files**:
    - Modify: `src/iacecil/connectors/__init__.py`
  - **Tasks**:
    - Update `load_plugin` to pass the connector's `Router` when `add_handlers_v3` is detected.
    - Exclude `telegram_v3` from generic command dispatch.

- U4. **Quart Integration (Safe Update)**
  - **Goal**: Integrate V3 into the Quart startup while preserving legacy code as comments.
  - **Files**:
    - Modify: `src/iacecil/views/quart_app/__init__.py`
  - **Execution note**: Keep old `quart_before_serving` logic commented out as requested.

---

## System-Wide Impact

- **Integration coverage**: Ensure that messages sent via Telegram V3 are correctly persisted to ZODB and chat stores via the `ConnectorManager`.
- **Unchanged invariants**: Legacy files remain present but may be non-functional due to the library version upgrade.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Namespace Conflict | Explicitly document that legacy code is "frozen" and likely broken until individual files are fixed or migrated. |
| Multi-bot resource usage | Monitor event loop latency under load with multiple polling tasks. |
| Middleware performance | Minimize logic in the global middleware. |

---

## Sources & References

- **Origin document**: [docs/brainstorms/2026-06-14-aiogram-3-architecture-requirements.md](docs/brainstorms/2026-06-14-aiogram-3-architecture-requirements.md)
