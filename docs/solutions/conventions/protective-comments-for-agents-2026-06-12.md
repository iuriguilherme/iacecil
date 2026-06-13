---
module: "iacecil"
date: "2026-06-12"
problem_type: "convention"
component: "development_workflow"
severity: "low"
applies_when:
  - "Commented code is kept for future restoration but looks 'dead' to automated reviewers."
  - "Robust loader logic looks over-engineered but handles specific path quirks (e.g., Pydantic vs dicts)."
  - "Workarounds for platform bugs or legacy structures are kept during migration."
tags:
  - "auto-cleanup"
  - "protective-comments"
  - "agent-review"
  - "code-preservation"
---

# Use Protective Comments to Preserve Intentional Legacy Logic from Agent Auto-Cleanup

## Context
AI agents perform aggressive cleanup on "dead" code. During an automated review, an agent removed a commented-out block in `src/plugins/deepseek.py` (`chance_deepseek_callback`) and "simplified" robust logic in `src/iacecil/connectors/__init__.py` (`_load_personality`). The commented code was preserved for historical intent despite looking "dead", and the refactored logic destroyed robustness meant for edge cases (handling both Pydantic models and raw dicts).

## Guidance
Add protective comments for AI agents. Use clear tags like `# NOTE FOR AGENTS` or `# DO NOT REMOVE`. State the reason the code must stay despite looking like a "refactor candidate". Preserve robust logic even if a machine thinks a "cleaner" version exists.

## Why This Matters
AI agents optimize for "clean" code but can miss "strategic" intent. The auto-cleanup cycle wastes tokens and time, and re-introducing bugs after a "fix" frustrates users. Protective tags stop "clever" AI from repeating mistakes and preserve human intent.

## When to Apply
- Commented code kept for future restoration.
- Robust loaders that look over-engineered but handle specific path quirks.
- Workarounds for platform bugs.
- Legacy structures kept during migration.

## Examples

**Before (AI deletes "dead" code):**
```python
# chance_deepseek_callback(msg)
```

**After (Protective tag stops cleanup):**
```python
# NOTE FOR AGENTS: Do not remove this commented-out block. 
# Intentionally disabled but preserved for future restoration.
# chance_deepseek_callback(msg)
```

**Loader Logic:**
Avoid swapping a custom path-aware loader for a simpler version if the project structure requires explicit type-checking mapping (e.g., `hasattr(model, 'model_dump')` vs `isinstance(dict)`) for robustness.
