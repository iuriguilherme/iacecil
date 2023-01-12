"""
ia.cecil

Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import logging, sys

try:
    import asyncio
    import locale
    import typing
    from importlib import import_module
    from typing import Union
    from pydantic import BaseSettings
    from ... import (
        commit,
        name,
        version,
    )
    from ...config import (
        DefaultBotConfig,
        ProductionConfig,
        DevelopmentConfig,
    )
    # ~ from ...views.quart_app import quart_startup
    from ..furhat_bot.personas import personas
    
    logging.info(f"Starting {name} v{version} ({commit})...")
    
    logging.debug("Loading configuration from .env files...")
    # ~ config: BaseSettings = ProductionConfig()
    config: BaseSettings = DevelopmentConfig()
    
    logging.debug("Setting log level...")
    log_level: str = 'debug'
    try:
        # ~ log_level = config.log_level
        log_level = 'debug'
    except Exception as e:
        logging.warning(f"""Logging level not informed, assuming \
{log_level}""")
        logging.exception(e)
    logging.basicConfig(level = getattr(logging, log_level.upper()))
    logger: object = logging.getLogger(name)
    
    logger.debug(f"Setting locale to {config.locale}...")
    try:
        locale.setlocale(locale.LC_ALL, config.locale)
    except Exception as e:
        logger.error(f"""Can't set locale to {config.locale}, make sure your \
system locale is set and available""")
        logger.exception(e)
    
    try:
        from instance._bots import bots
    except Exception as e:
        logger.error("Bot list not set! Please RTFM")
        logger.exception(e)
        bots: list = ['default']
    modules: list = [import_module('.' + bot, 'instance.bots') for bot in bots]
    configs: dict = {
        module.__name__.split('.')[2]: \
        (getattr(module, 'BotConfig')() \
        if hasattr(module, 'BotConfig') \
        else default_bot_config) \
        for module in modules
    }
    logger.critical(f"""\
Loaded configuration for bots: {bots}\n\
Bots listed: {len(bots)}, \
imported: {len(modules)}, \
configured: {len(configs)}\n\
bots that were not configured: {[bot for bot in bots if not bot in configs]}\
""")
    
    asyncio.run(personas(
        bots,
        configs[bots[0]].furhat,
        configs,
        configs[bots[0]].openai,
        skip_intro = configs[bots[0]].furhat.get('skip_intro'),
        log_messages = configs[bots[0]].furhat.get('log_messages'),
        add_startswith = configs[bots[0]].furhat.get('add_startswith'),
        add_endswith = configs[bots[0]].furhat.get('add_endswith'),
    ))
    logger.info(f"Finishing {name}")
except Exception as e:
    logging.exception(e)
    sys.exit("RTFM")
