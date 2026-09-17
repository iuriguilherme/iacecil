"""Shared storage through ZEO (R9, R10).

Slice 1 runs the connector unit and the web unit as separate processes.
FileStorage takes an exclusive lock, so the second process to open a
.fs crashes; both units connect to one ZEO server instead. These tests
run a real ZEO server rather than mocking the storage, because the lock
behavior is the whole point.
"""

import os

import pytest
import ZEO

import iacecil.controllers.persistence.chat_store as chat_store
import iacecil.controllers.persistence.neutral as neutral
import iacecil.controllers.persistence.storage as storage
from iacecil.controllers.persistence.chat_store import store_message
from iacecil.controllers.persistence.zodb_orm import get_db
from iacecil.models.envelope import Envelope


STORAGE_CONF = """
<filestorage people>
  path {base}/people.fs
</filestorage>
<filestorage messages>
  path {base}/messages.fs
</filestorage>
<filestorage chats_mybot>
  path {base}/chats_mybot.fs
</filestorage>
"""


@pytest.fixture
def zeo_server(tmp_path, monkeypatch):
    """Run a real ZEO server with the storage names slice 1 defines."""
    base = tmp_path / 'zeo'
    base.mkdir()
    address, stop = ZEO.server(
        storage_conf=STORAGE_CONF.format(base=base), threaded=True)
    monkeypatch.setattr(storage, 'zeo_address', address)
    try:
        yield address
    finally:
        monkeypatch.setattr(storage, 'zeo_address', None)
        stop()


def env(platform='loopback', chat='local_chat', text='hi', native_id=None):
    return Envelope(platform, 'user1', chat, text,
        native_message_id=native_id)


@pytest.mark.asyncio
async def test_neutral_dbs_connect_through_zeo(zeo_server):
    """Covers AE5: people and messages open without an exclusive lock."""
    people = await neutral.get_people_db()
    messages = await neutral.get_messages_db()

    assert 'ClientStorage' in type(people.storage.base).__name__
    assert 'ZlibStorage' in type(people.storage).__name__
    assert not os.path.exists(f"{neutral.zodb_path}/people.fs")
    assert people is not messages


@pytest.mark.asyncio
async def test_record_written_by_one_client_is_read_by_another(zeo_server):
    """Covers AE5: what the connector unit writes, the web unit reads."""
    person_id = await neutral.resolve_person('loopback', 'user1')

    reader = storage.open_db(f"{neutral.zodb_path}/people.fs", 'people')
    try:
        with reader.transaction() as connection:
            assert person_id in connection.root.people
    finally:
        reader.close()


@pytest.mark.asyncio
async def test_chat_store_writes_through_zeo(zeo_server):
    """The per-bot chats storage is served under its fixed name."""
    assert await store_message('mybot', env(text='one')) is not None
    assert await store_message('mybot', env(text='two')) is not None

    db = chat_store._get_db(chat_store._chat_db_path('mybot'),
        chat_store._storage_name('mybot'))
    with db.transaction() as connection:
        chat = connection.root.chats[chat_store._chat_key(
            'loopback', 'local_chat')]
        assert len(chat['messages']) == 2
    assert not os.path.exists(chat_store._chat_db_path('mybot'))


@pytest.mark.asyncio
async def test_new_chat_needs_no_new_storage(zeo_server):
    """R13: a chat that appears at runtime must land in the storage the
    server already serves — ZEO cannot open one its config never named."""
    for chat in ('c1', 'c2', 'c3'):
        assert await store_message('mybot', env(chat=chat)) is not None

    db = chat_store._get_db(chat_store._chat_db_path('mybot'),
        chat_store._storage_name('mybot'))
    with db.transaction() as connection:
        assert len(connection.root.chats) == 3


@pytest.mark.asyncio
async def test_falls_back_to_filestorage_without_zeo():
    """No zeo address configured: unchanged single-process behavior."""
    assert storage.zeo_address is None

    await neutral.resolve_person('loopback', 'user1')
    await store_message('mybot', env())

    assert os.path.exists(f"{neutral.zodb_path}/people.fs")
    assert os.path.exists(chat_store._chat_db_path('mybot'))
    people = await neutral.get_people_db()
    assert 'FileStorage' in type(people.storage.base).__name__


def test_unreachable_zeo_raises_connection_error_not_lock_error(
        tmp_path, monkeypatch):
    """A down ZEO server must fail as a connection problem, so the
    operator is not sent looking for a stale .lock file."""
    monkeypatch.setattr(storage, 'zeo_address', ('localhost', 1))
    with pytest.raises(Exception) as caught:
        storage.open_db(str(tmp_path / 'people.fs'), 'people', wait=False)
    assert 'lock' not in repr(caught.value).lower()


@pytest.mark.asyncio
async def test_legacy_get_db_stays_on_filestorage(tmp_path):
    """Legacy per-chat stores keep their own layout: consolidating them
    is deferred, so ZEO never names them as storages."""
    path = str(tmp_path / 'legacy' / '55.fs')
    db = await get_db(path)
    try:
        assert 'FileStorage' in type(db.storage.base).__name__
        assert os.path.exists(path)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_legacy_get_db_read_only_takes_no_lock(tmp_path):
    """The web unit reads legacy data while the connector unit holds the
    writer lock; a read-only open is what makes that safe."""
    path = str(tmp_path / 'legacy' / '55.fs')
    writer = await get_db(path)
    try:
        reader = await get_db(path, read_only=True)
        reader.close()
    finally:
        writer.close()


def test_configure_enables_and_disables_shared_storage():
    """Config, not code, decides whether storage is shared."""
    storage.configure({'enabled': True, 'address': ['localhost', 8100]})
    assert storage.zeo_address == ('localhost', 8100)

    storage.configure({'enabled': False, 'address': ['localhost', 8100]})
    assert storage.zeo_address is None

    storage.configure({'enabled': True, 'address': ()})
    assert storage.zeo_address is None

    storage.configure({})
    assert storage.zeo_address is None
