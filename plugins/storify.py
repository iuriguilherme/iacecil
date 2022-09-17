# vim:fileencoding=utf-8
#  Plugin storify para ia.cecil: Splits videos
#  Copyleft (C) 2022-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
logger = logging.getLogger(__name__)

import glob, os, uuid
from datetime import timedelta
from tempfile import gettempdir
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
    exception_callback,
)
from iacecil.controllers.ffmpeg_wrapper import storify

async def storify_callback(
    message: types.Message,
    h: str = '00',
    m: str = '00',
    s: str = '15',
    **kwargs,
):
    dispatcher = Dispatcher.get_current()
    videos = []
    input_file = None
    try:
        file_id = message.video.file_id
        await message.reply(f"""Peraí que eu vou cortar o vídeo em pedaços \
de {':'.join([h, m, s])} e já te mando...""")
        file_object = await dispatcher.bot.get_file(file_id)
        file_path = file_object.file_path
        input_file = os.path.join(gettempdir(), "ic.{}.mp4".format(
            uuid.uuid4()))
        await dispatcher.bot.download_file(file_path, input_file)
        videos = await storify(input_file, h, m, s)
        if videos is not None:
            for index, video in enumerate(sorted(videos)):
                with open(video, 'rb') as open_video:
                    await message.reply_video(open_video,
                        caption = u"({}/{})".format(str(index+1),
                        str(len(videos))))
        else:
            await message.reply(f"""Não consegui cortar o vídeo por problemas \
técnicos. Já avisei o pessoal do desenvolvimento. Se o erro persistir, favor \
avisar os (ir)responsáveis.""")
            await error_callback(
                error = "Erro com ffmpeg, provavelmente problema de codec",
                message = message,
                exception = None,
                descriptions = ['storify', 'ffmpeg', message.chat.type],
            )
    except Exception as exception:
        await message.reply(f"""Não consegui cortar o vídeo. Já avisei \
o pessoal do desenvolvimento e o problema é: {repr(exception)}""")
        await exception_callback(
            exception,
            ['storify', message.chat.type],
        )
    finally:
        if input_file is not None:
            for video_file in glob.glob('.'.join([input_file.split('.')[
                0], '*'])):
                os.remove(video_file)

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Break videos in 15 seconds chunks
        @dispatcher.message_handler(
            filters.ChatTypeFilter('private'),
            content_types = types.ContentTypes.VIDEO,
        )
        async def admin_storify_callback(message: types.Message):
            await message_callback(message, ['storify',
                message.chat.type])
            h, m, s = ('00', '00', '15')
            if message.caption:
                try:
                    h, m, s = str(timedelta(seconds=int(message.caption
                        ))).split(':')
                except ValueError:
                    pass
            if message.get_args() not in [None, '', ' ']:
                try:
                    h, m, s = str(timedelta(seconds=int(
                        message.get_args()))).split(':')
                except ValueError:
                    pass
            await storify_callback(message, h, m, s)
        
        @dispatcher.message_handler(
            is_reply = True,
            commands = ['storify', 'cut', 'instagram', 'ig'],
        )
        async def reply_storify_callback(message: types.Message):
            await message_callback(message, ['storify',
                message.chat.type])
            if message.reply_to_message:
                h, m, s = ('00', '00', '15')
                if message.reply_to_message.caption:
                    try:
                        h, m, s = str(timedelta(seconds=int(
                            message.reply_to_message.caption))).split(
                            ':')
                    except ValueError:
                        pass
                if message.get_args() not in [None, '', ' ']:
                    try:
                        h, m, s = str(timedelta(seconds=int(
                            message.get_args()))).split(':')
                    except ValueError:
                        pass
                await storify_callback(message.reply_to_message, h, m,
                    s)
    except Exception as exception:
        raise
