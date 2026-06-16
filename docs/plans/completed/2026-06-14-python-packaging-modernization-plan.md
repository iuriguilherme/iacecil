# Plan: Python Packaging Modernization

Modernize `ia.cecil` packaging by adopting PEP 621 standards in `pyproject.toml`, consolidating metadata/dependencies, and generating a tool-agnostic `requirements.txt` lockfile.

---

## Problem Frame

The current packaging is fragmented across five files (`setup.py`, `setup.cfg`, `pyproject.toml`, `Pipfile`, `requirements.txt`) that frequently disagree. Dependencies are not clearly categorized by connector, leading to a bloated install for everyone.

### Proposed Changes

1.  **Consolidate Metadata**: Move all metadata to a PEP 621 `[project]` table in `pyproject.toml`.
2.  **Categorize Dependencies**: Use optional extras for platform-specific dependencies (Telegram, Matrix, etc.).
3.  **Standardize Build**: Use `setuptools` as the build backend with dynamic versioning.
4.  **Universal Locking**: Generate a single `requirements.txt` as the definitive lockfile.
5.  **Hygiene**: Clean up root clutter and modernize Docker configuration.
6.  **Documentation Alignment**: Update README and project guides to reflect the new workflow.

---

## Requirements

### Primary Goals (Mandatory)
- **R-1**: PEP 621 Single Source of Truth in `pyproject.toml`.
- **R-2**: Strict compatibility with `python -m venv` and `python -m pip`. This is the authoritative test.
- **R-3**: Support for multiple run-ways:
    - **Module**: `python -m iacecil`
    - **Installed Package**: `iacecil` command (console script).
    - **GitHub/PyPI Ready**: Installable via `pip install git+https://github.com/...` or future PyPI publish.

### Secondary Goals
- **R-4**: Compatibility with `uv`, `poetry`, and `pipenv` (they should all be able to read the PEP 621 metadata).
- **R-5**: Dependency & Extras Restructuring (Connectors as extras).

### Tertiary Goals
- **R-6**: Preserve legacy implementations (e.g., `telegram.py` vs `telegram_v3.py`) if they are still actively used in configurations.

---

## Scope Boundaries

- **S-1**: No new task runner (Makefile/justfile). Existing tool-specific scripts can stay.
- **S-2**: Standardize on Python 3.11.

---

## Context & Research

### Relevant Code and Patterns

- `pyproject.toml`: Current build-backend declaration.
- `setup.cfg`: Current source for metadata.
- `Pipfile`: Current de-facto source for pins.
- `src/iacecil/__main__.py`: Target for entry point refactor.
- `src/iacecil/_version.py`: Source for dynamic versioning.
- `instance/`: Check active bot configs for legacy connector usage.

---

## Key Technical Decisions

- **KD-1: Setuptools Backend**: Use `setuptools.build_meta` for universal PEP 517 compatibility.
- **KD-2: Dynamic Versioning**: Read `__version__` from `src/iacecil/_version.py`.
- **KD-3: Entry Point Wrapper**: Refactor `__main__.py` to use a `main()` function.
- **KD-4: Pip-Tools for Locking**: Use `pip-compile` to generate `requirements.txt`.

---

## Implementation Units

- U1. **Hygiene Sweep & Legacy Audit**
    - **Goal**: Clean up root and verify used legacy code.
    - **Files**:
        - Rename: `Dockfile` -> `Dockerfile`
        - Move: `parse_lock.py`, `update_personas.py`, `update_personas2.py`, `test_sanitizer.py` to `scripts/`
    - **Approach**: Grep `instance/` and `src/` to see if legacy connectors (e.g. `telegram.py`) are still imported. If not, mark for future deletion but keep for now as requested. Update `Dockerfile` to use `python:3.11`.

- U2. **Entry Point Refactor**
    - **Goal**: Support both `python -m` and console script.
    - **Files**:
        - Modify: `src/iacecil/__main__.py`
    - **Approach**: Move execution logic into `def main():`. Ensure `python -m iacecil` calls `main()`.

- U3. **Consolidate pyproject.toml (PEP 621)**
    - **Goal**: Create the "Single Source of Truth".
    - **Files**:
        - Modify: `pyproject.toml`
    - **Approach**: 
        - Replace Poetry/Setuptools-legacy with PEP 621 `[project]`.
        - Add `[project.scripts]` entry point.
        - Define extras for `telegram`, `discord`, etc.
        - Include `pip-tools` in `dev` extra.

- U4. **Lockfile Generation**
    - **Goal**: Produce vanilla `requirements.txt`.
    - **Files**:
        - Modify: `requirements.txt`
    - **Approach**: Generate using `pip-compile`.

- U5. **Documentation & Cleanup**
    - **Goal**: Align guides and remove legacy config.
    - **Files**:
        - Modify: `README.md`, `GEMINI.md`
        - Delete: `setup.py`, `setup.cfg`, `Pipfile`, `Pipfile.lock`, `uv.lock`
    - **Approach**: Document the "vanilla first" workflow.

---

## Success Criteria
- [ ] `python -m venv .venv && source .venv/bin/activate && pip install -e .[all]` succeeds.
- [ ] `iacecil production` (console script) works.
- [ ] `python -m iacecil production` (module) works.
- [ ] `pip install git+https://github.com/iuriguilherme/iacecil.git` (package) works.
- [ ] `uv`, `poetry`, and `pipenv` can all parse `pyproject.toml` without errors.
