# vim:fileencoding=utf-8
#  Plugin ytdl para ia.cecil: Devolve vídeo/áudio a partir de link.
#  Copyleft (C) 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

import os, random, uuid, validators, youtube_dl
from tempfile import gettempdir
from aiogram.utils.markdown import escape_md, pre
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

async def baixar(url):
    video_file_name = os.path.join(gettempdir(), "ic.{}.mp4".format(
        uuid.uuid4()))
    options = {
        'outtmpl' : video_file_name,
        #'format': 'worstvideo+worstaudio/worst',
        'format': 'mp4',
        #'merge_output_format': 'mp4',
        #'postprocessor_args': [
            #'-an',
            #'-c:v libx264',
            #'-crf 26',
            #'-vf scale=640:-1',
        #],
    }
    ## FIXME Blocking!
    youtube_dl.YoutubeDL(options).download([url])
    return video_file_name

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
                video_file = await baixar(url)
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
                        await message.reply_video(
                            video = video,
                            caption = url,
                        )
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
                if os.path.exists(video_file):
                    os.remove(video_file)
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
    except Exception as exception:
        raise
