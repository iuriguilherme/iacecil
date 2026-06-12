"""Connector conformance suite (R15).

The same contract checks run against every connector: declared chunk
limits honored on send, self-message guard, envelope construction from
a fake native event, and an echo round-trip through a real manager —
with telegram pinned as persist-only (strangler-fig arbitration rule,
docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md).

A new connector joins the net by adding one descriptor entry.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from iacecil.models.envelope import Envelope
from iacecil.connectors import ConnectorManager
from iacecil.connectors import discord as discord_mod
from iacecil.connectors import loopback as loopback_mod
from iacecil.connectors import matrix as matrix_mod
from iacecil.connectors import telegram as telegram_mod
from iacecil.connectors import xmpp as xmpp_mod

CONNECTOR_CLASSES = {
    'telegram': telegram_mod.Connector,
    'xmpp': xmpp_mod.Connector,
    'discord': discord_mod.Connector,
    'matrix': matrix_mod.Connector,
    'loopback': loopback_mod.Connector,
}

## The platform limits the plan pins; loopback prints to stdout and
## declares no limit (0 = exempt from chunking).
DECLARED_LIMITS = {
    'telegram': 4096,
    'xmpp': 4000,
    'discord': 2000,
    'matrix': 16000,
    'loopback': 0,
}

ACTIVATION_CONFIGS = {
    'telegram': {'token': 'x'},
    'xmpp': {'jid': 'bot@host', 'password': 'pw'},
    'discord': {'token': 'x'},
    'matrix': {'homeserver': 'https://h', 'token': 'x'},
    'loopback': {'enabled': True},
}


def make_send_capture(name):
    """Construct the connector with a fake client and return
    (connector, get_sent_chunks)."""
    manager = MagicMock()
    manager.bot_id = 'conformance'
    conn = CONNECTOR_CLASSES[name](manager, ACTIVATION_CONFIGS[name])
    if name == 'telegram':
        conn.bot = AsyncMock()
        return conn, lambda: [c.kwargs['text']
            for c in conn.bot.send_message.call_args_list]
    if name == 'xmpp':
        conn.bot = MagicMock()
        return conn, lambda: [c.kwargs['mbody']
            for c in conn.bot.send_message.call_args_list]
    if name == 'discord':
        channel = SimpleNamespace(id=1, send=AsyncMock())
        conn.client = MagicMock()
        conn.client.get_channel.return_value = channel
        return conn, lambda: [c.args[0]
            for c in channel.send.call_args_list]
    if name == 'matrix':
        conn.client = SimpleNamespace(room_send=AsyncMock())
        return conn, lambda: [c.kwargs['content']['body']
            for c in conn.client.room_send.call_args_list]
    raise ValueError(name)


@pytest.mark.parametrize('name', sorted(CONNECTOR_CLASSES))
def test_declared_limit_matches_contract(name):
    assert CONNECTOR_CLASSES[name].MAX_TEXT == DECLARED_LIMITS[name]


@pytest.mark.parametrize('name', sorted(CONNECTOR_CLASSES))
def test_activation_contract(name):
    cls = CONNECTOR_CLASSES[name]
    assert cls.is_active(ACTIVATION_CONFIGS[name]) is True
    assert cls.is_active({}) is False


CHUNKED = [n for n, limit in DECLARED_LIMITS.items() if limit]


@pytest.mark.asyncio
@pytest.mark.parametrize('name', sorted(CHUNKED))
async def test_send_at_exact_limit_single_chunk(name):
    conn, sent = make_send_capture(name)
    limit = DECLARED_LIMITS[name]
    await conn.send(Envelope(name, 'u', '1', 'x' * limit))
    assert sent() == ['x' * limit]


@pytest.mark.asyncio
@pytest.mark.parametrize('name', sorted(CHUNKED))
async def test_send_over_limit_chunks_in_order(name):
    conn, sent = make_send_capture(name)
    limit = DECLARED_LIMITS[name]
    text = 'a' * limit + 'b'
    await conn.send(Envelope(name, 'u', '1', text))
    chunks = sent()
    assert len(chunks) == 2
    assert all(len(chunk) <= limit for chunk in chunks)
    assert ''.join(chunks) == text


@pytest.mark.asyncio
async def test_self_message_guard_xmpp():
    bot = xmpp_mod.XMPPBot('bot@host', 'pw', MagicMock())
    bot.connector.manager = AsyncMock()
    msg = MagicMock()
    msg.__getitem__.side_effect = lambda k: {
        'type': 'chat', 'body': 'hi',
        'from': SimpleNamespace(full=bot.boundjid.full, bare='bot@host'),
        'id': 'x',
    }[k]
    await bot.message(msg)
    bot.connector.manager.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_self_message_guard_discord():
    manager = AsyncMock()
    conn = discord_mod.Connector(manager, {'token': 'x'})
    own = SimpleNamespace(
        author=SimpleNamespace(id=1, bot=True),
        content='hi', channel=SimpleNamespace(id=2), id=3,
        reference=None, created_at=None)
    await conn._on_message(own)
    manager.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_self_message_guard_matrix():
    manager = AsyncMock()
    conn = matrix_mod.Connector(manager,
        {'homeserver': 'h', 'token': 'x', 'user': '@bot:h'})
    conn.user_id = '@bot:h'
    own = SimpleNamespace(sender='@bot:h', body='hi', event_id='$1',
        server_timestamp=None)
    await conn._on_event('!r:h', own)
    manager.dispatch.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('name', sorted(CONNECTOR_CLASSES))
async def test_echo_round_trip_contract(name, monkeypatch):
    """One real manager per platform with echo registered: every
    non-telegram connector answers exactly once with the original text;
    telegram persists but never replies (arbitration pin)."""
    from plugins.echo import add_envelope_handlers
    import iacecil.controllers.persistence.neutral as neutral
    import iacecil.controllers.persistence.chat_store as chat_store

    monkeypatch.setattr(neutral, 'persist_envelope', AsyncMock())
    monkeypatch.setattr(neutral, 'resolve_person', AsyncMock())
    monkeypatch.setattr(chat_store, 'store_message', AsyncMock())

    manager = ConnectorManager({name: ACTIVATION_CONFIGS[name]},
        bot_id='conformance')
    assert name in manager.connectors
    manager.connectors[name].running = True
    await add_envelope_handlers(manager)
    manager.connectors[name].send = AsyncMock()

    await manager.dispatch(Envelope(name, 'user', 'chat', 'echo me'))

    if name == 'telegram':
        manager.connectors[name].send.assert_not_called()
    else:
        manager.connectors[name].send.assert_called_once()
        reply = manager.connectors[name].send.call_args[0][0]
        assert reply.text == 'echo me'
        assert reply.platform == name
        assert reply.conversation_ref == 'chat'
