"""Platform-neutral operator logging: route stdlib logging records to
chat conversations on any active connector.

Bot config carries ``log_sinks``: a list of
``{platform, conversation_ref, level, tags, logger, verbose}`` entries.
``logger`` filters by logger-name prefix (e.g.
``iacecil.connectors.xmpp`` at ERROR routed to a private telegram
group); ``verbose`` opts a trusted sink into full tracebacks — the
default format excludes in-flight message content and caps tracebacks.

Additive to controllers/log.py (R8): the legacy telegram-only loggers
keep working; this module never imports them.
"""

import asyncio
import contextvars
import logging
import sys
import time
import traceback
from collections import deque

from iacecil.models.envelope import Envelope

logger = logging.getLogger(__name__)

## Records from this module's own namespace never re-enter the handler
_OWN_PREFIX = __name__

## Set while a record is being delivered through manager.send; any
## logging emitted by that delivery (connector internals, libraries) is
## dropped instead of recursing.
_delivering = contextvars.ContextVar('log_sink_delivering', default=False)

MAX_QUEUE = 1000
TRACEBACK_CAP = 500
DRAIN_INTERVAL = 0.5


class ConnectorLogHandler(logging.Handler):
    def __init__(self, manager, sinks):
        super().__init__()
        self.manager = manager
        self.sinks = [dict(sink) for sink in (sinks or [])]
        self.queue = deque(maxlen=MAX_QUEUE)
        ## Sinks forward records off-host to chat platforms. The default
        ## formatter excludes in-flight message content, but a sink set
        ## below WARNING will forward whatever other modules log at DEBUG/
        ## INFO — which may include user message text or model output
        ## (e.g. the deepseek plugin). Warn so the exposure is a choice.
        for sink in self.sinks:
            if self._sink_level(sink) < logging.WARNING:
                logger.warning(
                    "Log sink for %s/%s is below WARNING (%s): it will"
                    " forward DEBUG/INFO records — which may contain user"
                    " message content — off-host to that chat.",
                    sink.get('platform'), sink.get('conversation_ref'),
                    sink.get('level'))

    @staticmethod
    def _sink_level(sink) -> int:
        level = sink.get('level', 'WARNING')
        if isinstance(level, int):
            return level
        return getattr(logging, str(level).upper(), logging.WARNING)

    def _matches(self, sink, record) -> bool:
        if record.levelno < self._sink_level(sink):
            return False
        prefix = sink.get('logger')
        if prefix and not record.name.startswith(prefix):
            return False
        tags = sink.get('tags')
        if tags:
            record_tags = set(getattr(record, 'tags', None) or [])
            if not record_tags.intersection(set(tags)):
                return False
        return True

    def _format_sink(self, record, verbose: bool) -> str:
        ## Deliberate field list: level, time, logger, message. The
        ## in-flight envelope text/sender of handled messages is never
        ## included, and tracebacks are capped unless the sink opted
        ## into verbose — sinks deliver off-host to chat platforms.
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S',
            time.gmtime(record.created))
        text = f"[{record.levelname}] {timestamp} {record.name}: " \
            f"{record.getMessage()}"
        if record.exc_info:
            tb = ''.join(traceback.format_exception(*record.exc_info))
            if not verbose and len(tb) > TRACEBACK_CAP:
                tb = tb[:TRACEBACK_CAP] + ' ...[truncated]'
            text += '\n' + tb
        return text

    def emit(self, record):
        ## stdlib contract: emit never raises into the logging caller.
        try:
            if record.name.startswith(_OWN_PREFIX):
                return
            if _delivering.get():
                return
            for sink in self.sinks:
                if self._matches(sink, record):
                    self.queue.append(
                        (sink, self._format_sink(record,
                            bool(sink.get('verbose')))))
        except Exception:
            self.handleError(record)

    async def flush_ready(self):
        """Deliver queued records whose sink's connector is connected;
        records for present-but-not-yet-connected platforms stay queued
        (the bounded queue buffers boot-time records)."""
        requeue = []
        while self.queue:
            sink, text = self.queue.popleft()
            platform = sink.get('platform')
            connector = self.manager.connectors.get(platform)
            if connector is not None and not getattr(connector, 'running',
                    False):
                requeue.append((sink, text))
                continue
            ## Absent platform: manager.send warns once and drops.
            token = _delivering.set(True)
            try:
                await self.manager.send(Envelope(
                    platform=platform,
                    sender_ref='log',
                    conversation_ref=str(sink.get('conversation_ref')),
                    text=text,
                ))
            except Exception as e:
                ## manager.send never raises by contract; this is the
                ## last-resort guard. Never back into logging.
                sys.stderr.write(f"log sink delivery failed: {e!r}\n")
            finally:
                _delivering.reset(token)
        ## Prepend, don't append: records emitted by other tasks during
        ## the awaits above may have refilled the bounded deque, and
        ## extend() would evict exactly the boot-time records we are
        ## holding for a not-yet-connected sink. Front placement keeps
        ## the oldest undelivered records; overload drops the newest.
        self.queue.extendleft(reversed(requeue))

    async def drain(self):
        """Run by ConnectorManager.run_all; cancelled on shutdown with
        a final bounded flush."""
        try:
            while True:
                await self.flush_ready()
                await asyncio.sleep(DRAIN_INTERVAL)
        except asyncio.CancelledError:
            ## Bounded final flush: a hung connector send at shutdown must
            ## not make the drain task hang forever.
            try:
                await asyncio.wait_for(self.flush_ready(), timeout=5.0)
            except asyncio.TimeoutError:
                sys.stderr.write("log sink final flush timed out\n")
            raise
