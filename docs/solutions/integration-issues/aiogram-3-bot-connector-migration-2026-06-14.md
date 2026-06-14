---
title: "Aiogram 3 Bot Connector and Dispatcher Migration"
date: 2026-06-14
last_updated: 2026-06-14
category: docs/solutions/integration-issues
module: src/iacecil/connectors/telegram_v3.py
problem_type: integration_issue
component: assistant
symptoms:
  - "AttributeError: 'Dispatcher' object has no attribute 'register_message_handler'"
  - "aiogram.exceptions.TelegramConflictError: Conflict: terminated by other getUpdates request"
  - "System hangs on shutdown/SIGINT when using Aiogram 3 polling"
  - "Dispatcher.get_current() removed in Aiogram 3 breaking context retrieval"
root_cause: wrong_api
resolution_type: migration
severity: high
tags:
  - aiogram-3
  - migration
  - dispatcher
  - arbitration
  - context-vars
---

# Aiogram 3 Bot Connector and Dispatcher Migration

## Problem
The migration of the `ia.cecil` Telegram bot framework from aiogram 2 to aiogram 3 introduced critical failures: legacy methods were removed, global state retrieval (`Dispatcher.get_current()`) was eliminated, and resource conflicts (token double-polling) caused startup crashes and shutdown hangs.

## Symptoms
- `AttributeError: 'Dispatcher' object has no attribute 'register_message_handler'` when loading plugins.
- `TelegramConflictError` when both legacy `telegram` and modern `telegram_v3` connectors attempted to poll simultaneously with the same token.
- Process hangs on shutdown (SIGINT) due to unhandled async `stop_polling()` and signal capture conflicts between multiple dispatchers.
- `AttributeError` when trying to set attributes (like `.bot`) on immutable Pydantic configuration objects.

## What Didn't Work
- **Direct serialization for ZODB**: Attempting to convert modern `Message` Pydantic models to `dict` for legacy persistence caused `AttributeError: 'dict' object has no attribute 'chat'` in downstream logic that expected a hybrid object.
- **Legacy Polling**: Using `start_polling()` with default signal handling in a multi-bot environment caused one dispatcher to "steal" signals, preventing others from stopping.

## Solution
We implemented a robust **Strangler Fig** migration architecture alongside core fixes for context and lifecycle management:

1. **Connector Arbitration (`ConnectorManager`)**:
   Implemented arbitration logic in `_load_connectors`. If `telegram_v3` is active, the system automatically suppresses the legacy `telegram` connector to prevent token conflicts and signal interference.

2. **Context Management (`ContextVars`)**:
   Replaced the removed `Dispatcher.get_current()` with a unified context retrieval utility (`get_aiogram_context`). It uses `ContextVars` populated by a modern `ContextMiddleware` to safely retrieve the `bot`, `dispatcher`, `manager`, and `config` in any async task.

3. **Graceful Shutdown**:
   - Configured `start_polling(handle_signals=False)` for all dispatchers to allow the process-level loop to manage signals.
   - Implemented explicit `await self.dispatcher.stop_polling()` in the connector `disconnect()` method.
   - Updated the runner to gather coroutines directly rather than creating detached tasks, ensuring cancellation propagates correctly on SIGINT.

4. **Pydantic Resilience**:
   Updated constructors (like `IACecilBotV3`) to safely handle both dictionary and Pydantic object inputs, using `getattr` and `hasattr` to avoid attribute errors when the configuration source varies.

5. **Exception Mapping**:
   Preserved distinct callback behaviors by catching unified exceptions like `TelegramForbiddenError` and performing string matching on `exception.message` (e.g., `"kicked"` or `"blocked"`).

## Why This Works
The Strangler Fig pattern allows the new architecture to coexist with the old one, providing a safe path for incremental plugin migration. `ContextVars` provide a thread-safe (and task-safe) way to restore the "current context" pattern without the downsides of global singletons. By disabling internal signal handling in aiogram, we return control to the application runner, which can then orchestrate a clean teardown of all active bot sessions.

## Prevention
- **Arbitration First**: When introducing a modern version of a legacy component, implement explicit arbitration in the loader to prevent resource collisions.
- **Task Gathering**: Prefer `asyncio.gather(*coroutines)` over `asyncio.create_task()` in top-level runners if you need signal cancellation to propagate.
- **Context Abstraction**: Use a central utility like `get_aiogram_context()` instead of accessing middleware data or global state directly; this decouples business logic from the underlying framework version.
- **Immutable Handling**: Always check if a configuration object is a Pydantic model before attempting `setattr`; prefer keeping the bot instance on the dispatcher or manager rather than the config object.

## Related Issues
- `docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md`
- `docs/solutions/architecture-patterns/aiogram-handler-registration-order.md`
- `docs/solutions/build-errors/aiogram-matrix-nio-dependency-conflict-2026-06-13.md`
