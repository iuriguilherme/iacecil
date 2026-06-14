---
title: Python Packaging Modernization (PEP 621)
date: 2026-06-14
category: docs/solutions/tooling-decisions/
module: packaging
problem_type: tooling_decision
component: tooling
severity: high
applies_when:
  - "Modernizing build infrastructure"
  - "Consolidating project metadata"
  - "Resolving dependency conflicts across multiple sources"
tags: [packaging, pyproject-toml, pep-621, uv, pip-tools, single-source-of-truth]
---

# Python Packaging Modernization (PEP 621)

## Context
The project suffered from fragmented metadata and dependencies spread across `setup.py`, `setup.cfg`, `Pipfile`, `requirements.txt`, and a limited Poetry-style `pyproject.toml`. This redundancy caused "dependency hell" and synchronization errors (see [aiogram-matrix-nio-dependency-conflict-2026-06-13.md](../build-errors/aiogram-matrix-nio-dependency-conflict-2026-06-13.md)).

## Guidance
Adopt the **PEP 621** (`pyproject.toml`) standard as the single source of truth for metadata and dependencies.

1.  **Consolidation**: Move all content from `setup.py`, `setup.cfg`, and `Pipfile` to the `[project]` table in `pyproject.toml`.
2.  **Multi-Tool Support**: Retain `[tool.poetry]` and `[tool.pipenv.scripts]` blocks within `pyproject.toml` to maintain secondary compatibility for developers using those specific workflows.
3.  **Entry Points**: Refactor `src/iacecil/__main__.py` to include a `main()` function and register it under `[project.scripts]`. This allows the package to be installed and run as a global command (`iacecil`).
4.  **Extras**: Use `[project.optional-dependencies]` to separate heavy dependencies for each connector (telegram, discord, mastodon, etc.), enabling lean installations.
5.  **Agnostic Locking**: Use `uv` (or `pip-compile`) to generate a pinned `requirements.txt` from `pyproject.toml`. This file serves as a universal lockfile, compatible with any package manager.

## Why This Matters
-   **Tool Independence**: The project can now be installed via `pip`, `uv`, `poetry`, or `pipenv` from a single manifest.
-   **Standards Compliance**: Follows current PyPA recommendations while respecting the user's preference for broad tool support.
-   **Maintainability**: Changing a library version now requires editing only one file (`pyproject.toml`).

## When to Apply
-   When starting new modules or connectors.
-   When updating critical dependencies that cause conflicts.
-   In CI/CD environments to ensure reproducible builds via `requirements.txt`.

## Future Refinements
-   **Plugin Renaming**: Renaming the `plugins` package to `iacecil-plugins` is a confirmed future goal. This will ensure namespace safety when the project is installed in a shared Python environment.
-   **Clean Versioning**: The legacy git-scraping logic in `src/iacecil/__init__.py` should eventually be replaced by the static `_version.py` source of truth to ensure reliability in non-git environments.

## Examples

### pyproject.toml (PEP 621)
```toml
[project]
name = "iacecil"
dynamic = ["version", "description"]
dependencies = [
    "aiodns",
    "aiohttp[speedups]>=3.10",
    # ... core deps
]

[project.optional-dependencies]
telegram = ["aiogram>=2.25.1", "python-telegram-bot==22.5"]
all = ["iacecil[telegram,discord,mastodon,matrix,xmpp,furhat,web3]"]

[project.scripts]
iacecil = "iacecil.__main__:main"
```

### Vanilla Workflow
```bash
python -m venv .venv
source .venv/bin/activate
(.venv) user@home:~/iacecil$ pip install -e .[all]
(.venv) user@home:~/iacecil$ python -m iacecil  # or just 'iacecil'
```

## Related
-   [docs/solutions/build-errors/aiogram-matrix-nio-dependency-conflict-2026-06-13.md](../build-errors/aiogram-matrix-nio-dependency-conflict-2026-06-13.md)
-   [docs/solutions/integration-issues/aiogram-3-bot-connector-migration-2026-06-14.md](../integration-issues/aiogram-3-bot-connector-migration-2026-06-14.md)
