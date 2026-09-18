---
title: monkeypatch.undo() defeats the autouse ZODB isolation fixture
date: 2026-09-17
category: test-failures
module: tests
problem_type: test_failure
component: testing
symptoms:
  - "A test asserting on its own records read 180 rows, including real production messages"
  - "12 test records (m0/m1/m2/after) were appended to the real instance/zodb/messages.fs"
  - "The test still passed while writing outside its temp directory"
root_cause: wrong_api
resolution_type: code_fix
severity: high
tags: [pytest, monkeypatch, zodb, test-isolation, fixtures]
---

# monkeypatch.undo() defeats the autouse ZODB isolation fixture

## Problem

A write-buffer test needed storage to fail, then succeed: simulate a ZEO outage,
then let the real store work again. The obvious way to end the outage was to undo
the patch that installed the failing stand-in:

```python
monkeypatch.setattr(neutral, 'get_messages_db', _returning(DisconnectedDB()))
...
monkeypatch.undo()          # end the outage
db = await neutral.get_messages_db()
```

The test passed, and wrote its records into the real `instance/zodb/messages.fs`.

## Root Cause

`monkeypatch.undo()` takes no arguments and reverses **every** patch that
`monkeypatch` fixture instance has applied. The isolation fixture in
`tests/conftest.py` is autouse and function-scoped, and it repoints
`neutral.zodb_path` and `chat_store.zodb_path` at `tmp_path` through that *same*
fixture instance. Undoing "my" patch therefore also restored the real
`instance/zodb` path, and the next write landed in production data.

pytest gives each test one `monkeypatch` instance shared by every fixture that
requests it, so patches from different fixtures are indistinguishable to `undo()`.

## Solution

Never call `monkeypatch.undo()` in this suite. Make the *stand-in* switchable
instead, so the patch stays in place for the whole test:

```python
class Outage:
    def __init__(self, monkeypatch):
        self.down = True
        monkeypatch.setattr(neutral, 'get_messages_db', self._get_db)

    async def _get_db(self, *args, **kwargs):
        if self.down:
            return DisconnectedDB()
        return await _open_messages_db()

    def restore(self):
        self.down = False
```

`tests/test_write_buffer.py` carries this pattern with a comment naming the hazard.

## Prevention

- Treat `monkeypatch.undo()` as repo-forbidden: it is global to the test, not to
  the caller, and this suite's data isolation rides on an autouse fixture.
- To reverse one patch mid-test, model the state change in the double (a flag, a
  queue of responses, a side-effect list) rather than unwinding the patch.
- A passing test proves nothing about isolation. When a test exercises the
  persistence layer, assert on record counts it created rather than on "all
  records", so foreign data makes the test fail loudly instead of silently.
- Related: `docs/solutions/test-failures/tests-deleted-real-instance-zodb.md`
  covers the fixture itself, which `CLAUDE.md` says must never be removed.
