import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from iacecil.connectors import ConnectorManager
from iacecil.config import BotConfig
from iacecil.controllers.aiogram_v3.middlewares import manager_context, config_context
from iacecil.controllers.log import debug_logger
from aiogram import types

import pytest

@pytest.mark.asyncio
async def test_v3_lifecycle_integration():
    ## 1. Setup BotConfig (Pydantic object)
    data = {
        'coinmarketcap': {}, 'deepseek': {}, 'discord': {}, 'donate': {},
        'furhat': {}, 'info': {'website': 'http://test', 'repository': 'http://repo'}, 
        'openai': {}, 'jobs': [],
        'loopback': {}, 'mastodon': {}, 'matrix': {}, 'xmpp': {},
        'personalidade': 'default', 'plugins': {'enable': ['echo']},
        'serpapi': {}, 'tecido': {}, 
        'telegram': {
            'token': '123:abc',
            'info': {'group': 'g', 'channel': 'c', 'admin': 'a', 'dev': 'd'},
            'users': {'special': {'debug': 12345}}
        },
        'telegram_v3': {'token': '123:abc'},
        'timezone': 'UTC', 'tropixel': {}, 'web3': {}
    }
    config = BotConfig(**data)
    
    ## 2. Initialize Manager
    manager = ConnectorManager(config, bot_id="test_bot")
    
    ## 3. Verify Telegram V3 Connector Connect
    connector = manager.connectors.get('telegram_v3')
    assert connector is not None
        
    ## Mock bot for network safety
    mock_bot = AsyncMock()
    mock_bot.id = 999
    mock_bot.session = MagicMock()
    
    ## Patch aiogram_v3_startup to return a mocked dispatcher
    from iacecil.controllers.aiogram_v3 import aiogram_v3_startup
    
    ## Force bot into dispatcher
    dispatcher = aiogram_v3_startup(config, "test_bot")
    setattr(dispatcher, 'bot', mock_bot)
    
    ## Trigger connector setup manually with mocked parts
    connector.dispatcher = dispatcher
    connector.bot = mock_bot
    setattr(dispatcher, 'manager', manager)
    
    ## Verify Middleware and Plugin Registration
    await connector.register_plugins()
    
    ## 4. Verify Context and Logging
    ## Simulate a message update triggering a handler
    message = MagicMock()
    message.chat = MagicMock()
    message.chat.id = 12345
    message.chat.type = "private"
    message.message_id = 67890
    message.text = "Hello"
    ## Mock dictionary behavior for item assignment check in log.py
    message.__getitem__.side_effect = lambda k: {}
    message.model_dump = MagicMock(return_value={'message_id': 67890, 'text': 'Hello'})
    
    from iacecil.controllers.aiogram_v3.middlewares import manager_context, config_context, dispatcher_context
    
    ## Manually set context vars (normally done by middleware)
    t_manager = manager_context.set(manager)
    t_config = config_context.set(config)
    t_dispatcher = dispatcher_context.set(dispatcher)
    
    try:
        await debug_logger(error="Verification Test", message=message)
        
        ## Verify bot.send_message was called with the correct chat_id from config
        mock_bot.send_message.assert_called()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs['chat_id'] == 12345
    finally:
        manager_context.reset(t_manager)
        config_context.reset(t_config)
        dispatcher_context.reset(t_dispatcher)
