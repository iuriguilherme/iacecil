"""
Plugin welcome para ia.cecil: Boas vindas a pessoas que entram em grupos

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

from aiogram import (
    filters,
    types,
)
from aiogram.utils.markdown import escape_md
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from iacecil.controllers.personalidades import (
    gerar_texto,
)

async def add_handlers(dispatcher):
    try:
        ## Padrão de boas vindas. Exclui grupos 'omega' pra evitar de mandar
        ## mensagem de boas vindas em grupos onde o bot só é utilizado com
        ## os comandos básicos. Requer que grupos que queiram ativar o 
        ## plugin de boas vindas sejam adicionados pelo menos às listas 
        ## 'delta' ou 'gama'.
        @dispatcher.message_handler(
            # ~ filters.IDFilter(
                # ~ chat_id = dispatcher.config.telegram['users'].get(
                    # ~ 'delta', -1) + dispatcher.config.telegram[
                    # ~ 'users'].get('gamma', -1),
            # ~ ),
            content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
        )
        async def welcome_callback(message: types.Message):
            command_type = 'welcome'
            await message_callback(message,
                [command_type, message.chat.type],
            )
            text = await gerar_texto('welcome', dispatcher.bot, message)
            if str(message['new_chat_member']['first_name']).lower() in \
                [
                    unwant.lower() \
                    for unwant in \
                    dispatcher.config.telegram.get('unwanted', ['SPAM']) \
                ]:
                text = await gerar_texto('portaria', dispatcher.bot,
                    message,
                )
                command_type = 'portaria'
            command = await message.reply(text)
            await command_callback(command,
                [command_type, message.chat.type],
            )
    except Exception as e:
        logger.exception(e)
        raise
