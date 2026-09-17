"""Neutral records survive a ZEO outage in memory (R11, AE6).

Connectors must keep answering while shared storage is unreachable. A
failed write goes to a bounded in-memory buffer and is flushed on the
next successful write. The bound is the accepted loss: if the connector
process itself dies mid-outage, buffered records are gone.
"""

import socket

import pytest
import ZEO

import iacecil.controllers.persistence.neutral as neutral
import iacecil.controllers.persistence.storage as storage
from iacecil.models.envelope import Envelope


def env(text='hi', native_id=None):
    return Envelope('loopback', 'user1', 'local_chat', text,
        native_message_id=native_id)


class DisconnectedDB:
    """Stands in for a DB whose ZEO server went away."""

    def __init__(self, error=None):
        self.error = error or ConnectionError('server went away')

    def transaction(self):
        raise self.error


class Outage:
    """Switchable storage: down until ``restore()`` is called.

    Never use ``monkeypatch.undo()`` to end an outage — it also undoes
    the autouse isolation fixture in conftest, and the test then writes
    into the real instance/zodb store.
    """

    def __init__(self, monkeypatch):
        self.down = True
        monkeypatch.setattr(neutral, 'get_messages_db', self._get_db)

    async def _get_db(self, *args, **kwargs):
        if self.down:
            return DisconnectedDB()
        return await self.real_db()

    async def real_db(self):
        return await _open_messages_db()

    def restore(self):
        self.down = False


@pytest.fixture(autouse=True)
def empty_buffer():
    neutral._write_buffer.clear()
    yield
    neutral._write_buffer.clear()


@pytest.mark.asyncio
async def test_write_during_outage_is_buffered_not_raised(monkeypatch):
    """A connector must not stop replying because storage blipped."""
    Outage(monkeypatch)

    msg_id = await neutral.persist_envelope(env(text='during outage'))

    assert msg_id is not None
    assert len(neutral._write_buffer) == 1


@pytest.mark.asyncio
async def test_buffered_records_flush_on_next_successful_write(monkeypatch):
    """Covers AE6: reconnect flushes everything buffered, in order."""
    outage = Outage(monkeypatch)
    buffered = [await neutral.persist_envelope(env(text=f'm{i}'))
        for i in range(3)]
    assert len(neutral._write_buffer) == 3

    outage.restore()
    recovered = await neutral.persist_envelope(env(text='after'))

    assert not neutral._write_buffer
    db = await _open_messages_db()
    with db.transaction() as connection:
        stored = dict(connection.root.messages)
    assert [stored[i]['text'] for i in buffered] == ['m0', 'm1', 'm2']
    assert stored[recovered]['text'] == 'after'


@pytest.mark.asyncio
async def test_buffer_is_bounded_and_drops_oldest(monkeypatch):
    """The bound is what keeps a long outage from exhausting memory."""
    monkeypatch.setattr(neutral, '_write_buffer',
        _new_buffer(maxlen=2))
    Outage(monkeypatch)

    for text in ('oldest', 'middle', 'newest'):
        await neutral.persist_envelope(env(text=text))

    assert [record['text'] for _, record in neutral._write_buffer] == [
        'middle', 'newest']


@pytest.mark.asyncio
async def test_disconnect_mid_flush_keeps_the_rest_buffered(monkeypatch):
    """A flush that fails halfway must not drop what it had not written."""
    outage = Outage(monkeypatch)
    for text in ('m0', 'm1', 'm2'):
        await neutral.persist_envelope(env(text=text))

    outage.restore()
    real_db = await _open_messages_db()
    calls = {'n': 0}
    original = neutral._write_message_record

    def fail_on_second(db, msg_id, record):
        calls['n'] += 1
        if calls['n'] == 2:
            raise ConnectionError('server went away again')
        return original(db, msg_id, record)

    monkeypatch.setattr(neutral, '_write_message_record', fail_on_second)
    await neutral.persist_envelope(env(text='after'))

    ## First buffered record written; the rest stay queued and the new
    ## record queues behind them rather than overtaking them
    assert [record['text'] for _, record in neutral._write_buffer] == [
        'm1', 'm2', 'after']
    with real_db.transaction() as connection:
        assert [r['text'] for r in connection.root.messages.values()] == ['m0']


@pytest.mark.asyncio
async def test_normal_write_does_not_touch_the_buffer():
    """With storage up, nothing is buffered and nothing is flushed."""
    msg_id = await neutral.persist_envelope(env(text='fine'))

    assert not neutral._write_buffer
    db = await _open_messages_db()
    with db.transaction() as connection:
        assert connection.root.messages[msg_id]['text'] == 'fine'


@pytest.mark.asyncio
async def test_records_survive_a_real_zeo_restart(tmp_path, monkeypatch):
    """Covers AE6 end to end: the ZEO unit dies, the connector keeps
    writing into the buffer, the supervisor restarts ZEO, and the
    buffered records land in the storage."""
    base = tmp_path / 'zeo'
    base.mkdir()
    port = _free_port()
    conf = f"<filestorage messages>\n  path {base}/messages.fs\n</filestorage>\n"
    address, stop = ZEO.server(
        storage_conf=conf, port=port, threaded=True)
    monkeypatch.setattr(storage, 'zeo_address', address)

    before = await neutral.persist_envelope(env(text='before outage'))
    stop()
    neutral._messages_db = None

    during = await neutral.persist_envelope(env(text='during outage'))
    assert len(neutral._write_buffer) == 1

    address, stop = ZEO.server(
        storage_conf=conf, port=port, threaded=True)
    try:
        neutral._messages_db = None
        after = await neutral.persist_envelope(env(text='after restart'))

        assert not neutral._write_buffer
        db = await neutral.get_messages_db()
        with db.transaction() as connection:
            stored = dict(connection.root.messages)
        assert stored[before]['text'] == 'before outage'
        assert stored[during]['text'] == 'during outage'
        assert stored[after]['text'] == 'after restart'
    finally:
        stop()


def _new_buffer(maxlen):
    import collections
    return collections.deque(maxlen=maxlen)


async def _open_messages_db():
    """Open the isolated store directly, without going through the
    patched get_messages_db."""
    if neutral._messages_db is None:
        await _init_messages_db()
    return neutral._messages_db


async def _init_messages_db():
    import iacecil.controllers.persistence.storage as storage_module
    import BTrees
    neutral._messages_db = storage_module.open_db(
        f"{neutral.zodb_path}/messages.fs", 'messages')
    with neutral._messages_db.transaction() as connection:
        if not hasattr(connection.root, 'messages'):
            connection.root.messages = BTrees.OOBTree.OOBTree()


def _free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]
