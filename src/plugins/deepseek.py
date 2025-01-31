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

# ~ import aiohttp
# ~ import asyncio
# ~ import glob
import json
# ~ import os
# ~ import random
# ~ import typing
# ~ import uuid

# ~ import openai
from ollama import AsyncClient

from aiogram import (
    Dispatcher,
    types,
)
from aiogram.utils.markdown import (
    italic,
)

from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from iacecil.controllers.util import (
    # ~ dice_high,
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
# ~ from iacecil.controllers.personalidades import (
    # ~ gerar_texto,
# ~ )

# ~ async def get_aiogram_deepseek_r1_completion(*args, **kwargs) -> str:
    # ~ """Generate Deepseek R1 text completion for Telegram Bot"""
    # ~ text: str | None = None
    # ~ try:
        # ~ logger.info(f"Getting deepseek completion request")
        # ~ kwargs['prompt'] = await gerar_texto(
            # ~ 'chatgpt_prompt',
            # ~ kwargs.get('dispatcher').bot,
            # ~ kwargs.get('message'),
        # ~ )
        # ~ kwargs['ollama_host'] = kwargs.get('dispatcher').config.deepseek.get(
            # ~ 'ollama', {'host': "http://127.0.0.1:11434"}).get('host',
            # ~ "http://127.0.0.1:11434")
        # ~ kwargs['ollama_model'] = kwargs.get('dispatcher').config.deepseek.get(
            # ~ 'ollama', {'model': "deepseek-r1:1.5b"}).get('model',
            # ~ "deepseek-r1:1.5b")
        # ~ post_data: dict[str, str] = {
            # ~ 'model': kwargs.get('ollama_model'),
            # ~ 'prompt': kwargs.get('prompt'),
            # ~ 'stream': False,
        # ~ }
        # ~ async with aiohttp.ClientSession() as session:
            # ~ async with session.post('/'.join([kwargs.get('ollama_host'),
                # ~ 'api', 'generate']), data = post_data) as response:
                # ~ logger.info(f"Status: {response.status}")
                # ~ logger.info(f"""Content-type: \
# ~ {response.headers['content-type']}""")
                # ~ html = await response.text()
                # ~ logger.info(f"Body: {html[:15]}...")
                # ~ text = html
        # ~ completion: openai.Completion = await get_completion(*args,
            # ~ **kwargs)
        # ~ choice: dict = random.choice(completion.choices)
        # ~ text: str = choice.get('text')
    # ~ except Exception as e:
        # ~ logger.exception(e)
        # ~ raise
    # ~ return text

# ~ async def get_aiogram_deepseek_r1_chat(*args, **kwargs) -> str:
    # ~ """Generate Deepseek R1 chat text completion for Telegram Bot"""
    # ~ text: str | None = None
    # ~ try:
        # ~ logger.info(f"Getting deepseek completion request")
        # ~ kwargs['prompt'] = await gerar_texto(
            # ~ 'chatgpt_prompt',
            # ~ kwargs.get('dispatcher').bot,
            # ~ kwargs.get('message').get_args(),
        # ~ )
        # ~ logger.info(f"Using prompt: {kwargs.get('prompt')}")
        # ~ kwargs['ollama_host'] = kwargs.get('dispatcher').config.deepseek.get(
            # ~ 'ollama', {'host': "http://127.0.0.1:11434"}).get('host',
            # ~ "http://127.0.0.1:11434")
        # ~ logger.info(f"Using host: {kwargs.get('ollama_host')}")
        # ~ kwargs['ollama_model'] = kwargs.get('dispatcher').config.deepseek.get(
            # ~ 'ollama', {'model': "deepseek-r1:1.5b"}).get('model',
            # ~ "deepseek-r1:1.5b")
        # ~ logger.info(f"Using model: {kwargs.get('ollama_model')}")
        # ~ post_data: dict[str, str] = {
            # ~ 'model': kwargs.get('ollama_model'),
            # ~ 'prompt': kwargs.get('prompt'),
            # ~ 'stream': False,
        # ~ }
        # ~ async with aiohttp.ClientSession() as session:
            # ~ async with session.post('/'.join([kwargs.get('ollama_host'),
                # ~ 'api', 'generate']), data = post_data) as response:
                # ~ logger.info(f"Status: {response.status}")
                # ~ logger.info(f"""Content-type: \
# ~ {response.headers['content-type']}""")
                # ~ html = await response.text()
                # ~ logger.info(f"Body: {html[:15]}...")
                # ~ logger.info(f"Body: {html}...")
                # ~ text = html
        # ~ completion: openai.Completion = await get_completion(*args,
            # ~ **kwargs)
        # ~ choice: dict = random.choice(completion.choices)
        # ~ text: str = choice.get('text')
    # ~ except Exception as e:
        # ~ logger.exception(e)
        # ~ raise
    # ~ return text

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Aiogram Handlers"""
    try:
        @dispatcher.message_handler(commands = ['ds', 'deepseek'])
        async def deepseek_callback(message: types.Message) -> None:
            """Callback for /ds command handler"""
            descriptions: list[str] = ['deepseek',
                dispatcher.config.personalidade, message.chat.type]
            command: types.Message | None = None
            think: bool = False
            think_buffer: list = []
            answer_buffer: list = []
            try:
                ollama_model: str = dispatcher.config.deepseek.get(
                    'ollama', {'model': "deepseek-r1:1.5b"}).get('model',
                    "deepseek-r1:1.5b")
                await message_callback(message, descriptions)
                ollama_message: dict[str] = {'role': 'user',
                    'content': message.get_args()}
                async for part in await AsyncClient().chat(
                    model = ollama_model, messages = [ollama_message],
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
                command = await message.reply(''.join(['...'] + think_buffer))
                await command_callback(command, descriptions)
                command = await message.reply(''.join(answer_buffer))
                await command_callback(command, descriptions)
            except Exception as e:
                logger.exception(e)
                # ~ await error_callback(
                    # ~ "Erro genérico",
                    # ~ message,
                    # ~ e,
                    # ~ ['exception'] + descriptions,
                # ~ )
        @dispatcher.message_handler(content_types = types.ContentTypes.TEXT,
            state = "*")
        async def chance_gpt_callback(message: types.Message) -> None:
            """Responde toda e qualquer mensagem em uma chance \
aleatória"""
            try:
                if len(message.text) > 15 and await dice_low(30):
                    await deepseek_callback(message)
            except Exception as e:
                logger.exception(e)
    except Exception as e:
        logger.exception(e)
