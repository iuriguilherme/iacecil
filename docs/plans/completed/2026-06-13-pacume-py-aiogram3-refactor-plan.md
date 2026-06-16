---
title: Refactor pacume/__init__.py for aiogram 3 (Formatting and Filters)
date: 2026-06-13
category: docs/plans/
module: iacecil personalidades
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, personalidades, refactor, formatting, filters]
---

# Refactor pacume/__init__.py for aiogram 3

## Problem
The file `src/iacecil/controllers/personalidades/pacume/__init__.py` contains an unused import of `escape_md` (aiogram 2 legacy) and uses keyword-based filters (`is_reply_to_id`) which are no longer supported in aiogram 3's dispatcher without global binding (which has been removed).

## Requirements
- R1. Remove unused `escape_md` import.
- R2. Import `IsReplyToIdFilter` from `iacecil.controllers.aiogram_bot.filters`.
- R3. Update all `@dispatcher.message_handler(is_reply_to_id=...)` calls to use explicit `IsReplyToIdFilter` instances.
- R4. Maintain existing functionality of the "pacume" (Tiozão do Churrasco) personality.

---

## Scope Boundaries

- Focuses strictly on `src/iacecil/controllers/personalidades/pacume/__init__.py`.
- Migration of `random_texts.py` (formatting) is acknowledged but handled as a separate step or part of the broader U3 Master Plan unit.

---

## Context & Research

### Relevant Code and Patterns
- `src/iacecil/controllers/personalidades/pacume/__init__.py` uses `is_reply_to_id = dispatcher.bot.id` in two handler decorators.
- It imports `escape_md` but never calls it in active code.

### Key Technical Decisions
- **Decision:** Remove the unused `escape_md` import instead of replacing it with `Text`.
  **Rationale:** Since it's unused, removal is cleaner and fulfills the "least possible interference" requirement.
- **Decision:** Use explicit `IsReplyToIdFilter` for handlers.
  **Rationale:** Necessary for aiogram 3 compatibility after `filters_factory.bind` removal.

---

## Implementation Units

- U1. **Refactor pacume/__init__.py**
    - Modify `src/iacecil/controllers/personalidades/pacume/__init__.py`.
    - Remove `from aiogram.utils.markdown import escape_md`.
    - Add `from ...aiogram_bot.filters import IsReplyToIdFilter`.
    - Update handlers on lines 150 and 212 to use `IsReplyToIdFilter(is_reply_to_id = dispatcher.bot.id)`.

**Execution note:** Ensure `PIPENV_DONT_LOAD_ENV=1` is used if testing.

---

## System-Wide Impact
- **Unchanged invariants:** The personality's aggressive behavior and response logic remain identical.
- **Dependency:** Requires `aiogram >= 3.0.0` and the already refactored `filters.py`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Circular import | `...aiogram_bot.filters` import should be safe as it's a sibling/parent relative import. |
