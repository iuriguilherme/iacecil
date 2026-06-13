"""Per-connector, per-chat message storage.

Replaces the telegram-only legacy scheme
(``instance/zodb/bots/<numeric bot id>/chats/<chat id>.fs``, pickled
aiogram objects) with a platform-neutral one:

    instance/zodb/bots/<bot_id>/<connector>/chats/<chat_id>.fs

Components are sanitized via path_utils (filesystem-safe on
HFS+/NTFS/ext4/btrfs); records are normalized dicts — never live
platform objects. Legacy data stays readable through zodb_orm.
"""

import logging
import os
import time
import uuid
from collections import OrderedDict

import BTrees
import zc.zlibstorage
import ZODB
import ZODB.FileStorage

from .path_utils import sanitize_component

logger = logging.getLogger(__name__)

## Module globals so the test isolation fixture can repoint storage.
zodb_path = 'instance/zodb'

## One FileStorage per chat per connector adds up on busy bots; keep a
## bounded LRU of open handles (the legacy path opened/closed per call;
## this trades a small cache for hot-chat performance without unbounded
## fd growth).
MAX_OPEN_DBS = 32

_dbs = OrderedDict()


def close_all() -> None:
    """Close every cached DB handle (test teardown)."""
    while _dbs:
        _, db = _dbs.popitem(last=False)
        try:
            db.close()
        except Exception:
            pass


def _chat_db_path(bot_id, connector, chat_id) -> str:
    base = os.path.abspath(zodb_path)
    path = os.path.abspath(os.path.join(
        base, 'bots',
        sanitize_component(bot_id),
        sanitize_component(connector),
        'chats',
        sanitize_component(chat_id) + '.fs',
    ))
    ## Belt-and-braces: even a sanitizer regression or a
    ## traversal-shaped component must never escape the zodb base.
    if not path.startswith(base + os.sep):
        raise ValueError(f"Chat store path escapes zodb base: {path}")
    return path


def _get_db(path: str):
    db = _dbs.pop(path, None)
    if db is None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        storage = ZODB.FileStorage.FileStorage(path)
        db = ZODB.DB(zc.zlibstorage.ZlibStorage(storage))
    _dbs[path] = db
    while len(_dbs) > MAX_OPEN_DBS:
        old_path, old_db = _dbs.popitem(last=False)
        try:
            old_db.close()
        except Exception as e:
            ## A failed close leaves the FileStorage .lock behind;
            ## surface it instead of masking.
            logger.warning(f"Failed to close evicted chat DB {old_path}: {e}")
    return db


async def store_message(bot_id: str, envelope, direction: str = 'in'):
    """Store one normalized message record in its chat's database.

    Returns the record id, or None when the message deduplicated away.
    Dedupe applies only when the platform supplied a native message id;
    records without one (outbound replies, loopback) always store.
    """
    path = _chat_db_path(bot_id, envelope.platform,
        envelope.conversation_ref)
    db = _get_db(path)
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'messages'):
            root.messages = BTrees.OOBTree.OOBTree()
        native_id = getattr(envelope, 'native_message_id', None)
        if native_id is not None:
            if not hasattr(root, 'native_ids'):
                root.native_ids = BTrees.OOBTree.TreeSet()
            if native_id in root.native_ids:
                logger.debug(
                    f"Message {native_id} already stored, skipping...")
                return None
            root.native_ids.add(native_id)

        record = {
            'connector': envelope.platform,
            'sender_ref': envelope.sender_ref,
            'conversation_ref': envelope.conversation_ref,
            'text': envelope.text,
            'reply_ref': envelope.reply_ref,
            'tags': list(envelope.tags),
            'direction': direction,
            'native_message_id': native_id,
            'person_id': getattr(envelope, 'person_id', None),
            'timestamp': getattr(envelope, 'timestamp', None) or time.time(),
        }
        msg_id = str(uuid.uuid4())
        root.messages[msg_id] = record
        return msg_id
