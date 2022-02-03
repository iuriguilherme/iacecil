# vim:fileencoding=utf-8
#  Plugin portaria para ia.cecil: Controle de acesso e moderação
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

## FIXME: Plugin está quebrado e não está sendo utilizado. O plugin
## welcome estava distribuído pelas personalidades e este plugin acabou
## se tornando várias linhas de código redundantes em todos eles.

import logging
logger = logging.getLogger(__name__)

from aiogram import types
from aiogram.utils.markdown import escape_md
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from iacecil.controllers.aiogram_bot.filters import WhoJoinedFilter
from plugins.personalidades import (
    gerar_texto,
)

async def add_handlers(dispatcher):
    ## Padrão para lidar com pessoas indesejáveis é enviar uma mensagem
    ## para o grupo denunciando a entrada de alguém que não é bem vindo.
    ## Para expulsar, banir, escorraçar, ou dar boas vindas é necessário
    ## configurar isto na personalidade.
    @dispatcher.message_handler(
        WhoJoinedFilter(
            unwanted = [unwant.lower() for unwant in 
                dispatcher.bot.users.get('unwanted', ['SPAM'])],
        ),
        content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
    )
    async def portaria_callback(message: types.Message):
        await message_callback(message, ['portaria', message.chat.type])
        text = await gerar_texto('portaria', dispatcher.bot, message)
        # ~ command = await message.reply(text)
        # ~ await command_callback(command, 
            # ~ ['portaria', message.chat.type]
        # ~ )
        await error_callback(
            text,
            message,
            None,
            ['portaria', 'dev', 'teste',],
        )
