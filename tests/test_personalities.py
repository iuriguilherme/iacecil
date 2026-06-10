import pytest
from iacecil.connectors import ConnectorManager
from iacecil.models.envelope import Envelope
from iacecil.controllers.personalidades import default, personalidades

class FakeUser:
    def __init__(self, first_name, last_name, id):
        self.first_name = first_name
        self.last_name = last_name
        self.id = id

class FakeMessage:
    def __init__(self, text, first_name="Test", last_name="User", id="123"):
        self.text = text
        self.from_user = FakeUser(first_name, last_name, id)

@pytest.mark.asyncio
async def test_personality_commands_dict():
    assert hasattr(default, 'commands')
    assert 'start' in default.commands
    
@pytest.mark.asyncio
async def test_default_start_envelope():
    env = Envelope(
        platform='test',
        sender_ref='456',
        conversation_ref='chat',
        text='/start',
        extra={'first_name': 'Env', 'last_name': 'User'}
    )
    result = await default.commands['start'](env)
    assert 'Env User' in result
    assert '456' in result

@pytest.mark.asyncio
async def test_same_personality_two_connectors():
    env1 = Envelope('telegram', '1', '1', '/start', extra={'first_name': 'A', 'last_name': 'B'})
    env2 = Envelope('xmpp', '1', '1', '/start', extra={'first_name': 'A', 'last_name': 'B'})
    
    res1 = await default.commands['start'](env1)
    res2 = await default.commands['start'](env2)
    assert res1 == res2

@pytest.mark.asyncio
async def test_gerar_texto_legacy_path():
    from iacecil.controllers.personalidades import gerar_texto
    class FakeBot:
        class Config:
            personalidade = 'default'
        config = Config()
    
    msg = FakeMessage('/start', 'Legacy', 'User', '123')
    result = await gerar_texto('start', FakeBot(), msg)
    assert 'Legacy User' in result
    assert '123' in result
