---
title: Refactor log.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil logging
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, logging, refactor, formatting]
---

# Refactor log.py for aiogram 3 formatting

## Problem
The file `src/iacecil/controllers/log.py` currently uses `escape_md` and `pre` from `aiogram.utils.markdown`, which are aiogram 2.x paradigms. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module (specifically the `Text` class and its components like `Pre` or `Code`) to construct and render formatted messages.

## Requirements
- R1. Remove usage of `escape_md` and `pre` from `src/iacecil/controllers/log.py`.
- R2. Replace them with the `Text` class and appropriate formatting components from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (e.g. escaping `#` for tags, pre-formatted JSON blocks).
- R4. Interfere the least possible with the rest of the file's structure.

---

## Scope Boundaries

- This plan strictly focuses on updating the text formatting in `log.py`. It does not attempt to fix other aiogram 3.x breaking changes (like `Dispatcher.get_current()`, or method signatures like `bot.send_message`), which will be handled in a broader aiogram 3 migration.
- Changes are limited to `debug_logger`, `exception_logger`, and `info_logger` functions in `src/iacecil/controllers/log.py`.

---

## Context & Research

### Relevant Code and Patterns
- `src/iacecil/controllers/log.py` assembles messages into a list of strings (`text.append(...)`) and joins them with `\n`.
- Aiogram 3 formatting documentation: https://docs.aiogram.dev/en/v3.28.2/utils/formatting.html
- The `Text` class takes multiple components and can render them via `.as_markdown()`.

### Key Technical Decisions
- **Decision:** Keep the `text.append()` list-of-strings structure.
  **Rationale:** The instruction is to interfere the least possible. Instead of rewriting the entire assembly to be a single `Text` object instantiation, we will append rendered strings or smaller `Text` objects rendered via `.as_markdown()` to the existing `text` list.
- **Decision:** Use `Text(..., " ", ...).as_markdown()` for inline escaping.
  **Rationale:** By passing raw strings to `Text`, they are automatically escaped when `.as_markdown()` is called. This perfectly replaces `escape_md(string)`.
- **Decision:** Use `Pre(json_string, language="").as_markdown()` for code blocks.
  **Rationale:** This replaces the old `pre(json_string)` function exactly.

---

## Implementation Units

- U1. **Refactor debug_logger, exception_logger, and info_logger formatting**

**Goal:** Update `src/iacecil/controllers/log.py` to use aiogram 3 formatting tools.

**Requirements:** R1, R2, R3, R4

**Dependencies:** None

**Files:**
- Modify: `src/iacecil/controllers/log.py`

**Approach:**
1. Update imports: Remove `escape_md`, `pre` from `aiogram.utils.markdown`. Add `Text`, `Pre` from `aiogram.utils.formatting`.
2. In `debug_logger`, `exception_logger`, and `info_logger`, replace `escape_md("#" + d)` with `Text("#" + d).as_markdown()`.
3. In `debug_logger`, `exception_logger`, and `info_logger`, replace `pre(json.dumps(...))` with `Pre(json.dumps(...)).as_markdown()`.
4. Leave the `text = list()` and `'\n'.join(text)` structure intact.

**Execution note:** Ensure `PIPENV_DONT_LOAD_ENV=1` is used if testing within pipenv due to the `.env` permission issue.

**Test scenarios:**
- Formatting path: The markdown text is successfully escaped and wrapped in pre blocks when the functions are called.

**Verification:**
- `log.py` imports `Text` and `Pre` from `aiogram.utils.formatting`.
- `escape_md` and `pre` are no longer in the file.
- The file passes syntax/import checks via python interpreter.

---

## System-Wide Impact
- **Unchanged invariants:** The overall message structure sent to the Telegram log channels remains the same. The rest of the legacy aiogram stack continues to function (or fail) exactly as before, as this is purely a formatting replacement step.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `as_markdown()` escapes characters differently than aiogram 2. | Rely on the `Text` class handling standard MarkdownV2 escaping properly, which is safer than manual escaping anyway. |
