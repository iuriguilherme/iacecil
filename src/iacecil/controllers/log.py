"""
Plugin log para ia.cecil: logging/debugging

Copyleft 2016-2026 Iuri Guilherme <https://iuri.neocities.org/>

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
from aiogram.utils.formatting import (
    Text,
    Pre,
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

from .aiogram_v3.util import get_aiogram_context

key_error: str = """Mensagem não enviada para grupo de log. Para ativar log \
em grupos de telegram, coloque o bot em um grupo e use o chat_id do grupo no \
arquivo de configuração."""

async def tecido_logger(texto: str = '') -> int:
    """Log no console"""
    tecido_logger: object = logger.getLogger('tecido')
    tecido_logger.setLevel(logger.DEBUG)
    
    ctx = get_aiogram_context()
    config = ctx['config']
    if not config:
        logger.error("tecido_logger: No config found in context")
        return 1
        
    ## https://pymotw.com/3/socket/tcp.html
    # socket_echo_client.py
    # Create a TCP/IP socket
    sock: object = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ## JAMAIS bloquear
    # ~ sock.setblocking(0) ## Talvez bloquear de vez em quando
    # Connect the socket to the port where the server is listening
    server_address: tuple[str] = (
        config.tecido.get('host'),
        config.tecido.get('port'),
    )
    tecido_logger.info("connecting to {} port {}".format(*server_address))
    try:
        await sock.connect(server_address)
    except ConnectionRefusedError as e:
        tecido_logger.debug(f"""Servidor TextoTecidoPalavras não escutando em \
{config.tecido.get('host')}:{config.tecido.get('port')}\
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
    ctx = get_aiogram_context()
    bot = ctx['bot']
    config = ctx['config']
    
    if not bot or not config:
        logger.error(f"debug_logger: No bot/config in context. Error: {error}")
        return

    tb: Union[object, None] = None
    url: str = ''
    if hasattr(message, 'chat') and message.chat.type != "private":
        # ~ url = message.url
        try:
            url = message.link('link', as_html = False)
        except (AttributeError, TypeError):
            pass

    text: list = list()
    text.append(" ".join([" ".join(
        [Text("#" + d).as_markdown() for d in descriptions]),
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
            
            ## aiogram 3 Message.to_python() is replaced by .model_dump()
            try:
                msg_dict = message.model_dump()
            except AttributeError:
                msg_dict = message.to_python()
                
            text.append(Pre(json.dumps(msg_dict, indent = 2,
                ensure_ascii = False), language="").as_markdown()
            )
        except AttributeError as e:
            message = str(message).translate(
                str.maketrans('', '', '\\'))
            text.append(Pre(json.dumps(message, indent = 2,
                ensure_ascii = False), language="").as_markdown())
            logger.exception(e)
        except Exception as e:
            logger.exception(e)
        text.append('')
    if exception is not None:
        tb: Union[object, None] = \
            traceback.TracebackException.from_exception(exception)
        text.append(Pre(json.dumps(repr(exception), indent = 2,
            ensure_ascii = False), language="").as_markdown())
        text.append('')
        text.append(Pre(json.dumps(str(tb), indent = 2, ensure_ascii = False), language="").as_markdown())
        text.append('')
    text.append(Text(error).as_markdown())
    try:
        await bot.send_message(
            chat_id = config.telegram.get('users').get(
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
        ctx = get_aiogram_context()
        bot = ctx['bot']
        config = ctx['config']
        
        if not bot or not config:
            logger.error(f"exception_logger: No bot/config in context. Exception: {exception}")
            return

        tb: object = traceback.TracebackException.from_exception(exception)
        text = list()
        text.append(" ".join([" ".join([Text("#" + d).as_markdown() for d in \
            descriptions])]))
        text.append('')
        text.append(Pre(json.dumps(repr(exception), indent = 2,
            ensure_ascii = False), language="").as_markdown())
        text.append('')
        text.append(Pre(json.dumps(str(tb), indent = 2, ensure_ascii = False), language="").as_markdown())
        try:
            await bot.send_message(
                chat_id = config.telegram.get('users').get('special'
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
    ctx = get_aiogram_context()
    bot = ctx['bot']
    config = ctx['config']
    
    if not bot or not config:
        logger.error(f"info_logger: No bot/config in context.")
        return

    url = ''
    if hasattr(update, 'chat') and update.chat.type != "private":
        try:
            url = update.link('link', as_html = False)
        except (AttributeError, TypeError):
            pass
            
    text = list()
    text.append(" ".join([
        " ".join([Text("#" + d).as_markdown() for d in descriptions]),
        url,
    ]))
    text.append('')
    if update is not None:
        if not isinstance(update, str):
            try:
                try:
                    upd_dict = update.model_dump()
                except AttributeError:
                    upd_dict = update.to_python()
                text.append(Pre(json.dumps(upd_dict, indent = 2,
                    ensure_ascii = False), language="").as_markdown())
            except AttributeError as e:
                text.append(Pre(json.dumps(update, indent = 2,
                    ensure_ascii = False), language="").as_markdown())
                logger.exception(e)
        else:
            text.append(Pre(json.dumps(update, indent = 2,
                ensure_ascii = False), language="").as_markdown())
    try:
        ## TelegramTextoTecidoTabelas
        #await tecido_logger(getattr(update, 'text', ''))
        await bot.send_message(
            chat_id = config.telegram.get('users').get('special'
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
        ctx = get_aiogram_context()
        config = ctx.get('config')
        if not config:
            logger.error("furhat_logger: No config found in context")
            return
            
        furhat_config: dict = config.furhat
        furhat: object = await get_furhat(furhat_config.get('address'))
        await set_voice(furhat, furhat_config.get('voice'))
        await set_led(furhat, **furhat_config.get('led'))
        await set_face(furhat, furhat_config.get('mask'), furhat_config.get('character'))
        await do_say_text(furhat, text)
    except Exception as e:
        await exception_logger(e, ['log', 'furhat'])
        logger.exception(e)
