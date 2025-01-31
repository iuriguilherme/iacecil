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
logger = logging.getLogger(__name__)

from aiogram import (
    Bot,
    Dispatcher,
    types,
)
from typing import Union
from ..aiogram_bot.callbacks import (
    error_callback,
    exception_callback,
)
from ...models import Iteration

## FIXME use importlib.import_module instead
from . import (
    cryptoforex,
    custom,
    default,
    gamboa,
    iacecil,
    matebot,
    metarec,
    pacume,
    paola,
    pasoca,
    pave,
)
## TODO: remover isto, não é necessário. O módulo que tentar importar 
## personalidade que não existe deve tratar a exceção.
personalidades: dict[str, object] = {'default': default}
try:
    personalidades: dict[str, object] = {
        'cryptoforex': cryptoforex,
        'custom': custom,
        'default': default,
        'iacecil': iacecil,
        'matebot': matebot,
        'metarec': metarec,
        'pacume': pacume,
        'paola': paola,
        'pasoca': pasoca,
        'pave': pave,
        'gamboa': gamboa,
    }
except Exception as e:
    logger.error("Problema tentando carregar as personalidades")
    logger.exception(e)

## TODO: enviar o aiogram.Dispatcher ao invés de aiogram.Dispatcher.Bot
async def gerar_comando(
    command: str,
    bot: Bot,
    message: types.Message,
) -> Union[types.Message, None]:
    """Returns aiogram.types.Message from given personalidade controller"""
    try:
        return await getattr(
            personalidades.get(bot.config.personalidade, 'default'),
            command,
        )(message)
    except AttributeError as e:
        logger.exception(e)
        try:
            return await getattr(personalidades.get(default), command)(message)
        except Exception as e1:
            logger.exception(e1)
            await error_callback(
                "Erro tentando achar comando em personalidade padrão",
                message,
                e1,
                [
                    'personalidades',
                    bot.config.personalidade,
                    'gerarComando',
                ],
            )
    except Exception as e:
        logger.exception(e)
        try:
            await error_callback(
                "Erro tentando achar comando em personalidade",
                message,
                e,
                [
                    'personalidades',
                    bot.config.personalidade,
                    'gerarComando',
                ],
            )
        except Exception as e1:
            logger.exception(e1)
            await error_callback(
                "Erro tentando obter personalidade a partir de configuração",
                message,
                e1,
                ['personalidades', 'gerarComando'],
            )
    return None

async def gerar_texto(
    command: str,
    bot: Bot,
    message: types.Message,
) -> Union[str, None]:
    """Returns generated text from given personalidade"""
    try:
        return await getattr(
            personalidades.get(bot.config.personalidade, 'default'),
            command,
        )(message)
    except AttributeError as e:
        logger.exception(e)
        try:
            return await getattr(personalidades['default'], command)(message)
        except Exception as e1:
            logger.exception(e1)
            await error_callback(
                "Erro tentando achar comando em personalidade",
                message,
                e1,
                [
                    'personalidades',
                    bot.config.personalidade,
                    'gerarTexto',
                ],
            )
    except Exception as e:
        logger.exception(e)
        try:
            await error_callback(
                "Erro tentando achar comando em personalidade",
                message,
                e,
                [
                    'personalidades',
                    bot.config.personalidade,
                    'gerarTexto',
                ],
            )
        except Exception as e1:
            logger.exception(e1)
            await error_callback(
                "Erro tentando obter personalidade a partir de configuração",
                message,
                e1,
                ['personalidades', 'gerarTexto'],
            )
    return None

async def add_handlers(dispatcher: Dispatcher) -> None:
    """
    Register aiogram handlers to aiogram.Dispatcher
    from configured personalidade
    """
    try:
        await getattr(
            personalidades.get(dispatcher.config.personalidade, 'default'),
            'add_handlers',
        )(dispatcher)
    except AttributeError as e:
        logger.exception(e)
        await getattr(personalidades['default'], 'add_handlers')(dispatcher)
    except Exception as e:
        logger.exception(e)
        await exception_callback(e, ['personalidades', 'add_handlers'])

async def generate_command_furhat(
    config: object,
    command: str,
    message: types.Message,
) -> Union[types.Message, None]:
    """Returns aiogram.types.Message from furhat controller"""
    try:
        return getattr(
            personalidades.get(config.personalidade, 'default'),
            'furhat_' + command,
        )
    except AttributeError as e:
        logger.exception(e)
        try:
            return getattr(personalidades['default'], 'furhat_' + command)
        except Exception as e1:
            logger.warning("Erro tentando achar comando em personalidade")
            logger.exception(e1)
    except Exception as e:
        logger.warning("Erro tentando achar comando em personalidade")
        logger.exception(e)
    return None

async def generate_text_furhat(
    config: object,
    command: str,
    message: types.Message,
) -> Union[types.Message, None]:
    """Returns aiogram.types.Message from furhat controller"""
    # ~ command = message.split(' ')[0]
    try:
        return await getattr(
            personalidades.get(config.personalidade, 'default'),
            'furhat_' + command,
        )(config, message)
    except AttributeError as e:
        logger.exception(e)
        try:
            return await getattr(
                personalidades['default'],
                'furhat_' + command,
            )(config, message)
        except Exception as e1:
            logger.warning("Erro tentando achar comando em personalidade")
            logger.exception(e1)
    except Exception as e:
        logger.warning("Erro tentando achar comando em personalidade")
        logger.exception(e)
    return None

async def get_furhat_startswith_handlers(
    persona: Union[Dispatcher, Bot],
) -> Union[Iteration, None]:
    try:
        return await getattr(
            personalidades.get(persona, 'default'),
            'furhat_startswith_iterations',
        )()
    except AttributeError as e:
        logger.exception(e)
        return [Iteration()]
    except Exception as e:
        logger.exception(e)
        raise
    return None

async def get_furhat_endswith_handlers(
    persona: Union[Dispatcher, Bot],
) -> Union[Iteration, None]:
    try:
        return await getattr(
            personalidades.get(persona, 'default'),
            'furhat_endswith_iterations',
        )()
    except AttributeError as e:
        logger.exception(e)
        return [Iteration()]
    except Exception as e:
        logger.exception(e)
        raise
    return None

async def get_furhat_contains_handlers(
    persona: Union[Dispatcher, Bot],
) -> Union[Iteration, None]:
    try:
        return await getattr(
            personalidades.get(persona, 'default'),
            'furhat_contains_iterations',
        )()
    except AttributeError as e:
        logger.exception(e)
        return [Iteration()]
    except Exception as e:
        logger.exception(e)
        raise
    return None
