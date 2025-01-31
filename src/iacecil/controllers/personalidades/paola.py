"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2025 Iuri Guilherme <https://iuri.neocities.org/>

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
logger: logging.Logger = logging.getLogger(__name__)

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
    from instance.personalidades.paola import random_texts
except Exception as e:
    logger.debug(f"random_texts em instance não encontrada para {__name__}")
    # ~ logger.exception(e)
    try:
        from . import random_texts
    except Exception as e1:
        logger.debug(f"no random_texts at all for {__name__}")
        # ~ logger.exception(e1)

async def add_handlers(dispatcher) -> None:
    """Aiogram Handlers"""
    try:
        await add_default_handlers(dispatcher)
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

async def croak(*args, **kwargs) -> str:
    """Mensagem padrão pra todo e qualqeur problema, herança da Gamboa"""
    return """Desculpa eu não poder falar contigo agora, o meu programador tá \
mexendo no meu código e eu tenho medo de me perder."""

async def furhat_startswith_iterations(*args, **kwargs) -> list:
    """Gatilhos para interações que comecem com uma das palavras"""
    return (await furhat_startswith_iterations_default()) + [
        Iteration(
            text = subtext,
            callback = croak,
        ) for subtext in [
            "oi",
            "olá",
            "alô",
            "Oi",
            "Oi.",
            "Olá",
            "Alô",
        ]
    ]

async def furhat_endswith_iterations(*args, **kwargs) -> list:
    """Gatilhos para interações que terminem com uma das palavras"""
    return (await furhat_endswith_iterations_default())

async def furhat_contains_iterations(*args, **kwargs) -> list:
    """Gatilhos para interações que contenham uma das palavras"""
    return (await furhat_contains_iterations_default()) + [
        Iteration(text = subtext, callback = croak,
            ) for subtext in [
                'alexa',
                'lexa',
                'siri',
                'google',
            ]
    ]
