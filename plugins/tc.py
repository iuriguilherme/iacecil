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

def dice(faces = 6, seed = None, *args, **kwargs) -> int:
    numpy.random.seed(seed)
    return numpy.random.randint(1, faces + 1)

def coord(seed = None, *args, **kwargs) -> float:
    numpy.random.seed(seed)
    return numpy.random.rand()

async def add_handlers(dispatcher):
    """
    Registra handlers em um Aiogram Dispatcher caso este plugin esteja
    habilitado.
    """
    try:
        ## Rola um dado
        @dispatcher.message_handler(
            commands = ['dice', 'dado', 'd'],
        )
        async def dice_callback(message):
            """
            Retorna um valor pseudo aleatório de uma face de um dado com 
            tantos lados quantos o primeiro argumento. Padrão: 6
            """
            await message_callback(message, ['tc', 'dice', message.chat.type])
            faces = 6
            try:
                if message.get_args() not in [None, '', ' ', 0]:
                    faces = int(message.get_args())
                    if not faces > 0:
                        raise ValueError()
            except ValueError:
                pass
                # ~ await message.reply(f"""{message.get_args()} não é um \
# ~ número de faces de um dado válido, vou usar um dado de seis faces normal.\
# ~ """)
            command = await message.reply(dice(faces))
            await command_callback(command, ['tc', 'dice', message.chat.type])
    except Exception as exception:
        raise
