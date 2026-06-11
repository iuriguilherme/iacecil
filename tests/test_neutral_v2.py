import pytest
from unittest.mock import AsyncMock

from iacecil.models.envelope import Envelope
from iacecil.connectors import ConnectorManager
import iacecil.controllers.persistence.neutral as neutral


async def _all_records():
    db = await neutral.get_messages_db()
    with db.transaction() as conn:
        if not hasattr(conn.root, 'messages'):
            return []
        return [dict(r) for r in conn.root.messages.values()]


@pytest.mark.asyncio
async def test_inbound_record_carries_v2_fields():
    env = Envelope('xmpp', 's@h', 's@h', 'hello',
        native_message_id='abc123', timestamp=1700000000.0)
    await neutral.persist_envelope(env, direction='in')

    records = await _all_records()
    assert len(records) == 1
    rec = records[0]
    assert rec['direction'] == 'in'
    assert rec['native_message_id'] == 'abc123'
    assert rec['timestamp'] == 1700000000.0


@pytest.mark.asyncio
async def test_defaults_when_platform_supplies_nothing():
    env = Envelope('loopback', 'local_user', 'local_chat', 'hi')
    await neutral.persist_envelope(env)

    rec = (await _all_records())[0]
    assert rec['direction'] == 'in'
    assert rec['native_message_id'] is None
    assert rec['timestamp'] is not None  # filled with "now"


@pytest.mark.asyncio
async def test_old_shape_record_readable():
    """Records written before v2 lack the new keys; readers tolerate."""
    db = await neutral.get_messages_db()
    with db.transaction() as conn:
        import BTrees
        if not hasattr(conn.root, 'messages'):
            conn.root.messages = BTrees.OOBTree.OOBTree()
        conn.root.messages['legacy'] = {
            'platform': 'telegram', 'sender_ref': '1',
            'conversation_ref': '2', 'text': 'old', 'reply_ref': None,
            'tags': [],
        }
    records = await _all_records()
    assert records[0].get('direction') is None
    assert records[0].get('timestamp') is None


@pytest.mark.asyncio
async def test_echo_round_trip_persists_in_and_out():
    """The round's stated goal: the echo exchange is verifiable from
    storage — one 'in' and one 'out' record."""
    manager = ConnectorManager({'loopback': {'enabled': True}})
    from plugins.echo import add_envelope_handlers
    await add_envelope_handlers(manager)
    manager.connectors['loopback'].send = AsyncMock()

    await manager.dispatch(Envelope('loopback', 'u', 'c', 'echo me'))

    records = await _all_records()
    directions = sorted(r['direction'] for r in records)
    assert directions == ['in', 'out']
    out = [r for r in records if r['direction'] == 'out'][0]
    assert out['text'] == 'echo me'
    assert out['conversation_ref'] == 'c'
