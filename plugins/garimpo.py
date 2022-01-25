# vim:fileencoding=utf-8
#  Plugin garimpo para ia.cecil: Coleta links
#  Copyleft (C) 2022 Iuri Guilherme <https://iuri.neocities.org/>
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

import logging, validators
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from plugins.log import (
    info_logger,
    debug_logger,
    zodb_logger,
)

async def varre_link(message):
    try:
        dispatcher = Dispatcher.get_current()
        if dispatcher.bot.info.get('personalidade', None) in [
            'default',
            'metarec',
            'matebot',
            'iacecil',
        ]:
            url = None
            if message.entities is not None:
                for entity in message.entities:
                    if entity['type'] == "url":
                        url =  message.text[
                            entity['offset']:entity['length'] + \
                            entity['offset']
                        ]
            if url and validators.url(url):
                pass
            else:
                url = None
            if url:
                await message.send_copy(
                    chat_id = dispatcher.bot.users['special'][
                        'garimpo'],
                )
    except Exception as exception:
        await debug_logger(u"Erro tentando garimpar link", message,
            exception, ['garimpo', 'exception'],
        )

async def add_handlers(dispatcher):
    ## Salva link em outro grupo

    ## FIXME implementar garimpo total (garimpa_tudo_callback) com
    ## filtro de chat_id em grupos exclusivos, e estes dois outros
    ## filtros em todos grupos
    # ~ @dispatcher.message_handler(filters.Command([
        # ~ 'g', 'garimpo', 'garimpa', 'salva', 'verdepois', 'vouver',
    # ~ ]))
    # ~ async def garimpo_callback(message):
        # ~ await info_logger(message, ['garimpo', message.chat.type])
        # ~ command = await varre_link(message)
        # ~ await info_logger(command, ['command', 'garimpo',
            # ~ message.chat.type],
        # ~ )

    # ~ @dispatcher.message_handler(filters.Text([
        # ~ 'depois eu vejo',
        # ~ 'um dia eu vejo',
        # ~ 'uma hora eu vejo',
        # ~ 'vou ver',
        # ~ 'já vejo',
        # ~ 'salva',
        # ~ 'garimpo',
        # ~ 'garimpa',
    # ~ ]))
    # ~ async def procastinacao_callback(message):
        # ~ await info_logger(message, ['procastinacao',
            # ~ message.chat.type])
        # ~ if message.reply_to_message is not None:
            # ~ command = await varre_link(message.reply_to_message)
            # ~ await info_logger(command, ['command', 'procastinacao',
                # ~ message.chat.type]
            # ~ )

    ## TODO garimpa todos links de todos grupos pra estas personalidades
    @dispatcher.message_handler(filters.ContentTypeFilter(
        types.message.ContentType.ANY
    ))
    async def garimpa_tudo_callback(message):
        await zodb_logger(message)
        await varre_link(message)
