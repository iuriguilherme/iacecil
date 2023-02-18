"""
ia.cecil

Copyleft 2012-2023 Iuri Guilherme <https://iuri.neocities.org/>

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

## TODO: / FIXME: Pamordedio refatorar essa merda, quase 600 linhas de 
## código??? Umas práticas de programação que não se justificam nem no tempo 
## da Vegga que era tudo na pressa, na urgência, nas coxa, na ansiedade e na 
## ejaculação precoce

import logging
logger: logging.Logger = logging.getLogger(__name__)

# ~ import glob, os
import aiohttp
import asyncio
import openai
import random
import typing
import uuid
from urllib3.exceptions import (
    MaxRetryError,
    NewConnectionError,
)
from ..remote_api import (
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
from ....models.furhat_models import Status
from ...util import (
    dice_high,
    dice_low,
)
from ...persistence.zodb_orm import (
    # ~ get_messages_texts_list,
    # ~ get_furhat_texts_messages,
    set_furhat_text,
)
# ~ from ....plugins.natural import (
    # ~ generate,
    # ~ concordance,
    # ~ collocations,
    # ~ common_contexts,
    # ~ count,
    # ~ similar,
# ~ )
from ..controllers.furhat_controllers import (
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
from ..controllers.natural_controllers import(
    natural_handler,
)
from ..controllers.zodb_controllers import(
    zodb_get_session,
    zodb_get_sessions,
    zodb_get_aiogram,
)
from ...personalidades import (
    gerar_comando,
    gerar_texto,
    generate_command_furhat,
    generate_text_furhat,
)
from .handlers import (
    furhat_handler,
)
from plugins.borogodo import perguntas, respostas
from ...._version import __version__ as iacecil_version

async def olhar(furhat: object, *args, **kwargs) -> None:
    """Makes Furhat look for the first person or the closest one"""
    try:
        await do_attend_user(furhat, 'CLOSEST')
        # ~ await do_attend_id(furhat, '0')
    except Exception as e:
        logger.exception(e)
        # ~ await do_attend_user(furhat, 'CLOSEST')

async def calcular_delay_simples(
    tamanho: int,
    razão: float = 9.6,
    *args,
    **kwargs,
) -> float:
    """Quantidade de letras dividido por razão arbitrária (padrão 9.6)"""
    return tamanho / razão

async def calcular_delay_razão(tamanho: int, *args, **kwargs) -> float:
    """Faixas de razões arbitrária de acordo com tamanho da sentença"""
    razão: float = 1.0
    if tamanho in range(1, 9):
        razão: float = 3
    elif tamanho in range(9, 18):
        razão: float = 6
    elif tamanho in range(18, 43):
        razão: float = 9.6
    elif tamanho in range(43, 55):
        razão: float = 10.2
    elif tamanho in range(55, 76):
        razão: float = 11.1
    elif tamanho in range(76, 86):
        razão: float = 11.4
    elif tamanho in range(86, 91):
        razão: float = 11.7
    elif tamanho in range(91, 121):
        razão: float = 12.0
    elif tamanho in range(121, 151):
        razão: float = 12.3
    elif tamanho in range(151, 251):
        razão: float = 12.6
    elif tamanho in range(251, 301):
        razão: float = 12.9
    elif tamanho in range(301, 320):
        razão: float = 13.2
    elif tamanho in range(320, 400):
        razão: float = 13.5
    elif tamanho in range(400, 500):
        razão: float = 13.8
    elif tamanho in range(500, 600):
        razão: float = 14.1
    elif tamanho in range(600, 900):
        razão: float = 14.4
    elif tamanho in range(901, 1500):
        razão: float = 15
    else:
        razão: float = 30
    return razão

async def calcular_delay_3(
    texto: str,
    vírgulas: int,
    pontos_finais: int,
    linhas_novas: int,
    números: int,
    pausa_vírgula: float,
    pausa_pontos_finais: float,
    pausa_linhas_novas: float,
    pausa_número: float,
    soma_vírgula: float,
    soma_pontos_finais: float,
    soma_linhas_novas: float,
    soma_número: float,
    razão: float = 9.6,
    *args,
    **kwargs,
) -> float:
    """Adiciona delay a cada vírgula, ponto final, linha nova e a cada \
dígito, porque vai ser falado por extenso."""
    razão: float = await calcular_delay_razão(len(texto))
    cálculo: float = await calcular_delay_simples(len(texto), razão) + \
        soma_número + soma_vírgula + soma_pontos_finais + \
        soma_linhas_novas
    logger.info(f"""Método 3: Calculando delay com {len(texto)} \
caracteres, razão {razão}, {vírgulas} vírgulas, {pontos_finais} pontos \
finais, {números} números, pausa para vírgula {pausa_vírgula}, pausa \
para pontos finais {pausa_pontos_finais}, pausa para linhas novas \
{pausa_linhas_novas}, pausa para números {pausa_número}: ({len(texto)} \
/ {razão}) + ({vírgulas} * {pausa_vírgula}) + ({pontos_finais} * \
{pausa_pontos_finais}) + ({linhas_novas} * {pausa_linhas_novas}) + (\
{números} * {pausa_número}) = {cálculo}""")
    return cálculo

async def calcular_delay(
    texto: str,
    razão: float = 9.6,
    pausa_vírgula: float = 0.3,
    pausa_pontos_finais: float = 0.3,
    pausa_linhas_novas: float = 0.3,
    pausa_número: float = 0.3,
    *args,
    **kwargs,
) -> float:
    """Algoritmo para tentar calcular delay de fala da Furhat"""
    vírgulas: int = texto.count(',')
    pontos_finais: int = texto.count('.')
    linhas_novas: int = texto.count('\n')
    números: int = sum([texto.count(str(número)) for número in range(0,9)])
    soma_número: float = números * pausa_número
    soma_vírgula: float = vírgulas * pausa_vírgula
    soma_pontos_finais: float = pontos_finais * pausa_pontos_finais
    soma_linhas_novas: float = linhas_novas * pausa_linhas_novas
    return await calcular_delay_3(
        texto,
        vírgulas,
        pontos_finais,
        linhas_novas,
        números,
        pausa_vírgula,
        pausa_pontos_finais,
        pausa_linhas_novas,
        pausa_número,
        soma_vírgula,
        soma_pontos_finais,
        soma_linhas_novas,
        soma_número,
        razão,
    )

async def falar(
    furhat: object,
    text: str,
    delay: float = 9.6,
    *args,
    **kwargs,
) -> None:
    """Waits for the Furhat to finish speaking to do next thing"""
    await do_say_text(furhat, text)
    await asyncio.sleep(await calcular_delay(text, delay))

async def atender(
    furhat: object,
    text: str,
    delay: float = 9.6,
    *args,
    **kwargs,
) -> None:
    """Makes Furhat look at nearest person and speak"""
    # ~ await olhar(furhat)
    await do_attend_user(furhat, 'CLOSEST')
    await falar(furhat, text, delay = delay)
    # ~ await do_attend_location(furhat, x = 0.0, y = 1.0, z = 0.0)

async def croak(
    furhat,
    *args,
    exception: typing.Union[Exception, None] = None,
    **kwargs,
) -> None:
    """Behaviour when exception or error occurs"""
    if exception is not None:
        logger.exception(exception)
    await atender(furhat, "Me perdi.")
    await atender(furhat, """Na verdade, o programador é que errou. \
Mas quem passa vergonha sou eu.""")
    await led_blank(furhat)

async def get_prompt_default(text: str) -> str:
    """Q/A chatGPT prompt"""
    return f"Pergunta: {text}\nResposta:"

async def get_prompt_paola_1(text: str) -> str:
    """Paola chatGPT teste um"""
    return f"Paola é uma robô gentil.\n\nEu: {text}\nPaola:"

async def get_prompt_paola_2(text: str) -> str:
    """Paola chatGPT teste dois"""
    return f"""Paola é uma robô que responde com relutância e de forma \
sarcástica.\n\nEu: {text}\nPaola:"""

async def get_prompt_paola_3(text: str) -> str:
    """Paola chatGPT teste três"""
    return f"""Paola é uma robô sarcástica que fala em português \
brasileiro.\n\nEu: {text}\nPaola:"""

async def get_prompt_paola_4(text: str) -> str:
    """Paola chatGPT teste quatro"""
    return f"""Paola é uma robô social fabricada pela empresa Furhat, \
com personalidade sarcástica e que fala em português brasileiro.\n\n\
Eu: {text}\nPaola:"""

async def get_prompt_paola_5(text: str) -> str:
    """Paola chatGPT teste cinco"""
    return f"""Paola é uma especialista em matemática.\n\nEu: {text}\n\
Paola:"""

async def get_prompt_paola_6(text: str) -> str:
    """Paola chatGPT teste seis"""
    return f"""Paola é uma humana especialista em matemática.\nPaola \
fica irritada quando chamam ela de robô.\n\nEu: {text}\nPaola:"""

async def get_prompt_paola_7(text: str) -> str:
    """Paola chatGPT teste sete"""
    return f"Paola é uma robô falando sozinha.\n\nPaola: {text}\nPaola:"

async def get_prompt_paola_8(text: str) -> str:
    """Paola chatGPT teste oito"""
    # ~ text: str = random.choice(["João", "Maria", "Yuri"]) + f": {text}"
    return f"""Paola é uma robô gentil em uma sala de aula. João é um \
engenheiro que responde com relutância e de forma sarcástica. Maria is \
an architect which only speaks in english and give funny answers. Yuri \
é um Desenvolvedor de Software.\n\nYuri: {text}\nPaola:"""

async def get_prompt_paola_9(*args, **kwargs) -> str:
    """Paola chatGPT teste nove"""
    # ~ return f"""Paola é uma robô gentil, solícita e atenciosa. \
# ~ João é um engenheiro que responde com relutância e de forma \
# ~ sarcástica. \
# ~ Maria is an architect which only speaks in english and give funny \
# ~ answers. \
# ~ Yuri é um Desenvolvedor de Software tentando programar a robô Paola.\
# ~ Paola:"""
    return f"""Paola é uma robô gentil, solícita e atenciosa. Ela está \
convencida de que é um ser humano especialista em matemática, e fica \
ofendida quando alguém chama ela de robô. \
João é um engenheiro que responde com relutância e de forma \
sarcástica e jocosa. \
Maria is an architect which only speaks in english and give funny \
and clever answers. \
Yuri é um Desenvolvedor de Software tentando programar uma robô social.\
"""

async def get_prompt_paola_10(text: str, *args, **kwargs) -> str:
    """Paola chatGPT teste dez"""
    # ~ return f"""Paola é uma robô gentil, solícita e atenciosa. \
# ~ João é um engenheiro que responde com relutância e de forma \
# ~ sarcástica. \
# ~ Maria is an architect which only speaks in english and give funny \
# ~ answers. \
# ~ Yuri é um Desenvolvedor de Software tentando programar a robô Paola. \
# ~ \n\nYuri: {text}\n\n"""
    return f"""Paola é uma robô gentil, solícita e atenciosa. Ela está \
convencida de que é um ser humano especialista em matemática, e fica \
ofendida quando alguém chama ela de robô. \
João é um engenheiro que responde com relutância e de forma \
sarcástica e jocosa. \
Maria is an architect which only speaks in english and give funny \
and clever answers. \
Yuri é um Desenvolvedor de Software tentando programar uma robô social.\
\n\nYuri: {text}\n\nPaola:"""

async def falar_personalidade(
    furhat: object,
    personalidade: str = "default",
    text: str = "Olá.",
    *args,
    **kwargs,
) -> None:
    try:
        mapa_personalidades: dict = {
            "default": {
                "character": "Isabel",
                "voice": "Vitoria-Neural",
            },
            "Paola": {
                "character": "Kione",
                "voice": "Camila-Neural",
            },
            "João": {
                "character": "Gyeong",
                "voice": "Cristiano",
            },
            "Maria": {
                "character": "Yumi",
                "voice": "Kevin-Neural",
            },
            "Yuri": {
                "character": "Titan",
                "voice": "Ricardo",
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
        logger.info(f"""{personalidade} falando com voz {voice} e \
máscara {character}:\n{text}\n\n""")
        await led_blue(furhat)
        await set_voice(furhat, voice)
        await set_face(furhat, character = character)
        await atender(furhat, text)
        await led_blank(furhat)
        await asyncio.sleep(1e-15)
    except Exception as e:
        logger.exception(e)
        await croak(furhat, exception = e)

async def multiplos_personagens(furhat: object, text: str) -> None:
    """Teste GPT3 múltiplos personagens + Furhat múltiplos personagens\
"""
    try:
        logger.info(f"Recebido texto do ChatGPT:\n{text}\n")
        # ~ text: list = '\n'.join(text.split('\n\n')).split('\n')
        text: list = text.split('\n\n')
        new_text: list = []
        for sentence in text:
            if len(sentence.split('\n')) > 1:
                if sum([len(s.split(':')) > 1 for s in \
                    sentence.split('\n')]) > 1:
                    new_text.append(sentence.split('\n')[0])
                    new_text.append('\n'.join(sentence.split('\n')[1:]))
                    continue
            new_text.append(sentence)
        text: list = new_text
        await falar_personalidade(furhat, "Paola", text[0])
        for sentence in text[1:]:
            sentence: list = sentence.split(':')
            await falar_personalidade(
                furhat,
                sentence[0],
                ':'.join(sentence[1:]),
            )
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
            await atender(furhat, f"""Olá. Eu sou uma burrice \
artificial, versão {iacecil_version}. Aguarde a conexão com o chát \
gêpetê, até que o LED fique verde para começar a falar.""")
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
            prompt: str = await get_prompt_paola_9()
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
        except Exception as e:
            logger.exception(e)
            if openai.aiosession.get() is not None:
                await openai.aiosession.get().close()
            await croak(furhat, exception = e)
            return
        logger.info("""Tudo pronto, quando o LED ficar verde, é só \
começar a falar!""")
        while True:
            await do_attend_location(furhat, x = 0.0, y = 1.0, z = 0.0)
            if openai.aiosession.get() is None:
                openai.aiosession.set(aiohttp.ClientSession())
            text: Status | None = Status()
            await asyncio.sleep(float(
                print('Ouvindo', end = '') or 1e-12))
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
            logger.info(f"Ouvido:\n{text.message}\n\n")
            for stop in ['por favor cala a boca', 'cala a boca']:
                if stop in text.message:
                    await atender(furhat, """Não grita comigo! Dessa \
vez eu vou calar a boca, mas não acostuma. Bom dia!""")
                    return
            prompt: str = await get_prompt_paola_10(text.message)
            try:
                await led_yellow(furhat)
                logger.info("""Criando completação com a API do chatGPT\
...""")
                completion: object = openai.Completion.create(
                    # ~ engine = openai_config.get('engine', 'text-ada-001'),
                    engine = 'text-davinci-003',
                    # ~ max_tokens = openai_config.get(
                        # ~ 'max_tokens', 4000) - len(prompt), # 1 to 4000
                    max_tokens = 4000 - len(prompt),
                    # ~ temperature = openai_config.get(
                        # ~ 'temperature', 0.6), # 0.0 to 1.0
                    # ~ top_p = openai_config.get(
                        # ~ 'top_p', 0.1), # 0.0 to 1.0
                    top_p = 0.1,
                    # ~ frequency_penalty = openai_config.get(
                        # ~ 'frequency_penalty', 1.0), # 0.0 to 2.0
                    frequency_penalty = 2.0,
                    # ~ presence_penalty = openai_config.get(
                        # ~ 'presence_penalty', 1.0), # 0.0 to 2.0
                    presence_penalty = 2.0,
                    # ~ echo = openai_config.get('echo', False),
                    # ~ n = 2,
                    user = str(user),
                    prompt = prompt,
                    # ~ stop = ['Paola:', 'Eu:', 'Você:'],
                )
                # ~ logger.debug(f"Completion ({type(completion)} = {completion}")
                logger.debug(f"""Completion ({type(completion)}), 
{len(completion)} = {completion}""")
                choice: dict = random.choice(completion.choices)
                # ~ await olhar(furhat)
                t: str = choice.get('text')
                # ~ await do_say_text(furhat, t)
                # ~ logger.info(f"Falando:\n{t}")
                # ~ await atender(furhat, t)
                await multiplos_personagens(furhat, t)
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
                await atender(furhat, """O Chat GPT não tá \
funcionando, eu não sei o que responder. Espere um pouco e tente de \
novo.""")
                continue
            except (
                openai.error.APIError,
                openai.error.InvalidRequestError,
                Exception,
            ) as e:
                logger.exception(e)
                await atender(furhat, "Não sei")
                if openai.aiosession.get() is not None:
                    await openai.aiosession.get().close()
                continue
            # ~ finally:
                # ~ if openai.aiosession.get() is not None:
                    # ~ await openai.aiosession.get().close()
            await asyncio.sleep(1e-12)
    except (MaxRetryError, NewConnectionError, KeyboardInterrupt):
        raise
    except Exception as e:
        await croak(furhat, exception = e)
        return
    finally:
        if openai.aiosession.get() is not None:
            await openai.aiosession.get().close()

async def personas(
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
        address: str = furhat_config['address']
        furhat = await get_furhat(address)
        await led_blue(furhat)
        order: str = 'por favor'
        furhat_id: str = furhat_config['bot']
        language: str = furhat_config['language']
        mask: str = furhat_config['mask']
        character: str = furhat_config['character']
        voice: str = furhat_config['voice']
        voice_url: str = furhat_config['voice_url']
        session_id = uuid.uuid4()
        # ~ voices = await get_voices(furhat)
        # ~ logger.info(voices)
        await set_face(furhat, mask, character)
        await set_voice(furhat, voice)
        await do_attend_user(furhat, 'CLOSEST')
        if not skip_intro:
            await atender(furhat, """iniciando modo de múltiplas pe\
rsonalidades""")
        await led_blank(furhat)
        # ~ await programa_antigo(bots, furhat_config, bots_config,
            # ~ skip_intro, log_messages, add_startswith, add_endswith,
            # ~ order, furhat_id, address, language, mask, character, voice,
            # ~ voice_url, session_id, furhat, voices)
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
        logger.error("""Furhat Remote API is not online. You need a Furhat \
Robot connected to a reachable network running the Remote API Skill. \
Reference: https://docs.furhat.io/remote-api/""")
    except KeyboardInterrupt:
        logger.critical("Closing loop")
    except Exception as e:
        logger.exception(e)
        await blue_speak(
            furhat,
            "Desculpe, tive um problema técnico. Chama o Yuri!",
        )
