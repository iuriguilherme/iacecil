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
import signal
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


## ConnectorManager keeps only one of these: a live telegram_v3
## supersedes the legacy telegram connector (strangler-fig arbitration).
## Looking only for 'telegram' skipped both pings on every v3 bot.
TELEGRAM_CONNECTORS = ('telegram_v3', 'telegram')


def telegram_connector(manager):
    """Name of the telegram connector this manager actually runs, or None."""
    for name in TELEGRAM_CONNECTORS:
        if name in manager.connectors:
            return name
    return None


def liveness_envelope(conversation_ref: str, text: str,
        platform: str = 'telegram'):
    """The ping as an ordinary outbound envelope.

    Tagged so an operator notification is distinguishable from
    conversation traffic later.
    """
    from iacecil.models.envelope import Envelope
    return Envelope(
        platform,
        'iacecil',
        str(conversation_ref),
        text,
        tags=('liveness',),
    )


def liveness_chat(manager, connector_name: str = 'telegram'):
    """The operator chat for this bot, or None when none is configured.

    Read from the running connector's own section first, then the legacy
    telegram section, which is where existing configs keep it.
    """
    config = manager._config_as_dict()
    for section in (connector_name, 'telegram'):
        users = (config.get(section) or {}).get('users') or {}
        chat = (users.get('special') or {}).get('info')
        if chat:
            return chat
    return None


async def _wait_until_running(manager, timeout: float,
        connector_name: str = 'telegram') -> bool:
    """Sending before connect() finished would silently drop the ping.

    Checks before waiting, so a zero timeout still sends when the
    connector is already up.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        connector = manager.connectors.get(connector_name)
        if connector is not None and connector.running:
            return True
        if asyncio.get_event_loop().time() >= deadline:
            return False
        await asyncio.sleep(LIVENESS_POLL)


async def announce_liveness(managers: list, text: str,
        timeout: float = LIVENESS_TIMEOUT, wait: bool = True) -> None:
    """Tell each bot's operator chat that its connectors are up or down.

    On startup the connector is still connecting, so the announcement
    waits for it (``wait``). The shutdown ping is sent before the
    connectors are torn down (see run_managers): ConnectorManager.send
    drops anything addressed to a connector that is no longer running,
    so a ping sent after teardown never leaves the process.

    Best-effort throughout: a bot with no telegram connector or no
    configured operator chat is skipped, and a failed send is logged.
    Bots serving matters more than an operator notification.
    """
    ## Per bot, concurrently: each wait is independent, so a bot whose
    ## connector is slow to come up must not hold the announcement for
    ## every bot behind it in the list.
    await asyncio.gather(*[_announce_one(manager, text, timeout, wait)
        for manager in managers], return_exceptions=True)


async def _announce_one(manager, text: str, timeout: float,
        wait: bool = True) -> None:
    connector_name = telegram_connector(manager)
    if connector_name is None:
        logger.info(
            f"Bot {manager.bot_id}: no telegram connector; no {text!r} ping")
        return
    chat_id = liveness_chat(manager, connector_name)
    if not chat_id:
        logger.info(
            f"Bot {manager.bot_id}: no operator chat configured "
            f"(users.special.info); no {text!r} ping")
        return
    if wait and not await _wait_until_running(manager, timeout,
            connector_name):
        logger.warning(
            f"Bot {manager.bot_id}: {connector_name} connector did not come "
            f"up in {timeout}s; skipping {text!r}")
        return
    try:
        delivered = await manager.send(
            liveness_envelope(chat_id, text, connector_name))
        if delivered is False:
            logger.warning(
                f"Bot {manager.bot_id}: {text!r} not delivered; the "
                f"{connector_name} connector is down")
            return
        logger.info(f"Bot {manager.bot_id}: sent {text!r} to {chat_id}")
    except Exception as exception:
        logger.warning(
            f"Bot {manager.bot_id}: could not send {text!r}: "
            f"{exception!r}")


async def _stop_gracefully(managers, tasks, state) -> None:
    """Say goodbye while the connectors can still carry it, then stop."""
    if not state.get('off_sent'):
        state['off_sent'] = True
        try:
            await announce_liveness(managers, LIVENESS_OFF, timeout=0,
                wait=False)
        except Exception as exception:
            logger.warning(f"Could not announce shutdown: {exception!r}")
    for task in tasks:
        task.cancel()


def _install_shutdown_handlers(managers, tasks, state) -> None:
    """Make SIGTERM stop the run the way Ctrl-C already does.

    The supervisor stops this unit with SIGTERM. Python's default
    handler exits the process outright, so without this the connectors
    never disconnect cleanly and the #off ping never goes out. The ping
    goes first, while the connectors are still up to carry it.
    """
    loop = asyncio.get_event_loop()

    def stop():
        logger.info("Received shutdown signal; stopping connectors")
        loop.create_task(_stop_gracefully(managers, tasks, state))

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop)
        except (NotImplementedError, RuntimeError, ValueError):
            ## Not the main thread, or a loop without signal support.
            logger.debug(f"Cannot install handler for {sig}")


async def run_managers(managers: list) -> None:
    if not managers:
        logger.error("No bot could be started; nothing to run.")
        return
    tasks = [asyncio.ensure_future(manager.run_all())
        for manager in managers]
    state = {'off_sent': False}
    _install_shutdown_handlers(managers, tasks, state)
    ## Announce alongside the run rather than before it: the connectors
    ## are not up until run_all has started them.
    announcement = asyncio.ensure_future(
        announce_liveness(managers, LIVENESS_ON))
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for manager, result in zip(managers, results):
            if isinstance(result, asyncio.CancelledError):
                logger.info(f"Bot {manager.bot_id} stopped")
            elif isinstance(result, BaseException):
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
        ## Signalled shutdowns already said #off while the connectors
        ## were up. Any other exit (every bot crashed, or run_all
        ## returned) tries here; a connector that already went down
        ## drops it, and _announce_one logs that rather than hiding it.
        if not state['off_sent']:
            state['off_sent'] = True
            try:
                await announce_liveness(managers, LIVENESS_OFF, timeout=0,
                    wait=False)
            except Exception as exception:
                logger.warning(f"Could not announce shutdown: {exception!r}")


def run_app(*argv) -> None:
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(),
            logging.INFO))
    argv = list(argv)
    configs = load_bot_configs(argv)
    ## Storage first: the managers below persist on their first message,
    ## and a store opened before this would use the wrong backend.
    from iacecil.controllers.persistence.storage import configure_from_configs
    configure_from_configs(configs)
    logger.info(f"Starting connectors runner for bots: {list(configs)}")
    managers = build_managers(configs)
    try:
        asyncio.run(run_managers(managers))
    except KeyboardInterrupt:
        ## run_managers already announced #off in its finally block.
        logger.info("Exiting cleanly")
