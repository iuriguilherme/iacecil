# vim:fileencoding=utf-8
#  Plugin log para ia.cecil: Logging/debugging
#  Copyleft (C) 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

import BTrees, datetime, json, logging, socket, transaction, \
    ZODB, ZODB.FileStorage
from aiogram import (
    Dispatcher,
    types,
)
from aiogram.utils.markdown import (
    escape_md,
    pre,
)
from iacecil import version

## Telepot
## FIXME Deprecated
class log_str():
    def __init__(self):
        pass
    def debug(message):
        return u'[%s] [DEBUG] %s' % (str(datetime.datetime.now()), message)
    def info(message):
        return u'[%s] [INFO] %s' % (str(datetime.datetime.now()), message)
    def warn(message):
        return u'[%s] [WARN] (?) %s' % (str(datetime.datetime.now()), message)
    def err(message):
        return u'[%s] [ERR] (!) %s' % (str(datetime.datetime.now()), message)
    def cmd(command):
        return u'[%s] [CMD] Executando "%s"' % (str(datetime.datetime.now()), command)
    def rcv(target, message):
        return u'[%s] [RCV] Recebemos "%s" de %s' % (str(datetime.datetime.now()), message, target)
    def send(target, message):
        return u'[%s] [SEND] Enviando "%s" para %s' % (str(datetime.datetime.now()), message, target)

key_error = u"""Mensagem não enviada para grupo de log. Para ativar log\
em grupos de telegram, coloque o bot em um grupo e use o chat_id do gru\
po no arquivo de configuração."""

async def tecido_logger(texto: str = ''):
    logger = logging.getLogger('tecido')
    logger.setLevel(logging.DEBUG)
    dispatcher = Dispatcher.get_current()
    bot = dispatcher.bot
    ## https://pymotw.com/3/socket/tcp.html
    # socket_echo_client.py
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ## JAMAIS bloquear
    # ~ sock.setblocking(0) ## Talvez bloquear de vez em quando
    # Connect the socket to the port where the server is listening
    server_address = (
        bot.info['tecido']['host'],
        bot.info['tecido']['port'],
    )
    logger.info('connecting to {} port {}'.format(*server_address))
    try:
        await sock.connect(server_address)
    except ConnectionRefusedError:
        logger.debug(u"""Servidor TextoTecidoPalavras não escutando em \
{0}:{1}""".format(bot.info['tecido']['host'],
        bot.info['tecido']['port']))
        return 1
    try:
        # Send data
        ## Texto da mensagem passado pelo parâmetro desta função
        message = texto.encode('raw_unicode_escape', 'replace')
        # ~ message = bytes(texto, 'cp860')
        # ~ message = bytearray(texto, 'UTF-8')
        logger.info('sending {!r}'.format(message))
        await sock.sendall(message)
        # Look for the response
        # ~ amount_received = 0
        # ~ amount_expected = len(message)
        # ~ while amount_received < amount_expected:
            # ~ data = sock.recv(16)
            # ~ amount_received += len(data)
            # ~ logger.info('received {!r}'.format(data))
    except Exception as e:
        logger.debug(repr(e))
        return 1
    finally:
        logger.info('closing socket')
        await sock.close()
        return 0

async def debug_logger(
    error: str = u"Alguma coisa deu errado",
    message: types.Message = None,
    exception: Exception = None,
    descriptions: list = 'error',
):
    dispatcher = Dispatcher.get_current()
    bot = dispatcher.bot
    url = ''
    if hasattr(message, 'chat') and message.chat.type != "private":
        # ~ url = message.url
        url = message.link('link', as_html = False)
    text = list()
    text.append(
        u" ".join([
            u" ".join([escape_md("#" + d) for d in descriptions]),
            url,
        ])
    )
    text.append('')
    if message is not None:
        try:
            original_text = message.get('text', None)
            if original_text is not None and hasattr(original_text,
                'translate',
            ):
                original_text = original_text.translate(
                    str.maketrans('', '', '\\')
                )
                message['text'] = original_text
            text.append(pre(json.dumps(message.to_python(), indent = 2,
                ensure_ascii = False))
            )
        except AttributeError:
            message = str(message).translate(
                str.maketrans('', '', '\\')
            )
            text.append(pre(json.dumps(message, indent = 2,
                ensure_ascii = False))
            )
        text.append('')
    if exception is not None:
        text.append(pre(json.dumps(repr(exception), indent = 2,
            ensure_ascii = False))
        )
        text.append('')
    text.append(escape_md(error))
    try:
        await bot.send_message(
            chat_id = bot.users['special']['debug'],
            text = '\n'.join(text),
            disable_notification = True,
            parse_mode = "MarkdownV2",
        )
    except KeyError:
        logging.debug(key_error)
    except Exception as e:
        logging.critical(repr(e))

async def exception_logger(
    exception: Exception = None,
    descriptions: list = 'error',
):
    dispatcher = Dispatcher.get_current()
    bot = dispatcher.bot
    text = list()
    text.append(
        u" ".join([
            u" ".join([escape_md("#" + d) for d in descriptions]),
        ])
    )
    text.append('')
    text.append(pre(json.dumps(repr(exception), indent = 2,
        ensure_ascii = False))
    )
    try:
        await bot.send_message(
            chat_id = bot.users['special']['debug'],
            text = '\n'.join(text),
            disable_notification = True,
            parse_mode = "MarkdownV2",
        )
    except KeyError:
        logging.debug(key_error)
    except Exception as e:
        logging.critical(repr(e))

async def zodb_logger(message):
    dispatcher = Dispatcher.get_current()
    try:
        storage = ZODB.FileStorage.FileStorage(
            'instance/zodb/{}.{}.fs'.format(
            dispatcher.bot.id,
            message.chat.id,
        ))
        db = ZODB.DB(storage)
        # ~ compressed_storage = zc.zlibstorage.ZlibStorage(storage)
        # ~ db = ZODB.DB(compressed_storage)
        try:
            connection = db.open()
            root = connection.root
            pms = None
            pm = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            try:
                pm = pms[message.message_id]
            except KeyError:
                pms[message.message_id] = BTrees.OOBTree.OOBTree()
                pm = pms[message.message_id]
            pm.update(message)
            pm['version'] = version
            transaction.commit()
        except Exception as exception:
            transaction.abort()
            await debug_logger(
                u"Message NOT added to database",
                message,
                exception,
                ['log', 'zodb', 'exception'],
            )
            raise
        finally:
            db.close()
    except Exception as exception:
        await exception_logger(
            exception,
            ['log', 'zodb'],
        )

## TODO: Descobrir tipo de update (era types.Message)
async def info_logger(
    update: types.Update,
    descriptions: list = ['none'],
):
    # ~ await zodb_callback(update)
    dispatcher = Dispatcher.get_current()
    bot = dispatcher.bot
    url = ''
    if hasattr(update, 'chat') and update.chat.type != "private":
        # url = update.url
        url = update.link('link', as_html = False)
    text = list()
    text.append(
        u" ".join([
            u" ".join([escape_md("#" + d) for d in descriptions]),
            url,
        ])
    )
    text.append('')
    if update is not None:
        if not isinstance(update, str):
            try:
                text.append(pre(json.dumps(update.to_python(),
                    indent = 2, ensure_ascii = False))
                )
            except AttributeError:
                text.append(pre(json.dumps(update, indent = 2,
                    ensure_ascii = False))
                )
        else:
            text.append(pre(json.dumps(update, indent = 2,
                ensure_ascii = False))
            )
    try:
        ## TelegramTextoTecidoTabelas
        #await tecido_logger(getattr(update, 'text', ''))
        await bot.send_message(
            chat_id = bot.users['special']['info'],
            text = '\n'.join(text),
            disable_notification = True,
            parse_mode = "MarkdownV2",
        )
    except KeyError:
        logging.debug(key_error)
    except Exception as e:
        logging.critical(repr(e))
