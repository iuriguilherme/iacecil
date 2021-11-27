# vim:fileencoding=utf-8
#  Plugin echo para ia.cecil: Repete tudo, melhor que papagaio
#  Copyleft (C) 2016-2021 Iuri Guilherme <https://iuri.neocities.org/>
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

from aiogram import types

async def add_handlers(dispatcher):
    from iacecil.controllers.aiogram_bot.callbacks import (
        command_callback,
        message_callback,
    )
    @dispatcher.message_handler()
    async def echo(message: types.Message):
        await message_callback(message, ['echo', message.chat.type])
        command = await message.answer(message.text)
        await command_callback(command, ['echo', message.chat.type])
