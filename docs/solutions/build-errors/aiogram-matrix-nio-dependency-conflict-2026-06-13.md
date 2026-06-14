---
title: Resolving aiogram and matrix-nio dependency conflict over aiohttp versions
date: 2026-06-13
category: docs/solutions/build-errors/
module: iacecil dependency management
problem_type: build_error
component: tooling
severity: high
symptoms:
  - "Pipenv resolution failure"
  - "Version conflict between aiogram 2.25.1 and matrix-nio"
  - "aiohttp version mismatch (< 3.9 vs >= 3.10)"
  - "Pipenv permission error on .env file (mode 000)"
root_cause: config_error
resolution_type: dependency_update
tags:
  - aiogram
  - aiohttp
  - matrix-nio
  - pipenv
  - dependency-conflict
---

# Resolving aiogram and matrix-nio dependency conflict over aiohttp versions

## Problem
A version conflict between `aiogram 2.25.1` and `matrix-nio` regarding their `aiohttp` requirements prevented `pipenv lock` from succeeding. This blocked updates to the Matrix connector and other dependency changes.

## Symptoms
- `pipenv install` or `pipenv lock` fails with a resolution error.
- Error log shows `aiogram 2.25.1` pins `aiohttp < 3.9`.
- Error log shows `matrix-nio` (required for Matrix support) requires `aiohttp >= 3.10`.
- Secondary symptom: `PermissionError: [Errno 13] Permission denied: '.env'` when Pipenv attempts to load environment variables (mode 000).

## What Didn't Work
- Attempting to force both `aiogram 2.25.1` and `matrix-nio` failed because their sub-dependency requirements for `aiohttp` are strictly disjoint (one requires < 3.9, the other >= 3.10).
- Running Pipenv normally failed because it would attempt to read a `.env` file that had been restricted to mode 000 for security/isolation testing.

## Solution
1. **Loosen aiogram constraints**: Updated `Pipfile`, `setup.py`, and `pyproject.toml` to change the `aiogram` requirement from `== 2.25.1` to `>= 2.25.1`. This allows the resolver to pick `aiogram 3.x` (or a compatible 2.x if one exists with higher `aiohttp` support), enabling a valid resolution with `aiohttp 3.x`.
2. **Bypass .env permission error**: Used the environment variable `PIPENV_DONT_LOAD_ENV=1` to prevent Pipenv from trying to read the inaccessible `.env` file during the locking process.

Example change in `Pipfile`:
```toml
[packages]
aiogram = ">=2.25.1"
matrix-nio = "*"
```

## Why This Works
- Loosening the constraint gives the dependency resolver the flexibility needed to find a shared version of `aiohttp` that satisfies both packages.
- Matrix support was prioritized as a core project goal. While `aiogram 2.x` code may require updates to be compatible with `aiogram 3.x`, this path was accepted because a major refactor of the Telegram stack was already planned and necessary for modernization.
- `PIPENV_DONT_LOAD_ENV=1` specifically instructs Pipenv to skip its automatic `.env` loading logic, which avoids the `PermissionError` when that file is intentionally or accidentally restricted.

## Prevention
- Avoid strict version pinning (`==`) in library-like components (e.g., `setup.py`) to prevent "dependency hell" for downstream users or when adding new platform connectors.
- Use `PIPENV_DONT_LOAD_ENV=1` as a standard practice in restricted environments or CI where `.env` files are managed separately or restricted.
- Document known version conflicts in a dedicated section to help future platform integrations.

## Related Issues
- `docs/solutions/architecture-patterns/aiogram-handler-registration-order.md` (related to Telegram stack limitations)
