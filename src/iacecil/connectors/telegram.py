import logging
import asyncio
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

class Connector(BaseConnector):
    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.bot = None
        self.dispatcher = None
        self.running = False
        
    async def connect(self):
        if getattr(self, 'bot', None) is None:
            from ..controllers.aiogram_bot.bot import IACecilBot
            from aiogram import Dispatcher
            self.bot = IACecilBot(token=self.config.get('token'), config=self.manager.bot_config)
            self.dispatcher = Dispatcher(self.bot)
            self.dispatcher.manager = self.manager
        self.running = True

    async def listen(self):
        if not self.dispatcher:
            raise ValueError("Dispatcher not initialized")
            
        try:
            # Polling loop
            while self.running:
                # we don't do while self.running around start_polling usually, start_polling blocks
                # but if start_polling exits, we could retry if self.running is still True.
                await self.dispatcher.start_polling(
                    reset_webhook=True,
                    timeout=20,
                    relax=0.1,
                    fast=True,
                    allowed_updates=None,
                )
                if not self.running:
                    break
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Polling exception: {e}")
            raise

    async def send(self, envelope: Envelope):
        if not self.bot:
            return
            
        chat_id = envelope.conversation_ref
        reply_to_message_id = envelope.reply_ref
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=envelope.text,
            reply_to_message_id=reply_to_message_id
        )

    async def disconnect(self):
        self.running = False
        if self.dispatcher:
            self.dispatcher.stop_polling()
