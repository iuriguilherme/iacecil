import pytest
from iacecil.controllers._iacecil.connectors_v3_runner import build_managers_v3
from iacecil.config import BotConfig
from unittest.mock import MagicMock

def test_build_managers_v3_mapping():
    ## Use real BotConfig with explicit telegram_v3
    data = {
        'coinmarketcap': {}, 'deepseek': {}, 'discord': {}, 'donate': {},
        'furhat': {}, 'info': {}, 'openai': {}, 'jobs': [], 
        'loopback': {}, 'mastodon': {}, 'matrix': {}, 'xmpp': {},
        'personalidade': 'default', 'plugins': {'enable': []},
        'serpapi': {}, 'tecido': {}, 'telegram': {},
        'telegram_v3': {'token': 'test_token'},
        'timezone': 'UTC', 'tropixel': {}, 'web3': {}
    }
    config = BotConfig(**data)
    
    configs = {'bot1': config}
    
    managers = build_managers_v3(configs)
    
    assert len(managers) == 1
    assert config.telegram_v3 == {'token': 'test_token'}
