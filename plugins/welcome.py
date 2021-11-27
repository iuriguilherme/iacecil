# vim:fileencoding=utf-8
#  Plugin welcome para ia.cecil: Boas vindas a pessoas que entram em 
#  grupos
#  Copyleft (C) 2020-2021 Iuri Guilherme <https://iuri.neocities.org/>
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

from aiogram import (
    filters,
    types,
)
from aiogram.utils.markdown import escape_md
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from plugins.personalidades import (
    gerar_texto,
)

async def add_handlers(dispatcher):
    ## Padrão de boas vindas. Exclui grupos 'omega' pra evitar de mandar mensagem
    ## de boas vindas em grupos onde o bot só é utilizado com os comandos básicos.
    ## Requer que grupos que queiram ativar o plugin de boas vindas sejam
    ## adicionados pelo menos às listas 'delta' ou 'gama'.
    @dispatcher.message_handler(
        filters.IDFilter(
            chat_id = dispatcher.bot.users.get('delta', -1) +
                dispatcher.bot.users.get('gamma', -1),
        ),
        content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
    )
    async def welcome_callback(message: types.Message):
        await message_callback(message, ['welcome', message.chat.type])
        text = await gerar_texto('welcome', dispatcher.bot, message)
        command = await message.reply(text)
        await command_callback(command, ['welcome', message.chat.type])
