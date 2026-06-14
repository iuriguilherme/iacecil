"""
ia.cecil - Telegram V3 Connector (aiogram 3)
"""

import logging
logger = logging.getLogger(__name__)

import asyncio
from typing import Any
from aiogram import Dispatcher, Router, types
from .base import BaseConnector
from ..controllers.aiogram_v3 import aiogram_v3_startup
from ..controllers.aiogram_v3.middlewares import ContextMiddleware

class TelegramV3Connector(BaseConnector):
    ## Requires 'token' in its config section
    required_keys = ('token',)

    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.platform = 'telegram_v3'
        self.dispatcher = None
        self.bot = None

    async def connect(self):
        """Initializes the aiogram 3 dispatcher and bot"""
        logger.info(f"Connecting Telegram V3 for bot {self.manager.bot_id}...")
        ## Fix: Pass full bot_config so startup can pull telegram_v3 or telegram
        self.dispatcher = aiogram_v3_startup(self.manager.bot_config, self.manager.bot_id)
        self.bot = getattr(self.dispatcher, 'bot')
        
        ## Attach manager to dispatcher for DI middleware
        setattr(self.dispatcher, 'manager', self.manager)
        
        ## Setup Middleware
        self.dispatcher.message.middleware(ContextMiddleware(self.manager, self.manager.bot_config, self.config))
        self.dispatcher.callback_query.middleware(ContextMiddleware(self.manager, self.manager.bot_config, self.config))
        
        ## Register handlers from plugins
        await self.register_plugins()
        
        ## Global Update Logger for debugging
        @self.dispatcher.update()
        async def v3_update_logger(update: types.Update):
            logger.debug(f"V3 Bot {self.manager.bot_id} received update: {update.update_id} (type={update.event_type})")
            return None # Continue to other handlers

        ## Fallback bridge handler: translates aiogram 3 Message to ia.cecil Envelope
        ## This ensures compatibility with generic plugins and personalities.
        @self.dispatcher.message()
        async def v3_bridge_handler(message: types.Message):
            from ..controllers.aiogram_v3.callbacks import message_callback
            logger.debug(f"V3 Bridge handling message {message.message_id}")
            await message_callback(message, manager=self.manager)

        self.running = True

    async def listen(self):
        """Starts long polling for the bot"""
        logger.info(f"Starting polling for Telegram V3 bot {self.manager.bot_id}...")
        
        ## Ensure aiogram logger is at the same level as our root logger
        aiogram_logger = logging.getLogger('aiogram')
        aiogram_logger.setLevel(logger.root.level)
        
        try:
            ## aiogram 3 start_polling blocks. 
            ## handle_signals=False is crucial when running multiple bots in the same loop.
            await self.dispatcher.start_polling(self.bot, handle_signals=False)
        except asyncio.CancelledError:
            logger.info(f"Polling cancelled for Telegram V3 bot {self.manager.bot_id}")
            raise
        except Exception as e:
            logger.error(f"Polling failed for Telegram V3 bot {self.manager.bot_id}")
            logger.exception(e)
            self.running = False

    async def send(self, envelope):
        """Sends an envelope via Telegram"""
        if not self.bot:
            logger.error(f"Cannot send: bot not initialized for {self.platform}")
            return
            
        try:
            await self.bot.send_message(
                chat_id=envelope.conversation_ref,
                text=envelope.text,
                reply_to_message_id=envelope.reply_ref if envelope.reply_ref else None
            )
        except Exception as e:
            logger.error(f"Failed to send message via Telegram V3: {e}")

    async def register_plugins(self):
        """Registers handlers from enabled plugins"""
        from . import load_plugin
        config = self.manager.bot_config
        if hasattr(config, 'plugins'):
            enabled_plugins = config.plugins.get('enable', [])
        else:
            enabled_plugins = config.get('plugins', {}).get('enable', [])
            
        for plugin_name in enabled_plugins:
            try:
                ## Pass the dispatcher itself as the target for V3 handlers
                await load_plugin(self.platform, plugin_name, self.dispatcher)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name} for Telegram V3")
                logger.exception(e)

    async def disconnect(self):
        """Shuts down the bot session"""
        logger.info(f"Disconnecting Telegram V3 for bot {self.manager.bot_id}...")
        self.running = False
        if self.dispatcher:
            try:
                await self.dispatcher.stop_polling()
            except Exception:
                pass
        if self.bot:
            await self.bot.session.close()
Connector = TelegramV3Connector
