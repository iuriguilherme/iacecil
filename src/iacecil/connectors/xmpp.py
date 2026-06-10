import logging
import asyncio
from slixmpp import ClientXMPP
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

class XMPPBot(ClientXMPP):
    def __init__(self, jid, password, manager):
        super().__init__(jid, password)
        self.manager = manager
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.send_presence()
        self.get_roster()

    async def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            env = Envelope(
                platform='xmpp',
                sender_ref=str(msg['from'].bare),
                conversation_ref=str(msg['from'].bare),
                text=msg['body'],
                raw=msg
            )
            await self.manager.dispatch(env)

class Connector(BaseConnector):
    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.running = False
        self.bot = None

    async def connect(self):
        jid = self.config.get('jid')
        password = self.config.get('password')
        self.bot = XMPPBot(jid, password, self.manager)
        
        # Connect
        self.bot.connect()
        self.running = True

    async def listen(self):
        if not self.bot:
            raise ValueError("XMPP Bot not initialized")
        
        # Keep task alive
        while self.running:
            await asyncio.sleep(1)

    async def send(self, envelope: Envelope):
        if not self.bot:
            return
        
        text = envelope.text or ""
        # split by 4000
        for i in range(0, len(text), 4000):
            chunk = text[i:i+4000]
            self.bot.send_message(mto=envelope.conversation_ref, mbody=chunk, mtype='chat')

    async def disconnect(self):
        self.running = False
        if self.bot:
            self.bot.disconnect()
