"""
Example Telegram Bot (t.me/matehackersbot)
Copy this file to instance/bots/matehackersbot.py
"""

import logging
logger = logging.getLogger(__name__)

from pydantic_settings import BaseSettings

try:
    from .default import DefaultBotConfig
except Exception as e:
    logger.exception(e)
    from iacecil.config import DefaultBotConfig

default_config = DefaultBotConfig()

class BotConfig(BaseSettings):
    coinmarketcap: dict = default_config.coinmarketcap
    deepseek: dict = default_config.deepseek
    discord: dict = default_config.discord
    donate: dict = default_config.donate
    furhat: dict = default_config.furhat
    info: dict = default_config.info
    jobs: list = default_config.jobs
    quart: dict = default_config.quart
    serpapi: dict = default_config.serpapi
    tecido: dict = default_config.tecido
    timezone: str = default_config.timezone
    tropixel: dict = default_config.tropixel
    web3: dict = default_config.web3
    
    personalidade: str = "matebot"
    plugins: dict = dict(
        enable = [
            "admin",
            "archive",
            "cryptoforex",
            "donate",
            "feedback",
            "greatful",
            "hashes",
            "mate_matica",
            "qr",
            "storify",
            "tropixel",
            "ytdl",
            "rss",
            "tts",
            "garimpo",
            "natural",
            "default",
            "welcome",
        ], # enable
        disable = [
            "echo",
            "totalvoice",
            "portaria",
            # ~ "admin",
            # ~ "archive",
            # ~ "cryptoforex",
            # ~ "donate",
            # ~ "feedback",
            # ~ "greatful",
            # ~ "hashes",
            # ~ "mate_matica",
            # ~ "qr",
            # ~ "storify",
            # ~ "tropixel",
            # ~ "tts",
            # ~ "web3_wrapper",
            # ~ "ytdl",
            "bomdia",
            "calendar",
            # ~ "rss",
            # ~ "default",
            # ~ "tts",
            # ~ "natural",
            "web3_wrapper",
            "tracker",
            # ~ "welcome",
            # ~ "garimpo",
            "deepseek",
        ], # disable
    ) # plugins
    telegram: dict = dict(
        default_config.telegram.copy(),
        token = "garbage",
    ) # telegram
