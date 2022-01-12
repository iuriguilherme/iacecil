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

from aiogram import (
    filters,
    types,
)

class IsReplyToIdFilter(filters.BoundFilter):
    key = 'is_reply_to_id'
    def __init__(self, is_reply_to_id):
        self.is_reply_to_id = is_reply_to_id
    async def check(self, msg: types.Message):
        if msg.reply_to_message and (
            msg.reply_to_message.from_user.id == self.is_reply_to_id
        ):
            return True

class WhoJoinedFilter(filters.BoundFilter):
    key = 'unwanted'
    def __init__(self, unwanted):
        self.unwanted = unwanted
    async def check(self, msg: types.Message):
        print("AQUI AQUI AQUI: {}".format(self.unwanted))
        if 'new_chat_member' in msg and str(
            msg['new_chat_member'].get('first_name', ''
            ).lower() in self.unwanted
        ):
            return True
