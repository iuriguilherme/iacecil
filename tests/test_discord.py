import pytest
import sys
import types
from unittest.mock import AsyncMock, MagicMock

from iacecil.models.envelope import Envelope
from iacecil.connectors.discord import Connector
from iacecil.connectors import ConnectorManager
from plugins.echo import add_envelope_handlers
import iacecil.controllers.persistence.neutral as neutral


async def _all_records():
    db = await neutral.get_messages_db()
    with db.transaction() as conn:
        if not hasattr(conn.root, 'messages'):
            return []
        return [dict(r) for r in conn.root.messages.values()]


def _wired_manager():
    """A real ConnectorManager with the echo default handler and a stubbed
    Discord send — so dispatch runs persistence + is_authorized gating for
    real, but no live gateway is touched."""
    manager = ConnectorManager({'discord': {'token': 'fake', 'channels': ['222']}})
    conn = manager.connectors['discord']
    conn.running = True
    conn.send = AsyncMock()
    return manager, conn


class FakeAuthor:
    def __init__(self, id=111, bot=False):
        self.id = id
        self.bot = bot


class FakeChannel:
    def __init__(self, id=222):
        self.id = id
        self.send = AsyncMock()


class FakeMessage:
    def __init__(self, content="hello", author=None, message_id=333,
            guild=None, mentions=None):
        self.content = content
        self.author = author or FakeAuthor()
        self.channel = FakeChannel()
        self.id = message_id
        self.reference = None
        self.created_at = None
        ## guild=None ⇒ DM (always addressed to the bot).
        self.guild = guild
        self.mentions = mentions or []


def make_connector():
    manager = AsyncMock()
    return Connector(manager, {'token': 'fake'}), manager


@pytest.mark.asyncio
async def test_inbound_message_becomes_envelope():
    conn, manager = make_connector()
    msg = FakeMessage("hello discord")

    await conn._on_message(msg)

    manager.dispatch.assert_called_once()
    env = manager.dispatch.call_args[0][0]
    assert env.platform == 'discord'
    assert env.sender_ref == '111'
    assert env.conversation_ref == '222'
    assert env.text == 'hello discord'
    assert env.native_message_id == '333'


@pytest.mark.asyncio
async def test_bot_authors_skipped():
    """Self and any other bot: no dispatch (echo-loop guard)."""
    conn, manager = make_connector()
    await conn._on_message(FakeMessage(author=FakeAuthor(bot=True)))
    manager.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_guild_message_dispatched_always():
    """All messages are dispatched for persistence (no more firehose gate
    in the connector). gating happens at dispatch/plugin layer."""
    conn, manager = make_connector()
    await conn._on_message(FakeMessage(content="just chatting", guild=object()))
    manager.dispatch.assert_called_once()


def test_is_authorized_dm():
    conn, _ = make_connector()
    msg = FakeMessage(guild=None)
    env = Envelope(platform='discord', sender_ref='111', conversation_ref='444', text='hi', raw=msg)
    assert conn.is_authorized(env) is True


def test_is_authorized_guild_allowed():
    manager = AsyncMock()
    conn = Connector(manager, {'token': 'fake', 'channels': ['222', '333']})
    env = Envelope(platform='discord', sender_ref='111', conversation_ref='222', text='hi')
    assert conn.is_authorized(env) is True


def test_is_authorized_guild_denied():
    manager = AsyncMock()
    conn = Connector(manager, {'token': 'fake', 'channels': ['222']})
    env = Envelope(platform='discord', sender_ref='111', conversation_ref='444', text='hi')
    assert conn.is_authorized(env) is False


@pytest.mark.asyncio
async def test_guild_command_dispatched():
    conn, manager = make_connector()
    await conn._on_message(FakeMessage(content="/start", guild=object()))
    manager.dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_guild_mention_dispatched():
    conn, manager = make_connector()
    me = object()
    conn.client = MagicMock()
    conn.client.user = me
    await conn._on_message(
        FakeMessage(content="hey bot", guild=object(), mentions=[me]))
    manager.dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_dm_dispatched():
    """No guild ⇒ DM ⇒ always addressed."""
    conn, manager = make_connector()
    await conn._on_message(FakeMessage(content="hi in dm", guild=None))
    manager.dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_send_chunks_at_discord_limit():
    conn, _ = make_connector()
    channel = FakeChannel()
    conn.client = MagicMock()
    conn.client.get_channel.return_value = channel

    env = Envelope('discord', '1', '222', 'x' * 4500)
    await conn.send(env)

    calls = channel.send.call_args_list
    assert len(calls) == 3
    assert all(len(c.args[0]) <= 2000 for c in calls)
    assert ''.join(c.args[0] for c in calls) == 'x' * 4500


@pytest.mark.asyncio
async def test_send_carries_reply_reference(monkeypatch):
    fake_discord = types.ModuleType("discord")
    fake_discord.MessageReference = MagicMock(return_value='REF')
    monkeypatch.setitem(sys.modules, "discord", fake_discord)

    conn, _ = make_connector()
    channel = FakeChannel()
    conn.client = MagicMock()
    conn.client.get_channel.return_value = channel

    env = Envelope('discord', '1', '222', 'short reply', reply_ref='999')
    await conn.send(env)

    channel.send.assert_called_once()
    assert channel.send.call_args.kwargs['reference'] == 'REF'
    fake_discord.MessageReference.assert_called_once_with(
        message_id=999, channel_id=222, fail_if_not_exists=False)


@pytest.mark.asyncio
async def test_empty_content_warns_once(caplog):
    import logging
    conn, manager = make_connector()
    with caplog.at_level(logging.WARNING):
        await conn._on_message(FakeMessage(content=""))
        await conn._on_message(FakeMessage(content=""))
    hints = [r for r in caplog.records
        if "Message Content intent" in r.getMessage()]
    assert len(hints) == 1
    ## Still dispatched — persistence sees the (empty) message
    assert manager.dispatch.call_count == 2


@pytest.mark.asyncio
async def test_listen_without_client_raises():
    conn, _ = make_connector()
    with pytest.raises(ValueError):
        await conn.listen()


def test_activation_rule():
    assert Connector.is_active({'token': 'x'}) is True
    assert Connector.is_active({'token': ''}) is False
    assert Connector.is_active({}) is False


@pytest.mark.asyncio
async def test_send_times_out_and_drops(caplog):
    """A hung Discord API call must not block the event loop forever; the
    send times out, logs, and drops the reply."""
    import asyncio
    import logging
    from iacecil.connectors.discord import Connector

    conn = Connector(MagicMock(), {'token': 'x'})
    conn.SEND_TIMEOUT = 0.01

    channel = MagicMock()

    async def slow_send(*a, **k):
        await asyncio.sleep(1)

    channel.send = slow_send
    conn.client = MagicMock()
    conn.client.get_channel.return_value = channel
    conn.running = True

    with caplog.at_level(logging.ERROR):
        await conn.send(Envelope('discord', 'u', '123', 'hi'))
    assert any('timed out' in r.getMessage() for r in caplog.records)


## ---------------------------------------------------------------------------
## Integration: full on_message -> dispatch -> persistence -> echo/auth gating
## through a REAL ConnectorManager (not a mocked dispatch). Proves the prompt's
## observation-vs-response split: every message is persisted, but only DMs and
## authorized channels get an echo reply.
## ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dm_echo_round_trip_persists():
    """DM: persisted in+out, and the echo reply is actually sent."""
    manager, conn = _wired_manager()
    await add_envelope_handlers(manager)

    await conn._on_message(FakeMessage(content="echo me", guild=None))

    conn.send.assert_called_once()
    records = await _all_records()
    assert sorted(r['direction'] for r in records) == ['in', 'out']
    out = [r for r in records if r['direction'] == 'out'][0]
    assert out['text'] == 'echo me'


@pytest.mark.asyncio
async def test_authorized_guild_echo_round_trip_persists():
    """Authorized guild channel (222 in channels): persisted in+out, reply sent."""
    manager, conn = _wired_manager()
    await add_envelope_handlers(manager)

    await conn._on_message(FakeMessage(content="hi guild", guild=object()))

    conn.send.assert_called_once()
    records = await _all_records()
    assert sorted(r['direction'] for r in records) == ['in', 'out']


@pytest.mark.asyncio
async def test_unauthorized_guild_persists_but_no_reply():
    """Unauthorized guild channel: observed and persisted, but NO echo reply."""
    manager, conn = _wired_manager()
    await add_envelope_handlers(manager)

    msg = FakeMessage(content="unauth", guild=object())
    msg.channel = FakeChannel(999)  # not in channels=['222']
    await conn._on_message(msg)

    conn.send.assert_not_called()
    records = await _all_records()
    assert [r['direction'] for r in records] == ['in']
    assert records[0]['text'] == 'unauth'
