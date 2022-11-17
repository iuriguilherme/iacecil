"""
Plugin log para ia.cecil: logging/debugging

Copyleft 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
logger = logging.getLogger(__name__)

import datetime
import json
import socket
import traceback
from aiogram import (
    Bot,
    Dispatcher,
    types,
)
from aiogram.utils.markdown import (
    escape_md,
    pre,
)
from quart import current_app
from typing import Union
from .. import (
    commit,
    name,
    version,
)
from .persistence.zodb_orm import log_message
from .furhat_bot.remote_api import (
    do_attend_user,
    do_say_text,
    get_furhat,
    set_face,
    set_led,
    set_voice,
)

key_error: str = """Mensagem não enviada para grupo de log. Para ativar log \
em grupos de telegram, coloque o bot em um grupo e use o chat_id do grupo no \
arquivo de configuração."""

async def tecido_logger(texto: str = '') -> int:
    """Log no console"""
    tecido_logger: object = logger.getLogger('tecido')
    tecido_logger.setLevel(logger.DEBUG)
    dispatcher: Dispatcher = Dispatcher.get_current()
    bot: Bot = dispatcher.bot
    ## https://pymotw.com/3/socket/tcp.html
    # socket_echo_client.py
    # Create a TCP/IP socket
    sock: object = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ## JAMAIS bloquear
    # ~ sock.setblocking(0) ## Talvez bloquear de vez em quando
    # Connect the socket to the port where the server is listening
    server_address: tuple[str] = (
        dispatcher.config.tecido.get('host'),
        dispatcher.config.tecido.get('port'),
    )
    tecido_logger.info("connecting to {} port {}".format(*server_address))
    try:
        await sock.connect(server_address)
    except ConnectionRefusedError as e:
        tecido_logger.debug(f"""Servidor TextoTecidoPalavras não escutando em \
{dispatcher.config.tecido.get('host')}:{dispatcher.config.tecido.get('port')}\
""")
        tecido_logger.exception(e)
        return 1
    try:
        # Send data
        ## Texto da mensagem passado pelo parâmetro desta função
        message: bytes = texto.encode('raw_unicode_escape', 'replace')
        # ~ message = bytes(texto, 'cp860')
        # ~ message = bytearray(texto, 'UTF-8')
        tecido_logger.info(f"sending {message:!r}")
        await sock.sendall(message)
        # Look for the response
        # ~ amount_received = 0
        # ~ amount_expected = len(message)
        # ~ while amount_received < amount_expected:
            # ~ data = sock.recv(16)
            # ~ amount_received += len(data)
            # ~ tecido_logger.info(f"received {data:!r}")
    except Exception as e:
        tecido_logger.exception(e)
        return 1
    finally:
        tecido_logger.info("closing socket")
        await sock.close()
        return 0

async def debug_logger(
    error: str = "Alguma coisa deu errado",
    message: types.Message = None,
    exception: Exception = None,
    descriptions: list = 'error',
) -> None:
    """Envia mensagem para o grupo DEBUG do Telegram em caso de erro"""
    dispatcher: Dispatcher = Dispatcher.get_current()
    bot: Bot = dispatcher.bot
    tb: Union[object, None] = None
    url: str = ''
    if hasattr(message, 'chat') and message.chat.type != "private":
        # ~ url = message.url
        url = message.link('link', as_html = False)
    text: list = list()
    text.append(" ".join([" ".join(
        [escape_md("#" + d) for d in descriptions]),
        url,
    ]))
    text.append('')
    if message is not None:
        try:
            original_text: Union[str, None] = getattr(message, 'text', None)
            if original_text is not None and hasattr(original_text,
                'translate',
            ):
                original_text: str = original_text.translate(
                    str.maketrans('', '', '\\')
                )
                message['text']: str = original_text
            text.append(pre(json.dumps(message.to_python(), indent = 2,
                ensure_ascii = False))
            )
        except AttributeError as e:
            message = str(message).translate(
                str.maketrans('', '', '\\'))
            text.append(pre(json.dumps(message, indent = 2,
                ensure_ascii = False)))
            logger.exception(e)
        except Exception as e:
            logger.exception(e)
        text.append('')
    if exception is not None:
        tb: Union[object, None] = \
            traceback.TracebackException.from_exception(exception)
        text.append(pre(json.dumps(repr(exception), indent = 2,
            ensure_ascii = False)))
        text.append('')
        text.append(pre(json.dumps(str(tb), indent = 2, ensure_ascii = False)))
        text.append('')
    text.append(escape_md(error))
    try:
        await bot.send_message(
            chat_id = dispatcher.config.telegram.get('users').get(
                'special').get('debug'),
            text = '\n'.join(text),
            disable_notification = True,
            parse_mode = "MarkdownV2",
        )
    except KeyError as e:
        logger.debug(key_error)
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

async def exception_logger(
    exception: Exception = None,
    descriptions: list = 'error',
) -> None:
    """Manda mensagem para grupo de DEBUG do Telegram em caso de exceção"""
    try:
        dispatcher: Dispatcher = Dispatcher.get_current()
        bot: Bot = dispatcher.bot
        tb: object = traceback.TracebackException.from_exception(exception)
        text = list()
        text.append(" ".join([" ".join([escape_md("#" + d) for d in \
            descriptions])]))
        text.append('')
        text.append(pre(json.dumps(repr(exception), indent = 2,
            ensure_ascii = False)))
        text.append('')
        text.append(pre(json.dumps(str(tb), indent = 2, ensure_ascii = False)))
        await bot.send_message(
            chat_id = dispatcher.config.telegram.get('users').get('special'
                ).get('debug'),
            text = '\n'.join(text),
            disable_notification = True,
            parse_mode = "MarkdownV2",
        )
    except KeyError as e:
        logger.debug(key_error)
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

async def info_logger(
    update: types.Update,
    descriptions: list = ['none'],
) -> None:
    """Manda mensagem para grupo INFO do Telegram para eventos configurados"""
    dispatcher: Dispatcher = Dispatcher.get_current()
    bot: Bot = dispatcher.bot
    url = ''
    if hasattr(update, 'chat') and update.chat.type != "private":
        # url = update.url
        url = update.link('link', as_html = False)
    text = list()
    text.append(" ".join([
        " ".join([escape_md("#" + d) for d in descriptions]),
        url,
    ]))
    text.append('')
    if update is not None:
        if not isinstance(update, str):
            try:
                text.append(pre(json.dumps(update.to_python(), indent = 2,
                    ensure_ascii = False)))
            except AttributeError as e:
                text.append(pre(json.dumps(update, indent = 2,
                    ensure_ascii = False)))
                logger.exception(e)
        else:
            text.append(pre(json.dumps(update, indent = 2,
                ensure_ascii = False)))
    try:
        ## TelegramTextoTecidoTabelas
        #await tecido_logger(getattr(update, 'text', ''))
        await bot.send_message(
            chat_id = dispatcher.config.telegram.get('users').get('special'
                ).get('info'),
            text = '\n'.join(text),
            disable_notification = True,
            parse_mode = "MarkdownV2",
        )
    except KeyError as e:
        logger.debug(key_error)
        logger.exception(e)
    except Exception as e:
        logger.exception(e)

async def zodb_logger(message: types.Message) -> None:
    """Salva mensagem no banco de dados ZODB"""
    try:
        await log_message(message)
    except Exception as e:
        await exception_logger(e, ['log', 'zodb'])
        logger.exception(e)

async def furhat_logger(text: str) -> None:
    """Sends message to Furhat robot"""
    try:
        logger.info("Sending to Furhat...")
        config: dict = Dispatcher.get_current().config.furhat
        furhat: object = await get_furhat(config.get('address'))
        await set_voice(furhat, config.get('voice'))
        await set_led(furhat, **config.get('led'))
        await set_face(furhat, config.get('mask'), config.get('character'))
        await do_say_text(furhat, text)
    except Exception as e:
        await exception_logger(e, ['log', 'furhat'])
        logger.exception(e)
