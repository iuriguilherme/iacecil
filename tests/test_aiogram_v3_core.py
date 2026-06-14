import pytest
from iacecil.controllers.aiogram_v3.bot import IACecilBotV3
from iacecil.controllers.aiogram_v3.middlewares import ContextMiddleware
from aiogram import Dispatcher
from unittest.mock import MagicMock

from iacecil.config import BotConfig

def test_bot_config_replication():
    ## Test with all required fields
    data = {
        'coinmarketcap': {}, 'deepseek': {}, 'discord': {}, 'donate': {},
        'furhat': {}, 'info': {}, 'openai': {}, 'jobs': [],
        'loopback': {}, 'mastodon': {}, 'matrix': {}, 'xmpp': {},
        'personalidade': 'default', 'plugins': {'enable': []},
        'serpapi': {}, 'tecido': {}, 'telegram': {'token': 'abc'},
        'telegram_v3': {'token': 'abc'},
        'timezone': 'UTC', 'tropixel': {}, 'web3': {}
    }
    config = BotConfig(**data)
    assert config.telegram_v3 == {'token': 'abc'}

def test_iacecil_bot_v3_init():
    ## Use a dict to test robust constructor
    config = {
        'info': "test info",
        'telegram': {'token': 'test_token', 'users': {'special': {}}},
        'plugins': []
    }

    bot = IACecilBotV3(token="123:abc", config=config)
    assert bot.token == "123:abc"
    assert bot.info == "test info"
@pytest.mark.asyncio
async def test_context_middleware():
    manager = MagicMock()
    bot_config = MagicMock()
    conn_config = MagicMock()
    middleware = ContextMiddleware(manager, bot_config, conn_config)
    
    async def mock_handler(event, data):
        return data
    
    event = MagicMock()
    data = {}
    
    result = await middleware(mock_handler, event, data)
    assert result['manager'] == manager
    assert result['bot_config'] == bot_config
    assert result['connector_config'] == conn_config
