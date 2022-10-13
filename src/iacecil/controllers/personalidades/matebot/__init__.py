"""
Personalidades para ia.cecil: Robô também é gente?

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

### Personalidade padrão do @mate_obot
from ...aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from ....models import Iteration
from ..default import (
    start,
    help,
    info,
    portaria,
    welcome,
    furhat_contains_iterations as furhat_contains_iterations_default,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
    add_handlers as add_default_handlers,
)

try:
    from instance.personalidades.matebot import random_texts
except Exception as e:
    logger.info(f"random_texts em instance não encontrada para {__name__}")
    logger.exception(e)
    from . import random_texts

async def add_handlers(dispatcher):
    await add_default_handlers(dispatcher)
    ## BOFH
    @dispatcher.message_handler(
        commands = ['bofh'],
    )
    async def bofh_callback(message):
        await message_callback(message, ['personalidades', 'matebot',
            'bofh', message.chat.type])
        command = await message.reply(await random_texts.bofh())
        await command_callback(command, ['personalidades', 'matebot',
            'bofh', message.chat.type])

## Furhat
async def furhat_desculpa(config, message):
    return await random_texts.bofh()

async def furhat_contains_iterations():
    return (await furhat_contains_iterations_default()) + [
        Iteration(text = subtext, callback = furhat_desculpa,
            ) for subtext in [
                'não tá funcionando',
                'internet tá ruim',
                'wi-fi tá ruim',
                'not working',
            ]
    ]
