# vim:fileencoding=utf-8
#  Plugin archive para ia.cecil: Salva URL na Wayback Machine.
#  Copyleft (C) 2019-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

import requests
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
)

def cmd_a(args):
    try:
        if len(args['command_list']) > 0:
            wayback_machine_url = 'https://web.archive.org'
            requisicao = requests.get('/'.join([wayback_machine_url, 'save', ''.join(args['command_list'])]))
            if requisicao:
                response = u"Página salva com sucesso: %s" % (''.join([wayback_machine_url, requisicao.headers['Content-Location']]))
                debug = u"[#waybackmachine]: %s %s" % (str(requisicao), str(requisicao.headers))
            else:
                response = u"Não consegui salvar a página, erro: %s" % (requisicao.headers['X-Archive-Wayback-Runtime-Error'])
                debug = u"[#waybackmachine]: %s %s" % (str(requisicao), str(requisicao.headers))
            return {
                'status': True,
                'type': args['command_type'],
                'response': response,
                'debug': debug,
                'multi': False,
                'parse_mode': None,
                'reply_to_message_id': args['message_id'],
            }
        else:
            response = u"O comando vós já achardes. Agora me envia o comando mais um link, um URL, alguma coisa que está na world wide web e que eu possa salvar. Por exemplo:\n\n/a https://matehackers.org"
            debug = u"[#waybackmachine]: [nenhum link]"
    except Exception as e:
        response = u"Não consegui salvar a página por problemas técnicos. Os desenvolvedores devem ter sido avisados já, eu acho."
        debug = u"[#waybackmachine]: [exception] %s" % (e)
    return {
        'status': False,
        'type': 'erro',
        'response':    response,
        'debug': debug,
        'multi': False,
        'parse_mode': None,
        'reply_to_message_id': args['message_id'],
    }

## Aliases
def cmd_salvar(args):
    return cmd_a(args)
def cmd_arquivar(args):
    return cmd_a(args)
def cmd_arquivo(args):
    return cmd_a(args)
def cmd_wm(args):
    return cmd_a(args)

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Salva URL na Wayback Machine
        @dispatcher.message_handler(
            commands = ['a', 'archive', 'salvar', 'arquivar', 'wm'],
        )
        async def archive_callback(message):
            await message_callback(message, ['archive',
                message.chat.type])
            ## lol
            archive = cmd_a({
                'command_type': None,
                'message_id': None,
                'command_list': message.get_args(),
            })
            command = await message.reply(u"{}".format(archive[
                'response']))
            await command_callback(command, ['archive',
                message.chat.type])
    except Exception as exception:
        raise
