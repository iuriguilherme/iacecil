---
title: sanitize_component is not idempotent, so migrations must not re-sanitize on-disk names
date: 2026-09-17
category: database-issues
module: persistence
problem_type: data_corruption
component: database
symptoms:
  - "Migrated matrix/xmpp chat keys read `%2521...` where runtime writes `%21...`"
  - "A migrated chat never matched new traffic for the same room: the same conversation split into two keys"
  - "Only identifiers containing non-safe characters were affected; numeric telegram and discord ids looked correct"
root_cause: wrong_assumption
resolution_type: code_fix
severity: high
tags: [zodb, persistence, migration, path-encoding, chat-store, idempotency]
---

# sanitize_component is not idempotent, so migrations must not re-sanitize on-disk names

## Problem

The chat-store consolidation migration (`scripts/migrate_chat_stores.py`) reads the old
per-chat layout `bots/<bot>/<connector>/chats/<chat>.fs` and writes each chat into one
storage per bot, keyed by `<connector>/<chat_id>`. The first version built that key with
`_chat_key(connector, chat_id)` — the same helper `store_message` uses — on the components
it read from disk.

For a matrix room that produced `matrix/%2521i%2553bs...` where runtime traffic writes
`matrix/%21i%53bs...`. Every migrated matrix and xmpp chat would have been stranded under a
key no live message could ever reach, while the conversation silently restarted under the
correct key.

## Root Cause

`sanitize_component` (`src/iacecil/controllers/persistence/path_utils.py`) is deliberately
*injective, not idempotent*. It percent-encodes `%` itself, precisely so that encoded output
can never collide with raw input: `!room:matrix.org` → `%21room%3amatrix.org`, and feeding
that back in gives `%2521room%253amatrix.org`. The property that makes the encoding safe is
the same property that makes double application wrong.

Components already on disk are *output* of the sanitizer. A migration that reads them has
crossed the encoding boundary already; applying the sanitizer again encodes a second time.

## Solution

Join on-disk components verbatim; sanitize only raw, platform-native identifiers.

```python
## Right: the names on disk are already sanitizer output
key = '{}/{}'.format(connector, chat_id)

## Wrong: double-encodes every id containing a non-safe character
key = _chat_key(connector, chat_id)
```

The regression test pins the invariant end to end: it derives the on-disk name from
`_chat_key`, migrates, and then asserts that a live `store_message` for the same room lands
in the migrated chat rather than creating a second one
(`tests/test_chat_store_consolidated.py::test_migrated_key_matches_runtime_key_for_encoded_ids`).

## Prevention

- Treat "is this value raw or already encoded?" as an explicit question at every boundary
  that reads persisted names. Sanitizers in this repo are injective encoders, not normalizers.
- Numeric ids (telegram, discord) pass through unchanged, so a migration smoke-tested only on
  them looks perfectly healthy. Exercise an identifier with `!`, `:`, `@`, or uppercase —
  matrix rooms and xmpp JIDs are the canonical cases.
- Run a migration against a *copy* of `instance/zodb/` and read the resulting keys before
  trusting record counts. Counts matched exactly in this bug; only the keys were wrong.
