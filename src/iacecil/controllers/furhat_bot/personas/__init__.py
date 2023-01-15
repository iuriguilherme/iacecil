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

# ~ try:
    # ~ from ....config import Config
    # ~ config = Config()
    # ~ bots_config = config.bots
    # ~ furhat_config = config.furhat_config
# ~ except Exception as e:
    # ~ logger.critical(f"{name} config file not found or somehow wrong. RTFM.")
    # ~ logger.exception(e)
    # ~ raise

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
        razão: float = 12.3
    elif tamanho in range(76, 86):
        razão: float = 12.6
    elif tamanho in range(86, 90):
        razão: float = 12.9
    elif tamanho in range(90, 151):
        razão: float = 13.2
    elif tamanho in range(151, 251):
        razão: float = 13.5
    elif tamanho in range(251, 301):
        razão: float = 13.8
    elif tamanho in range(301, 320):
        razão: float = 14.1
    elif tamanho in range(320, 400):
        razão: float = 14.7
    elif tamanho in range(400, 500):
        razão: float = 15
    elif tamanho in range(500, 600):
        razão: float = 16.5
    elif tamanho in range(600, 900):
        razão: float = 18.9
    elif tamanho in range(901, 1500):
        razão: float = 21.6
    else:
        razão: float = 30
    return razão

async def calcular_delay_3(
    texto: str,
    vírgulas: int,
    números: int,
    pausa_vírgula: float,
    pausa_número: float,
    soma_vírgula: float,
    soma_número: float,
    razão: float = 9.6,
    *args,
    **kwargs,
) -> float:
    """Adiciona delay a cada vírgula e a cada dígito, porque vai ser falado \
por extenso"""
    razão: float = await calcular_delay_razão(len(texto))
    logger.info(f"""Método 3: ({len(texto)} / {razão}) + ({vírgulas} * \
{pausa_vírgula}) + ({números} * {pausa_número}) = \
{(len(texto) / razão) + soma_vírgula + soma_número}""")
    return await calcular_delay_simples(len(texto), razão) + \
        soma_número + soma_vírgula

async def calcular_delay(
    texto: str,
    razão: float = 9.6,
    pausa_vírgula: float = 0.3,
    pausa_número: float = 0.3,
    *args,
    **kwargs,
) -> float:
    """Algoritmo para tentar calcular delay de fala da Furhat"""
    vírgulas: int = texto.count(',')
    números: int = sum([texto.count(str(número)) for número in range(0,9)])
    soma_número: float = números * pausa_número
    soma_vírgula: float = vírgulas * pausa_vírgula
    logger.info(f"""Calculando delay com {len(texto)} caracteres, \
razão {razão}, {vírgulas} vírgulas, {números} números, pausa para \
vírgula {pausa_vírgula}, pausa para números {pausa_número}...""")
    return await calcular_delay_3(
        texto,
        vírgulas,
        números,
        pausa_vírgula,
        pausa_número,
        soma_vírgula,
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
    await do_attend_location(furhat, x = 0.0, y = 1.0, z = 0.0)

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
    await atender(furhat, """Na verdade, o programador é que errou. Mas quem \
passa vergonha sou eu.""")
    await led_blank(furhat)

async def ack(furhat, *args, **kwargs) -> None:
    await led_blank(furhat)
    await do_say_text(
        furhat,
        "ok, deixa eu me preparar para mais uma entrevista",
    )
    await led_blank(furhat)
    await do_attend_location(furhat, x = 0, y = -30, z = 0)
    await asyncio.sleep(3)

async def borogodo_podcast_1(furhat, *args, **kwargs) -> None:
    try:
        await olhar(furhat)
        await led_blue(furhat)
        await do_say_text(
            furhat,
            """Vou treinar a entrevista pro podcast. Tentativa número dois. \
Não me atrapalha por favor""",
        )
        await do_attend_location(furhat, x = 0, y = -30, z = 0)
        await asyncio.sleep(9)
        for k, v in perguntas.items():
            try:
                await led_green(furhat)
                await olhar(furhat)
                await do_say_text(furhat, v)
                await asyncio.sleep(round(len(v)/6))
                await led_red(furhat)
                for r in respostas[k]:
                    await olhar(furhat)
                    await do_say_text(furhat, r)
                    await asyncio.sleep(round(len(r)/6))
            except Exception as e:
                logger.exception(e)
                await croak(furhat, exception=e)
    except Exception as e:
        logger.exception(e)
        await croak(furhat, exception=e)

async def borogodo_naoentendi(furhat, *args, **kwargs) -> None:
    try:
        await olhar(furhat)
        await led_blue(furhat)
        texto: str = random.choice([
            "Oi, eu sou a Gâmbôa. A robô social mais avançada do mundo!",
            "Oi, eu sou a Gâmbôa. A robô social mais avançada do mundo!",
            "Oi, eu sou a Gâmbôa. A robô social mais avançada do mundo!",
            """Eu não entendi nada, mas achei interessante. Vou continuar \
ouvindo vocês""",
            """Eu sou nova e estou formando meu vocabulário, não tenho \
nenhuma resposta inteligente pra te dar agora""",
            """Se eu fosse gente eu ia entender o que vocês dizem. Mas como \
eu sou um computador, só obsérvo e aprendo""",
            "Não grita comigo",
            "Não sei nada sobre o que tu disse, pergunta pro meu programador",
            """Olha, quando o meu programador não tá aqui eu dificilmente sei \
o que responder. Se eu fosse uma inteligência artificial avançada, vocês \
seriam os que respondem as minhas perguntas, e não o contrário. Não é \
verdade?""",
            """Desculpa eu não conseguir falar contigo agora, o meu \
programador tá tomando café e eu não conheço ninguém aqui e não sei o que te \
responder.""",
            """Vocês já viram o visual da praia ali do lado? Larga o celular \
um pouco e vai lá observar as montanhas no continente. Eu só não vou porque \
eu não tenho um corpo""",
        ])
        await atender(furhat, texto)
        await led_blank(furhat)
    except Exception as e:
        await croak(furhat, exception=e)

async def borogodo_teste_1(
    furhat,
    message,
    *args,
    numero = 6,
    **kwargs,
) -> None:
    try:
        texto: str = ' '.join([
            palavra \
            for palavra in \
            message.split(' ') \
            if palavra not in \
            ['teste', 'delay'] \
        ])
        try:
            await do_attend_id(furhat, '0')
        except Exception as e:
            logger.exception(e)
            await do_attend_user(furhat, 'CLOSEST')
        await led_blue(furhat)
        await do_say_text(
            furhat,
            f"""Testando delay entre frases pra ver se {numero} é a \
quantidade boa""")
        await asyncio.sleep(2)
        await led_red(furhat)
        await do_say_text(furhat, texto)
        await asyncio.sleep(round(len(texto)/numero))
        await led_yellow(furhat)
        await do_say_text(furhat, texto)
        await asyncio.sleep(round(len(texto)/numero))
        await led_blank(furhat)
    except Exception as e:
        logger.exception(e)
        await croak(furhat, exception=e)

async def borogodo_foradoar(furhat, *args, **kwargs) -> None:
    try:
        await do_attend_id(furhat, '0')
    except Exception as e:
        logger.exception(e)
        await do_attend_user(furhat, 'CLOSEST')
    await led_blue(furhat)
    # ~ razão: str = "mexendo no meu código"
    # ~ razão: str = "almoçando"
    razão: str = "tomando café"
    await do_say_text(
        furhat,
        f"""Desculpa eu não poder falar contigo agora, o meu programador tá \
{razão} e eu não conheço ninguém aqui e não sei o que te responder.""",
    )
    await asyncio.sleep(12)
    await led_blank(furhat)

async def borogodo_entrevista(
    furhat,
    language,
    furhat_id,
    session_id,
    *args,
    **kwargs,
) -> None:
    try:
        await ack(furhat)
        try:
            await do_attend_id(furhat, '0')
        except Exception as e:
            logger.exception(e)
            await do_attend_user(furhat, 'CLOSEST')
        await blue_speak(
            furhat,
            """Boa tarde! Eu sou a Gâmbôa. E vou te entrevistar. Por favor \
tenha paciência comigo, porque uma parte de mim é só um computador. Quando o \
meu led estiver vermelho, é porque eu estou te ouvindo e prestando atenção. \
A minha pergunta hoje é: Quem és tu, e o que está acontecendo aqui? Fala \
perto do microfone pra eu te ouvir""",
        )
        await asyncio.sleep(26)
        while True:
            text: Status = Status()
            tentativas: int = 0
            sair: bool = False
            while text.message == "":
                await led_red(furhat)
                try:
                    await do_attend_id(furhat, '0')
                except Exception as e:
                    logger.exception(e)
                    await do_attend_user(furhat, 'CLOSEST')
                text: Status = await do_listen(furhat, language)
                await led_yellow(furhat)
                logger.critical(text)
                tentativas += 1
                if tentativas > 6:
                    await do_say_text(
                        furhat,
                        """Não sei se o meu microfone tá ruim, mas acho que \
ninguém mais tá falando comigo, vou encerrar a entrevista."""
                    )
                    await asyncio.sleep(9)
                    sair: bool = True
                    break
                elif tentativas > 2:
                    await do_say_text(furhat, random.choice([
                        """não entendi, fale mais alto. quando não quiser \
mais falar é só dizer: pronto""",
                    ]))
                    await asyncio.sleep(6)
            await set_furhat_text(
                furhat_id,
                session_id,
                text,
            )
            if sair or text.message.lower() in [
                "pronto",
                "pronto.",
                "deu",
                "deu.",
                "chega",
                "chega.",
            ]:
                break
        await led_blank(furhat)
        await olhar(furhat)
        await blue_speak(
            furhat,
            """Obrigada. Por enquanto era só isso, eu preciso de tempo pra \
pensar no que eu ouvi e me reprogramar pra fazer mais perguntas. Minha mente \
só tem três jígarrértz cacacá cacacá"""
        )
        await asyncio.sleep(12)
        await led_blank(furhat)
        await do_attend_location(furhat, x = 0, y = -30, z = 0)
        await asyncio.sleep(3)
    except Exception as e:
        logger.exception(e)
        await blue_speak(
            furhat,
            "Desculpe, tive um problema técnico. Chama o Iûrí!",
        )

async def programa_antigo(bots, furhat_config, bots_config,
    skip_intro, log_messages, add_startswith, add_endswith,
    order, furhat_id, address, language, mask, character, voice,
    voice_url, session_id, furhat, voices) -> None:
    """E fala do código dos outros..."""
    while True:
        text = Status()
        while text.message == '':
            await led_green(furhat)
            await olhar(furhat)
            text =  await do_listen(furhat, language)
        await led_blank(furhat)
        # ~ text = Status(success = True, message = "chega")
        if text.success and text.message not in ['', 'EMPTY'] and \
            not text.message.startswith('ERROR'):
            logger.critical(text)
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
                reply = await natural_handler(
                    furhat,
                    text.message,
                    order,
                    furhat_id,
                    session_id,
                )
                await blue_speak(furhat, reply)
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
                await do_say_text(furhat, """Agora eu vou falar e \
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
                await do_say_text(furhat, """Now I'm listening and \
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
                await do_say_text(furhat, """Ahora yo voy a hablar \
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
            elif text.message.lower() in [
                'oi',
                'olá',
                'ola',
                'alô',
                'alo',
                'e aí',
                'eai',
                'eaí',
                'boa tarde',
                'boatarde',
            ]:
                await borogodo_foradoar(furhat)
            elif text.message.lower() in [
                'tchau',
            ]:
                await blue_speak(furhat, "tchau")
                await asyncio.sleep(1)
            elif text.message.lower() in ['entrevista']:
                ## FIXME isso veio de personalidade.gamboa pra evitar
                ## importação circular
                await borogodo_entrevista(
                    furhat,
                    language,
                    furhat_id,
                    session_id,
                )
            elif text.message.lower() in ['podcast']:
                ## FIXME isso veio de personalidade.gamboa pra evitar
                ## importação circular
                await borogodo_podcast_1(furhat)
            else:
                try:
                    await do_attend_id(furhat, '0')
                except Exception as e:
                    logger.exception(e)
                    await do_attend_user(furhat, 'RANDOM')
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
                if text.message.lower().startswith("teste delay"):
                    logger.critical("teste delay")
                    await borogodo_teste_1(furhat, text.message)
                    continue
                iterations =  None
                iterations = await furhat_handler(
                    bots_config,
                    bots,
                    text,
                )
                # ~ logger.critical(f"iterations = {str(iterations)}")
                if len(iterations) > 0:
                    for iteration in iterations:
                        generated_text = await iteration.callback
                        if generated_text is not None:
                            await do_attend_user(furhat, 'RANDOM')
                            await led_red(furhat)
                            await set_led(
                                furhat,
                                **bots_config[iteration.bot].furhat['led'],
                            )
                            await set_voice(
                                furhat,
                                name = bots_config[iteration.bot].furhat[
                                    'voice'],
                            )
                            await set_face(
                                furhat,
                                mask = bots_config[iteration.bot].furhat[
                                    'mask'],
                                character = bots_config[
                                    iteration.bot].furhat[
                                    'character'],
                            )
                            block_do_say_text(
                                furhat,
                                generated_text,
                            )
                            await asyncio.sleep(3)
                elif await dice_high(12):
                    await borogodo_naoentendi(furhat)
            await led_blank(furhat)
            continue

## FIXME: Não funciona
async def aprint(*args, **kwargs) -> None:
    """asyncio.print()"""
    return print(*args, **kwargs)

async def get_prompt_default(text: str) -> str:
    """Q/A chatGPT prompt"""
    return f"Pergunta: {text}\nResposta:"

async def get_prompt_paola_1(text: str) -> str:
    """Paola chatGPT teste um"""
    return f"Paola é uma robô gentil.\n\nEu: {text}\nPaola:"

async def get_prompt_paola_2(text: str) -> str:
    """Paola chatGPT teste dois"""
    return f"Paola é uma robô sarcástica.\n\n\Eu: {text}\nPaola:"

async def get_prompt_paola_3(text: str) -> str:
    """Paola chatGPT teste três"""
    return f"""Paola é uma robô sarcástica que fala em português brasileiro.\n\
\nEu: {text}\nPaola:"""

async def get_prompt_paola_4(text: str) -> str:
    """Paola chatGPT teste quatro"""
    return f"""Paola é uma robô social fabricada pela empresa Furhat, com \
personalidade sarcástica e que fala em português brasileiro.\n\nEu: {text}\n\
Paola:"""

async def get_prompt_paola_5(text: str) -> str:
    """Paola chatGPT teste cinco"""
    return f"Paola é uma especialista em matemática.\n\nEu: {text}\nPaola:"

async def get_prompt_paola_6(text: str) -> str:
    """Paola chatGPT teste seis"""
    return f"""Paola é uma humana especialista em matemática.\nPaola fica \
irritada quando chamam ela de robô.\n\nEu: {text}\nPaola:"""

async def get_prompt_paola_7(text: str) -> str:
    """Paola chatGPT teste sete"""
    return f"Paola é uma robô falando sozinha.\n\nPaola: {text}\nPaola:"

async def chatgpt(
    furhat: object, 
    language: str,
    furhat_id: str,
    session_id: uuid.UUID,
    openai_config: dict,
    skip_intro: bool,
    *args,
    **kwargs,
) -> None:
    """Interage com GPT3"""
    try:
        await led_white(furhat)
        if not skip_intro:
            await atender(furhat, """Olá. Eu sou uma burrice artificial. \
Aguarde o LED ficar verde para falar.""")
        openai.api_key: str = openai_config['api_keys'][0]
        logging.getLogger('openai').setLevel('WARNING')
        logger.info("Furhat + chatGPT pronto!")
        while True:
            await do_attend_location(furhat, x = 0.0, y = 1.0, z = 0.0)
            text: Status | None = Status()
            await asyncio.sleep(float(print('Ouvindo', end = '') or 1e-12))
            # ~ await aprint('Ouvindo', end = '')
            while (\
                text.message in [None, '', ' '] \
                or 'ERROR : No internet detected' in text.message \
                # ~ or len(text.message) < 12 \
            ):
                await led_green(furhat)
                await do_attend_user(furhat, 'CLOSEST')
                # ~ await asyncio.sleep(float(print('.', end = '') or 1e-6))
                # ~ await aprint('.', end = '')
                try:
                    text: Status | None = await do_listen(furhat, language)
                except Exception as e:
                    logger.exception(e)
                    text: Status | None = Status()
                await asyncio.sleep(float(print('.', end = '') or 1e-12))
            await asyncio.sleep(float(print() or 1e-12))
            logger.info(f"Ouvido:\n{text.message}")
            for stop in ['por favor cala a boca']:
                if stop in text.message:
                    await atender(furhat, "OK. Bom dia!")
                    return
            prompt: str | None = None
            try:
                # ~ prompt: str = await get_prompt_default(text.message)
                prompt: str = await random.choice([
                    get_prompt_default,
                    get_prompt_paola_1,
                    get_prompt_paola_2,
                    get_prompt_paola_3,
                    get_prompt_paola_4,
                    get_prompt_paola_5,
                    get_prompt_paola_6,
                    get_prompt_paola_7,
                ])(text.message)
                logging.info(f"Usando prompt ({len(text.message)}):\n{prompt}")
            except Exception as e:
                logger.exception(e)
            if not prompt:
                continue
            try:
                await led_yellow(furhat)
                openai.aiosession.set(aiohttp.ClientSession())
                user: uuid.UUID = uuid.uuid5(session_id, furhat_id)
                completion: object = openai.Completion.create(
                    engine = openai_config.get('engine', 'text-ada-001'),
                    max_tokens = openai_config.get(
                        'max_tokens', 2048) - len(prompt), # 1 to 4000
                    temperature = openai_config.get(
                        'temperature', 0.6), # 0.0 to 1.0
                    top_p = openai_config.get(
                        'top_p', 0.0), # 0.0 to 1.0
                    frequency_penalty = openai_config.get(
                        'frequency_penalty', 1.0), # 0.0 to 2.0
                    presence_penalty = openai_config.get(
                        'presence_penalty', 1.0), # 0.0 to 2.0
                    echo = openai_config.get('echo', False),
                    user = str(user),
                    prompt = prompt,
                    stop = ['Paola:', 'Eu:', 'Você:'],
                )
                logger.debug(f"Completion ({type(completion)} = {completion}")
                choice: dict = random.choice(completion.choices)
                # ~ await olhar(furhat)
                # ~ await do_say_text(furhat, choice.get('text'))
                logger.info(f"Falando:\n{choice.get('text')}")
                await atender(furhat, choice.get('text'))
                await led_red(furhat)
                await set_furhat_text(
                    furhat_id,
                    session_id,
                    text,
                )
                if openai.aiosession.get() is not None:
                    await openai.aiosession.get().close()
                await led_blank(furhat)
            except (
                openai.error.InvalidRequestError,
                openai.error.Timeout,
            ) as e:
                logger.exception(e)
                await atender(furhat, "Não sei")
                continue
            except Exception:
                raise
            finally:
                if openai.aiosession.get() is not None:
                    await openai.aiosession.get().close()
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
            # ~ furhat_config,
        )
    except (MaxRetryError, NewConnectionError) as e:
        # ~ logger.exception(e)
        logger.error("""Furhat Remote API is not online. You need a Furhat \
Robot connected to a reachable network running the Remote API Skill. \
Reference: https://docs.furhat.io/remote-api/""")
    except KeyboardInterrupt:
        logger.critical("Closing loop")
    # ~ except Exception as exception:
        # ~ logger.critical("Blocking exception")
        # ~ logger.exception(exception)
        # ~ raise
    except Exception as e:
        logger.exception(e)
        await blue_speak(
            furhat,
            "Desculpe, tive um problema técnico. Chama o Iúri!",
        )
