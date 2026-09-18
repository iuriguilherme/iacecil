"""
ZODB wrapper for ia.cecil

ia.cecil

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

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

## TODO: Separar funções em módulos (arquivos)

import logging
logger = logging.getLogger(__name__)

import BTrees
import os
import transaction
import uuid
from aiogram import (
    Dispatcher,
)
from ... import (
    commit,
    name,
    version,
)
from ..assertions import assertIsNotNone

zodb_path = 'instance/zodb'

## Per process, not per call: the readers below are shared by the web
## routes and by connector-side plugins, and only the process knows which
## side it is. The web unit turns this on at startup; the connector unit,
## whose plugins write these stores, leaves it off.
read_only = False

async def croak_db(db):
    try:
        db.close()
    except Exception as exception:
        logger.warning(u"Database was already closed: {}".format(repr(
            exception))
        )

async def croak_transaction(transaction):
    try:
        transaction.abort()
    except Exception as exception:
        logger.warning(u"Transaction already aborted: {}".format(repr(
            exception))
        )

async def get_db(path_string, read_only=None):
    """Open one legacy store, or None when reading one that does not exist.

    Legacy data keeps its own per-chat layout, so ZEO never names these
    files as storages (consolidating them is deferred; see the slice 1
    plan's follow-up work). Cross-process sharing relies on read_only
    instead: FileStorage takes its exclusive lock only for a writer, so
    the web unit reads what the connector unit holds open for writing.

    ``read_only`` defaults to this process's setting (the module-level
    flag). A read-only open cannot create a missing file, so a store that
    was never written reads as absent — every reader already treats a
    falsy db as "nothing stored".
    """
    if read_only is None:
        read_only = globals()['read_only']
    if read_only and not os.path.exists(path_string):
        return None
    try:
        from .storage import open_db
        return open_db(path_string, read_only=read_only)
    except Exception as exception:
        logging.warning(repr(exception))
        raise

async def get_messages(chat_id):
    if not await assertIsNotNone([chat_id]):
        return False, False
    from ..aiogram_v3.util import get_aiogram_context
    ctx = get_aiogram_context()
    bot = ctx.get('bot')
    if not bot:
        logger.error("get_messages: No bot found in context")
        return False, False
    try:
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot.id,
            chat_id,
        ))
        if not db:
            return False, False
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return db, pms
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_messages_garimpo(chat_id):
    if not await assertIsNotNone([chat_id]):
        return False, False
    from ..aiogram_v3.util import get_aiogram_context
    ctx = get_aiogram_context()
    bot = ctx.get('bot')
    if not bot:
        logger.error("get_messages_garimpo: No bot found in context")
        return False, False
    try:
        db = await get_db('{}/bots/{}/garimpo/{}.fs'.format(
            zodb_path,
            bot.id,
            chat_id,
        ))
        if not db:
            return False, False
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return db, pms
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_messages_admin(chat_id):
    if not await assertIsNotNone([chat_id]):
        return False, False
    from ..aiogram_v3.util import get_aiogram_context
    ctx = get_aiogram_context()
    bot = ctx.get('bot')
    if not bot:
        logger.error("get_messages_admin: No bot found in context")
        return False, False
    try:
        db = await get_db('{}/bots/{}/admin/{}.fs'.format(
            zodb_path,
            bot.id,
            chat_id,
        ))
        if not db:
            return False, False
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return db, pms
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_bot_messages(bot_id, chat_id):
    if not await assertIsNotNone([bot_id, chat_id]):
        return False, False
    try:
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot_id,
            chat_id,
        ))
        if not db:
            return False, False
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return db, pms
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_messages_texts_list(
    bot_id: str = None,
    chat_id: str = None,
    offset: int = 0,
    limit: int = 0,
):
    if not await assertIsNotNone([bot_id, chat_id, offset, limit]):
        return (0, ['nada'])
    try:
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot_id,
            chat_id,
        ))
        if not db:
            return (0, ['nada'])
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return (
                len(pms),
                [pm.get('text','') for pm in pms.values()][
                    offset:limit:-1],
            )
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return (0, ['nada'])

async def get_messages_list(
    bot_id: str = None,
    chat_id: str = None,
    offset: int = 0,
    limit: int = 0,
):
    if not await assertIsNotNone([bot_id, chat_id, offset, limit]):
        return (0, [{}])
    try:
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot_id,
            chat_id,
        ))
        if not db:
            return (0, [{}])
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return (
                len(pms),
                [{k:v for (k,v) in pm.items()} for pm in pms.values()][
                    offset:limit:-1],
            )
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return (0, [{}])

async def get_aiogram_messages(
    bot_id: str = None,
    chat_id: str = None,
    offset: int = 0,
    limit: int = 0,
):
    if not await assertIsNotNone([bot_id, chat_id]):
        return (0, [{}])
    try:
        logger.debug('3')
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot_id,
            chat_id,
        ))
        if not db:
            return (0, [{}])
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return (len(pms), [{k:v for (k,v) in pm.items()} for pm in \
                pms.values()][::-1][offset:limit])
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return (0, [{}])

async def get_aiogram_messages_texts(
    bot_id: str = None,
    chat_id: str = None,
    offset: int = 0,
    limit: int = None,
):
    if not await assertIsNotNone([bot_id, chat_id]):
        return (0, ['nada'])
    try:
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot_id,
            chat_id,
        ))
        if not db:
            return (0, ['nada'])
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return (len(pms), [pm[item] for pm in pms.values() for item\
                in {k:v for (k,v) in pm.items()} if item == 'text'][
                ::-1][offset:limit]
            )
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return (0, ['nada'])

async def get_bot_files(bot_id):
    if not await assertIsNotNone([bot_id]):
        return False, False
    try:
        db = await get_db('{}/bots/{}/files.fs'.format(
            zodb_path,
            bot_id,
        ))
        if not db:
            return False, False
        try:
            connection = db.open()
            root = connection.root
            files = None
            try:
                files = root.files
            except AttributeError:
                root.files = BTrees.OOBTree.OOBTree()
                files = root.files
            return db, files
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_file_id_by_reference(bot_id, reference):
    if not await assertIsNotNone([bot_id, reference]):
        return False
    try:
        db = await get_db('{}/bots/{}/files.fs'.format(
            zodb_path,
            bot_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            files = None
            try:
                files = root.files
            except AttributeError:
                return False
            _file = None
            try:
                _file = [files[__file] for __file in files if \
                    files[__file]['reference'] == reference
                ][0]
            except IndexError:
                return False
            except Exception as e2:
                logger.warning(repr(e2))
                raise
            finally:
                await croak_db(db)
            file_id = _file['file_id']
            return file_id
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def set_file(bot_id, file_unique_id, file_id, reference):
    if not await assertIsNotNone([bot_id, file_unique_id, file_id, 
        reference]):
        return False
    try:
        db = await get_db('{}/bots/{}/files.fs'.format(
            zodb_path,
            bot_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            files = None
            try:
                files = root.files
            except AttributeError:
                root.files = BTrees.OOBTree.OOBTree()
                files = root.files
            file_ = None
            try:
                if len([files[file_] for file_ in files if \
                    file_ == file_unique_id]
                ) > 0:
                    ## file is already on database, doing nothing
                    return True
            except IndexError:
                try:
                    files[file_unique_id] = BTrees.OOBTree.OOBTree()
                    file_ = files[file_unique_id]
                    file_['file_unique_id'] = file_unique_id
                    file_['file_id'] = file_id
                    file_['reference'] = reference
                    file_[name] = {
                        'version': version,
                        'commit': commit,
                        'plugin': 'aiogram',
                    }
                    transaction.commit()
                except Exception as e2:
                    await croak_transaction(transaction)
                    logger.warning(repr(e2))
                    raise
                finally:
                    await croak_db(db)
                return True
            except Exception as e2:
                logger.warning(repr(e2))
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def log_message(message):
    if not await assertIsNotNone([message]):
        return False
    from ..aiogram_v3.util import get_aiogram_context
    ctx = get_aiogram_context()
    bot = ctx.get('bot')
    if not bot:
        logger.error("log_message: No bot found in context")
        return False
    try:
        db = await get_db('{}/bots/{}/chats/{}.fs'.format(
            zodb_path,
            bot.id,
            message.chat.id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            pm = None
            try:
                pm = pms[message.message_id]
                logger.info(u"Message already on database, skipping...")
                return False
            except KeyError:
                try:
                    pms[message.message_id] = BTrees.OOBTree.OOBTree()
                    pm = pms[message.message_id]
                    pm.update(message)
                    pm[name] = {
                        'version': version,
                        'commit': commit,
                        'plugin': 'aiogram',
                    }
                    transaction.commit()
                    return True
                except Exception as e2:
                    await croak_transaction(transaction)
                    logger.warning(repr(e2))
                    raise
                finally:
                    await croak_db(db)
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return False

async def get_furhat_texts_messages(
    furhat_id: str = None,
    session_id: str = None,
):
    if not await assertIsNotNone([
        furhat_id,
        session_id,
    ]):
        return []
    try:
        db = await get_db('{}/furhats/{}/sessions/{}.fs'.format(
            zodb_path,
            furhat_id,
            session_id,
        ))
        if not db:
            return []
        try:
            connection = db.open()
            root = connection.root
            texts = None
            try:
                texts = root.texts
            except AttributeError:
                root.texts = BTrees.OOBTree.OOBTree()
                texts = root.texts
            try:
                return [texts[text]['message'] for text in texts][::-1]
            except IndexError:
                return []
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return []

async def set_furhat_text(
    furhat_id: str = None,
    session_id: str = None,
    furhat_text: object = None,
):
    if not await assertIsNotNone([
        furhat_id,
        session_id,
        furhat_text,
    ]):
        return False
    try:
        db = await get_db('{}/furhats/{}/sessions/{}.fs'.format(
            zodb_path,
            furhat_id,
            session_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            texts = None
            try:
                texts = root.texts
            except AttributeError:
                root.texts = BTrees.OOBTree.OOBTree()
                texts = root.texts
            try:
                text_id = uuid.uuid4()
                texts[text_id] = BTrees.OOBTree.OOBTree()
                text = texts[text_id]
                text['success'] = furhat_text.success
                text['message'] = furhat_text.message
                text[name] = {
                    'version': version,
                    'commit': commit,
                    'plugin': 'furhat',
                }
                transaction.commit()
                return True
            except Exception as e2:
                await croak_transaction(transaction)
                logger.warning(repr(e2))
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.warning(repr(e1))
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return False

## tc
async def get_tc_data(bot_id, user_id):
    if not await assertIsNotNone([bot_id, user_id]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/{}.fs'.format(
            zodb_path,
            bot_id,
            user_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            data = None
            try:
                data = root.data
            except AttributeError:
                root.data = BTrees.OOBTree.OOBTree()
                data = root.data
            return {k:v for (k,v) in data.items()}
        except Exception as e1:
            logger.exception(e1)
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_ts_rolls(bot_id, user_id):
    if not await assertIsNotNone([bot_id, user_id]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/{}.fs'.format(
            zodb_path,
            bot_id,
            user_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            rolls = None
            try:
                rolls = root.rolls
            except AttributeError:
                try:
                    root.rolls = BTrees.IIBTree.IIBTree()
                    rolls = root.rolls
                    rolls[0] = 0
                    transaction.commit()
                except Exception as e3:
                    logger.exception(e3)
                    await croak_transaction(transaction)
                    raise
            try:
                return sorted(rolls.items(), key = lambda i: i[0])
            except Exception as e2:
                logger.exception(e2)
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.exception(e1)
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.exception(exception)
        raise

async def get_tc_levels(bot_id, user_id):
    if not await assertIsNotNone([bot_id, user_id]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/{}.fs'.format(
            zodb_path,
            bot_id,
            user_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            levels = None
            try:
                levels = root.levels
            except AttributeError:
                try:
                    root.levels = BTrees.IIBTree.IIBTree()
                    levels = root.levels
                    levels[0] = 0
                    transaction.commit()
                except Exception as e3:
                    logger.exception(e3)
                    await croak_transaction(transaction)
                    raise
            try:
                return sorted(levels.items(), key = lambda i: i[0])
            except Exception as e2:
                logger.exception(e2)
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.exception(e1)
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.exception(exception)
        raise

async def set_tc_roll(bot_id, user_id, roll):
    if not await assertIsNotNone([bot_id, user_id, roll]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/{}.fs'.format(
            zodb_path,
            bot_id,
            user_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            rolls = None
            try:
                rolls = root.rolls
            except AttributeError:
                try:
                    root.rolls = BTrees.IIBTree.IIBTree()
                    rolls = root.rolls
                    rolls[0] = 0
                    transaction.commit()
                except Exception as e3:
                    logger.exception(e3)
                    await croak_transaction(transaction)
                    raise
            try:
                rolls[len(rolls)] = roll
                transaction.commit()
                return True
            except Exception as e2:
                await croak_transaction(transaction)
                logger.exception(e2)
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.exception(e1)
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.exception(exception)
        raise
    return False

async def set_tc_level(bot_id, user_id, level):
    if not await assertIsNotNone([bot_id, user_id, level]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/{}.fs'.format(
            zodb_path,
            bot_id,
            user_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            levels = None
            try:
                levels = root.levels
            except AttributeError:
                try:
                    root.levels = BTrees.IIBTree.IIBTree()
                    levels = root.levels
                    levels[0] = 0
                    transaction.commit()
                except Exception as e3:
                    logger.exception(e3)
                    await croak_transaction(transaction)
                    raise
            try:
                levels[len(levels)] = level
                transaction.commit()
                return True
            except Exception as e2:
                await croak_transaction(transaction)
                logger.exception(e2)
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.exception(e1)
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.exception(exception)
        raise
    return False

async def get_tc_prizes(bot_id):
    if not await assertIsNotNone([bot_id]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/metadata.fs'.format(
            zodb_path,
            bot_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            prizes = None
            try:
                prizes = root.prizes
            except AttributeError:
                root.prizes = BTrees.IIBTree.IIBTree()
                prizes = root.prizes
            return set(prizes.values())
        except Exception as e1:
            logger.exception(e1)
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.exception(exception)
        raise

async def set_tc_prize(bot_id, prize):
    if not await assertIsNotNone([bot_id, prize]):
        return False
    try:
        db = await get_db('{}/bots/{}/tc/metadata.fs'.format(
            zodb_path,
            bot_id,
        ))
        if not db:
            return False
        try:
            connection = db.open()
            root = connection.root
            prizes = None
            try:
                prizes = root.prizes
            except AttributeError:
                root.prizes = BTrees.IIBTree.IIBTree()
                prizes = root.prizes
            try:
                prizes[len(prizes)] = prize
                transaction.commit()
                return True
            except Exception as e2:
                await croak_transaction(transaction)
                logger.exception(e2)
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.exception(e1)
            raise
        finally:
            await croak_db(db)
    except Exception as exception:
        logger.exception(exception)
        raise
    return False
