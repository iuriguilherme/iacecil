---
title: ZODB persistent objects returned after their connection closed
date: 2026-06-10
category: database-issues
module: persistence
problem_type: database_issue
component: database
symptoms:
  - "Functions returned Person objects created inside a closed `with db.transaction()` block"
  - "Attribute access on the returned objects worked only incidentally (cached state), risking ConnectionStateError on ghosted objects"
  - "Tests held and dereferenced the detached objects, baking the fragile pattern into the suite"
root_cause: wrong_api
resolution_type: code_fix
severity: medium
tags: [zodb, persistence, connection-lifecycle, ghost-objects, transaction]
---

# ZODB persistent objects returned after their connection closed

## Problem

`resolve_person` and `merge_persons` returned `persistent.Persistent`
objects out of a `with db.transaction()` block. After the block exits, the
connection that loaded those objects is closed — the objects are detached,
and any attribute access that needs to load state from the database raises
rather than reading.

## Symptoms

- Returned objects worked in tests only because their state happened to be
  in the in-memory cache when accessed
- Callers (the connector manager) used only the side effect and ignored the
  return value — masking the latent fragility
- Nothing fails until an object is ghosted before access, which is
  timing-dependent and surfaces far from the cause

## What Didn't Work

- Treating "the tests pass" as proof the API was sound: cached state made
  detached access succeed nondeterministically, which is exactly the kind
  of green that turns red under memory pressure or larger data

## Solution

Return plain identifiers, never live persistent objects, from functions
that own their transaction scope:

```python
# Before
async def resolve_person(platform, native_id) -> Person:
    with db.transaction() as connection:
        ...
        return person          # detached once the block exits

# After
async def resolve_person(platform, native_id) -> str:
    with db.transaction() as connection:
        ...
        return person.id       # plain string, safe anywhere
```

Callers that need object state open their own transaction and load by id.
Tests assert against fresh reads:

```python
db = await neutral.get_people_db()
with db.transaction() as conn:
    mappings = set(conn.root.people[person_id].mappings)
```

## Why This Works

A persistent object's validity is bounded by its connection's lifetime. A
function that opens and closes its own transaction therefore cannot hand a
live object across that boundary — the only values that safely cross are
plain data (ids, dicts, primitives). Returning ids makes the boundary
explicit and forces every reader to acquire state inside a live
connection.

## Prevention

- Functions that own a `with db.transaction()` block return plain data,
  never `persistent.Persistent` instances
- When object state is needed by the caller, pass the id and re-load
  inside the caller's own transaction
- In tests, never assert on attributes of an object obtained from a
  closed transaction — re-read through a fresh connection

## Related Issues

- docs/solutions/test-failures/tests-deleted-real-instance-zodb.md — same
  persistence layer; the isolation fixture there is what made these tests
  safe to run at all
