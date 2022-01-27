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

import copy, datetime, json, logging, pytz, ZODB, ZODB.FileStorage, \
    BTrees, transaction, persistent.mapping
# ~ import zc.zlibstorage
from aiogram import (
    Dispatcher,
    filters,
)
from aiogram.utils.markdown import code, pre
from iacecil import (
    name,
    version,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
    exception_callback,
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
    ## Testar o bot. Ecoa o texto enviado ou produz um erro se não
    ## tiver nenhum argumento.
    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
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
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
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
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
        ),
        commands = ['responder', 'reply']
    )
    async def reply_callback(message):
        await message_callback(message, ['reply', message.chat.type])
        args = message.get_args().split(' ')
        command = await dispatcher.bot.send_message(
            chat_id = str(args[0]),
            text = ' '.join(args[2::1]),
            reply_to_message_id = int(args[1]),
            allow_sending_without_reply = True,
        )
        await command_callback(command, ['reply', message.chat.type])

    ## Lista de comandos reservados para dev/admin
    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
        ),
        commands = ['admin'],
    )
    async def admin_callback(message):
        await message_callback(message, ['admin', message.chat.type])
        lista = list()
        lista.append(u"""/enviar <chat_id> <texto>: Enviar "texto" para\
"chat_id".""")
        lista.append(u"""/responder <chat_id> <message_id> <texto>: Res\
ponder "message_id" em "chat_id" com "texto".""")
        lista.append(u"""/tz: Teste de timezone do servidor.""")
        command = await message.reply(u"""Lista de comandos reservados \
para dev/admin:\n{lista}""".format(lista = "\n".join(lista)))
        await command_callback(command, ['admin', message.chat.type])

    ## Teste de timezone do servidor
    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
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

    ## Persistence
    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
        ),
        commands = ['gravar', 'record'],
    )
    async def persistence_write_callback(message):
        dispatcher = Dispatcher.get_current()
        try:
            storage = ZODB.FileStorage.FileStorage(
                'instance/zodb/{}.{}.admin.fs'.format(
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
                await error_callback(
                    u"Message NOT added to database",
                    message,
                    exception,
                    ['admin', 'write', 'zodb', 'exception'],
                )
            finally:
                db.close()
        except Exception as exception:
            await exception_callback(
                exception,
                ['admin', 'write', 'zodb'],
            )

    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
        ),
        commands = ['recuperar', 'retrieve'],
    )
    async def persistence_read_callback(message):
        dispatcher = Dispatcher.get_current()
        try:
            storage = ZODB.FileStorage.FileStorage(
                'instance/zodb/{}.{}.admin.fs'.format(
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
                await message.reply('\n'.join([
                    pre(json.dumps({k:v for (k,v) in pm.items()},
                    indent = 2,
                    ensure_ascii = False,
                    )) for pm in pms.values()
                ]), parse_mode = "MarkdownV2")
            except Exception as exception:
                await error_callback(
                    u"Message NOT retrieved from database",
                    message,
                    exception,
                    ['admin', 'retrieve', 'zodb', 'exception'],
                )
            finally:
                db.close()
        except Exception as exception:
            await exception_callback(
                exception,
                ['admin', 'retrieve', 'zodb'],
            )

    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
        ),
        commands = ['count'],
    )
    async def persistence_count_callback(message):
        dispatcher = Dispatcher.get_current()
        try:
            chat_id = message.get_args()
            storage = ZODB.FileStorage.FileStorage(
                'instance/zodb/{}.{}.fs'.format(
                dispatcher.bot.id,
                chat_id,
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
                await message.reply(len(pms))
            except Exception as exception:
                await error_callback(
                    u"Message NOT retrieved from database",
                    message,
                    exception,
                    ['admin', 'count', 'zodb', 'exception'],
                )
            finally:
                db.close()
        except IndexError:
            await message.reply(u"which chat?")
        except Exception as exception:
            await exception_callback(
                exception,
                ['admin', 'count', 'zodb'],
            )

    @dispatcher.message_handler(
        filters.IDFilter(
            user_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
            chat_id = dispatcher.bot.users['alpha'] + \
                dispatcher.bot.users['beta'],
        ),
        commands = ['dump'],
    )
    async def persistence_dump_callback(message):
        dispatcher = Dispatcher.get_current()
        try:
            chat_id = message.get_args()
            storage = ZODB.FileStorage.FileStorage(
                'instance/zodb/{}.{}.fs'.format(
                dispatcher.bot.id,
                chat_id,
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
                await message.reply('\n'.join([
                    pre(json.dumps({k:v for (k,v) in pm.items()},
                    indent = 2,
                    ensure_ascii = False,
                    )) for pm in pms.values()
                ]), parse_mode = "MarkdownV2")
            except Exception as exception:
                await error_callback(
                    u"Message NOT retrieved from database",
                    message,
                    exception,
                    ['admin', 'dump', 'zodb', 'exception'],
                )
            finally:
                db.close()
        except IndexError:
            await message.reply(u"which chat?")
        except Exception as exception:
            await exception_callback(
                exception,
                ['admin', 'dump', 'zodb'],
            )
