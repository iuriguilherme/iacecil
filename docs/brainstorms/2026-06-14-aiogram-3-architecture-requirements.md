---
date: 2026-06-14
topic: aiogram-3-architecture-v3
---

# Requirements: Aiogram 3 "Telegram V3" Architecture

## Summary

This document defines the requirements for a new aiogram 3 architecture for the `ia.cecil` Telegram connector, focusing on dependency injection, multibot support via long polling, and strict backward compatibility via the Strangler Fig pattern.

---

## Problem Frame

The migration to aiogram 3 removed `Dispatcher.get_current()`, breaking the existing bot's ability to access shared resources (config, manager) within handlers and utility functions. A new architecture is needed that follows aiogram 3's explicit dependency injection model while supporting multiple bot instances polling concurrently. This new system must be built parallel to the old one to avoid any regressions or breakage in the legacy code.

---

## Requirements

**Migration & Compatibility**
- R1. **Strangler Fig Pattern**: The new implementation MUST co-exist with the old one. Existing files under `src/iacecil/controllers/aiogram_bot/` and `src/iacecil/connectors/telegram.py` MUST NOT be modified or deleted.
- R2. **Isolated Namespaces**: New code MUST live in `src/iacecil/controllers/aiogram_v3/` and `src/iacecil/connectors/telegram_v3.py`.
- R3. **New Bot Class**: A new `IACecilBotV3` class MUST be created for all aiogram 3 specific logic.

**Core Functionality**
- R4. **Dependency Injection**: `ConnectorManager` and `BotConfig` MUST be injected into handlers using aiogram 3 middlewares or magic data.
- R5. **Polling over Webhooks**: Long polling MUST be the primary supported multibot mechanism, though the system MUST be architected to allow webhooks as a future configuration option.
- R6. **Configurable Connectivity**: The choice between polling and webhooks MUST be a configuration setting.

**Integration**
- R7. **Plugin Entry Point**: A new `add_handlers_v3` entry point MUST be supported in plugins for aiogram 3 `Router` registration.
- R8. **Safe Shared Modification**: Changes to `src/iacecil/views/quart_app/__init__.py` MUST keep old logic commented out to support concurrent development.

---

## Success Criteria

- Successful concurrent polling of multiple Telegram bots using aiogram 3.
- Complete removal of `Dispatcher.get_current()` in the new code path.
- Existing legacy bot continues to function exactly as before.

---

## Scope Boundaries

- **Deferred**: Production-ready webhook server.
- **Outside Identity**: Refactoring the legacy `IACecilBot` class.
- **Out of Scope**: Migrating all existing plugins in this single task.
