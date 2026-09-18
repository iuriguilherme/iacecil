# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pipenv install

# Run in testing/development mode
pipenv run test        # python -m iacecil
pipenv run dev         # uvicorn src.iacecil.controllers._iacecil.development:app --reload

# Run in production mode
pipenv run prod        # python -m iacecil production

# Run Furhat personas mode
pipenv run paola       # python -m iacecil fpersonas

# Without pipenv (after pip install -e .)
python -m iacecil
python -m iacecil production
python -m iacecil fpersonas
python -m iacecil furhatgpt
```

Requires Python 3.11. The test suite is invoked with `pipenv run pytest`.

## Architecture

ia.cecil is a multi-platform chatbot (primarily Telegram via aiogram, also Discord and Furhat robot) built around a plugin + personality system.

### Entry point dispatch (`src/iacecil/__main__.py`)

`python -m iacecil [mode]` dispatches to controller modules:
- no arg → `controllers/_iacecil/testing.py` (loopback REPL dev runner — type `/start` on stdin)
- `production` or `ENV=production` → `controllers/_iacecil/supervisor.py` (supervises the units below as sibling processes, so a web crash never stops a bot: the storage server when a bot enables ZEO, the connector unit, and the web unit. `production.py` is now only the web unit's entry, `run_web`)
- `zeo` → `controllers/_iacecil/zeo_runner.py` (the shared storage server alone, for running it under another supervisor or by hand)
- `connectors` → `controllers/_iacecil/connectors_runner.py` (connector-native runner: builds one `ConnectorManager` per bot and runs all connectors — matrix/discord/mastodon/xmpp/loopback — concurrently under asyncio, no Quart/aiogram wrapper)
- `fpersonas` → `controllers/_iacecil/fpersonas.py` (Furhat robot personas)
- `furhatgpt` / `chatgpt` / `furhat` → `controllers/_iacecil/furhatgpt.py`

### Core layers

**Connectors** (`src/iacecil/connectors/`): Platform abstraction. Each connector implements `connect/listen/send/disconnect` (`base.py` ABC). `ConnectorManager` loads connectors by config-section credentials (telegram: non-empty `token`; xmpp: `jid`+`password`; loopback: `enabled`), registers the configured personality's `commands`, and dispatches inbound `Envelope`s. Telegram-origin envelopes are persisted but NOT dispatched to the command registry — legacy aiogram handlers own Telegram replies. A connector failure marks it down without killing siblings.

**Envelope** (`src/iacecil/models/envelope.py`): Frozen platform-neutral message dataclass (platform, sender_ref, conversation_ref, text, reply_ref, tags) with `raw` (native object, excluded from repr, never persisted) and `extra` escape hatches.

**Neutral persistence** (`src/iacecil/controllers/persistence/neutral.py`): Person registry (`people.fs`, `(platform, native_id)` → person id, auto-create + merge) and normalized message records (`messages.fs`). Only normalized envelope fields are stored — never platform objects.

**Plugins** (`src/plugins/`): Independent modules that register message handlers. Importing a plugin has no side effects — registration happens only through loader functions, resolved per connector in this precedence (`load_plugin` in `connectors/__init__.py`): (1) a per-connector `add_handlers_<connector>`; (2) for Telegram only, the legacy aiogram `add_handlers(dispatcher)` (the generic loader never binds Telegram — strangler-fig arbitration); (3) the generic `add_envelope_handlers(manager)` for any non-Telegram connector. A connector with no matching loader no-ops with a logged warning. Plugins are loaded dynamically by name from `config.plugins['enable']`, skipping any in `config.plugins['disable']`. Handler registration order follows the `enable` list.

**Personalidades** (`src/iacecil/controllers/personalidades/`): Personality modules that control *what text* the bot generates for commands. Each personality exposes async functions like `start(message)`, `help(message)`, `add_handlers(dispatcher)` (aiogram path), and a `commands` dict mapping command name → envelope-safe async text function (connector path). Personalidade handlers are registered *after* all plugin handlers. Available personalities: `default`, `iacecil`, `cryptoforex`, `matebot`, `metarec`, `pave`, `pacume`, `pasoca`, `gamboa`, `paola`, `custom`.

**Aiogram controller** (`src/iacecil/controllers/aiogram_bot/`): Creates `IACecilBot` and `Dispatcher` instances. Attaches `config`, `users`, `plugins`, `scheduler` to the dispatcher. Calls plugin `add_handlers` and personality `add_handlers` at startup.

**Quart web app** (`src/iacecil/views/quart_app/`): ASGI app served via uvicorn. Owns no connectors: it starts no `ConnectorManager`, no aiogram dispatcher and no scheduler, and imports no aiogram. Bot identity comes from config via `views/quart_app/identity.py` (`quart_startup(config, bot_identities)`), not from live dispatchers. Blueprints for admin, furhat, plots and root. The admin routes that act on a live bot (`send_message`, `updates`, `polling`) answer 503 until slice 2 adds the connector control channel; the read pages work normally.

**Supervisor** (`src/iacecil/controllers/_iacecil/supervisor.py`): Starts each unit as its own child process — none is another's parent, so a crash restarts only the unit that crashed. First failure restarts immediately, repeats back off to a cap, and a unit that ran for the stability window starts over. Children are spawned, not forked, and configuration crosses the boundary as argv for each child to load itself. Its own supervision (systemd `Restart=always` or equivalent) is a production dependency it does not provide.

**Web unit** (`src/iacecil/controllers/_iacecil/production.py`, `run_web`): Loads `instance/_bots.py` for the bot list, imports `instance/bots/<name>.py` for each bot config, builds the Quart app from config-sourced identities, runs uvicorn (prefers Unix socket, falls back to TCP). Importing the module starts nothing.

**Storage server** (`src/iacecil/controllers/_iacecil/zeo_runner.py`): Runs ZEO when a bot enables it, serving a storage set fixed at startup — `people`, `messages`, and one `chats_<bot_id>` per bot. Binds loopback.

### Configuration system

**Do not edit** `src/iacecil/config.py` default values. Configuration flows:

1. `instance/_bots.py` — list of active bot names: `bots = ["mybot"]`
2. `instance/bots/<name>.py` — defines `class BotConfig(BaseSettings)` for each bot, inheriting from `DefaultBotConfig` in `src/iacecil/config.py`
3. `.env` file — overrides `BaseConfig` fields (PROD_, TEST_, DEV_ prefixes for environment-specific configs)
4. OS environment variables — highest priority, override `.env`

Key `BotConfig` fields: `personalidade` (str), `plugins` (dict with `enable`/`disable` lists), `telegram` (dict with `token`, `users`, `webhook`), `discord`, `furhat`, `openai`, `deepseek`.

The `instance/` directory is local-only and not versioned. See `doc/` for example configs.

### Persistence

ZODB object database. Legacy per-bot storage in `src/iacecil/controllers/persistence/zodb_orm.py` (read-only legacy data, still one `.fs` per chat); platform-neutral records and Person registry in `persistence/neutral.py`; per-bot chat records in `persistence/chat_store.py` — one `bots/<bot_id>/chats.fs` per bot, each chat a `<connector>/<chat_id>` key in a BTree. `scripts/migrate_chat_stores.py` converts the old per-chat files.

`persistence/storage.py` decides how any store opens: local `FileStorage` by default, or a ZEO client when a bot's `zeo` section enables it — which is what lets the connector and web units share data instead of fighting over an exclusive lock. Each process calls `storage.configure_from_configs(configs)` once at startup. During a storage outage the neutral store buffers records in memory and flushes them on reconnect, so connectors keep answering. `persistence/retry.py` holds the conflict retry both stores use.

Data stored in `instance/zodb/`. Tests are isolated from real data via the autouse fixture in `tests/conftest.py` — never remove it.

### Knowledge stores

- `docs/solutions/` — documented solutions to past problems (bugs, best practices, workflow patterns), organized by category with YAML frontmatter (`module`, `tags`, `problem_type`). Relevant when implementing or debugging in documented areas.
- `CONCEPTS.md` — shared domain vocabulary (entities, named processes, status concepts); relevant when orienting to the codebase or discussing domain concepts.

### Adding a new plugin

1. Create `src/plugins/myplugin.py`
2. Implement `async def add_handlers(dispatcher)` registering aiogram handlers
3. Add `"myplugin"` to `plugins['enable']` in the relevant bot config in `instance/bots/`

### Adding a new personalidade

1. Create module at `src/iacecil/controllers/personalidades/mypersona/`
2. Implement async functions for each command (`start`, `help`, etc.) and `add_handlers(dispatcher)`
3. Import and register it in `src/iacecil/controllers/personalidades/__init__.py`
4. Set `personalidade: str = "mypersona"` in the bot config
