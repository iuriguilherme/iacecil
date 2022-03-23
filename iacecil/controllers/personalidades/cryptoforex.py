# vim:fileencoding=utf-8
#  Plugin personalidades para ia.cecil: Robô também é gente?
#  Copyleft (C) 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

### Personalidade investidora forex do @cryptoforexbot
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from iacecil.models import Iteration
from iacecil.controllers.personalidades.default import (
    start,
    portaria,
    furhat_contains_iterations,
    furhat_endswith_iterations,
    furhat_startswith_iterations,
    add_handlers as add_default_handlers,
)

async def help(message):
    return u"""
Crypto Forex Bot help

This bot convert values in some cryptocurrencies to fiat/crypto currenc\
ies.



To see the price info for a cryptocurrency, use /price <coin>
Example: /price ETH



To convert values, use /conv <value> <from> <to>
Where <value> must be a valid real number (commas will be ignored);
<from> may be a coinmarketcap id or a cryptocurrency symbol;
<to> may be any fiat or cryptocurrency symbol supported by coinmarketca\
p;

Example: /conv 1 BTC USD

To see a list of available commands, type /lista
"""

async def welcome(message):
    return u"""Bem vinda(o) {members} ao grupo {title}\n\nVerifique a m\
ensagem fixada (se houver) para saber o que está acontecendo e quais sã\
o as regras do grupo. Qualquer coisa, estou à disposição. Mas não acost\
uma que é de graça...""".format(
        members = 's' if len(message.new_chat_members) > 1 else ' ' + 
            ', '.join([' '.join([
                member['first_name'] or '',
                member['last_name'] or ''],
            ) for member in message.new_chat_members]),
        title = message.chat.title,
    )

async def info(infos):
    return u"""Eu sou uma MateBot com personalidade de investidora fore\
x configurada para converter valores de criptomoedas, entre outros coma\
ndos relacionados ao criptomercado. O meu código fonte está em \
{repository} , Quem me administra é {admin} , quem me desenvolve é \
{dev}\nSe quiser acompanhar meu processo de desenvolvimento, tem um can\
al de notícias {channel}\nTambém tem um grupo do telegram onde mais gen\
te interessada no meu desenvolvimento se encontra, o link de acesso \
{group}""".format(
        repository = infos.get('repository', u"algum lugar"),
        admin = infos.get('admin', u"Ninguém"),
        dev = infos.get('dev', u"Alguém"),
        channel = infos.get('channel', u"que eu não sei."),
        group = infos.get('group', u"eu não sei."),
    )

async def add_handlers(dispatcher):
    await add_default_handlers(dispatcher)
