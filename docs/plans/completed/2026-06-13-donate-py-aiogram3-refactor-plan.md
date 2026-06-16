---
title: Refactor donate.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil plugins
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, plugins, refactor, formatting]
---

# Refactor donate.py for aiogram 3 formatting

## Problem
The file `src/plugins/donate.py` currently uses `escape_md` and `code` from `aiogram.utils.markdown`, which are aiogram 2.x paradigms. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module.

## Requirements
- R1. Remove usage of `escape_md` and `code` from `src/plugins/donate.py`.
- R2. Replace them with the `Text` and `Code` classes from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (MarkdownV2).
- R4. Interfere the least possible with the rest of the file's structure.

---

## Scope Boundaries

- Focuses strictly on `src/plugins/donate.py`.
- Limited to `donate_callback` function formatting logic.

---

## Context & Research

### Relevant Code and Patterns
- Uses `join` to construct lines: `''.join([f'{k}', escape_md(': '), code(f'{v}')])`.
- We will replace these with `.as_markdown()` calls.

### Key Technical Decisions
- **Decision:** Replace `escape_md(': ')` with `Text(': ').as_markdown()`.
- **Decision:** Replace `code(f'{v}')` with `Code(v).as_markdown()`.

---

## Implementation Units

- U1. **Refactor donate.py formatting**
    - Modify `src/plugins/donate.py`.
    - Update imports: `from aiogram.utils.formatting import Text, Code`.
    - Replace `escape_md` and `code` calls on line 46.

---

## System-Wide Impact
- **Unchanged invariants:** The donation addresses sent back to users remain identical in appearance.
- **Dependency:** Requires `aiogram >= 3.0.0`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| String interpolation in `Text`/`Code` | Ensure values are handled correctly as positional arguments. |
