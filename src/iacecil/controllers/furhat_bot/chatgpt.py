"""
ia.cecil

Copyleft 2012-2025 Iuri Guilherme <https://iuri.neocities.org/>

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
logger: logging.Logger = logging.getLogger(__name__)

# ~ import glob
import aiohttp
import asyncio
import openai
import os
import random
import typing
import uuid
from urllib3.exceptions import (
    MaxRetryError,
    NewConnectionError,
)
from .remote_api import (
    get_furhat,
    get_voices,
    set_face,
    set_led,
    set_voice,
    do_attend_location,
    do_attend_id,
    do_attend_user,
    do_listen,
    do_say_text,
    do_say_url,
    # ~ block_do_listen,
    block_do_say_text,
    block_do_say_url,
)
from ...models.furhat_models import Status
from ..util import (
    dice_high,
    dice_low,
)
from ..persistence.zodb_orm import (
    # ~ get_messages_texts_list,
    # ~ get_furhat_texts_messages,
    set_furhat_text,
)
# ~ from ...plugins.natural import (
    # ~ generate,
    # ~ concordance,
    # ~ collocations,
    # ~ common_contexts,
    # ~ count,
    # ~ similar,
# ~ )
from .controllers.furhat_controllers import (
    blue_speak,
    change_voice,
    led_blank,
    led_blue,
    led_green,
    led_red,
    led_white,
    led_yellow,
    shutup,
)
from .controllers.natural_controllers import(
    natural_handler,
)
from .controllers.zodb_controllers import(
    zodb_get_session,
    zodb_get_sessions,
    zodb_get_aiogram,
)
from ..personalidades import (
    gerar_comando,
    gerar_texto,
    generate_command_furhat,
    generate_text_furhat,
)
from .personas.handlers import (
    furhat_handler,
)
from plugins.borogodo import perguntas, respostas
from ..._version import __version__ as iacecil_version
from .personas import (
    olhar,
    calcular_delay_simples,
    calcular_delay_razão,
    calcular_delay_3,
    calcular_delay,
    falar,
    atender,
    croak,
    falar_personalidade,
    multiplos_personagens,
)

async def croak(
    furhat,
    *args,
    exception: typing.Union[Exception, None] = None,
    **kwargs,
) -> None:
    """Behaviour when exception or error occurs"""
    if exception is not None:
        logger.exception(exception)
    await atender(furhat, "I lost myself.")
    await atender(furhat, """Actually, the programmer messed up. \
but I'm the one here being embarrassed.""")
    await led_blank(furhat)

async def get_prompt(
    *args,
    text: str = "",
    prompt: dict = {'before': "Me: ", 'after': ""},
    **kwargs,
) -> str:
    """ChatGPT prompt"""
    return prompt.get('before', "Me: ") + text + prompt.get('after', "")

async def single_personality(
    furhat: object,
    text: str = "Hello.",
    *args,
    **kwargs,
) -> None:
    """Single personality Furhat robot"""
    try:
        personalidade: None = None
        mapa_personalidades: dict = {
            "default": {
                "character": os.getenv("FURHAT_CHARACTER",
                    default = "Titan"),
                "voice": os.getenv("FURHAT_VOICE",
                    default = "Joanna-Neural"),
            },
        }
        voice: str = mapa_personalidades.get(
            personalidade,
            mapa_personalidades.get('default')
        ).get('voice')
        character: str = mapa_personalidades.get(
            personalidade,
            mapa_personalidades.get('default')
        ).get('character')
        logger.info(f"""{personalidade} speaking with Polly voice \
{voice} and Furhat mask {character}:\n{text}\n\n""")
        await led_blue(furhat)
        await set_voice(furhat, voice)
        await set_face(furhat, character = character)
        for t in text.split('\n'):
            if t not in ['', ' ', None]:
                await atender(furhat, t)
        await led_blank(furhat)
        await asyncio.sleep(1e-15)
    except Exception as e:
        logger.exception(e)
        await croak(furhat, exception = e)

async def chatgpt(
    furhat: object, 
    language: str,
    furhat_id: str,
    session_id: uuid.UUID,
    openai_config: dict,
    skip_intro: bool,
    furhat_config: dict,
    *args,
    **kwargs,
) -> None:
    """Interage com GPT3"""
    try:
        await led_white(furhat)
        skip_intro: bool = False
        if not skip_intro:
            await atender(furhat, f"""Hello. I am a Furhat Robot \
running an artificial cleverness software version {iacecil_version}. \
Please wait for the connection with Open A.I. and wait for the led to \
become green to start interaction.""")
        openai.api_key: str = openai_config['api_keys'][0]
        logging.getLogger('openai').setLevel('INFO')
        try:
            await led_red(furhat)
            openai.aiosession.set(aiohttp.ClientSession())
            user: uuid.UUID = uuid.uuid5(session_id, furhat_id)
            logger.info("Furhat + chatGPT pronto!")
            logger.info("""Fazendo requisição para iniciar novo \
documento com a API do OpenAI...""")
            completion: object = openai.Completion.create(
                engine = openai_config.get('engine',
                    'text-davinci-003'),
                max_tokens = 4000,
                user = str(user),
            )
            logger.debug(f"""Completion ({type(completion)}), 
{len(completion)} = {completion}""")
            prompt: str = await get_prompt(
                prompt = furhat_config.get('prompt'))
            logging.info(f"Usando prompt:\n{prompt}")
            completion: object = openai.Completion.create(
                engine = openai_config.get('engine',
                    'text-davinci-003'),
                max_tokens = openai_config.get(
                    'max_tokens', 4000) - len(prompt), # 1 to 4000
                top_p = openai_config.get(
                    'top_p', 0.1), # 0.0 to 1.0
                user = str(user),
                prompt = prompt,
            )
            logger.debug(f"""Completion ({type(completion)}), 
{len(completion)} = {completion}""")
            # ~ choice: dict = random.choice(completion.choices)
            # ~ t: str = choice.get('text')
            # ~ await multiplos_personagens(furhat, t)
        except openai.error.RateLimitError as e:
            logger.exception(e)
            await atender(furhat, """Well this is embarrassing. Looks \
like someone didn't pay the OpenAI bill or didn't setup the correct \
key. I cannot connect with my brain from ChatGPT!""")
        except Exception as e:
            logger.exception(e)
            if openai.aiosession.get() is not None:
                await openai.aiosession.get().close()
            await croak(furhat, exception = e)
            return
        logger.info("""All set, when LED is green, you may start \
talking!""")
        while True:
            await do_attend_location(furhat, x = 0.0, y = 1.0, z = 0.0)
            if openai.aiosession.get() is None:
                openai.aiosession.set(aiohttp.ClientSession())
            text: Status | None = Status()
            await asyncio.sleep(float(
                print('Listening', end = '') or 1e-12))
            while (\
                text.message in [None, '', ' '] \
                or 'ERROR : No internet detected' in text.message \
                # ~ or len(text.message) < 12 \
            ):
                await led_green(furhat)
                await do_attend_user(furhat, 'CLOSEST')
                await asyncio.sleep(float(print('.', end = '') or 1e-6))
                try:
                    text: Status | None = await do_listen(furhat,
                        language)
                except Exception as e:
                    logger.exception(e)
                    text: Status | None = Status()
                await asyncio.sleep(float(
                    print('.', end = '') or 1e-12))
            await asyncio.sleep(float(print() or 1e-12))
            if not text.message:
                continue
            logger.info(f"Heard:\n{text.message}\n\n")
            for stop in ['please shut up', 'shut up']:
                if stop in text.message:
                    await atender(furhat, """Don't yell at me! This \
time I'm gonna shut up, but don't get used to it. Have a nice day!""")
                    return
            prompt: str = await get_prompt(
                text = text.message,
                prompt = furhat_config.get('prompt'),
            )
            logging.info(f"Usando prompt:\n{prompt}")
            try:
                await led_yellow(furhat)
                logger.info("Creating completion with ChatGPT...")
                completion: object = openai.Completion.create(
                    engine = openai_config.get('engine',
                      'text-davinci-003'),
                    max_tokens = openai_config.get(
                        'max_tokens', 4000) - len(prompt),
                    # ~ temperature = openai_config.get(
                        # ~ 'temperature', 0.6), # 0.0 to 1.0
                    top_p = openai_config.get(
                        'top_p', 0.1), # 0.0 to 1.0
                    frequency_penalty = openai_config.get(
                        'frequency_penalty', 2.0), # 0.0 to 2.0
                    presence_penalty = openai_config.get(
                        'presence_penalty', 2.0), # 0.0 to 2.0
                    # ~ echo = openai_config.get('echo', False),
                    # ~ n = 2,
                    user = str(user),
                    prompt = prompt,
                    # ~ stop = ['Paola:', 'Eu:', 'Você:'],
                )
                logger.debug(f"""Completion ({type(completion)}), 
{len(completion)} = {completion}""")
                choice: dict = random.choice(completion.choices)
                # ~ await olhar(furhat)
                t: str = choice.get('text')
                # ~ await do_say_text(furhat, t)
                # ~ logger.info(f"Falando:\n{t}")
                # ~ await atender(furhat, t)
                # ~ await multiplos_personagens(furhat, t)
                await single_personality(furhat, t)
                await led_red(furhat)
                await set_furhat_text(
                    furhat_id,
                    session_id,
                    text,
                )
                await led_blank(furhat)
            except (
                openai.error.RateLimitError,
                openai.error.ServiceUnavailableError,
                openai.error.Timeout,
            ) as e:
                logger.exception(e)
                await atender(furhat, """Chat GPT is not working, and \
I don't know what to answer. Either try again later or debug me.""")
                continue
            except (
                openai.error.APIError,
                openai.error.InvalidRequestError,
                Exception,
            ) as e:
                logger.exception(e)
                await atender(furhat, "I don't know.")
                if openai.aiosession.get() is not None:
                    await openai.aiosession.get().close()
                continue
            await asyncio.sleep(1e-12)
    except (MaxRetryError, NewConnectionError, KeyboardInterrupt):
        raise
    except Exception as e:
        await croak(furhat, exception = e)
        return
    finally:
        if openai.aiosession.get() is not None:
            await openai.aiosession.get().close()

async def gptparrot(
    bots: list,
    furhat_config: dict,
    bots_config: object,
    openai_config: dict,
    skip_intro: bool = False,
    log_messages = True,
    add_startswith = None,
    add_endswith = None,
):
    try:
        address: str = furhat_config.get('address')
        furhat = await get_furhat(address)
        await led_blue(furhat)
        order: str = 'por favor'
        furhat_id: str = furhat_config.get('bot')
        language: str = furhat_config.get('language')
        mask: str = furhat_config.get('mask')
        character: str = furhat_config.get('character')
        voice: str = furhat_config.get('voice')
        voice_url: str = furhat_config.get('voice_url')
        session_id = uuid.uuid4()
        await set_face(furhat, mask, character)
        await set_voice(furhat, voice)
        await do_attend_user(furhat, 'CLOSEST')
        await chatgpt(
            furhat,
            language,
            furhat_id,
            session_id,
            openai_config,
            skip_intro,
            furhat_config,
        )
    except (MaxRetryError, NewConnectionError) as e:
        logger.exception(e)
        logger.error("""Furhat Remote API is not online. You need a \
Furhat Robot connected to a reachable network running the Remote API \
Skill, or the Furhat SDK running a Virtual Furhat with the Remote API \
Skill on. Reference: https://docs.furhat.io/remote-api/""")
    except KeyboardInterrupt:
        logger.critical("Closing loop")
    except Exception as e:
        logger.exception(e)
        await blue_speak(
            furhat,
            "I am sorry, I had a technical issue. Call the programmer!",
        )
