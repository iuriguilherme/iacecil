---
title: Refactor random_texts.py for aiogram 3 formatting
date: 2026-06-13
category: docs/plans/
module: iacecil personalidades pave
problem_type: best_practice
component: tooling
severity: low
tags: [aiogram, aiogram3, plugins, refactor, formatting, pave]
---

# Refactor random_texts.py for aiogram 3 formatting

## Problem
The file `src/iacecil/controllers/personalidades/pave/random_texts.py` uses `escape_md` from `aiogram.utils.markdown` extensively (over 30 times). Under aiogram 3.x, the recommended approach is to use the `aiogram.utils.formatting` module.

## Requirements
- R1. Remove usage of `escape_md` from `src/iacecil/controllers/personalidades/pave/random_texts.py`.
- R2. Replace all occurrences with the `Text` class from `aiogram.utils.formatting`.
- R3. Maintain the exact same output visual structure and behavior (MarkdownV2).
- R4. Perform the replacement efficiently (bulk replacement preferred).

---

## Scope Boundaries

- Focuses strictly on `src/iacecil/controllers/personalidades/pave/random_texts.py`.
- Limited to `biblia_sacra` function (and others if any) formatting logic.

---

## Context & Research

### Relevant Code and Patterns
- Many lines like: `verso = escape_md(u"""...""")` and `livro = escape_md(u"...")`.
- They are all inside dictionaries in a list.

### Key Technical Decisions
- **Decision:** Replace `escape_md(...)` with `Text(...).as_markdown()`.
- **Decision:** Use a single-pass replacement tool or multiple sequential edits if needed.

---

## Implementation Units

- U1. **Refactor random_texts.py formatting**
    - Modify `src/iacecil/controllers/personalidades/pave/random_texts.py`.
    - Update imports: `from aiogram.utils.formatting import Text`.
    - Bulk replace `escape_md(` with `Text(` and `)` with `).as_markdown()` where appropriate.

---

## System-Wide Impact
- **Unchanged invariants:** The verses sent back to users remain identical in appearance.
- **Dependency:** Requires `aiogram >= 3.0.0`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Incorrect parentheses matching | Use targeted replacements and verify with a final pass. |
