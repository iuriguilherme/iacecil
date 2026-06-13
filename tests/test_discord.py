import pytest
import sys
import types
from unittest.mock import AsyncMock, MagicMock

from iacecil.models.envelope import Envelope
from iacecil.connectors.discord import Connector


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
async def test_guild_message_not_addressed_skipped():
    """Plain guild message, no mention and no command: not dispatched
    (firehose gate -- the bot must not answer every channel line)."""
    conn, manager = make_connector()
    await conn._on_message(FakeMessage(content="just chatting", guild=object()))
    manager.dispatch.assert_not_called()


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
