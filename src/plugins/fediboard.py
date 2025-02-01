"""
Plugin fediboard para ia.cecil

Copyleft 2025 Iuri Guilherme <https://iuri.neocities.org/>

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
logger: logging.Logger = logging.getLogger(__name__)

from aiogram import (
    Dispatcher,
    filters,
    types,
)

from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Aiogram Handlers"""
    try:
        @dispatcher.message_handler(filters.Text(contains = '#matehackers',
            ignore_case = True))
        async def fediboard_callback(message: types.Message) -> None:
            """Garimpa todas mensagens pro fediboard"""
            try:
                descriptions: list[str] = ['fediboard',
                    dispatcher.config.personalidade, message.chat.type]
                await message_callback(message, descriptions)
                command: types.Message = await message.reply("""\
Mensagem enviada para https://denise.matehackers.org/fediboard""")
                await command_callback(command, descriptions)
            except Exception as e:
                logger.exception(e)
                await error_callback(
                    "Erro enviando para fediboard",
                    message,
                    e,
                    ['exception'] + descriptions,
                )
    except Exception as e:
        logger.exception(e)
