import logging
import os
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

## Where matrix sync tokens live; tests patch this to a temp dir.
TOKEN_DIR = 'instance/matrix'

class Connector(BaseConnector):
    ## Safely under the 64 KiB total event bound, leaving room for
    ## envelope/JSON overhead.
    MAX_TEXT = 16000

    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.client = None
        self.running = False
        self.next_batch = None
        self.user_id = config.get('user')
        self._warned_encrypted = set()

    @classmethod
    def is_active(cls, conf: dict) -> bool:
        if not conf or not conf.get('homeserver'):
            return False
        return bool(conf.get('token')
            or (conf.get('user') and conf.get('password')))

    def _token_path(self) -> str:
        from iacecil.controllers.persistence.path_utils import (
            sanitize_component,
        )
        bot_id = getattr(self.manager, 'bot_id', 'default')
        return os.path.join(TOKEN_DIR,
            sanitize_component(bot_id) + '.next_batch')

    def _load_token(self):
        path = self._token_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                token = f.read().strip()
        except OSError as e:
            logger.warning(
                f"Matrix sync token at {path} unreadable ({e}); starting a"
                " fresh sync — joined rooms' history will be re-synced"
                " (not re-echoed; first sync never dispatches).")
            return None
        if not token:
            logger.warning(
                f"Matrix sync token at {path} is empty/corrupt; starting a"
                " fresh sync — joined rooms' history will be re-synced"
                " (not re-echoed; first sync never dispatches).")
            return None
        return token

    def _save_token(self, token: str) -> None:
        path = self._token_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        ## Atomic on every target filesystem: a crash mid-write leaves
        ## the previous good token in place.
        tmp_path = path + '.tmp'
        with open(tmp_path, 'w') as f:
            f.write(token)
        os.replace(tmp_path, path)

    async def connect(self):
        ## Lazy import: the module loads (and the manager can report a
        ## clear error) even when matrix-nio is not installed.
        import nio
        homeserver = self.config.get('homeserver')
        self.client = nio.AsyncClient(homeserver,
            user=self.config.get('user') or '')
        token = self.config.get('token')
        if token:
            self.client.access_token = token
            if not self.user_id:
                try:
                    response = await self.client.whoami()
                    self.user_id = getattr(response, 'user_id', None)
                except Exception as e:
                    logger.warning(f"Matrix whoami failed: {e}")
        else:
            response = await self.client.login(self.config.get('password'))
            if not getattr(response, 'access_token', None):
                raise ConnectionError(f"Matrix login failed: {response!r}")
            self.user_id = getattr(response, 'user_id', self.user_id)
        self.next_batch = self._load_token()
        self.running = True

    async def _on_event(self, room_id, event):
        sender = getattr(event, 'sender', None)
        if sender is None or sender == self.user_id:
            ## Own messages echoed back by sync; replying would loop
            return
        body = getattr(event, 'body', None)
        if body is None:
            ## Encrypted or non-message event; plaintext rooms only
            if (event.__class__.__name__ == 'MegolmEvent'
                    and room_id not in self._warned_encrypted):
                self._warned_encrypted.add(room_id)
                logger.warning(
                    f"Room {room_id} is encrypted; this connector handles"
                    " plaintext rooms only — ignoring its events.")
            return
        timestamp = getattr(event, 'server_timestamp', None)
        env = Envelope(
            platform='matrix',
            sender_ref=str(sender),
            conversation_ref=str(room_id),
            text=body,
            raw=event,
            native_message_id=getattr(event, 'event_id', None),
            timestamp=timestamp / 1000 if timestamp else None,
        )
        await self.manager.dispatch(env)

    async def listen(self):
        if not self.client:
            raise ValueError("Matrix client not initialized")
        while self.running:
            response = await self.client.sync(timeout=30000,
                since=self.next_batch)
            next_batch = getattr(response, 'next_batch', None)
            if not next_batch:
                raise ConnectionError(f"Matrix sync failed: {response!r}")
            first_sync = self.next_batch is None
            self.next_batch = next_batch
            self._save_token(next_batch)
            if first_sync:
                ## Token acquisition only: dispatching the initial sync
                ## would reply to every joined room's backlog.
                continue
            rooms = getattr(getattr(response, 'rooms', None), 'join', None) or {}
            for room_id, room_info in rooms.items():
                events = (getattr(getattr(room_info, 'timeline', None),
                    'events', None) or [])
                for event in events:
                    await self._on_event(room_id, event)

    async def send(self, envelope: Envelope):
        if not self.client:
            return
        text = envelope.text or ""
        for i in range(0, len(text), self.MAX_TEXT):
            await self.client.room_send(
                room_id=envelope.conversation_ref,
                message_type="m.room.message",
                content={"msgtype": "m.text",
                    "body": text[i:i + self.MAX_TEXT]},
            )

    async def disconnect(self):
        self.running = False
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass
