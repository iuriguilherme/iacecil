<task>
Invoke the `/compound-engineering:ce-ideate` skill to generate and critically evaluate grounded ideas for **decoupling the Quart web interface from the connector system** in ia.cecil — so the two run as isolated units that communicate, instead of being forced to start and live together in one coupled runtime.

Start by invoking the skill. Do not begin implementing anything — this is an ideation pass whose output is a set of evaluated, ranked ideas, not code.
</task>

<context>
ia.cecil is a multi-platform chatbot built around a plugin + personality system. Read `CLAUDE.md` first for project conventions, then ground yourself in the actual code before ideating.

**The problem.** The current run path forces the Quart web app and the connector system to start and run together in one coupled lifecycle. That was a reasonable first cut, but it was always expected to be refactored. The web interface exposes (and should expose more) routes that **control** the connectors — restart them, turn individual chatbots on/off, inspect their health. That control relationship only makes sense if the web layer and the connector layer are separable: today, because they share one runtime, a web crash takes the chatbots down with it. **The chatbots must keep running even if the web system goes down.**

**Where the coupling currently lives** (examine each — these are the seams any decoupling must cut cleanly):
- `src/iacecil/controllers/_iacecil/production.py` — production runner: loads `instance/_bots.py`, imports each `instance/bots/<name>.py`, builds the combined Quart+aiogram app, runs uvicorn (prefers Unix socket, falls back to TCP). This is where web and connectors are fused into one process today.
- `src/iacecil/controllers/_iacecil/development.py` — dev/uvicorn entry (`pipenv run dev`); shows the same fused startup at smaller scale.
- `src/iacecil/views/quart_app/` — the Quart ASGI app and its blueprints (admin, furhat, plots, root). The admin blueprint is the natural home for connector-control routes.
- `src/iacecil/connectors/` — `ConnectorManager` and the per-connector `connect/listen/send/disconnect` lifecycle (`base.py` ABC). This is the unit that must survive independently of the web layer.
- `src/iacecil/controllers/aiogram_bot/` — creates `IACecilBot` + `Dispatcher`, attaches `config/users/plugins/scheduler`, registers plugin and personality handlers at startup. Note where aiogram's own polling/lifecycle is entangled with the web app.
- `src/iacecil/__main__.py` — mode dispatch (`production` / dev / `fpersonas` / `furhatgpt`); shows every current entry point and what each one boots.

**Knowledge stores worth consulting for grounding:**
- `docs/solutions/` — documented past solutions, including recent connector-architecture and sync→async bridge learnings directly relevant to how the connector runtime behaves.
- `CONCEPTS.md` — domain vocabulary (ConnectorManager, Envelope, Person registry).
</context>

<ideation_focus>
Concentrate idea generation on three architectural questions, in priority order:

1. **The decoupling mechanism.** How do the web layer and the connector layer stop sharing one lifecycle? Treat the design space as open: separate OS processes under a supervisor, a connector daemon plus a web client that attaches to it, threads with hard isolation boundaries within one process, or another decoupling shape entirely. For each mechanism, be explicit about how connector survival is actually guaranteed when the web layer dies (not merely asserted).

2. **The control + communication channel.** Once separated, the web routes must reliably command the connector layer — restart a connector, toggle a chatbot on/off, query health — and the channel must be **secure** (authenticated, local-only, not exposed to the network). Ideas should specify the wire contract (what commands exist, request/response vs. fire-and-forget), how the web layer discovers and connects to the connector layer, and what happens to a control command issued while the connector layer is restarting or down.

3. **Lifecycle, supervision, and startup.** How do the units start independently, how does each entry point in `__main__.py` map onto the new shape, and how is the connector layer kept alive / auto-restarted independently of the web layer. Address graceful shutdown and the failure-isolation guarantee that already exists *within* `ConnectorManager` (one connector failing doesn't kill siblings) — and extend that same philosophy up a level so the web layer failing doesn't kill connectors.
</ideation_focus>

<constraints_and_grounding>
- **Deployment target is a single host.** All bots and the web app run on one machine (today via a Unix socket + uvicorn). Optimize ideas for this. You may note in passing if an idea happens to scale to multiple hosts later, but do NOT pull network brokers or distributed-systems machinery into the headline design to serve a topology that isn't required.
- **Dependencies: stdlib / minimal, strongly preferred.** Favor `multiprocessing`, Unix domain sockets, `asyncio`, named pipes, a small supervisor pattern — mechanisms already close to the current footprint (the production runner already prefers a Unix socket). Treat any external broker (Redis, ZeroMQ, etc.) as a last resort that must justify itself against a stdlib alternative; if you propose one, show the stdlib option it beats and why.
- **Connector survival AND control fidelity are co-primary.** The leading idea must do both well: chatbots keep running when the web layer dies, AND the web layer can reliably restart/toggle/inspect connectors. Do not rank an idea highly if it nails isolation but makes control flaky, or vice versa. Call out honestly where an idea trades one against the other.
- **Security of the control channel is a first-class requirement, not an afterthought.** Local-only by default (Unix socket file permissions, peer credentials, or an equivalent), with a clear answer to "what stops an unauthorized local process from toggling a bot."
- **Follow, don't fight, the existing conventions.** `ConnectorManager`'s per-connector failure isolation is the proven resilience pattern in this repo; extend it coherently rather than introducing a parallel, differently-shaped supervision model. Respect the config layering in `CLAUDE.md` (don't propose editing `src/iacecil/config.py` defaults; new wiring belongs in `BotConfig` / `instance/`).
- Python 3.11. Telegram replies still flow through legacy aiogram handlers (see `CLAUDE.md`) — any split must keep aiogram's runtime on the connector side, intact.
</constraints_and_grounding>

<deliverable>
Let the `/compound-engineering:ce-ideate` skill drive the output format. The result should be a set of grounded, critically-evaluated, ranked ideas for decoupling the web interface from the connectors — including, for the leading idea(s): the decoupling mechanism, the secure control/communication contract, how each `__main__.py` entry point re-maps onto the new shape, the precise guarantee for connector survival when the web layer dies, and the honest weaknesses of each approach.

Do not write production code in this pass. If the skill produces an artifact file, note its path at the end.
</deliverable>

---
**Completed:** 2026-06-15
**Artifact:** docs/ideation/decouple-quart-from-connectors-2026-06-15.md
**Result:** Ranked, critically-evaluated ideation set. Leading idea: promote existing `connectors` runner to a connector daemon + pure web client communicating over a Unix-socket control plane (newline-delimited JSON, SO_PEERCRED + 0600 perms).
