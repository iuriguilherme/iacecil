import logging
import asyncio
from slixmpp import ClientXMPP
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

class XMPPBot(ClientXMPP):
    def __init__(self, jid, password, connector):
        super().__init__(jid, password)
        self.connector = connector
        self.manager = connector.manager
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("failed_auth", self.on_failure)
        self.add_event_handler("connection_failed", self.on_failure)
        self.add_event_handler("disconnected", self.on_disconnected)

    async def start(self, event):
        logger.info(f"XMPP session started as {self.boundjid.full}")
        self.send_presence()
        self.get_roster()
        channels = self.connector.config.get('channels') or []
        for channel in channels:
            self.plugin['xep_0045'].join_muc(channel, self.boundjid.user)

    async def on_failure(self, event):
        self.connector.failure = "XMPP authentication or connection failed"
        self.connector.running = False

    async def on_disconnected(self, event):
        ## Unexpected disconnect (not initiated by Connector.disconnect)
        if self.connector.running:
            self.connector.failure = "XMPP session disconnected unexpectedly"
            self.connector.running = False

    async def message(self, msg):
        if msg['type'] == 'groupchat':
            if msg['from'].resource == self.boundjid.user:
                return
        elif msg['from'].full == self.boundjid.full:
            ## Own messages echoed back by server; replying would loop
            return
            
        if msg['type'] in ('chat', 'normal', 'groupchat'):
            stanza_id = str(msg['id']) if msg['id'] else None
            env = Envelope(
                platform='xmpp',
                sender_ref=str(msg['from'].bare),
                conversation_ref=str(msg['from'].bare),
                text=msg['body'],
                raw=msg,
                native_message_id=stanza_id,
            )
            await self.manager.dispatch(env)

class Connector(BaseConnector):
    required_keys = ('jid', 'password')
    ## Conservative message length limit; servers vary
    MAX_TEXT = 4000

    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.running = False
        self.bot = None
        self.failure = None

    def is_authorized(self, envelope: Envelope) -> bool:
        message = envelope.raw
        if message is not None and message.get('type') != 'groupchat':
            return True
        authorized_channels = self.config.get('channels') or []
        return str(envelope.conversation_ref) in [str(c) for c in authorized_channels]

    async def connect(self):
        jid = self.config.get('jid')
        password = self.config.get('password')
        self.bot = XMPPBot(jid, password, self)
        self.bot.register_plugin('xep_0045')
        self.bot.connect()
        self.running = True

    async def listen(self):
        if not self.bot:
            raise ValueError("XMPP Bot not initialized")

        while self.running:
            await asyncio.sleep(1)
        if self.failure:
            raise ConnectionError(self.failure)

    async def send(self, envelope: Envelope):
        if not self.bot:
            return

        mtype = 'chat'
        if envelope.raw and envelope.raw.get('type') == 'groupchat':
            mtype = 'groupchat'

        for chunk in self._chunks(envelope.text):
            self.bot.send_message(mto=envelope.conversation_ref, mbody=chunk, mtype=mtype)

    async def disconnect(self):
        self.running = False
        if self.bot:
            self.bot.disconnect()
