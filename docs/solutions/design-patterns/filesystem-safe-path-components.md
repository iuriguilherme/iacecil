---
title: Injective percent-encoding for cross-filesystem path components
date: 2026-06-11
category: design-patterns
module: persistence
problem_type: design_pattern
component: database
severity: high
applies_when:
  - "Platform-native identifiers (JIDs, Matrix room ids, chat ids) become file or directory names"
  - "Storage must be valid on HFS+, NTFS, ext4 and btrfs simultaneously"
  - "Two distinct identifiers must never map to the same path"
tags: [path-sanitization, percent-encoding, ntfs, case-insensitive, injective, filesystem, zodb]
---

# Injective percent-encoding for cross-filesystem path components

## Context

Per-chat message databases are stored at
`instance/zodb/bots/<bot_id>/<connector>/chats/<chat_id>.fs`, where the
components come from platform-native identifiers: XMPP JIDs
(`user@host.org`), Matrix room ids (`!AbC:server.org` — `:` is illegal on
NTFS), Telegram group ids (`-1001234`). The operator may run on any of
HFS+, NTFS, ext4 or btrfs, so one encoding has to be legal — and
collision-free — on all four at once.

## Guidance

Allowlist + percent-encode everything else, with three non-obvious rules
(`src/iacecil/controllers/persistence/path_utils.py`):

1. **Encode uppercase letters too.** HFS+ and NTFS are case-insensitive:
   `Room` and `room` are the same file there. Lowercasing breaks
   injectivity; encoding uppercase (`A` → `%41`) keeps both distinct on
   every filesystem. Allowlist is `a-z0-9._-` only.
2. **Encode the literal `%` (`%25`).** Otherwise input `%41` collides with
   input `A` — the escape character must never appear raw, or encoded
   output collides with raw input.
3. **Guard the lowercase NTFS reserved names.** `con`, `prn`, `aux`,
   `nul`, `com1`-`com9`, `lpt1`-`lpt9` pass a lowercase allowlist verbatim
   and NTFS reserves them case-insensitively *with any extension*
   (`con.fs` included). Encode the leading character of a reserved stem.
   Note the trap: testing with uppercase `CON` proves nothing — the
   uppercase rule already neutralizes it; the live hazard is lowercase.
   Same treatment for dot-only names (`.`, `..`).

Belt-and-braces at assembly time: after joining sanitized components,
assert the absolute path still lives under the storage base, so even a
sanitizer regression cannot traverse out
(`chat_store._chat_db_path`).

## Why This Matters

Path collisions here are silent data corruption — two chats sharing one
database file. Illegal characters are a hard crash on the operator's
filesystem only (works on ext4 in dev, breaks on the NTFS deployment).
Injectivity plus reversibility (`desanitize_component`) make the encoding
testable: round-trip equality proves no information was lost.

## When to Apply

- Any time external/untrusted identifiers become path components
- Especially when ids are case-sensitive (Matrix, base64-ish tokens) but
  the filesystem may not be

## Examples

```python
sanitize_component('user@host.org')   # 'user%40host.org'
sanitize_component('!AbC:server.org') # '%21%41b%43%3aserver.org'
sanitize_component('Room') != sanitize_component('room')  # case-safe
sanitize_component('%41') != sanitize_component('A')      # escape-safe
sanitize_component('con')             # '%63on' — NTFS reserved guarded
```

Test suite: `tests/test_path_utils.py` (legal alphabet, round-trip,
pairwise injectivity, reserved-with-extension).

## Related

- docs/solutions/database-issues/zodb-objects-returned-after-connection-close.md —
  same persistence layer
