---
title: Bridging a blocking client library into an asyncio connector
date: 2026-06-13
category: design-patterns
module: connectors
problem_type: design_pattern
component: service_object
severity: medium
applies_when:
  - "A connector's upstream client library is synchronous/blocking (requests, sseclient, urllib, a sync SDK) while the connector ABC is fully async"
  - "The library delivers events via callbacks on its own worker thread rather than an awaitable"
  - "Sibling connectors are async-native or self-looping and offer no pattern to copy"
tags: [asyncio, threading, blocking-io, connector, mastodon, run-coroutine-threadsafe, to-thread, event-loop-bridge]
---

# Bridging a blocking client library into an asyncio connector

## Context

The connector ABC (`src/iacecil/connectors/base.py`) requires every connector
to implement `connect/listen/send/disconnect` as coroutines; the manager runs
each as an asyncio task and dispatches `Envelope`s through an async pipeline.
The Mastodon connector (`src/iacecil/connectors/mastodon.py`) was the first
whose platform library — **Mastodon.py — is purely synchronous** (blocking
`requests` + `sseclient` streaming, no async mode). Every other connector
sidesteps this: matrix-nio is async-native (`await client.sync(...)`); slixmpp
runs its own internal loop and only needs a keep-alive sleep. Mastodon.py had
no async surface to await and no internal loop, so it needed an explicit bridge
from a blocking, thread-callback client into the connector's event loop.

## Guidance

Three moving parts: start the blocking stream off-loop, marshal worker-thread
callbacks back onto the loop, and offload every blocking send.

**1. Start the blocking stream without blocking the loop.** `stream_user(...,
run_async=True)` spawns the library's own daemon thread but the startup
handshake itself blocks; run it via `asyncio.to_thread`, then keep the
connector task alive with a sleep loop (as xmpp does):

```python
async def listen(self):
    loop = asyncio.get_running_loop()        # capture BEFORE entering the thread
    listener = self._make_listener(loop)
    self._stream_handle = await asyncio.to_thread(
        self.client.stream_user, listener, run_async=True)
    while self.running:
        await asyncio.sleep(1)
```

`get_running_loop()` must be called on the loop thread and the reference passed
into the listener — it is unavailable from inside the worker thread.

**2. Marshal callbacks from the worker thread.** The listener callback fires on
the streaming thread, where there is no running loop, so it cannot `await`. Use
`asyncio.run_coroutine_threadsafe` — the only correct way to submit a coroutine
to a loop from another thread:

```python
def _make_listener(self, loop):
    import mastodon
    connector = self
    class _Listener(mastodon.StreamListener):
        def on_notification(self, notification):
            if notification.get('type') != 'mention':
                return
            status = notification.get('status')
            if status is not None:
                ## runs on the worker thread → marshal back to the loop
                asyncio.run_coroutine_threadsafe(
                    connector._handle_status(status), loop)
    return _Listener()
```

**3. Offload blocking sends.** A bare `self.client.status_post(...)` would
freeze the loop for the network round-trip; wrap it:

```python
await asyncio.to_thread(self.client.status_post, chunk, in_reply_to_id=ref)
```

**4. Close the stream handle on disconnect**, guarded so a close failure does
not mask the teardown trigger:

```python
async def disconnect(self):
    self.running = False
    if self._stream_handle is not None:
        try:
            self._stream_handle.close()
        except Exception:
            pass
```

## Why This Matters

Any blocking I/O on the loop thread starves every other connector, the dispatch
pipeline, and reply handling for the duration of the call — one blocked
`status_post` during a burst stalls all platforms. `asyncio.to_thread` keeps the
loop free. The thread→loop direction is equally load-bearing: `loop.call_soon`
is not safe for coroutines from another thread, and `asyncio.run()` inside the
callback would spin up a *second* loop that does not share the connector's
state; `run_coroutine_threadsafe` is the one correct primitive.

**Known residual:** `run_coroutine_threadsafe` returns a
`concurrent.futures.Future` that is fire-and-forget here, so an exception
escaping `_handle_status` (or the persistence it calls) is silently swallowed.
Close the gap with a done-callback when visibility is needed:

```python
fut = asyncio.run_coroutine_threadsafe(connector._handle_status(status), loop)
fut.add_done_callback(
    lambda f: f.exception() and logger.error("dispatch error: %s", f.exception()))
```

## When to Apply

All three must hold:

1. The connector ABC requires async `connect/listen/send/disconnect`.
2. The client library is synchronous (blocking HTTP/streaming).
3. Event delivery is callback-based, not poll-based.

Degenerate cases need less: a **blocking but poll-based** library only needs
`asyncio.to_thread` on each poll inside a `while self.running` loop — no
`run_coroutine_threadsafe`. A library that **runs its own loop** (slixmpp-style)
needs only the keep-alive sleep — neither helper.

## Examples

Naive vs. correct, at the two boundaries:

```python
## BAD — blocks the loop thread for the life of the stream
async def listen(self):
    self.client.stream_user(listener)

## BAD — cannot await on the worker thread (no running loop there)
def on_notification(self, notification):
    await connector._handle_status(status)
```

The correct forms are shown under Guidance (1) and (2). Contrast the
async-native sibling, where dispatch is a direct inline `await` because
everything is on one thread:

```python
## src/iacecil/connectors/matrix.py
response = await self.client.sync(timeout=30000, since=self.next_batch)
for event in events:
    await self._on_event(room_id, event)
```

## Related

- `docs/solutions/architecture-patterns/connector-self-declared-activation.md` —
  how the manager discovers and activates a connector; this bridge is what runs
  inside that connector's lifecycle once active.
- `docs/solutions/design-patterns/logging-handler-recursion-guard.md` —
  adjacent sync→async boundary in the same codebase (`log_sinks.py`), solved
  the *other* way: a queue plus an owned drain task instead of
  `run_coroutine_threadsafe`. Useful contrast when choosing between the two.
- `docs/solutions/logic-errors/bounded-deque-requeue-eviction.md` — the sharp
  edge to watch if a staging queue is ever added between the sync callback and
  async send.
