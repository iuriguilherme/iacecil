---
title: Refactor feedback.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil plugins
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, plugins, refactor, formatting]
---

# Refactor feedback.py for aiogram 3 formatting

## Problem
The file `src/plugins/feedback.py` currently uses `escape_md` from `aiogram.utils.markdown`, which is an aiogram 2.x paradigm. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module.

## Requirements
- R1. Remove usage of `escape_md` from `src/plugins/feedback.py`.
- R2. Replace it with the `Text` class from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (MarkdownV2).
- R4. Interfere the least possible with the rest of the file's structure.

---

## Scope Boundaries

- Focuses strictly on `src/plugins/feedback.py`.
- Limited to `feedback_callback` function formatting logic.

---

## Context & Research

### Relevant Code and Patterns
- `escape_md(u"...") + u"`...`"`.
- We will replace `escape_md` with `Text(...).as_markdown()`.

### Key Technical Decisions
- **Decision:** Replace `escape_md(text)` with `Text(text).as_markdown()`.

---

## Implementation Units

- U1. **Refactor feedback.py formatting**
    - Modify `src/plugins/feedback.py`.
    - Update imports: `from aiogram.utils.formatting import Text`.
    - Replace `escape_md` call on line 135.

---

## System-Wide Impact
- **Unchanged invariants:** The feedback help message sent back to users remains identical in appearance.
- **Dependency:** Requires `aiogram >= 3.0.0`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Multi-line string in `Text` | Ensure triple-quoted strings are handled correctly within `Text()`. |
