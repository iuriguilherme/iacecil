---
title: Test suite deleted real instance/zodb data
date: 2026-06-10
category: test-failures
module: persistence
problem_type: test_failure
component: testing_framework
symptoms:
  - "Running pytest wiped instance/zodb/ (live ZODB message history and Person registry)"
  - "Tests passed while silently destroying deployment data in the working directory"
  - "Second test file wrote records into the real instance/zodb path with no cleanup"
root_cause: test_isolation
resolution_type: test_fix
severity: critical
tags: [zodb, pytest, fixtures, test-isolation, data-loss, instance-directory]
---

# Test suite deleted real instance/zodb data

## Problem

The first test files written for the neutral persistence layer pointed at the
real storage path. A fixture deleted `instance/zodb/` wholesale before each
test, and another test wrote records into it — so running `pipenv run pytest`
in a deployment checkout destroyed live bot data while reporting green.

## Symptoms

- `tests/test_person.py` carried `shutil.rmtree("instance/zodb")` in an
  autouse fixture — any pytest run erased real message history and the
  Person registry
- `tests/test_loopback.py` persisted test envelopes into the real store with
  no cleanup
- Nothing failed: the destruction was invisible in test output

## What Didn't Work

- Relying on per-test cleanup inside individual test files: each new test
  file had to remember the discipline, and the second one already forgot —
  cleanup-by-convention does not survive growth
- Module-level `zodb_path = 'instance/zodb'` constants read at import time
  invite exactly this class of bug: any code path that touches persistence
  during tests hits production paths by default

## Solution

One autouse fixture in `tests/conftest.py` redirects the storage root to
pytest's `tmp_path` before any test runs and resets the module-level
database singletons so nothing reuses a handle opened against the real path:

```python
import pytest

@pytest.fixture(autouse=True)
def isolated_zodb(tmp_path, monkeypatch):
    """Redirect neutral persistence to a temp dir so tests never touch
    the real instance/zodb data."""
    import iacecil.controllers.persistence.neutral as neutral
    monkeypatch.setattr(neutral, 'zodb_path', str(tmp_path / 'zodb'))
    neutral._people_db = None
    neutral._messages_db = None
    yield
    for attr in ('_people_db', '_messages_db'):
        db = getattr(neutral, attr)
        if db is not None:
            db.close()
            setattr(neutral, attr, None)
```

The destructive `clean_zodb` fixture was deleted from `tests/test_person.py`.

## Why This Works

Isolation moves from per-test convention to suite-level guarantee: the
autouse fixture runs for every test in the package, present and future, so
no individual test file can opt out by forgetting. Resetting the cached
`_people_db` / `_messages_db` singletons matters as much as patching the
path — without it, a handle opened against the real path by an earlier
import would survive the monkeypatch.

## Prevention

- Storage paths consumed by tests must be injectable (module attribute,
  env var, or constructor arg) — never only a hardcoded constant
- Put filesystem/database isolation in an autouse `conftest.py` fixture, not
  in individual test files; one forgetting kills real data
- Never write `rmtree` of a real data directory into a fixture, even as
  "cleanup" — redirect instead of clean
- After any persistence-touching test work, verify the real data directory
  is untouched (`ls instance/zodb` before/after the suite)
- CLAUDE.md documents the fixture as load-bearing: "never remove it"

## Related Issues

- None yet — first entry in docs/solutions/.
