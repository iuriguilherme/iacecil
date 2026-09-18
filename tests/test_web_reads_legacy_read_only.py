"""The web unit reads legacy data without locking it.

Legacy per-chat stores stay on FileStorage: ZEO never names them. The
connector unit's plugins write them, and FileStorage lets only one
writer hold a file. If the web unit opened them read-write, an admin
page load would take the lock a plugin needs, or fail because a plugin
holds it — the same fight between processes that the split exists to
end. A read-only open takes no lock.
"""

import os

import BTrees
import pytest

import iacecil.controllers.persistence.zodb_orm as zodb_orm


def _legacy_path(bot_id='123456', chat_id='-100555'):
    return '{}/bots/{}/chats/{}.fs'.format(zodb_orm.zodb_path, bot_id, chat_id)


async def _write_legacy_messages(path, texts):
    """What a connector-side plugin does: open read-write and commit."""
    db = await zodb_orm.get_db(path, read_only=False)
    with db.transaction() as connection:
        root = connection.root
        root.messages = BTrees.IOBTree.IOBTree()
        for index, text in enumerate(texts):
            root.messages[index] = {'text': text, 'message_id': index}
    return db


@pytest.mark.asyncio
async def test_web_process_reads_while_a_plugin_holds_the_writer_lock():
    """The failure this exists to prevent: both processes open one file."""
    writer = await _write_legacy_messages(_legacy_path(), ['one', 'two'])
    try:
        zodb_orm.read_only = True
        total, messages = await zodb_orm.get_messages_list(
            bot_id='123456', chat_id='-100555', offset=0, limit=0)
    finally:
        writer.close()

    assert total == 2


@pytest.mark.asyncio
async def test_read_only_is_the_process_default_once_set():
    """Callers are shared between the web routes and connector plugins,
    so the switch is per process, not per call site."""
    zodb_orm.read_only = True
    path = _legacy_path()
    writer = await _write_legacy_messages(path, ['x'])
    try:
        db = await zodb_orm.get_db(path)
        try:
            assert db.storage.isReadOnly()
        finally:
            db.close()
    finally:
        writer.close()


@pytest.mark.asyncio
async def test_connector_process_still_opens_read_write():
    """Plugins write these stores; the default must not change for them."""
    path = _legacy_path()
    db = await zodb_orm.get_db(path)
    try:
        assert not db.storage.isReadOnly()
    finally:
        db.close()


@pytest.mark.asyncio
async def test_a_store_that_does_not_exist_reads_as_empty_not_an_error():
    """Read-only cannot create the file, and a web page must not 500
    because a bot has never stored anything."""
    zodb_orm.read_only = True

    assert await zodb_orm.get_db(_legacy_path(chat_id='never')) is None
    assert await zodb_orm.get_messages_list(
        bot_id='123456', chat_id='never', offset=0, limit=0) == (0, [{}])
    assert not os.path.exists(_legacy_path(chat_id='never'))


@pytest.mark.asyncio
async def test_a_read_leaves_the_store_unchanged():
    """Readers set an empty root when a store has none. In the web
    process that must not reach disk."""
    path = _legacy_path()
    writer = await zodb_orm.get_db(path)
    writer.close()
    size_before = os.path.getsize(path)

    zodb_orm.read_only = True
    await zodb_orm.get_messages_list(
        bot_id='123456', chat_id='-100555', offset=0, limit=0)

    assert os.path.getsize(path) == size_before


def test_web_unit_switches_its_process_to_read_only(monkeypatch):
    """The web unit is the process that must never write legacy data."""
    from iacecil.controllers._iacecil import production

    calls = []
    import iacecil.controllers.persistence.storage as storage
    monkeypatch.setattr(storage, 'configure_from_configs',
        lambda configs: calls.append(configs))

    production.configure_persistence({'mybot': object()})

    assert zodb_orm.read_only is True
    assert calls == [{'mybot': calls[0]['mybot']}]
