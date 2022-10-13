"""
Plugin hash para ia.cecil: retorna message digest / secure hash de um texto 
em um determinado algoritmo
Documentação do hashlib - https://docs.python.org/3/library/hashlib.html

ia.cecil

Copyleft 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

## TODO: annotations

import logging
logger = logging.getLogger(__name__)

import hashlib
from aiogram import Dispatcher
from aiogram.utils.markdown import escape_md
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

def cmd_hash(args: dict) -> dict:
    """Generates a hashed version of supplied string"""
    type = 'nada'
    response = u"Que hash? De que algoritmo?"
    debug = u"Não consegui fazer o hash"
    parse_mode = None
    try:
        lista = ', '.join(sorted(hashlib.algorithms_guaranteed)).lower()
        if len(args['command_list']) > 1:
            try:
                algo = args['command_list'][0].lower()
                text = ' '.join(args['command_list'][1:]).encode('utf-8')
                if algo in [testing.lower() for testing in
                                        hashlib.algorithms_guaranteed]:
                    response = u"`%s`" % getattr(hashlib, algo, None)(text
                        ).hexdigest()
                    parse_mode = 'MarkdownV2'
                else:
                    response = """Desculpe, estou rodando em um servidor sem \
suporte para '%s', ou '%s' não é um algoritmo.\n\nAlgoritmos suportados: %s\
""" % (algo, algo, lista)
                return {
                    'status': True,
                    'type': args['command_type'],
                    'response': response,
                    'debug': u"hash bem sucedido",
                    'multi': False,
                    'parse_mode' : parse_mode,
                    'reply_to_message_id': args['message_id'],
                }
            except Exception as e:
                type = 'erro'
                response = """Erro tentando calcular o hash %s de '%s'.\n\n\
Os desenvolvedores vão ser notificados de qualquer forma. Mas tente \
novamente, por favor.\n\nAlgoritmos suportados: %s""" % (
                    algo, ' '.join(args['command_list'][1:]), lista)
                debug = u"hash falhou\nExceção: %s" % (e)
        else:
            type = 'erro'
            response = """Vossa excelência está tentando usar o bot de uma \
maneira incorreta, errada, equivocada. Vamos tentar novamente?\n\nA sintaxe \
deve ser exatamente assim:\n\n/hash (algoritmo) (mensagem)\n\nExemplo: /hash \
md5 Agora sim eu aprendi a usar o comando\n\nOutro exemplo: /hash sha256 \
MinhaSenhaSecreta1234\n\nAlgoritmos disponíveis: %s""" % (lista)
            debug = u"hash falhou, erro do usuário"
    except Exception as e:
        type = 'erro'
        response = """Erro tentando calcular hash.\n\nOs desenvolvedores vão \
ser notificados de qualquer forma. Quem estragou o plugin será \
responsabilizado."""
        debug = u"hash falhou\nExceção: %s" % (e)
    return {
        'status': False,
        'type': type,
        'response': response,
        'debug': debug,
        'multi': False,
        'parse_mode': parse_mode,
        'reply_to_message_id': args['message_id'],
    }

## TODO apagar todos lugares onde isto é utilizado e remover
def inner_hash(algo, text):
    return getattr(hashlib, algo, None)(text.encode('utf-8')).hexdigest()

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register Aiogram Handlers to Dispatcher"""
    try:
        @dispatcher.message_handler(commands = ['hash'])
        async def hash_callback(message):
            await message_callback(message, ['hash', message.chat.type])
            command = None
            ## lol
            try:
                hashes = cmd_hash({
                    'command_type': None,
                    'message_id': None,
                    'command_list': message.get_args().split(),
                    'parse_mode': None,
                })
                command = await message.reply(
                    u"{}".format(hashes['response']),
                    parse_mode = hashes['parse_mode'],
                )
            except Exception as exception:
                await error_callback(u"Erro tentando calcular hash",
                    message, exception, ['hash', 'exception'])
                command = await message.reply("""Não consegui calcular o hash \
por problemas técnicos. Os (ir)responsáveis serão avisados...""")
            await command_callback(command, ['hash', message.chat.type])
    except Exception as e:
        logger.exception(e)
        raise
