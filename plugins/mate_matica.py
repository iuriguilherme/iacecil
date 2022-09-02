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

import binascii, math, mpmath, numpy, os, sympy
from decimal import Decimal
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    exception_callback,
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

async def get_pi(precision: int = 53) -> str:
    """A melhor aproximação de π com python (por enquanto)"""
    while precision > 0:
        try:
            with mpmath.workdps(precision + 1):
                return str(mpmath.pi)[:-1]
        except Exception as exception:
            await exception_callback(exception, ['matematica', 'fib'])
            return await get_pi(precision - 1)
    return str(mpmath.pi)[:-1]

async def get_phi(precision: int = 53) -> str:
    """A melhor aproximação de φ com python (por enquanto)"""
    while precision > 0:
        try:
            with mpmath.workdps(precision + 1):
                return str(mpmath.phi)[:-1]
        except Exception as exception:
            await exception_callback(exception, ['matematica', 'fib'])
            return await get_phi(precision - 1)
    return str(mpmath.phi)[:-1]

async def get_fibonacci(position: int = 0) -> str:
    """Um número de uma posição arbitrária da escala de fibonacci"""
    try:
        return str(sympy.fibonacci(position))
    except Exception as exception:
        await exception_callback(exception, ['matematica', 'fib'])
        return "Não consegui! Tente outro número :("

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

        @dispatcher.message_handler(
            commands = ['pi'],
        )
        async def pi_callback(message):
            await message_callback(message, ['pi', message.chat.type])
            precision: int = 53
            if ''.join(message.get_args()).isdigit():
                precision = max(0, int(''.join(message.get_args()))) + 2
            command = await message.reply(get_pi(precision))
            await command_callback(command, ['pi', message.chat.type])

        @dispatcher.message_handler(
            commands = ['phi'],
        )
        async def phi_callback(message):
            await message_callback(message, ['phi', message.chat.type])
            precision: int = 53
            if ''.join(message.get_args()).isdigit():
                precision = max(0, int(''.join(message.get_args()))) + 2
            command = await message.reply(get_phi(precision))
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

        ## Acha uma posição na escala Fibonacci
        @dispatcher.message_handler(
            commands = ['fib', 'fibonacci'],
        )
        async def fibonacci_callback(message):
            await message_callback(message, ['fibonacci', message.chat.type])
            position: int = 0
            if ''.join(message.get_args()).isdigit():
                position = max(0, int(''.join(message.get_args())))
            command = await message.reply(await get_fibonacci(position))
            await command_callback(command, ['fibonacci', message.chat.type])

    except Exception as exception:
        raise
