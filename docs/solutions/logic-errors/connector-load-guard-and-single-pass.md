---
title: A connector's import error must not crash the manager; don't derive load decisions by replaying imports
date: 2026-06-14
category: logic-errors
module: connectors
problem_type: logic_error
component: service_object
symptoms:
  - "ConnectorManager construction raises ImportError and the whole bot fails to start when one connector's platform dependency is missing"
  - "test_manager_import_failure_logs_error fails: ImportError escapes _load_connectors instead of being logged"
  - "Every connector module is imported twice during a single manager construction"
root_cause: logic_error
resolution_type: code_fix
severity: high
tags: [connectors, plugin-loading, import-module, exception-handling, sibling-isolation, strangler-fig]
---

# A connector's import error must not crash the manager; don't derive load decisions by replaying imports

## Problem

`ConnectorManager._load_connectors` gained a throwaway pre-scan loop to decide
telegram_v3 arbitration. The pre-scan re-imported every connector module and
caught only `(ModuleNotFoundError, AttributeError)`, so a connector whose
platform library raised a plain `ImportError` escaped the guard and crashed
manager construction — taking down the entire bot instead of just that one
connector.

## Symptoms

- A bot with one connector whose dependency is missing fails to start at all:
  `ImportError` propagates out of `_load_connectors`.
- `test_manager_import_failure_logs_error` (which simulates a missing `nio`)
  fails — the error is raised, not logged.
- Each connector module is imported twice per construction (pre-scan, then the
  real load), doubling import cost and side effects.

## What Didn't Work

- The narrower fix — just adding `ImportError` to the pre-scan's `except` — would
  have stopped the crash but left the deeper smell: a second full import pass
  whose only product was a `set` of active platform names. Patching the symptom
  preserves the duplicated, side-effecting pass.

## Solution

Collapse to a single import pass and apply the arbitration **after** loading,
because connector `__init__` is side-effect-free (no network until `connect()`),
so an instantiated-then-discarded connector costs nothing.

```python
# BEFORE — pre-scan replays every import to compute `suppress`, and the
# pre-scan's except is narrower than the real loop's, so a plain ImportError
# from a connector dependency escapes and crashes construction.
active_platforms = set()
for name, conf in config_dict.items():
    ...
    try:
        module = import_module('.' + name, 'iacecil.connectors')
        connector_class = getattr(module, 'Connector')
        if issubclass(connector_class, BaseConnector) and connector_class.is_active(conf):
            active_platforms.add(name)
    except (ModuleNotFoundError, AttributeError):  # plain ImportError NOT caught
        continue
suppress = {'telegram'} if 'telegram_v3' in active_platforms else set()
for name, conf in config_dict.items():     # second full import pass
    ...

# AFTER — one pass with full error handling; arbitration applied post-load.
for name, conf in config_dict.items():
    if not isinstance(conf, dict):
        continue
    try:
        module = import_module('.' + name, 'iacecil.connectors')
        connector_class = getattr(module, 'Connector')
        if issubclass(connector_class, BaseConnector) and connector_class.is_active(conf):
            self.connectors[name] = connector_class(self, conf)
    except ModuleNotFoundError as e:
        if e.name in (f'iacecil.connectors.{name}', name):
            logger.debug(f"Skipping non-connector section {name}")   # not a connector
        else:
            logger.error(f"Failed to load connector {name}: missing dependency {e.name!r}")
    except AttributeError:
        logger.debug(f"Skipping non-connector section {name}")       # no Connector class
    except Exception as e:
        # Any other import-time failure (plain ImportError included):
        # log, don't crash — siblings must still load.
        logger.error(f"Failed to load connector {name}: {e}")

# Strangler-fig arbitration: telegram_v3 supersedes legacy telegram.
if 'telegram_v3' in self.connectors and 'telegram' in self.connectors:
    del self.connectors['telegram']
```

## Why This Works

Two faults, one structural cause: the code derived a *decision input* (which
platforms are active) by replaying an *expensive, side-effecting operation*
(module import) in a separate pass — and that duplicated pass drifted from the
real loop's exception handling. The state needed for the arbitration decision is
already produced by the main load (`self.connectors`), so collect first and
decide after. A single `except Exception` backstop on the one remaining loop
guarantees the sibling-isolation invariant (one connector's failure never stops
the others), which the activation-discovery design depends on
(see [connector-self-declared-activation](../architecture-patterns/connector-self-declared-activation.md)).
Applying suppression post-load is only correct because connector construction is
pure — the suppressed connector is instantiated and dropped without ever opening
a socket.

## Prevention

- **Never derive a decision input by replaying a side-effecting pass.** If you
  need "which X are active/valid," collect the result of doing the work once,
  then branch on it — don't run a shadow pass that re-imports / re-queries / re-fetches.
- **An exception-isolation guard must catch the whole error family it isolates.**
  A loader meant to keep one bad module from killing siblings must catch
  `Exception` (or at least the full import-error family), not a hand-picked
  subset like `(ModuleNotFoundError, AttributeError)` — `ImportError` and others
  slip through and defeat the isolation. Distinguish *log levels* by exception
  detail (e.g. `ModuleNotFoundError.name`), but never let detail-matching narrow
  the *catch*.
- **Lean on the side-effect-free `__init__` invariant** for connectors: keep all
  I/O in `connect()`, so load-time decisions (instantiate, inspect, discard) stay
  cheap and safe. Keep that invariant true as connectors evolve.
- Regression test pins it: `tests/test_manager.py::test_manager_import_failure_logs_error`
  plus `test_telegram_v3_suppresses_legacy_telegram` / `test_legacy_telegram_kept_without_v3`.

## Related Issues

- [connector-self-declared-activation](../architecture-patterns/connector-self-declared-activation.md)
  — the activation-discovery loader and `e.name` log-level rule this regression
  broke and now restores; this doc is the cautionary companion to that pattern.
- [strangler-fig-dispatch-arbitration](../architecture-patterns/strangler-fig-dispatch-arbitration.md)
  — the same module's ownership boundary; telegram_v3-supersedes-telegram is the
  load-time analogue of that dispatch-time rule.
