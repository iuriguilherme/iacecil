# Ideation: Pluggable Persistence + Model Neutrality

**Date:** 2026-06-16
**Mode:** repo-grounded
**Subject:** Break the hardcoded ZODB coupling so persistence and domain models become pluggable through the same plugin-style architecture ia.cecil already uses for connectors.
**Output:** ranked, critically-evaluated ideas (no production code). Next step is `ce-brainstorm` on the chosen idea, then `ce-plan`.

---

## Grounding Context

### The reference pattern (connectors)
- `connectors/base.py` — `BaseConnector(ABC)` defines a 4-method contract (`connect/listen/send/disconnect`) plus a **self-declared activation rule**: `required_keys` (all truthy in the config section) or an overridden `is_active(conf)`. The manager never hardcodes per-platform checks.
- `connectors/__init__.py::ConnectorManager._load_connectors` — discovers connectors **dynamically** by iterating config dict sections, `import_module('.'+name, 'iacecil.connectors')`, fetching the `Connector` class, and activating it iff `is_active(conf)`. Missing connector module → quiet skip; missing dependency → loud error; sibling failures never crash the manager.
- `run_all` uses `asyncio.gather(..., return_exceptions=True)` for **per-connector failure isolation**.

### What the persistence layer actually needs (the real contract surface)
From `connectors/__init__.py::ConnectorManager.dispatch` — the **only** consumer of the clean persistence layer — the operations exercised are exactly:
1. `resolve_person(platform, sender_ref) -> person_id` (get-or-create + mapping)
2. `persist_envelope(envelope, direction) -> msg_id` (append normalized record to global `messages.fs`)
3. `store_message(bot_id, envelope, direction) -> msg_id | None` (append to per-chat store, with native-id dedupe)
4. `merge_persons(id1, id2) -> id` (registry maintenance; **not** called from dispatch — used by maintenance/admin flows)
5. Read/query: admin + plots routes read message lists with offset/limit; `merge` and registry inspection in tests.

### Where ZODB coupling lives (and how much)
- **Clean layer — 1 write call site.** `neutral.py` (Person registry + global `messages.fs`) and `chat_store.py` (per-chat store) are consumed for writes by exactly **one** module: `connectors/__init__.py`. This is the high-leverage, low-blast-radius surface.
- **Legacy layer — ~15 call sites.** `zodb_orm.py` is imported across `plugins/admin.py`, `plugins/garimpo.py`, `plugins/natural.py`, `plugins/tc.py`, `plugins/openai.py`, the whole `furhat_bot/` tree, `controllers/log.py`, and the Quart `admin`/`plots` routes. Tangled, pickles aiogram objects, read-only legacy data. **Decoupling this is a separate, much larger project** and must not be coupled to the clean-layer abstraction.
- Config already hints at SQL: `config.py` has commented `sqlalchemy_database_uri` lines and **`flask-sqlalchemy` is already a Pipfile dependency**. ZODB stack: `zodb==6.1`, `zc.zlibstorage`, `BTrees`, `transaction`, `persistent`.
- Test isolation (`tests/conftest.py`) monkeypatches module-level `zodb_path` on `neutral` + `chat_store` and resets the `_*_db` globals. Any abstraction must keep an equally cheap test-isolation seam.

### Models bound to ZODB
- `models/envelope.py` — **already neutral** (frozen dataclass, `raw` excluded from repr and never persisted). The model of what neutrality looks like.
- `Person(persistent.Persistent)` in `neutral.py` — bound to ZODB via base class + `BTrees.OOBTree.TreeSet` for `mappings`. The message "record" is **already a plain dict** (not a persistent class), keyed in an OOBTree — so message records are 80% neutral already; only Person carries the `persistent.Persistent` base.

### Concurrency / correctness invariants any backend must preserve
- **Commit (fsync) is blocking → runs via `asyncio.to_thread`** so it never stalls the single event loop shared by all connectors (see `blocking-client-asyncio-bridge.md`).
- **Return plain ids, never live persistent objects** out of a transaction scope (see `zodb-objects-returned-after-connection-close.md` — a documented past bug). The contract must be values-only at its boundary.
- **Per-step failure isolation** in `dispatch`: person-resolve / neutral-persist / chat-store each wrapped independently so one failure doesn't skip the others.
- **Concurrent-writer conflict retry** (`_commit_with_retry`, 5 attempts on `ConflictError`) — a ZODB-specific concern; a SQL/doc backend handles concurrency differently (transactions/upserts), so this belongs *inside* a backend, not in the contract.

### Topic axes
1. Backend contract (operations the interface exposes)
2. Model neutrality (decouple Person/records from `persistent.Persistent`)
3. Registration & loading (discover/select a backend like a connector)
4. Failure isolation & concurrency (to_thread, per-step isolation, conflict handling)
5. Config wiring & migration (`BotConfig`/`instance/`; legacy ZODB story)

---

## Ranked Survivors

> Generation produced ~30 candidates across six frames (extend-the-pattern, invert/minimize, steal-from-adjacent, first-principles contract, failure-mode, migration-cost). After adversarial critique, the survivors below remain. Rejected ideas and reasons are listed at the end.

### #1 — `PersistenceBackend` ABC + connector-style registry, scoped to the *clean* layer only

**The idea.** Define `controllers/persistence/base.py::PersistenceBackend(ABC)` with the exact methods `dispatch` needs, mirroring `BaseConnector` one-for-one:

```
class PersistenceBackend(ABC):
    required_keys: tuple = ()
    @classmethod
    def is_active(cls, conf: dict) -> bool: ...      # same self-declared activation as connectors
    async def resolve_person(self, platform, native_id) -> str: ...
    async def merge_persons(self, id1, id2) -> str: ...
    async def persist_envelope(self, envelope, direction='in') -> str: ...
    async def store_message(self, bot_id, envelope, direction='in') -> str | None: ...
    async def query_messages(self, bot_id, conversation_ref, offset=0, limit=0) -> tuple[int, list[dict]]: ...
    async def close(self) -> None: ...
```

A `PersistenceManager` (or a module-level `get_backend(bot_config)`) reads a new `persistence` config section, imports `persistence.backends.<name>`, fetches its `Backend` class, and activates it iff `is_active(conf)` — byte-for-byte the connector discovery loop. Default backend = `zodb` so nothing changes until a bot opts in. `dispatch` calls `backend.resolve_person(...)` etc. instead of importing free functions.

**Backends served:**
- **ZODB** (default, wraps current `neutral.py`/`chat_store.py` verbatim) — trivial, preserves all data, zero migration.
- **SQLite-direct** (stdlib `sqlite3` via `to_thread`, or `aiosqlite`) — *best fit*. File-based like ZODB, zero new heavy dependency, embedded feel. The 5 operations map to 3 tables (`people`, `mappings`, `messages`) with an upsert for resolve and a unique index for native-id dedupe.
- **SQLAlchemy** (Postgres/SQLite + Alembic) — served well for multi-tenant/server deploys; the contract is small enough that an ORM is almost overkill but Alembic migrations are a real bonus.
- **Document store** (MongoDB/TinyDB) — served *naturally*: the message record is already a dict; Person is a tiny doc. Closest to ZODB's object model.

**Why it leads.** It is the *only* idea that extends the proven repo pattern with no new shape, and its blast radius is exactly one file (`dispatch`) because the clean layer has a single consumer. Activation, failure isolation (`return_exceptions`/per-step try-blocks already exist in `dispatch`), and the to_thread discipline all transfer directly. The contract is *derived from actual call sites*, not invented — six methods, no speculative surface.

**Honest weaknesses.**
- Five async methods is a wider contract than connectors' four, and `query_messages`' offset/limit semantics are currently messy (the admin routes do negative-slice arithmetic). Pin the query contract in `ce-brainstorm` before coding or it will leak ZODB slicing assumptions into the ABC.
- Per-chat `store_message` carries a `bot_id` and path-sanitization concern that the global `persist_envelope` doesn't — the two stores have deliberately distinct schemas (`platform` vs `connector` key). The ABC must not paper over that or it breaks the documented dual-schema invariant.
- Does nothing for the ~15 legacy `zodb_orm` call sites — and shouldn't. Must be explicitly scoped as "clean layer only" or scope-creeps into the swamp.

---

### #2 — Plain-dataclass domain models + per-backend serializer (the model-neutrality half)

**The idea.** Make `Person` a frozen/plain dataclass (`id: str`, `mappings: frozenset[tuple[str,str]]`) living in `models/`, exactly like `Envelope` already is. The message record stays a plain dict (already neutral) but gets a typed `MessageRecord` dataclass for clarity. Each backend owns an **adapter/serializer** that maps these neutral models to/from its native form: ZODB wraps them in a `persistent.Persistent` shell at write time; SQL maps to rows; doc store dumps to a document. Models never inherit `persistent.Persistent`.

**Why it survives.** This is the load-bearing half of "model neutrality" and directly resolves the documented ghost-object bug (`zodb-objects-returned-after-connection-close.md`): if the boundary only ever returns dataclasses/ids, no live persistent object can leak. It's the natural companion to #1 — #1 is the *behavior* contract, #2 is the *data* contract. `Envelope` proves the pattern works in this repo.

**Backends served:** all equally — that's the point. Plain models + per-backend mapping is the standard ORM-agnostic approach (vs. an ORM-native model per backend, which couples models to one library).

**Honest weaknesses.**
- ZODB's whole value is transparent object persistence; forcing it through a serializer makes the ZODB backend slightly *more* code than today (a wrapping step), purely to serve neutrality. Acceptable tax, but real.
- `Person.mappings` as a `frozenset` loses ZODB's incremental `TreeSet` conflict resolution — the ZODB backend must reconstruct conflict-safe merging internally. Concurrency invariant moves into the backend (which is correct per #1's philosophy, but it's work).
- Weak on its own — without #1's contract it's just a refactor with no swap capability. Should be brainstormed *together with* #1, not as a rival.

---

### #3 — SQLite-direct as the reference second backend (proof the abstraction is real)

**The idea.** Don't stop at the ABC — implement **one** non-ZODB backend to prove the seam, and make it SQLite-direct (stdlib `sqlite3` behind `to_thread`, or `aiosqlite`). Three tables, an upsert for `resolve_person`, `INSERT OR IGNORE` on a unique native-id index for dedupe, `LIMIT/OFFSET` for queries. Ship ZODB + SQLite together; a one-time migration script reads the OOBTrees and bulk-inserts.

**Why it survives.** An ABC with one implementation is unfalsifiable — the contract only earns trust when a second, *structurally different* backend round-trips the same models. SQLite is the lowest-cost such proof: no new heavy dependency, file-based (preserves ZODB's embedded operational story), and `LIMIT/OFFSET` is genuinely cleaner than the current negative-slice arithmetic. It also gives the project real SQL queryability the ZODB stores never had.

**Backends served well:** SQLite (excellent), and by extension validates the contract for SQLAlchemy/doc later. Serves Postgres *poorly* directly (no pooling/async driver) — that's SQLAlchemy's job.

**Honest weaknesses.**
- SQLite write concurrency is single-writer; under the concurrent-writer bursts the `_commit_with_retry` logic exists for, you trade `ConflictError` retries for `database is locked` retries. Net-neutral, but not free — WAL mode + a busy_timeout is mandatory, not optional.
- Schema-versioning burden the doc-store and ZODB backends sidestep. For 3 tables it's tolerable; without Alembic you hand-roll migrations.
- Scope risk: this is implementation, and ideation shouldn't over-commit. Frame as "the brainstorm/plan should include exactly one reference backend, recommend SQLite" rather than "build SQLite now."

---

### #4 — `persistence:` config section mirroring the `plugins` enable/disable shape

**The idea.** Add one config section to `DefaultBotConfig`:
```
persistence: dict = {'backend': 'zodb', 'path': 'instance/zodb', 'uri': None, ...}
```
`backend` selects the module under `persistence/backends/`; remaining keys are the backend's `required_keys`/config — exactly how `telegram: dict` carries `token`/`users`. Default `zodb` keeps every existing bot unchanged. Per `CLAUDE.md`, this goes in `BotConfig`/`instance/`, never in `config.py` defaults beyond the neutral default section.

**Why it survives.** Backend selection *must* live somewhere, and this is the convention-matching home — it makes "select a backend by config section" literally identical to "select a connector by config section." Cheap, obvious, and it's the wiring that makes #1 usable.

**Honest weaknesses.**
- Connectors can run *several* at once (multi-platform); persistence is realistically *one* backend per bot. So the activation loop degenerates to "pick the one named backend" — slightly forcing the connector analogy. A single `backend:` key may be cleaner than full `is_active` discovery. Worth resolving in brainstorm: full registry vs. simple name lookup.
- Secondary by the prompt's own framing — list it as a supporting decision under #1, not a standalone headline.

---

### #5 — Leave legacy `zodb_orm` frozen behind a read-only facade; never abstract it

**The idea.** Explicitly *decide* that the ~15-consumer legacy layer is out of scope: wrap it (if at all) in a thin read-only `LegacyStore` facade and freeze it. All new pluggability targets the clean layer only. Legacy data stays ZODB forever or gets a one-shot export, decoupled from the backend abstraction.

**Why it survives (as a guardrail, not a feature).** The single biggest risk to this whole effort is scope-bleed into the legacy swamp — 15 tangled call sites that pickle aiogram objects and span furhat/plugins/web. Naming "don't" as an explicit survivor protects #1-#4 from drowning. The prompt grants that backward-compat is not required and legacy data is disposable; this idea operationalizes that permission.

**Honest weaknesses.**
- Not a build idea — it's a scope fence. Belongs in the plan's non-goals.
- If a future goal *is* unifying all storage, this defers rather than solves it. Acceptable: clean layer first, legacy is a separate epic.

---

## Leading Recommendation

**Pursue #1 + #2 + #4 as a single coherent unit, with #3 as the validation backend and #5 as the scope fence.** They are not five rival ideas — they are the behavior contract (#1), the data contract (#2), the config wiring (#4), the falsification test (#3), and the boundary (#5) of *one* design:

> A `PersistenceBackend` ABC modeled exactly on `BaseConnector` (self-declared `is_active`, dynamic import-by-config-section, value-only boundary returning ids/dataclasses), backing plain-dataclass domain models (Person joins Envelope as a non-`Persistent` model), selected via a `persistence:` config section, defaulting to a ZODB backend that wraps today's `neutral.py`/`chat_store.py` unchanged, and validated by a SQLite-direct second backend — all scoped strictly to the clean single-consumer layer, leaving legacy `zodb_orm` frozen.

This wins because: (a) it reuses the one proven extensibility pattern in the repo rather than inventing a parallel one; (b) its write-path blast radius is a single file (`dispatch`) thanks to the clean layer's single consumer; (c) the contract is derived from real call sites, not speculation; (d) it resolves a documented past bug (ghost objects) by construction; and (e) it serves the document-store and SQLite backends most naturally (records are already dicts) while leaving the SQLAlchemy door open for server deployments.

**Backend fit summary:**
- **SQLite-direct** — best overall fit; embedded, zero heavy dep, file-based like ZODB, cleaner queries. Watch single-writer locking (WAL + busy_timeout).
- **Document store (Mongo/TinyDB)** — most natural model mapping (records already dicts); best if a server doc-DB is already in the stack. TinyDB keeps the embedded feel; Mongo adds an external service.
- **SQLAlchemy (+Alembic)** — best for multi-tenant/Postgres/server; Alembic migrations are the real prize. Slight over-engineering for a 6-method contract; `flask-sqlalchemy` already present lowers the cost.
- **ZODB** — keep as the default backend so the change is non-breaking and data survives.

**Biggest open question for `ce-brainstorm`:** pin the `query_messages` contract (offset/limit semantics, the dual-schema `platform`-vs-`connector` keying, per-chat `bot_id` scoping) before any ABC is frozen — that's where ZODB-specific assumptions will otherwise leak into the neutral interface.

---

## Rejected Ideas (and why)

- **Full repository/Unit-of-Work pattern (Cosmic Python style).** Over-engineered for a 6-method, single-consumer surface; introduces a parallel abstraction shape the repo doesn't use. Rejected for convention-fighting and YAGNI.
- **Abstract `zodb_orm` legacy layer behind the same ABC.** 15 tangled consumers, pickled aiogram objects, read-only data — couples the clean-layer win to a swamp. Rejected; see survivor #5.
- **Swap ZODB for an ORM wholesale (no abstraction, just replace).** Loses the pluggability goal entirely, forces immediate migration of disposable data, and breaks the "default keeps working" property. Rejected — pluggability *is* the requirement.
- **Per-backend ORM-native models (e.g., SQLAlchemy declarative as the canonical Person).** Couples domain models to one library — the opposite of neutrality. Rejected in favor of #2's plain dataclasses + adapters.
- **Event-sourcing / append-only log as the neutral substrate.** Interesting (messages are already append-only), but a large conceptual leap with no current consumer demand; would reshape reads too. Rejected as premature; note for a future ideation if query needs grow.
- **Pluggable storage via Python `importlib.metadata` entry points (setuptools plugins).** More machinery than the repo's import-by-name convention; connectors don't use it, so it's an inconsistent shape. Rejected for convention mismatch.
- **Make `Envelope` itself the persisted unit (drop the separate record dict).** `Envelope` carries `raw` (never persisted) and is inbound-shaped; the record adds `direction`/`person_id`/`timestamp`. Conflating them re-introduces platform-object leakage risk. Rejected — the separation is deliberate.

---

## Suggested Next Step

`ce-brainstorm` on the leading unit (#1+#2+#4), with the first agenda item being the `query_messages` / dual-schema contract. Then `ce-plan` with #3 (SQLite reference backend) and #5 (legacy scope fence) as explicit plan items / non-goals.
