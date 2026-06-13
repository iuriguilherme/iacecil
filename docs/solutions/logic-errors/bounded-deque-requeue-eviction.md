---
title: Requeueing into a bounded deque evicts the records being requeued
date: 2026-06-11
category: logic-errors
module: log_sinks
problem_type: logic_error
component: service_object
symptoms:
  - "Log records buffered for a not-yet-connected sink silently vanish under startup log volume"
  - "Bounded queue holds fewer boot-time records after a flush than before it"
root_cause: wrong_api
resolution_type: code_fix
severity: medium
tags: [deque, maxlen, asyncio, requeue, bounded-queue, log-sinks, eviction]
---

# Requeueing into a bounded deque evicts the records being requeued

## Problem

The log-sink drain (`src/iacecil/controllers/log_sinks.py`) held records for
not-yet-connected connectors in a local `requeue` list during a flush, then
put them back with `self.queue.extend(requeue)`. Under load, the records that
were deliberately being preserved were the exact ones silently lost.

## Symptoms

- Boot-time records buffered for a sink whose connector had not connected yet
  never arrived after the connector came up
- No error anywhere — `deque` with `maxlen` drops silently

## What Didn't Work

- Reasoning about the queue as if it were static during the flush: each
  `await manager.send(...)` inside the `while self.queue:` loop yields to the
  event loop, so other tasks' `emit()` calls refill the deque mid-flush. By
  the time `extend(requeue)` ran, the deque could already be at capacity.

## Solution

Prepend instead of append. On a `deque(maxlen=N)`, `extend` (append-side)
evicts from the left — the oldest items, which after a refill are exactly the
held-back records. `extendleft` evicts from the right — the newest items —
which is the correct overload policy (keep oldest undelivered, drop newest).

```python
# Before — boot records evicted when the deque refilled mid-flush
self.queue.extend(requeue)

# After — oldest undelivered records win; overload drops the newest
self.queue.extendleft(reversed(requeue))
```

`reversed()` preserves the requeued items' relative order at the front.

## Why This Works

`deque(maxlen=N)` evicts from the side opposite the insertion: `append`/
`extend` drop from the left, `appendleft`/`extendleft` drop from the right.
The hold-back records are the oldest in the system, so they must re-enter on
the left (front) — any append-side insertion makes them the first eviction
candidates the moment newer records compete for space.

## Prevention

- Any "drain a queue, hold some items back, put them back" loop over a
  bounded container must re-insert on the front, never the back
- In asyncio, treat every `await` inside a drain loop as a point where the
  queue mutates; never assume the capacity observed before the loop
- Regression test models the race directly: a send side-effect that refills
  the deque to capacity, then asserts the requeued record survives at index 0
  (`tests/test_log_sinks.py::test_requeued_boot_records_survive_midflush_refill`)

## Related Issues

- docs/solutions/design-patterns/logging-handler-recursion-guard.md — same
  module, the other sharp edge of routing logging through connectors
