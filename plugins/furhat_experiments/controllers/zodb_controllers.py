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

import asyncio, glob, os, random, uuid
from urllib3.exceptions import MaxRetryError
from iacecil.controllers.furhat_bot.remote_api import (
    get_furhat,
    get_voices,
    set_face,
    set_led,
    set_voice,
    do_attend_location,
    do_attend_user,
    do_listen,
    do_say_text,
    do_say_url,
    block_do_listen,
    block_do_say_text,
    block_do_say_url,
)
from iacecil.models.furhat_models import Status
from plugins.persistence.zodb_orm import (
    get_messages_texts_list,
    get_furhat_texts_messages,
    set_furhat_text,
)
from plugins.natural import (
    generate,
    concordance,
    collocations,
    common_contexts,
    count,
    similar,
)

async def zodb_get_session(furhat_id, session_id):
    messages = await get_furhat_texts_messages(furhat_id, session_id)
    # ~ logger.debug(str(messages))
    return messages

async def zodb_get_sessions(furhat_id):
    all_messages = list()
    for session in glob.glob(
        'instance/zodb/furhats/{}/sessions/*.fs'.format(furhat_id)
    ):
        messages = await get_furhat_texts_messages(
            furhat_id, session.split('/')[-1].split('.')[0]
        )
        if isinstance(messages, list):
            all_messages = all_messages + messages
        elif isinstance(messages, str):
            all_messages.append(messages)
    # ~ logger.debug(str(all_messages))
    return all_messages

async def zodb_get_aiogram():
    all_messages = list()
    for bot in glob.glob('instance/zodb/bots/*'):
        for chat in glob.glob('{}/chats/*.fs'.format(bot)):
            messages = await get_messages_texts_list(
                bot.split('/')[-1], chat.split('/')[-1].split('.')[0],
                -1, 0,
            )
            if isinstance(messages[1], list):
                all_messages = all_messages + messages[1]
            elif isinstance(messages[1], str):
                all_messages.append(messages[1])
            logger.debug(len(all_messages))
    return all_messages
