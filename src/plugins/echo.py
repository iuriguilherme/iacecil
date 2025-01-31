"""
Plugin echo para ia.cecil: Repete tudo, melhor que papagaio

ia.cecil

Copyleft 2016-2025 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
logger = logging.getLogger(__name__)

from aiogram import (
    Dispatcher,
    types
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register Aiogram Handlers to Dispatcher"""
    try:
        @dispatcher.message_handler()
        async def echo(message: types.Message):
            await message_callback(message, ['echo', message.chat.type])
            command = await message.answer(message.text)
            await command_callback(command, ['echo', message.chat.type])
    except Exception as e:
        logger.exception(e)
        raise
