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
from plugins.furhat_experiments.controllers.zodb_controllers import (
    zodb_get_session,
    zodb_get_sessions,
)

async def nlp_generate(furhat_id):
    all_messages = await zodb_get_sessions(furhat_id)
    return await generate(all_messages)

async def nlp_generate_session(furhat_id, session_id):
    messages = await zodb_get_session(furhat_id, session_id)
    return await generate(messages)

async def nlp_generate_aiogram():
    all_messages = await zodb_get_aiogram()
    return await generate(all_messages)

async def nlp_collocations(furhat_id):
    all_messages = await zodb_get_sessions(furhat_id)
    return await collocations(all_messages)

async def nlp_collocations_session(furhat_id, session_id):
    messages = await zodb_get_session(furhat_id, session_id)
    return await collocations(messages)

async def nlp_concordance(furhat_id, word):
    all_messages = await zodb_get_sessions(furhat_id)
    concordances = await concordance(all_messages, word)
    return u"concordâncias com {}: {}".format(word, concordances)

async def nlp_concordance_session(furhat_id, session_id, word):
    messages = await zodb_get_session(furhat_id, session_id)
    concordances = await concordance(messages, word)
    return u"concordâncias com {}: {}".format(word, concordances)

async def nlp_similar(furhat_id, word):
    all_messages = await zodb_get_sessions(furhat_id)
    similars = await similar(all_messages, word)
    return u"palavras similares a {}: {}".format(word, similars)

async def nlp_similar_session(furhat_id, session_id, word):
    messages = await zodb_get_session(furhat_id, session_id)
    similars = await similar(messages, word)
    return u"palavras similares a {}: {}".format(word, similars)

async def nlp_count(furhat_id, word):
    all_messages = await zodb_get_sessions(furhat_id)
    counted = await count(all_messages, word)
    return u"{} foi dita {} vezes".format(word, counted)

async def nlp_count_session(furhat_id, session_id, word):
    messages = await zodb_get_session(furhat_id, session_id)
    counted = await count(messages, word)
    return u"{} foi dita {} vezes".format(word, counted)

async def nlp_common_context(furhat_id, words):
    all_messages = await zodb_get_sessions(furhat_id)
    contexts = await common_contexts(all_messages, words)
    return u"contextos comuns para as palavras {}: {}".format(
        ' '.join(words),
        contexts,
    )

async def nlp_common_context_session(furhat_id, session_id, words):
    messages = await zodb_get_session(furhat_id, session_id)
    contexts = await common_contexts(messages, words)
    return u"contextos comuns para as palavras {}: {}".format(
        ' '.join(words),
        contexts,
    )
