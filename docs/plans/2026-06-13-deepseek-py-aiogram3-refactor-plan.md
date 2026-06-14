---
title: Refactor deepseek.py for aiogram 3
date: 2026-06-13
category: docs/plans/
module: iacecil plugins deepseek
problem_type: breaking_change
component: bot
severity: medium
tags: [aiogram, aiogram3, plugins, refactor, formatting, filters, deepseek]
---

# Refactor deepseek.py for aiogram 3

## Problem
The file `src/plugins/deepseek.py` uses legacy formatting (`italic`, `spoiler`) and a legacy filter parameter (`is_reply_to_id`). These need to be migrated to aiogram 3 paradigms.

## Requirements
- R1. Replace `italic` and `spoiler` with `Italic` and `Spoiler` from `aiogram.utils.formatting`.
- R2. Replace `is_reply_to_id = dispatcher.bot.id` with `IsReplyToIdFilter(is_reply_to_id = dispatcher.bot.id)`.
- R3. Maintain "thinking" block formatting behavior.
- R4. Maintain reply-to-bot behavior.

---

## Scope Boundaries

- Focuses strictly on `src/plugins/deepseek.py`.
- Limited to `deepseek_callback` and handler registration.

---

## Context & Research

### Relevant Code and Patterns
- Formatting: `spoiler(italic(''.join(think_buffer)))`.
- Filter: `@dispatcher.message_handler(is_reply_to_id = dispatcher.bot.id)`.

### Key Technical Decisions
- **Decision:** Use explicit `IsReplyToIdFilter` instance.
- **Decision:** Use `Spoiler(Italic(...)).as_markdown()`.

---

## Implementation Units

- U1. **Refactor deepseek.py**
    - Modify `src/plugins/deepseek.py`.
    - Update imports: `from aiogram.utils.formatting import Italic, Spoiler`.
    - Add import: `from iacecil.controllers.aiogram_bot.filters import IsReplyToIdFilter`.
    - Update lines 46-50, 93, and 105.

---

## System-Wide Impact
- **Unchanged invariants:** The bot continues to hide Deepseek thinking blocks and respond to replies.
- **Dependency:** Requires `aiogram >= 3.0.0` and refactored `filters.py`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Nested formatting | Verify that `Spoiler(Italic(...)).as_markdown()` produces valid MarkdownV2. |
