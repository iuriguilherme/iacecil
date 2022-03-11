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

### Personalidade metarec https://metareciclagem.github.io/
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)
from plugins.personalidades.default import (
    info,
    start,
    welcome,
)

async def tropixel(message):
    return u"""Bem vinde{members}!\n\nSe você quer ser desconstruíde e \
re-construíde, ter suas idéias modificadas, reificadas, pisoteadas e am\
adas, se seu ego é grande o suficiente para ter amor ao que faz mas con\
segue reconhecer o que os outros fazem sem inveja, se não está aqui bus\
cando promoção social, mérito ou grana, e se, acima de tudo, acredita e\
m fadas, duendes e um mundo perfeito, seja bem-vinde a {title}.\n\nUma \
rede onde maluques conversam, jogam bola, mandam emails, discutem e faz\
em as pazes, filosofam sobre vida e morte, colaboração, apropriação de \
tecnologia, como as coisas são por dentro, de onde viemos e para onde v\
amos.\n\nAviso de utilidade pública: Não nos responsabilizamos pelas mo\
dif\icações causadas nos seus neurônios após o convívio (prolongado ou \
não) com esta comunidade. Use com moderação.\n\nSe apesar de todos esse\
s avisos você ainda está à procura de pessoas que fazem parte dessa red\
e, nós nos encontramos aos sábados no Boteco Tropixel (use o comando /b\
oteco pra pegar o link), e fora do tempo no site/forum/rede Tropixel (u\
se o comando /rede pra pegar o link).""".format(
        members = 's' if len(message.new_chat_members) > 1 else ' ' + 
            ', '.join([' '.join([
                member['first_name'] or '',
                member['last_name'] or '',
            ]) for member in message.new_chat_members]),
        title = message.chat.title,
    )

async def portaria(message):
    return u"""...sem querer incomodar @admin, mas tá na minha lista de\
 desafetos o {members} e o nosso convívio precisa de mais terapia.\
""".format(
        members = 's' if len(message.new_chat_members) > 1 else ' ' + 
            ', '.join([' '.join(
                [member['first_name'] or '',
                member['last_name'] or '',
            ]) for member in message.new_chat_members]),
    )

async def add_handlers(dispatcher):
    ## Comando /info herdado da personalidade padrão
    @dispatcher.message_handler(
        commands = ['info'],
    )
    async def info_callback(message):
        await message_callback(message, ['info',
            dispatcher.bot.get('personalidade', 'metarec'),
            message.chat.type],
        )
        command = await message.reply(await info(dispatcher.bot.config['info']))
        await command_callback(command, ['info',
            dispatcher.bot.get('personalidade', 'metarec'),
            message.chat.type],
        )
