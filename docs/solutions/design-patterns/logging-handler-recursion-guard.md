---
title: Guarding a logging.Handler that delivers through the system it logs
date: 2026-06-11
category: design-patterns
module: log_sinks
problem_type: design_pattern
component: service_object
severity: high
applies_when:
  - "A stdlib logging.Handler delivers records through application code (network send, message bus, chat platform)"
  - "The delivery path itself logs (connector internals, client libraries)"
tags: [logging, handler, recursion, contextvar, asyncio, log-sinks, feedback-loop]
---

# Guarding a logging.Handler that delivers through the system it logs

## Context

`ConnectorLogHandler` routes logging records to chat conversations via the
bot's own connectors (`manager.send`). The delivery path is application
code that logs: connector failures log errors, client libraries log
retries. Without guards, a delivery-time log record re-enters `emit()`,
gets queued, gets delivered, logs again — a self-feeding loop that floods
the operator channel or recurses.

## Guidance

Three guards, layered (`src/iacecil/controllers/log_sinks.py`):

1. **Own-namespace drop.** `emit()` ignores records whose logger name
   starts with the handler module's own namespace — the handler can never
   feed itself directly.
2. **In-delivery contextvar.** Set a `contextvars.ContextVar` flag around
   the `manager.send` await; `emit()` drops any record raised while the
   flag is set in that task. Catches everything the delivery path logs —
   connector code, platform libraries — without naming them.

```python
_delivering = contextvars.ContextVar('log_sink_delivering', default=False)

token = _delivering.set(True)
try:
    await self.manager.send(envelope)
finally:
    _delivering.reset(token)
```

3. **Never-raise emit + non-logging fallback.** `emit()` wraps everything
   in try/except per the stdlib Handler contract; last-resort delivery
   failures write to `sys.stderr` directly — never back into `logging`.

Complete the pattern with a bounded drop-oldest queue (error storms must
not grow memory) and decouple emit (synchronous, any thread) from
delivery (async drain task owned by the component's lifecycle).

## Why This Matters

Logging infrastructure that uses the system it observes is a feedback
loop by construction. The contextvar guard is the load-bearing piece: it
is task-local, so concurrent dispatches keep logging normally while one
delivery is in flight, and it requires no registry of "loggers to
ignore" that would rot as libraries change.

Known residual: records emitted by the platform library's *background*
tasks (not the delivery task) are not covered by the contextvar — a sink
at DEBUG on platform X still amplifies X's own client-library chatter.
Filter those with a per-sink logger-name prefix instead.

## When to Apply

- Telegram/Matrix/Slack "error channel" handlers
- Any handler shipping records over the network through code that logs
  (HTTP clients, message queues)

## Examples

`tests/test_log_sinks.py::test_delivery_failure_no_recursion` — a send
that itself logs delivers once, queues nothing, and later records still
flow.

## Related

- docs/solutions/logic-errors/bounded-deque-requeue-eviction.md — the
  other sharp edge in the same drain loop
