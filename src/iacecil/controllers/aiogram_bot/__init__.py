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

from importlib import import_module
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from pydantic import BaseSettings
from ... import name
from .bot import IACecilBot
from .. import personalidades
from .callbacks import (
    message_callback,
    command_callback,
    error_callback,
    any_message_callback,
    any_edited_message_callback,
    any_channel_post_callback,
    any_edited_channel_post_callback,
    any_update_callback,
    any_error_callback,
)
from .filters import (
    IsReplyToIdFilter,
    WhoJoinedFilter,
)
from plugins.calendar import (
    get_scheduler,
    add_job,
)

def aiogram_startup(configs: list[BaseSettings], names: list) -> list:
    """
    Current starting point for Aiogram
    Returns list of aiogram.Dispatcher
    """
    logger.info("Starting up Aiogram...")
    dispatchers = list()
    for name in names:
        try:
            bot = (IACecilBot(
                token = configs[name].telegram['token'],
                ## TODO: config should be only in the dispatcher
                config = configs[name],
            ))
            dispatcher = Dispatcher(bot)
            ## FIXME backwards compat
            setattr(dispatcher, 'name', name)
            setattr(dispatcher, 'config', configs[name])
            setattr(
                dispatcher,
                'info',
                dict(
                    configs[name].info.copy(),
                    telegram = configs[name].telegram['info'],
                )
            )
            setattr(dispatcher, 'users', configs[name].telegram['users'])
            setattr(dispatcher, 'plugins', configs[name].plugins)
            setattr(dispatcher, 'scheduler', get_scheduler())
            dispatchers.append(dispatcher)
        except Exception as e:
            logger.error(f"Skipping {name}, see error details below")
            logging.exception(e)
    return dispatchers

async def add_jobs(dispatcher: Dispatcher) -> None:
    """Add jobs to the dispatcher's scheduler"""
    for job in dispatcher.config.jobs:
        await add_job(job, dispatcher.scheduler, dispatcher)

async def add_filters(dispatcher: Dispatcher) -> None:
    """Add filters to dispatcher"""
    dispatcher.filters_factory.bind(IsReplyToIdFilter)
    dispatcher.filters_factory.bind(WhoJoinedFilter)

async def add_plugin(dispatcher: Dispatcher, plugin: str) -> None:
    """Imports plugin and register handlers to dispatcher"""
    try:
        logger.debug(f"Activating plugin {plugin} for {dispatcher.name}")
        module = import_module('.' + plugin, 'plugins')
        try:
            logger.debug("Registering handlers")
            await getattr(module, 'add_handlers')(dispatcher)
        except AttributeError:
            logger.debug("Plugin don't have handlers to register")
        logger.info(f"Activated plugin {plugin} for {dispatcher.name}")
    except Exception as e:
        logger.warning(f"""Failed to activate plugin {plugin} for \
{dispatcher.name}""")
        logger.exception(e)

async def add_handlers(dispatcher: Dispatcher) -> None:
    """
    Register handlers to aiogram.Dispatcher
    New plugin handling system since v0.1.17
    """
    enable: list = ['default']
    disable: list = ['echo']
    try:
        enable: list = dispatcher.config.plugins['enable']
        disable: list = dispatcher.config.plugins['disable']
    except Exception as e:
        logger.error("Plugins not properly configured. RTFM.")
        logger.exception(e)
    [
        await add_plugin(dispatcher, plugin) \
        for plugin in enable \
        if plugin not in disable \
    ]
    ## Specific to personalidade handlers registered after the others
    await personalidades.add_handlers(dispatcher)

    ## Todas updates que não forem tratadas por handlers anteriores
    dispatcher.register_message_handler(
        any_message_callback,
        # ~ content_types = types.message.ContentType.ANY,
    )
    dispatcher.register_edited_message_handler(
        any_edited_message_callback,
        content_types = types.message.ContentType.ANY,
    )
    dispatcher.register_channel_post_handler(
        any_channel_post_callback,
        content_types = types.message.ContentType.ANY,
    )
    dispatcher.register_edited_channel_post_handler(
        any_edited_channel_post_callback,
        content_types = types.message.ContentType.ANY,
    )
    # ~ dispatcher.register_inline_handler(
        # ~ any_inline_handler_callback,
    # ~ )
    # ~ dispatcher.register_chosen_inline_handler(
        # ~ any_chosen_inline_handler_callback,
    # ~ )
    # ~ dispatcher.register_callback_query_handler(
        # ~ any_callback_query_handler_callback,
    # ~ )
    # ~ dispatcher.register_shipping_query_handler(
        # ~ any_shipping_query_handler_callback,
    # ~ )
    # ~ dispatcher.register_pre_checkout_query_handler(
        # ~ any_pre_checkout_query_handler_callback,
    # ~ )
    # ~ dispatcher.register_poll_handler(
        # ~ any_poll_callback,
    # ~ )
    # ~ dispatcher.register_poll_answer_handler(
        # ~ any_poll_answer_callback,
    # ~ )
    # ~ dispatcher.register_my_chat_member_handler(
        # ~ any_my_chat_member_callback,
    # ~ )
    # ~ dispatcher.register_chat_member_handler(
        # ~ any_chat_member_callback,
    # ~ )
    # ~ dispatcher.register_chat_join_request_handler(
        # ~ any_chat_join_request_callback,
    # ~ )
    dispatcher.register_errors_handler(
        any_error_callback,
        exception = Exception,
    )
