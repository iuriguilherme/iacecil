# vim:fileencoding=utf-8
#  Plugin qr para ia.cecil: Gera qr code a partir de texto.
#  Copyleft (C) 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>
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
logger = logging.getLogger('plugins.qr')
import os, pyqrcode, tempfile
from aiogram.utils.markdown import pre
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

def create_qrcode(text):
    photo = tempfile.mkstemp(suffix='.png')
    qrcode = pyqrcode.create(str(text), version=10)
    qrcode.png(photo[1], scale=6)
    return {
        'photo': photo, 
        'text': str(text),
    }

## Aiogram
async def add_handlers(dispatcher):
    ## Envia qr code a partir de texto
    @dispatcher.message_handler(
        commands = ['qr', 'qrcode'],
    )
    async def qr_callback(message):
        await message_callback(message, ['qr', message.chat.type])
        if message.get_args():
            try:
                photo = open(str(
                    create_qrcode(message.get_args())['photo'][1],
                ), 'rb')
                command = await message.reply_photo(
                    photo = photo,
                    caption = message.get_args(),
                )
            except Exception as exception:
                await error_callback(
                    u"Falha ao gerar qr code",
                    message,
                    exception,
                    ['command', 'qr', 'exception'],
                )
                command = await message.reply(u"""Não consegui gerar qr\
 code, avisei o pessoal do desenvolvimento...""")
        else:
            command = await message.reply(pre(u"""\nO comando {comando}\
 serve pra gerar um qr code a partir de um texto. Digite "{comando} tex\
to" para usar (dê um espaço entre o comando e o texto). Por exemplo, pa\
ra gerar o qr code de um rick roll:\n\n{comando} https://youtube.com/wa\
tch?v=dQw4w9WgXcQ""".format(comando = message.get_command())),
                parse_mode = "MarkdownV2",
            )
        await command_callback(command, ['qr', message.chat.type])
