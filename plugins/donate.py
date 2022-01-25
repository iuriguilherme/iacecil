# vim:fileencoding=utf-8
#  Plugin donate para ia.cecil: Indica formas de receber doações
#  Copyleft (C) 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)

## Aiogram
async def add_handlers(dispatcher):
    ## Mostra opções de doação
    @dispatcher.message_handler(
        commands = ['donate', 'doar'],
    )
    async def donate_callback(message):
        await message_callback(message, ['donate', message.chat.type])
        command = await message.reply(
            text = u"""List of addresses to donate for the bot develope\
rs:\n\n{}\n\nMissing one? Send /feedback""".format(
                addresses = '\n'.join(
                    dispatcher.bot.info['donate']['crypto']
                ),
            ),
            parse_mode = "MarkdownV2",
        )
        await command_callback(command, ['donate', message.chat.type])
