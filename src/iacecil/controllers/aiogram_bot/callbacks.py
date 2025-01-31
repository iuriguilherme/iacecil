"""
ia.cecil

Copyleft 2012-2025 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
logger = logging.getLogger(__name__)

from aiogram import types
from quart import current_app
from typing import Union
from ..log import (
    debug_logger,
    exception_logger,
    furhat_logger,
    info_logger,
    zodb_logger,
)
from plugins.garimpo import varre_link

async def message_callback(
    message: types.Message,
    descriptions: list = ['message'],
) -> None:
    """
    Callback for messages that need to be handled with more than one
    logger
    """
    if message is not None:
        setattr(message, 'tags', descriptions)
        try:
            if current_app.furhat and message.text is not None:
                await furhat_logger(message.text)
        except Exception as exception:
            logger.exception(exception)
        await zodb_logger(message)
    else:
        await debug_logger(
            "Message callback ran without a message!",
            message,
            None,
            descriptions,
        )
    ## TODO: 429
    # ~ await info_logger(message, ['message'] + descriptions)

async def command_callback(
    message: types.Message,
    descriptions: list = ['command'],
) -> None:
    """Successful aiogram.types.Message (s) sent"""
    if message is not None:
        await info_logger(message, ['command'] + descriptions)
    else:
        await debug_logger(
            "Command callback ran without a message!",
            message,
            None,
            descriptions,
        )

async def error_callback(
    error: str = "Erro",
    message: Union[types.Message, None] = None,
    exception: Union[Exception, None] = Exception("Erro"),
    descriptions: list = ['error'],
) -> None:
    """
    Send exception to configured logger,
    error message and exception to telegram
    """
    # ~ logger.exception(exception)
    await debug_logger(error, message, exception, descriptions)

async def exception_callback(
    exception: Union[Exception, None] = Exception("Erro"),
    descriptions: list = ['error'],
) -> None:
    """Send exception to configured logger and to telegram"""
    # ~ logger.exception(exception)
    await exception_logger(exception, descriptions)

async def any_message_callback(message: types.Message) -> None:
    """Fallback callback for any message for handlers"""
    try:
        if current_app.furhat and message.text is not None:
            await furhat_logger(message.text)
    except Exception as exception:
        logger.warning(repr(exception))
    await zodb_logger(message)
    # ~ await info_logger(message, ['message'])

async def any_edited_message_callback(message: types.Message) -> None:
    """Fallback callback for edited messages for handlers"""
    # ~ await info_logger(message, ['edited_message', message.chat.type])
    await zodb_logger(message)

async def any_channel_post_callback(message: types.Message) -> None:
    """Fallback callback for channel messages for handlers"""
    await info_logger(message, ['channel_post'])

async def any_edited_channel_post_callback(message: types.Message) -> None:
    """Fallback callback for edited channel messages for handlers"""
    await info_logger(message, ['edited_channel_post'],)

async def any_update_callback(update) -> None:
    """Fallback callback for all updates not handled for handlers"""
    await info_logger(update, ['update'])

async def any_error_callback(update, error) -> None:
    """Fallback callback for errors for handlers"""
    try:
        if update:
            if repr(error) in [
                """BotKicked('Forbidden: bot was kicked from \
    the supergroup chat')""",
                "Forbidden: bot was kicked from the supergroup chat",
            ]:
                await debug_logger("We were kicked from {} ({})".format(
                    update.message.chat.id,
                    update.message.chat.title,
                ), update, error, ['BotKicked', 'exception'])
            else:
                await debug_logger("Erro não tratado:", update, error,
                    ['error', 'unhandled']
                )
        else:
            await exception_logger(error, ['error', 'unhandled'])
    except Exception as exception:
        await exception_logger(
            exception,
            ['error', 'internal', 'exception', 'unhandled'],
        )
