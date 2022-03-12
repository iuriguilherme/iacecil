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

### Aiogram
from aiogram import (
    Dispatcher,
    filters,
    types,
)

from iacecil import name
from iacecil.controllers.aiogram_bot.bot import IACecilBot

## Plugins
from plugins import (
    admin as plugin_admin,
    archive as plugin_archive,
    cryptoforex as plugin_cryptoforex,
    default as plugin_default,
    donate as plugin_donate,
    echo as plugin_echo,
    feedback as plugin_feedback,
    garimpo as plugin_garimpo,
    # ~ greatful as plugin_greatful,
    hashes as plugin_hashes,
    mate_matica as plugin_matematica,
    personalidades as plugin_personalidades,
    portaria as plugin_portaria,
    qr as plugin_qr,
    # ~ totalvoice as plugin_totalvoice
    tropixel as plugin_tropixel,
    welcome as plugin_welcome,
    ytdl as plugin_ytdl,
)

## Generic Callbacks
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

## Filters
from iacecil.controllers.aiogram_bot.filters import (
    IsReplyToIdFilter,
    WhoJoinedFilter,
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
        dispatchers.append(dispatcher)
    return dispatchers

async def add_filters(dispatcher: Dispatcher):
    ### Filters
    dispatcher.filters_factory.bind(IsReplyToIdFilter)
    dispatcher.filters_factory.bind(WhoJoinedFilter)

async def add_handlers(dispatcher: Dispatcher):
    await plugin_admin.add_handlers(dispatcher)
    # ~ await plugin_echo.add_handlers(dispatcher)
    ## Personalidades plugin, loaded first to overwrite methods
    ## (aiogram behaviour)
    # ~ await plugin_portaria.add_handlers(dispatcher)
    await plugin_personalidades.add_handlers(dispatcher)
    ## Special case plugins
    if dispatcher.bot.config['info'].get('personalidade', None) in [
        'default',
        'metarec',
        'pave',
        'cryptoforex',
        'iacecil',
        'matebot',
    ]:
        await plugin_donate.add_handlers(dispatcher)
        await plugin_archive.add_handlers(dispatcher)
    ## Plugins mais que especiais
    if dispatcher.bot.config['info'].get('personalidade', None) in [
        'metarec',
        'matebot',
    ]:
        try:
            await plugin_welcome.add_handlers(dispatcher)
        except KeyError:
            logger.warning(u"plugin welcome não configurado")
        try:
            await plugin_tropixel.add_handlers(dispatcher)
        except KeyError:
            logger.warning(u"plugin tropixel não configurado")
    if dispatcher.bot.config['info'].get('personalidade') in [
        'cryptoforex',
        'iacecil',
    ]:
        try:
            await plugin_cryptoforex.add_handlers(dispatcher)
        except KeyError:
            logger.warning(u"plugin cryptoforex não configurado")
    ## Plugins gerais
    await plugin_hashes.add_handlers(dispatcher)
    await plugin_matematica.add_handlers(dispatcher)
    await plugin_qr.add_handlers(dispatcher)
    await plugin_feedback.add_handlers(dispatcher)
    await plugin_ytdl.add_handlers(dispatcher)
    await plugin_default.add_handlers(dispatcher)
    if dispatcher.bot.config['info'].get('personalidade', None) in [
        'default',
        'metarec',
        'matebot',
        'iacecil',
    ]:
        try:
            await plugin_garimpo.add_handlers(dispatcher)
        except KeyError:
            logger.warning(u"plugin garimpo não configurado")
    ## Todas updates que não forem tratadas por handlers anteriores
    dispatcher.register_message_handler(
        any_message_callback,
        content_types = types.message.ContentType.ANY,
    )
    dispatcher.register_edited_message_handler(
        any_edited_message_callback
    )
    dispatcher.register_channel_post_handler(any_channel_post_callback)
    dispatcher.register_edited_channel_post_handler(
        any_edited_channel_post_callback,
    )
    dispatcher.register_errors_handler(any_error_callback)
