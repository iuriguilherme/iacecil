"""A burst of concurrent writes must not lose records.

Found running the real bot: on connect, Matrix replays room history and
every message is dispatched at once. Each persists through its own
worker thread, the transactions collide on the same BTree buckets, and
five back-to-back retries with no pause all collide again — so records
were dropped with ConflictError. Consolidating every chat of a bot into
one storage makes this contention the normal case, not an edge.
"""

import asyncio

import pytest

import iacecil.controllers.persistence.chat_store as chat_store
import iacecil.controllers.persistence.neutral as neutral
from iacecil.models.envelope import Envelope

BURST = 60


@pytest.mark.asyncio
async def test_a_burst_of_neutral_records_all_land():
    envelopes = [Envelope('matrix', f'user{i % 7}', f'!room{i % 5}:m.org',
        f'message {i}') for i in range(BURST)]

    results = await asyncio.gather(
        *[neutral.persist_envelope(envelope) for envelope in envelopes],
        return_exceptions=True)

    failures = [r for r in results if isinstance(r, BaseException)]
    assert failures == []
    db = await neutral.get_messages_db()
    with db.transaction() as connection:
        assert len(connection.root.messages) == BURST
    assert not neutral._write_buffer


@pytest.mark.asyncio
async def test_a_burst_across_chats_of_one_bot_all_land():
    """Chats that used to live in separate files now share one BTree."""
    envelopes = [Envelope('matrix', 'u', f'!room{i % 12}:m.org',
        f'message {i}', native_message_id=f'$event{i}') for i in range(BURST)]

    results = await asyncio.gather(
        *[chat_store.store_message('mybot', envelope)
            for envelope in envelopes],
        return_exceptions=True)

    failures = [r for r in results if isinstance(r, BaseException)]
    assert failures == []
    db = chat_store._get_db(chat_store.chat_db_path('mybot'))
    with db.transaction() as connection:
        total = sum(len(chat['messages'])
            for chat in connection.root.chats.values())
    assert total == BURST


@pytest.mark.asyncio
async def test_a_burst_of_new_people_all_resolve():
    """Identity is the first write of every dispatch."""
    results = await asyncio.gather(
        *[neutral.resolve_person('matrix', f'@user{i}:m.org')
            for i in range(BURST)],
        return_exceptions=True)

    assert [r for r in results if isinstance(r, BaseException)] == []
    assert len(set(results)) == BURST
