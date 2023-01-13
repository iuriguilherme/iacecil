"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2023 Iuri Guilherme <https://iuri.neocities.org/>

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

### Personalidade do Tiozão do Pavê @tiozao_bot

import logging
logger = logging.getLogger(__name__)

import random
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from ...aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from .furhat_handlers import (
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
)

## TODO Sentenças impróprias para publicar no Github por razões diversas
try:
    from instance.personalidades.pave import random_texts
except Exception as e:
    logger.debug(f"random_texts em instance não encontrada para {__name__}")
    # ~ logger.exception(e)
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

async def info():
    return u"""Eu sou um bot com personalidade de tiozão do pavê (termo\
 moderno politicamente correto: "humor boomer") configurado e desenvolv\
ido para ser impertinente, sarcástico, ignorante, agressivo e sem noção\
. A tua opinião em relação à minha atitude influencia no meu comportame\
nto que nunca vai ser pra te agradar. Para enviar sugestões ou relatar \
problemas para o pessoal que faz manutenção, use o comando /feedback po\
r exemplo /feedback Obrigado pelo bot!"""

async def portaria(message):
    return u"alá @admin, esse guampudo conseguiu voltar!"

## Pegadinha
### FIXME armazenar file_id, porque muda conforme o grupo
async def pegadinha4(message):
    bot = Dispatcher.get_current().bot
    return await message.reply(
        u"é {}, pa pa pa".format(
            await bot.get_chat_members_count(message.chat.id)),
    )
async def pegadinha1(message):
    try:
        return await message.reply_photo('''AgACAgEAAx0EWWIw7gABAzPXYid\
XQU56JMvt8IbBpON8d8TfI7oAAgyqMRvSF_FEnT2QiVbie1UBAAMCAANzAAMjBA''',
        )
    except Exception as exception:
        logger.warning(
            u"file_id estava errado tentando mandar pegadinha1",
        )
        try:
            return await message.reply_photo(open(
                'instance/personalidades/pave/pegadinha/pegadinha1.jpg',
                'rb',
            ))
        except Exception as e1:
            logger.warning(u"Arquivo não encontrado: {}".format(
                repr(e1))
            )
            return await pegadinha4(message)
async def pegadinha2(message):
    try:
        return await message.reply_photo('''AgACAgEAAx0EWWIw7gABAzPOYid\
UEBEUFFncjjtkd6HBdAVnKVQAAleqMRvSF-lEWQpWEeJ0UWUBAAMCAANzAAMjBA''',
        )
    except Exception as exception:
        logger.warning(
            u"file_id estava errado tentando mandar pegadinha2",
        )
        try:
            return await message.reply_photo(open(
                'instance/personalidades/pave/pegadinha/pegadinha2.png',
                'rb',
            ))
        except Exception as e1:
            logger.warning(u"Arquivo não encontrado: {}".format(
                repr(e1))
            )
            return await pegadinha4(message)
async def pegadinha3(message):
    try:
        return await message.reply_animation('''CgACAgEAAx0EWWIw7gABAzL\
4YiYP73EVBmcEbCrr_XztGpitP30AAgoCAALGHDFF5NSrfwkfoP4jBA''',
        )
    except Exception as exception:
        logger.warning(
            u"file_id estava errado tentando mandar pegadinha3",
        )
        try:
            return await message.reply_animation(open(
                'instance/personalidades/pave/pegadinha/pegadinha3.mp4',
                'rb',
            ))
        except Exception as e1:
            logger.warning(u"Arquivo não encontrado: {}".format(
                repr(e1))
            )
            return await pegadinha4(message)
async def pegadinha5(message):
    bot = Dispatcher.get_current().bot
    try:
        ## esprimente a linguiça
        return await message.reply_sticker('''AAMCAQADHQJZYjDuAAEDM-ViJ\
2fMxBKkKvbPFq0miPLUuAavAAM4AAMcZ90u6TNY9DNgTcwBAAdtAAMjBA''',
        )
    except Exception as exception:
        logger.warning(u"Não consegui mandar sticker: {}".format(
            repr(exception))
        )
        return await pegadinha4(message)
async def pegadinha(message):
    return await random.choice([
        pegadinha1,
        pegadinha2,
        pegadinha3,
        pegadinha4,
        pegadinha5,
    ])(message)

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Responde mensagens que são respostas a mensagens deste bot
        ## Reponde com patada
        @dispatcher.message_handler(is_reply_to_id = dispatcher.bot.id)
        async def resposta_ignorante_callback(message):
            descriptions: list = ['resposta', 'ignorante',
                dispatcher.config.personalidade, message.chat.type]
            try:
                await message_callback(
                    message,
                    descriptions,
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
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'ignorante',
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        ## Saúda com trollada
        @dispatcher.message_handler(
            filters.IDFilter(
                ## Somente grupos configurados pra receber novas pessoas com
                ## pegadinha
                ## Atualmente só o @ZaffariPoa
                chat_id = dispatcher.config.telegram['users'].get(
                    'pegadinha', -1),
            ),
            content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
        )
        async def welcome_pegadinha_callback(message: types.Message):
            descriptions: list = [dispatcher.config.personalidade,
                message.chat.type]
            try:
                command_type = 'welcome'
                await message_callback(message, [command_type] + descriptions,
                )
                if str(message['new_chat_member']['first_name']).lower() in \
                    [unwant.lower() for unwant in \
                    dispatcher.config.telegram.get('unwanted',
                        ['SPAM'])]:
                    text = await portaria(message)
                    command_type = 'portaria'
                    command = await message.reply(text)
                else:
                    command = await pegadinha(message)
                if command:
                    await command_callback(command,
                        [command_type] + descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'welcome',
                    message,
                    e1,
                    ['exception', 'welcome'] + descriptions,
                )

        ## /brinde
        @dispatcher.message_handler(
            filters.IDFilter(
                ## Somente grupos configurados pra receber novas pessoas com
                ## pegadinha
                ## Atualmente só o @ZaffariPoa
                chat_id = dispatcher.config.telegram['users'].get(
                    'pegadinha', -1),
            ),
            commands = ['brinde', 'brindes'],
        )
        async def brinde_pegadinha_callback(message: types.Message):
            descriptions: list = [dispatcher.config.personalidade,
                message.chat.type]
            try:
                command_type = 'brinde'
                await message_callback(message, [command_type] + descriptions,
                )
                command = await pegadinha(message)
                if command:
                    await command_callback(command,
                        [command_type] + descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'brinde',
                    message,
                    e1,
                    ['exception', 'brinde'] + descriptions,
                )
        ## Seja mau vindo
        @dispatcher.message_handler(
            content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
        )
        async def welcome_callback(message: types.Message):
            descriptions: list = [dispatcher.config.personalidade,
                message.chat.type]
            try:
                command_type = 'welcome'
                await message_callback(message,
                    [command_type] + descriptions,
                )
                text = await welcome(message)
                if str(message['new_chat_member']['first_name']).lower() in \
                    [unwant.lower() for unwant in \
                    dispatcher.config.telegram.get('unwanted',
                        ['SPAM'])]:
                    text = await portaria(message)
                    command_type = 'portaria'
                command = await message.reply(text)
                if command:
                    await command_callback(command,
                        [command_type] + descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'welcome',
                    message,
                    e1,
                    ['exception', 'welcome'] + descriptions,
                )

        ## Piadas sem graça
        # ~ @dispatcher.message_handler(
            # ~ commands = ['piada'],
        # ~ )
        # ~ async def piada_callback(message):
            # ~ await message_callback(message, ['piada',
                # ~ dispatcher.config.personalidade,
                # ~ message.chat.type])
            # ~ command = await message.reply(random_texts.piadas())
            # ~ await command_callback(command, ['piada',
                # ~ dispatcher.config.personalidade,
                # ~ message.chat.type])

        ## Versículos bíblicos fora de contexto
        @dispatcher.message_handler(
            commands = ['versiculo'],
        )
        async def versiculo_callback(message):
            descriptions: list = ['versiculo', dispatcher.config.personalidade,
                    message.chat.type]
            try:
                await message_callback(message, descriptions)
                command = await message.reply(
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
                    'versiculo',
                    message,
                    e1,
                    ['exception'] + descriptions,
                )
        ## /info
        @dispatcher.message_handler(
            commands = ['info'],
        )
        async def info_callback(message):
            descriptions = ['info', dispatcher.config.personalidade,
                    message.chat.type]
            try:
                await message_callback(
                    message,
                    descriptions,
                )
                command = await message.reply(await info())
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'info',
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
                dispatcher.config.get.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                command = await message.reply(random_texts.respostas_quanto())
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'quanto',
                    message,
                    e1,
                    ['exception', 'pave', 'quanto'],
                )

        @dispatcher.message_handler(
            filters.Regexp(r'\b({})\b'.format('|'.join(random_texts.bebidas())))
        )
        async def resposta_bebida_callback(message: types.Message) -> None:
            """Responde toda referência a bebidas"""
            descriptions: list = [
                'resposta',
                'bebida',
                dispatcher.config.get.personalidade,
                message.chat.type,
            ] # descriptions
            try:
                await message_callback(message, descriptions)
                command = await message.reply(random_texts.respostas_bebida())
                if command:
                    await command_callback(command, descriptions)
                else:
                    raise Exception(f"command was {str(command)}")
            except Exception as e1:
                logger.exception(e1)
                await error_callback(
                    'bebida',
                    message,
                    e1,
                    ['exception', 'pave', 'bebida'],
                )
    except Exception as e:
        logger.exception(e)
