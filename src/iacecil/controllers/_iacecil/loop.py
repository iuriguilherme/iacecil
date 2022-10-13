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

## FIXME: Provavelmente nada disto funciona

import logging, sys

try:
    import asyncio
    import locale
    import uvicorn
    from pydantic import BaseConfig
    from quart import Quart
    from typing import Union
    from ... import (
        commit,
        name,
        version,
    )
    from ...config import ProductionConfig
    from ...views.quart_app import quart_startup
    from ..aiogram_bot import aiogram_startup
    
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
    
    ### ia.cecil
    ## Current implementation of script is using aiogram as middleware into 
    ## a quart app
    def get_app(bots: list, config: BaseSettings) -> Quart:
        """Return Quart App with provided configurations"""
        return quart_startup(
            config.quart,
            aiogram_startup(
                config,
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
    
    app: Quart = get_app(bots)
    setattr(app, 'canonical', config.canonical)
    setattr(app, 'furhat', config.furhat)

    dispatchers: list = aiogram_startup(config, bots)
    loop: Union[object, None] = None
    try:
        loop = asyncio.get_event_loop()
    except Exception as e1:
        logger.exception(e1)
        try:
            loop = asyncio.new_event_loop()
        except Exception as e2:
            logger.exception(e2)
    for dispatcher in dispatchers:
        ## TODO: Move this to bot config file
        loop.create_task(dispatcher.start_polling(
            reset_webhook = True,
            timeout = 20,
            relax = 0.1,
            fast = True,
            allowed_updates = None,
        ))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        try:
            for dispatcher in dispatchers:
                loop.call_soon(dispatcher.storage.close())
                loop.call_soon(dispatcher.storage.wait_closed())
            loop.stop()
            logger.info('done')
        except Exception as e2:
            logger.exception(e2)
    except Exception as e1:
        logger.exception(e1)
    logger.info(f"Finishing {name}")
except Exception as e:
    logging.exception(e)
    sys.exit("RTFM")
