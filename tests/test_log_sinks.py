import asyncio
import logging
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from iacecil.controllers.log_sinks import (
    MAX_QUEUE,
    ConnectorLogHandler,
)


def make_manager(platforms=('matrix',), running=True):
    manager = SimpleNamespace()
    manager.connectors = {
        name: SimpleNamespace(running=running) for name in platforms}
    manager.send = AsyncMock(return_value=True)
    return manager


def make_logger(name='iacecil.test', handler=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if handler is not None:
        logger.addHandler(handler)
    return logger


@pytest.fixture
def cleanup_loggers():
    yield
    for name in list(logging.Logger.manager.loggerDict):
        if name.startswith('iacecil.test'):
            logging.getLogger(name).handlers.clear()


@pytest.mark.asyncio
async def test_matching_record_delivered(cleanup_loggers):
    manager = make_manager()
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!ops:x',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    log.error("something broke")
    await handler.flush_ready()

    manager.send.assert_called_once()
    env = manager.send.call_args[0][0]
    assert env.platform == 'matrix'
    assert env.conversation_ref == '!ops:x'
    assert "something broke" in env.text
    assert "[ERROR]" in env.text


@pytest.mark.asyncio
async def test_below_level_not_delivered(cleanup_loggers):
    manager = make_manager()
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!ops:x',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    log.warning("just a warning")
    await handler.flush_ready()
    manager.send.assert_not_called()


@pytest.mark.asyncio
async def test_logger_prefix_routes_subsystem(cleanup_loggers):
    """The acceptance scenario: xmpp errors to a private telegram
    group; unrelated loggers filtered out of that sink."""
    manager = make_manager(platforms=('telegram',))
    handler = ConnectorLogHandler(manager, [
        {'platform': 'telegram', 'conversation_ref': '-100777',
         'level': 'ERROR', 'logger': 'iacecil.connectors.xmpp'},
    ])
    xmpp_log = make_logger('iacecil.connectors.xmpp', handler)
    other_log = make_logger('iacecil.test.other', handler)

    xmpp_log.error("XMPP session died")
    other_log.error("unrelated")
    await handler.flush_ready()

    manager.send.assert_called_once()
    env = manager.send.call_args[0][0]
    assert env.platform == 'telegram'
    assert env.conversation_ref == '-100777'
    assert "XMPP session died" in env.text
    xmpp_log.handlers.clear()


@pytest.mark.asyncio
async def test_two_sinks_both_receive(cleanup_loggers):
    manager = make_manager(platforms=('matrix', 'xmpp'))
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!a:x',
         'level': 'ERROR'},
        {'platform': 'xmpp', 'conversation_ref': 'ops@host',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    log.error("boom")
    await handler.flush_ready()

    platforms = [c.args[0].platform for c in manager.send.call_args_list]
    assert sorted(platforms) == ['matrix', 'xmpp']


@pytest.mark.asyncio
async def test_traceback_capped_unless_verbose(cleanup_loggers):
    manager = make_manager(platforms=('matrix', 'xmpp'))
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!a:x',
         'level': 'ERROR'},
        {'platform': 'xmpp', 'conversation_ref': 'ops@host',
         'level': 'ERROR', 'verbose': True},
    ])
    log = make_logger(handler=handler)

    try:
        ## Deep stack for a long traceback
        def recurse(n):
            if n == 0:
                raise ValueError("deep failure " + "x" * 600)
            return recurse(n - 1)
        recurse(30)
    except ValueError:
        log.exception("caught")
    await handler.flush_ready()

    texts = {c.args[0].platform: c.args[0].text
        for c in manager.send.call_args_list}
    assert '...[truncated]' in texts['matrix']
    assert '...[truncated]' not in texts['xmpp']
    assert len(texts['xmpp']) > len(texts['matrix'])


@pytest.mark.asyncio
async def test_delivery_failure_no_recursion(cleanup_loggers):
    """A send that itself logs must not re-enter the handler; later
    records still deliver."""
    manager = make_manager()
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!a:x',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    async def send_that_logs(envelope):
        ## Simulates connector internals logging during delivery
        log.error("error during delivery")
        return False

    manager.send = AsyncMock(side_effect=send_that_logs)

    log.error("first")
    await handler.flush_ready()
    assert manager.send.call_count == 1
    ## The in-delivery record was dropped, not queued
    assert len(handler.queue) == 0

    log.error("second")
    await handler.flush_ready()
    assert manager.send.call_count == 2


@pytest.mark.asyncio
async def test_boot_records_buffered_until_connected(cleanup_loggers):
    manager = make_manager(running=False)
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!a:x',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    log.error("emitted before connect")
    await handler.flush_ready()
    manager.send.assert_not_called()
    assert len(handler.queue) == 1

    manager.connectors['matrix'].running = True
    await handler.flush_ready()
    manager.send.assert_called_once()
    assert "emitted before connect" in manager.send.call_args[0][0].text


@pytest.mark.asyncio
async def test_burst_bounded_queue_drops_oldest(cleanup_loggers):
    manager = make_manager(running=False)
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!a:x',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    for i in range(MAX_QUEUE + 500):
        log.error(f"record {i}")
    assert len(handler.queue) == MAX_QUEUE
    ## Oldest dropped: the first queued record is no longer record 0
    assert "record 0" not in handler.queue[0][1]


@pytest.mark.asyncio
async def test_requeued_boot_records_survive_midflush_refill(cleanup_loggers):
    """Records held for a not-yet-connected sink must not be evicted
    when other tasks refill the bounded deque during the flush's
    awaits — requeue prepends instead of appending."""
    import iacecil.controllers.log_sinks as log_sinks_mod
    manager = make_manager(platforms=('slow', 'fast'))
    manager.connectors['slow'].running = False
    handler = ConnectorLogHandler(manager, [
        {'platform': 'slow', 'conversation_ref': 's', 'level': 'ERROR',
         'logger': 'iacecil.test.slow'},
        {'platform': 'fast', 'conversation_ref': 'f', 'level': 'ERROR',
         'logger': 'iacecil.test.fast'},
    ])
    ## Tiny bound so a mid-flush refill hits capacity
    handler.queue = type(handler.queue)(maxlen=3)
    slow_log = make_logger('iacecil.test.slow', handler)
    fast_log = make_logger('iacecil.test.fast', handler)

    slow_log.error("boot record for slow sink")
    fast_log.error("fast one")

    refilled = False

    async def send_and_refill(envelope):
        ## Models another task emitting during the delivery await
        nonlocal refilled
        if not refilled:
            refilled = True
            ## New records also waiting on the slow sink: total held
            ## records exceed the bound, and the oldest must win
            handler.queue.append((handler.sinks[0], "[ERROR] refill a"))
            handler.queue.append((handler.sinks[0], "[ERROR] refill b"))
            handler.queue.append((handler.sinks[0], "[ERROR] refill c"))
        return True

    manager.send = AsyncMock(side_effect=send_and_refill)
    await handler.flush_ready()

    ## The boot record sits at the FRONT of the queue, not evicted
    assert "boot record for slow sink" in handler.queue[0][1]
    slow_log.handlers.clear()
    fast_log.handlers.clear()


@pytest.mark.asyncio
async def test_absent_platform_dropped_via_manager_send(cleanup_loggers):
    """A sink naming a platform with no connector routes through
    manager.send, which warns once and drops."""
    manager = make_manager(platforms=())
    handler = ConnectorLogHandler(manager, [
        {'platform': 'discord', 'conversation_ref': '1',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    log.error("nowhere to go")
    await handler.flush_ready()
    manager.send.assert_called_once()
    assert len(handler.queue) == 0


@pytest.mark.asyncio
async def test_drain_cancel_flushes(cleanup_loggers):
    manager = make_manager()
    handler = ConnectorLogHandler(manager, [
        {'platform': 'matrix', 'conversation_ref': '!a:x',
         'level': 'ERROR'},
    ])
    log = make_logger(handler=handler)

    task = asyncio.get_event_loop().create_task(handler.drain())
    await asyncio.sleep(0)
    log.error("emitted just before shutdown")
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    manager.send.assert_called_once()
