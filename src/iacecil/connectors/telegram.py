import logging
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

class Connector(BaseConnector):
    required_keys = ('token',)
    MAX_TEXT = 4096

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

        ## start_polling blocks until stop_polling is called or polling
        ## fails; a failure propagates so the manager marks this
        ## connector down.
        await self.dispatcher.start_polling(
            reset_webhook=True,
            timeout=20,
            relax=0.1,
            fast=True,
            allowed_updates=None,
        )

    async def send(self, envelope: Envelope):
        if not self.bot:
            return

        chat_id = envelope.conversation_ref
        text = envelope.text or ""

        ## Telegram rejects messages over 4096 chars; chunk, replying
        ## only on the first chunk.
        for i in range(0, len(text), self.MAX_TEXT):
            await self.bot.send_message(
                chat_id=chat_id,
                text=text[i:i + self.MAX_TEXT],
                reply_to_message_id=envelope.reply_ref if i == 0 else None,
            )

    async def disconnect(self):
        self.running = False
        if self.dispatcher:
            self.dispatcher.stop_polling()
