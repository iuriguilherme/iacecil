"""
ia.cecil - modern bot class for aiogram 3
"""

import logging
logger = logging.getLogger(__name__)

import asyncio
from typing import Any, Union
from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNotFound,
    TelegramConflictError,
    TelegramEntityTooLarge,
    TelegramAPIError,
)

class IACecilBotV3(Bot):
    def __init__(self, token: str, config: Any, **kwargs):
        self.bot_config = config
        ## Compatibility attributes
        self.config = config
        
        ## Safely extract attributes from config (handles both Pydantic and dict)
        if hasattr(config, 'get'):
            self.info = config.get('info', {})
            tel_conf = config.get('telegram', {})
            self.plugins = config.get('plugins', {})
        else:
            self.info = getattr(config, 'info', {})
            tel_conf = getattr(config, 'telegram', {})
            self.plugins = getattr(config, 'plugins', {})
            
        ## Extract users section
        if hasattr(tel_conf, 'get'):
            self.users = tel_conf.get('users', {})
        else:
            self.users = getattr(tel_conf, 'users', {})
            
        super().__init__(token=token, **kwargs)

    async def _handle_exception(
        self,
        method_name: str,
        super_method: Any,
        *args,
        **kwargs,
    ):
        try:
            return await super_method(*args, **kwargs)
        except TelegramRetryAfter as e:
            logger.warning(f"Flood control in {method_name}: waiting {e.retry_after}s")
            await asyncio.sleep(float(e.retry_after))
            return await self._handle_exception(method_name, super_method, *args, **kwargs)
        except TelegramForbiddenError as e:
            logger.error(f"Forbidden error in {method_name}: {e.message}")
            ## Callbacks will be implemented in aiogram_v3.callbacks
            from .callbacks import error_callback, exception_callback
            if "kicked" in e.message.lower():
                await error_callback(f"Kicked during {method_name}", None, e, [method_name, 'BotKicked'])
            elif "blocked" in e.message.lower():
                await error_callback(f"Blocked during {method_name}", None, e, [method_name, 'BotBlocked'])
            elif "deactivated" in e.message.lower():
                await error_callback(f"Deactivated during {method_name}", None, e, [method_name, 'UserDeactivated'])
        except TelegramNotFound as e:
            if "replied message not found" in e.message.lower():
                logger.warning(f"Message not found in {method_name}, retrying without reply")
                kwargs['allow_sending_without_reply'] = True
                return await super_method(*args, **kwargs)
            else:
                from .callbacks import error_callback
                await error_callback(f"Not found during {method_name}", None, e, [method_name, 'NotFound'])
        except TelegramConflictError as e:
            logger.critical(f"Conflict error: same token used elsewhere! {e}")
        except TelegramEntityTooLarge as e:
            logger.error(f"Entity too large in {method_name}, chunking needed (not yet implemented here)")
            ## Port chunking logic if strictly needed, or defer to Envelope-level chunking
        except TelegramAPIError as e:
            logger.error(f"Telegram API error in {method_name}: {e}")
            from .callbacks import error_callback
            await error_callback(f"API Error in {method_name}", None, e, [method_name, 'TelegramAPIError'])
        except Exception as e:
            logger.exception(f"Unexpected error in {method_name}")
            from .callbacks import exception_callback
            await exception_callback(e, [method_name, 'InternalError'])
        return None

    async def send_message(self, *args, **kwargs):
        return await self._handle_exception('sendMessage', super().send_message, *args, **kwargs)

    async def send_photo(self, *args, **kwargs):
        return await self._handle_exception('sendPhoto', super().send_photo, *args, **kwargs)

    async def send_voice(self, *args, **kwargs):
        return await self._handle_exception('sendVoice', super().send_voice, *args, **kwargs)

    async def send_video(self, *args, **kwargs):
        return await self._handle_exception('sendVideo', super().send_video, *args, **kwargs)

    async def send_sticker(self, *args, **kwargs):
        return await self._handle_exception('sendSticker', super().send_sticker, *args, **kwargs)
