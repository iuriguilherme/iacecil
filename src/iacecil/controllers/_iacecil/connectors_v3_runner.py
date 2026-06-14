"""
ia.cecil modern connector runner (Telegram V3): `python -m iacecil connectors_v3`

Identical to connectors_runner.py but uses TelegramV3Connector for 
any Telegram bot configuration.

Copyleft 2026 Iuri Guilherme <https://iuri.neocities.org/>
"""

import asyncio
import logging
import os
from importlib import import_module
from .connectors_runner import load_bot_configs, _attach_log_sinks

logger = logging.getLogger(__name__)

def build_managers_v3(configs: dict) -> list:
    """One ConnectorManager per bot."""
    logger.info("Building bot managers with Telegram V3 support...")
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
            _attach_log_sinks(manager, config)
        except Exception as e:
            logger.error(f"Failed to attach log sinks for bot {bot_id}: {e}")
        managers.append(manager)
    return managers

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
    logger.info(f"Starting V3 connectors runner for bots: {list(configs)}")
    managers = build_managers_v3(configs)
    try:
        asyncio.run(run_managers(managers))
    except KeyboardInterrupt:
        logger.info("Exiting cleanly")
