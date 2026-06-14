---
title: Refactor ytdl.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil plugins
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, plugins, refactor, formatting]
---

# Refactor ytdl.py for aiogram 3 formatting

## Problem
The file `src/plugins/ytdl.py` currently uses `escape_md` and `pre` from `aiogram.utils.markdown`, which are aiogram 2.x paradigms. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module.

## Requirements
- R1. Remove usage of `escape_md` and `pre` from `src/plugins/ytdl.py`.
- R2. Replace them with the `Text` and `Pre` classes from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (MarkdownV2).
- R4. Interfere the least possible with the rest of the file's structure.

---

## Scope Boundaries

- Focuses strictly on `src/plugins/ytdl.py`.
- Limited to `ytdl` function formatting logic.

---

## Context & Research

### Relevant Code and Patterns
- Uses `+` to concatenate escaped markdown strings.
- Example: `escape_md(...) + pre(...)`.
- We will replace these with `.as_markdown()` calls.

### Key Technical Decisions
- **Decision:** Replace `escape_md(text)` with `Text(text).as_markdown()`.
- **Decision:** Replace `pre(text)` with `Pre(text, language="").as_markdown()`.

---

## Implementation Units

- U1. **Refactor ytdl.py formatting**
    - Modify `src/plugins/ytdl.py`.
    - Update imports: `from aiogram.utils.formatting import Text, Pre`.
    - Replace `escape_md` calls on lines 115, 152, and 158.
    - Replace `pre` calls on lines 116 and 157.

---

## System-Wide Impact
- **Unchanged invariants:** The messages sent back to users after YTDL operations remain identical in appearance.
- **Dependency:** Requires `aiogram >= 3.0.0`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| String interpolation in `Text` | Ensure `.format()` or f-strings are resolved correctly before or inside `Text()`. |
