# Requirements: Python Packaging Modernization

## Summary
Modernize `ia.cecil` packaging by adopting PEP 621 standards in `pyproject.toml`, consolidating metadata/dependencies into a single source of truth, and generating a tool-agnostic `requirements.txt` lockfile while preserving existing run-ways.

## Problem Frame
The current packaging configuration is fragmented across `setup.py`, `setup.cfg`, `pyproject.toml` (Poetry style), `Pipfile`, and `requirements.txt`. These sources frequently disagree on versions and dependencies, leading to environment drift and manual synchronization overhead (`parse_lock.py`).

## Requirements

### R-1: PEP 621 Single Source of Truth
- **Description**: Move all package metadata (name, description, authors, classifiers, URLs, `requires-python`) and runtime dependencies into the standard `[project]` table in `pyproject.toml`.
- **Constraint**: Delete `setup.py`, `setup.cfg`, `Pipfile`, and `[tool.poetry]` sections from `pyproject.toml` once the move is verified.

### R-2: Dependency & Extras Restructuring
- **Description**: Define core dependencies in `[project].dependencies` and platform-specific dependencies in `[project.optional-dependencies]`.
- **Connectors**: Create extras for `telegram`, `discord`, `mastodon`, `matrix`, `xmpp`, and `furhat`.
- **Convenience**: Include an `all` extra that aggregates all connector dependencies.

### R-3: Tool-Agnostic Locking
- **Description**: Commit exactly one lockfile. Generate a vanilla-pip compatible `requirements.txt` from the `pyproject.toml` manifest using a standard resolver (e.g., `pip-compile` or `uv`).
- **Sync**: Ensure Docker and plain-pip users install from this generated `requirements.txt`.

### R-4: Portable Entry Points
- **Description**: Add a `[project.scripts]` entry point for `iacecil = "iacecil.__main__:main"`.
- **Scripts**: Allow existing scripts to remain in tool-specific tables (e.g., `[tool.poetry.scripts]` or `[tool.pipenv.scripts]`) as a secondary concern.

### R-5: Hygiene Sweep
- **Description**: Clean up repo-root and configuration smells.
- **Dependency cleanup**: Remove the invalid `install-requires` package from all declarations.
- **Root cleanup**: Relocate or delete stray scripts like `parse_lock.py`, `update_personas*.py`, and `test_sanitizer.py`.
- **Docker**: Rename `Dockfile` to `Dockerfile` and align its base image with the project's Python version (3.11).

## Key Decisions

### KD-1: Build Backend - Setuptools
- **Decision**: Standardize on `setuptools` as the PEP 517 build backend.
- **Rationale**: It is already partially declared and supports standard src-layout discovery.

### KD-2: Manifest over Management
- **Decision**: Prioritize PEP-compliant `pyproject.toml` as the source of truth, making the choice of workflow tool (uv, poetry, pipenv) an operator preference rather than a project requirement.

## Scope Boundaries

### S-1: Task Runner
- **Out of Scope**: Implementation of a tool-agnostic task runner (Makefile, justfile). Scripts stay in tool-specific sections.

### S-2: Python Version
- **Boundary**: Maintain requirement for Python 3.11+.

## Success Criteria
- [ ] `pip install -e .` in a vanilla venv installs all core dependencies and the `iacecil` command.
- [ ] `pip install .[telegram]` installs only core + Telegram dependencies.
- [ ] No duplicated metadata or versions across the codebase.
- [ ] `requirements.txt` is successfully generated from `pyproject.toml` and used by Docker.
