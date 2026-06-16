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
async def test_xmpp_groupchat_message():
    from iacecil.connectors.xmpp import XMPPBot
    manager = AsyncMock()
    connector = MagicMock()
    connector.manager = manager
    bot = XMPPBot('user@host', 'pw', connector)
    # mock full jid string
    bot.boundjid.full = 'user@host/res'
    bot.boundjid.user = 'user'

    msg = MagicMock()
    def getitem(k):
        if k == 'type': return 'groupchat'
        if k == 'body': return 'hello muc'
        if k == 'from': 
            m = MagicMock()
            m.bare = 'room@conf.host'
            m.resource = 'other_user'
            m.full = 'room@conf.host/other_user'
            return m
        return None
    msg.__getitem__.side_effect = getitem

    await bot.message(msg)

    manager.dispatch.assert_called_once()
    env = manager.dispatch.call_args[0][0]
    assert env.platform == 'xmpp'
    assert env.conversation_ref == 'room@conf.host'
    assert env.text == 'hello muc'

@pytest.mark.asyncio
async def test_xmpp_ignore_own_groupchat_message():
    from iacecil.connectors.xmpp import XMPPBot
    manager = AsyncMock()
    connector = MagicMock()
    connector.manager = manager
    bot = XMPPBot('user@host', 'pw', connector)
    bot.boundjid.full = 'user@host/res'
    bot.boundjid.user = 'user'

    msg = MagicMock()
    def getitem(k):
        if k == 'type': return 'groupchat'
        if k == 'from': 
            m = MagicMock()
            m.bare = 'room@conf.host'
            m.resource = 'user'  # same as boundjid.user
            m.full = 'room@conf.host/user'
            return m
        return None
    msg.__getitem__.side_effect = getitem

    await bot.message(msg)
    manager.dispatch.assert_not_called()

@pytest.mark.asyncio
async def test_xmpp_on_invite():
    from iacecil.connectors.xmpp import XMPPBot
    connector = MagicMock()
    bot = XMPPBot('user@host', 'pw', connector)
    bot.boundjid.user = 'user'
    # Mock xep_0045 plugin
    bot.plugin = {'xep_0045': MagicMock()}
    
    inv = {'from': 'room@conf.host', 'inviter': 'friend@host'}
    await bot.on_invite(inv)
    
    bot.plugin['xep_0045'].join_muc.assert_called_once_with('room@conf.host', 'user')

def test_xmpp_is_authorized():
    from iacecil.connectors.xmpp import Connector
    manager = MagicMock()
    # authorized channels config
    conn = Connector(manager, {'jid': 'user@host', 'password': 'pw', 'channels': ['room1@conf.host']})
    
    # DM is always authorized
    env_dm = Envelope(platform='xmpp', sender_ref='user2@host', conversation_ref='user2@host', raw={'type': 'chat'}, text='hi')
    assert conn.is_authorized(env_dm) is True
    
    # Authorized MUC
    env_muc_auth = Envelope(platform='xmpp', sender_ref='room1@conf.host/user', conversation_ref='room1@conf.host', raw={'type': 'groupchat'}, text='hi')
    assert conn.is_authorized(env_muc_auth) is True
    
    # Unauthorized MUC
    env_muc_unauth = Envelope(platform='xmpp', sender_ref='room2@conf.host/user', conversation_ref='room2@conf.host', raw={'type': 'groupchat'}, text='hi')
    assert conn.is_authorized(env_muc_unauth) is False

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
