"""
ia.cecil connector-native runner: `python -m iacecil connectors`

Runs one ConnectorManager per configured bot, with no Quart and no
legacy aiogram wrapper — the first production-shaped process where
non-telegram connectors (xmpp, discord, matrix, loopback) actually
run. Loads the same instance/ configuration contract as the
production runner: `instance/_bots.py` (or `instance/_bots_<name>.py`
via argv) lists the bots; `instance/bots/<name>.py` provides each
bot's BotConfig; DefaultBotConfig is the fallback.

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import asyncio
import logging
import os
from importlib import import_module

logger = logging.getLogger(__name__)


def load_bot_configs(argv: list) -> dict:
    """Return {bot_name: config}, mirroring the production runner's
    instance/ loading: bot list from instance/_bots.py (or
    instance/_bots_<argv[2]>.py), per-bot BotConfig from
    instance/bots/<name>.py, DefaultBotConfig as fallback."""
    logger.info("Loading default bot configuration...")
    from iacecil.config import DefaultBotConfig
    default_config = DefaultBotConfig()
    try:
        default_bot = import_module('.default', 'instance.bots')
        default_config = default_bot.DefaultBotConfig()
    except Exception:
        logger.warning(
            "Default bot configuration not found; using built-in defaults")

    logger.info("Loading bots list from local configuration...")
    bots: list[str] | None = None
    try:
        if len(argv) > 2:
            _bots = import_module(f"instance._bots_{argv[2]}")
        else:
            _bots = import_module("instance._bots")
        bots = list(_bots.bots)
    except Exception as e:
        logger.error(f"Bot list not found ({e}); using ['default']")
        bots = ['default']

    logger.info("Loading bots configuration...")
    configs = {}
    for bot in bots:
        try:
            module = import_module('.' + bot, 'instance.bots')
            configs[bot] = (getattr(module, 'BotConfig')()
                if hasattr(module, 'BotConfig') else default_config)
        except Exception as e:
            logger.error(f"Failed to load config for bot {bot}: {e}")
            if bot == 'default':
                configs[bot] = default_config
    if not configs:
        logger.warning("No bot config loaded; running 'default'")
        configs['default'] = default_config
    return configs


def build_managers(configs: dict) -> list:
    """One ConnectorManager per bot; a bot failing to build does not
    stop its siblings (R2 at bot granularity)."""
    logger.info("Building bot managers...")
    from iacecil.connectors import ConnectorManager
    managers = []
    for bot_id, config in configs.items():
        try:
            manager = ConnectorManager(config, bot_id=bot_id)
        except Exception as e:
            logger.error(f"Failed to build manager for bot {bot_id}: {e}")
            logger.exception(e)
            continue
        try:
            ## A broken sink config degrades logging, not the bot
            _attach_log_sinks(manager, config)
        except Exception as e:
            logger.error(f"Failed to attach log sinks for bot {bot_id}: {e}")
        managers.append(manager)
    return managers


def _attach_log_sinks(manager, config) -> None:
    """Wire the bot's configured log sinks (if any) into the root
    logger; the manager's run_all owns the drain task lifecycle."""
    sinks = manager._config_as_dict().get('log_sinks') or []
    if not sinks:
        return
    from iacecil.controllers.log_sinks import ConnectorLogHandler
    handler = ConnectorLogHandler(manager, sinks)
    logging.getLogger().addHandler(handler)
    manager.log_handler = handler
    logger.info(
        f"Bot {manager.bot_id}: {len(sinks)} log sink(s) attached.")


## The operator's in-chat liveness signal. It used to fire from the web
## app's serving hooks, so it reported that the *web* layer was up; it
## fires here now, so it reports connector liveness — which is what an
## operator actually needs to know, and the only such signal until the
## slice 2 health view lands (R12).
LIVENESS_ON = "Mãe tá #on"
LIVENESS_OFF = "Mãe tá #off"
LIVENESS_TIMEOUT = 30.0
LIVENESS_POLL = 0.1


def liveness_envelope(conversation_ref: str, text: str):
    """The ping as an ordinary outbound envelope.

    Tagged so an operator notification is distinguishable from
    conversation traffic later.
    """
    from iacecil.models.envelope import Envelope
    return Envelope(
        'telegram',
        'iacecil',
        str(conversation_ref),
        text,
        tags=('liveness',),
    )


def liveness_chat(manager):
    """The operator chat for this bot, or None when none is configured."""
    telegram = manager._config_as_dict().get('telegram') or {}
    users = telegram.get('users') or {}
    special = users.get('special') or {}
    return special.get('info')


async def _wait_until_running(manager, timeout: float) -> bool:
    """Sending before connect() finished would silently drop the ping.

    Checks before waiting, so a zero timeout still sends when the
    connector is already up — which is the shutdown case.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        connector = manager.connectors.get('telegram')
        if connector is not None and connector.running:
            return True
        if asyncio.get_event_loop().time() >= deadline:
            return False
        await asyncio.sleep(LIVENESS_POLL)


async def announce_liveness(managers: list, text: str,
        timeout: float = LIVENESS_TIMEOUT) -> None:
    """Tell each bot's operator chat that its connectors are up or down.

    Best-effort throughout: a bot with no telegram connector or no
    configured operator chat is skipped, and a failed send is logged.
    Bots serving matters more than an operator notification.
    """
    ## Per bot, concurrently: each wait is independent, so a bot whose
    ## connector is slow to come up must not hold the announcement for
    ## every bot behind it in the list.
    await asyncio.gather(*[_announce_one(manager, text, timeout)
        for manager in managers], return_exceptions=True)


async def _announce_one(manager, text: str, timeout: float) -> None:
    chat_id = liveness_chat(manager)
    if not chat_id or 'telegram' not in manager.connectors:
        return
    if not await _wait_until_running(manager, timeout):
        logger.warning(
            f"Bot {manager.bot_id}: telegram connector did not come up "
            f"in {timeout}s; skipping {text!r}")
        return
    try:
        await manager.send(liveness_envelope(chat_id, text))
        logger.info(f"Bot {manager.bot_id}: sent {text!r} to {chat_id}")
    except Exception as exception:
        logger.warning(
            f"Bot {manager.bot_id}: could not send {text!r}: "
            f"{exception!r}")


async def run_managers(managers: list) -> None:
    if not managers:
        logger.error("No bot could be started; nothing to run.")
        return
    tasks = [asyncio.ensure_future(manager.run_all())
        for manager in managers]
    ## Announce alongside the run rather than before it: the connectors
    ## are not up until run_all has started them.
    announcement = asyncio.ensure_future(
        announce_liveness(managers, LIVENESS_ON))
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for manager, result in zip(managers, results):
            if isinstance(result, BaseException):
                logger.error(f"Bot {manager.bot_id} crashed: {result!r}")
    finally:
        announcement.cancel()
        try:
            await announcement
        except asyncio.CancelledError:
            ## Expected: the cancel above, because the run is over.
            pass
        except Exception as exception:
            logger.warning(
                f"Liveness announcement failed: {exception!r}")
        ## A crash is exactly when the operator wants to hear #off, so
        ## this runs on every exit path — but never blocks shutdown.
        try:
            await announce_liveness(managers, LIVENESS_OFF, timeout=0)
        except Exception as exception:
            logger.warning(f"Could not announce shutdown: {exception!r}")


def run_app(*argv) -> None:
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(),
            logging.INFO))
    argv = list(argv)
    configs = load_bot_configs(argv)
    logger.info(f"Starting connectors runner for bots: {list(configs)}")
    managers = build_managers(configs)
    try:
        asyncio.run(run_managers(managers))
    except KeyboardInterrupt:
        ## run_managers already announced #off in its finally block.
        logger.info("Exiting cleanly")
