"""Migration from the per-chat layout to one storage per bot (R13)."""

import os
import sys

import pytest
import zc.zlibstorage
import ZODB
import ZODB.FileStorage
import BTrees

import iacecil.controllers.persistence.chat_store as chat_store
from iacecil.controllers.persistence.chat_store import (
    chat_db_path,
    _chat_key,
    store_message,
)
from iacecil.models.envelope import Envelope

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import migrate_chat_stores  # noqa: E402


def _old_path(zodb_path, bot_id, connector, chat_id):
    return os.path.join(zodb_path, 'bots', bot_id, connector, 'chats',
        chat_id + '.fs')


def _write_old_store(path, records, native_ids=()):
    """Build a store in the pre-migration layout."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = ZODB.DB(zc.zlibstorage.ZlibStorage(
        ZODB.FileStorage.FileStorage(path)))
    try:
        with db.transaction() as connection:
            root = connection.root
            root.messages = BTrees.OOBTree.OOBTree()
            root.native_ids = BTrees.OOBTree.TreeSet()
            for msg_id, record in records.items():
                root.messages[msg_id] = record
            for native_id in native_ids:
                root.native_ids.add(native_id)
    finally:
        db.close()


def _chats(bot_id):
    db = chat_store._get_db(chat_db_path(bot_id))
    with db.transaction() as connection:
        return {key: [dict(r) for r in chat['messages'].values()]
            for key, chat in connection.root.chats.items()}


def test_migration_moves_every_record_and_native_id():
    zodb_path = chat_store.zodb_path
    _write_old_store(_old_path(zodb_path, 'mybot', 'discord', '42'),
        {'m1': {'connector': 'discord', 'text': 'one'}}, ['n1'])
    _write_old_store(_old_path(zodb_path, 'mybot', 'matrix', '42'),
        {'m2': {'connector': 'matrix', 'text': 'two'}})

    counts = migrate_chat_stores.migrate(zodb_path)

    assert counts['mybot'] == {'chats': 2, 'records': 2, 'native_ids': 1}
    chats = _chats('mybot')
    assert set(chats) == {_chat_key('discord', '42'),
        _chat_key('matrix', '42')}
    assert chats[_chat_key('discord', '42')][0]['text'] == 'one'
    assert chats[_chat_key('matrix', '42')][0]['text'] == 'two'


@pytest.mark.asyncio
async def test_migrated_native_ids_still_deduplicate():
    """A message already stored before the migration is not stored again."""
    zodb_path = chat_store.zodb_path
    _write_old_store(_old_path(zodb_path, 'mybot', 'discord', '42'),
        {'m1': {'connector': 'discord', 'text': 'one'}}, ['n1'])

    migrate_chat_stores.migrate(zodb_path)

    envelope = Envelope('discord', 'u', '42', 'one', native_message_id='n1')
    assert await store_message('mybot', envelope) is None


def test_dry_run_writes_nothing():
    zodb_path = chat_store.zodb_path
    _write_old_store(_old_path(zodb_path, 'mybot', 'discord', '42'),
        {'m1': {'connector': 'discord', 'text': 'one'}})

    counts = migrate_chat_stores.migrate(zodb_path, dry_run=True)

    assert counts['mybot']['records'] == 1
    assert not os.path.exists(chat_db_path('mybot'))


def test_legacy_telegram_layout_is_left_alone():
    """bots/<id>/chats/<chat>.fs has no connector component: legacy data
    read through zodb_orm, not the clean chat store."""
    zodb_path = chat_store.zodb_path
    legacy = os.path.join(zodb_path, 'bots', '1162758874', 'chats', '55.fs')
    _write_old_store(legacy, {'m1': {'text': 'legacy'}})

    found = list(migrate_chat_stores.find_old_stores(zodb_path))

    assert found == []
    assert os.path.exists(legacy)


def test_migration_is_rerunnable():
    zodb_path = chat_store.zodb_path
    _write_old_store(_old_path(zodb_path, 'mybot', 'discord', '42'),
        {'m1': {'connector': 'discord', 'text': 'one'}}, ['n1'])

    migrate_chat_stores.migrate(zodb_path)
    chat_store.close_all()
    migrate_chat_stores.migrate(zodb_path)

    assert len(_chats('mybot')[_chat_key('discord', '42')]) == 1


@pytest.mark.asyncio
async def test_migrated_key_matches_runtime_key_for_encoded_ids():
    """sanitize_component is not idempotent: it encodes '%' itself. The
    migration must join the on-disk names verbatim, or a matrix room
    ('!room:matrix.org' -> '%21room%3amatrix.org') would migrate to
    '%2521room%253amatrix.org' and never match new traffic."""
    zodb_path = chat_store.zodb_path
    room = '!room:matrix.org'
    runtime_key = _chat_key('matrix', room)
    on_disk_chat_id = runtime_key.split('/', 1)[1]
    _write_old_store(_old_path(zodb_path, 'mybot', 'matrix', on_disk_chat_id),
        {'m1': {'connector': 'matrix', 'text': 'old'}}, ['n1'])

    migrate_chat_stores.migrate(zodb_path)

    assert list(_chats('mybot')) == [runtime_key]
    ## New traffic for the same room lands in the migrated chat
    envelope = Envelope('matrix', 'u', room, 'new', native_message_id='n2')
    assert await store_message('mybot', envelope) is not None
    assert len(_chats('mybot')[runtime_key]) == 2
