---
title: Tests that set the seam, or fake it more permissively than production, hide defects
date: 2026-09-17
last_updated: 2026-09-17
category: test-failures
module: tests
problem_type: test_failure
component: testing
symptoms:
  - "Every ZEO test passed while no production code ever set storage.zeo_address"
  - "The survival integration test assigned the address inside its own stand-in child process"
  - "Liveness tests asserted a shutdown ping that ConnectorManager.send would drop in production"
  - "A telegram_v3 bot never sent its liveness pings; the fake manager used the name 'telegram'"
  - "A reviewed and tested fix for the shutdown ping was still incomplete; only a live run showed it"
root_cause: missing_integration
resolution_type: test_fix
severity: high
related_components: [connectors, persistence, supervisor]
tags: [testing, test-doubles, fakes, integration, wiring, liveness, telegram-v3, false-confidence]
---

# Tests that set the seam, or fake it more permissively than production, hide defects

## Problem

Test doubles that do more than production does let a green suite certify code that
cannot work. It happened three times in one change, each time with the rest of the
test looking faithful: real processes, real signals, a real ZEO server.

## Symptoms

- Every ZEO test passed while no production code ever set `storage.zeo_address`.
  Shared storage would have been silently inactive: each unit opened local files
  against the files the storage server had locked, the resulting lock error was not
  in the write buffer's unreachable-storage set, and `ConnectorManager.dispatch`
  logged it per message and moved on.
- The liveness tests asserted a "Mãe tá #off" ping that production could never
  deliver, and a "Mãe tá #on" ping that a `telegram_v3` bot never sent.
- Code review caught the wiring gap, and flagged that #off never fired. The fix for
  #off was incomplete, the `telegram_v3` defect went unflagged, and both survived the
  322-test suite, surfacing in the first minutes of running the real bot under the
  supervisor.

## What Didn't Work

- **Faithful-looking integration tests.** The survival test spawns real processes and
  a real storage server, and still could not see the missing wiring, because its
  stand-in child assigned the address itself
  (`tests/test_survival_integration.py:62`, `storage.zeo_address = ('127.0.0.1', port)`).
  Fidelity everywhere else made the one substituted step more convincing, not less.
- **A code review with six reviewers, and a fix verified against a fake.** Review
  found the wiring gap (two reviewers independently) and flagged that #off could never
  fire because it waited for a connector that was already down. The fix removed that
  wait, and the tests went green, but `ConnectorManager.send` drops envelopes for a
  downed connector on its own, so the ping still could not leave. The fake's `send`
  accepted it anyway, which is why the incomplete fix looked complete. The
  `telegram_v3` defect was not flagged at all: it lived in the gap between the fake
  and the real configuration, which a diff read does not exercise.

## Solution

Three fixes, one per defect, plus test doubles that obey the real contract.

**Wiring.** One function owns it, and each unit calls it with the configs it already
loads, before anything opens a store
(`src/iacecil/controllers/_iacecil/connectors_runner.py:334`, and the web unit via
`configure_persistence` at `src/iacecil/controllers/_iacecil/production.py:129`):

```python
configs = load_bot_configs(argv)
configure_from_configs(configs)
```

**Connector name.** `ConnectorManager` deletes the legacy `telegram` connector whenever
`telegram_v3` is present (`src/iacecil/connectors/__init__.py:118-121`). The liveness
code now resolves whichever one runs (`connectors_runner.py:133-136`,
`TELEGRAM_CONNECTORS = ('telegram_v3', 'telegram')`) instead of hard-coding `'telegram'`.

**Delivery order.** `ConnectorManager.send` drops any envelope addressed to a connector
that is not `running` and returns `False` (`src/iacecil/connectors/__init__.py:143-147`).
The #off ping had been sent after the connectors tore down, so it could never leave
the process. On SIGTERM it is now sent first, then the run is cancelled
(`connectors_runner.py:248`, `_stop_gracefully`), and a `False` from `send` is logged
as "not delivered" rather than reported as sent (`connectors_runner.py:236-239`).

**The doubles.** The fake manager's `send` now drops exactly what the real one drops
(`tests/test_liveness_ping.py:49-50`):

```python
async def send(self, envelope):
    connector = self.connectors.get(envelope.platform)
    if connector is None or not connector.running:
        return False
    self.sent.append(envelope)
    return True
```

Before, it appended every envelope. That one permissive line is what let the
"#off after teardown" test pass.

## Why This Works

A test double substitutes for a collaborator, and the test's verdict is only as good
as the substitution. Each of these doubles was *more permissive* than the thing it
replaced: it performed a step production never performed (setting the address), it
accepted input production rejects (envelopes for a downed connector), or it used a
name production never uses (`'telegram'` on a v3 bot). A more permissive double
cannot fail in the places production fails, so the test turns green exactly where the
real system is red. Making the double enforce the real contract restores the failure
path, which is the only part of the test that was carrying information.

## Prevention

- **A test may fake the environment, but it must not perform the step under test.**
  If a stand-in has to assign the value production assigns, the test replaced the
  code path it claims to cover. Grep for a module-level setting's writers in `src/`
  before trusting any test that reads it; a setting with only test-side writers is a
  wiring bug.
- **A double must reject what the real collaborator rejects.** When writing a fake,
  read the real method's early returns and guards (`if not connector.running: return
  False`) and copy them. Guards are the contract; the happy path is the easy part.
- **Take identifiers from the real configuration, not from memory.** The fake manager
  was built with `'telegram'` because that is the name everyone says; the bot in
  production runs `'telegram_v3'`. A test that parametrizes over the names the real
  arbitration can produce (`TELEGRAM_CONNECTORS`) covers both.
- **Assert structure from the AST, not source text.** `tests/test_web_no_connectors.py`
  and `tests/test_entry_modes.py` read imports and executed names, so a stale-but-present
  line cannot satisfy them.
- **Run the real thing before calling it done.** The incomplete #off fix and the
  `telegram_v3` defect both passed 322 tests and a six-reviewer review; both showed
  up in the first minutes of a live run against a real bot. For a change whose whole point is process lifecycle
  (startup, signals, shutdown order), a live run is a verification step, not an extra.

## Related

- `docs/solutions/test-failures/monkeypatch-undo-defeats-zodb-isolation.md` and
  `docs/solutions/test-failures/tests-deleted-real-instance-zodb.md` — the same family
  of "the test passed, so we believed it" failures, on the isolation side.
- `docs/solutions/logic-errors/connector-load-guard-and-single-pass.md` and
  `docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md` — where
  the `telegram_v3`-supersedes-`telegram` invariant comes from; any code that looks a
  connector up by name has to respect it.
