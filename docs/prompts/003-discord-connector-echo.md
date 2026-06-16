Start by invoking the `/lfg` skill (compound-engineering:lfg) to run this end-to-end autonomously: plan, work, code review, test, commit, push, open PR, watch CI, and fix CI failures until green. Treat everything below as the feature description for that pipeline.

<objective>
Make the Discord connector work correctly under ia.cecil's current connector architecture, and document exactly what is required to configure it for production (the Docker / `connectors_v3` runner).

The end goal — and the only acceptance signal — is the `echo` plugin replying over Discord in two situations:
1. Direct messages to the bot, and
2. Authorized channels on Discord servers (guilds).

A real Discord bot token and an authorized test channel are available for live verification, so this must be proven end-to-end against the real Discord gateway, not only with mocks.
</objective>

<context>
ia.cecil is a multi-platform chatbot (Python 3.11, asyncio). Read `CLAUDE.md` first for project conventions, the connector/plugin/personality architecture, and the configuration system. Also read `CONCEPTS.md` and skim `docs/solutions/` for any prior connector/Discord learnings.

Key facts already established about the current state (verify them yourself, do not assume they are still exactly true):

- A Discord connector already exists at `src/iacecil/connectors/discord.py` (~138 lines). It lazy-imports `discord.py`, enables `intents.message_content`, registers an `on_message` handler, skips bots/self, and currently gates guild messages via an `_addressed_to_bot` check (DM always, or leading `/`, or bot @mention).
- The `echo` plugin at `src/plugins/echo.py` exposes `add_envelope_handlers(manager)` which calls `manager.set_default_handler(echo_envelope)` — this is the generic connector path (non-Telegram).
- Plugin loading precedence lives in `src/iacecil/connectors/__init__.py::load_plugin`. The `ConnectorManager` there persists every inbound envelope, then routes to a command handler or the default handler (see `dispatch`, `set_default_handler`).
- The canonical runner is `src/iacecil/controllers/_iacecil/connectors_v3_runner.py`, invoked as `python -m iacecil connectors_v3` (see `src/iacecil/__main__.py`). The Dockerfile `CMD` already uses `iacecil connectors_v3`. This `connectors_v3` runner is the aiogram2→aiogram3 migration runner, Telegram already works on it, and it is the one to update; the older `connectors_runner.py` (mode `connectors`) is legacy and `connectors_v3` will eventually be renamed back to `connectors`.

Reference implementation: the user's earlier Discord implementation lives in a fork of an old version of this program at https://github.com/fabricadofuturo-poa/nasabot — consult it for how Discord was wired before (intents, event handling, server/channel handling, sending), but DO NOT copy its architecture wholesale. The current system uses the Envelope + ConnectorManager + plugin model; adapt the reference to that novel system rather than reverting to the old design.
</context>

<requirements>
1. Confirm the `echo` plugin reaches Discord through the connector path. Trace the full flow: Discord `on_message` → `Envelope` → `ConnectorManager.dispatch` → default handler (`echo_envelope`) → connector `send`. Fix any break in that chain so an echo reply is actually sent.

2. Observation vs. response are separate concerns — implement them that way:
   - The bot must LOG/persist every message it has access to (all DMs, and all messages in guild channels it can see), as a neutral record. Observation is not gated.
   - The decision of WHICH messages get answered must be delegated to the plugin/handler layer, the same way Telegram delegates to its handlers — not hardcoded as bot-only policy inside the connector. Read the relevant discord.py docs (intents, `on_message`, DM vs guild `message.channel`/`message.guild`, permissions) to determine the right adaptation point, then wire "authorized channels" so that authorization is expressed where handlers/config naturally live in this system, consistent with how Telegram handler/allowlist gating works. Document the mechanism you choose and why.

3. Configuration: produce a clear, accurate answer to "what do we need to configure to run the Discord connector properly" under the `connectors_v3` runner and the Docker deployment. Cover at minimum: the bot token location in `instance/bots/<name>.py` (the `discord` config dict) and `.env`/env precedence; the Discord developer-portal toggles required for `intents.message_content`; how a Discord bot is added to a server and how channels are authorized in this system; and how the `connectors_v3` runner selects/loads the Discord connector. Reflect this in `doc/`/`docs/` example configs as needed (the real `instance/` is local-only and unversioned).

4. Do not edit default values in `src/iacecil/config.py`. Follow the configuration flow described in `CLAUDE.md` (`instance/_bots.py` → `instance/bots/<name>.py` → `.env` → OS env).

5. Reconcile the `connectors`/`connectors_v3` naming only as far as needed to make Discord work and to keep docs accurate; the eventual rename back to `connectors` is out of scope unless it blocks the goal — if you touch it, note it explicitly.
</requirements>

<implementation>
- Prefer adapting the existing `discord.py` connector over rewriting it. It already implements lazy import, `message_content` intent, and bot-loop protection (skipping other bots) — preserve those, since removing them risks two bots echoing each other forever or empty `message.content`.
- Keep the connector platform-neutral: only normalized `Envelope` fields are persisted; never persist native Discord objects (use the `raw`/`extra` escape hatches per `src/iacecil/models/envelope.py`).
- A connector failure must mark only that connector down without killing siblings — keep that isolation property intact.
- Respect Telegram strangler-fig arbitration: the generic `add_envelope_handlers` path must not bind Telegram. Your changes should affect Discord only.
- Honor the 2000-char Discord message cap (`MAX_TEXT`) and the send timeout already present.
- For maximum efficiency, when performing multiple independent read/search operations during investigation, batch them in parallel rather than sequentially.
</implementation>

<verification>
Because a live token and an authorized test channel are available, verify end-to-end, not just with unit tests:

1. Add/confirm unit tests that simulate Discord `on_message` for (a) a DM and (b) a guild channel message, asserting the envelope is persisted and the echo reply is produced. Run `pipenv run pytest` and ensure the suite (including the autouse ZODB isolation fixture in `tests/conftest.py`) passes — never remove that fixture.
2. Live smoke test against real Discord:
   - Configure the provided bot token in the appropriate `instance/` config and start the bot via `python -m iacecil connectors_v3` (or `pipenv run` equivalent).
   - Send a DM to the bot → confirm it echoes the message back.
   - Send a message in the authorized server channel (using whatever authorization mechanism you implemented) → confirm it echoes back.
   - Send a message in a NON-authorized channel → confirm the bot LOGS/persists it but does NOT reply, proving observation and response are correctly separated.
3. Confirm the neutral persistence layer recorded every observed message (authorized or not) in `instance/zodb/` records via the `messages.fs` / Person registry path.

Report concrete evidence: test output, and the actual Discord round-trip results (what was sent, what came back) for DM, authorized channel, and unauthorized channel.
</verification>

<success_criteria>
- The `echo` plugin replies over Discord to direct messages with the bot. ✓ proven live.
- The `echo` plugin replies over Discord in authorized server channels, and stays silent (but still logs) in unauthorized ones. ✓ proven live.
- Authorization is delegated to the plugin/handler/config layer (Telegram-style), not hardcoded bot policy in the connector, and the chosen mechanism is documented.
- A written answer exists for how to configure the Discord connector properly for the `connectors_v3` / Docker runner (token, portal intents, server/channel authorization, runner loading).
- `pipenv run pytest` is green; connector isolation and Telegram arbitration are preserved.
- The `/lfg` pipeline completes: changes committed, pushed, PR opened, CI watched and driven to green.
</success_criteria>
