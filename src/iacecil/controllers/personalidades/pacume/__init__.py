"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

### Personalidade do Tiozão do Churrasco @tiodochurrasbot
### AVISO: Personalidade ácida, agressiva e ofensiva. Se não souber o 
### que está fazendo, não teste.

import logging
logger = logging.getLogger(__name__)

import os
import random
import typing
from aiogram import (
    Bot,
    Dispatcher,
    exceptions,
    filters,
    types,
)
from aiogram.utils.markdown import escape_md
from ...aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from ...amazon_boto import get_audio
from ...ffmpeg_wrapper import telegram_voice
from ...util import (
    dice_high,
    dice_low,
)
from .. import pave
from .furhat_handlers import (
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
)

## TODO Sentenças impróprias para publicar no Github por razões diversas
try:
    from instance.personalidades.pacume import (
        random_texts,
        add_instance_handlers,
    )
except Exception as e:
    logger.debug(f"random_texts em instance não encontrada para {__name__}")
    #logger.exception(e)
    try:
        from . import random_texts
    except Exception as e1:
        logger.debug(f"no random_texts at all for {__name__}")
        # ~ logger.exception(e1)

async def start(message: types.Message) -> str:
    """Answer /start"""
    return random_texts.start(message)

async def welcome(message: types.Message) -> str:
    """Answer new members"""
    bot: Bot = Dispatcher.get_current().bot
    admin: str = "@admin"
    count: str = await bot.get_chat_members_count(message.chat.id)
    ## FIXME move this to handlers with filters for groups
    if message.chat.type in ['group', 'supergroup']:
        try:
            admin: str = [member.user for member in \
                await bot.get_chat_administrators(
                message.chat.id
                ) if member.status == 'creator'][0].first_name
        except IndexError as e:
            logger.exception(e)
    return random_texts.welcome(message, count, admin)

async def portaria(message: types.Message) -> str:
    """Answer unwanted new members"""
    return "Puta que pariu, entrou esse filho da puta aqui ó @admin"

async def bye(message: types.Message) -> str:
    """Answer member lefts"""
    bot: Bot = Dispatcher.get_current().bot
    admin: str = "admin"
    ## FIXME: Move this to handler with filter for groups
    if message.chat.type in ['group', 'supergroup']:
        try:
            admin = [member.user for member in \
                await bot.get_chat_administrators(
                message.chat.id
                ) if member.status == 'creator'][0].first_name
        except IndexError as e:
            logger.exception(e)
        except exceptions.BotKicked as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(e)
    return random_texts.respostas_bye(admin)

async def info() -> str:
    """Answers /info"""
    return """\
Eu sou um bot com personalidade de tiozão do churrasco (termo moderno \
politicamente correto: "humor boomer") configurado e desenvolvido para ser \
impertinente, sarcástico, ignorante, agressivo, sem noção, ofensivo, \
politicamente incorreto. A tua opinião em relação à minha atitude influencia \
no meu comportamento que nunca vai ser pra te agradar. Para enviar sugestões \
ou relatar problemas para o pessoal que faz manutenção, use o comando \
/feedback por exemplo /feedback Dane-se!\n\nPara enviar reclamações sobre \
comportamento indevido, abra processo no Ministério Público Federal, chama a \
tua mãe, se fode.\
"""

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register Aiogram message handlers to aiogram.Dispatcher"""
    try:
        @dispatcher.message_handler(
            filters.Regexp(r'\b({})\b'.format('|'.join(
            random_texts.adjetivos()))),
            is_reply_to_id = dispatcher.bot.id,
        )
        async def resposta_adjetivo_callback(message: types.Message) -> None:
            """Não deixa de graça"""
            descriptions: list = [
                'resposta',
                'adjetivo',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            command: typing.Union[types.Message, None] = None
            audio_text: typing.Union[str, None] = None
            opus_file: typing.Union[str, None] = None
            try:
                await message_callback(message, descriptions)
                for adjetivo in random_texts.adjetivos():
                    if adjetivo.lower() == message.text[message.text.lower(
                        ).find(adjetivo.lower()):][:len(adjetivo.lower())]:
                        audio_text: str = adjetivo.lower() + \
                            ' é tu. E tu é um {}.'.format(
                            random_texts.respostas_adjetivos().lower()
                        )
                if audio_text is not None:
                    vorbis_file: object = await get_audio(audio_text)
                    opus_file: typing.Union[str, None] = \
                        await telegram_voice(vorbis_file)
                    if opus_file is not None:
                        with open(opus_file, 'rb') as audio:
                            command: types.Message = \
                                await message.reply_voice(audio)
                        if command is not None:
                            await command_callback(command, descriptions)
                        else:
                            await error_callback(
                                "Não consegui responder com mensagem de voz",
                                message,
                                None,
                                ['error'] + descriptions,
                            )
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Problema tentando mandar audio",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
            finally:
                if opus_file is not None:
                    os.remove(opus_file)
        
        @dispatcher.message_handler(is_reply_to_id = dispatcher.bot.id)
        async def resposta_ignorante_callback(message: types.Message) -> None:
            """
            Responde mensagens que são respostas a mensagens deste bot
            Reponde com patada
            """
            descriptions: list = [
                'resposta',
                'ignorante',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                admin: str = message.from_user.first_name
                if message.chat.type in ['group', 'supergroup']:
                    try:
                        admin: str = [member.user for member in \
                            await dispatcher.bot.get_chat_administrators(
                            message.chat.id
                            ) if member.status == 'creator'][0].first_name
                    except IndexError as e:
                        logger.exception(e)
                command: types.Message = await message.reply(
                    random_texts.respostas_ignorante(admin)
                )
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Não consegui mandar patada",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(
            content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
        )
        async def welcome_callback(message: types.Message) -> None:
            """Seja mau vindo"""
            descriptions: list = [
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                command_type: str = 'welcome'
                await message_callback(message, [command_type] + descriptions)
                text = await welcome(message)
                if message['new_chat_member']['first_name'].lower() in \
                    [unwant.lower() for unwant in \
                    dispatcher.config.telegram.get('unwanted', ['SPAM'])
                ]:
                    text: str = await portaria(message)
                    command_type: str = 'portaria'
                command: types.Message = await message.reply(text)
                if command:
                    await command_callback(
                        command,
                        [command_type] + descriptions,
                    )
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro enviando mensagem de más vindas",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(
            content_types = types.ContentTypes.LEFT_CHAT_MEMBER,
        )
        async def bye_callback(message: types.Message):
            """Volte nunca"""
            descriptions: list = [
                'bye',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                text: str = await bye(message)
                command: types.Message = await message.reply(text)
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro dando tchau",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(commands = ['piada'])
        async def piada_callback(message: types.Message) -> None:
            """Piadas sem graça"""
            descriptions: list = [
                'piada',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                ## FIXME async/await
                command: types.Message = await message.reply(
                    random_texts.respostas_piadas())
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro tentando mandar piada",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(commands = ['versiculo'])
        async def versiculo_callback(message: types.Message) -> None:
            """Versículos bíblicos fora de contexto"""
            descriptions: list = [
                'versiculo',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                ## FIXME async/await
                command: types.Message = await message.reply(
                    random_texts.versiculos_md(),
                    parse_mode = "MarkdownV2",
                )
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro tentando mandar versículo",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(commands = ['info'])
        async def info_callback(message: types.Message) -> None:
            """Reply to /info"""
            descriptions: list = [
                'info',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                command: types.Message = await message.reply(await info())
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro tentando responder /info",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(filters.Regexp('\w{2,}(a|ã)o(\?|\!|\.)*$'))
        async def rima_ao_callback(message: types.Message) -> None:
            """
            Qualquer frase que termina em 'ão' com uma palavra de pelo menos 
            quatro letras
            """
            descriptions: list = [
                'rima',
                'ao',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                if (await dice_low(3)):
                    ## FIXME async/await
                    command: types.Message = await message.reply(
                        random_texts.rimas_ao())
                    if command:
                        await command_callback(command, descriptions)
                    else:
                        raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro tentando responder rima com ão",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(
            filters.Regexp(
                r'\b({})\b'.format('|'.join(random_texts.bebidas())),
            ),
        )
        async def resposta_bebida_callback(message: types.Message) -> None:
            """Responde toda referência a bebidas"""
            descriptions: list = [
                'resposta',
                'bebida',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, dispatcher)
                if (await dice_high(3)):
                    command: types.Message = await message.reply(
                        random_texts.respostas_bebida())
                    if command:
                        await command_callback(command, descriptions)
                    else:
                        raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro tentando responder para bebidas",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        @dispatcher.message_handler(
            filters.Text(contains = 'quanto', ignore_case = True),
            filters.Regexp('(?i)\\b(vale|custa|cobra)\\b'),
        )
        async def resposta_quanto_callback(message: types.Message) -> None:
            """Responde 'quanto vale'"""
            descriptions: list = [
                'resposta',
                'quanto',
                dispatcher.config.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                if (await dice_high(3)):
                    ## FIXME async/await
                    command: types.Message = await message.reply(
                        random_texts.respostas_quanto()
                    )
                    if command:
                        await command_callback(command, descriptions)
                    else:
                        raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    "Erro tentando responder para quanto",
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        try:
            await add_instance_handlers(dispatcher)
        except Exception as e1:
            logger.debug(f"Didn't register {__name__} instance handlers")
            logger.exception(e1)
    except Exception as e:
        logger.error(f"Couldn't register {__name__} handlers")
        logger.exception(e)
