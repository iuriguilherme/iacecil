"""
ia.cecil connector-native runner: `python -m iacecil connectors`

Runs one ConnectorManager per configured bot, with no Quart and no
legacy aiogram wrapper — the first production-shaped process where
non-telegram connectors (xmpp, discord, matrix, loopback) actually
run. Loads the same instance/ configuration contract as the
production runner: `instance/_bots.py` (or `instance/_bots_<name>.py`
via argv) lists the bots; `instance/bots/<name>.py` provides each
bot's BotConfig; DefaultBotConfig is the fallback.

Copyleft 2012-2025 Iuri Guilherme <https://iuri.neocities.org/>

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
    from iacecil.config import DefaultBotConfig
    default_config = DefaultBotConfig()
    try:
        default_bot = import_module('.default', 'instance.bots')
        default_config = default_bot.DefaultBotConfig()
    except Exception:
        logger.warning(
            "Default bot configuration not found; using built-in defaults")

    bots = None
    try:
        if len(argv) > 2:
            _bots = import_module(f"instance._bots_{argv[2]}")
        else:
            _bots = import_module("instance._bots")
        bots = list(_bots.bots)
    except Exception as e:
        logger.error(f"Bot list not found ({e}); using ['default']")
        bots = ['default']

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
    from iacecil.connectors import ConnectorManager
    managers = []
    for bot_id, config in configs.items():
        try:
            manager = ConnectorManager(config, bot_id=bot_id)
            _attach_log_sinks(manager, config)
            managers.append(manager)
        except Exception as e:
            logger.error(f"Failed to build manager for bot {bot_id}: {e}")
            logger.exception(e)
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


async def run_managers(managers: list) -> None:
    if not managers:
        logger.error("No bot could be started; nothing to run.")
        return
    results = await asyncio.gather(
        *[manager.run_all() for manager in managers],
        return_exceptions=True,
    )
    for manager, result in zip(managers, results):
        if isinstance(result, BaseException):
            logger.error(f"Bot {manager.bot_id} crashed: {result!r}")


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
        logger.info("Exiting cleanly")
