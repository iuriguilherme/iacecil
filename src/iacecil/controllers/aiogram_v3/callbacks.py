"""
ia.cecil - aiogram 3 modern callbacks
"""

import logging
logger = logging.getLogger(__name__)

from aiogram import types
from typing import Union, Any
from .middlewares import manager_context, config_context

## These callbacks should be used by V3 handlers
## They retrieve the manager and config from context if not passed

async def message_callback(
    message: types.Message,
    descriptions: list = None,
    manager: Any = None,
) -> None:
    if descriptions is None:
        descriptions = ['message']
    
    if message is not None:
        try:
            from ...models.envelope import Envelope
            
            ## Priority: 1. passed manager, 2. context-var manager
            mgr = manager or manager_context.get()
            
            if mgr:
                env = Envelope(
                    platform='telegram',
                    sender_ref=str(message.from_user.id),
                    conversation_ref=str(message.chat.id),
                    text=message.text or '',
                    reply_ref=str(message.reply_to_message.message_id) if message.reply_to_message else None,
                    tags=set(descriptions),
                    raw=message,
                    extra={
                        'first_name': message.from_user.first_name,
                        'last_name': message.from_user.last_name
                    },
                    native_message_id=str(message.message_id),
                    timestamp=message.date.timestamp(),
                )
                await mgr.dispatch(env)
        except Exception as e:
            logger.error(f"Failed to emit envelope in V3 message_callback: {e}")
            
        ## Re-use legacy loggers but they must be refactored to be context-aware
        # from ..log import zodb_logger
        # await zodb_logger(message)
    else:
        logger.warning("V3 Message callback ran without a message!")

async def error_callback(
    error: str = "Erro",
    message: Union[types.Message, None] = None,
    exception: Union[Exception, None] = None,
    descriptions: list = None,
) -> None:
    if descriptions is None:
        descriptions = ['error']
    from ..log import debug_logger
    await debug_logger(error, message, exception, descriptions)

async def exception_callback(
    exception: Union[Exception, None] = None,
    descriptions: list = None,
) -> None:
    if descriptions is None:
        descriptions = ['error']
    from ..log import exception_logger
    await exception_logger(exception, descriptions)
