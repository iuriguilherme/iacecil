# vim:fileencoding=utf-8
"""Plugin tc para ia.cecil"""
#  Copyleft (C) 2022 Iuri Guilherme <https://iuri.neocities.org/>
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
#  

import logging
logger = logging.getLogger(__name__)

import numpy
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

def dice(faces = 6, *args, **kwargs) -> int:
    return numpy.random.randint(1, facets + 1)

def coord(seed = None, *args, **kwargs) -> float:
    if seed is not None:
        numpy.random.seed(seed)
    return numpy.random.rand()

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Rola um dado
        @dispatcher.message_handler(
            commands = ['dice', 'dado', 'd'],
        )
        async def dice_callback(message):
            await message_callback(message, ['tc', 'dice', message.chat.type])
            faces = 6
            try:
                faces = int(message.get_args())
                if not faces > 0:
                    raise ValueError()
            except ValueError:
                await message.reply(f"""{message.get_args()} não é um número \
de faces de um dado válido, vou usar um dado de seis faces normal.""")
            command = await message.reply(dado(faces))
            await command_callback(command, ['tc', 'dice', message.chat.type])
    except Exception as exception:
        raise
