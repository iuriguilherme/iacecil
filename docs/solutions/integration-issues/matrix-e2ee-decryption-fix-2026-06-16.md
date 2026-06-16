---
title: "Matrix E2EE decryption: Fix for missing dependencies, store directory, and manual decryption loop"
date: 2026-06-16
category: docs/solutions/integration-issues
module: src/iacecil/connectors/matrix.py
problem_type: integration_issue
component: tooling
severity: high
symptoms:
  - "Hard crash on startup: 'ImportError: No module named libolm'"
  - "Database error: 'unable to open database file' for client.db"
  - "Async mismatch: 'NoneType' object cannot be used in 'await' expression (for load_store)"
  - "Messages in encrypted rooms appear as 'Encrypted message' or empty text"
root_cause: incomplete_setup
resolution_type: code_fix
tags:
  - matrix
  - e2ee
  - matrix-nio
  - encryption
  - libolm
  - sqlite
---

# Matrix E2EE decryption: Fix for missing dependencies, store directory, and manual decryption loop

## Problem
The Matrix connector failed to decrypt messages in encrypted rooms due to a combination of missing host dependencies, uninitialized filesystem paths, and missing explicit decryption calls in the custom event loop. This blocked the "Echo everywhere" feature from working on encrypted Matrix channels.

## Symptoms
- **Hard Crash**: The bot failed to start if `encryption: True` was set because `libolm` (the C library for Matrix encryption) was missing from the host system.
- **SQLite Error**: `sqlite3.OperationalError: unable to open database file` when the bot attempted to create its encryption store because the parent directory `/home/user/.iacecil/matrix/store/` did not exist.
- **Message Visibility**: Messages received in encrypted rooms were captured as "Encrypted message" or empty strings because the connector didn't explicitly call the decryption method on incoming events.
- **Async Errors**: `TypeError` or `NoneType` errors when calling `client.load_store()` if treated as synchronous when the installed `matrix-nio` version expects it to be awaited.

## What Didn't Work
- **Automatic Decryption**: Assuming `matrix-nio` decrypts events automatically in a manual sync loop. It doesn't; you must manually trigger decryption for each encrypted event.
- **Default Store Path**: Leaving the store path to the library default, which often points to locations the bot doesn't have permission to write to or that don't exist by default.

## Solution
The fix required ensuring host-level dependencies were present, creating the store directory structure, and updating the event processing loop to handle decryption explicitly.

### 1. Host Dependency (libolm)
Matrix E2EE requires the `libolm` C library.
```bash
sudo apt-get install libolm-dev  # Ubuntu/Debian
```

### 2. Store Initialization
Ensure the directory exists before the client attempts to open the SQLite database.

```python
## src/iacecil/connectors/matrix.py
import os
store_path = self.config.get('store_path', 'instance/matrix/store')
os.makedirs(store_path, exist_ok=True)

# Use AsyncStore for E2EE
from nio import AsyncClient, AsyncClientConfig
client_config = AsyncClientConfig(store_sync_diff=True)
client = AsyncClient(homeserver, user_id, store_path=store_path, config=client_config)

# load_store MUST be awaited in modern nio
await client.load_store()
```

### 3. Explicit Decryption Loop
When using a custom sync loop (rather than `client.sync_forever`), encrypted events must be decrypted manually.

```python
## In the sync loop:
for room_id, room in response.rooms.invite.items():
    # ... handle invites ...

for room_id, room in response.rooms.join.items():
    for event in room.ephemeral:
        # ... handle typing ...
    
    for event in room.timeline.events:
        if isinstance(event, MegolmEvent):
            # nio needs the room_id context for decryption
            event.room_id = room_id
            decrypted_event = client.decrypt_event(event)
            if isinstance(decrypted_event, RoomMessageText):
                # Now the event text is readable
                await self._on_message(room_id, decrypted_event)
```

## Why This Works
- **libolm**: Required for the cryptographic primitives of the Megolm and Olm protocols used by Matrix.
- **AsyncStore**: `matrix-nio` uses a SQLite backend to store session keys. It cannot create directories recursively, so `os.makedirs` is mandatory.
- **Manual Decryption**: In a manual sync loop, the library provides the raw `MegolmEvent`. Calling `decrypt_event` uses the keys stored in the local database to recover the original plaintext and returns a new event object (e.g., `RoomMessageText`).

## Prevention
- **Dependency Checks**: Add a startup check for `libolm` availability if encryption is enabled.
- **Path Guard**: Always use `os.makedirs(..., exist_ok=True)` when initializing connectors that require local persistence.
- **Version Pinning**: Use `matrix-nio[e2ee]` in `requirements.txt` to ensure the Python-side crypto dependencies are pulled in.

## Related Issues
- `docs/solutions/build-errors/aiogram-matrix-nio-dependency-conflict-2026-06-13.md`
- `docs/solutions/design-patterns/blocking-client-asyncio-bridge.md`
