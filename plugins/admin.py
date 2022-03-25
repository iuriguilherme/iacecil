# vim:fileencoding=utf-8
#  Plugin admin para ia.cecil: Plugin para administração e testes
#  Copyleft (C) 2018-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

import BTrees, datetime, glob, json, os, pytz, transaction, uuid, ZODB
from datetime import timedelta
from tempfile import gettempdir
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from aiogram.utils.markdown import code, pre
from iacecil import (
    commit,
    name,
    version,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
    exception_callback,
)
from iacecil.controllers.persistence.zodb_orm import (
    get_aiogram_messages,
    get_aiogram_messages_texts,
    get_messages,
    get_messages_texts_list,
    get_messages_admin,
)

## TODO migrar para aiogram - este código era do telepot
## Testar timezone do servidor
def cmd_tz(args):
    testetz_timezone = pytz.timezone('America/Sao_Paulo')
    testetz_format = '%Y-%m-%d %H:%M:%S'

    response = list()
    response.append(u'Timezone: %s, %s' % (str(testetz_timezone), testetz_timezone.zone))
    response.append(u'datetime.now(): %s' % (str(datetime.datetime.now())))
    response.append(u'datetime.now(testetz_timezone): %s' % (str(datetime.datetime.now(testetz_timezone))))
    response.append(u'(datetime.datetime.now(testetz_timezone()) - datetime.timedelta(days=2)).strftime(db_datetime()): %s' % ((datetime.datetime.now(testetz_timezone) - datetime.timedelta(days=2)).strftime(testetz_format)))
    response.append(u'(datetime.datetime.now(testetz_timezone()) - datetime.timedelta(minutes=5)).strftime(db_datetime()): %s' % ((datetime.datetime.now(testetz_timezone) - datetime.timedelta(minutes=5)).strftime(testetz_format)))
    response.append(u'(datetime.datetime.now(testetz_timezone()) - datetime.timedelta(days=2)).strftime(db_datetime()): %s' % ((datetime.datetime.now(testetz_timezone) - datetime.timedelta(days=2)).strftime(testetz_format)))
    return {
        'status': True,
        'type': args['command_type'],
        'response': '\n'.join(response),
        'debug': u'testetz: %s' % (response),
        'multi': False,
        'parse_mode': None,
    }

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Testar o bot. Ecoa o texto enviado ou produz um erro se não
        ## tiver nenhum argumento.
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['teste', 'test'],
        )
        async def test_callback(message):
            await message_callback(message, ['test', message.chat.type])
            command = await message.reply(message.get_args())
            await command_callback(command, ['test', message.chat.type])

        ## Enviar mensagem para alguém através do bot
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['enviar', 'send']
        )
        async def send_callback(message):
            await message_callback(message, ['send', message.chat.type])
            args = message.get_args().split(' ')
            command = await dispatcher.bot.send_message(
                chat_id = args[0],
                text = ' '.join(args[1::1]),
            )
            await command_callback(command, ['send', message.chat.type])

        ## Responder uma mensagem através do bot
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['responder', 'reply']
        )
        async def reply_callback(message):
            await message_callback(message, ['reply',
                message.chat.type])
            args = message.get_args().split(' ')
            command = await dispatcher.bot.send_message(
                chat_id = str(args[0]),
                text = ' '.join(args[2::1]),
                reply_to_message_id = int(args[1]),
                allow_sending_without_reply = True,
            )
            await command_callback(command, ['reply',
                message.chat.type])

        ## Lista de comandos reservados para dev/admin
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['admin'],
        )
        async def admin_callback(message):
            await message_callback(message, ['admin',
                message.chat.type])
            lista = list()
            lista.append(u"""/enviar <chat_id> <texto>: Enviar "texto" \
para "chat_id".""")
            lista.append(u"""/responder <chat_id> <message_id> <texto>:\
 Responder "message_id" em "chat_id" com "texto".""")
            lista.append(u"""/tz: Teste de timezone do servidor.""")
            command = await message.reply(u"""Lista de comandos reserva\
dos para dev/admin:\n{lista}""".format(lista = "\n".join(lista)))
            await command_callback(command, ['admin',
                message.chat.type])

        ## Teste de timezone do servidor
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
                chat_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['tz', 'timezone'],
        )
        async def tz_callback(message):
            await message_callback(message, ['tz', message.chat.type])
            ## lol
            command = await message.reply(code(u"{}".format(cmd_tz(
                {'command_type': None})['response'])),
                parse_mode = "MarkdownV2",
            )
            await command_callback(command, ['tz', message.chat.type])

        ## ZODB
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['gravar', 'record'],
        )
        async def persistence_write_callback(message):
            db = None
            try:
                db, pms = await get_messages_admin(message.chat.id)
                try:
                    try:
                        pm = pms[message.message_id]
                    except KeyError:
                        pms[message.message_id
                            ] = BTrees.OOBTree.OOBTree()
                        pm = pms[message.message_id]
                    pm.update(message)
                    pm[name + '_version'] = version
                    pm[name + '_commit'] = commit
                    transaction.commit()
                    await message.reply(u"ok")
                except Exception as e3:
                    transaction.abort()
                    await error_callback(
                        u"Message NOT added to database",
                        message,
                        e3,
                        ['admin', 'write', 'zodb', 'exception'],
                    )
                finally:
                    try:
                        db.close()
                    except Exception as e2:
                        logger.warning(
                            u"db was never created on {}: {}".format(
                            __name__,
                            repr(e2),
                        ))
            except Exception as exception:
                await exception_callback(
                    exception,
                    ['admin', 'write', 'zodb'],
                )
            finally:
                try:
                    db.close()
                except Exception as e1:
                    logger.warning(
                        u"db was never created on {}: {}".format(
                        __name__,
                        repr(e1),
                    ))

        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['recuperar', 'retrieve'],
        )
        async def persistence_read_callback(message):
            db = None
            try:
                db, pms = await get_messages_admin(message.chat.id)
                try:
                    await message.reply('\n'.join([
                        pre(json.dumps({k:v for (k,v) in pm.items()},
                        indent = 2,
                        ensure_ascii = False,
                        )) for pm in pms.values()
                    ]), parse_mode = "MarkdownV2")
                except Exception as e3:
                    await error_callback(
                        u"Message NOT retrieved from database",
                        message,
                        e3,
                        ['admin', 'retrieve', 'zodb', 'exception'],
                    )
                finally:
                    try:
                        db.close()
                    except Exception as e2:
                        logger.warning(
                            u"db was never created on {}: {}".format(
                            __name__,
                            repr(e2),
                        ))
            except Exception as exception:
                await exception_callback(
                    exception,
                    ['admin', 'retrieve', 'zodb'],
                )
            finally:
                try:
                    db.close()
                except Exception as e1:
                    logger.warning(
                        u"db was never created on {}: {}".format(
                        __name__,
                        repr(e1),
                    ))

        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['count'],
        )
        async def persistence_count_callback(message):
            db = None
            try:
                if message.get_args() != '':
                    db, pms = await get_messages(message.get_args())
                else:
                    db, pms = await get_messages(message.chat.id)
                try:
                    await message.reply(len(pms))
                except Exception as e3:
                    await error_callback(
                        u"Message NOT retrieved from database",
                        message,
                        e3,
                        ['admin', 'count', 'zodb', 'exception'],
                    )
                finally:
                    try:
                        db.close()
                    except Exception as e2:
                        logger.warning(
                            u"db was never created on {}: {}".format(
                            __name__,
                            repr(e2),
                        ))
            except Exception as exception:
                await exception_callback(
                    exception,
                    ['admin', 'count', 'zodb'],
                )
            finally:
                try:
                    db.close()
                except Exception as e1:
                    logger.warning(
                        u"db was never created on {}: {}".format(
                        __name__,
                        repr(e1),
                    ))
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['find']
        )
        async def find_callback(message):
            await message_callback(message, ['admin', 'zodb',
                'find', message.chat.type]
            )
            word = None
            command = None
            if message.chat.type not in ['group', 'supergroup']:
                command = await message.reply(
                    u"Comando só funciona em grupos"
                )
            else:
                if len(message.get_args()) > 0:
                    word = message.get_args()
                if word is not None:
                    messages = await get_aiogram_messages(
                        bot_id = dispatcher.bot.id,
                        chat_id = message.chat.id,
                        offset = 0,
                        limit = None,
                    )
                    links = list()
                    for message_ in messages[1]:
                        if word in message_.get('text', ''):
                            url = 'https://t.me/'
                            if message_.get('username', None
                                ) is not None:
                                url += f"{message_['username']}/"
                            else:
                                url += \
                                f"c/{str(message_['chat']['id'])[4:]}/"
                            url += f"{message_['message_id']}"
                            links.append(url)
                    command = await message.reply(
                        u"Encontrei '{}' nestas mensagens:".format(word)
                    )
                    command = await message.reply('\n'.join(links))
                    await command_callback(command, ['admin', 'zodb',
                        'find', message.chat.type]
                    )

        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                        'users']['beta'],
            ),
            commands = ['dump'],
        )
        async def persistence_dump_callback(message):
            db = None
            try:
                if message.get_args() != '':
                    db, pms = await get_messages(message.get_args())
                else:
                    db, pms = await get_messages(message.chat.id)
                try:
                    await message.reply('\n'.join([
                        pre(json.dumps({k:v for (k,v) in pm.items()},
                        indent = 2,
                        ensure_ascii = False,
                        )) for pm in pms.values()
                    ]), parse_mode = "MarkdownV2")
                except Exception as e3:
                    await error_callback(
                        u"Message NOT retrieved from database",
                        message,
                        e3,
                        ['admin', 'dump', 'zodb', 'exception'],
                    )
                finally:
                    try:
                        db.close()
                    except Exception as e2:
                        logger.warning(
                            u"db was never created on {}: {}".format(
                            __name__,
                            repr(e2),
                        ))
            except Exception as exception:
                await exception_callback(
                    exception,
                    ['admin', 'dump', 'zodb'],
                )
            finally:
                try:
                    db.close()
                except Exception as e1:
                    logger.warning(
                        u"db was never created on {}: {}".format(
                        __name__,
                        repr(e1),
                    ))

        ## Enviar sticker para alguém através do bot
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.bot.config['telegram']['users'][
                    'alpha'] + dispatcher.bot.config['telegram'][
                    'users']['beta'],
            ),
            commands = ['sticker']
        )
        async def sticker_callback(message):
            await message_callback(message, ['admin', 'sticker',
                message.chat.type]
            )
            args = message.get_args().split(' ')
            command = await dispatcher.bot.send_sticker(
                chat_id = args[0],
                sticker = ' '.join(args[1::1]),
            )
            await command_callback(command, ['admin', 'sticker',
                message.chat.type]
            )
    except Exception as exception:
        raise
