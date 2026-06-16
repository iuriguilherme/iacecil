# Ideation: Decouple the Quart web interface from the connector system

**Date:** 2026-06-15
**Mode:** repo-grounded
**Subject:** Split the Quart web app and the connector system into isolated units that communicate, so the chatbots keep running even if the web layer crashes — and so web routes can reliably *control* the connectors (restart, toggle a bot on/off, query health) over a secure local channel.

---

## Grounding Context

### Where the coupling actually lives

The fusion is a single function: `quart_startup()` in `src/iacecil/views/quart_app/__init__.py`. Its `@quart_app.before_serving` hook (lines 114–146) does the damage:

```python
manager = ConnectorManager(dispatcher.config)
dispatcher.manager = manager
...
loop.create_task(manager.run_all())   # <-- connectors live INSIDE the Quart loop
```

`manager.run_all()` is scheduled as a task on the **same asyncio event loop uvicorn is serving Quart on**. The connectors are not siblings of the web app; they are children of it. When uvicorn's loop stops (web crash, unhandled exception in `before_serving`, OOM, `uvicorn.run` returns), every connector task is cancelled with it. `production.py` reinforces this: `uvicorn.run(app, ...)` is the single blocking call that owns the whole process lifetime (lines 144–166).

### The lever already in the repo

`connectors_runner.py` (`python -m iacecil connectors`) and `connectors_v3_runner.py` (`connectors_v3`) **already run the connector system standalone** — `asyncio.run(run_managers(managers))`, one `ConnectorManager` per bot, **no Quart, no aiogram wrapper**. The header comment calls it "the first production-shaped process where non-telegram connectors actually run." This is enormous for the ideation: the connector daemon is not hypothetical — it exists and boots from the same `instance/` config contract (`load_bot_configs`). The decoupling problem is therefore largely "make this the production path and bolt a control surface onto it," not "build a daemon from scratch."

### Resilience pattern to extend (not replace)

`ConnectorManager.run_all()` already gathers per-connector tasks with `return_exceptions=True` (`__init__.py:259`) — one connector failing marks it down without killing siblings (R2). `connectors_runner.run_managers()` extends the same pattern one level up: one *bot* crashing doesn't stop sibling bots. The task asks us to extend it one more level: the **web layer** crashing doesn't stop connectors. The idiom to follow is "gather siblings, isolate failures, log and continue" — not a new supervision framework.

### Control appetite already exists

The admin blueprint already has a control route: `polling()` in `blueprints/admin/routes.py:647` toggles `dispatcher.start_polling()` / `stop_polling()` on in-process dispatchers. This is exactly the kind of route the task wants more of — but today it works only because the dispatcher is in the same process. After decoupling it must become an out-of-process command. It is the proof of demand and the first migration target.

### Constraints carried into evaluation

- **Single host.** Prod already binds a Unix socket (`config.socket = 'uvicorn.sock'`). Optimize for one machine; no network broker in the headline design.
- **Stdlib / minimal deps.** `multiprocessing`, Unix domain sockets, `asyncio`, peer credentials. An external broker must beat a stdlib option to earn a place.
- **aiogram stays connector-side.** Telegram replies flow through legacy aiogram handlers; the telegram connector's `listen()` owns `start_polling`. Any split keeps aiogram's runtime in the connector unit.
- **Co-primary:** connector survival AND control fidelity. An idea that nails isolation but makes control flaky ranks no higher than one that does the reverse.
- **Config layering.** New wiring goes in `BotConfig` / `instance/`, never in `config.py` defaults.

### Topic axes

1. **Process/lifecycle split** — what runs in which process, and how the web process's death is prevented from reaching connectors.
2. **Control + communication channel** — wire contract, transport, discovery, behavior when the peer is down/restarting.
3. **Channel security** — what stops an unauthorized local process from toggling a bot.
4. **Supervision & startup** — how units start, auto-restart, and how each `__main__.py` entry point re-maps.
5. **Migration & state** — how the existing `before_serving` fusion and in-process admin routes (`polling`, `send_message`, `dispatchers`) are unwound without losing the Telegram reply path.

---

## Ranked Ideas

> Critique-first: ~14 candidates were generated across the five axes; the ones that failed on a co-primary (survival or control fidelity), pulled in a network broker the single-host topology doesn't need, or duplicated `connectors_runner` are rejected at the bottom with reasons. Eight survive.

### #1 — Connector daemon (existing `connectors` runner, promoted) + web client over a Unix-socket control plane

**This is the leading idea.** It is the smallest move that satisfies both co-primaries, because half of it already ships.

#### Decoupling mechanism

Two independent OS processes on the one host:

- **Connector unit** = `python -m iacecil connectors` (already exists). Owns every `ConnectorManager`, all connectors, aiogram polling, the scheduler, persistence writes. Runs under its own `asyncio.run()` with its own loop. **It does not import Quart and never has.** This is the survival guarantee's foundation: there is no code path by which a Quart fault reaches this process — they share no loop, no interpreter, no import graph.
- **Web unit** = a slimmed `production.py` that runs uvicorn+Quart but **no longer constructs or runs any `ConnectorManager`**. The `before_serving` hook loses its `manager = ConnectorManager(...)` / `create_task(run_all())` block entirely. Quart becomes a pure client of the connector unit.

They communicate over a **Unix domain socket** the connector unit listens on (e.g. `instance/run/control.sock`), parallel to the web unit's own `uvicorn.sock`.

#### The secure control/communication contract

The connector unit opens a second listener at startup — an `asyncio.start_unix_server()` **control server** — alongside its connectors, as one more task in the same `gather`. Wire protocol: **newline-delimited JSON request/response** (stdlib `json`, no dependency). One connection = one command = one response.

Command set (request → response):

| Command | Shape | Semantics |
|---|---|---|
| `health` | `{"cmd":"health"}` → `{"bots":{"iacecil":{"telegram":"up","xmpp":"down"}}, "uptime_s": N}` | request/response, read-only |
| `list` | `{"cmd":"list"}` → `{"bots":[...]}` | request/response |
| `connector.restart` | `{"cmd":"connector.restart","bot":"iacecil","connector":"telegram"}` → `{"ok":true}` | request/response, mutating |
| `bot.toggle` | `{"cmd":"bot.toggle","bot":"iacecil","state":"off"}` → `{"ok":true,"state":"off"}` | request/response, mutating |
| `connector.toggle` | `{"cmd":"connector.toggle","bot":"iacecil","connector":"discord","state":"on"}` → `{"ok":true}` | request/response, mutating |

Mutating commands map onto **new `ConnectorManager` methods** that wrap the existing `connect/listen/send/disconnect` lifecycle — extending the proven idiom, not inventing supervision. Sketch (interface only, not production code): `async def restart_connector(name)` = cancel that connector's task, `await connector.disconnect()`, re-create the task via the same `_run_connector(name, conn)` used in `run_all`; `async def toggle_connector(name, state)` = cancel/start the one task and flip `connector.running`; `bot.toggle` toggles all connectors for that manager. These are small because `run_all` already structures connectors as independently-cancellable tasks gathered with `return_exceptions=True`.

**Discovery:** the socket path lives in `BotConfig` (e.g. `control = {"socket": "instance/run/control.sock"}`), so the web unit reads the same `instance/` config and knows where to connect — symmetric with how both units already read `instance/_bots.py`. No registry, no port scan.

**Command issued while the connector unit is down or restarting:** the web client's `connect()` to the control socket fails fast (`ConnectionRefusedError` / `FileNotFoundError`). The admin route catches it and renders "connector service unavailable" rather than hanging — mirroring `ConnectorManager.send()`'s existing "warn once and drop if down" philosophy. A command that arrives *during* a single-connector restart is naturally serialized: the control server processes one command per connection and the restart method `await`s the disconnect before re-creating the task, so a concurrent `restart` either waits or returns `{"ok":false,"busy":true}`. No partial-state corruption because nothing toggles connectors except these awaited methods on the connector unit's own loop.

#### Channel security — "what stops an unauthorized local process from toggling a bot"

Defense in depth, all stdlib, all local:

1. **Unix socket file permissions.** Create the socket dir `0700` and the socket `0600`, owned by the service user. A different local user cannot `connect()` at the OS level. This is the primary control and is the same trust model the prod `uvicorn.sock` already relies on.
2. **Peer credential check.** On each accepted connection the control server reads `SO_PEERCRED` (`sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, ...)`, Linux; the deploy host is Linux per env) and rejects any peer whose uid is not the service uid. This defends even if the filesystem permissions are misconfigured.
3. **No network bind, ever.** The control socket is a filesystem path; it is structurally unreachable from the network. This is the single biggest security win over any TCP/HTTP control API.

Answer to the threat: a rogue local process running as another user is blocked by (1) and (2); a process running as the *same* user is already inside the trust boundary (it could read the bot tokens directly), so no channel can defend against it and none should pretend to.

#### How each `__main__.py` entry point re-maps

- `production` / `staging` → now starts the **web unit only** (uvicorn+Quart, no ConnectorManager). The connector unit is started independently (see supervision). *Alternatively*, `production` becomes a thin launcher that spawns the connector unit as a `multiprocessing.Process` child and then runs uvicorn — see "survival guarantee" caveat below for why the supervisor-sibling variant is safer.
- `connectors` / `connectors_v3` → **unchanged in spirit, promoted in status**: this *is* the connector unit. The only addition is the control server task inside `run_managers`.
- `fpersonas`, `furhatgpt`/`chatgpt`/`furhat` → **untouched.** They don't use the Quart+connector fusion; they keep their own runners.
- no-arg `testing` → **untouched** (loopback REPL).

#### The precise connector-survival guarantee

> If the web unit is started as a **separate process not parented to the connector unit's loop**, then no fault in Quart, uvicorn, or any blueprint can terminate, cancel, or block any connector task — because the connector tasks live in a different OS process with a different interpreter and a different event loop, and the two share state only through a request/response socket the connector unit reads at its own pace.

The guarantee holds **only** if the connector unit is the parent or an independent peer, never the child of the web process. If `production` spawns connectors as a `multiprocessing` *child* of the web process, a web-process crash can orphan or signal the child depending on start method — so the recommended shape is: a tiny supervisor (or systemd, see #2/#3) starts **both** units as siblings; neither is the other's parent. With that, web death = a `ConnectionRefusedError` on the next control command and nothing more.

#### Honest weaknesses / open questions

1. **`production.py` today is the web+connector fusion; splitting it means the web unit can no longer reach `dispatcher.bot` for the admin `send_message`/`updates`/`polling` routes.** Those routes call `dispatcher.bot.get_me()`, `dispatcher.bot.send_message()`, and read `current_app.dispatchers` directly. After the split, *every* such route must go through the control channel (add `message.send`, `bot.get_me` commands) or read from neutral persistence instead. This is real migration work and the single biggest cost of the idea — the admin blueprint is tightly bound to in-process aiogram objects today.
2. **Who supervises the supervisor?** The idea guarantees web-death-doesn't-kill-connectors, but says nothing about *connector*-death. A bare `python -m iacecil connectors` that crashes stays dead. The guarantee is only complete when paired with a restart mechanism (idea #2 or #3). Ranked #1 because it is the necessary core, but it is not sufficient alone.
3. **Two-process operational change.** Operators used to one `uvicorn.sock` process now run two units, two log streams, two restart commands. Needs a documented `doc/` runbook and likely the systemd units of #3 to not regress operability.
4. **`SO_PEERCRED` is Linux-specific.** Fine for the stated deploy host, but the codebase has cross-platform guards elsewhere (`_cwd_is_trusted` degrades when `os.geteuid` is absent). The control server should degrade the same way: permissions-only on platforms without `SO_PEERCRED`, documented as such.

---

### #2 — Same daemon split, supervised by a stdlib `multiprocessing` parent with auto-restart

Adds the missing supervision layer to #1 using only stdlib, for hosts without systemd (or where the maintainer wants self-contained supervision).

**Mechanism:** a thin top-level supervisor process (`python -m iacecil` new mode, e.g. `supervised`) spawns **two sibling children** with `multiprocessing.Process` (or `subprocess`): the connector unit and the web unit. The supervisor's only job is a `join`/poll loop: if a child exits, log and re-`spawn` it with backoff. Critically, the **two children are siblings, not parent/child of each other** — so the survival guarantee from #1 holds (web child dying never touches the connector child; the supervisor restarts the web child independently).

**Survival guarantee (extended):** web child crash → supervisor restarts *only* the web child; connector child untouched. Connector child crash → supervisor restarts it (brief connector downtime, but self-healing). This is the "extend ConnectorManager's failure isolation up a level" the task explicitly asks for: R2 (connector) → bot-level (run_managers) → **process-level (supervisor)**, one coherent escalating pattern rather than a parallel model.

**Control channel/security:** identical to #1 (Unix socket, peer creds).

**Honest weaknesses:**
1. **A stdlib supervisor re-implements a slice of systemd/supervisord** — restart backoff, crash loops, log handling, signal forwarding (SIGTERM → graceful child shutdown). Easy to get the 80% and miss the nasty 20% (thundering restart loops, zombie reaping, double-fork). On a Linux host that *has* systemd, this is rebuilding the wheel — which is exactly why #3 ranks just below as the "use the platform" alternative.
2. **`multiprocessing` start method matters.** `fork` after the asyncio loop or aiogram sessions are touched is hazardous; the supervisor must spawn children *before* importing connector/Quart machinery, or use `spawn`. A subtle footgun.
3. Restarting the connector child is heavier than restarting a single connector — a misbehaving Discord connector takes the whole bot fleet down for the restart window, where #1's `connector.restart` command is surgical. Best paired: control channel for surgical restarts, supervisor for whole-process crash recovery.

---

### #3 — Daemon split (#1) supervised by **systemd** (or equivalent) instead of a Python parent

The "use the host's process manager" variant. Two systemd units: `iacecil-connectors.service` and `iacecil-web.service`, no dependency edge between them (or `web` `Wants=connectors` but `connectors` never depends on web).

**Why it ranks here:** the deploy host is a single Linux machine. systemd already does crash-restart with backoff, log capture (journald), socket activation, graceful SIGTERM, resource limits, and uid/permission setup — all the hard parts #2 hand-rolls. Zero new Python supervision code. The Unix control socket of #1 can even be **socket-activated** by systemd, which solves discovery and permissions in one stroke (`ListenStream=` with `SocketUser=`/`SocketMode=0600`).

**Survival guarantee:** strongest of all — the two units are independent systemd services; the web unit cannot be the connector unit's parent. Kernel + systemd enforce isolation. Web unit `OOMKilled` → journald logs it, systemd restarts *only* `iacecil-web`, connectors never notice.

**Honest weaknesses:**
1. **Ties production ops to systemd.** The project is GPL/self-hostable; not every operator runs systemd (containers without an init, BSD, dev laptops). Needs #2 as the no-systemd fallback, so you likely build both anyway.
2. **Doesn't help the dev/testing inner loop.** `pipenv run dev`/`test` won't spawn systemd units; developers still need an in-process or `multiprocessing` path. So #3 is a *production deployment* answer, not a *code architecture* answer — it presupposes #1's split already exists.
3. Socket activation is elegant but adds a systemd-specific config surface (`.socket` unit) that must stay in sync with `BotConfig`'s socket path — two sources of truth unless carefully documented.

---

### #4 — Threads with "hard isolation" in one process (connector thread owns its own asyncio loop)

Run connectors on a **dedicated thread** with its own `asyncio.new_event_loop()`, web on the main thread/uvicorn loop, communicate via a thread-safe `queue.Queue` + `loop.call_soon_threadsafe`.

**Why considered:** no second process, no socket, simplest deploy; control is just enqueueing a command object the connector loop drains.

**Why it ranks below the process splits — it fails the survival co-primary.** Threads share one interpreter and one process. An unhandled exception in a Quart worker that the ASGI server doesn't catch, a `sys.exit`, a segfault in a C extension (aiogram's dependencies, ZODB), or an OOM kill takes down **the whole process including the connector thread**. "Hard isolation" between threads is a fiction at the failure modes the task cares about ("a web crash takes the chatbots down"). It improves *logical* separation and would make the control channel trivial, but it does **not** deliver the headline guarantee. Honest verdict: good as an intermediate refactor step (move connectors off the `before_serving` task onto a clearly-separated loop) but not an acceptable final answer to "chatbots must survive a web crash."

---

### #5 — Keep one process, but make the web app a **separately-restartable ASGI sub-app** the connector loop hosts

Invert the parenting: the **connector unit** is the long-lived process and *it* optionally mounts the Quart app (via `uvicorn.Server` started as a task inside the connector loop, wrapped in try/except + restart). Web faults are caught at the task boundary; the connector loop survives and can re-launch the web task.

**Why considered:** single process, and it correctly puts connectors as the *parent* (the right survival polarity — web is the child that can die and be restarted). Control channel becomes in-process function calls.

**Why it ranks here, not higher:** it only survives faults that are *catchable Python exceptions at the task boundary*. A web fault that crashes the shared loop or process (loop corruption, C-level crash, OOM) still takes connectors with it — same fundamental flaw as #4, slightly mitigated by correct parenting. Also, hosting uvicorn-as-a-task inside another asyncio app is fiddly (uvicorn wants to own signal handling and the loop). It's a real improvement over today's inversion (today web parents connectors — the *worst* polarity) but stops short of true isolation. Worth noting as the **cheapest meaningful improvement** if a full two-process split is deferred: flipping the parenting so connectors host web, not vice versa, already changes "web crash kills bots" into "web crash kills web, bots survive most faults."

---

### #6 — Control channel as a tiny HTTP-over-Unix-socket API instead of newline-JSON

Same two-process split as #1, but the control server speaks **HTTP/1.1 bound to a Unix socket** (uvicorn/hypercorn can bind `uds=`; or stdlib `http.server` over a `AF_UNIX` socket). Web unit talks to it with `httpx`/`aiohttp` `UnixConnector`.

**Why considered:** HTTP gives free routing, methods, status codes, and the team already knows ASGI; auth could reuse familiar middleware.

**Why it ranks below #1's raw JSON:** it pulls a second ASGI server (or an HTTP client dep) into the connector unit purely for a 5-command local control plane — exactly the "does it beat the stdlib option?" test the constraints demand, and it doesn't. `asyncio.start_unix_server` + `json` is ~40 lines with no new dependency and the same security properties. HTTP's verbs/status codes are over-engineering for `{restart, toggle, health, list}`. Keep this idea in pocket only if the control surface later grows large enough to want real REST semantics. **Rejected as headline, retained as a scale-up path.**

---

### #7 — Health/state via a shared file (heartbeat + status JSON) instead of (or alongside) a query command

The connector unit writes `instance/run/status.json` (and touches a heartbeat mtime) every N seconds; the web `health` route just reads the file — no IPC round-trip, works even when the control socket is briefly busy.

**Why it's a useful complement, not a standalone:** it gives the web layer a *read-only* health view that survives the connector unit being mid-restart (stale-but-present data with a timestamp the UI can show as "last seen Ns ago"). It cannot do *control* (you can't restart a connector by writing a file without a watcher, which reintroduces a channel). Best role: pair with #1 so `health` is cheap and degrades gracefully, while mutating commands go over the socket. Ranked as an **additive enhancement** to the leading idea, not a competitor.

---

### #8 — Named-pipe (FIFO) control channel

Same split, but command transport is a stdlib named pipe (`os.mkfifo`) instead of a Unix socket.

**Why it's rejected as headline:** FIFOs are unidirectional and awful for request/response (you need two FIFOs and hand-rolled correlation; no per-connection peer creds; `SO_PEERCRED` unavailable). A Unix *socket* is strictly better for this exact use case — bidirectional, connection-oriented, peer-credentialed — for the same stdlib cost. Listed only to record that it was considered and beaten by #1's socket on every axis that matters.

---

## Rejected candidates (with reasons)

- **Redis / ZeroMQ / RabbitMQ pub-sub control bus.** Network broker for a single-host, ~5-command control plane. Fails the "must beat the stdlib alternative" bar outright; `asyncio.start_unix_server` does everything needed with zero deps and better security (no network surface). Only justifiable if the deployment genuinely becomes multi-host, which the task says it is not.
- **gRPC control service.** Same objection as #6 amplified: a schema-compiled RPC framework and protobuf dependency for a local toggle/restart surface. Massive over-engineering.
- **Signals (SIGHUP/SIGUSR1) to the connector process for control.** Works for "reload" but cannot carry arguments (which bot? which connector? on/off?) or return health. Too low-bandwidth for the required control fidelity.
- **D-Bus.** Native Linux IPC, but a heavyweight dependency and API surface for what a Unix socket does in 40 lines; also ties to Linux desktop-ish infra. Rejected.
- **Leave the fusion, just wrap `before_serving` in try/except.** Doesn't decouple anything — connectors still live in the Quart loop and still die with it. Fails the headline guarantee. This is the status quo with a band-aid.
- **A second full ASGI app dedicated to control.** Duplicates the web unit's machinery on the connector side; #6 already covers the "HTTP control" space and is itself out-ranked by raw JSON.

---

## Recommended direction for `ce-brainstorm`

**Take idea #1 as the core, with #3 (systemd) as the production supervisor and #2 (multiprocessing) as the no-systemd fallback, plus #7 (status file) as the cheap health path.** The brainstorm should pin down:

1. The exact `ConnectorManager` control-method API (`restart_connector`, `toggle_connector`, `toggle_bot`, `health`) and how each composes the existing `connect/listen/disconnect` + task lifecycle.
2. The newline-JSON command schema and the web-side client (timeout, "service down" rendering, serialization-during-restart behavior).
3. The migration of the admin blueprint's in-process aiogram dependencies (`dispatcher.bot`, `current_app.dispatchers`, the `polling`/`send_message`/`updates` routes) onto control commands and/or neutral persistence reads — the largest and riskiest slice.
4. The `BotConfig`/`instance/` wiring for the control socket path and permissions, keeping `config.py` defaults untouched.
5. Whether `production` becomes "web unit only" (paired with a separate connector-unit launch) or a sibling-spawning launcher — and the precise guarantee that follows from that choice.

**The one thing the brainstorm must not lose:** the survival guarantee is contingent on the connector unit never being a *child* of the web process. Every concrete supervision choice has to preserve that polarity, or the headline property evaporates.
