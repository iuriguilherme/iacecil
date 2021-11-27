# vim:fileencoding=utf-8
#  Plugin personalidades para matebot: Robô também é gente?
#  Copyleft (C) 2020-2021 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

### Personalidade do Tiozão do Churrasco @tiodochurras
### AVISO: Personalidade ácida, agressiva e ofensiva. Se não souber o que está
### fazendo, não teste.

import logging, random

from aiogram import (
    Dispatcher,
    filters,
    types,
)

from aiogram.utils.markdown import escape_md

from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)

from plugins.personalidades import pave

## TODO Sentenças impróprias para publicar no Github por razões diversas
try:
    from instance.personalidades.pacume import random_texts
except Exception as e:
    logging.warning("Não achei o arquivo: {}".format(e))
    from plugins.personalidades.pacume import random_texts

async def start(message):
    return random_texts.start(message)

async def welcome(message):
    bot = Dispatcher.get_current().bot
    admin = message.from_user.first_name
    count = await bot.get_chat_members_count(message.chat.id)
    if message.chat.type in ['group', 'supergroup']:
        admin = [member.user for member in await bot.get_chat_administrators(
            message.chat.id) if member.status == 'creator'][0].first_name or u"@admin"
    return random_texts.welcome(message, count, admin)

async def bye(message):
    bot = Dispatcher.get_current().bot
    admin = message.from_user.first_name
    if message.chat.type in ['group', 'supergroup']:
        admin = [member.user for member in await bot.get_chat_administrators(
            message.chat.id) if member.status == 'creator'][0].first_name or u"@admin"
    return random_texts.bye(admin)

async def info():
    return u"""Eu sou um bot com personalidade de tiozão do churrasco (termo mode\
rno politicamente correto: "humor boomer") configurado e desenvolvido para ser \
impertinente, sarcástico, ignorante, agressivo, sem noção, ofensivo, politicame\
nte incorreto. A tua opinião em relação à minha atitude influencia no meu compo\
rtamento que nunca vai ser pra te agradar. Para enviar sugestões ou relatar pro\
blemas para o pessoal que faz manutenção, use o comando /feedback por exemplo /\
feedback Dane-se!"""

async def add_handlers(dispatcher):
    ## Saúda com trollada
    @dispatcher.message_handler(
        filters.IDFilter(
            ## Somente grupos configurados pra receber novas pessoas com pegadinha
            ## Atualmente só o @ZaffariPoa
            chat_id = dispatcher.bot.users.get('pegadinha', -1),
        ),
        content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
    )
    async def welcome_pegadinha_callback(message: types.Message):
        await message_callback(message, ['welcome', 'pegadinha', message.chat.type])
        command = await pave.pegadinha(message)
        await command_callback(command, ['welcome', 'pegadinha', message.chat.type])

    ## Seja mau vindo
    @dispatcher.message_handler(
        content_types = types.ContentTypes.NEW_CHAT_MEMBERS,
    )
    async def welcome_callback(message: types.Message):
        await message_callback(message, ['welcome', dispatcher.bot.info.get(
            'personalidade', 'pacume'), message.chat.type])
        text = await welcome(message)
        command = await message.reply(text)
        await command_callback(command, ['welcome', dispatcher.bot.info.get(
            'personalidade', 'pacume'), message.chat.type])

    ## Volte nunca
    @dispatcher.message_handler(
        content_types = types.ContentTypes.LEFT_CHAT_MEMBER,
    )
    async def bye_callback(message: types.Message):
        await message_callback(message, ['bye', dispatcher.bot.info.get(
            'personalidade', 'pacume'), message.chat.type])
        text = await bye(message)
        command = await message.reply(text)
        await command_callback(command, ['bye', dispatcher.bot.info.get(
            'personalidade', 'pacume'), message.chat.type])

    ## Piadas sem graça
    @dispatcher.message_handler(
        commands = ['piada'],
    )
    async def piada_callback(message):
        await message_callback(message, ['piada',
            dispatcher.bot.get('personalidade', 'pacume'), message.chat.type])
        command = await message.reply(random_texts.piadas())
        await command_callback(command, ['piada',
            dispatcher.bot.get('personalidade', 'pacume'), message.chat.type])

    ## Versículos bíblicos fora de contexto
    @dispatcher.message_handler(
        commands = ['versiculo'],
    )
    async def versiculo_callback(message):
        await message_callback(message, ['versiculo', message.chat.type])
        command = await message.reply(
            random_texts.versiculos_md(),
            parse_mode = "MarkdownV2",
        )
        await command_callback(command, ['versiculo', message.chat.type])

    ## /info
    @dispatcher.message_handler(
        commands = ['info'],
    )
    async def info_callback(message):
        await message_callback(message, ['info',
            dispatcher.bot.get('personalidade', 'pacume'), message.chat.type])
        command = await message.reply(await info())
        await command_callback(command, ['info',
            dispatcher.bot.get('personalidade', 'pacume'), message.chat.type])

    ## Qualquer frase que termina em 'ão' com uma palavra de pelo menos quatro
    ## letras
    @dispatcher.message_handler(
        filters.Regexp('\w{2,}(a|ã)o(\?|\!|\.)*$'),
    )
    async def rima_ao_callback(message):
        await message_callback(message, ['rima', 'ao',
            dispatcher.bot.get('personalidade', 'pacume'), message.chat.type])
        command = await message.reply(random_texts.rimas_ao())
        await command_callback(command, ['rima', 'ao',
            dispatcher.bot.get('personalidade', 'pacume'), message.chat.type])

    ## Responde toda referência a bebidas
    @dispatcher.message_handler(
        filters.Regexp(r'\b({})\b'.format('|'.join(random_texts.bebidas()))),
    )
    async def resposta_bebida_callback(message):
        await message_callback(message, ['resposta', 'bebida', message.chat.type])
        command = await message.reply(random_texts.respostas_bebida())
        await command_callback(command, ['resposta', 'bebida', message.chat.type])

    ## Responde "quanto vale"
    @dispatcher.message_handler(
        filters.Text(contains = 'quanto', ignore_case = True),
        filters.Regexp('(?i)\\b(vale|custa|cobra)\\b'),
    )
    async def resposta_quanto_callback(message):
        await message_callback(message, ['resposta', 'quanto',
            message.chat.type])
        command = await message.reply(random_texts.respostas_quanto())
        await command_callback(command, ['resposta', 'quanto',
            message.chat.type])

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
            admin = [member.user for member in \
                await dispatcher.bot.get_chat_administrators(
                message.chat.id) if member.status == 'creator'][0].first_name \
                or u"@admin"
        command = await message.reply(random_texts.respostas_ignorante(admin))
        await command_callback(command, ['resposta' 'ignorante', message.chat.type])
