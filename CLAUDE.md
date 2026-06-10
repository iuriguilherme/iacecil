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
- `production` or `ENV=production` → `controllers/_iacecil/production.py`
- `fpersonas` → `controllers/_iacecil/fpersonas.py` (Furhat robot personas)
- `furhatgpt` / `chatgpt` / `furhat` → `controllers/_iacecil/furhatgpt.py`

### Core layers

**Connectors** (`src/iacecil/connectors/`): Platform abstraction. Each connector implements `connect/listen/send/disconnect` (`base.py` ABC). `ConnectorManager` loads connectors by config-section credentials (telegram: non-empty `token`; xmpp: `jid`+`password`; loopback: `enabled`), registers the configured personality's `commands`, and dispatches inbound `Envelope`s. Telegram-origin envelopes are persisted but NOT dispatched to the command registry — legacy aiogram handlers own Telegram replies. A connector failure marks it down without killing siblings.

**Envelope** (`src/iacecil/models/envelope.py`): Frozen platform-neutral message dataclass (platform, sender_ref, conversation_ref, text, reply_ref, tags) with `raw` (native object, excluded from repr, never persisted) and `extra` escape hatches.

**Neutral persistence** (`src/iacecil/controllers/persistence/neutral.py`): Person registry (`people.fs`, `(platform, native_id)` → person id, auto-create + merge) and normalized message records (`messages.fs`). Only normalized envelope fields are stored — never platform objects.

**Plugins** (`src/plugins/`): Independent modules that register aiogram message handlers. The legacy entry `async def add_handlers(dispatcher)` binds only under the Telegram connector; other connectors resolve `add_handlers_<connector>` and no-op with a logged warning when absent. Plugins are loaded dynamically by name from `config.plugins['enable']`, skipping any in `config.plugins['disable']`. Handler registration order follows the `enable` list.

**Personalidades** (`src/iacecil/controllers/personalidades/`): Personality modules that control *what text* the bot generates for commands. Each personality exposes async functions like `start(message)`, `help(message)`, `add_handlers(dispatcher)` (aiogram path), and a `commands` dict mapping command name → envelope-safe async text function (connector path). Personalidade handlers are registered *after* all plugin handlers. Available personalities: `default`, `iacecil`, `cryptoforex`, `matebot`, `metarec`, `pave`, `pacume`, `pasoca`, `gamboa`, `paola`, `custom`.

**Aiogram controller** (`src/iacecil/controllers/aiogram_bot/`): Creates `IACecilBot` and `Dispatcher` instances. Attaches `config`, `users`, `plugins`, `scheduler` to the dispatcher. Calls plugin `add_handlers` and personality `add_handlers` at startup.

**Quart web app** (`src/iacecil/views/quart_app/`): ASGI app served via uvicorn. Wraps the aiogram dispatchers. Has blueprints for admin, furhat, plots, and root routes.

**Production runner** (`src/iacecil/controllers/_iacecil/production.py`): Loads `instance/_bots.py` for bot list, imports `instance/bots/<name>.py` for each bot config, builds the Quart+aiogram app, runs uvicorn (prefers Unix socket, falls back to TCP).

### Configuration system

**Do not edit** `src/iacecil/config.py` default values. Configuration flows:

1. `instance/_bots.py` — list of active bot names: `bots = ["mybot"]`
2. `instance/bots/<name>.py` — defines `class BotConfig(BaseSettings)` for each bot, inheriting from `DefaultBotConfig` in `src/iacecil/config.py`
3. `.env` file — overrides `BaseConfig` fields (PROD_, TEST_, DEV_ prefixes for environment-specific configs)
4. OS environment variables — highest priority, override `.env`

Key `BotConfig` fields: `personalidade` (str), `plugins` (dict with `enable`/`disable` lists), `telegram` (dict with `token`, `users`, `webhook`), `discord`, `furhat`, `openai`, `deepseek`.

The `instance/` directory is local-only and not versioned. See `doc/` for example configs.

### Persistence

ZODB object database. Legacy per-bot storage in `src/iacecil/controllers/persistence/zodb_orm.py` (read-only legacy data); platform-neutral records and Person registry in `persistence/neutral.py`. Data stored in `instance/zodb/`. Tests are isolated from real data via the autouse fixture in `tests/conftest.py` — never remove it.

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
