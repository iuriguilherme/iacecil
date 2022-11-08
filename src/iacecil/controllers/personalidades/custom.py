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

from aiogram import Dispatcher

try:
    from instance.personalidades.custom import add_instance_handlers
except Exception as e:
    logger.info(f"""add_instance_handlers em instance não encontrada para \
{__name__}""")
    # ~ logger.exception(e)

async def add_handlers(dispatcher: Dispatcher) -> None:
    """
    Registers instance custom aiogram handlers
    of custom configured personalidade
    This is meant for external software using ia.cecil
    """
    try:
        await add_instance_handlers(dispatcher)
    except Exception as e:
        logger.error("""Could not register custom instance handlers, have \
you RTFM?""")
        logger.exception(e)
