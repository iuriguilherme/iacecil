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
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

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
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
)
from iacecil.controllers.ffmpeg_wrapper import telegram_voice
from plugins.personalidades import pave
from plugins.personalidades.pacume.furhat_handlers import (
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
)
from plugins.amazon_boto import get_audio

async def add_handlers(dispatcher):
    ## Transforma texto em áudio
    @dispatcher.message_handler(
        commands = ['fala'],
    )
    async def fala_callback(message):
        await message_callback(message, ['fala', message.chat.type])
        command = None
        opus_file = None
        try:
            if message.reply_to_message:
                audio_text = message.reply_to_message.text
            else:
                audio_text = message.get_args()
            if audio_text is not None and audio_text != '':
                vorbis_file = await get_audio(
                    audio_text,
                    Engine = dispatcher.bot.config['furhat'][
                        'synthesizer']['amazon']['engine'],
                    VoiceId = dispathcer.bot.config['furhat']['voice'],
                )
                opus_file = await telegram_voice(vorbis_file)
                if opus_file is not None:
                    with open(opus_file, 'rb') as audio:
                        command = await message.reply_voice(audio)
                    if command is not None:
                        await command_callback(command, ['fala',
                            message.chat.type])
        except Exception as exception:
            await error_callback(
                u"Problema tentando mandar audio",
                message,
                exception,
                ['error', 'fala', message.chat.type],
            )
        finally:
            if opus_file is not None:
                os.remove(opus_file)
