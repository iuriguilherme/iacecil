# -*- coding: utf-8 -*-
#  
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import logging
logger = logging.getLogger(__name__)

from aiogram import types
from quart import current_app
from iacecil import config
from iacecil.controllers.log import (
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
):
    if message is not None:
        setattr(message, 'tags', descriptions)
        try:
            if current_app.furhat and message.text is not None:
                await furhat_logger(message.text)
        except Exception as exception:
            logger.info(repr(exception))
        await zodb_logger(message)
    await info_logger(message, ['message'] + descriptions)

async def command_callback(
    message: types.Message,
    descriptions: list = ['command'],
):
    if message is not None:
        await info_logger(message, ['command'] + descriptions)

async def error_callback(
    error: str = u"Erro",
    message: types.Message = None,
    exception: Exception = None,
    descriptions: list = ['error'],
):
    await debug_logger(error, message, exception, descriptions)

async def exception_callback(
    exception: Exception = None,
    descriptions: list = ['error'],
):
    await exception_logger(exception, descriptions)

async def any_message_callback(message: types.Message):
    try:
        if current_app.furhat and message.text is not None:
            await furhat_logger(message.text)
    except Exception as exception:
        logger.warning(repr(exception))
    await zodb_logger(message)
    # ~ await info_logger(message, ['message'])

async def any_edited_message_callback(message: types.Message):
    await info_logger(message, ['edited_message', message.chat.type])

async def any_channel_post_callback(message: types.Message):
    await info_logger(message, ['channel_post'])

async def any_edited_channel_post_callback(message: types.Message):
    await info_logger(message, ['edited_channel_post'],)

async def any_update_callback(update):
    await info_logger(update, ['update'])

async def any_error_callback(update, error):
    if update:
        if repr(error) in [
            """BotKicked('Forbidden: bot was kicked from \
the supergroup chat')""",
            "Forbidden: bot was kicked from the supergroup chat",
        ]:
            await debug_logger(u"We were kicked from {} ({})".format(
                update.message.chat.id,
                update.message.chat.title,
            ), update, error, ['BotKicked', 'exception'])
        else:
            await debug_logger(u"Erro não tratado:", update, error,
                ['error', 'unhandled']
            )
    else:
        await exception_logger(error, ['error', 'unhandled'])
