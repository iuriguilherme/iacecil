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

import logging
logger = logging.getLogger(__name__)

### Personalidade padrão do @mate_obot
import random
from ..aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from ...models import Iteration

## TODO Sentenças impróprias para publicar no Github por razões diversas
try:
    from instance.personalidades.default import random_texts
except Exception as e:
    logger.debug(f"random_texts em instance não encontrada para {__name__}")
    # ~ logger.exception(e)
    from . import random_texts

async def start(message):
    return u"""Oi oi oi {first_name} {last_name}, me use, me use. O teu\
 id no telegram é {telegram_id}""".format(
        first_name = message.from_user.first_name,
        last_name = message.from_user.last_name,
        telegram_id = message.from_user.id,
    )

async def help(message):
    return u"""Eu sou uma bot social com múltiplas personalidades progr\
amada para aprender conforme o ambiente onde estou. Para saber quais co\
mandos estou respondendo, envie /lista\nPara mais informações sobre a m\
inha atual personalidade, envie /info"""

async def welcome(message):
    return u"""Bem vinda(o)(e){members} ao grupo {title}\n\nVerifique a\
 mensagem fixada (se houver) para saber o que está acontecendo e se qui\
ser e puder, se apresente. Não parece, mas o pessoal daqui está genuina\
mente interessado em te ver escrevendo! Mas sem pressão, pode ser no te\
u tempo. Qualquer coisa, estou à disposição.""".format(
        members = 's' if len(message.new_chat_members) > 1 else ' ' + 
            ', '.join([' '.join([
                member['first_name'] or '',
                member['last_name'] or '',
            ]) for member in message.new_chat_members]),
        title = message.chat.title,
    )

async def portaria(message):
    return u"""sem querer caguetar @admin, mas taí de novo o {members}\
""".format(
        members = 's' if len(message.new_chat_members) > 1 else ' ' + 
            ', '.join([' '.join(
                [member['first_name'] or '',
                member['last_name'] or '',
            ]) for member in message.new_chat_members]),
    )

async def info(infos):
    return u"""Eu sou uma MateBot com personalidade padrão configurada \
para responder os comandos básicos. O meu código fonte está em \
{repository} , Quem me administra é {admin} , quem me desenvolve é \
{dev}\nSe quiser acompanhar meu processo de desenvolvimento, tem um can\
al de notícias {channel}\nTambém tem um grupo do telegram onde mais gen\
te interessada no meu desenvolvimento se encontra, o link de acesso é: \
{group}""".format(
        repository = infos.get('repository', u"algum lugar"),
        admin = infos.get('admin', u"Ninguém"),
        dev = infos.get('dev', u"Alguém"),
        channel = infos.get('channel', u"que eu não sei."),
        group = infos.get('group', u"eu não sei."),
    )

## Aiogram
async def add_handlers(dispatcher):
    ## Comando /info padrão
    @dispatcher.message_handler(
        commands = ['info'],
    )
    async def info_callback(message):
        await message_callback(message, ['info', dispatcher.config[
            'info'].get('personalidade', 'default'), message.chat.type])
        command = await message.reply(await info(dispatcher.config[
            'info']))
        await command_callback(command, ['info', dispatcher.config.get(
            'personalidade', 'default'), message.chat.type])

## Furhat
async def furhat_papagaio(config, message):
    return message.split(' ')[1:]

async def furhat_naoentendi(config, message):
    return u"Não entendi"

async def furhat_sevira(config, message):
    return u"Eu não sou {}".format(random.choice([
        u"a Alexa",
        u"o OK Google",
        u"a Siri",
    ]))

async def furhat_naosou(config, message):
    return u"Acho que tu me confundiu"

async def furhat_startswith_iterations():
    return [
        Iteration(text = 'repete', callback = furhat_papagaio),
    ] + [
        Iteration(text = subtext, callback = furhat_sevira
            ) for subtext in [
                'fab',
                'fabi',
                'fáb',
                'fábi',
                'fábio',
                'fabio',
            ]
    ]

async def furhat_endswith_iterations():
    return [
        Iteration(text = 'por favor', callback = furhat_naoentendi),
    ]

async def furhat_contains_iterations():
    return [
        Iteration(text = subtext, callback = furhat_naosou,
            ) for subtext in [
                'alexa',
                'a lexa',
                'google',
                'siri',
            ]
    ]
