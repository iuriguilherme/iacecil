---
title: Refactor pave filters for aiogram 3
date: 2026-06-13
category: docs/plans/
module: iacecil personalidades pave
problem_type: breaking_change
component: bot
severity: medium
tags: [aiogram, aiogram3, personalidades, refactor, filters, pave]
---

# Refactor pave filters for aiogram 3

## Problem
The file `src/iacecil/controllers/personalidades/pave/__init__.py` uses the `is_reply_to_id` parameter directly in a message handler decorator. In aiogram 3, global filter factory parameters like this have been removed in favor of explicit filter instances.

## Requirements
- R1. Import `IsReplyToIdFilter` from `iacecil.controllers.aiogram_bot.filters`.
- R2. Replace `is_reply_to_id = dispatcher.bot.id` with `IsReplyToIdFilter(is_reply_to_id = dispatcher.bot.id)`.
- R3. Maintain existing handler behavior (responding to replies to the bot).

---

## Scope Boundaries

- Focuses strictly on `src/iacecil/controllers/personalidades/pave/__init__.py`.
- Limited to filter registration logic.

---

## Context & Research

### Relevant Code and Patterns
- Current: `@dispatcher.message_handler(is_reply_to_id = dispatcher.bot.id)`.
- We have already refactored `IsReplyToIdFilter` to inherit from `BaseFilter`.

### Key Technical Decisions
- **Decision:** Use explicit filter instance in the decorator.

---

## Implementation Units

- U1. **Refactor pave filters**
    - Modify `src/iacecil/controllers/personalidades/pave/__init__.py`.
    - Add import: `from ...aiogram_bot.filters import IsReplyToIdFilter`.
    - Update line 176.

---

## System-Wide Impact
- **Unchanged invariants:** The bot continues to respond with "patadas" (rude responses) when someone replies to its messages.
- **Dependency:** Requires `aiogram >= 3.0.0` and the refactored `filters.py`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Import path | Ensure relative import `...aiogram_bot.filters` is correct for the directory structure. |
