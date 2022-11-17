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

import io
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
from iacecil.controllers.amazon_boto import get_audio
from iacecil.controllers.ffmpeg_wrapper import telegram_voice
from iacecil.controllers.personalidades import pave
from iacecil.controllers.personalidades.pacume.furhat_handlers import (
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
)

async def fala_callback(
    message: types.Message,
    audio_text: str,
    text_type: str = 'text',
    engine: Union[str, None] = None,
    **kwargs,
) -> None:
    """Converte para audio o texto de audio_text"""
    await message_callback(message, ['fala', message.chat.type])
    dispatcher: Dispatcher = Dispatcher.get_current()
    command: Union[types.Message, None] = None
    opus_file: Union[str, None] = None
    try:
        vorbis_file: Union[object, None] = await get_audio(
            Text = audio_text,
            TextType = text_type,
            Engine = engine,
        )
        opus_file: Union[object, None] = await telegram_voice(vorbis_file)
        if opus_file is not None:
            with open(opus_file, 'rb') as audio:
                command: Union[types.Message, None
                    ] = await message.reply_voice(audio)
            if command is not None:
                await command_callback(command, ['fala', message.chat.type])
    except Exception as e:
        await error_callback(
            "Problema tentando mandar audio",
            message,
            e,
            ['error', 'exception', 'fala', message.chat.type],
        )
    finally:
        if opus_file is not None:
            os.remove(opus_file)

async def fala_wrapper(message: types.Message) -> None:
    """Tenta converter o texto se tiver texto na mensagem"""
    audio_text: Union[None, str] = message.get_args()
    if audio_text not in [None, '', ' ']:
        await fala_callback(message, audio_text)

async def fala_reply_wrapper(message: types.Message) -> None:
    """Tenta converter o texto da resposta se tiver texto"""
    audio_text: str = ''
    reply_args: Union[None, str] = message.reply_to_message.get_args()
    message_args: Union[None, str] = message.get_args()
    if reply_args not in [None, '', ' ']:
        audio_text: str = audio_text + reply_args
    elif message.reply_to_message.text not in [None, '', ' ']:
        audio_text: str = audio_text + message.reply_to_message.text
    if message_args not in [None, '', ' ']:
        audio_text: str = audio_text + message_args
    if audio_text not in [None, '', ' ']:
        await fala_callback(message, audio_text)

async def fala_nl_wrapper(message: types.Message) -> None:
    """Tenta converter o texto do comando natural"""
    try:
        audio_text: str = ''.join(message.text.split(' ')[1:])
        if audio_text not in [None, '', ' ']:
            await fala_callback(message, audio_text)
    except Exception as e:
        await error_callback(
            "Problema tentando achar texto por comando natural",
            message,
            e,
            ['error', 'exception', 'fala', 'nl', message.chat.type],
        )

async def ssml_wrapper(message: types.Message, *args, **kwargs) -> None:
    """Tenta reproduzir um arquivo SSML"""
    dispatcher: Dispatcher = Dispatcher.get_current()
    audio_text: Union[io.StringIO, None] = io.StringIO()
    try:
        _file: types.File = await dispatcher.bot.get_file(
            message.document.file_id)
        audio_text: Union[io.StringIO, None] = \
            await dispatcher.bot.download_file(_file.file_path)
        await fala_callback(message, audio_text.read().decode(), 'ssml',
            'standard')
    except Exception as e:
        logger.exception(e)
        await error_callback(
            "Problema tentando falar arquivo SSML",
            message,
            e,
            ['error', 'exception', 'fala', 'ssml', message.chat.type],
        )
    finally:
        if audio_text:
            audio_text.close()

async def ssml_text_callback(*args, **kwargs) -> None:
    """Text filter callback"""
    await ssml_wrapper(*args, **kwargs)

async def ssml_command_callback(*args, **kwargs) -> None:
    """Command filter callback"""
    await ssml_wrapper(*args, **kwargs)

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register aiogram handlers"""
    try:
        ## Text to speech as a telegram voice message
        ## (pt-BR: áudio de zap)
        triggers: list[str] = ['fala', 'speak', 'say', 'diz']
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
        ## SSML
        dispatcher.register_message_handler(
            ssml_text_callback,
            filters.Text(startswith = triggers, ignore_case = True),
            content_types = types.ContentTypes.DOCUMENT,
        )
        dispatcher.register_message_handler(
            ssml_command_callback,
            filters.Command(triggers, ignore_caption = False),
            content_types = types.ContentTypes.DOCUMENT,
        )
    except Exception as e:
        logger.exception(e)
        raise
