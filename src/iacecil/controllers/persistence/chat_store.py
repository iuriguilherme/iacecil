"""Per-connector, per-chat message storage.

Replaces the telegram-only legacy scheme
(``instance/zodb/bots/<numeric bot id>/chats/<chat id>.fs``, pickled
aiogram objects) with a platform-neutral one: one storage per bot,

    instance/zodb/bots/<bot_id>/chats.fs

holding every chat of that bot under a ``<connector>/<chat_id>`` key.
One storage per chat was the earlier layout; ZEO serves only the
storages its config names at startup, while chats appear at runtime, so
the set of storages has to stay fixed (see R13 in
docs/plans/completed/2026-06-24-001-refactor-decouple-web-survival-slice1-plan.md).

Key components are sanitized via path_utils (filesystem-safe on
HFS+/NTFS/ext4/btrfs, and keys stay comparable); records are normalized
dicts — never live platform objects. Legacy data stays readable through
zodb_orm.
"""

import asyncio
import logging
import os
import threading
import time
import uuid
from collections import OrderedDict

import BTrees

from . import storage
from .path_utils import sanitize_component
from .retry import commit_with_retry

logger = logging.getLogger(__name__)

## Module globals so the test isolation fixture can repoint storage.
zodb_path = 'instance/zodb'

## One storage per bot now, so the LRU bounds open bots rather than open
## chats; keep it anyway for hosts running many bots from one process.
MAX_OPEN_DBS = 32

_dbs = OrderedDict()

## store_message runs its body via asyncio.to_thread, so the LRU and the
## FileStorage open it guards are reached from worker threads. Serialize
## them: without this, two concurrent cache misses for the same path both
## open the same .fs and the second collides on the FileStorage .lock.
_dbs_lock = threading.Lock()


def close_all() -> None:
    """Close every cached DB handle (test teardown)."""
    with _dbs_lock:
        while _dbs:
            _, db = _dbs.popitem(last=False)
            try:
                db.close()
            except Exception:
                pass


def _chat_key(connector, chat_id) -> str:
    """Key one chat inside its bot storage.

    Same sanitizer as the old path components, so a key never carries a
    separator of its own and two chats can never collide.
    """
    return '{}/{}'.format(
        sanitize_component(connector), sanitize_component(chat_id))


def _storage_name(bot_id) -> str:
    """Name the ZEO server serves this bot's chats under. Fixed at
    server startup: one per configured bot, never minted per chat."""
    return storage.storage_name_for_bot(bot_id)


def chat_db_path(bot_id, base_path=None) -> str:
    """Where one bot's chats live on disk.

    The single owner of this layout: the storage server derives the
    same path for the storage it serves under `chats_<bot_id>`, and a
    second copy of the join would drift on the sanitizer (a bot id with
    an uppercase letter or an `@` encodes to a different directory).
    """
    base = os.path.abspath(base_path or zodb_path)
    path = os.path.abspath(os.path.join(
        base, 'bots',
        sanitize_component(bot_id),
        'chats.fs',
    ))
    ## Belt-and-braces: even a sanitizer regression or a
    ## traversal-shaped component must never escape the zodb base.
    if not path.startswith(base + os.sep):
        raise ValueError(f"Chat store path escapes zodb base: {path}")
    return path


def _init_root(db) -> None:
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'chats'):
            root.chats = BTrees.OOBTree.OOBTree()


def _chat_container(root, key: str):
    """Return the per-chat container for ``key``, creating it if absent.

    The container holds this chat's records and its native-id set, so
    dedupe stays per chat exactly as it was when each chat owned a file.
    An OOBTree, not a persistent class: BTree inserts are the operation
    ZODB resolves, so concurrent writers to one chat never conflict on
    the container itself.

    Creation happens here, inside the transaction _store_message_sync
    retries: two writers whose chat is new both see the key absent, the
    loser gets a ConflictError on commit, and its retry finds the
    winner's container instead of replacing it (which would drop the
    winner's message).
    """
    chat = root.chats.get(key)
    if chat is None:
        chat = BTrees.OOBTree.OOBTree()
        chat['messages'] = BTrees.OOBTree.OOBTree()
        chat['native_ids'] = BTrees.OOBTree.TreeSet()
        root.chats[key] = chat
    return chat


def _get_db(path: str, storage_name=None):
    ## Serialize cache lookup, storage open, and eviction so concurrent
    ## worker threads cannot double-open the same .fs.
    with _dbs_lock:
        db = _dbs.pop(path, None)
        if db is None:
            db = storage.open_db(path, storage_name)
            ## Create the root container once, here under the lock, so
            ## concurrent writers never race to replace a root attribute
            ## (unresolvable); they then only do OOBTree/TreeSet inserts,
            ## which ZODB resolves.
            _init_root(db)
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
    path = chat_db_path(bot_id)
    key = _chat_key(envelope.platform, envelope.conversation_ref)
    ## Storage open + ZODB commit are blocking; keep off the loop.
    return await asyncio.to_thread(
        _store_message_sync, path, _storage_name(bot_id), key, envelope,
        direction)


def _store_message_sync(path: str, storage_name: str, key: str, envelope,
        direction: str = 'in'):
    ## Concurrent writes to one chat race on the lazy container init;
    ## retry the standard ZODB way, through the same helper the neutral
    ## store uses so both layers agree on the retry count.
    db = _get_db(path, storage_name)
    return commit_with_retry(_write_record, db, key, envelope, direction)


def _write_record(db, key: str, envelope, direction: str):
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'chats'):
            root.chats = BTrees.OOBTree.OOBTree()
        chat = _chat_container(root, key)
        native_id = getattr(envelope, 'native_message_id', None)
        if native_id is not None:
            if native_id in chat['native_ids']:
                logger.debug(
                    f"Message {native_id} already stored, skipping...")
                return None
            chat['native_ids'].add(native_id)

        ## NOTE: per-chat schema uses 'connector' for envelope.platform
        ## (the store is keyed by connector in its path). The global
        ## messages.fs store in neutral.py records the same value under
        ## 'platform' — deliberately distinct schemas; see the note there.
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
        chat['messages'][msg_id] = record
        return msg_id
