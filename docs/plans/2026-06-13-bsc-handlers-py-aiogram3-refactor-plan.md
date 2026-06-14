---
title: Refactor bsc_handlers.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil plugins web3_wrapper
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, plugins, web3, refactor, formatting]
---

# Refactor bsc_handlers.py for aiogram 3 formatting

## Problem
The file `src/plugins/web3_wrapper/bsc_handlers.py` currently uses `escape_md`, `bold`, `code`, and `spoiler` from `aiogram.utils.markdown`, which are aiogram 2.x paradigms. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module.

## Requirements
- R1. Remove usage of legacy `aiogram.utils.markdown` functions.
- R2. Replace them with the `Text`, `Bold`, `Code`, and `Spoiler` classes from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (MarkdownV2).
- R4. Interfere the least possible with the rest of the file's structure.

---

## Scope Boundaries

- Focuses strictly on `src/plugins/web3_wrapper/bsc_handlers.py`.
- Limited to `bcreate_callback` function formatting logic.

---

## Context & Research

### Relevant Code and Patterns
- Construction: `''.join([escape_md(...), bold(...), ...])`.
- We will replace each call with `.as_markdown()`.

### Key Technical Decisions
- **Decision:** Replace each component call with its `aiogram.utils.formatting` equivalent followed by `.as_markdown()`.

---

## Implementation Units

- U1. **Refactor bsc_handlers.py formatting**
    - Modify `src/plugins/web3_wrapper/bsc_handlers.py`.
    - Update imports: `from aiogram.utils.formatting import Text, Bold, Code, Spoiler`.
    - Replace calls on lines 129-137.

---

## System-Wide Impact
- **Unchanged invariants:** The account creation messages remain identical in appearance.
- **Dependency:** Requires `aiogram >= 3.0.0`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Spoiler syntax | Ensure `Spoiler` class renders to the correct `||...||` or HTML-style spoiler for MarkdownV2. |
