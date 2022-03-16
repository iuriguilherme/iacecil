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

# ~ import asyncio, glob, os, random, uuid
import asyncio, random, uuid
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
    do_shutup,
    # ~ block_do_listen,
    block_do_say_text,
    block_do_say_url,
)
from iacecil.models.furhat_models import Status
from plugins.persistence.zodb_orm import (
    # ~ get_messages_texts_list,
    # ~ get_furhat_texts_messages,
    set_furhat_text,
)
# ~ from plugins.natural import (
    # ~ generate,
    # ~ concordance,
    # ~ collocations,
    # ~ common_contexts,
    # ~ count,
    # ~ similar,
# ~ )
from plugins.furhat_experiments.controllers.furhat_controllers import (
    change_voice,
    led_blue,
    led_green,
    led_red,
    led_white,
    led_blank,
    blue_speak,
)
from plugins.furhat_experiments.controllers.natural_controllers import(
    nlp_generate,
    nlp_generate_session,
    nlp_generate_aiogram,
    nlp_collocations,
    nlp_collocations_session,
    nlp_concordance,
    nlp_concordance_session,
    nlp_similar,
    nlp_similar_session,
    nlp_count,
    nlp_count_session,
    nlp_common_context,
    nlp_common_context_session,
)
from plugins.furhat_experiments.controllers.zodb_controllers import(
    zodb_get_session,
    zodb_get_sessions,
    zodb_get_aiogram,
)
from plugins.personalidades import (
    gerar_comando,
    gerar_texto,
    generate_command_furhat,
    generate_text_furhat,
)
from plugins.furhat_experiments.personas.handlers import (
    furhat_handler,
)

async def personas(
    bots,
    furhat_config,
    bots_config,
    skip_intro,
    log_messages,
):
    try:
        furhat_id = furhat_config['bot']
        address = furhat_config['address']
        language = furhat_config['language']
        mask = furhat_config['mask']
        character = furhat_config['character']
        voice = furhat_config['voice']
        voice_url = furhat_config['voice_url']
        session_id = uuid.uuid4()
        furhat = await get_furhat(address)
        await led_blue(furhat)
        voices = await get_voices(furhat)
        # ~ logger.info(voices)
        await set_face(furhat, mask, character)
        await set_voice(furhat, voice)
        await do_attend_user(furhat, 'CLOSEST')
        if not skip_intro:
            await do_say_text(furhat, """iniciando modo de múltiplas pe\
rsonalidades""")
            await asyncio.sleep(3)
        await led_blank(furhat)
        while True:
            text = Status()
            while text.message == '':
                # ~ await do_attend_location(furhat, x = 0, y = -30, z = 0)
                await led_green(furhat)
                text =  await do_listen(furhat, language)
                # ~ logger.debug(str(text))
            await led_blank(furhat)
            # ~ text = Status(success = True, message = "chega")
            if text.success and text.message not in ['', 'EMPTY'] and \
                not text.message.startswith('ERROR'):
                logger.info(str(text))
                if 'cala boca' in text.message.lower() or 'cala a boca'\
                    in text.message.lower():
                    await do_shutup(furhat)
                elif text.message.lower() in [
                    'chega',
                    'listo',
                    'enough',
                ]:
                    await do_shutup(furhat)
                    await led_blue(furhat)
                    language = 'pt-BR'
                    await change_voice(furhat, voices, language)
                    await do_attend_user(furhat, 'RANDOM')
                    await do_say_text(
                        furhat,
                        'agora eu vou calar a boca. tchau!',
                    )
                    await asyncio.sleep(1)
                    await led_blank(furhat)
                    break
                elif text.message.lower().endswith('por favor'):
                    message = u"não entendi."
                    if text.message == 'geração sessão por favor':
                        message = await nlp_generate_session(
                            furhat_id,
                            session_id,
                        )
                    elif text.message.lower() == 'geração por favor':
                        message = await nlp_generate(furhat_id)
                    elif text.message.lower() == \
                        'colocação sessão por favor':
                        message = await nlp_collocations_session(
                            furhat_id,
                            session_id,
                        )
                    elif text.message.lower() == 'colocação por favor':
                        message = await nlp_collocations(furhat_id)
                    elif text.message.lower().startswith(
                        'contar sessão'
                    ):
                        word = ' '.join(text.message.split(' ')[2:-2])
                        message = await nlp_count_session(
                            furhat_id,
                            session_id,
                            word,
                        )
                    elif text.message.lower().startswith('contar'):
                        word = ' '.join(text.message.split(' ')[1:-2])
                        message = await nlp_count(furhat_id, word)
                    elif text.message.lower().startswith(
                        'similar sessão'
                    ):
                        word = ' '.join(text.message.split(' ')[2:-2])
                        message = await nlp_similar_session(furhat_id,
                            word)
                    elif text.message.lower().startswith('similar'):
                        word = ' '.join(text.message.split(' ')[1:-2])
                        message = await nlp_similar(furhat_id, word)
                    elif text.message.lower().startswith(
                        'concordância sessão'
                    ):
                        word = ' '.join(text.message.split(' ')[2:-2])
                        message = await nlp_concordance_session(
                            furhat_id,
                            word,
                        )
                    elif text.message.lower().startswith(
                        'concordância'
                    ):
                        word = ' '.join(text.message.split(' ')[1:-2])
                        message = await nlp_concordance(furhat_id, word)
                    elif text.message.lower().startswith(
                        'contexto sessão'
                    ):
                        words = text.message.split(' ')[2:-2]
                        message = await nlp_common_context_session(
                            furhat_id,
                            words,
                        )
                    elif text.message.lower().startswith(
                        'contexto'
                    ):
                        words = text.message.split(' ')[1:-2]
                        message = await nlp_common_context(furhat_id,
                            words)
                    await blue_speak(furhat, message)
                elif text.message.lower() in [
                    'português',
                    'portugués',
                    'portuguese',
                ]:
                    await asyncio.sleep(1)
                    await led_blue(furhat)
                    language = 'pt-BR'
                    await change_voice(furhat, voices, language)
                    await do_attend_user(furhat, 'RANDOM')
                    await do_say_text(furhat, u"""Agora eu vou falar e \
escutar em português brasileiro.""")
                elif text.message.lower() in [
                    'inglês',
                    'inglés',
                    'english',
                ]:
                    await asyncio.sleep(1)
                    await led_blue(furhat)
                    language = 'en-US'
                    await change_voice(furhat, voices, language)
                    await do_attend_user(furhat, 'RANDOM')
                    await do_say_text(furhat, u"""Now I'm listening and\
 speaking in united states english.""")
                elif text.message.lower() in [
                    'espanhol',
                    'español',
                    'spanish',
                ]:
                    await asyncio.sleep(1)
                    await led_blue(furhat)
                    language = 'es-ES'
                    await change_voice(furhat, voices, language)
                    await do_attend_user(furhat, 'RANDOM')
                    await do_say_text(furhat, u"""Ahora yo voy a hablar\
 e escuchar en español""")
                elif text.message.lower() in [
                    'francês',
                    'francesc',
                    'french',
                ]:
                    await asyncio.sleep(1)
                    await led_blue(furhat)
                    await do_attend_user(furhat, 'RANDOM')
                    audio = random.choice([
                        # ~ 'boil',
                        'fart',
                        'french',
                        'hamster',
                        # ~ 'kniggits',
                        # ~ 'nomore',
                        # ~ 'pigdog',
                        # ~ 'taunt',
                        # ~ 'wipe',
                    ])
                    # ~ audio = 'frenchtaunter'
                    await do_say_url(
                        furhat,
                        ''.join([voice_url + audio + '.wav']),
                    )
                else:
                    if log_messages:
                        await set_furhat_text(
                            furhat_id,
                            session_id,
                            text,
                        )
                    iterations =  None
                    iterations = await furhat_handler(
                        bots_config,
                        bots,
                        text,
                    )
                    if len(iterations) > 0:
                        for iteration in iterations:
                            generated_text = await iteration.callback
                            if generated_text is not None:
                                await do_attend_user(furhat, 'RANDOM')
                                await led_red(furhat)
                                await set_led(
                                    furhat,
                                    **bots_config[iteration.bot][
                                        'furhat']['led'],
                                )
                                await set_voice(
                                    furhat,
                                    name = bots_config[iteration.bot][
                                        'furhat']['voice'],
                                )
                                await set_face(
                                    furhat,
                                    mask = bots_config[iteration.bot][
                                        'furhat']['mask'],
                                    character = bots_config[
                                        iteration.bot]['furhat'][
                                        'character'],
                                )
                                block_do_say_text(
                                    furhat,
                                    generated_text,
                                )
                                await asyncio.sleep(3)
                await led_blank(furhat)
                continue
    except MaxRetryError:
        logger.info(u"""Furhat Remote API is not online. You need a Fur\
hat Robot connected to a reachable network running the Remote API Skill\
. Reference: https://docs.furhat.io/remote-api/""")
    except KeyboardInterrupt:
        logger.info(u"Closing loop")
    except Exception as exception:
        logger.critical(u"Blocking exception: {}".format(
            repr(exception)
        ))
        raise
