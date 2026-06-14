---
title: Migrate Telegram Connector and Aiogram Controller to aiogram 3
date: 2026-06-13
category: docs/plans/
module: iacecil connectors telegram, iacecil controllers aiogram_bot
problem_type: breaking_change
component: bot
severity: high
tags: [aiogram, aiogram3, telegram, migration, refactor]
---

# Migrate Telegram Connector and Aiogram Controller to aiogram 3

## Problem
The ia.cecil project has been updated to use `aiogram 3.x`, but several core components still use aiogram 2.x patterns, specifically:
1. `Dispatcher(bot)` constructor (removed in v3).
2. `Dispatcher.start_polling` signature and parameters (changed in v3).
3. `Dispatcher.stop_polling` is now an asynchronous method.
4. Legacy handler registration methods (e.g., `register_message_handler`) are removed or renamed.
5. `IACecilBot` inheritance and internal attribute setting may conflict with v3 `Bot` internals.

## Requirements
- R1. Modernize `src/iacecil/connectors/telegram.py` to use aiogram 3 `Dispatcher` and `start_polling` patterns.
- R2. Modernize `src/iacecil/controllers/aiogram_bot/__init__.py` to use aiogram 3 `Dispatcher` and handler registration.
- R3. Ensure `IACecilBot` in `src/iacecil/controllers/aiogram_bot/bot.py` is compatible with aiogram 3.
- R4. Maintain existing behavior: long-polling, webhook resetting, and custom exception handling.

---

## Scope Boundaries

- Focuses on `src/iacecil/connectors/telegram.py` and `src/iacecil/controllers/aiogram_bot/`.
- Does NOT include migrating individual plugin handlers (those will be handled in separate plans if needed, though Unit 5 covers the core registration logic).
- Limited to restoring Telegram bot functionality.

---

## Context & Research

### Relevant Code and Patterns
- `aiogram 3` Dispatcher: `dp = Dispatcher()`.
- `aiogram 3` Polling: `await dp.start_polling(bot, ...)`.
- `aiogram 3` Handlers: `dp.message.register(handler, ...)` or `@dp.message(...)`.

### Institutional Learnings
- We recently resolved the `aiohttp` dependency conflict that allowed installing `aiogram 3.28.2`.

---

## Key Technical Decisions
- **Decision:** Initialize `Dispatcher` without a bot instance globally and pass the bot instance only at polling/execution time.
- **Decision:** Replace `register_message_handler` calls with the new aiogram 3 equivalents (`message.register`, `edited_message.register`, etc.).
- **Decision:** Call `bot.delete_webhook(drop_pending_updates=True)` explicitly before starting polling to mimic aiogram 2's `reset_webhook=True` behavior.

---

## Implementation Units

- U1. **Refactor IACecilBot for aiogram 3 compatibility**
    - Modify `src/iacecil/controllers/aiogram_bot/bot.py`.
    - Verify `super().__init__` call and attribute setting.
    - Update exception types if needed (e.g., `TelegramForbiddenError`).

- U2. **Modernize aiogram_bot controller core**
    - Modify `src/iacecil/controllers/aiogram_bot/__init__.py`.
    - Update `aiogram_startup` to initialize `Dispatcher()` without bot.
    - Replace all `register_*_handler` methods with v3 equivalents (e.g., `dispatcher.message.register`).
    - Remove or update references to `dispatcher.filters_factory` (done in previous turn, but ensure consistency).

- U3. **Modernize Telegram Connector**
    - Modify `src/iacecil/connectors/telegram.py`.
    - Update `connect()`: `self.dispatcher = Dispatcher()`.
    - Update `listen()`: `await self.bot.delete_webhook(drop_pending_updates=True)` then `await self.dispatcher.start_polling(self.bot, ...)`.
    - Update `disconnect()`: `await self.dispatcher.stop_polling()`.

---

## System-Wide Impact
- Restores Telegram bot functionality which is currently broken due to constructor mismatches.
- Affects how all bots are initialized and how their handlers are registered.
- **Integration coverage:** Cross-layer check that `aiogram_startup` return values are still compatible with the rest of the runner logic.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Handler signature changes | Verify if handler arguments (message, state, etc.) changed in v3. |
| Middleware changes | Check if the project uses middlewares that need migration. |
| Dependency on IACecilBot internals | Keep IACecilBot as slim as possible to avoid internal conflicts. |

---

## Documentation / Operational Notes
- This is a breaking change at the code level but preserves user-facing behavior.

---

## Sources & References
- aiogram 3 official documentation and migration guides.
