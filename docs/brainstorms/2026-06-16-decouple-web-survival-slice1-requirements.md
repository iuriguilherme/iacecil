---
date: 2026-06-16
topic: decouple-web-survival-slice1
---

# Decouple web from connectors — slice 1: survival

## Summary

Lift the connector system out of the Quart event loop into its own OS process, started as a sibling of the web process under a small `multiprocessing` supervisor, so the chatbots keep running when the web layer crashes. This is slice 1 of a larger decoupling: it delivers the survival guarantee and nothing else. The control channel, the connector-control commands, and the admin-route rewrite are slice 2.

## Problem Frame

The connector system runs as a task on uvicorn's own event loop. `quart_startup()` in `src/iacecil/views/quart_app/__init__.py` (the `before_serving` hook, lines 114–146) constructs a `ConnectorManager` and schedules `manager.run_all()` on the loop uvicorn is serving Quart on. The connectors are therefore children of the web app, not siblings: when uvicorn's loop stops — web crash, unhandled exception, OOM — every connector task is cancelled with it.

For a solo developer-researcher running bots for real communities, "the web layer fell over and took every bot offline" is a live operational failure, not a hypothetical. The full decoupling (a control channel so the web can restart/toggle/inspect connectors) is a larger body of work whose riskiest part is rewiring the admin routes off in-process aiogram objects. This slice cuts only the coupling that threatens survival, and leaves the rest standing.

## Key Decisions

- **Survival before control.** Ship the process split and the survival guarantee now; defer the control channel and the admin-route rewrite to slice 2. The two are separable, and admin migration is the largest risk — keeping it out of this slice keeps the slice small and low-risk.
- **`multiprocessing` supervisor, not systemd.** Self-contained, runs identically in dev and prod, no init-system dependency. systemd remains a viable production supervisor later but is not this slice's mechanism.
- **N-child sibling supervision.** The supervisor spawns its units as siblings (today: connector unit + web unit); no child is another child's parent. Shaped as an N-child set so the intended later evolution — each connector in its own subprocess — is an extension, not a rewrite.
- **`spawn` start method.** Children are spawned with the `spawn` start method (or spawned before any aiogram/Quart/asyncio machinery is imported), to avoid the hazards of `fork`-after-event-loop.
- **Comment out, don't rewrite.** Web-side code that reaches into in-process aiogram (the admin `polling` / `send_message` / `updates` routes and their imports) is commented out in slice 1 to stop cascading import/runtime failures that are out of this slice's scope. The rewrite onto the control channel is slice 2.

## Requirements

**Process split**

- R1. The connector system runs in its own OS process via the existing `python -m iacecil connectors` runner, owning all `ConnectorManager`s, every connector, aiogram polling, the scheduler, and persistence writes — and importing no Quart.
- R2. The web unit runs uvicorn+Quart with no `ConnectorManager`: the `before_serving` block in `src/iacecil/views/quart_app/__init__.py` that constructs `manager` and schedules `run_all()` is removed.
- R3. The connector unit is never started as a child of the web process. The survival polarity (connectors parent-or-peer, never child of web) is preserved by construction.

**Supervision and startup**

- R4. A `multiprocessing`-based supervisor starts the connector unit and the web unit as sibling children, and restarts a child that exits, with backoff.
- R5. The supervisor uses the `spawn` start method, or spawns its children before importing connector/Quart machinery.
- R6. Each `__main__.py` entry point re-maps: `production` starts the units via the supervisor as siblings; `connectors` / `connectors_v3` are unchanged and serve as the connector unit; `fpersonas`, `furhatgpt`/`chatgpt`/`furhat`, and no-arg `testing` are untouched.
- R7. On `SIGTERM` to the supervisor, the signal is forwarded to both children so each shuts down its connectors / server cleanly.

**Web-side cleanup**

- R8. The admin routes and any other web-side code referencing in-process aiogram (`dispatcher.bot`, `current_app.dispatchers` — the `polling` / `send_message` / `updates` routes) are commented out so the web unit imports and serves without them.

## Acceptance Examples

- AE1. **Covers R3.** Given both units running, when the web process is killed (`SIGKILL`), then every connector keeps delivering inbound and outbound messages and no connector task is cancelled.
- AE2. **Covers R4.** Given both units running, when the web child exits non-zero, then the supervisor restarts only the web child and the connector child is untouched.
- AE3. **Covers R4.** Given both units running, when the connector child crashes, then the supervisor restarts it; there is a brief connector downtime and the unit self-heals.
- AE4. **Covers R8.** Given the web unit boots with no `ConnectorManager`, when an operator opens the admin page, then it loads without error and the commented-out connector controls are simply absent.

## Success Criteria

- The defining test: killing the web process leaves the connectors serving.
- The web unit boots and serves with no `ConnectorManager` and no aiogram dispatcher in process.
- The supervisor restarts a crashed child independently of its sibling.

## Scope Boundaries

Deferred to slice 2 (and beyond):

- The Unix-domain-socket control server and the newline-delimited JSON command protocol.
- The `restart_connector` / `toggle_connector` / `toggle_bot` / `health` commands and the `ConnectorManager` methods behind them.
- Control-channel security (socket file permissions, `SO_PEERCRED` peer-credential checks).
- The `status.json` heartbeat writer and the read-only health view.
- The admin-route rewrite onto control commands (the commented-out routes from R8).
- systemd units as the production supervisor.
- Per-connector subprocess isolation — the N-child evolution the supervisor is being shaped for.

## Dependencies / Assumptions

- Single Linux host (Qubes/Fedora).
- The existing `connectors` runner already boots every bot from the `instance/` config contract (`load_bot_configs`) with no Quart — verified in `docs/ideation/decouple-quart-from-connectors-2026-06-15.md`.
- aiogram's runtime stays entirely on the connector side; Telegram replies continue to flow through the legacy aiogram handlers.
- New wiring goes in `BotConfig` / `instance/`, never in `src/iacecil/config.py` defaults.
- Assumption to verify in planning: the only web routes depending on in-process dispatchers are `polling` / `send_message` / `updates`; a grep for `dispatcher.bot` and `current_app.dispatchers` confirms the full set to comment out.

## Outstanding Questions

Deferred to planning:

- Whether `production` becomes a thin supervisor-launcher or a new dedicated mode (e.g. `supervised`), and the exact supervisor entry shape.
- Backoff policy, zombie reaping, and signal-forwarding specifics for the supervisor.
- The exact set of web modules importing aiogram that R8 must comment out (resolved by grep during planning).

## Sources / Research

- `docs/ideation/decouple-quart-from-connectors-2026-06-15.md` — ranked ideas; idea #1 (connector daemon split) and idea #2 (multiprocessing supervisor) are this slice's basis.
- Coupling site: `src/iacecil/views/quart_app/__init__.py:114-146`.
- Connector unit: `src/iacecil/controllers/_iacecil/connectors_runner.py`.
- In-process admin control route (slice-2 migration target): `src/iacecil/views/quart_app/blueprints/admin/routes.py:647`.
- Fused production runner: `src/iacecil/controllers/_iacecil/production.py`.

## Deferred / Open Questions

### From 2026-06-16 review

- P0 — Cross-process ZODB FileStorage contract is unspecified. The connector unit writes `instance/zodb/*.fs` (R1) while the web unit still reads the same files via `zodb_orm.get_db` (`src/iacecil/controllers/persistence/zodb_orm.py:65`, opened read-write) from admin/plots routes. `FileStorage` takes an exclusive OS lock — the second process to open a given `.fs` crashes, on boot, in the survival scenario itself. Resolve before the split ships: declare web persistence reads out-of-service this slice, or move to a ZEO/read-replica access model.
- P0 — R8/R2 understate the dispatcher blast radius; AE4 is currently false. R2 removes the `before_serving` block that *sets* `current_app.dispatchers`, but that attribute is read by `src/iacecil/views/quart_app/blueprints/root/routes.py:38` (the `/status/` home page) and ~10 admin routes, not just `polling`/`send_message`/`updates`. Each read raises `AttributeError` → 500s. Rewrite R8 to comment out or guard *every* web read of `current_app.dispatchers` / `dispatcher.bot`, resolve the grep before AE4 can pass, and decide whether the web unit still constructs inert dispatchers via `aiogram_startup` (`production.py:119-125`) or drops them. Related: web data pages (admin "messages", plots) depend on in-process bot context (`get_aiogram_messages`/`get_messages`) and will render empty after the split — a silent regression AE4 does not catch.
- P1 — Supervisor is the new single point of failure; the survival guarantee is narrower than stated. "Killing the web process leaves connectors serving" holds against web-*child* failure, but the `multiprocessing` supervisor parents both children; supervisor death (OOM, kill, unhandled exception) leaves a subsequently-crashing connector unrestarted and a process-group signal can take connectors with it. Restate the guarantee honestly and name the supervisor's own supervision (e.g. systemd `Restart=always`) as the unstated dependency.
- P1 — R2 under-scopes the `src/iacecil/views/quart_app/__init__.py` edits. "Remove the before_serving block" is ambiguous: that hook (lines 114-146) also runs `scheduler.start()`, `add_handlers`, and a bot notification. The paired `after_serving` hook (147-166) calls `dispatcher.scheduler.shutdown()` / `bot.send_message(...)` / `storage.close()` on machinery R2 removes, so web shutdown raises. Specify R2 as the exact `ConnectorManager`/`run_all()` lines removed (hook otherwise retained) and extend it to neutralize the `after_serving` dispatcher calls.
- P1 — Interim operator blindness between slice 1 and slice 2 (re-opens the Q4 "defer all health" decision). Commenting out all web control (R8) plus deferring `status.json` health leaves the solo operator strictly blinder than the coupled status quo. Either name the expected slice1→slice2 gap and a CLI fallback, or reconsider pulling the cheap read-only `status.json` health view into slice 1.
- FYI — Scope tension: scope-guardian flags R4's restart+backoff and the N-child generalization as beyond "survival and nothing else"; both were explicit brainstorm decisions, recorded here as tension, not a change. Also noted: `multiprocessing`-over-systemd rationale is thin given dev runners are untouched this slice; R7 SIGTERM forwarding is a graceful-shutdown nicety, not strictly survival; AE1 asserts message delivery that no requirement scopes; `spawn` requires passing config by path, not live `BotConfig` objects.
