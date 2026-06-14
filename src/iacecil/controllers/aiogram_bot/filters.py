"""
ia.cecil

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
logger = logging.getLogger(__name__)

from aiogram.filters import BaseFilter
from aiogram import types

class IsReplyToIdFilter(BaseFilter):
    def __init__(self, is_reply_to_id: int):
        self.is_reply_to_id = is_reply_to_id

    async def __call__(self, message: types.Message) -> bool:
        if message.reply_to_message and (
            message.reply_to_message.from_user.id == self.is_reply_to_id
        ):
            return True
        return False

class WhoJoinedFilter(BaseFilter):
    def __init__(self, unwanted: list[str]):
        self.unwanted = unwanted

    async def __call__(self, message: types.Message) -> bool:
        ## NOTE: In aiogram 3, new_chat_members is a list on the Message object
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.first_name and \
                   member.first_name.lower() in self.unwanted:
                    return True
        return False
