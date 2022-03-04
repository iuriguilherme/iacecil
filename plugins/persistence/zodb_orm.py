# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import logging
logger = logging.getLogger(__name__)

import BTrees, os, transaction, zc.zlibstorage, ZODB, ZODB.FileStorage
from aiogram import (
    Dispatcher,
)
from iacecil import (
    commit,
    name,
    version,
)
from iacecil.controllers.assertions import assertIsNotNone

db_path = 'instance/zodb/bots'

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

async def get_db(path_string):
    try:
        try:
            storage = ZODB.FileStorage.FileStorage(path_string)
        except FileNotFoundError:
            os.makedirs(os.path.dirname(path_string))
            storage = ZODB.FileStorage.FileStorage(path_string)
        compressed_storage = zc.zlibstorage.ZlibStorage(storage)
        db = ZODB.DB(compressed_storage)
        return db
    except Exception as exception:
        logging.warning(repr(exception))
        raise
    return None

async def get_messages(chat_id):
    if not await assertIsNotNone([chat_id]):
        return False, False
    dispatcher = Dispatcher.get_current()
    try:
        db = await get_db('{}/{}/chats/{}.fs'.format(
            db_path,
            dispatcher.bot.id,
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
    dispatcher = Dispatcher.get_current()
    try:
        db = await get_db('{}/{}/garimpo/{}.fs'.format(
            db_path,
            dispatcher.bot.id,
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
    dispatcher = Dispatcher.get_current()
    try:
        db = await get_db('{}/{}/admin/{}.fs'.format(
            db_path,
            dispatcher.bot.id,
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
        db = await get_db('{}/{}/chats/{}.fs'.format(
            db_path,
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


async def get_messages_texts_list(bot_id, chat_id):
    if not await assertIsNotNone([bot_id, chat_id]):
        return ['nada']
    try:
        db = await get_db('{}/{}/chats/{}.fs'.format(
            db_path,
            bot_id,
            chat_id,
        ))
        if not db:
            return ['nada']
        try:
            connection = db.open()
            root = connection.root
            pms = None
            try:
                pms = root.messages
            except AttributeError:
                root.messages = BTrees.IOBTree.IOBTree()
                pms = root.messages
            return ['nada']
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def get_bot_files(bot_id):
    if not await assertIsNotNone([bot_id]):
        return False, False
    try:
        db = await get_db('{}/{}/files.fs'.format(
            db_path,
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
        db = await get_db('{}/{}/files.fs'.format(
            db_path,
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
                await croak_db(db)
                return False
            except Exception as e2:
                logger.warning(repr(e2))
                raise
            file_id = _file['file_id']
            await croak_db(db)
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
        db = await get_db('{}/{}/files.fs'.format(
            db_path,
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
            _file = None
            try:
                _file = [files[__file] for __file in \
                    files if files[__file]['reference'] == reference
                ][0]
                if _file:
                    ## file is already on database, doing nothing
                    return True
            except IndexError:
                try:
                    files[file_unique_id] = BTrees.OOBTree.OOBTree()
                    _file = files[file_unique_id]
                    _file['file_unique_id'] = file_unique_id
                    _file['file_id'] = file_id
                    _file['reference'] = reference
                    _file[name + '_version'] = version
                    _file[name + '_commit'] = commit
                    transaction.commit()
                except Exception as e2:
                    await croak_transaction(transaction)
                    logger.warning(repr(e2))
                    raise
                return True
            except Exception as e2:
                logger.warning(repr(e2))
                raise
            finally:
                await croak_db(db)
        except Exception as e1:
            logger.warning(repr(e1))
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def log_message(message):
    if not await assertIsNotNone([message]):
        return False
    dispatcher = Dispatcher.get_current()
    try:
        db = await get_db('{}/{}/chats/{}.fs'.format(
            db_path,
            dispatcher.bot.id,
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
                    pm[name + '_version'] = version
                    pm[name + '_commit'] = commit
                    transaction.commit()
                    return True
                except Exception as e2:
                    croak_transaction(transaction)
                    logger.warning(repr(e2))
                    raise
                finally:
                    croak_db(db)
        except Exception as e1:
            logger.warning(repr(e1))
            await croak_db(db)
            raise
    except Exception as exception:
        logger.warning(repr(exception))
        raise
    return False
