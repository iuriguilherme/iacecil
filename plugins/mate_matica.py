# vim:fileencoding=utf-8
#  Plugin mate-matica para ia.cecil: Mate Mática
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
#  

import logging
logger = logging.getLogger(__name__)

import binascii, math, numpy, os
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

def dice(faces = 6, seed = None, *args, **kwargs) -> int:
    """Retorna um valor pseudo aleatório de uma das faces de um dado."""
    numpy.random.seed(seed)
    return numpy.random.randint(1, faces + 1)

def coord(seed = None, *args, **kwargs) -> float:
    """Retorna um valor pseudo aleatório entre zero e um."""
    numpy.random.seed(seed)
    return numpy.random.rand()

## π
def cmd_pi(args):
    try:
        tamanho = 51
        ## Eu não faço args['command_list'][0] pra evitar IndexError
        if ''.join(args['command_list']).isdigit():
            tamanho = int(''.join(args['command_list'])) + 2 ## Ignorar o '3.'
        constante = 4 * math.atan(1) ## Esta é uma boa aproximação de pi
        response = str(constante)[:tamanho]
        return {
            'status': True,
            'type': 'grupo',
            'response': response,
            'debug': u"pi calculado",
            'multi': False,
            'parse_mode': None,
            'reply_to_message_id': args['message_id'],
        }
    except Exception as e:
            return {
                'status': False,
                'type': 'erro',
                'response': u"Erro tentando calcular pi.",
                'debug': u"Pi falhou, exceção: %s" % (e),
                'multi': False,
                'parse_mode': None,
                'reply_to_message_id': args['message_id'],
            }

## φ
def cmd_phi(args):
    try:
        tamanho = 51
        ## Eu não faço args['command_list'][0] pra evitar IndexError
        if ''.join(args['command_list']).isdigit():
            tamanho = int(''.join(args['command_list'])) + 2 ## Ignorar o '1.'
        constante = ( 1 + math.sqrt(5) ) / 2 ## Esta é uma boa aproximação de phi
        response = str(constante)[:tamanho]
        return {
            'status': True,
            'type': 'grupo',
            'response': response,
            'debug': u"phi calculado",
            'multi': False,
            'parse_mode': None,
            'reply_to_message_id': args['message_id'],
        }
    except Exception as e:
            return {
                'status': False,
                'type': 'erro',
                'response': u"Erro tentando calcular phi.",
                'debug': u"Phi falhou, exceção: %s" % (e),
                'multi': False,
                'parse_mode': None,
                'reply_to_message_id': args['message_id'],
            }

## String hexadecimal suficientemente aleatória
def cmd_random(args):
    try:
        tamanho = 8
        response = list()
        ## Eu não faço args['command_list'][0] pra evitar IndexError
        ## Mas tem outras formas de testar isto, ler o manual do dict()
        argumento = ''.join(args['command_list'])
        if argumento:
            if argumento.isdigit() and int(argumento) <= 872 and int(argumento) > 2:
                tamanho = int(argumento)
            else:
                response.append(u"Tamanho deve ser entre 1 e 872, %s não serve! Revertendo para %s...\n" % (str(argumento), str(tamanho)))
        aleatorio = os.urandom(tamanho)
        response.append(u"<b>HEX</b>:\n<pre>%s</pre>\n" % binascii.hexlify(aleatorio).decode('utf-8'))
        response.append(u"<b>B64</b>:\n<pre>%s</pre>" % binascii.b2a_base64(aleatorio).decode('utf-8'))
        response.append(u"<b>HQX</b>:\n<pre>%s</pre>" % binascii.b2a_hqx(binascii.rlecode_hqx(aleatorio)).decode('utf-8'))
        return {
            'status': True,
            'type': 'grupo',
            'response': '\n'.join(response),
            'debug': u"Número aleatório gerado",
            'multi': False,
            'parse_mode': 'HTML',
            'reply_to_message_id': args['message_id'],
        }
    except Exception as e:
        return {
            'status': False,
            'type': 'erro',
            'response': u"Erro tentando gerar número aleatório.",
            'debug': u"Random falhou, exceção: %s" % (e),
            'multi': False,
            'parse_mode': None,
            'reply_to_message_id': args['message_id'],
        }

def cmd_r(args):
    return cmd_random(args)

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Gera números aleatórios
        @dispatcher.message_handler(
            commands = ['random', 'rand', 'r'],
        )
        async def random_callback(message):
            await message_callback(message, ['random',
                message.chat.type])
            ## lol
            r = cmd_r({
                'message_id': None,
                'command_list': message.get_args(),
            })
            command = await message.reply(
                u"{}".format(r['response']),
                parse_mode = r['parse_mode'],
            )
            await command_callback(command, ['random',
                message.chat.type])

        ## Uma boa aproximação de pi
        @dispatcher.message_handler(
            commands = ['pi'],
        )
        async def pi_callback(message):
            await message_callback(message, ['pi', message.chat.type])
            command = await message.reply(str(math.pi))
            await command_callback(command, ['pi', message.chat.type])

        ## Uma boa aproximação de φ
        @dispatcher.message_handler(
            commands = ['phi'],
        )
        async def phi_callback(message):
            await message_callback(message, ['phi', message.chat.type])
            command = await message.reply(
                str(( 1 + math.sqrt(5) ) / 2),
            )
            await command_callback(command, ['phi', message.chat.type])

        @dispatcher.message_handler(
            commands = ['dice', 'dado', 'd'],
        )
        async def dice_callback(message):
            """
            Retorna um valor pseudo aleatório de uma face de um dado com 
            tantos lados quantos o primeiro argumento. Padrão: 6
            """
            await message_callback(message, ['dice', message.chat.type])
            faces = 6
            try:
                if message.get_args() not in [None, '', ' ', 0]:
                    faces = int(message.get_args())
                    if not faces > 0:
                        raise ValueError()
            except ValueError:
                await message.reply(f"""{message.get_args()} não é um \
número de faces de um dado válido, vou usar um dado de seis faces normal.\
""")
            command = await message.reply(dice(faces))
            await command_callback(command, ['dice', message.chat.type])
        
    except Exception as exception:
        raise
