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
    # ~ from importlib import import_module
    # ~ from natsort import natsorted
    # ~ import iacecil
    # ~ import sys
    # ~ import glob
    # ~ import asyncio
    import locale
    import uvicorn
    import quart.flask_patch
    from importlib import import_module
    from pydantic import BaseSettings
    from quart import Quart
    from typing import Union
    from ... import (
        commit,
        name,
        version,
    )
    from ...config import (
        DefaultBotConfig,
        ProductionConfig,
    )
    from ...views.quart_app import quart_startup
    from ..aiogram_bot import aiogram_startup
    
    logging.info(f"Starting {name} {version} ({commit})...")
    
    logging.debug("Loading configuration from .env files...")
    config: BaseSettings = ProductionConfig()
    default_bot_config: BaseSettings = DefaultBotConfig()
    ## TODO: testes de desenvolvimento
    # ~ from ...config import DevelopmentConfig
    # ~ config: BaseSettings = DevelopmentConfig()
    
    logging.debug("Setting log level...")
    log_level: str = 'info'
    try:
        log_level = config.log_level
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
    configs: dict = {bot: getattr(module, 'BotConfig')() \
        if 'instance.bots.' + bot == module.__name__ \
        and hasattr(module, 'BotConfig') \
        else DefaultBotConfig() \
        for bot in bots for module in modules
    }
    
    ### ia.cecil
    ## Current implementation of script is using aiogram as middleware into 
    ## a quart app
    def get_app(
        config: BaseSettings,
        configs: list[BaseSettings],
        bots: list,
    ) -> Quart:
        """Return Quart App with provided configurations"""
        return quart_startup(
            config.quart,
            aiogram_startup(
                configs,
                bots,
            ),
        )
    
    def run_app(quart_app: Quart) -> None:
        """Run provided Quart App (blocking)"""
        quart_app.run()
    
    # ~ app: Quart = quart_startup(
        # ~ config.quart,
        # ~ aiogram_startup(
            # ~ config.bots,
            # ~ ['iacecil'],
        # ~ ),
    # ~ )
    
    app: Quart = get_app(config, configs, bots)
    setattr(app, 'canonical', config.canonical)
    # ~ setattr(app, 'iacecil_config', config)
    # ~ setattr(app, 'furhat', config.furhat)
    try:
        uvicorn.run(
            app,
            uds = config.socket,
            forwarded_allow_ips = config.forwarded_allow_ips,
            proxy_headers = True,
            timeout_keep_alive = config.timeout_keep_alive,
            log_level = config.log_level.lower(),
            reload = config._reload,
        )
    except Exception as e:
        logger.exception(e)
        try:
            uvicorn.run(
                app,
                host = config.host,
                port = int(config.port),
                log_level = config.log_level.lower(),
                reload = config._reload,
            )
        except Exception as e:
            logger.error("""Neither socket or hostname is set in \
configuration file, uvicorn therefore can't start!""")
            logger.exception(e)
    logger.info(f"Finishing {name}")
except Exception as e:
    logging.exception(e)
    sys.exit("RTFM")
