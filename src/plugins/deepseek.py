"""
Plugin deepseek para ia.cecil

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

## Deepseek website: https://www.deepseek.com/
## These commands currently interacting with a local serving instance 
## of https://ollama.com/
## Ollama API reference:
## https://github.com/ollama/ollama/blob/main/docs/api.md

import logging
logger: logging.Logger = logging.getLogger(__name__)

from ollama import AsyncClient

from aiogram import (
    Dispatcher,
    types,
)
from aiogram.utils.markdown import (
    # ~ escape_md,
    italic,
    spoiler,
)

from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from iacecil.controllers.util import (
    dice_low,
)

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Aiogram Handlers"""
    try:
        @dispatcher.message_handler(commands = ['ds', 'deepseek'])
        async def deepseek_callback(message: types.Message,
            reply: bool = False) -> None:
            """Callback for /ds command handler"""
            command: types.Message | None = None
            think: bool = False
            think_buffer: list = []
            answer_buffer: list = []
            try:
                descriptions: list[str] = ['deepseek',
                    dispatcher.config.personalidade, message.chat.type]
                await message_callback(message, descriptions)
                ollama_model: str = dispatcher.config.deepseek.get(
                    'ollama', {'model': "deepseek-r1:1.5b"}).get('model',
                    "deepseek-r1:1.5b")
                await message_callback(message, descriptions)
                ollama_messages: list[dict] = []
                if reply:
                    ollama_messages.append({'role': 'assistant',
                        'content': message['reply_to_message']['text']})
                ollama_messages.append({'role': 'user',
                    'content': message.get_args()})
                async for part in await AsyncClient().chat(
                    model = ollama_model, messages = ollama_messages,
                    stream = True):
                    logger.debug(f"""Chat completion part:
{part['message']['content']}""")
                    if '<think>' in part['message']['content']:
                        think = True
                        continue
                    elif '</think>' in part['message']['content']:
                        think = False
                        continue
                    if not think:
                        answer_buffer.append(part['message']['content'])
                    else:
                        think_buffer.append(part['message']['content'])
                    # ~ if part['message']['content'] in ['.', ',', '\n', '\n\n']:
                        # ~ command = await message.reply(''.join(command_buffer))
                        # ~ command_buffer = []
                # ~ if command:
                    # ~ await command_callback(command, descriptions)
                command = await message.reply(
                    spoiler(italic(''.join(think_buffer))),
                    parse_mode = 'MarkdownV2')
                await command_callback(command, descriptions)
                command = await message.reply(''.join(answer_buffer))
                await command_callback(command, descriptions)
            except Exception as e:
                logger.exception(e)
                await error_callback(
                    "Erro com resposta deepseek",
                    message,
                    e,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(is_reply_to_id = dispatcher.bot.id)
        async def resposta_deepseek_callback(message: types.Message) -> None:
            """Reply all replies to this bot"""
            descriptions: list[str] = ['resposta', 'deepseek',
                dispatcher.config.personalidade, message.chat.type]
            try:
                await deepseek_callback(message, True)
            except Exception as e:
                logger.exception(e)
                await error_callback(
                    "Erro com resposta deepseek",
                    message,
                    e,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(content_types = types.ContentTypes.TEXT,
            state = "*")
        async def chance_deepseek_callback(message: types.Message) -> None:
            """Responde toda e qualquer mensagem em uma chance \
aleatória"""
            try:
                if len(message.text) > 15 and await dice_low(30):
                    await deepseek_callback(message)
            except Exception as e:
                logger.exception(e)
    except Exception as e:
        logger.exception(e)
