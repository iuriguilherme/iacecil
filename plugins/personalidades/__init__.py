# vim:fileencoding=utf-8
#  Plugin personalidades para ia.cecil: Robô também é gente?
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

from aiogram import types
from iacecil.controllers.aiogram_bot.callbacks import (
    error_callback,
    exception_callback,
)
from iacecil.models import Iteration
from plugins.personalidades import (
    cryptoforex,
    default,
    iacecil,
    matebot,
    metarec,
    pacume,
    pave,
)

personalidades = {'default': default}
personalidades = {
    'cryptoforex': cryptoforex,
    'default': default,
    'iacecil': iacecil,
    'matebot': matebot,
    'metarec': metarec,
    'pacume': pacume,
    'pave': pave,
}

## Aiogram
async def gerar_comando(command, bot, message):
    try:
        # ~ return await getattr(globals()[bot.config['info'].get(
            # ~ 'personalidade', 'default')], command)(message)
        return await getattr(personalidades.get(bot.config['info'].get(
            'personalidade', 'default'), 'default'), command)(message)
    except AttributeError as exception:
        logger.info(repr(exception))
        try:
            # ~ return await getattr(globals()['default'], command)(
                # ~ message)
            return await getattr(personalidades['default'], command)(
                message)
        except Exception as exception:
            await error_callback(
                u"Erro tentando achar comando em personalidade",
                message, exception, ['personalidades', bot.config[
                'info'].get('personalidade', 'default'), 'gerarComando',
                ],
            )
    except Exception as exception:
        await error_callback(
            u"Erro tentando achar comando em personalidade",
            message, exception, ['personalidades', bot.config['info'
            ].get('personalidade', 'default'), 'gerarComando'],
        )

async def gerar_texto(command, bot, message):
    try:
        # ~ return await getattr(globals()[bot.config['info'].get(
            # ~ 'personalidade', 'default')],
            # ~ command)(message)
        return await getattr(personalidades.get(bot.config['info'].get(
            'personalidade', 'default'), 'default'), command)(message)
    except AttributeError as exception:
        logger.info(repr(exception))
        try:
            # ~ return await getattr(globals()['default'], command)(
                # ~ message)
            return await getattr(personalidades['default'], command)(
                message)
        except Exception as exception:
            await error_callback(
                u"Erro tentando achar comando em personalidade",
                message, exception, ['personalidades', bot.config[
                'info'].get('personalidade', 'default'), 'gerarTexto'],
            )
    except Exception as exception:
        await error_callback(
            u"Erro tentando achar comando em personalidade",
            message, exception, ['personalidades', bot.config['info'
            ].get('personalidade', 'default'), 'gerarTexto'],
        )

async def add_handlers(dispatcher):
    try:
        # ~ await getattr(globals()[dispatcher.bot.config['info'].get(
            # ~ 'personalidade', 'default')], 'add_handlers')(
            # ~ dispatcher)
        await getattr(personalidades.get(dispatcher.bot.config['info'
            ].get('personalidade', 'default'), 'default'),
            'add_handlers')(dispatcher)
    except AttributeError as exception:
        logger.info(repr(exception))
        # ~ await getattr(globals()['default'], 'add_handlers')(
            # ~ dispatcher)
        await getattr(personalidades['default'], 'add_handlers')(
            dispatcher)
    except Exception as exception:
        logger.warning(repr(exception))
        await exception_callback(exception, ['personalidades',
            'add_handlers'])

async def generate_command_furhat(config, command, message):
    try:
        return getattr(personalidades.get(config['info'
            ].get('personalidade', 'default'), 'default'),
            'furhat_' + command,
        )
    except AttributeError as exception:
        logger.info(repr(exception))
        try:
            return getattr(personalidades['default'],
                'furhat_' + command,
            )
        except Exception as exception:
            logger.warning(u"""Erro tentando achar comando em personali\
dade: {}""".format(repr(exception)))
    except Exception as exception:
        logger.warning(u"""Erro tentando achar comando em personalidade\
""".format(repr(exception)))

async def generate_text_furhat(config, command, message):
    # ~ command = message.split(' ')[0]
    try:
        return await getattr(
            personalidades.get(config['info'].get(
            'personalidade', 'default'), 'default'),
            'furhat_' + command,
        )(config, message)
    except AttributeError as exception:
        logger.info(repr(exception))
        try:
            return await getattr(personalidades['default'],
                'furhat_' + command)(config, message)
        except Exception as exception:
            logger.warning(u"""Erro tentando achar comando em personali\
dade""".format(repr(exception)))
    except Exception as exception:
        logger.warning(u"""Erro tentando achar comando em personalidade\
""".format(repr(exception)))

async def get_furhat_startswith_handlers(persona):
    try:
        return await getattr(
            personalidades.get(persona, 'default'),
            'furhat_startswith_iterations',
        )()
    except AttributeError as exception:
        return [Iteration()]
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_furhat_endswith_handlers(persona):
    try:
        return await getattr(
            personalidades.get(persona, 'default'),
            'furhat_endswith_iterations',
        )()
    except AttributeError as exception:
        return [Iteration()]
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_furhat_contains_handlers(persona):
    try:
        return await getattr(
            personalidades.get(persona, 'default'),
            'furhat_contains_iterations',
        )()
    except AttributeError as exception:
        return [Iteration()]
    except Exception as exception:
        logger.warning(repr(exception))
        raise
