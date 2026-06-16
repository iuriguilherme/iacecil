---
title: Refactor garimpo.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil plugins
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, plugins, refactor, formatting]
---

# Refactor garimpo.py for aiogram 3 formatting

## Problem
The file `src/plugins/garimpo.py` currently uses `escape_md` from `aiogram.utils.markdown`, which is an aiogram 2.x paradigm. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module (specifically the `Text` class) to construct and render formatted messages.

## Requirements
- R1. Remove usage of `escape_md` from `src/plugins/garimpo.py`.
- R2. Replace it with the `Text` class from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior.
- R4. Interfere the least possible with the rest of the file's structure.

---

## Scope Boundaries

- This plan strictly focuses on updating the text formatting in `garimpo.py`.
- Changes are limited to `forward_reply_callback` function in `src/plugins/garimpo.py`.

---

## Context & Research

### Relevant Code and Patterns
- `src/plugins/garimpo.py` uses f-strings with `escape_md` for message text: `text = f"\n{message.from_user.first_name} disse: {escape_md(message.text)}"`
- The `Text` class can render strings via `.as_markdown()`.

### Key Technical Decisions
- **Decision:** Replace `escape_md(message.text)` with `Text(message.text).as_markdown()`.
  **Rationale:** This is the direct equivalent in aiogram 3 for escaping raw text for MarkdownV2.
- **Decision:** Keep the f-string for the overall message assembly.
  **Rationale:** Minimal interference. Since `message.from_user.first_name` is also a raw string that might need escaping, it's safer to use `Text` for the whole line or parts of it. However, the user-provided `message.text` is the main target for escaping.

---

## Implementation Units

- U1. **Refactor forward_reply_callback formatting**

**Goal:** Update `src/plugins/garimpo.py` to use aiogram 3 formatting tools.

**Requirements:** R1, R2, R3, R4

**Dependencies:** None

**Files:**
- Modify: `src/plugins/garimpo.py`

**Approach:**
1. Update imports: Remove `escape_md` from `aiogram.utils.markdown`. Add `Text` from `aiogram.utils.formatting`.
2. In `forward_reply_callback`, replace `{escape_md(message.text)}` with `{Text(message.text).as_markdown()}`.
3. Consider if `{message.from_user.first_name}` also needs `Text(...).as_markdown()`. Yes, for consistency and safety.

**Execution note:** Ensure `PIPENV_DONT_LOAD_ENV=1` is used if testing within pipenv due to the `.env` permission issue.

**Test scenarios:**
- Formatting path: The markdown text is successfully escaped when the function is called.

**Verification:**
- `garimpo.py` imports `Text` from `aiogram.utils.formatting`.
- `escape_md` is no longer in the file.
- The file passes syntax/import checks via python interpreter.
