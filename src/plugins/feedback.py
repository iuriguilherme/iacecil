"""
Plugin feedback para ia.cecil: Envia feedback para o grupo de administração.

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

import logging
logger = logging.getLogger(__name__)

import json
from aiogram import (
    Dispatcher,
    exceptions,
)
from aiogram.utils.markdown import escape_md
from typing import Union
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

## TODO: Este plugin nunca foi testado para a eventualidade da inexistência 
## ou não permissão de envio para o grupo de administração.

def cmd_feedback(kwargs: dict) -> dict[str, str]:
    """Ancient telepot handler for the /feedback command"""
    try:
        if len(kwargs['command_list']) > 0:
            return {
                'status': True,
                'type': "feedback",
                'response': """Obrigado pelo feedback! Alguém em algum \
momento vai ler, eu acho.""",
                'feedback': ' '.join(kwargs['command_list']),
                'debug': "Feedback bem sucedido",
                'multi': False,
                'parse_mode': None,
                'reply_to_message_id': args['message_id'],
            }
        else:
            response: str = """Erro tentando enviar feedback. Você deve \
seguir este modelo:\n\n/feedback Digite a mensagem aqui"""
            debug: str = "Feedback falhou, mensagem vazia"
    except Exception as e:
        response: str = """Erro tentando enviar feedback. Os desenvolvedores \
vão ser notificados de qualquer forma. Mas tente novamente, por favor."""
        debug: str = f"Feedback falhou.\nExceção: {e}"
        logger.exception(e)
    return {
        'status': False,
        'type': "erro",
        'response': response,
        'debug': debug,
        'multi': False,
        'parse_mode': None,
        'reply_to_message_id': kwargs['message_id'],
    }

def cmd_f(args):
    return cmd_feedback(args)

## Aiogram
async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register Aiogram Handlers to Dispatcher"""
    try:
        @dispatcher.message_handler(commands = ['feedback', 'feed'])
        async def feedback_callback(message):
            await message_callback(message, ['feedback',
                message.chat.type])
            if message.get_args():
                try:
                    url: Union[str, None] = await \
                        message.chat.export_invite_link()
                except exceptions.BadRequest as exception:
                    await error_callback("""Erro com método \
chat.export_invite_link""", message, exception, ['feedback'])
                    url: Union[str, None] = None
                try:
                    ## TODO consertar esse horror
                    await dispatcher.bot.send_message(
                        chat_id = dispatcher.config.telegram[
                            'users']['special']['feedback'],
                        text = u"#feedback enviado\nde" + u"""{chat} \
{user} (<b>{user_id}</b>):\n{link}\n""".format(
                                user = message.from_user.mention,
                                user_id = message.from_user.id,
                                chat = u""" {chat_link} (<b>{chat_id}</\
b>)\npor""".format(
                                    chat_link = u"""<a href='{url}'>\
{title}</a>""".format(
                                            url = url,
                                            title = message.chat.title,
                                        ) if url else
                                        u"{title}".format(
                                            title = message.chat.title,
                                        ),
                                    chat_id = message.chat.id,
                                ) if 
                                    message.chat.type in ['group',
                                        'supergroup'] else ' ',
                                link = u"{}\n".format(
                                    message.link('link')
                                ) if message.chat.type in ['group',
                                    'supergroup'] else '',
                            ) + u"<pre>{feedback}</pre>".format(
                                feedback = message.get_args(),
                        ),
                        parse_mode = "HTML",
                    )
                    command = await message.reply(u"""Muito obrigado pe\
lo feedback, vós sois muito gentil! Alguém em algum momento vai ler, eu\
 acho...""")
                except KeyError as exception:
                    await error_callback(u"""Erro tentando enviar respo\
sta avisando que o feedback deu certo. O problema é que não tá configur\
ado certo no arquivo de configuração os parâmetros pertinentes. Eu acho\
.""", message, exception, ['feedback'])
                    logger.warning(u"""Alguém mandou /feedback mas não \
tem nenhum grupo registrado para receber!\nExceção: {}""".format(
                        json.dumps(repr(e), indent=2)))
                    command = await message.reply(u"""Muito obrigado pe\
lo feedback, vós sois muito gentil! Infelizmente ninguém vai ler porque\
 não me configuraram para receber feedback... \U0001f61e""")
                except Exception as exception:
                    await error_callback(u"""Erro tentando enviar respo\
sta avisando que o feedback deu certo. Ver log de depuração acima pra t\
entar entender o que aconteceu.""", message, exception, ['feedback'])
                    logger.warning(u"Exceção: {}".format(json.dumps(
                        repr(exception), indent=2))
                    )
                    command = await message.reply(u"""Muito obrigado pe\
lo feedback, vós sois muito gentil! Infelizmente ninguém vai ler porque\
 eu tive um problema técnico. Mas o erro que aconteceu enquanto eu tent\
ava enviar feedback, vão ler! Desculpe por isto \U0001f61e""")
            else:
                command = await message.reply(escape_md(u"""Obrigado pe\
la tentativa, mas se for pra mandar feedback tem que escrever alguma co\
isa! Exemplo:\n""") + u"`{} Muito obrigado pelo bot!`".format(
                    message.get_command()), parse_mode = "MarkdownV2")
            await command_callback(command, ['feedback',
                message.chat.type])
    except Exception as e:
        logger.exception(e)
        raise
