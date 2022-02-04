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

import BTrees, transaction, zc.zlibstorage, ZODB, ZODB.FileStorage
from aiogram import (
    Dispatcher,
)

async def get_messages(chat_id):
    if chat_id is not None:
        dispatcher = Dispatcher.get_current()
        try:
            storage = ZODB.FileStorage.FileStorage(
                'instance/zodb/{}.{}.fs'.format(
                dispatcher.bot.id,
                chat_id,
            ))
            compressed_storage = zc.zlibstorage.ZlibStorage(storage)
            db = ZODB.DB(compressed_storage)
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
            except:
                raise
        except:
            raise
    else:
        return False, False

async def get_bot_messages(bot_id, chat_id):
    if bot_id is not None and chat_id is not None:
        try:
            storage = ZODB.FileStorage.FileStorage(
                'instance/zodb/{}.{}.fs'.format(
                bot_id,
                chat_id,
            ))
            compressed_storage = zc.zlibstorage.ZlibStorage(storage)
            db = ZODB.DB(compressed_storage)
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
            except:
                raise
        except:
            raise
    else:
        return False, False
