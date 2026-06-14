---
title: Master Plan: Migrate aiogram 2 formatting to aiogram 3 (Text, Pre)
date: 2026-06-13
category: docs/plans/
module: iacecil
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, refactor, formatting, migration]
---

# Master Plan: Migrate aiogram 2 formatting to aiogram 3

## Problem
Multiple files in the project use legacy aiogram 2.x formatting utilities (`escape_md`, `pre`, `code`, `bold`, `italic`, `link`) from `aiogram.utils.markdown`. Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module (specifically the `Text` class and its components like `Pre`, `Code`, `Bold`, etc.) to construct and render formatted messages via `.as_markdown()`.

## Requirements
- R1. Remove usage of legacy `aiogram.utils.markdown` functions.
- R2. Replace them with the `Text` class and appropriate components from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (MarkdownV2).
- R4. Interfere the least possible with existing code structures (e.g., preserve list-based message assembly or f-strings where possible).

---

## Scope Boundaries

- This plan focuses strictly on **text formatting migration**.
- It does **not** cover other aiogram 3 breaking changes (signatures, dispatcher changes, etc.).
- Target files: All files in `src/` currently using `aiogram.utils.markdown`.

---

## Context & Research

### Relevant Code and Patterns
- Common patterns:
    - `text.append(pre(json_data))` -> `text.append(Pre(json_data, language="").as_markdown())`
    - `escape_md(text)` -> `Text(text).as_markdown()`
    - `f"Hello {escape_md(name)}"` -> `f"Hello {Text(name).as_markdown()}"`

### Key Technical Decisions
- **Decision:** Use `.as_markdown()` on individual components or `Text` objects to fit into existing string-joining logic.
  **Rationale:** Minimizes structural refactoring of functions that build messages incrementally.
- **Decision:** Use empty `language=""` for `Pre` blocks to match the behavior of the legacy `pre()` function unless a language was explicitly used.

---

## Implementation Units

- U1. **Core Controllers Migration**
    - `src/iacecil/controllers/log.py` (Completed)

- U2. **Plugins Migration**
    - `src/plugins/garimpo.py` (Completed)
    - `src/plugins/ytdl.py` (Pending)
    - `src/plugins/welcome.py` (Pending)
    - `src/plugins/tts.py` (Pending)
    - `src/plugins/qr.py` (Pending)
    - `src/plugins/portaria.py` (Pending)
    - `src/plugins/hashes.py` (Pending)
    - `src/plugins/feedback.py` (Pending)
    - `src/plugins/donate.py` (Pending)
    - `src/plugins/web3_wrapper/eth_handlers.py` (Pending)
    - `src/plugins/web3_wrapper/bsc_handlers.py` (Pending)

- U3. **Personalidades Migration**
    - `src/iacecil/controllers/personalidades/pave/random_texts.py` (Pending)
    - `src/iacecil/controllers/personalidades/pacume/__init__.py` (Pending)

**Approach per file:**
1. Identify all `aiogram.utils.markdown` imports.
2. Replace with corresponding `aiogram.utils.formatting` classes.
3. Surgical replacement of function calls with `.as_markdown()` equivalents.
4. Verify syntax with `python -m py_compile`.

---

## System-Wide Impact
- **Unchanged invariants:** Message formatting sent to Telegram remains MarkdownV2.
- **Dependency:** Requires `aiogram >= 3.0.0` (already satisfied in Pipfile).

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Different escaping behavior in `Text` | `Text` implements standard MarkdownV2 escaping which is the target; verify with manual inspection of rendered output if possible. |
