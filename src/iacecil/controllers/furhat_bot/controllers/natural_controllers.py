"""
ia.cecil

Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import asyncio
import glob
import os
import random
import uuid
from urllib3.exceptions import MaxRetryError
from ..remote_api import (
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
from ....models.furhat_models import Status
from ...persistence.zodb_orm import (
    get_messages_texts_list,
    get_furhat_texts_messages,
    set_furhat_text,
)
from ....plugins.natural import (
    generate,
    concordance,
    concordance_1,
    collocations,
    common_contexts,
    common_contexts_1,
    count,
    count_1,
    similar,
    similar_1,
)
from .zodb_controllers import (
    zodb_get_session,
    zodb_get_sessions,
)

async def nlp_generate(furhat_id):
    all_messages = await zodb_get_sessions(furhat_id)
    generated = await generate(all_messages)
    return ' '.join([word for word in generated if word.lower() != \
        "none"])

async def nlp_generate_session(furhat_id, session_id):
    messages = await zodb_get_session(furhat_id, session_id)
    generated = await generate(messages)
    return ' '.join([word for word in generated if word.lower() != \
        "none"])

async def nlp_generate_aiogram():
    all_messages = await zodb_get_aiogram()
    generated = await generate(all_messages)
    return ' '.join([word for word in generated if word.lower() != \
        "none"])

async def nlp_collocations(furhat_id):
    all_messages = await zodb_get_sessions(furhat_id)
    return await collocations(all_messages)

async def nlp_collocations_session(furhat_id, session_id):
    messages = await zodb_get_session(furhat_id, session_id)
    return await collocations(messages)

async def nlp_concordance(furhat_id, word):
    all_messages = await zodb_get_sessions(furhat_id)
    concordances = await concordance_1(all_messages, word)
    return u"concordâncias com {}: {}".format(word, concordances)

async def nlp_concordance_session(furhat_id, session_id, word):
    messages = await zodb_get_session(furhat_id, session_id)
    concordances = await concordance_1(messages, word)
    return u"concordâncias com {}: {}".format(word, concordances)

async def nlp_similar(furhat_id, word):
    all_messages = await zodb_get_sessions(furhat_id)
    similars = await similar_1(all_messages, word)
    return u"""palavras que eu ouvi e são similares a {}: {}""".format(
        word, similars)

async def nlp_similar_session(furhat_id, session_id, word):
    messages = await zodb_get_session(furhat_id, session_id)
    similars = await similar_1(messages, word)
    return u"""palavras que eu ouvi e são similares a {} nesta sessão: \
{}""".format(word, similars)

async def nlp_count(furhat_id, word):
    all_messages = await zodb_get_sessions(furhat_id)
    counted = await count_1(all_messages, word)
    return u"""eu já ouvi {}. {} vezes, sendo {:.2f} por cento de tudo \
que eu já ouvi""".format(word, counted['count'], counted['percentage'])

async def nlp_count_session(furhat_id, session_id, word):
    messages = await zodb_get_session(furhat_id, session_id)
    counted = await count_1(messages, word)
    return u"""eu já ouvi {}. {} vezes nessa sessão, sendo {:.2f} por c\
ento de tudo que eu já ouvi""".format(word, counted['count'],
        counted['percentage'])

async def nlp_common_context(furhat_id, words):
    all_messages = await zodb_get_sessions(furhat_id)
    contexts = await common_contexts_1(all_messages, words)
    return u"contextos comuns para as palavras {}: {}".format(
        ' e '.join(words),
        contexts,
    )

async def nlp_common_context_session(furhat_id, session_id, words):
    messages = await zodb_get_session(furhat_id, session_id)
    contexts = await common_contexts_1(messages, words)
    return u"contextos comuns para as palavras {}: {}".format(
        ' e '.join(words),
        contexts,
    )

async def ack(furhat):
    await do_say_text(furhat, text = 'ok, só um minuto')

async def natural_handler(furhat, message, order, furhat_id,
    session_id, *args, **kwargs):
    reply = u"não entendi."
    if message.lower() == 'geração sessão ' + order:
        await ack(furhat)
        reply = await nlp_generate_session(furhat_id, session_id)
    elif message.lower() == 'geração ' + order:
        await ack(furhat)
        reply = await nlp_generate(furhat_id)
    elif message.lower() == 'geração total ' + order:
        await ack(furhat)
        reply = await nlp_generate_aiogram(furhat_id)
    # ~ elif message.lower() == 'colocação sessão ' + order:
        # ~ await ack(furhat)
        # ~ reply = await nlp_collocations_session(
            # ~ furhat_id,
            # ~ session_id,
        # ~ )
    # ~ elif message.lower() == 'colocação ' + order:
        # ~ await ack(furhat)
        # ~ reply = await nlp_collocations(furhat_id)
    elif message.lower().startswith('contar sessão'):
        await ack(furhat)
        word = ' '.join(message.split(' ')[2:-len(order.split(' '))])
        reply = await nlp_count_session(furhat_id, session_id, word)
    elif message.lower().startswith('contar'):
        await ack(furhat)
        word = ' '.join(message.split(' ')[1:-len(order.split(' '))])
        reply = await nlp_count(furhat_id, word)
    elif message.lower().startswith('similar sessão'):
        await ack(furhat)
        word = ' '.join(message.split(' ')[2:-len(order.split(' '))])
        reply = await nlp_similar_session(furhat_id, word)
    elif message.lower().startswith('similar'):
        await ack(furhat)
        word = ' '.join(message.split(' ')[1:-len(order.split(' '))])
        reply = await nlp_similar(furhat_id, word)
    elif message.lower().startswith('concordância sessão'):
        await ack(furhat)
        word = ' '.join(message.split(' ')[2:-len(order.split(' '))])
        reply = await nlp_concordance_session(furhat_id, word)
    elif message.lower().startswith('concordância'):
        await ack(furhat)
        word = ' '.join(message.split(' ')[1:-len(order.split(' '))])
        reply = await nlp_concordance(furhat_id, word)
    elif message.lower().startswith('contexto sessão'):
        await ack(furhat)
        words = message.split(' ')[2:-len(order.split(' '))]
        reply = await nlp_common_context_session(furhat_id, words)
    elif message.lower().startswith('contexto'):
        await ack(furhat)
        words = message.split(' ')[1:-len(order.split(' '))]
        reply = await nlp_common_context(furhat_id, words)
    elif message.lower().startswith('escolhe'):
        words = message.split(' ')[1:-len(order.split(' '))]
        reply = random.choice(words)
    return reply
