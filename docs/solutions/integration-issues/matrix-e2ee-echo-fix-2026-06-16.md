---
title: Matrix Connector E2EE Decryption and Configuration Fixes
date: 2026-06-16
category: docs/solutions/integration-issues/
module: connectors.matrix
problem_type: integration_issue
component: tooling
symptoms:
  - "Connector crash: 'Encryption is enabled in the client configuration but dependencies for E2E encryption aren't installed'"
  - "Connector crash: 'unable to open database file' during SQLite store initialization"
  - "Connector crash: 'object NoneType can't be used in 'await' expression' (load_store is sync)"
  - "Bot fails to echo: 'Room <id> has an encrypted message that could not be decrypted'"
root_cause: logic_error
resolution_type: code_fix
severity: high
tags:
  - matrix
  - e2ee
  - nio
  - decryption
  - sqlite
---

# Matrix Connector E2EE Decryption and Configuration Fixes

## Problem
The Matrix connector was unable to echo messages in encrypted rooms due to multiple layers of integration failures with the `matrix-nio` E2EE implementation, leading to either hard crashes on startup or silent decryption failures.

## Symptoms
- **Hard crash on start**: `Encryption is enabled in the client configuration but dependencies for E2E encryption aren't installed` (missing `libolm-dev`).
- **Hard crash on initialization**: `unable to open database file` (missing `instance/matrix/store` directory).
- **Runtime error**: `object NoneType can't be used in 'await' expression` when calling `await self.client.load_store()`.
- **Decryption failure**: Logs showing `Room <id> has an encrypted message that could not be decrypted` despite keys being available in the store.

## What Didn't Work
- **Implicit Encryption**: Assuming that providing a `store_path` to `AsyncClient` would automatically enable E2EE.
- **Async Assumptions**: Assuming `load_store()` was an asynchronous method because it belongs to `AsyncClient`.
- **Standard Sync Loop**: Assuming that `nio` would automatically decrypt timeline events in a manual `client.sync()` loop (it only does this in the `sync_forever()` callback-driven mode).

## Solution
The implementation was updated with the following surgical fixes in `src/iacecil/connectors/matrix.py`:

1.  **Graceful E2EE Fallback**: Added auto-detection for the required C-libraries using `nio.crypto.ENCRYPTION_ENABLED`.
    ```python
    try:
        from nio.crypto import ENCRYPTION_ENABLED as e2e_supported
    except ImportError:
        e2e_supported = False
    
    if not e2e_supported:
        logger.warning("Matrix: E2EE dependencies missing. Falling back to plaintext.")
    ```

2.  **Directory Guard**: Explicitly ensured the SQLite store directory exists before initializing the client.
    ```python
    if e2e_supported:
        os.makedirs(STORE_DIR, mode=0o700, exist_ok=True)
    ```

3.  **Sync `load_store`**: Removed the `await` keyword from `self.client.load_store()` as it is a synchronous method.

4.  **Explicit Decryption**: Implemented manual decryption for `MegolmEvent`s in the sync loop and ensured the `room_id` is present on the event object.
    ```python
    if event.__class__.__name__ == 'MegolmEvent':
        if not getattr(event, 'room_id', None):
            event.room_id = room_id
        decrypted_event = self.client.decrypt_event(event)
        if decrypted_event:
            event = decrypted_event
    ```

5.  **Key lifecycle (the actually-load-bearing fix)**: Steps 1–4 are necessary
    but **not sufficient**. A manual `sync()` loop must also drive the key
    lifecycle that `AsyncClient.sync_forever()` performs internally. Without
    `keys_upload()` the bot's device + one-time keys are never published, so
    no sender can establish an Olm session to share a Megolm session key —
    every encrypted event then stays an undecryptable `MegolmEvent` and
    `decrypt_event()` (step 4) has no key to work with. This is why
    decryption "still failed" after steps 1–4. Replicate the lifecycle:
    ```python
    ## After load_store() in connect():
    if getattr(self.client, 'olm', None) and self.client.should_upload_keys:
        await self.client.keys_upload()

    ## After each successful sync() in the loop:
    if getattr(self.client, 'olm', None):
        if self.client.should_upload_keys:
            await self.client.keys_upload()
        if self.client.should_query_keys:
            await self.client.keys_query()
    ```
    And to *send* into an encrypted room from a headless bot (no interactive
    verification), pass `ignore_unverified_devices=True` to `room_send` or it
    raises `OlmUnverifiedDeviceError`.

6.  **Load full room state on (re)start**: Even with keys working, two
    further symptoms appeared — the bot echoed **plaintext** into an encrypted
    channel, and ignored DMs entirely. Both come from one cause: a manual
    `sync(since=token)` defaults to `full_state=False`, so on restart the
    client never reloads current room state. `room_send` only encrypts when
    `self.rooms[room_id].encrypted` is `True` (a flag set from the
    `m.room.encryption` *state* event), and the DM authorization path needs
    `member_count` from `m.room.member` state. Neither is present on an
    incremental resume → plaintext sends + failed DM auth. Fix: request full
    state on the first sync of each process.
    ```python
    response = await self.client.sync(
        timeout=30000, since=self.next_batch,
        full_state=not self._state_synced)
    # set self._state_synced = True after the first successful sync
    ```

## Why This Works
`matrix-nio`'s manual sync mode returns raw `MegolmEvent` objects which represent encrypted ciphertext. Unlike the callback-based `sync_forever`, the manual `sync()` response does not internalize decryption automatically for the returned events. Explicitly calling `decrypt_event()` with the correct `room_id` context allows the `OlmMachine` to retrieve keys from the SQLite store and transform the event into a readable `RoomMessageText` — **but only once the bot has uploaded its own keys (step 5) so a session key was ever shared with it.** `sync_forever` hides this by running `keys_upload`/`keys_query` for you; a hand-rolled loop must do it explicitly. Messages sent before the first `keys_upload` remain undecryptable forever (no key was ever shared); only messages sent afterward decrypt.

## Prevention
- **Dependency Awareness**: Always check `nio.crypto.ENCRYPTION_ENABLED` before attempting to use E2EE features to prevent crashes in environments without `libolm`.
- **Manual Sync Logic**: Remember that `client.sync()` requires manual event processing, including decryption of timeline events.
- **Store Persistence**: Use a stable `device_id` and a persistent `store_path` to avoid "Unknown Device" warnings and redundant verification requests.

## Related Issues
- `docs/solutions/architecture-patterns/echo-everywhere-multi-connector-architecture-2026-06-12.md`
- `docs/solutions/design-patterns/blocking-client-asyncio-bridge.md`
