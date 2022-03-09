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
from iacecil.controllers.furhat_bot import (
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

try:
    from instance.config import Config
    config = Config()
    furhat_config = config.quart['furhat']
except Exception as exception:
    logger.critical(u"""{} config file not found or somehow wrong. RTFM\
.\n{}""".format(actual_name, str(exception)))
    raise

async def change_voice(furhat, voices, language):
    await set_voice(furhat, random.choice([voice.name for voice in \
        voices if voice.language == language]))

async def zodb_get_session(furhat_id, session_id):
    messages = await get_furhat_texts_messages(furhat_id, session_id)
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

async def blue_speak(furhat, message):
    await asyncio.sleep(1)
    await set_led(furhat, red = 0, green = 0, blue = 255)
    await do_attend_user(furhat, 'RANDOM')
    await do_say_text(furhat, message)

## Blocking loop
async def papagaio(skip_intro = False):
    furhat_id = furhat_config['bot']
    address = furhat_config['address']
    language = furhat_config['language']
    mask = furhat_config['mask']
    character = furhat_config['character']
    voice = furhat_config['voice']
    voice_url = furhat_config['voice_url']
    session_id = uuid.uuid4()
    furhat = await get_furhat(address)
    await set_led(furhat, red = 0, green = 0, blue = 255)
    voices = await get_voices(furhat)
    # ~ logger.info(voices)
    await set_face(furhat, mask, character)
    await set_voice(furhat, voice)
    await do_attend_user(furhat, 'CLOSEST')
    if not skip_intro:
        await do_say_text(furhat, """olá! eu sou um papagaio. quando a \
minha luz for verde, eu estou ouvindo. quando a minha luz for vermelha,\
 eu estou falando. Eu vou repetir tudo o que disserem pra mim. Quando e\
njoar, é só dizer: "chega". Que eu calo a boca.""")
        await asyncio.sleep(18)

    # ~ message = await nlp_count(furhat_id, 'teste')
    # ~ await blue_speak(furhat, message)
    # ~ message = await nlp_generate(furhat_id)
    # ~ await blue_speak(furhat, message)
    # ~ message = await nlp_generate_aiogram()
    # ~ await blue_speak(furhat, message)

    await asyncio.sleep(1)
    await set_led(furhat, red = 0, green = 0, blue = 0)
    while True:
        await asyncio.sleep(1)
        await do_attend_location(furhat, x = 0, y = -30, z = 0)
        await set_led(furhat, red = 0, green = 255, blue = 0)
        await asyncio.sleep(1)
        text =  await do_listen(furhat, language)
        await asyncio.sleep(1)
        await set_led(furhat, red = 0, green = 0, blue = 0)
        if text.success and text.message not in ['', 'EMPTY']:
            logger.info(str(text))
            if text.message.lower() in ['chega', 'listo', 'enough']:
                await set_led(furhat, red = 0, green = 0, blue = 255)
                language = 'pt-BR'
                await change_voice(furhat, voices, language)
                await do_attend_user(furhat, 'RANDOM')
                await do_say_text(
                    furhat,
                    'agora eu vou calar a boca. tchau!',
                )
                await asyncio.sleep(1)
                await set_led(furhat, red = 0, green = 0, blue = 0)
                break
            elif text.message.lower().startswith('comando'):
                message = u"não entendi."
                if text.message == 'comando gerar sessão':
                    message = await nlp_generate_session(
                        furhat_id,
                        session_id,
                    )
                elif text.message.lower() == 'comando gerar':
                    message = await nlp_generate(furhat_id)
                elif text.message.lower() == 'comando colocação sessão':
                    message = await nlp_collocations_session(
                        furhat_id,
                        session_id,
                    )
                elif text.message == 'comando colocação':
                    message = await nlp_collocations(furhat_id)
                elif text.message.lower().startswith(
                    'comando contar sessão'
                ):
                    word = text.message.split(' ')[-1]
                    message = await nlp_count_session(
                        furhat_id,
                        session_id,
                        word,
                    )
                elif text.message.startswith('comando contar'):
                    word = text.message.split(' ')[-1]
                    message = await nlp_count(furhat_id, word)
                elif text.message.lower().startswith(
                    'comando similar sessão'
                ):
                    word = text.message.split(' ')[-1]
                    message = await nlp_similar_session(furhat_id, word)
                elif text.message.startswith('comando similar'):
                    word = text.message.split(' ')[-1]
                    message = await nlp_similar(furhat_id, word)
                elif text.message.lower().startswith(
                    'comando concordância sessão'
                ):
                    word = text.message.split(' ')[-1]
                    message = await nlp_concordance_session(
                        furhat_id,
                        word,
                    )
                elif text.message.lower().startswith(
                    'comando concordância'
                ):
                    word = text.message.split(' ')[-1]
                    message = await nlp_concordance(furhat_id, word)
                elif text.message.lower().startswith(
                    'comando contexto sessão'
                ):
                    words = text.message.split(' ')[3:]
                    message = await nlp_common_context_session(
                        furhat_id,
                        words,
                    )
                elif text.message.lower().startswith(
                    'comando contexto'
                ):
                    words = text.message.split(' ')[2:]
                    message = await nlp_common_context(furhat_id, words)
                await blue_speak(furhat, message)
            elif text.message.lower() in [
                'português',
                'portugués',
                'portuguese',
            ]:
                await asyncio.sleep(1)
                await set_led(furhat, red = 0, green = 0, blue = 255)
                language = 'pt-BR'
                await change_voice(furhat, voices, language)
                await do_attend_user(furhat, 'RANDOM')
                await do_say_text(furhat, u"""Agora eu vou falar e escu\
tar em português brasileiro.""")
            elif text.message.lower() in [
                'inglês',
                'inglés',
                'english',
            ]:
                await asyncio.sleep(1)
                await set_led(furhat, red = 0, green = 0, blue = 255)
                language = 'en-US'
                await change_voice(furhat, voices, language)
                await do_attend_user(furhat, 'RANDOM')
                await do_say_text(furhat, u"""Now I'm listening and spe\
aking in united states english.""")
            elif text.message.lower() in [
                'espanhol',
                'español',
                'spanish',
            ]:
                await asyncio.sleep(1)
                await set_led(furhat, red = 0, green = 0, blue = 255)
                language = 'es-ES'
                await change_voice(furhat, voices, language)
                await do_attend_user(furhat, 'RANDOM')
                await do_say_text(furhat, u"""Ahora yo voy a hablar e e\
scuchar en español""")
            elif text.message.lower() in [
                'francês',
                'francesc',
                'french',
            ]:
                await asyncio.sleep(1)
                await set_led(furhat, red = 0, green = 0, blue = 255)
                await do_attend_user(furhat, 'RANDOM')
                audio = random.choice([
                    'french',
                    'gotone',
                    'kniggits',
                    'pigdog',
                    'nomore',
                    'boil',
                    'fart',
                    'taunt',
                    'hamster',
                    'wipe',
                ])
                await do_say_url(
                    furhat,
                    ''.join([voice_url + audio + '.wav']),
                )
            else:
                await set_furhat_text(furhat_id, session_id, text)
                await asyncio.sleep(1)
                await do_attend_user(furhat, 'RANDOM')
                await set_led(furhat, red = 255, green = 0, blue = 0)
                block_do_say_text(furhat, text.message)
            await asyncio.sleep(1)
            await set_led(furhat, red = 0, green = 0, blue = 0)
            continue
