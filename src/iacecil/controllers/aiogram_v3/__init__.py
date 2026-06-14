"""
ia.cecil - aiogram 3 (Telegram V3) controller setup
"""

import logging
logger = logging.getLogger(__name__)

from typing import Any
from aiogram import Dispatcher, Router
from pydantic_settings import BaseSettings
from .bot import IACecilBotV3
from .middlewares import ContextMiddleware

def aiogram_v3_startup(config: Any, name: str) -> Dispatcher:
    """
    Initializes a single aiogram 3 Dispatcher for the given bot configuration.
    """
    logger.info(f"Starting up modern aiogram 3 (Telegram V3) for {name}...")
    try:
        ## Use telegram_v3 if available, else fallback to telegram
        if hasattr(config, 'telegram_v3'):
            tel_config = config.telegram_v3
        elif hasattr(config, 'get'):
            tel_config = config.get('telegram_v3') or config.get('telegram')
        else:
            tel_config = getattr(config, 'telegram', None)
            
        if not tel_config:
            raise ValueError(f"No telegram or telegram_v3 config found for {name}")
            
        token = tel_config.get('token') if hasattr(tel_config, 'get') else getattr(tel_config, 'token', None)
        if not token:
            raise ValueError(f"No token found in telegram configuration for {name}")

        bot = IACecilBotV3(
            token=token,
            config=config,
        )
        
        dp = Dispatcher()
        
        ## FIXME backwards compat / bridge attributes
        setattr(dp, 'bot', bot)
        setattr(dp, 'name', name)
        setattr(dp, 'config', config)
        
        logger.info(f"Initialized V3 dispatcher for {name}")
        return dp
        
    except Exception as e:
        logger.error(f"Failed to initialize V3 for {name}")
        logger.exception(e)
        raise
