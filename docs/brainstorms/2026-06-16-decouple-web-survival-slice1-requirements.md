---
date: 2026-06-16
topic: decouple-web-survival-slice1
---

# Decouple web from connectors — slice 1: survival + shared storage

## Summary

Lift the connector system out of the Quart event loop into its own OS process, started as a sibling of the web process under a small `multiprocessing` supervisor, so the chatbots keep running when the web layer crashes. To make that split actually bootable, the same slice introduces a ZEO shared-storage unit (both processes connect via `ClientStorage` instead of fighting over `FileStorage` locks) and re-sources the web unit's bot identity from config (`load_bot_configs`) so admin/plots pages render real ZEO-backed data without live aiogram dispatchers. The connector-control channel, the connector-control commands, the liveness/health view, and the admin-route control rewrite are slice 2.

## Problem Frame

The connector system runs as a task on uvicorn's own event loop. `quart_before_serving()` in `src/iacecil/views/quart_app/__init__.py` (the `before_serving` hook, lines 114–146) constructs a `ConnectorManager` per dispatcher and schedules `manager.run_all()` on the loop uvicorn is serving Quart on. The connectors are therefore children of the web app, not siblings: when uvicorn's loop stops — web crash, unhandled exception, OOM — every connector task is cancelled with it.

For a solo developer-researcher running bots for real communities, "the web layer fell over and took every bot offline" is a live operational failure, not a hypothetical. The full decoupling (a control channel so the web can restart/toggle/inspect connectors) is a larger body of work whose riskiest part is rewiring the admin *control* routes off in-process aiogram objects. This slice cuts the coupling that threatens survival and makes the split bootable, while leaving connector control standing for slice 2.

Two boot hazards make a naive process split crash in the survival scenario itself, so they are in this slice by necessity:

- **Storage lock.** `get_db` (`src/iacecil/controllers/persistence/zodb_orm.py:65`) opens `ZODB.FileStorage.FileStorage(path_string)` read-write with no read-only flag. The connector unit (aiogram handlers + neutral persistence) and the web unit (admin/plots data pages) both touch the same per-chat `.fs` files. `FileStorage` takes an exclusive OS lock — the second process to open a given `.fs` crashes on boot. Verified: web data paths (`get_messages`/`get_aiogram_messages` and friends) call `get_db` on the same `bots/<id>/chats/<chat>.fs` paths the connector side writes.
- **Dispatcher blast radius.** Removing the dispatcher setup from `before_serving` leaves `current_app.dispatchers` unset, but that attribute is read by `src/iacecil/views/quart_app/blueprints/root/routes.py:38` (the `/status/` home page) and ~15 admin routes (`src/iacecil/views/quart_app/blueprints/admin/routes.py`), not just the `polling`/`send_message`/`updates` control routes. Each read would raise `AttributeError` → 500s. Verified by grep across `src/iacecil/views/`.

## Key Decisions

- **Survival before control.** Ship the process split, the survival guarantee, shared storage, and config-sourced read pages now; defer the connector-control channel, the liveness/health view, and the admin-control-route rewrite to slice 2. Control migration is the largest risk — keeping it out keeps the slice's risk bounded.
- **`multiprocessing` supervisor, not systemd.** Self-contained, runs identically in dev and prod, no init-system dependency. systemd remains a viable production supervisor later but is not this slice's mechanism. The supervisor is itself the new single point of failure (see Success Criteria); systemd `Restart=always` on the supervisor process is the unstated production dependency, not a slice-1 deliverable.
- **N-child sibling supervision.** The supervisor spawns its units as siblings (this slice: ZEO unit + connector unit + web unit); no child is another child's parent. Shaped as an N-child set so the intended later evolution — each connector in its own subprocess — is an extension, not a rewrite. The ZEO unit slots into this set as the first additional sibling.
- **ZEO over `.fs` locking.** Resolve the cross-process lock with a ZEO storage server as a sibling unit; both the connector unit and the web unit connect via `ZEO.ClientStorage` (still wrapped in the existing `ZlibStorage`). Chosen over "web reads out-of-service this slice" and over read-only `FileStorage` (stale reads) so web data pages keep working correctly across the split. Cost: a fourth moving part inside a slice originally framed as survival-only.
- **`spawn` start method.** Children are spawned with the `spawn` start method (or spawned before any aiogram/Quart/asyncio machinery is imported), to avoid the hazards of `fork`-after-event-loop. Config crosses the process boundary by path/name, not as live `BotConfig` objects.
- **Web identity from config, not live dispatchers.** The web unit derives its bot list and bot ids from `load_bot_configs`, not from `current_app.dispatchers`. Read pages (admin "messages", plots) render real ZEO-backed data keyed by config-sourced bot id; they no longer call live `dispatcher.bot.get_me()`. This overlaps the slice-2 admin rewrite by intent — it is the part needed to keep read pages functional now.
- **Comment out control, not reads.** Web routes that *act* on a live in-process bot (the admin `polling` / `send_message` / `updates` routes) are commented out in slice 1; they need the slice-2 control channel. Web routes that only *read* are migrated to config-sourced identity, not commented out.
- **Availability over loss, durability over the web.** During a ZEO outage connectors keep serving and buffer failed Neutral Record writes in memory, flushing on reconnect — no record loss except if the connector unit itself dies mid-outage (a named, accepted bound). Connectors never stop replying because storage blipped.
- **Liveness ping moves to the connector unit.** The "Mãe tá #on/#off" operator notification fires from the connector unit's own startup/shutdown, not the web hooks R2 strips. With the slice-2 health view deferred, this is the operator's only in-chat liveness signal, and rooting it in the connector unit makes it reflect connector liveness directly.

## Requirements

**Process split**

- R1. The connector system runs in its own OS process via the existing `python -m iacecil connectors` runner, owning all `ConnectorManager`s, every connector, aiogram polling, the scheduler, and persistence writes — and importing no Quart.
- R2. The web unit runs uvicorn+Quart with no `ConnectorManager`. The `quart_before_serving` hook is retained but the exact lines that construct `manager`, wire it to the dispatcher, and `loop.create_task(manager.run_all())` (`src/iacecil/views/quart_app/__init__.py:128-134`) are removed, along with the per-dispatcher aiogram setup (`add_filters`/`add_handlers`/`add_jobs`/`scheduler.start()`) and the "Mãe tá #on" bot notification (lines 123-145) that the web unit no longer owns. The paired `quart_after_serving` hook (lines 147-166) is neutralized to match: the `scheduler.shutdown()`, `dispatcher.bot.send_message("Mãe tá #off")`, and `dispatcher.storage.close()` calls on removed machinery are dropped so web shutdown does not raise.
- R3. The connector unit is never started as a child of the web process. The survival polarity (connectors parent-or-peer, never child of web) is preserved by construction.

**Shared storage**

- R9. A ZEO storage server runs as its own sibling unit, owning the on-disk `FileStorage`. Both the connector unit and the web unit open persistence through `ZEO.ClientStorage` (wrapped in the existing `ZlibStorage`) instead of opening `FileStorage` directly, so no two units contend for an exclusive `.fs` lock.
- R10. `get_db` (`src/iacecil/controllers/persistence/zodb_orm.py`) and the neutral-persistence opener (`src/iacecil/controllers/persistence/neutral.py`) connect via `ClientStorage` when a ZEO address is configured. The ZEO address is configured through `BotConfig` / `instance/`, never in `src/iacecil/config.py` defaults.
- R11. When a Neutral Record write fails because the ZEO unit is unreachable, the connector unit keeps serving, buffers the failed write in memory, and flushes the buffer on ZEO reconnect. Records are lost only if the connector unit itself exits while its buffer is non-empty.

**Operator liveness**

- R12. The "Mãe tá #on/#off" operator notification fires from the connector unit's startup and shutdown, not the web unit. The web serving hooks no longer send it (see R2).

**Supervision and startup**

- R4. A `multiprocessing`-based supervisor starts the ZEO unit, the connector unit, and the web unit as sibling children, and restarts a child that exits, with backoff. The ZEO unit starts first (or its readiness is awaited) so the connector and web units can connect.
- R5. The supervisor uses the `spawn` start method, or spawns its children before importing connector/Quart machinery. Config is passed to children by path/name, not as live `BotConfig` objects.
- R6. Each `__main__.py` entry point re-maps: `production` starts the units via the supervisor as siblings; `connectors` / `connectors_v3` are unchanged and serve as the connector unit; `fpersonas`, `furhatgpt`/`chatgpt`/`furhat`, and no-arg `testing` are untouched.
- R7. On `SIGTERM` to the supervisor, the signal is forwarded to all children so each shuts down its connectors / server / storage cleanly.

**Web-side migration**

- R8. Every web read of `current_app.dispatchers` / `dispatcher.bot` is resolved before the web unit boots, confirmed by a grep for `current_app.dispatchers` and `dispatcher.bot` across `src/iacecil/views/`. Read paths (the `/status/` home page at `root/routes.py:38` and the read-only admin/plots routes) are migrated to config-sourced bot identity (`load_bot_configs`). Control paths that act on a live bot (`polling` / `send_message` / `updates`) are commented out pending the slice-2 control channel. The web unit imports and serves with no `AttributeError` from a missing `dispatchers` attribute.

## Acceptance Examples

- AE1. **Covers R3.** Given all units running, when the web process is killed (`SIGKILL`), then every connector keeps delivering inbound and outbound messages and no connector task is cancelled.
- AE2. **Covers R4.** Given all units running, when the web child exits non-zero, then the supervisor restarts only the web child; the ZEO and connector children are untouched.
- AE3. **Covers R4.** Given all units running, when the connector child crashes, then the supervisor restarts it; there is a brief connector downtime and the unit self-heals.
- AE4. **Covers R8, R9, R10.** Given the web unit boots with no `ConnectorManager` and a config-sourced bot list, when an operator opens the admin page, then it loads without error, renders real per-bot data read through ZEO, and the commented-out connector control actions are simply absent.
- AE5. **Covers R9.** Given the ZEO unit running, when both the connector unit and the web unit start, then both open persistence through `ClientStorage` without an exclusive-lock crash, and a record the connector unit writes is readable by the web unit.
- AE6. **Covers R4, R9, R11.** Given all units running, when the ZEO child crashes, then the supervisor restarts it, connectors keep serving and buffer writes during the outage, and on reconnect the buffered Neutral Records are flushed — rather than the whole tree dying or records being lost.
- AE7. **Covers R12.** Given the connector unit starts, then the "Mãe tá #on" notification is sent from the connector unit; when it shuts down cleanly, "Mãe tá #off" is sent; the web unit sends neither.

## Success Criteria

- The defining test: killing the web process leaves the connectors serving (AE1).
- The web unit boots and serves with no `ConnectorManager` and no aiogram dispatcher in process, rendering config-sourced read pages backed by ZEO.
- The supervisor restarts a crashed child independently of its siblings.
- **Honest scope of the guarantee.** Survival holds against web-*child* failure. It does not hold against supervisor death — the `multiprocessing` supervisor parents all children, so its own crash (OOM, kill, unhandled exception) leaves a subsequently-crashing child unrestarted, and a process-group signal can still take connectors down. The supervisor's own supervision (e.g. systemd `Restart=always`) is a named production dependency, not part of this slice.

## Scope Boundaries

Deferred to slice 2 (and beyond):

- The Unix-domain-socket control server and the newline-delimited JSON command protocol.
- The `restart_connector` / `toggle_connector` / `toggle_bot` / `health` commands and the `ConnectorManager` methods behind them.
- Control-channel security (socket file permissions, `SO_PEERCRED` peer-credential checks).
- The `status.json` heartbeat writer and the read-only liveness/health view. Interim gap accepted: between slice 1 and slice 2 the operator has no in-web connector-liveness view and relies on the connector unit's "#on/#off" ping (R12) plus `ps` / supervisor logs.
- The admin *control*-route rewrite onto control commands (the commented-out `polling` / `send_message` / `updates` routes from R8).
- systemd units as the production supervisor (named as the supervisor's own supervision dependency, not built here).
- Per-connector subprocess isolation — the N-child evolution the supervisor is being shaped for.
- ZEO authentication / network exposure — the ZEO unit binds local-only this slice; hardening is later.

## Dependencies / Assumptions

- Single Linux host (Qubes/Fedora).
- The existing `connectors` runner already boots every bot from the `instance/` config contract (`load_bot_configs`) with no Quart — verified in `docs/ideation/decouple-quart-from-connectors-2026-06-15.md`.
- aiogram's runtime stays entirely on the connector side; Telegram replies continue to flow through the legacy aiogram handlers.
- `ZlibStorage` composes over `ClientStorage` the same way it currently composes over `FileStorage`; existing compressed `.fs` data is readable through the ZEO server.
- New wiring (ZEO address, supervisor mode) goes in `BotConfig` / `instance/`, never in `src/iacecil/config.py` defaults.
- The supervisor's own supervision (systemd `Restart=always` or equivalent) exists in production; this slice does not provide it.

## Outstanding Questions

Deferred to planning:

- The exact ZEO topology: one ZEO server hosting all per-bot/per-chat storages, or one server per storage. Affects R9/R10 wiring and the connect-string config shape; resolvable by reading the `instance/zodb/` layout during planning.
- Whether `production` becomes a thin supervisor-launcher or a new dedicated mode (e.g. `supervised`), and the exact supervisor entry shape.
- Backoff policy, zombie reaping, ZEO-readiness gating, and signal-forwarding specifics for the supervisor.
- The exact set of web read routes R8 must migrate to config-sourced identity (resolved by the `current_app.dispatchers` / `dispatcher.bot` grep during planning).

## Sources / Research

- `docs/ideation/decouple-quart-from-connectors-2026-06-15.md` — ranked ideas; idea #1 (connector daemon split) and idea #2 (multiprocessing supervisor) are this slice's basis.
- Coupling site: `src/iacecil/views/quart_app/__init__.py:114-166` (`before_serving` 114-146, `after_serving` 147-166).
- Storage lock site: `src/iacecil/controllers/persistence/zodb_orm.py:62-75` (`get_db` opens `FileStorage` read-write).
- Dispatcher reads to migrate/comment: `src/iacecil/views/quart_app/blueprints/root/routes.py:38`; ~15 reads across `src/iacecil/views/quart_app/blueprints/admin/routes.py`.
- Connector unit: `src/iacecil/controllers/_iacecil/connectors_runner.py`.
- Fused production runner (current `aiogram_startup`): `src/iacecil/controllers/_iacecil/production.py`.
