---
title: Tests that set the seam themselves hide missing production wiring
date: 2026-09-17
category: test-failures
module: persistence
problem_type: test_blind_spot
component: testing
symptoms:
  - "Every ZEO test passed while no production code ever set storage.zeo_address"
  - "The survival integration test assigned the address inside its own stand-in child process"
  - "Shared storage would have been silently inactive in production: each unit opened local files against the files the storage server had locked"
root_cause: missing_integration
resolution_type: code_fix
severity: high
tags: [testing, integration, wiring, zeo, persistence, false-confidence]
---

# Tests that set the seam themselves hide missing production wiring

## Problem

`persistence/storage.py` gained a module-level `zeo_address` and a `configure()`
function documented as "called once per process at startup". Nothing ever called it.
`grep -rn "storage.configure" src/ scripts/` returned only test files.

The consequence in production would have been severe and quiet: `zeo_address` stays
`None`, `open_db` takes the local-file branch, and the connector and web units open the
same `.fs` files the ZEO child process has already opened and locked. The resulting
lock error is not in `_STORAGE_UNREACHABLE`, so it is neither buffered nor surfaced —
`ConnectorManager.dispatch` logs it per message and moves on. Message persistence dies
silently while every bot keeps replying.

Nine tests exercised the ZEO path and all passed, because each one did this first:

```python
monkeypatch.setattr(storage, 'zeo_address', address)
```

Even the end-to-end survival test, which spawns real processes and runs a real ZEO
server, set the address by hand inside its own stand-in child:

```python
def connector_child(zodb_path, port, marker_dir):
    storage.zeo_address = ('127.0.0.1', port)   # production never does this
```

## Root Cause

The tests substituted for the exact step that was missing. A test that patches a seam
proves the code *downstream* of the seam works; it says nothing about whether anything
upstream ever sets it. The more faithful the rest of the test looks — real processes,
real signals, a real storage server — the more convincing the false confidence.

The same shape appeared twice more in this branch:

- The liveness tests' `FakeConnector` never set `running = False`, so they asserted a
  shutdown ping that could never fire in production, where `ConnectorManager` clears
  that flag during its own teardown before the run returns.
- `tests/test_entry_modes.py` asserted the dispatch table with substring checks against
  `inspect.getsource(module)`. A line that is present but unreachable passes.

## Solution

One function owns the wiring, and each unit calls it with the configs it already loads:

```python
configs = load_bot_configs(argv)
configure_from_configs(configs)   # before anything opens a store
```

For the tests, the rule that catches this class: **a test may fake the environment, but
it must not perform the step under test.** If a stand-in child has to assign the value
production assigns, the test has replaced the code path it claims to cover.

## Prevention

- When a module-level setting exists, grep for its writers in `src/` before trusting any
  test that reads it. A setting with only test-side writers is a wiring bug.
- Give a fake the real lifecycle: a fake connector that never goes down cannot test
  shutdown, and a fake clock that never advances cannot test a timeout.
- Assert structure from the AST, not from source text. `tests/test_web_no_connectors.py`
  and `tests/test_entry_modes.py` read imports and executed names, so a stale-but-present
  line cannot satisfy them.
- Related: `docs/solutions/test-failures/monkeypatch-undo-defeats-zodb-isolation.md` and
  `docs/solutions/test-failures/tests-deleted-real-instance-zodb.md` — the same family of
  "the test passed, so we believed it" failures.
