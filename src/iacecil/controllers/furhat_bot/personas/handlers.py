"""
ia.cecil

Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
logger = logging.getLogger(__name__)

from ....models import Callback
from ...personalidades import (
    get_furhat_startswith_handlers,
    get_furhat_endswith_handlers,
    get_furhat_contains_handlers,
)

async def database_iterations_startswith(persona):
    try:
        return await get_furhat_startswith_handlers(persona)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def database_iterations_contains(persona):
    try:
        return await get_furhat_contains_handlers(persona)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def database_iterations_endswith(persona):
    try:
        return await get_furhat_endswith_handlers(persona)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def iterations_startswith(persona):
    ## Should return the text which the sentence should start with to 
    ## trigger, and the callback to be awaited
    return await database_iterations_startswith(persona)

async def iterations_endswith(persona):
    ## Should return the text which the sentence should start with to 
    ## trigger, and the callback to be awaited
    return await database_iterations_endswith(persona)

async def iterations_contains(persona):
    ## Should return the text which the sentence should start with to 
    ## trigger, and the callback to be awaited
    return await database_iterations_contains(persona)

async def furhat_handler_startswith(persona, sentence):
    iterations = await iterations_startswith(persona)
    for iteration in iterations:
        if sentence.lower().startswith(iteration.text.lower()):
            return iteration.callback
    return None

async def furhat_handler_endswith(persona, sentence):
    iterations = await iterations_endswith(persona)
    for iteration in iterations:
        if sentence.lower().endswith(iteration.text.lower()):
            return iteration.callback
    return None

async def furhat_handler_contains(persona, sentence):
    iterations = await iterations_contains(persona)
    for iteration in iterations:
        ## This is the Python implementation for string.contains()
        if iteration.text.lower() in sentence.lower():
            return iteration.callback
    return None

## This argument is a furhat_bot.Status
async def furhat_handler(config, personas, text):
    callbacks = list()
    for persona in personas:
        ## We will only check full message if it doesn't starts with 
        ## something pre defined
        callback = await furhat_handler_startswith(
            config[persona].personalidade,
            text.message,
        )
        if callback is None:
            callback = await furhat_handler_endswith(
                config[persona].personalidade,
                text.message,
            )
            if callback is None:
                callback = await furhat_handler_contains(
                    config[persona].personalidade,
                    text.message,
                )
        if callback is not None:
            callbacks.append(Callback(
                bot = persona,
                callback = callback(config[persona], text.message),
            ))
    return callbacks
