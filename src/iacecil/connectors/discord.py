import asyncio
import logging
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

class Connector(BaseConnector):
    required_keys = ('token',)
    MAX_TEXT = 2000
    ## Cap on a single Discord API call so a slow/hung gateway cannot
    ## block the event loop indefinitely (overridable in tests).
    SEND_TIMEOUT = 10.0

    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.client = None
        self.running = False
        self._warned_empty_content = False

    async def connect(self):
        ## Lazy import: the module loads (and the manager can report a
        ## clear error) even when discord.py is not installed.
        import discord
        intents = discord.Intents.default()
        ## Without this — and the matching toggle in the developer
        ## portal — message.content arrives empty.
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        connector = self

        @self.client.event
        async def on_message(message):
            await connector._on_message(message)

        self.running = True

    def is_authorized(self, envelope: Envelope) -> bool:
        """Checks if the envelope's conversation is authorized for replies.
        DMs are always authorized. Guild channels must be in the 'channels' list."""
        if envelope.conversation_ref == envelope.sender_ref:
            ## It's a DM (sender == conversation)
            return True
        authorized_channels = self.config.get('channels') or []
        return str(envelope.conversation_ref) in [str(c) for c in authorized_channels]

    async def _on_message(self, message):
        author = getattr(message, 'author', None)
        ## Skip self and every other bot: discord bots see each other's
        ## messages (unlike telegram), and with echo as the default
        ## handler two bots would feed each other forever.
        if author is None or getattr(author, 'bot', False):
            return
        text = message.content or ''
        
        if not text and not self._warned_empty_content:
            self._warned_empty_content = True
            logger.warning(
                "Discord message arrived with empty content — enable the"
                " Message Content intent in the developer portal.")
        reply_ref = None
        reference = getattr(message, 'reference', None)
        if reference is not None and getattr(reference, 'message_id', None):
            reply_ref = str(reference.message_id)
        created = getattr(message, 'created_at', None)
        env = Envelope(
            platform='discord',
            sender_ref=str(author.id),
            conversation_ref=str(message.channel.id),
            text=text,
            reply_ref=reply_ref,
            raw=message,
            native_message_id=str(message.id),
            timestamp=created.timestamp() if created is not None else None,
        )
        await self.manager.dispatch(env)

    async def listen(self):
        if not self.client:
            raise ValueError("Discord client not initialized")
        ## start() blocks until close() or a gateway failure; failures
        ## propagate so the manager marks this connector down.
        await self.client.start(self.config.get('token'))

    def _reference(self, channel, reply_ref):
        ## Reached only from send(), after connect() imported discord and
        ## set self.client — the library is guaranteed available here.
        import discord
        return discord.MessageReference(
            message_id=int(reply_ref),
            channel_id=channel.id,
            fail_if_not_exists=False,
        )

    async def send(self, envelope: Envelope):
        if not self.client:
            logger.warning("Discord send dropped: client not initialized.")
            return
        channel_id = int(envelope.conversation_ref)
        channel = self.client.get_channel(channel_id)
        if channel is None:
            try:
                channel = await asyncio.wait_for(
                    self.client.fetch_channel(channel_id), self.SEND_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(
                    f"Discord fetch_channel timed out for {channel_id};"
                    " dropping reply.")
                return
        for index, chunk in enumerate(self._chunks(envelope.text)):
            kwargs = {}
            if index == 0 and envelope.reply_ref:
                reference = self._reference(channel, envelope.reply_ref)
                if reference is not None:
                    kwargs['reference'] = reference
            try:
                await asyncio.wait_for(
                    channel.send(chunk, **kwargs),
                    self.SEND_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(
                    "Discord channel.send timed out; dropping remaining"
                    " message chunks.")
                return

    async def disconnect(self):
        self.running = False
        if self.client:
            try:
                await self.client.close()
            except Exception:
                ## A close failure during shutdown must not mask the
                ## original error that triggered teardown.
                pass
