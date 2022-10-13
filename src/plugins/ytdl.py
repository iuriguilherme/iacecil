"""
Plugin ytdl para ia.cecil: Devolve vídeo/áudio a partir de link.

ia.cecil

Copyleft 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>

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
import random
import uuid
import validators
import youtube_dl
import yt_dlp
from aiogram.utils.markdown import escape_md, pre
from contextlib import redirect_stdout
from tempfile import gettempdir
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

async def baixar(url, extension = 'mp4', **kwargs):
    try:
        video_file_name = os.path.join(gettempdir(), "ic.{}.{}".format(
            uuid.uuid4(), extension))
        options = {
            'outtmpl' : video_file_name,
            #'format': 'worstvideo+worstaudio/worst',
            # ~ 'format': 'mp4',
            # ~ 'max_filesize': 1,
            #'merge_output_format': 'mp4',
            #'postprocessor_args': [
                #'-an',
                #'-c:v libx264',
                #'-crf 26',
                #'-vf scale=640:-1',
            #],
            **kwargs,
        }
        ## FIXME Blocking!
        ## This is always blocking in upstream:
        ## https://github.com/ytdl-org/youtube-dl/issues/30815
        ## https://github.com/yt-dlp/yt-dlp/issues/3298
        ## https://github.com/yt-dlp/yt-dlp/issues/1918
        # ~ youtube_dl.YoutubeDL(options).download([url])
        yt_dlp.YoutubeDL(options).download([url])
        return video_file_name
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def ytdl(dispatcher, message):
        url = None
        command = u"Não deu certo..."
        ## Será que é link?
        if message.entities is not None:
            for entity in message.entities:
                if entity['type'] == "url":
                    url =  message.text[entity['offset']:entity[
                        'length'] + entity['offset']]
        if not url and message.reply_to_message is not None:
            for entity in message.reply_to_message.entities:
                if entity['type'] == "url":
                    url = message.reply_to_message.text[entity[
                        'offset']:entity['length'] + entity['offset']]
        if url and validators.url(url):
            pass
        else:
            url = None
        if url:
            video_file = None
            try:
                with redirect_stdout(io.StringIO()) as f:
                    await baixar(url, format = 'mp4', max_filesize = 1)
                video_size = f.getvalue().split(
                    '[download] File is larger than max-filesize ('
                    )[1].split(' bytes > 1 bytes). Aborting.'
                    )[0]
                if int(video_size) >= 50000000:
                    command = await message.reply(u"""O vídeo é maior d\
o que o limite de 50mb do telegram e por consequência disto não posso t\
e ajudar hoje. Se no futuro o meu desenvolvedor conseguir dividir o víd\
eo em pedaços, uma das robôs vai avisar no canal: {}""".format(
                        dispatcher.config.telegram['info']['channel']))
                else:
                    video_file = await baixar(url, extension='mp4',
                        format='mp4')
            except Exception as exception:
                await error_callback(
                    u"Erro tentando baixar vídeo",
                    message,
                    exception,
                    ['ytdl'],
                )
                command = await message.reply(
                    escape_md(u"""Não consegui extrair a mídia. Olha o \
que o servidor me disse: """) + pre("{}".format(str(exception))),
                    parse_mode = "MarkdownV2",
                    disable_notification = True,
                )
            video = None
            try:
                if video_file:
                    with open(video_file, 'rb') as video:
                        command = await message.reply_video(
                            video = video,
                            caption = url,
                        )
                    if not command:
                        raise
            except Exception as exception:
                await error_callback(
                    u"Erro tentando subir vídeo",
                    message,
                    exception,
                    ['ytdl', 'exception'],
                )
                command = await message.reply(u"""Não consegui enviar o\
 arquivo. Tentei avisar o pessoal do desenvolvimento...""",
                    disable_notification = True,
                )
            finally:
                if video is not None:
                    video.close()
                try:
                    if video_file is not None and os.path.exists(
                        video_file):
                        os.remove(video_file)
                except Exception as exception:
                    logging.warning(u"probably path doesn't exist")
                    logging.warning(repr(exception))
        else:
            command = await message.reply(escape_md(u"""\nO comando \
{comando} serve pra extrair um vídeo ou áudio de algum site com suporte\
. Este comando usa o youtube-dl. Digite "{comando} url" para usar (dê u\
m espaço entre o comando e o link). Por exemplo, para baixar o vídeo do\
 rick roll:\n\n""".format(comando = message.get_command())) + \
pre(u"""{comando} https://youtube.com/watch?v=dQw4w9WgXcQ""".format(
    comando = message.get_command())) + escape_md(u"""\n\nOu então resp\
onda uma mensagem que tem um link com {comando} na resposta.""".format(
                    comando = message.get_command()
                )),
                parse_mode = "MarkdownV2",
            )
        await command_callback(command, ['ytdl', message.chat.type])

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Extrai vídeo ou áudio de vários serviços
        @dispatcher.message_handler(commands = ['y', 'yt', 'ytdl',
            'youtube', 'baixar', 'video', 'download', 'dl'])
        async def ytdl_callback(message):
            await message_callback(message, ['ytdl', message.chat.type])
            await message.reply(u"ok, vou baixar o vídeo e já te aviso")
            await ytdl(dispatcher, message)
    except Exception as e:
        logger.exception(e)
        raise
