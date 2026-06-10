import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

from iacecil.connectors import ConnectorManager
from iacecil.connectors.base import BaseConnector
from iacecil.models.envelope import Envelope

# We create some fake connectors for testing
import sys
import types

class FakeConnector(BaseConnector):
    async def connect(self): pass
    async def listen(self): pass
    async def send(self, env): pass
    async def disconnect(self): pass

class FakeRaisingConnector(BaseConnector):
    async def connect(self): pass
    async def listen(self): raise ValueError("Crash!")
    async def send(self, env): pass
    async def disconnect(self): pass

# Patch import machinery to allow fake connectors
@pytest.fixture(autouse=True)
def mock_connectors(monkeypatch):
    telegram_mod = types.ModuleType("iacecil.connectors.telegram")
    telegram_mod.Connector = FakeConnector
    sys.modules["iacecil.connectors.telegram"] = telegram_mod

    xmpp_mod = types.ModuleType("iacecil.connectors.xmpp")
    xmpp_mod.Connector = FakeConnector
    sys.modules["iacecil.connectors.xmpp"] = xmpp_mod

    bad_mod = types.ModuleType("iacecil.connectors.loopback")
    bad_mod.Connector = FakeRaisingConnector
    sys.modules["iacecil.connectors.loopback"] = bad_mod

    yield
    del sys.modules["iacecil.connectors.telegram"]
    del sys.modules["iacecil.connectors.xmpp"]
    del sys.modules["iacecil.connectors.loopback"]


@pytest.mark.asyncio
async def test_manager_loading(caplog):
    config = {
        'telegram': {'token': '123'},
        'xmpp': {'jid': 'user@host', 'password': 'pw'},
        'discord': {}, # empty
        'unknown_service': {'token': 'fake'}
    }
    
    with caplog.at_level(logging.ERROR):
        manager = ConnectorManager(config)
    
    assert 'telegram' in manager.connectors
    assert 'xmpp' in manager.connectors
    assert 'discord' not in manager.connectors
    assert "Unknown connector section 'unknown_service' with credentials, skipping." in caplog.text


@pytest.mark.asyncio
async def test_manager_run_all(caplog):
    config = {
        'telegram': {'token': '123'}, # fake
        'loopback': {'enabled': True} # fake raising
    }
    manager = ConnectorManager(config)
    
    with caplog.at_level(logging.ERROR):
        await manager.run_all()
    
    # Assert loopback crashed and marked down, but didn't take down telegram (telegram exited instantly since fake listen does nothing)
    assert "Connector loopback failed: Crash!" in caplog.text
    assert "Connector loopback marked down." in caplog.text
    assert "Connector telegram marked down." in caplog.text


@pytest.mark.asyncio
async def test_dispatch_routing():
    manager = ConnectorManager({'telegram': {'token': '123'}})
    
    start_handler = AsyncMock(return_value="Hello Start")
    default_handler = AsyncMock(return_value="Hello Default")
    
    manager.register_command("start", start_handler)
    manager.set_default_handler(default_handler)
    
    manager.connectors['telegram'].send = AsyncMock()
    
    env1 = Envelope("telegram", "s", "c", "/start args")
    await manager.dispatch(env1)
    start_handler.assert_called_once_with(env1)
    default_handler.assert_not_called()
    manager.connectors['telegram'].send.assert_called_once()
    
    start_handler.reset_mock()
    manager.connectors['telegram'].send.reset_mock()
    
    env2 = Envelope("telegram", "s", "c", "normal text")
    await manager.dispatch(env2)
    start_handler.assert_not_called()
    default_handler.assert_called_once_with(env2)
    manager.connectors['telegram'].send.assert_called_once()
