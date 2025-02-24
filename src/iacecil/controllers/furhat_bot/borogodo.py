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

# ~ try:
    # ~ from ....config import Config
    # ~ config = Config()
    # ~ bots_config = config.bots
    # ~ furhat_config = config.furhat_config
# ~ except Exception as e:
    # ~ logger.critical(f"{name} config file not found or somehow wrong. RTFM.")
    # ~ logger.exception(e)
    # ~ raise

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
