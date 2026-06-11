import pytest
from unittest.mock import AsyncMock, MagicMock
from iacecil.models.envelope import Envelope
from iacecil.controllers.aiogram_bot.callbacks import message_callback
from aiogram import Dispatcher
import logging

class FakeUser:
    def __init__(self):
        self.id = 123
        self.first_name = "First"
        self.last_name = "Last"

class FakeChat:
    def __init__(self):
        self.id = 456

class FakeMessage:
    def __init__(self, text="hello"):
        self.text = text
        self.from_user = FakeUser()
        self.chat = FakeChat()
        self.reply_to_message = None

@pytest.mark.asyncio
async def test_telegram_envelope_emission(monkeypatch):
    # Mock Dispatcher.get_current()
    dispatcher = MagicMock()
    manager = AsyncMock()
    dispatcher.manager = manager
    monkeypatch.setattr("aiogram.Dispatcher.get_current", lambda: dispatcher)
    
    # Mock furhat_logger and zodb_logger to avoid side effects
    monkeypatch.setattr("iacecil.controllers.aiogram_bot.callbacks.zodb_logger", AsyncMock())
    
    msg = FakeMessage("hello")
    await message_callback(msg)
    
    manager.dispatch.assert_called_once()
    env = manager.dispatch.call_args[0][0]
    
    assert env.platform == 'telegram'
    assert env.sender_ref == '123'
    assert env.conversation_ref == '456'
    assert env.text == 'hello'
    assert env.extra['first_name'] == 'First'
    assert env.extra['last_name'] == 'Last'
    assert env.raw == msg

@pytest.mark.asyncio
async def test_connector_send():
    from iacecil.connectors.telegram import Connector
    manager = MagicMock()
    conn = Connector(manager, {'token': 'fake'})
    conn.bot = AsyncMock()
    
    env = Envelope(
        platform='telegram',
        sender_ref='1',
        conversation_ref='chat1',
        text='reply text',
        reply_ref='10'
    )
    
    await conn.send(env)
    conn.bot.send_message.assert_called_once_with(
        chat_id='chat1',
        text='reply text',
        reply_to_message_id='10'
    )

@pytest.mark.asyncio
async def test_connector_send_chunks_at_telegram_limit():
    from iacecil.connectors.telegram import Connector
    manager = MagicMock()
    conn = Connector(manager, {'token': 'fake'})
    conn.bot = AsyncMock()

    env = Envelope(
        platform='telegram',
        sender_ref='1',
        conversation_ref='chat1',
        text='x' * 4500,
        reply_ref='10',
    )

    await conn.send(env)
    calls = conn.bot.send_message.call_args_list
    assert len(calls) == 2
    assert len(calls[0].kwargs['text']) == 4096
    assert len(calls[1].kwargs['text']) == 404
    ## Reply reference only on the first chunk
    assert calls[0].kwargs['reply_to_message_id'] == '10'
    assert calls[1].kwargs['reply_to_message_id'] is None
