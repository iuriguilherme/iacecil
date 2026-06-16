<task>
Invoke the `/compound-engineering:ce-ideate` skill to generate and critically evaluate grounded ideas for making **persistence and domain models pluggable** in ia.cecil — breaking the current hardcoded ZODB coupling so the project can support alternative backends through the same plugin-style architecture it already uses for connectors and (aspirationally) plugins.

Start by invoking the skill. Do not begin implementing anything — this is an ideation pass whose output is a set of evaluated, ranked ideas, not code.
</task>

<context>
ia.cecil is a multi-platform chatbot built around a plugin + personality system. Read `CLAUDE.md` first for project conventions, then ground yourself in the actual code before ideating.

**The problem.** Persistence is hardcoded to ZODB everywhere. The original design intent was that components should be pluggable. The connector layer already realizes this intent well and should be studied as the reference pattern:
- `src/iacecil/connectors/base.py` — abstract base class defining the `connect/listen/send/disconnect` contract every connector implements.
- `src/iacecil/connectors/` + `ConnectorManager` — loads connectors by config-section credentials, dispatches platform-neutral `Envelope`s, and marks a failed connector down without killing siblings.

The same logic has NOT been applied to persistence or models. ZODB (and `transaction`, `persistent.Persistent`, `BTrees`) is imported and used directly across the codebase.

**Where ZODB coupling currently lives** (examine each — these are the call sites any abstraction must absorb):
- `src/iacecil/controllers/persistence/neutral.py` — Person registry (`people.fs`, `(platform, native_id)` → person id, auto-create + merge) and normalized message records (`messages.fs`). The newest, cleanest persistence layer — likely the best template for a neutral interface.
- `src/iacecil/controllers/persistence/zodb_orm.py` — legacy per-bot storage (read-only legacy data).
- `src/iacecil/controllers/persistence/chat_store.py`
- `src/iacecil/views/quart_app/blueprints/admin/routes.py`
- `src/iacecil/views/quart_app/blueprints/plots/routes.py`
- `src/plugins/admin.py`
- `src/plugins/garimpo.py`

**Domain models to make backend-neutral:**
- `src/iacecil/models/envelope.py` — frozen platform-neutral message dataclass (already backend-agnostic; a good model of what neutrality looks like).
- The Person and normalized message records in `persistence/neutral.py` — these are the entities currently bound to ZODB's `persistent.Persistent` base class and must be decoupled so they survive a backend swap.

**Knowledge stores worth consulting for grounding:**
- `docs/solutions/` — documented past solutions (note the recent connector-architecture learnings).
- `CONCEPTS.md` — domain vocabulary (Person registry, Envelope, neutral records).
</context>

<ideation_focus>
Concentrate idea generation on two architectural layers, in priority order:

1. **Persistence abstraction** — a pluggable backend interface (abstract base class + registry/loader) modeled on the connector pattern, so a backend can be selected via config the way connectors are selected by config-section credentials. Ideas should cover: the minimal contract a backend must satisfy (what operations `neutral.py` actually needs — get/create person, merge, append message record, query), how backends register and load, and how failure isolation works.

2. **Model neutrality** — decoupling the domain entities (Person, normalized message records, and the already-neutral `Envelope`) from ZODB's `persistent.Persistent` base class so the same model objects round-trip through any backend. Ideas should address how models are defined once and mapped per-backend (e.g., plain dataclasses + per-backend adapters/serializers vs. an ORM-native model per backend).

Treat config wiring (how backend choice flows through `BotConfig` / `instance/` configs, mirroring the plugins `enable`/`disable` lists) and migration as secondary dimensions — mention them where they materially affect an idea's viability, but they are not the headline.
</ideation_focus>

<constraints_and_grounding>
- **Backends to seriously evaluate:** SQL via SQLAlchemy (Postgres/SQLite through an ORM, Alembic migrations), SQLite direct (stdlib `sqlite3`, zero extra dependency, file-based — closest to ZODB's embedded feel), and a document store (MongoDB/TinyDB — schemaless, closest to ZODB's object model). Each idea should make clear which backends it serves well and which it serves poorly.
- **Backward compatibility is NOT a hard requirement.** Greenfield is acceptable: ideas may assume a clean slate or a one-time migration, and legacy `instance/zodb/` data can be treated as disposable or handled separately. Do not let "must keep reading legacy ZODB" constrain the design space — but note when an idea happens to preserve a smooth migration anyway, since that's a free bonus.
- **Follow, don't fight, the existing conventions.** The connector pattern is the proven template in this repo; favor ideas that extend it coherently over ideas that introduce a parallel, differently-shaped abstraction.
- Python 3.11. Respect the configuration layering in `CLAUDE.md` (do not propose editing `src/iacecil/config.py` default values; backend selection belongs in `BotConfig` / `instance/`).
- Stay platform-neutral at the persistence boundary: only normalized fields are stored, never native platform objects (the `raw` escape hatch is never persisted).
</constraints_and_grounding>

<deliverable>
Let the `/compound-engineering:ce-ideate` skill drive the output format. The result should be a set of grounded, critically-evaluated, ranked ideas for the pluggable persistence + model-neutrality architecture — including, for the leading idea(s), the proposed backend-interface contract, how models stay neutral, the tradeoffs across SQLAlchemy / SQLite / document-store backends, and the honest weaknesses of each approach.

Do not write production code in this pass. If the skill produces an artifact file, note its path at the end.
</deliverable>

---
<!-- run-prompt completion metadata -->
- **Completed:** 2026-06-16
- **Executed by:** general-purpose sub-task via /run-prompt
- **Skill driven:** /compound-engineering:ce-ideate
- **Artifact:** docs/ideation/2026-06-16-pluggable-persistence-and-model-neutrality.md
- **Status:** Success — ideation pass only, no production code
