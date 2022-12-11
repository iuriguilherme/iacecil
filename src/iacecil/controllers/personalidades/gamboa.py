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

### Gamboa RD Summit
# ~ from ...aiogram_bot.callbacks import (
    # ~ command_callback,
    # ~ message_callback,
# ~ )
from ...models import Iteration
from .default import (
    start,
    help,
    info,
    portaria,
    welcome,
    furhat_contains_iterations as furhat_contains_iterations_default,
    furhat_endswith_iterations as furhat_endswith_iterations_default,
    furhat_startswith_iterations as furhat_startswith_iterations_default,
    add_handlers as add_default_handlers,
)

try:
    from instance.personalidades.gamboa import random_texts
except Exception as e:
    logger.debug(f"random_texts em instance não encontrada para {__name__}")
    # ~ logger.exception(e)
    try:
        from . import random_texts
    except Exception as e1:
        logger.debug(f"no random_texts at all for {__name__}")
        # ~ logger.exception(e1)

async def add_handlers(dispatcher):
    try:
        await add_default_handlers(dispatcher)
        # ~ ## BOFH
        # ~ @dispatcher.message_handler(
            # ~ commands = ['bofh'],
        # ~ )
        # ~ async def bofh_callback(message):
            # ~ await message_callback(message, ['personalidades', 'matebot',
                # ~ 'bofh', message.chat.type])
            # ~ command = await message.reply(await random_texts.bofh())
            # ~ await command_callback(command, ['personalidades', 'matebot',
                # ~ 'bofh', message.chat.type])
                
    except Exception as e:
        logger.exception(e)

## Furhat
# ~ from ..furhat_bot.remote_api import (
    # ~ get_furhat,
    # ~ get_voices,
    # ~ set_face,
    # ~ set_led,
    # ~ set_voice,
    # ~ do_attend_id,
    # ~ do_attend_location,
    # ~ do_attend_user,
    # ~ do_listen,
    # ~ do_say_text,
    # ~ do_say_url,
    # ~ block_do_listen,
    # ~ block_do_say_text,
    # ~ block_do_say_url,
# ~ )
# ~ from ..furhat_bot.controllers.furhat_controllers import (
    # ~ blue_speak,
    # ~ change_voice,
    # ~ led_blank,
    # ~ led_blue,
    # ~ led_green,
    # ~ led_red,
    # ~ led_white,
    # ~ shutup,
# ~ )

async def borogodo_foradoar(config, message) -> str:
    return """Desculpa eu não poder falar contigo agora, o meu programador tá \
mexendo no meu código e eu tenho medo de me perder."""

async def furhat_desculpa(config, message) -> str:
    return "É, eu vi que a internet aqui tá ruim mesmo"

async def furhat_startswith_iterations() -> list:
    return (await furhat_startswith_iterations_default()) + [
        Iteration(
            text = subtext,
            callback = borogodo_foradoar,
        ) for subtext in [
            "oi",
            "olá",
            "alô",
            "Oi",
            "Oi.",
            "Olá",
            "Alô",
        ]
    # ~ ] + [
        # ~ Iteration(text = "entrevista", callback = borogodo_entrevista),
    ]

async def furhat_endswith_iterations() -> list:
    return (await furhat_endswith_iterations_default())

async def furhat_contains_iterations() -> list:
    return (await furhat_contains_iterations_default()) + [
        Iteration(text = subtext, callback = furhat_desculpa,
            ) for subtext in [
                'não tá funcionando',
                'internet tá ruim',
                'wi-fi tá ruim',
                'not working',
            ]
    ]
