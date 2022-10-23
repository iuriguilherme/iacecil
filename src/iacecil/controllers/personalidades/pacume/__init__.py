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
from aiogram import (
    Dispatcher,
    exceptions,
    filters,
    types,
)
from aiogram.utils.markdown import escape_md
from ...aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
)
from ...ffmpeg_wrapper import telegram_voice
from .. import pave
from .furhat_handlers import (
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
)
from ...amazon_boto import get_audio
from ...util import (
    dice_high,
    dice_low,
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

async def start(message):
    return random_texts.start(message)

async def welcome(message):
    bot = Dispatcher.get_current().bot
    admin = u"@admin"
    count = await bot.get_chat_members_count(message.chat.id)
    if message.chat.type in ['group', 'supergroup']:
        try:
            admin = [member.user for member in \
                await bot.get_chat_administrators(
                message.chat.id
                ) if member.status == 'creator'][0].first_name
        except IndexError:
            pass
    return random_texts.welcome(message, count, admin)

async def portaria(message):
    return u"Puta que pariu, entrou esse filho da puta aqui ó @admin"

async def bye(message):
    bot = Dispatcher.get_current().bot
    admin = u"admin"
    if message.chat.type in ['group', 'supergroup']:
        try:
            admin = [member.user for member in \
                await bot.get_chat_administrators(
                message.chat.id
                ) if member.status == 'creator'][0].first_name
        except IndexError:
            pass
        except exceptions.BotKicked:
            pass
        except Exception as exception:
            logger.info(repr(exception))
    return random_texts.respostas_bye(admin)

async def info():
    return u"""Eu sou um bot com personalidade de tiozão do churrasco (\
termo moderno politicamente correto: "humor boomer") configurado e dese\
nvolvido para ser impertinente, sarcástico, ignorante, agressivo, sem n\
oção, ofensivo, politicamente incorreto. A tua opinião em relação à min\
ha atitude influencia no meu comportamento que nunca vai ser pra te agr\
adar. Para enviar sugestões ou relatar problemas para o pessoal que faz\
 manutenção, use o comando /feedback por exemplo /feedback Dane-se!\n\n\
Para enviar reclamações sobre comportamento indevido, abra processo no \
Ministério Público Federal, chama a tua mãe, se fode."""

async def add_handlers(dispatcher):
    ## Não deixa de graça
    @dispatcher.message_handler(
        filters.Regexp(r'\b({})\b'.format('|'.join(
        random_texts.adjetivos()))),
        is_reply_to_id = dispatcher.bot.id,
    )
    async def resposta_adjetivo_callback(message):
        await message_callback(message, ['resposta', 'adjetivo',
            message.chat.type],
        )
        command = None
        audio_text = None
        opus_file = None
        try:
            for adjetivo in random_texts.adjetivos():
                if adjetivo.lower() == message.text[message.text.lower(
                    ).find(adjetivo.lower()):][:len(adjetivo.lower())]:
                    audio_text = adjetivo.lower() + \
                        ' é tu. E tu é um {}.'.format(
                        random_texts.respostas_adjetivos().lower()
                    )
            if audio_text is not None:
                vorbis_file = await get_audio(audio_text)
                opus_file = await telegram_voice(vorbis_file)
                if opus_file is not None:
                    with open(opus_file, 'rb') as audio:
                        command = await message.reply_voice(audio)
                    await command_callback(command, ['resposta',
                        'adjetivo', message.chat.type])
        except Exception as exception:
            await error_callback(
                u"Problema tentando mandar audio",
                message,
                exception,
                ['error', 'reposta', 'adjetivo', message.chat.type],
            )
        finally:
            if opus_file is not None:
                os.remove(opus_file)
    
    ## Responde mensagens que são respostas a mensagens deste bot
    ## Reponde com patada
    @dispatcher.message_handler(is_reply_to_id = dispatcher.bot.id)
    async def resposta_ignorante_callback(message):
        await message_callback(
            message,
            ['resposta', 'ignorante', message.chat.type],
        )
        admin = message.from_user.first_name
        if message.chat.type in ['group', 'supergroup']:
            try:
                admin = [member.user for member in \
                    await dispatcher.bot.get_chat_administrators(
                    message.chat.id
                    ) if member.status == 'creator'][0].first_name
            except IndexError:
                pass
        command = await message.reply(
            random_texts.respostas_ignorante(admin),
        )
        await command_callback(command, ['resposta' 'ignorante', 
            message.chat.type],
        )
    
    ## Seja mau vindo
    @dispatcher.message_handler(
        content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
    )
    async def welcome_callback(message: types.Message):
        command_type = 'welcome'
        await message_callback(message,
            [command_type, dispatcher.config.personalidade, message.chat.type],
        )
        text = await welcome(message)
        if str(message['new_chat_member']['first_name']).lower() in \
            [unwant.lower() for unwant in \
            dispatcher.config.telegram.get('unwanted', ['SPAM'])
        ]:
            text = await portaria(message)
            command_type = 'portaria'
        command = await message.reply(text)
        await command_callback(command,
            [command_type, dispatcher.config.personalidade, message.chat.type],
        )

    ## Volte nunca
    @dispatcher.message_handler(
        content_types = types.ContentTypes.LEFT_CHAT_MEMBER,
    )
    async def bye_callback(message: types.Message):
        await message_callback(message, ['bye',
            dispatcher.config.personalidade, message.chat.type])
        text = await bye(message)
        command = await message.reply(text)
        await command_callback(command, ['bye',
            dispatcher.config.personalidade, message.chat.type])

    ## Piadas sem graça
    @dispatcher.message_handler(
        commands = ['piada'],
    )
    async def piada_callback(message):
        await message_callback(message, ['piada',
            dispatcher.config.personalidade,
            message.chat.type],
        )
        command = await message.reply(random_texts.respostas_piadas())
        await command_callback(
            command,
            [
                'piada',
                dispatcher.bot.personalidade,
                message.chat.type,
            ],
        ) # command_callback

    ## Versículos bíblicos fora de contexto
    @dispatcher.message_handler(
        commands = ['versiculo'],
    )
    async def versiculo_callback(message):
        await message_callback(message, ['versiculo',
            message.chat.type],
        )
        command = await message.reply(
            random_texts.versiculos_md(),
            parse_mode = "MarkdownV2",
        )
        await command_callback(command, ['versiculo',
            message.chat.type],
        )

    ## /info
    @dispatcher.message_handler(
        commands = ['info'],
    )
    async def info_callback(message):
        await message_callback(message, ['info',
            dispatcher.config.personalidade, message.chat.type])
        command = await message.reply(await info())
        await command_callback(command, ['info',
            dispatcher.config.personalidade, message.chat.type])

    ## Qualquer frase que termina em 'ão' com uma palavra de pelo menos
    ## quatro letras
    @dispatcher.message_handler(
        filters.Regexp('\w{2,}(a|ã)o(\?|\!|\.)*$'),
    )
    async def rima_ao_callback(message):
        await message_callback(message, ['rima', 'ao',
            dispatcher.bot.personalidade,
            message.chat.type],
        )
        if (await dice_low(3)):
            command = await message.reply(random_texts.rimas_ao())
            await command_callback(command, ['rima', 'ao',
                dispatcher.bot.personalidade,
                message.chat.type],
            )

    ## Responde toda referência a bebidas
    @dispatcher.message_handler(
        filters.Regexp(r'\b({})\b'.format('|'.join(
        random_texts.bebidas()))),
    )
    async def resposta_bebida_callback(message):
        await message_callback(message, ['resposta', 'bebida',
            message.chat.type],
        )
        if (await dice_high(3)):
            command = await message.reply(
                random_texts.respostas_bebida())
            await command_callback(command, ['resposta', 'bebida',
                message.chat.type],
            )

    ## Responde "quanto vale"
    @dispatcher.message_handler(
        filters.Text(contains = 'quanto', ignore_case = True),
        filters.Regexp('(?i)\\b(vale|custa|cobra)\\b'),
    )
    async def resposta_quanto_callback(message):
        await message_callback(message, ['resposta', 'quanto',
            message.chat.type])
        if (await dice_high(3)):
            command = await message.reply(
                random_texts.respostas_quanto())
            await command_callback(command, ['resposta', 'quanto',
                message.chat.type])


    try:
        await add_instance_handlers(dispatcher)
    except Exception as e:
        logger.debug("Didn't register instance handlers")
        # ~ logger.exception(e)
