"""
Plugin echo para ia.cecil: Repete tudo, melhor que papagaio

ia.cecil

Copyleft 2016-2026 Iuri Guilherme <https://iuri.neocities.org/>

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

from typing import Any

async def add_handlers_v3(router: Any) -> None:
    """Register Aiogram 3 Handlers to Router"""
    try:
        from aiogram import F
        from iacecil.controllers.aiogram_v3.callbacks import message_callback
        
        @router.message(F.text == "/echo_v3")
        async def echo_v3(message: types.Message):
            await message_callback(message, ['echo', message.chat.type])
            await message.answer(message.text)
            
        @router.message()
        async def echo_all_v3(message: types.Message):
            """Catch-all for echo testing in V3"""
            logger.debug(f"Echo V3 catching message: {message.text}")
            await message_callback(message, ['echo', message.chat.type])
            await message.answer(message.text)

    except Exception as e:
        logger.exception(e)
        raise

async def echo_envelope(envelope) -> str:
    """Echo handler for connector platforms (testing)"""
    return envelope.text

async def add_envelope_handlers(manager) -> None:
    """Echo every message that no command handler claimed (any connector)"""
    manager.set_default_handler(echo_envelope)
