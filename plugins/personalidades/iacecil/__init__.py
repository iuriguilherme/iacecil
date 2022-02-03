# vim:fileencoding=utf-8
#  Plugin personalidades para ia.cecil: Robô também é gente?
#  Copyleft (C) 2020-2022 Iuri Guilherme
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

### Personalidade fofa
import random
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from plugins.personalidades.default import start, help, welcome, info

## TODO Sentenças impróprias para publicar no Github por razões diversas
try:
    from instance.personalidades.iacecil import random_texts
except:
    from plugins.personalidades.iacecil import random_texts

async def add_handlers(dispatcher):
    ## Comando /info herdado da personalidade padrão
    @dispatcher.message_handler(
        commands = ['info'],
    )
    async def info_callback(message):
        await message_callback(message, [
            'info',
            dispatcher.bot.get('personalidade', 'iacecil'),
            message.chat.type,
        ])
        command = await message.reply(await info(dispatcher.bot.info))
        await command_callback(command, [
            'info',
            dispatcher.bot.get('personalidade', 'iacecil'),
            message.chat.type,
        ])
    @dispatcher.message_handler(
        commands = ['fofa'],
    )
    async def fofice_callback(message):
        await message_callback(message, [
            'fofice',
            dispatcher.bot.get('personalidade', 'iacecil'),
            message.chat.type,
        ])
        command = await message.reply(random_texts.fofices())
        await command_callback(command, [
            'info',
            dispatcher.bot.get('personalidade', 'iacecil'),
            message.chat.type,
        ])
