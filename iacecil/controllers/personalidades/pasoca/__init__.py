# vim:fileencoding=utf-8
#  Plugin personalidades para ia.cecil: Robô também é gente?
#  Copyleft (C) 2020-2022 Iuri Guilherme
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

import logging
logger = logging.getLogger(__name__)

### Personalidade Tia do Zap
import random
from aiogram import filters
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from iacecil.models import Iteration
from iacecil.controllers.personalidades.default import (
    start,
    help,
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations as \
        furhat_startswith_iterations_default,
    add_handlers as add_default_handlers,
)

## TODO Sentenças impróprias para publicar no Github por razões diversas
try:
    from instance.personalidades.pasoca import random_texts
except:
    from iacecil.controllers.personalidades.pasoca import random_texts

async def info():
    return u"""Eu sou uma chatbot com personalidade de tia do zap confi\
gurada e desenvolvido para mandar mensagem de bom dia e hoax (termo mod\
erno: "fake news"). A tua opinião em relação à minha atitude influencia\
 no meu comportamento que nunca vai ser pra te agradar. Para enviar sug\
estões ou relatar problemas para o pessoal que faz manutenção, use o co\
mando /feedback por exemplo /feedback Obrigado pelo bot!"""

async def welcome(message):
    return await random_texts.welcome()

async def portaria(message):
    return u"ó @admin, esse é persona non grata!"

async def mensagem_bomdia():
    return await message.reply(await random_texts.bomdia())

## Aiogram
async def add_handlers(dispatcher):
    await add_default_handlers(dispatcher)
    @dispatcher.message_handler(commands = ['bomdia', 'mensagem'])
    async def mensagem_bomdia_callback(message):
        await message_callback(message, [
            'mensagemBomdia',
            dispatcher.config['info'].get('personalidade', 'pasoca'),
            message.chat.type,
        ])
        command = await mensagem_bom_dia()
        await command_callback(command, [
            'mensagemBomdia',
            dispatcher.config['info'].get('personalidade', 'pasoca'),
            message.chat.type,
        ])
    ## Reply every good morning
    @dispatcher.message_handler(
        filters.Text(contains = 'bom dia', ignore_case = True),
        filters.Regexp('+[.!-]*'.join(letter for letter in 'bom dia')),
    )
    async def resposta_bomdia_callback(message):
        await message_callback(message, [
            'resposta',
            'bomdia',
            dispatcher.config['info'].get('personalidade', 'pasoca'),
            message.chat.type,
        ])
        command = await message.reply(u"Bom dia.")
        await command_callback(command, [
            'resposta',
            'bomdia',
            dispatcher.config['info'].get('personalidade', 'pasoca'),
            message.chat.type,
        ])
    ## The ultimate tia do zap reply
    @dispatcher.message_handler(
        filters.Regexp('''(é|eh) p(ara|ra|a)( v|v)(ê|e|er) ou p(a|ra|ar\
a)( c|c)(o|u)m(er|ê|e)'''),
    )
    async def resposta_bomdia_callback(message):
        await message_callback(message, [
            'resposta',
            'pasoca',
            dispatcher.config['info'].get('personalidade', 'pasoca'),
            message.chat.type,
        ])
        command = await message.reply(u"É paçoca. Paçocá no teu cu.")
        await command_callback(command, [
            'resposta',
            'pasoca',
            dispatcher.config['info'].get('personalidade', 'pasoca'),
            message.chat.type,
        ])

## Furhat
async def furhat_bomdia(config, message):
    return await random_texts.bom_dia()

async def furhat_contains_iterations():
    return [Iteration(text = 'bom dia', callback = furhat_bomdia)]
