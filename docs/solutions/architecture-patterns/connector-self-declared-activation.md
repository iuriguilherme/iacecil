---
title: Connectors declare their own activation; the manager discovers instead of allowlisting
date: 2026-06-11
last_updated: 2026-06-12
category: architecture-patterns
module: connectors
problem_type: architecture_pattern
component: service_object
severity: medium
applies_when:
  - "A registry/manager loads pluggable modules from config sections"
  - "Adding a new module currently requires editing the loader (allowlist, per-module credential rules)"
  - "Config carries many non-module sections that must not trigger load noise"
tags: [connectors, activation, allowlist, plugin-loading, import-module, discovery, open-closed]
---

# Connectors declare their own activation; the manager discovers instead of allowlisting

## Context

`ConnectorManager` originally hardcoded both an allowlist
(`{telegram, xmpp, loopback, discord}`) and per-platform credential rules
(`_is_active`: telegram needs `token`, xmpp needs `jid`+`password`, ...).
Every new platform required editing the manager in two places — discovered
the moment the matrix connector (the first platform the architecture had
not anticipated) was added.

## Guidance

Invert ownership: each connector class declares its own activation rule;
the manager iterates config sections and asks the class.

```python
class BaseConnector(ABC):
    required_keys: tuple = ()

    @classmethod
    def is_active(cls, conf: dict) -> bool:
        if not conf:
            return False
        return all(conf.get(key) for key in cls.required_keys)

# telegram: required_keys = ('token',)
# xmpp:     required_keys = ('jid', 'password')
# matrix overrides is_active(): homeserver + (token or user+password)
```

The manager's loader becomes discovery: try
`import_module('.' + section, 'iacecil.connectors')` for every dict
config section. The crucial detail is disambiguating
`ModuleNotFoundError` — config carries ~12 credential-shaped
non-connector sections (`openai`, `coinmarketcap`, ...) that must not
produce an error storm:

```python
except ModuleNotFoundError as e:
    if e.name == f"iacecil.connectors.{name}":
        logger.debug(...)   # section is not a connector — quiet skip
    else:
        logger.error(...)   # connector exists, its dependency is missing
```

`e.name` distinguishes "no such connector module" from "connector module
found but its platform library is not installed" — same exception type,
opposite log levels. Pair with lazy platform-library imports inside
`connect()` so connector modules always import cleanly.

## Why This Matters

A new platform becomes one module plus one config section, with zero
manager edits — the matrix connector landed exactly that way, and the
conformance suite pins the property with a fake `dummy` connector test.
Without the `e.name` check, removing the allowlist floods every boot with
false errors (or silently hides real missing-dependency failures).

*Note (2026-06-12): The "Echo everywhere" refactor completes this architectural transition. It unifies dispatch logic across natively supported connectors (Discord, Matrix, XMPP, Loopback) while preserving the legacy Telegram ownership boundary.*

## When to Apply

- Replacing a loader allowlist with discovery over config/sections
- Any `import_module`-based plugin system where "not a plugin" and
  "broken plugin" must log differently

## Examples

See `src/iacecil/connectors/__init__.py` (`_load_connectors`),
`src/iacecil/connectors/base.py`, and
`tests/test_manager.py::test_dummy_connector_activates_with_zero_manager_edits`.

## Related

- docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md —
  same module; the dispatch-ownership rule this loader change preserves
- docs/solutions/architecture-patterns/aiogram-handler-registration-order.md —
  the legacy loading order this coexists with on telegram
