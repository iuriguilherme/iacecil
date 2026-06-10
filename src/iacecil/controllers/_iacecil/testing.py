import asyncio
import logging
import sys
from iacecil.config import DefaultBotConfig
from iacecil.connectors import ConnectorManager

logger = logging.getLogger(__name__)

def run_app(*args):
    logger.info("Starting loopback dev runner...")
    
    try:
        config_dict = DefaultBotConfig().model_dump()
    except AttributeError:
        config_dict = getattr(DefaultBotConfig(), '__dict__', {})
        if not config_dict:
            config_dict = {}
        
    config_dict['loopback'] = {'enabled': True}
    
    manager = ConnectorManager(config_dict)

    ## Personality commands handle /start, /help etc; everything else
    ## gets an echo so the REPL always answers.
    async def fallback_handler(env):
        return f"Echo: {env.text}"

    manager.set_default_handler(fallback_handler)
    
    try:
        asyncio.run(manager.run_all())
    except KeyboardInterrupt:
        logger.info("Exiting cleanly")
    except Exception as e:
        logger.exception(e)
