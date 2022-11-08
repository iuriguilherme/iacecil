"""
Plugin tts para ia.cecil: text to speech

ia.cecil

Copyleft 2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import os
from aiogram import (
    Dispatcher,
    exceptions,
    filters,
    types,
)
from aiogram.utils.markdown import escape_md
from typing import Union
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
)
from iacecil.controllers.ffmpeg_wrapper import telegram_voice
from iacecil.controllers.personalidades import pave
from iacecil.controllers.personalidades.pacume.furhat_handlers import (
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
)
from iacecil.controllers.amazon_boto import get_audio

async def fala_callback(message: types.Message, audio_text: str) -> None:
    """Converte para audio o texto de auido_text"""
    await message_callback(message, ['fala', message.chat.type])
    dispatcher: Dispatcher = Dispatcher.get_current()
    command: Union[types.Message, None] = None
    opus_file: Union[str, None] = None
    try:
        vorbis_file: Union[object, None] = await get_audio(audio_text)
        opus_file: Union[object, None] = await telegram_voice(vorbis_file)
        if opus_file is not None:
            with open(opus_file, 'rb') as audio:
                command: Union[types.Message, None
                    ] = await message.reply_voice(audio)
            if command is not None:
                await command_callback(command, ['fala', message.chat.type])
    except Exception as exception:
        await error_callback(
            "Problema tentando mandar audio",
            message,
            exception,
            ['error', 'fala', message.chat.type],
        )
    finally:
        if opus_file is not None:
            os.remove(opus_file)

async def fala_wrapper(message):
    audio_text = message.get_args()
    if audio_text not in [None, '', ' ']:
        await fala_callback(message, audio_text)
async def fala_reply_wrapper(message):
    audio_text = ''
    reply_args = message.reply_to_message.get_args()
    message_args = message.get_args()
    if reply_args not in [None, '', ' ']:
        audio_text = audio_text + reply_args
    elif message.reply_to_message.text not in [None, '', ' ']:
        audio_text = audio_text + message.reply_to_message.text
    if message_args not in [None, '', ' ']:
        audio_text = audio_text + message_args
    if audio_text not in [None, '', ' ']:
        await fala_callback(message, audio_text)
async def fala_nl_wrapper(message):
    audio_text = ''.join(message.text.split(' ')[1:])
    if audio_text not in [None, '', ' ']:
        await fala_callback(message, audio_text)

async def add_handlers(dispatcher):
    try:
        ## Text to speech as a telegram voice message
        ## (pt-BR: áudio de zap)
        triggers = ['fala', 'speak', 'say', 'diz']
        ## Natural language trigger
        dispatcher.register_message_handler(
            fala_nl_wrapper,
            filters.Text(startswith = triggers, ignore_case = True),
            is_reply_to_id = dispatcher.bot.id,
            content_types = types.ContentTypes.TEXT,
        )
        ## Uses the text from a replied message with /fala
        dispatcher.register_message_handler(
            fala_reply_wrapper,
            is_reply = True,
            commands = triggers,
            content_types = types.ContentTypes.TEXT,
        )
        ## Uses provided text in arguments or croak
        dispatcher.register_message_handler(
            fala_wrapper,
            commands = triggers,
            content_types = types.ContentTypes.TEXT,
        )
    except Exception as e:
        logger.exception(e)
        raise
