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
    from pydantic import BaseConfig
    from ... import (
        commit,
        name,
        version,
    )
    from ...config import ProductionConfig
    from ..furhat_bot.personas import personas
    
    logging.info(f"Starting {name} {version} ({commit})...")
    
    logging.debug("Loading configuration from .env files...")
    config: BaseSettings = ProductionConfig()
    
    logging.debug("Setting log level...")
    log_level: str = 'info'
    try:
        log_level = config.log_level
    else:
        logging.warning(f"""Logging level not informed, assuming \
{log_level}""")
    logging.basicConfig(level = getattr(logging, log_level.upper()))
    logger: object = logging.getLogger(name)
    
    ## FIXME: move to config.py
    locale_str: str = 'pt_BR.UTF-8'
    logger.debug(f"Setting locale to {locale_str}...")
    locale.setlocale(locale.LC_ALL, locale_str)
    
    try:
        from instance._bots import bots
    except Exception as e:
        logger.error("Bot list not set! Please RTFM")
        logger.exception(e)
        bots: list = ['default']
    configs: list = [import_module('.' + bot, 'instance.bots') for bot in bots]
    configs: dict = {bot: getattr(config, 'BotConfig')() \
        for bot in bots for config in configs
    }
    
    asyncio.run(personas(
        bots,
        configs[0].furhat,
        configs,
        skip_intro = config.skip_intro,
        log_messages = config.log_messages,
        add_startswith = config.add_startswith,
        add_endswith = config.add_endswith,
    ))
    logger.info(f"Finishing {name}")
except Exception as e:
    logging.exception(e)
    sys.exit("RTFM")
