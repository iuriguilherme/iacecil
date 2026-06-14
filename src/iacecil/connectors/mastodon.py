import logging
import asyncio
import re
import html as _html
from .base import BaseConnector
from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r'<[^>]+>')


def strip_html(content: str) -> str:
    """Mastodon status.content is HTML; envelopes carry plain text.
    Preserve paragraph/line breaks, drop the rest, unescape entities."""
    if not content:
        return ''
    text = (content
        .replace('</p><p>', '\n\n')
        .replace('<br>', '\n')
        .replace('<br/>', '\n')
        .replace('<br />', '\n'))
    return _html.unescape(_TAG_RE.sub('', text)).strip()


class Connector(BaseConnector):
    required_keys = ('api_base_url', 'access_token')
    ## Mastodon's default per-status character limit; instances may
    ## raise it, but 500 is the safe floor (cf. matrix's conservative
    ## MAX_TEXT pin).
    MAX_TEXT = 500
    ## How often listen() wakes to check the streaming thread is alive
    ## (overridable in tests).
    POLL_INTERVAL = 1
    ## Per-request timeout for the blocking Mastodon client so a slow
    ## instance cannot tie up to_thread workers indefinitely.
    REQUEST_TIMEOUT = 10

    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.client = None
        self.running = False
        self.own_account_id = None
        self._stream_handle = None

    async def connect(self):
        ## Lazy import: the module loads (and the manager can report a
        ## clear error) even when Mastodon.py is not installed.
        import mastodon
        self.client = mastodon.Mastodon(
            access_token=self.config.get('access_token'),
            api_base_url=self.config.get('api_base_url'),
            request_timeout=self.REQUEST_TIMEOUT,
        )
        try:
            ## Resolve own account id for the self-message guard.
            me = await asyncio.to_thread(self.client.account_verify_credentials)
            self.own_account_id = me['id'] if me is not None else None
        except Exception as e:
            logger.warning(f"Mastodon account_verify_credentials failed: {e}")
        self.running = True

    def _status_to_envelope(self, status) -> Envelope:
        account = status.get('account') or {}
        created = status.get('created_at')
        status_id = str(status.get('id'))
        return Envelope(
            platform='mastodon',
            sender_ref=str(account.get('id')),
            ## Reply target: post our answer in-reply-to this status.
            conversation_ref=status_id,
            text=strip_html(status.get('content')),
            raw=status,
            reply_ref=status_id,
            native_message_id=status_id,
            timestamp=created.timestamp() if created is not None else None,
        )

    async def _handle_status(self, status):
        account = status.get('account') or {}
        if (self.own_account_id is not None
                and str(account.get('id')) == str(self.own_account_id)):
            ## Own status streamed back; replying would loop.
            return
        await self.manager.dispatch(self._status_to_envelope(status))

    def _make_listener(self, loop):
        import mastodon
        connector = self

        class _Listener(mastodon.StreamListener):
            def on_notification(self, notification):
                ## Echo trigger for v1: mentions only.
                if notification.get('type') != 'mention':
                    return
                status = notification.get('status')
                if status is None:
                    return
                ## This callback runs on the streaming worker thread;
                ## marshal the async dispatch back onto the event loop.
                future = asyncio.run_coroutine_threadsafe(
                    connector._handle_status(status), loop)

                def _log_dispatch_error(fut):
                    ## The future is otherwise fire-and-forget; surface
                    ## dispatch/persistence failures instead of swallowing.
                    if fut.cancelled():
                        return
                    exc = fut.exception()
                    if exc is not None:
                        logger.error(f"Mastodon dispatch error: {exc!r}")

                future.add_done_callback(_log_dispatch_error)

        return _Listener()

    async def listen(self):
        if not self.client:
            raise ValueError("Mastodon client not initialized")
        loop = asyncio.get_running_loop()
        listener = self._make_listener(loop)
        ## stream_user(run_async=True) streams on its own thread and
        ## returns a handle we can close on shutdown; keep listen() alive
        ## until disconnect() flips running (cf. the xmpp connector).
        self._stream_handle = await asyncio.to_thread(
            self.client.stream_user, listener, run_async=True)
        while self.running:
            await asyncio.sleep(self.POLL_INTERVAL)
            ## The stream runs on its own thread; if it dies silently
            ## (network drop, instance down) this loop would otherwise spin
            ## forever with the connector wrongly considered up. Surface it
            ## so _run_connector marks the connector down.
            handle = self._stream_handle
            is_alive = getattr(handle, 'is_alive', None)
            if is_alive is not None and not is_alive():
                raise ConnectionError(
                    "Mastodon streaming thread exited unexpectedly")

    async def send(self, envelope: Envelope):
        if not self.client:
            logger.warning("Mastodon send dropped: client not initialized.")
            return
        ## Thread the answer onto the source status. Echo replies built by
        ## dispatch() carry no reply_ref, so fall back to conversation_ref
        ## (which, for mastodon, *is* the status id to reply to); without
        ## this the reply posts as an orphan top-level status.
        in_reply_to = envelope.reply_ref or envelope.conversation_ref
        for chunk in self._chunks(envelope.text):
            await asyncio.to_thread(
                self.client.status_post,
                chunk,
                in_reply_to_id=in_reply_to,
            )
            ## Only the first chunk threads onto the original status; the
            ## rest follow as a self-reply chain.
            in_reply_to = None

    async def disconnect(self):
        self.running = False
        handle = self._stream_handle
        if handle is not None:
            try:
                handle.close()
            except Exception:
                ## A close failure during shutdown must not mask the
                ## original teardown trigger.
                pass
