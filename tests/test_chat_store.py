import os
import pytest
from unittest.mock import AsyncMock

from iacecil.models.envelope import Envelope
import iacecil.controllers.persistence.chat_store as chat_store
from iacecil.controllers.persistence.chat_store import (
    _chat_db_path,
    store_message,
)


def env(platform='loopback', chat='local_chat', text='hi', native_id=None):
    return Envelope(platform, 'user1', chat, text,
        native_message_id=native_id)


async def _records(bot_id, envelope):
    path = _chat_db_path(bot_id, envelope.platform,
        envelope.conversation_ref)
    db = chat_store._get_db(path)
    with db.transaction() as conn:
        return [dict(r) for r in conn.root.messages.values()]


@pytest.mark.asyncio
async def test_same_chat_one_file_two_records(tmp_path):
    await store_message('mybot', env(text='one'))
    await store_message('mybot', env(text='two'))

    records = await _records('mybot', env())
    assert len(records) == 2
    assert {r['text'] for r in records} == {'one', 'two'}
    assert all(r['connector'] == 'loopback' for r in records)

    chats_dir = os.path.dirname(
        _chat_db_path('mybot', 'loopback', 'local_chat'))
    fs_files = [f for f in os.listdir(chats_dir) if f.endswith('.fs')]
    assert len(fs_files) == 1


@pytest.mark.asyncio
async def test_two_connectors_same_chat_id_distinct_paths():
    path_a = _chat_db_path('mybot', 'discord', '42')
    path_b = _chat_db_path('mybot', 'matrix', '42')
    assert path_a != path_b

    await store_message('mybot', env(platform='discord', chat='42'))
    await store_message('mybot', env(platform='matrix', chat='42'))
    assert os.path.exists(path_a)
    assert os.path.exists(path_b)


@pytest.mark.asyncio
async def test_duplicate_native_id_skipped():
    first = await store_message('mybot', env(native_id='n1'))
    second = await store_message('mybot', env(native_id='n1'))
    assert first is not None
    assert second is None
    assert len(await _records('mybot', env())) == 1


@pytest.mark.asyncio
async def test_records_without_native_ids_never_collide():
    """Outbound and loopback records carry no native id; both store."""
    assert await store_message('mybot', env(text='a')) is not None
    assert await store_message('mybot', env(text='b')) is not None
    assert len(await _records('mybot', env())) == 2


def test_traversal_components_stay_under_base():
    base = os.path.abspath(chat_store.zodb_path)
    path = _chat_db_path('mybot', '../../../etc', '../../escape')
    assert path.startswith(base + os.sep)


def test_containment_assert_fires_on_sanitizer_regression(monkeypatch):
    monkeypatch.setattr(chat_store, 'sanitize_component', lambda v: str(v))
    with pytest.raises(ValueError):
        _chat_db_path('mybot', '../../../etc', 'chat')


@pytest.mark.asyncio
async def test_lru_bound_closes_oldest(monkeypatch):
    monkeypatch.setattr(chat_store, 'MAX_OPEN_DBS', 2)
    for chat in ('c1', 'c2', 'c3', 'c4'):
        await store_message('mybot', env(chat=chat))
    assert len(chat_store._dbs) <= 2


@pytest.mark.asyncio
async def test_dispatch_writes_chat_store_for_all_platforms():
    """Inbound and outbound flow through the chat store keyed by the
    manager's bot_id; telegram inbound is stored too (reply ownership
    unchanged)."""
    from iacecil.connectors import ConnectorManager
    from plugins.echo import add_envelope_handlers

    manager = ConnectorManager({'loopback': {'enabled': True}},
        bot_id='mybot')
    await add_envelope_handlers(manager)
    manager.connectors['loopback'].send = AsyncMock()

    await manager.dispatch(Envelope('loopback', 'u', 'local_chat', 'ping'))

    records = await _records('mybot', env())
    directions = sorted(r['direction'] for r in records)
    assert directions == ['in', 'out']

    ## Telegram envelope: persisted (in) but never answered
    await manager.dispatch(Envelope('telegram', 'u', '777', '/start',
        native_message_id='m1'))
    tg_records = await _records('mybot',
        env(platform='telegram', chat='777'))
    assert len(tg_records) == 1
    assert tg_records[0]['direction'] == 'in'
