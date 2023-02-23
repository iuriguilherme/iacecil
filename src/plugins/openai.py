"""
ia.cecil

Copyleft 2012-2023 Iuri Guilherme <https://iuri.neocities.org/>

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

# ~ import aiohttp
# ~ import asyncio
# ~ import glob
# ~ import os
import random
# ~ import typing
import uuid

import openai

from aiogram import (
    Dispatcher,
    types,
)

from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from iacecil.controllers.util import (
    dice_high,
    dice_low,
)
# ~ from ...persistence.zodb_orm import (
    # ~ get_messages_texts_list,
    # ~ get_furhat_texts_messages,
    # ~ set_furhat_text,
# ~ )
# ~ from ....plugins.natural import (
    # ~ generate,
    # ~ concordance,
    # ~ collocations,
    # ~ common_contexts,
    # ~ count,
    # ~ similar,
# ~ )
# ~ from ...personalidades import (
    # ~ gerar_comando,
    # ~ gerar_texto,
    # ~ generate_command_furhat,
    # ~ generate_text_furhat,
# ~ )
# ~ from ...._version import __version__ as iacecil_version
from iacecil.controllers.openai_chatgpt import (
    openai_start_session,
    openai_stop_session,
    get_completion,
)
from iacecil.controllers.personalidades import (
    gerar_texto,
)

async def get_aiogram_chatgpt_completion(*args, **kwargs) -> str:
    """Generate ChatGPT text completion for Telegram Bot"""
    text: str | None = None
    try:
        kwargs['prompt'] = await gerar_texto(
            'chatgpt_prompt',
            kwargs.get('dispatcher').bot,
            kwargs.get('message'),
        )
        kwargs['api_key'] = kwargs.get('dispatcher').config.openai.get(
            'api_key')
        completion: openai.Completion = await get_completion(*args,
            **kwargs)
        choice: dict = random.choice(completion.choices)
        text: str = choice.get('text')
    except Exception as e:
        logger.exception(e)
        raise
    return text

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Aiogram Handlers"""
    try:
        @dispatcher.message_handler(
            commands = ['gpt', 'chatgpt'],
        )
        async def chatgpt_callback(message: types.Message) -> None:
            """Callback for /gpt command handler"""
            descriptions: list = [
                'chatgpt',
                dispatcher.config.personalidade,
                message.chat.type,
            ]
            try:
                await message_callback(message, descriptions)
                command: types.Message = await message.reply(
                    await get_aiogram_chatgpt_completion(
                        dispatcher = dispatcher,
                        message = message,
                    ),
                )
                await command_callback(command, descriptions)
            except Exception as e:
                logger.exception(e)
                # ~ await error_callback(
                    # ~ "Erro genérico",
                    # ~ message,
                    # ~ e,
                    # ~ ['exception'] + descriptions,
                # ~ )
        @dispatcher.message_handler(
            content_types = types.ContentTypes.TEXT,
            state = "*",
        )
        async def chance_gpt_callback(message: types.Message) -> None:
            """Responde toda e qualquer mensagem em uma chance \
aleatória"""
            if len(message.text) > 15 and await dice_low(30):
                await chatgpt_callback(message)
    except Exception as e:
        logger.exception(e)
