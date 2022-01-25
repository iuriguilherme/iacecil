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
)
from plugins.log import (
    info_logger,
    debug_logger,
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
            command = u"Não deu certo..."
            ## Será que é link?
            if message.entities is not None:
                for entity in message.entities:
                    if entity['type'] == "url":
                        url =  message.text[
                            entity['offset']:entity['length'] + \
                            entity['offset']
                        ]
            if not url and message.reply_to_message is not None:
                for entity in message.reply_to_message.entities:
                    if entity['type'] == "url":
                        url = message.reply_to_message.text[
                            entity['offset']:entity['length'] + \
                                entity['offset']
                        ]
                        message = message.reply_to_message
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
    @dispatcher.message_handler(
        commands = ['g', 'garimpo', 'garimpa', 'salva', 'verdepois',
            'vouver'
        ],
    )
    async def garimpo_callback(message):
        await info_logger(message, ['garimpo', message.chat.type])
        command = await varre_link(message)
        await info_logger(command, ['command', 'garimpo',
            message.chat.type],
        )

    @dispatcher.message_handler(filters.Text([
        'depois eu vejo',
        'um dia eu vejo',
        'uma hora eu vejo',
        'vou ver',
        'já vejo',
        'salva',
        'garimpo',
        'garimpa',
    ]))
    async def procastinacao_callback(message):
        await info_logger(message, ['procastinacao',
            message.chat.type])
        if message.reply_to_message is not None:
            command = await varre_link(message)
            await info_logger(command, ['command', 'procastinacao',
                message.chat.type]
            )
