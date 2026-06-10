import pytest
import asyncio
from unittest.mock import AsyncMock
from iacecil.connectors import ConnectorManager
from iacecil.connectors.loopback import Connector

@pytest.mark.asyncio
async def test_loopback_inject(capfd):
    manager = ConnectorManager({'loopback': {'enabled': True}})
    manager.command_registry = {}
    
    async def mock_handler(env):
        if env.text.startswith('/start'):
            return "Loopback: /start command received"
        return f"Echo: {env.text}"
    
    manager.set_default_handler(mock_handler)
    
    connector = manager.connectors['loopback']
    await connector.connect()
    
    listen_task = asyncio.create_task(connector.listen())
    
    await connector.inject("/start args")
    await asyncio.sleep(0.1)
    
    captured = capfd.readouterr()
    assert "> Loopback: /start command received\n" in captured.out
    
    await connector.inject("hello")
    await asyncio.sleep(0.1)
    
    captured = capfd.readouterr()
    assert "> Echo: hello\n" in captured.out
    
    await connector.disconnect()
    await listen_task

@pytest.mark.asyncio
async def test_loopback_persists_neutral_record(capfd):
    manager = ConnectorManager({'loopback': {'enabled': True}})
    manager.command_registry = {}
    
    async def mock_handler(env):
        return "reply"
    manager.set_default_handler(mock_handler)
    
    connector = manager.connectors['loopback']
    await connector.connect()
    listen_task = asyncio.create_task(connector.listen())
    
    await connector.inject("/test")
    await asyncio.sleep(0.1)
    
    import iacecil.controllers.persistence.neutral as neutral
    db = await neutral.get_messages_db()
    with db.transaction() as conn:
        msgs = list(conn.root.messages.values())
        assert len(msgs) > 0
        assert any(m['text'] == '/test' for m in msgs)
        
    await connector.disconnect()
    await listen_task
