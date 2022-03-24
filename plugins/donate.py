# vim:fileencoding=utf-8
#  Plugin donate para ia.cecil: Indica formas de receber doações
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
logger = logging.getLogger(__name__)

from aiogram.utils.markdown import code, escape_md
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Mostra opções de doação
        @dispatcher.message_handler(
            commands = ['donate', 'doar'],
        )
        async def donate_callback(message):
            await message_callback(message, ['donate',
                message.chat.type])
            command = await message.reply(
                text = '\n'.join([u"""List of addresses to donate for t\
he bot developers:""", *[''.join([f'{k}', escape_md(': '), code(f'{v}')]
                    ) for k, v in dispatcher.bot.config['info'][
                    'donate']['crypto'].items()], '',
                    u"Missing one? Send /feedback",]),
                parse_mode = "MarkdownV2",
            )
            await command_callback(command, ['donate',
                message.chat.type])
    except Exception as exception:
        raise
