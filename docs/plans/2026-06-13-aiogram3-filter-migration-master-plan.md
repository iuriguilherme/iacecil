---
title: Master Plan: Migrate aiogram 2 filters to aiogram 3
date: 2026-06-13
category: docs/plans/
module: iacecil aiogram_bot
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, filters, migration, refactor]
---

# Master Plan: Migrate aiogram 2 filters to aiogram 3

## Problem
The project uses custom filters (`IsReplyToIdFilter`, `WhoJoinedFilter`) based on aiogram 2.x `BoundFilter` paradigms. In aiogram 3.x, `BoundFilter` and `filters_factory.bind` have been removed. Filters are now either standard `BaseFilter` subclasses (using `__call__`) or simple functions/lambdas. Handler registration also changed from positional/keyword magic to explicit filter objects.

## Requirements
- R1. Refactor `IsReplyToIdFilter` and `WhoJoinedFilter` in `src/iacecil/controllers/aiogram_bot/filters.py` to inherit from `aiogram.filters.BaseFilter`.
- R2. Update filter logic from `async def check(...)` to `async def __call__(self, event: types.TelegramObject, ...)` (usually `types.Message`).
- R3. Remove `dispatcher.filters_factory.bind` usage in `src/iacecil/controllers/aiogram_bot/__init__.py`.
- R4. Update all `@dispatcher.message_handler(is_reply_to_id=...)` calls to pass the filter object explicitly: `@dispatcher.message_handler(IsReplyToIdFilter(is_reply_to_id=...))`.
- R5. Maintain existing filtering behavior (reply-to ID check and unwanted member name check).

---

## Scope Boundaries

- This plan focuses strictly on **custom filter migration**.
- It does **not** cover standard aiogram filter changes (like `filters.IDFilter` which might need updating if they were positional before), except where they are found in the same files.
- It does **not** cover the full migration of `Dispatcher` or `message_handler` decorators (which will be a separate master plan), but it acknowledges that the syntax for passing filters to them has changed.

---

## Context & Research

### Relevant Code and Patterns
- `src/iacecil/controllers/aiogram_bot/filters.py`: Contains the `BoundFilter` classes.
- `src/iacecil/controllers/aiogram_bot/__init__.py`: Binds the filters.
- Usage points: `deepseek.py`, `tts.py`, `pave/__init__.py`, `pacume/__init__.py`, `portaria.py`.

### Key Technical Decisions
- **Decision:** Inherit from `BaseFilter` and implement `__call__`.
  **Rationale:** This is the canonical aiogram 3 way for class-based custom filters.
- **Decision:** Pass filter instances to handlers.
  **Rationale:** Since we can't "bind" them globally to keyword arguments anymore, we must instantiate them in the `@message_handler` decorator.

---

## Implementation Units

- U1. **Refactor custom filter classes**
    - Modify `src/iacecil/controllers/aiogram_bot/filters.py`.
    - Replace `BoundFilter` with `BaseFilter`.
    - Change `async def check(self, msg: types.Message)` to `async def __call__(self, message: types.Message) -> bool`.
    - Ensure imports are updated: `from aiogram.filters import BaseFilter`.

- U2. **Remove global binding**
    - Modify `src/iacecil/controllers/aiogram_bot/__init__.py`.
    - Delete `dispatcher.filters_factory.bind(...)` lines.

- U3. **Update handler usage**
    - Search for all keyword usage of `is_reply_to_id` and `unwanted` in handler decorators.
    - Replace with explicit class instantiation.
    - Example: `@dispatcher.message_handler(is_reply_to_id=X)` -> `@dispatcher.message_handler(IsReplyToIdFilter(is_reply_to_id=X))`.
    - Files:
        - `src/plugins/deepseek.py`
        - `src/plugins/tts.py`
        - `src/plugins/portaria.py`
        - `src/iacecil/controllers/personalidades/pave/__init__.py`
        - `src/iacecil/controllers/personalidades/pacume/__init__.py`

**Approach per file:**
1. Update imports if necessary.
2. Replace keyword filter argument with positional filter instance.
3. Verify syntax.

---

## System-Wide Impact
- **Unchanged invariants:** The logic for identifying "unwanted" users and "reply-to-me" messages remains identical.
- **Dependency:** Requires `aiogram >= 3.0.0`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `message_handler` decorator itself might fail before filters are reached | The broader migration to `router.message(...)` is related but we are trying to keep changes surgical. If `message_handler` is already broken, these changes will at least fix the filter part. |
| Event types in `__call__` | Use `types.Message` for these specific filters as they are currently message-only. |
