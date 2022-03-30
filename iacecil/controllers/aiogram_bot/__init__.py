# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import logging
logger = logging.getLogger(__name__)

from importlib import import_module
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from iacecil import name
from iacecil.controllers.aiogram_bot.bot import IACecilBot
from iacecil.controllers import personalidades
from iacecil.controllers.aiogram_bot.callbacks import (
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
from iacecil.controllers.aiogram_bot.filters import (
    IsReplyToIdFilter,
    WhoJoinedFilter,
)
from plugins.calendar import (
    get_scheduler,
    add_job,
)

def aiogram_startup(config, names):
    logger.info(u"Starting up Aiogram...")
    dispatchers = list()
    for name in names:
        bot = (IACecilBot(
            token = config[name]['telegram']['token'],
            config = config[name],
        ))
        dispatcher = Dispatcher(bot)
        ## FIXME backwards compat
        setattr(dispatcher, 'config', config[name])
        setattr(dispatcher, 'info', config[name]['info'])
        setattr(dispatcher, 'users', config[name]['telegram']['users'])
        setattr(dispatcher, 'plugins', config[name]['info']['plugins'])
        setattr(dispatcher, 'scheduler', get_scheduler())
        dispatchers.append(dispatcher)
    return dispatchers

async def add_jobs(dispatcher: Dispatcher):
    for job in dispatcher.config['info']['jobs']:
        await add_job(job, dispatcher.scheduler,
            tz = dispatcher.config['info']['timezone'])

async def add_filters(dispatcher: Dispatcher):
    ### Filters
    dispatcher.filters_factory.bind(IsReplyToIdFilter)
    dispatcher.filters_factory.bind(WhoJoinedFilter)

async def add_handlers(dispatcher: Dispatcher):
    ## New plugin handling system since v0.1.17
    enable = ['default']
    disable = ['echo']
    try:
        enable = dispatcher.bot.config['info']['plugins']['enable']
        disable = dispatcher.bot.config['info']['plugins']['disable']
    except Exception as exception:
        logger.critical(u"Plugins not properly configured. RTFM.")
        raise
    for plugin in enable:
        if plugin not in disable:
            try:
                module = import_module('.'.join(['plugins', plugin]))
                await getattr(module, 'add_handlers')(dispatcher)
                logger.info(u"Activated plugin {}".format(plugin))
            except Exception as exception:
                logger.warning(
                    u"Failed to activate plugin {}:\n{}".format(
                        plugin, repr(exception))
                )
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
