import asyncio
import logging
import os
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

## Where matrix sync tokens live; tests patch this to a temp dir.
TOKEN_DIR = 'instance/matrix'
STORE_DIR = os.path.join(TOKEN_DIR, 'store')

class Connector(BaseConnector):
    ## Safely under the 64 KiB total event bound, leaving room for
    ## envelope/JSON overhead.
    MAX_TEXT = 16000

    ## Sync retry policy (overridable in tests). Transient sync errors
    ## back off exponentially; the connector is only marked down after
    ## SYNC_MAX_FAILURES consecutive failures, or immediately on a
    ## permanent error that no retry can fix.
    SYNC_BACKOFF_BASE = 2.0
    SYNC_BACKOFF_CAP = 60.0
    SYNC_MAX_FAILURES = 10
    PERMANENT_SYNC_ERRORS = frozenset({
        'M_UNKNOWN_TOKEN', 'M_MISSING_TOKEN', 'M_FORBIDDEN'})
    ## A sync position the server no longer recognises (corrupt/expired
    ## next_batch): not fatal — discard it and re-sync from scratch.
    RECOVERABLE_SYNC_ERRORS = frozenset({'M_UNKNOWN_POS'})

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

    def is_authorized(self, envelope: Envelope) -> bool:
        """Checks if the envelope's conversation is authorized for replies."""
        authorized_channels = self.config.get('channels') or []
        room_id = envelope.conversation_ref
        
        logger.debug(f"Checking authorization for Matrix room {room_id}")
        logger.debug(f"Authorized channels: {authorized_channels}")
        
        # 1. Authorize explicitly configured channels
        if str(room_id) in [str(c) for c in authorized_channels]:
            logger.debug(f"Room {room_id} authorized by ID match.")
            return True
            
        # 2. Check room state for aliases or member count (DMs)
        if self.client and hasattr(self.client, 'rooms'):
            room = self.client.rooms.get(room_id)
            if room:
                # 2a. Check aliases
                room_aliases = []
                if hasattr(room, 'canonical_alias') and room.canonical_alias:
                    room_aliases.append(room.canonical_alias)
                # alt_aliases might be available in newer nio versions
                if hasattr(room, 'alt_aliases'):
                    room_aliases.extend(room.alt_aliases)
                
                logger.debug(f"Room {room_id} aliases: {room_aliases}")
                for alias in room_aliases:
                    if str(alias) in [str(c) for c in authorized_channels]:
                        logger.debug(f"Room {room_id} authorized by alias match: {alias}")
                        return True

                # 2b. Authorize 1:1 DMs (rooms with 2 or fewer members)
                # nio.MatrixRoom has member_count; fallback to users dict length
                member_count = getattr(room, 'member_count', len(getattr(room, 'users', {})))
                logger.debug(f"Room {room_id} member count: {member_count}")
                if member_count > 0 and member_count <= 2:
                    logger.debug(f"Room {room_id} authorized as DM (count={member_count}).")
                    return True
            else:
                logger.debug(f"Room {room_id} not found in client.rooms")
                
        logger.debug(f"Room {room_id} NOT authorized.")
        return False

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

    def _discard_token(self) -> None:
        """Remove a rejected sync token so the next boot syncs fresh."""
        try:
            os.remove(self._token_path())
        except FileNotFoundError:
            pass
        except OSError as e:
            logger.warning(f"Matrix could not discard sync token: {e}")

    def _save_token(self, token: str) -> None:
        path = self._token_path()
        os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
        ## Atomic on every target filesystem: a crash mid-write leaves
        ## the previous good token in place. 0600 is defense-in-depth —
        ## next_batch is a sync cursor, not a credential, but there is no
        ## reason for it to be world-readable.
        tmp_path = path + '.tmp'
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(token)
        os.replace(tmp_path, path)

    async def connect(self):
        ## Lazy import: the module loads (and the manager can report a
        ## clear error) even when matrix-nio is not installed.
        import nio
        homeserver = self.config.get('homeserver')
        if homeserver and not (homeserver.startswith('http://') or homeserver.startswith('https://')):
            homeserver = f"https://{homeserver}"
            
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
            logger.warning(
                f"Matrix connector for {self.user_id or 'unknown'} using"
                " password login; this is bootstrap-only — please exchange"
                " for an access token and update your config for better"
                " security.")
            response = await self.client.login(self.config.get('password'))
            if not getattr(response, 'access_token', None):
                ## To avoid leaking credentials or sensitive object state, we 
                ## only log the 'status_code' (e.g. M_FORBIDDEN) and 'message' 
                ## (human-readable description), which are standard Matrix 
                ## error fields parsed by matrix-nio.
                status = getattr(response, 'status_code', 'M_UNKNOWN')
                error_msg = getattr(response, 'message', 'No error message provided by server')
                raise ConnectionError(f"Matrix login failed: {status} - {error_msg}")
            self.user_id = getattr(response, 'user_id', self.user_id)
        if not self.user_id:
            ## Without our own mxid the self-message guard in _on_event
            ## cannot fire, so the bot would echo its own messages in a
            ## loop. Fail closed instead of starting in that state.
            raise ConnectionError(
                "Matrix own user_id unknown after login; refusing to start"
                " (self-message guard would fail and cause an echo loop).")
        self.next_batch = self._load_token()
        self.running = True

    async def _on_event(self, room_id, event):
        sender = getattr(event, 'sender', None)
        logger.debug(f"Matrix: received event in room {room_id} from {sender}")
        
        if sender is None or sender == self.user_id:
            ## Own messages echoed back by sync; replying would loop
            logger.debug(f"Matrix: skipping event from self or None ({sender})")
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
            logger.debug(f"Matrix: skipping event without body (class={event.__class__.__name__})")
            return
            
        logger.debug(f"Matrix: dispatching message: {body!r}")
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
        
        # 1. Join configured channels on startup
        authorized_channels = self.config.get('channels') or []
        for channel in authorized_channels:
            try:
                # nio.AsyncClient.join can take room ID or alias
                await self.client.join(channel)
                logger.info(f"Matrix: joined configured room {channel}")
            except Exception as e:
                logger.warning(f"Matrix: could not join configured room {channel}: {e}")

        failures = 0
        backoff = self.SYNC_BACKOFF_BASE
        while self.running:
            try:
                response = await self.client.sync(timeout=30000,
                    since=self.next_batch)
            except Exception as e:
                response = None
                exc = e
            else:
                exc = None
            
            next_batch = getattr(response, 'next_batch', None)
            if not next_batch:
                ## Error response (or raised exception). A permanent error
                ## cannot be retried away — mark down at once. Otherwise
                ## back off and retry; only give up after SYNC_MAX_FAILURES.
                status = getattr(response, 'status_code', None)
                if status in self.PERMANENT_SYNC_ERRORS:
                    raise ConnectionError(
                        f"Matrix sync permanent error {status}: {response!r}")
                if status in self.RECOVERABLE_SYNC_ERRORS:
                    ## Stale/corrupt sync position: drop it and re-sync from
                    ## scratch instead of bricking on a token the server
                    ## will reject forever. (first sync never dispatches.)
                    logger.warning(
                        f"Matrix sync position rejected ({status}); discarding"
                        " token and re-syncing fresh.")
                    self.next_batch = None
                    await asyncio.to_thread(self._discard_token)
                    failures = 0
                    backoff = self.SYNC_BACKOFF_BASE
                    continue
                failures += 1
                detail = exc if exc is not None else repr(response)
                if failures >= self.SYNC_MAX_FAILURES:
                    raise ConnectionError(
                        f"Matrix sync failed {failures} times: {detail}")
                logger.warning(
                    f"Matrix sync error (attempt {failures}), retrying in"
                    f" {backoff}s: {detail}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self.SYNC_BACKOFF_CAP)
                continue
            
            ## Success: reset the retry state.
            failures = 0
            backoff = self.SYNC_BACKOFF_BASE
            
            # 2. Handle invitations
            invited_rooms = getattr(getattr(response, 'rooms', None), 'invite', None) or {}
            for room_id in invited_rooms:
                logger.info(f"Matrix: accepting invitation to room {room_id}")
                try:
                    await self.client.join(room_id)
                except Exception as e:
                    logger.error(f"Matrix: failed to join invited room {room_id}: {e}")

            first_sync = self.next_batch is None
            self.next_batch = next_batch
            if first_sync:
                ## Token acquisition only: dispatching the initial sync
                ## would reply to every joined room's backlog. Persist now
                ## (nothing to dispatch) so the backlog is never replayed.
                ## File write is blocking; keep it off the event loop.
                await asyncio.to_thread(self._save_token, next_batch)
                continue
            
            rooms = getattr(getattr(response, 'rooms', None), 'join', None) or {}
            for room_id, room_info in rooms.items():
                events = (getattr(getattr(room_info, 'timeline', None),
                    'events', None) or [])
                for event in events:
                    try:
                        await self._on_event(room_id, event)
                    except Exception as e:
                        ## One malformed event must not kill the sync loop
                        ## and take the whole connector down with it.
                        logger.error(
                            "Matrix: error dispatching event"
                            f" {getattr(event, 'event_id', None)!r} in"
                            f" {room_id}: {e}")
            ## Persist the token only after this batch's events were
            ## dispatched. A crash mid-batch re-syncs from the previous
            ## token next boot; native-id dedupe in the chat store makes
            ## the replay idempotent (effectively-once) rather than
            ## silently dropping the messages between save and dispatch.
            ## File write is blocking; keep it off the event loop.
            await asyncio.to_thread(self._save_token, next_batch)

    async def send(self, envelope: Envelope):
        if not self.client:
            ## Silent return would let manager.send report success and the
            ## dispatch path persist a dropped reply as delivered.
            logger.warning("Matrix send dropped: client not initialized.")
            return
        for chunk in self._chunks(envelope.text):
            await self.client.room_send(
                room_id=envelope.conversation_ref,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": chunk},
            )

    async def disconnect(self):
        self.running = False
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass
