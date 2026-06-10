import pytest
from unittest.mock import AsyncMock, MagicMock
from iacecil.models.envelope import Envelope

@pytest.mark.asyncio
async def test_xmpp_message():
    from iacecil.connectors.xmpp import XMPPBot
    manager = AsyncMock()
    connector = MagicMock()
    connector.manager = manager
    bot = XMPPBot('user@host', 'pw', connector)

    msg = MagicMock()
    def getitem(k):
        return {'type': 'chat', 'body': 'hello xmpp'}.get(k, MagicMock(bare='sender@host'))
    msg.__getitem__.side_effect = getitem

    await bot.message(msg)

    manager.dispatch.assert_called_once()
    env = manager.dispatch.call_args[0][0]
    assert env.platform == 'xmpp'
    assert env.sender_ref == 'sender@host'
    assert env.text == 'hello xmpp'

@pytest.mark.asyncio
async def test_xmpp_failure_marks_connector_down():
    from iacecil.connectors.xmpp import Connector, XMPPBot
    manager = MagicMock()
    conn = Connector(manager, {'jid': 'user@host', 'password': 'pw'})
    conn.bot = MagicMock()
    conn.running = True

    from types import SimpleNamespace
    fake_bot = SimpleNamespace(connector=conn)
    await XMPPBot.on_failure(fake_bot, None)

    assert conn.running is False
    with pytest.raises(ConnectionError):
        await conn.listen()

@pytest.mark.asyncio
async def test_xmpp_send():
    from iacecil.connectors.xmpp import Connector
    manager = MagicMock()
    conn = Connector(manager, {'jid': 'user@host', 'password': 'pw'})
    conn.bot = MagicMock()
    
    env = Envelope(
        platform='xmpp',
        sender_ref='sender@host',
        conversation_ref='sender@host',
        text='reply'*1000 # 5000 chars
    )
    
    await conn.send(env)
    assert conn.bot.send_message.call_count == 2
