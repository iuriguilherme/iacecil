---
date: 2026-06-16
topic: pluggable-persistence
---

# Pluggable Persistence + Model Neutrality

## Summary

Make persistence database-agnostic by splitting the clean persistence layer into
concern-scoped stores — identity, global message records, per-chat storage — each
bound to a backend through config. An operator picks ZODB, SQLite, both, or none
per connector. Shared keys keep records joinable across backends, and ZODB plus
SQLite both ship so a second, structurally different backend proves the seam.

---

## Problem Frame

ia.cecil's stated approach is composability via runtime-loadable modules: any
combination of platform, community, and experiment assembled without forking. The
connector layer realizes this — each connector declares its own activation rule and
loads dynamically, a failing one is marked down without stopping siblings. Persistence
never got the same treatment. The clean layer (`src/iacecil/controllers/persistence/neutral.py`,
`src/iacecil/controllers/persistence/chat_store.py`) hardcodes ZODB: `Person` inherits
`persistent.Persistent`, records live in `BTrees.OOBTree`, and `dispatch` calls free
functions directly.

ZODB itself is not the pain. The pain is that the architecture offers no seam — there
is no way to run a different database for a data-handling step, no way to add a backend
alongside or in place of ZODB, and no way to let one bot's connector store to SQLite
while another stays on ZODB. The goal is the seam, with ZODB kept as one valid backend.

---

## Key Decisions

**Concern-scoped stores, not one backend interface.** The clean layer splits into three
stores by data concern: an identity store (`resolve_person`, `merge_persons`), a message
store (global neutral records / `persist_envelope`), and a chat store (per-chat
`store_message`). Each binds to its own backend. This matches the operator model "a
different database for each step of data handling" and lets identity stay authoritative
while message and chat fan out.

**Identity is single-authority; message and chat are per-connector.** A Person maps
multiple `(platform, native_id)` pairs to one human and is cross-platform by definition,
so the identity store is one global backend — per-connector identity would fork the same
human into divergent records. Backend selection per connector governs the message and
chat stores only.

**Referential consistency, not transactional.** The same `person_id` and `msg_id` appear
identically in every store that holds a given record, so records stay joinable across
backends. Each store still writes independently — a failure in one is isolated and logged,
preserving the current per-step `try/except` in `dispatch`. No cross-backend atomic commit.

**Shared keys minted once at the authoritative layer.** `person_id` is minted by the
identity store's get-or-create. `msg_id` is minted once above the fan-out and passed to
every active message/chat backend, which stores the id it is given. Fan-out backends are
pure sinks that never mint their own ids — otherwise a "both"-mode message would carry a
different `msg_id` in each store and stop being joinable.

**Models drop `persistent.Persistent`.** `Person` becomes a plain dataclass like
`Envelope` already is; the message record stays a plain dict (it already is one). Models
are defined once and mapped per-backend by that backend's serializer. The boundary returns
ids and plain values only, never live persistent objects.

**ZODB and SQLite both ship in v1.** They are literal per-connector config choices, so a
working second backend is part of the deliverable. An ABC with one implementation would
not prove agnosticism.

---

## Requirements

### Backend contract

R1. A backend contract exists per concern — identity, message, chat — exposing only the
operations the clean layer's call sites exercise today: identity = `resolve_person`,
`merge_persons`; message = `persist_envelope`; chat = `store_message`; plus lifecycle
(`close`). The contract is write-only.

R2. Every contract method is async at the boundary and returns ids or plain values, never
a live backend object. Blocking I/O (fsync, file open) runs off the event loop so a
backend never stalls the shared connector loop.

R3. A backend declares its own activation the way connectors do (a self-declared
`is_active` / `required_keys` rule), and is discovered dynamically by name from config —
no per-backend branching in the loader.

### Backend selection and fan-out

R4. An operator selects ZODB, SQLite, both, or none for a connector's message and chat
stores through config, mirroring how a connector's config section carries its credentials.

R5. A concern binds to an ordered list of backends. The first is authoritative (mints
shared keys, serves any future reads); the rest are mirror sinks. A single backend is a
list of one; "both" is a list of two; "none" is empty.

R6. When several backends are active for a concern, the same record is written to each with
identical shared keys (`person_id`, `msg_id`).

R7. "none" for a connector skips all persistence for that connector's traffic, including
identity resolution — nothing is written and no `person_id` is minted.

### Consistency and isolation

R8. The identity store is a single global authoritative backend across all connectors; it
mints `person_id` and owns the `(platform, native_id) -> person_id` mapping.

R9. Each store write is isolated: a failure in one store (or one fan-out backend) is logged
and does not skip the other stores or block command dispatch. Identity never forks; a mirror
store may lag.

R10. The dual-schema invariant is preserved across backends — the global message store keys
the platform value as `platform`, the per-chat store keys it as `connector`. No backend
unifies the two without migrating both stores and their readers.

### Models

R11. `Person` is a plain dataclass with no ZODB base class; mappings are a plain collection.
The message record is a plain dict / typed record. Neither model imports `persistent`,
`BTrees`, or `transaction`.

R12. Each backend owns a serializer mapping the neutral models to and from its native form.
The ZODB backend wraps them at write time; SQLite maps to rows.

### Backends

R13. A ZODB backend reproduces today's `neutral.py` / `chat_store.py` behavior — conflict
retry, per-chat path sanitization, native-id dedupe, LRU of open handles — behind the
contract, so a bot defaulting to ZODB is unchanged.

R14. A SQLite backend implements the same contract: get-or-create (upsert) for identity,
`INSERT OR IGNORE` on a unique native-id index for dedupe, file-based storage. It runs with
WAL mode and a busy_timeout to absorb single-writer contention.

### Config and tests

R15. Backend selection lives in a parallel `persistence:` config section in `BotConfig` /
`instance/` configs, not in `config.py` default values beyond a neutral default section. The
section carries the global identity backend and a per-connector map of backend lists
(`persistence.connectors.<name>: [zodb, sqlite]` for both, `[sqlite]` for one, `[]` for none).
It sits alongside `plugins:` / `telegram:` / `discord:`, mirroring the `plugins` enable/disable
precedent. The default keeps every existing bot on ZODB.

R16. The test-isolation seam stays as cheap as today's — backends are repointable to a temp
location per test, and the autouse isolation fixture in `tests/conftest.py` keeps working.

---

## Acceptance Examples

AE1. **Covers R5, R6, R8.** Connector configured "both." A message arrives. Identity store
(global ZODB) mints `person_id=uuid-A`. The message store fans out one record to ZODB and one
to SQLite, both carrying `person_id=uuid-A` and the same `msg_id`. The two records are joinable.

AE2. **Covers R7.** Connector configured "none." A message arrives. No `person_id` is minted,
no message or chat record is written, command dispatch still runs.

AE3. **Covers R9.** Connector configured "both." The SQLite write raises. The ZODB record is
still written, the error is logged, identity is unchanged, and dispatch continues.

AE4. **Covers R13.** Bot with no persistence config. Behavior is identical to today: ZODB
stores, conflict retry, dedupe, sanitized chat paths.

---

## Scope Boundaries

**Deferred for later:**
- Reads / queries. The clean layer is write-only in production today — neither `neutral.py`
  nor `chat_store.py` defines a read function, and the admin/plots routes read from legacy
  `zodb_orm`. A query contract becomes a future concern-slot when a real reader exists, so it
  is not invented now against legacy negative-slice semantics.
- `merge_persons` is part of the identity contract but has no production caller (tests and
  maintenance only); it ships but is not a driver of the design.
- Additional backends (SQLAlchemy + Alembic for server/Postgres, document store) — the
  contract is shaped to admit them, but only ZODB and SQLite ship now.
- Migration of legacy `instance/zodb/` data. Legacy data is disposable; a one-time export is
  out of scope here.

**Outside this effort's identity:**
- Decoupling legacy `zodb_orm` (~15 call sites across plugins, furhat, web routes, pickling
  aiogram objects). It stays frozen behind its current surface — a separate epic that must not
  be coupled to the clean-layer seam.
- Transactional / distributed-commit consistency across backends, and any reconciliation/repair
  pass. Referential consistency is the chosen guarantee.

---

## Dependencies / Assumptions

- The clean layer has exactly one production write consumer: `ConnectorManager.dispatch`
  (`src/iacecil/connectors/__init__.py:163,168,172,214,215`). The write-path blast radius is
  that one module. Verified.
- `flask-sqlalchemy` is already a Pipfile dependency and `config.py` carries commented
  `sqlalchemy_database_uri` lines — latent SQL intent, but the chosen SQLite backend uses
  stdlib `sqlite3` (or `aiosqlite`), not necessarily SQLAlchemy.
- The connector pattern (`src/iacecil/connectors/base.py`, `ConnectorManager._load_connectors`)
  is the template for backend registration and failure isolation. Assumed stable.
- Telegram-origin envelopes are persisted but not command-dispatched (legacy aiogram owns
  Telegram replies); the persistence seam does not change that arbitration.

---

## Outstanding Questions

**Deferred to planning:**
- Whether the SQLite backend uses stdlib `sqlite3` behind `asyncio.to_thread` or `aiosqlite`.
- Exact table shape for the SQLite backend (people / mappings / messages / chat).
- Whether the three concern contracts are three ABCs or one ABC with a concern tag.

---

## Sources / Research

- `docs/ideation/2026-06-16-pluggable-persistence-and-model-neutrality.md` — origin ideation,
  ranked ideas and rejected alternatives.
- `src/iacecil/controllers/persistence/neutral.py` — identity + global message store, `Person(persistent.Persistent)`, dual-schema note, conflict retry.
- `src/iacecil/controllers/persistence/chat_store.py` — per-chat store, path sanitization, native-id dedupe, LRU handles.
- `src/iacecil/connectors/__init__.py:155-217` — `dispatch`, the sole write consumer; `person_id` mint + stamp flow.
- `src/iacecil/connectors/base.py` — `BaseConnector` activation/registration template.
- `tests/conftest.py` — autouse persistence isolation fixture the seam must preserve.
- `CONCEPTS.md` — Person, Neutral Record, Chat Store, Connector vocabulary.

---

## Deferred / Open Questions

### From 2026-06-16 review

- **`none` / global-identity contradiction (P1, coherence).** R7 and AE2 say a "none"
  connector mints no `person_id`, but Key Decisions and R8 say identity is one global
  authoritative store across all connectors. Resolve whether "none" skips only message/chat
  persistence (identity resolution still runs) or gates `resolve_person` at dispatch. Pairs
  with the gate-location FYI below.
- **`both`/fan-out may exceed the goal (P1, product-lens + scope-guardian).** Ordered backend
  lists (R5), identical-key fan-out (R6), mirror-lag isolation (R9), and AE1/AE3 exist only to
  run two live backends at once, a scenario no operator need in the doc explains. Decide: name
  the scenario (e.g. zero-downtime migration) or descope `both` to a later slice and ship v1 as
  single-backend-per-concern substitution. The two entries below dissolve if `both` is descoped.
  - **Shared `msg_id` vs dedupe skip (P1, adversarial).** Chat store returns `None` on native-id
    dedupe while the message store always writes; one `msg_id` across both sinks leaves a global
    record with no matching chat record, silently breaking AE1 joinability.
  - **Message vs chat dedupe asymmetry (P1, adversarial).** Only the chat store dedupes on
    native-id today; the global store never does. R6's "same record, identical keys" is impossible
    for duplicates, yet R13 demands ZODB reproduce today's asymmetric behavior.
- **"Referential consistency" undefined for the dangling direction (P2, adversarial).** Identity
  can commit while message writes fail (R9 isolation), leaving a `person_id` with no referencing
  records. Define the guarantee: keys are byte-identical in any store that holds the record,
  presence is not guaranteed, orphan `person_id`s are accepted and unrepaired.
- **"Write-only contract" vs read-modify-write (P2, adversarial).** R1 says "write-only," but
  `resolve_person` is get-or-create and R5 says the authoritative backend "serves any future
  reads." Reframe as "write-and-resolve, no query API" — identity read-modify-write, message/chat
  append-only, no ad-hoc query surface.
