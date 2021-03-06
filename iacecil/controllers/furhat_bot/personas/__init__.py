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
    # ~ block_do_listen,
    block_do_say_text,
    block_do_say_url,
)
from iacecil.models.furhat_models import Status
from iacecil.controllers.persistence.zodb_orm import (
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
from iacecil.controllers.furhat_bot.controllers.furhat_controllers import (
    blue_speak,
    change_voice,
    led_blank,
    led_blue,
    led_green,
    led_red,
    led_white,
    shutup,
)
from iacecil.controllers.furhat_bot.controllers.natural_controllers import(
    natural_handler,
)
from iacecil.controllers.furhat_bot.controllers.zodb_controllers import(
    zodb_get_session,
    zodb_get_sessions,
    zodb_get_aiogram,
)
from iacecil.controllers.personalidades import (
    gerar_comando,
    gerar_texto,
    generate_command_furhat,
    generate_text_furhat,
)
from iacecil.controllers.furhat_bot.personas.handlers import (
    furhat_handler,
)

try:
    from instance.config import Config
    config = Config()
    bots_config = config.bots
    furhat_config = config.furhat
except Exception as exception:
    logger.critical(u"""{} config file not found or somehow wrong. RTFM\
.\n{}""".format(actual_name, str(exception)))
    raise

async def personas(
    bots,
    furhat_config,
    bots_config,
    skip_intro = False,
    log_messages = True,
    add_startswith = None,
    add_endswith = None,
):
    try:
        order = 'por favor'
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
            await do_say_text(furhat, """iniciando modo de m??ltiplas pe\
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
                    await shutup(furhat)
                elif text.message.lower() in [
                    'chega',
                    'listo',
                    'enough',
                ]:
                    await shutup(furhat)
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
                elif text.message.lower().endswith(order):
                    reply = await natural_handler(furhat, text.message,
                        order, furhat_id, session_id)
                    await blue_speak(furhat, reply)
                elif text.message.lower() in [
                    'portugu??s',
                    'portugu??s',
                    'portuguese',
                ]:
                    await asyncio.sleep(1)
                    await led_blue(furhat)
                    language = 'pt-BR'
                    await change_voice(furhat, voices, language)
                    await do_attend_user(furhat, 'RANDOM')
                    await do_say_text(furhat, u"""Agora eu vou falar e \
escutar em portugu??s brasileiro.""")
                elif text.message.lower() in [
                    'ingl??s',
                    'ingl??s',
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
                    'espa??ol',
                    'spanish',
                ]:
                    await asyncio.sleep(1)
                    await led_blue(furhat)
                    language = 'es-ES'
                    await change_voice(furhat, voices, language)
                    await do_attend_user(furhat, 'RANDOM')
                    await do_say_text(furhat, u"""Ahora yo voy a hablar\
 e escuchar en espa??ol""")
                elif text.message.lower() in [
                    'franc??s',
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
                    if add_startswith is not None:
                        text.message = add_startswith + ' ' + \
                            text.message
                    if add_endswith is not None:
                        text.message = text.message + ' ' + \
                            add_endswith
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
