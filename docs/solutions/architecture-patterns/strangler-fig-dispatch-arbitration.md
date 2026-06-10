---
title: Arbitrate dispatch ownership when engulfing a legacy handler stack
date: 2026-06-10
category: architecture-patterns
module: connectors
problem_type: architecture_pattern
component: service_object
severity: high
applies_when:
  - "A new dispatch layer is wrapped around a legacy framework whose handlers still run (strangler-fig / engulf migration)"
  - "Events are emitted from inside the legacy pipeline into the new layer"
  - "Both layers are capable of producing user-visible responses"
tags: [strangler-fig, dispatch, connectors, telegram, double-reply, migration]
---

# Arbitrate dispatch ownership when engulfing a legacy handler stack

## Context

The connector abstraction engulfed the existing aiogram (Telegram) stack:
the legacy dispatcher and its handlers kept running, while a new
ConnectorManager gained a command registry fed by envelopes emitted from
inside the legacy callback chokepoint. Without an explicit rule, both
layers answered the same command — every Telegram `/start` produced two
replies, violating the migration's behavior-freeze requirement. The plan's
document review predicted this exact gap; the implementation initially
shipped without the arbitration.

## Guidance

When two dispatch layers coexist during an engulf migration, write the
ownership rule into the new layer explicitly: exactly one layer responds
per event source, and the new layer's responsibilities on the legacy
source are limited to side effects (persistence, identity resolution).

```python
async def dispatch(self, envelope):
    await resolve_person(envelope.platform, envelope.sender_ref)
    await persist_envelope(envelope)

    if envelope.platform == 'telegram':
        ## Legacy aiogram handlers own command replies on Telegram;
        ## dispatching here too would answer every command twice (R6).
        return

    # ... command registry dispatch for native connectors ...
```

Pin the rule with a regression test asserting the legacy source produces
no reply from the new layer:

```python
await manager.dispatch(Envelope("telegram", "s", "c", "/start args"))
start_handler.assert_not_called()
manager.connectors['telegram'].send.assert_not_called()
```

## Why This Matters

Dual ownership is the default failure mode of strangler-fig migrations:
the new layer is wired to see everything (that is the point of the
chokepoint emission), so unless responding is explicitly withheld, it
responds. The result is user-visible duplication on the platform that has
real users — exactly where behavior was supposed to be frozen. An explicit
arbitration rule also documents the cutover seam: flipping the legacy
platform to registry-only dispatch later is a one-line change at a known
location, with the regression test marking what must flip with it.

## When to Apply

- Wrapping an existing event/handler framework behind a new abstraction
  while the old framework keeps serving production
- Emitting events from inside a legacy pipeline into a new bus, registry,
  or persistence layer
- Any transition state where two systems could plausibly answer the same
  stimulus

## Examples

Before (both layers answer):
legacy handler replies via the framework AND the emitted envelope matches
a registry command, so the new layer sends a second reply through the
connector.

After (ownership arbitrated):
the new layer persists and resolves identity for legacy-source events,
then returns; native connectors (XMPP, loopback) get full registry
dispatch. One stimulus, one responder, per source.

## Related

- docs/plans/2026-06-10-001-feat-connector-abc-plan.md — Deferred / Open
  Questions: "Registry and legacy aiogram handlers both answer same
  command" (the prediction this learning confirms)
