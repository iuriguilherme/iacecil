---
title: "Aiogram 3 Bot Connector and Dispatcher Migration"
date: 2026-06-14
category: docs/solutions/integration-issues
module: src/iacecil/controllers/aiogram_bot
problem_type: integration_issue
component: assistant
symptoms:
  - "AttributeError: 'Dispatcher' object has no attribute 'register_message_handler'"
  - "ImportError: legacy exceptions like 'BotKicked' or 'ChatNotFound' missing"
  - "TypeError: start_polling() missing 1 required positional argument: 'bot'"
root_cause: wrong_api
resolution_type: migration
severity: high
tags:
  - aiogram-3
  - migration
  - dispatcher
  - exceptions
---

# Aiogram 3 Bot Connector and Dispatcher Migration

## Problem
The core `ia.cecil` bot connector crashed on startup under aiogram 3 because legacy v2 methods (e.g., `register_message_handler`, `Dispatcher(bot)`, specific exceptions) were entirely removed. The framework required a strict syntax migration to maintain existing error recovery and message handling behaviors.

## Symptoms
- `AttributeError: 'Dispatcher' object has no attribute 'register_message_handler'` when loading plugins.
- `ImportError` and `AttributeError` for legacy exceptions like `BotKicked`, `BotBlocked`, `ChatNotFound`, and `MessageToReplyNotFound`.
- Polling failed due to asynchronous signature changes for `start_polling` and `stop_polling`.

## What Didn't Work
- Attempting to import legacy exceptions directly from `aiogram.exceptions` fails as they have been consolidated into unified HTTP-status-based exception classes.
- Passing `bot` directly to `Dispatcher(bot)` raises a `TypeError` in v3, as the dispatcher is now independent of the bot instance.

## Solution
We systematically migrated the Telegram connector and the core aiogram startup logic to v3 patterns without losing functionality:

1. **Exception Mapping (`bot.py`)**:
   - Replaced `BotKicked`, `BotBlocked`, and `UserDeactivated` with `TelegramForbiddenError`. We preserved the distinct callback behaviors by using string matching on `exception.message` (e.g., `if "kicked" in exception.message.lower():`).
   - Replaced `ChatNotFound` and `MessageToReplyNotFound` with `TelegramNotFound`.
   - Updated flood control to use `TelegramRetryAfter` and read `.retry_after` instead of `.timeout`.

2. **Dispatcher Initialization (`__init__.py`)**:
   - Initialized `dispatcher = Dispatcher()` without the `bot` parameter.
   - Assigned the `bot` object to the dispatcher instance manually (`setattr(dispatcher, 'bot', bot)`) for backward compatibility with the project's internal runner.
   - Converted all handler registrations from `dispatcher.register_message_handler` to `dispatcher.message.register`.

3. **Telegram Connector Polling (`telegram.py`)**:
   - Explicitly dropped pending updates before polling via `await self.bot.delete_webhook(drop_pending_updates=True)`.
   - Updated the polling signature to `await self.dispatcher.start_polling(self.bot, polling_timeout=20, allowed_updates=None)`.
   - Updated disconnection logic to await the async `await self.dispatcher.stop_polling()`.

## Why This Works
Aiogram 3 separated the `Bot` instance from the `Dispatcher`, requiring the bot to be explicitly passed to `start_polling`. Exceptions were completely unified around standard Telegram API responses, meaning applications must now inspect `exception.message` to distinguish between sub-types of 403 or 404 errors. By adopting the new registration syntax (`dispatcher.message.register`), we align with the v3 architecture while retaining all legacy hook integration.

## Prevention
- Always consult the aiogram 3.x Migration Guide when interacting with framework APIs.
- Instead of catching `BotBlocked`, catch `TelegramForbiddenError` and inspect the message string.
- Ensure all handler registrations utilize `dispatcher.<event_type>.register(...)` or explicit `Router` components.

## Related Issues
- `docs/solutions/build-errors/aiogram-matrix-nio-dependency-conflict-2026-06-13.md`
- `docs/solutions/architecture-patterns/aiogram-handler-registration-order.md`