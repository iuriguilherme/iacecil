---
title: "fix: Matrix E2EE key lifecycle so echo works in encrypted rooms"
date: 2026-06-16
type: fix
depth: standard
origin: user request ("matrix encryption + echo plugin still broken since v0.83.2")
---

# fix: Matrix E2EE key lifecycle so echo works in encrypted rooms

## Summary

The Matrix connector still cannot echo in encrypted rooms despite the prior
agent's fixes (E2EE dependency auto-detect, store dir creation, sync
`load_store()`, manual `decrypt_event` call). The remaining gap is the
**key-management lifecycle**: a manual `client.sync()` loop must call
`keys_upload()` / `keys_query()` itself, and must send with
`ignore_unverified_devices=True`. `AsyncClient.sync_forever()` does this
automatically; our hand-rolled loop in `matrix.py` does not. Without it the
bot never publishes its device keys, so no sender can share a Megolm session
key with the bot — every encrypted message arrives as an undecryptable
`MegolmEvent`, `_on_event` sees `body=None`, and the echo default-handler is
never reached.

## Problem Frame

- Symptom: logs show `Room <id> has an encrypted message that could not be
  decrypted`; echo plugin never replies in encrypted Matrix rooms.
- Verified environment (`.venv`): `matrix-nio==0.25.2`, `nio.crypto.ENCRYPTION_ENABLED=True`, `python-olm` importable, `load_store` is **sync**. So E2EE is fully supported at runtime — the blocker is logic, not deps.
- Confirmed via nio source: `AsyncClient.sync_forever` runs `keys_upload()`
  when `should_upload_keys` and `keys_query()` when `should_query_keys`. The
  manual loop in `listen()` runs neither.
- Confirmed: `AsyncClient.room_send(ignore_unverified_devices=False)` by
  default — sending into an encrypted room with any unverified device raises,
  so even a decrypted message would fail to echo back.

## Root Cause

`src/iacecil/connectors/matrix.py` drives its own `sync()` loop instead of
`sync_forever()`, but never replicates the key lifecycle `sync_forever`
performs. Two concrete defects:

1. **No `keys_upload` / `keys_query`** — device keys + one-time keys are never
   published; the bot is invisible to senders' key-sharing, so it can never
   obtain Megolm session keys → decryption always fails.
2. **`send()` omits `ignore_unverified_devices=True`** — replies into encrypted
   rooms raise `OlmUnverifiedDeviceError`.

## Key Technical Decisions

- **KTD1 — Replicate the lifecycle inline, keep the manual loop.** Do not
  switch to `sync_forever`; the manual loop is load-bearing for token
  persistence, fresh-sync suppression, and backoff. Add the same key calls
  `sync_forever` makes.
- **KTD2 — `ignore_unverified_devices=True` on both `room_send` and any group
  session share.** This is a bot with no UI to do interactive device
  verification; trust-on-first-use is the only workable posture. `room_send`
  already shares the group session internally, so no explicit
  `share_group_session` call is needed — passing the flag through is enough.
- **KTD3 — Guard all key calls behind `getattr`/`should_*` and the existing
  `e2e_supported` path** so plaintext-only mode (no libolm) is unaffected and
  no `AttributeError` fires when `self.client.olm` is absent.

## Implementation Units

### U1. Upload device keys after store load in `connect()`

**Goal:** Publish the bot's device + one-time keys once the encryption store is
loaded, so senders can establish Olm sessions and share Megolm keys.

**Files:** `src/iacecil/connectors/matrix.py`

**Approach:** After the existing `load_store()` block, if encryption is active
and `self.client.should_upload_keys`, `await self.client.keys_upload()`. Wrap
in try/except → warn-and-continue (key upload failure must not brick startup;
plaintext rooms still work).

**Patterns to follow:** mirror the existing `load_store` try/except warning
style already in `connect()`.

**Test scenarios:**
- Encryption active + `should_upload_keys=True` → `keys_upload` awaited once.
- `keys_upload` raises → warning logged, `connect()` still completes, `running=True`.
- Plaintext mode (no olm) → `keys_upload` never called (no AttributeError).

### U2. Run key maintenance each sync iteration in `listen()`

**Goal:** Replenish one-time keys and track device-list changes on every
successful sync, exactly as `sync_forever` does.

**Files:** `src/iacecil/connectors/matrix.py`

**Approach:** In the loop, after a successful sync (`next_batch` obtained,
retry state reset), before/after event dispatch: if
`getattr(self.client, 'olm', None)` then `if self.client.should_upload_keys:
await self.client.keys_upload()` and `if self.client.should_query_keys: await
self.client.keys_query()`. Failures here are logged and swallowed — they must
not break the sync loop or trip the backoff counter.

**Test scenarios:**
- `should_query_keys=True` after sync → `keys_query` awaited.
- `should_upload_keys=True` after sync → `keys_upload` awaited.
- key call raises → logged, loop continues to next sync, `failures` not incremented.
- Plaintext mode (`self.client.olm` is None/absent) → neither called.

### U3. Send with `ignore_unverified_devices=True`

**Goal:** Allow echo replies to be encrypted and delivered into encrypted rooms
without manual device verification.

**Files:** `src/iacecil/connectors/matrix.py`

**Approach:** In `send()`, pass `ignore_unverified_devices=True` to
`self.client.room_send(...)`. Harmless for unencrypted rooms (flag ignored).

**Test scenarios:**
- `send()` calls `room_send` with `ignore_unverified_devices=True`.
- Multi-chunk text → flag passed on every chunk.

## Verification

- Unit tests in `tests/test_matrix.py` cover U1–U3 with a mocked `client`
  exposing `should_upload_keys`, `should_query_keys`, `keys_upload`,
  `keys_query`, `room_send`, `olm`.
- Manual: against a real homeserver, a NEW message in an encrypted room (sent
  after the bot has uploaded keys) decrypts and the echo reply appears.
  Pre-existing messages sent before first key upload remain undecryptable —
  expected, not a regression.

## Scope Boundaries

In scope: key upload/query lifecycle + verified-device send flag.

### Deferred to Follow-Up Work
- Interactive / emoji device verification (TOFU is sufficient for a bot).
- Key backup / cross-signing.
- Re-decrypting historical messages received before first key upload.
