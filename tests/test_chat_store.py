import os
import pytest
from unittest.mock import AsyncMock

from iacecil.models.envelope import Envelope
import iacecil.controllers.persistence.chat_store as chat_store
from iacecil.controllers.persistence.chat_store import (
    _chat_db_path,
    _chat_key,
    store_message,
)


def env(platform='loopback', chat='local_chat', text='hi', native_id=None):
    return Envelope(platform, 'user1', chat, text,
        native_message_id=native_id)


async def _records(bot_id, envelope):
    db = chat_store._get_db(_chat_db_path(bot_id))
    key = _chat_key(envelope.platform, envelope.conversation_ref)
    with db.transaction() as conn:
        chat = conn.root.chats.get(key)
        if chat is None:
            return []
        return [dict(r) for r in chat['messages'].values()]


@pytest.mark.asyncio
async def test_same_chat_one_file_two_records(tmp_path):
    await store_message('mybot', env(text='one'))
    await store_message('mybot', env(text='two'))

    records = await _records('mybot', env())
    assert len(records) == 2
    assert {r['text'] for r in records} == {'one', 'two'}
    assert all(r['connector'] == 'loopback' for r in records)

    bots_dir = os.path.dirname(os.path.dirname(_chat_db_path('mybot')))
    fs_files = [f for f in os.listdir(os.path.join(bots_dir, 'mybot'))
        if f.endswith('.fs')]
    assert fs_files == ['chats.fs']


@pytest.mark.asyncio
async def test_two_connectors_same_chat_id_distinct_keys():
    assert _chat_key('discord', '42') != _chat_key('matrix', '42')

    await store_message('mybot',
        env(platform='discord', chat='42', text='d'))
    await store_message('mybot',
        env(platform='matrix', chat='42', text='m'))

    discord = await _records('mybot', env(platform='discord', chat='42'))
    matrix = await _records('mybot', env(platform='matrix', chat='42'))
    assert [r['text'] for r in discord] == ['d']
    assert [r['text'] for r in matrix] == ['m']
    ## One storage for the bot, both chats inside it
    assert os.path.exists(_chat_db_path('mybot'))


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


@pytest.mark.asyncio
async def test_concurrent_same_chat_writes_no_collision():
    """store_message runs its body via asyncio.to_thread, so concurrent
    writes to the same (new) chat reach _get_db from multiple worker
    threads at once. The LRU lock must keep them from double-opening the
    same .fs (FileStorage .lock collision), root pre-init avoids the
    unresolvable root-attribute race, and conflict-retry lets the parallel
    inserts all land in one chat container."""
    import asyncio
    results = await asyncio.gather(*[
        store_message('mybot', env(text=f'm{i}', native_id=f'c{i}'))
        for i in range(3)
    ])
    assert all(r is not None for r in results)
    assert len(await _records('mybot', env())) == 3

    bots_dir = os.path.dirname(os.path.dirname(_chat_db_path('mybot')))
    fs_files = [f for f in os.listdir(os.path.join(bots_dir, 'mybot'))
        if f.endswith('.fs')]
    assert fs_files == ['chats.fs']


def test_traversal_components_stay_under_base():
    base = os.path.abspath(chat_store.zodb_path)
    assert _chat_db_path('../../../etc').startswith(base + os.sep)


def test_traversal_components_stay_inside_chat_key():
    key = _chat_key('../../../etc', '../../escape')
    assert '/' not in key.replace('/', '', 1)


def test_containment_assert_fires_on_sanitizer_regression(monkeypatch):
    monkeypatch.setattr(chat_store, 'sanitize_component', lambda v: str(v))
    with pytest.raises(ValueError):
        _chat_db_path('../../../etc')


@pytest.mark.asyncio
async def test_lru_bound_closes_oldest(monkeypatch):
    """The LRU now bounds open bots, not open chats."""
    monkeypatch.setattr(chat_store, 'MAX_OPEN_DBS', 2)
    for bot in ('b1', 'b2', 'b3', 'b4'):
        await store_message(bot, env())
    assert len(chat_store._dbs) <= 2


@pytest.mark.asyncio
async def test_many_chats_share_one_storage():
    """R13: a new chat must never need a new storage — that is what a
    ZEO server, whose storage names are fixed at startup, cannot serve."""
    for chat in ('c1', 'c2', 'c3', 'c4'):
        await store_message('mybot', env(chat=chat))

    assert len(chat_store._dbs) == 1
    db = chat_store._get_db(_chat_db_path('mybot'))
    with db.transaction() as conn:
        assert len(conn.root.chats) == 4


@pytest.mark.asyncio
async def test_dedupe_is_per_chat_not_per_bot():
    """The same native id in two chats is two distinct messages."""
    assert await store_message('mybot',
        env(chat='c1', native_id='n1')) is not None
    assert await store_message('mybot',
        env(chat='c2', native_id='n1')) is not None
    assert await store_message('mybot',
        env(chat='c1', native_id='n1')) is None
    assert len(await _records('mybot', env(chat='c1'))) == 1
    assert len(await _records('mybot', env(chat='c2'))) == 1


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
    manager.connectors['loopback'].running = True
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
