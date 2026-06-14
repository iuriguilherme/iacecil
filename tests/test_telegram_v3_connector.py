import pytest
from iacecil.connectors.telegram_v3 import TelegramV3Connector
from iacecil.connectors import ConnectorManager
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_telegram_v3_connector_init():
    manager = MagicMock()
    manager.bot_config.bots = {'bot1': MagicMock()}
    config = {}
    connector = TelegramV3Connector(manager, config)
    assert connector.platform == 'telegram_v3'

@pytest.mark.asyncio
async def test_load_plugin_v3():
    from iacecil.connectors import load_plugin
    from aiogram import Router
    
    router = Router()
    plugin_name = 'echo'
    
    ## Mock the plugin module
    import sys
    mock_plugin = MagicMock()
    ## load_plugin checks f'add_handlers_{connector_name}'
    ## which is 'add_handlers_telegram_v3' in this case
    mock_plugin.add_handlers_telegram_v3 = AsyncMock()
    mock_plugin.add_handlers_v3 = AsyncMock()
    
    ## Ensure it doesn't have the first check to hit the second
    del mock_plugin.add_handlers_telegram_v3
    
    sys.modules['plugins.echo'] = mock_plugin
    
    await load_plugin('telegram_v3', 'echo', router)
    mock_plugin.add_handlers_v3.assert_called_once_with(router)
