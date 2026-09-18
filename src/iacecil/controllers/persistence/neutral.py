import asyncio
import collections
import logging
import threading
import time
import uuid
import BTrees
import transaction
import persistent

from . import storage
from .retry import commit_with_retry as _commit_with_retry

logger = logging.getLogger(__name__)

zodb_path = 'instance/zodb'
_people_db = None
_messages_db = None

## Availability over durability (R11): when shared storage is
## unreachable, connectors keep answering and their message records wait
## here until a write succeeds again. In memory only, so the bound is the
## accepted loss — a connector process that dies mid-outage takes the
## buffer with it. Oldest records are dropped first once it is full.
_WRITE_BUFFER_MAX = 10000
_write_buffer = collections.deque(maxlen=_WRITE_BUFFER_MAX)
## The buffer is reached from asyncio.to_thread workers, so every
## mutation is serialized; without this, two threads interleave a
## popleft and an appendleft and the "oldest first" order is a lie.
_buffer_lock = threading.Lock()

## Opening a store is awaited, so two concurrent first messages would
## otherwise both open it: two handles on one file, or a leaked ZEO
## connection. chat_store guards the same thing with _dbs_lock.
_open_lock = asyncio.Lock()

try:
    from ZEO.Exceptions import ClientDisconnected
    ## OSError covers the socket-level failures a dying server produces
    ## before ZEO reports its own disconnect.
    _STORAGE_UNREACHABLE = (ClientDisconnected, OSError)
except ImportError:  ## pragma: no cover - ZEO is optional
    _STORAGE_UNREACHABLE = (OSError,)

def _get_shared_db(db_path, storage_name):
    """Open one shared store: a ZEO client when shared storage is
    configured, a local FileStorage otherwise (see persistence.storage)."""
    return storage.open_db(db_path, storage_name)

def _open_people_db(db_path):
    db = _get_shared_db(db_path, 'people')
    ## Pre-create roots once, before any concurrent writer exists, so the
    ## to_thread writers below never race to replace a root attribute
    ## (an unresolvable conflict).
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'people'):
            root.people = BTrees.OOBTree.OOBTree()
        if not hasattr(root, 'mappings'):
            root.mappings = BTrees.OOBTree.OOBTree()
    return db

def _open_messages_db(db_path):
    db = _get_shared_db(db_path, 'messages')
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'messages'):
            root.messages = BTrees.OOBTree.OOBTree()
    return db

## Opening a store blocks: a FileStorage open does I/O, and a ZEO client
## waits for the server. Neither may run on the loop every connector
## shares — a reconnect during a storage outage would freeze every bot
## instead of buffering (R11).
async def get_people_db():
    global _people_db
    if _people_db is None:
        async with _open_lock:
            ## Re-check: another coroutine may have opened it while this
            ## one waited for the lock.
            if _people_db is None:
                _people_db = await asyncio.to_thread(
                    _open_people_db, f"{zodb_path}/people.fs")
    return _people_db

async def get_messages_db():
    global _messages_db
    if _messages_db is None:
        async with _open_lock:
            if _messages_db is None:
                _messages_db = await asyncio.to_thread(
                    _open_messages_db, f"{zodb_path}/messages.fs")
    return _messages_db

class Person(persistent.Persistent):
    def __init__(self, person_id=None):
        self.id = person_id or str(uuid.uuid4())
        self.mappings = BTrees.OOBTree.TreeSet()

async def resolve_person(platform: str, native_id: str) -> str:
    db = await get_people_db()
    ## ZODB commit (fsync) is blocking; keep it off the event loop.
    return await asyncio.to_thread(
        _commit_with_retry, _resolve_person_sync, db, platform, native_id)

def _resolve_person_sync(db, platform: str, native_id: str) -> str:
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'people'):
            root.people = BTrees.OOBTree.OOBTree()
        if not hasattr(root, 'mappings'):
            root.mappings = BTrees.OOBTree.OOBTree()
            
        mapping_key = (platform, native_id)
        person_id = root.mappings.get(mapping_key)
        
        if person_id and person_id in root.people:
            return person_id

        person = Person()
        person.mappings.add(mapping_key)
        root.people[person.id] = person
        root.mappings[mapping_key] = person.id
        return person.id

async def merge_persons(id1: str, id2: str) -> str:
    db = await get_people_db()
    return await asyncio.to_thread(_merge_persons_sync, db, id1, id2)

def _merge_persons_sync(db, id1: str, id2: str) -> str:
    with db.transaction() as connection:
        root = connection.root
        p1 = root.people.get(id1)
        p2 = root.people.get(id2)
        if not p1 or not p2:
            raise ValueError("Person not found")

        for mapping in p2.mappings:
            p1.mappings.add(mapping)
            root.mappings[mapping] = p1.id

        del root.people[p2.id]
        return p1.id

async def persist_envelope(envelope, direction: str = 'in'):
    """Append one normalized record to the global message store.

    The id is minted here rather than inside the transaction, so a record
    written now and a record buffered through an outage carry the same
    kind of id and the caller always gets one back.
    """
    msg_id = str(uuid.uuid4())
    record = _build_record(envelope, direction)
    try:
        db = await get_messages_db()
    except _STORAGE_UNREACHABLE as exception:
        _buffer_record(msg_id, record, exception)
        return msg_id
    return await asyncio.to_thread(_persist_sync, db, msg_id, record)

def _persist_sync(db, msg_id, record):
    ## Flush first: a successful write proves storage is back, and the
    ## buffered records are older than this one.
    flush_failure = _flush_buffer(db)
    if flush_failure is not None:
        ## Storage is still down, or went down again mid-flush. Queue
        ## this record behind the ones already waiting rather than
        ## writing it ahead of them and scrambling the order.
        _buffer_record(msg_id, record, flush_failure)
        return msg_id
    try:
        return _commit_with_retry(_write_message_record, db, msg_id, record)
    except _STORAGE_UNREACHABLE as exception:
        _buffer_record(msg_id, record, exception)
        return msg_id

def _buffer_record(msg_id, record, exception):
    with _buffer_lock:
        if len(_write_buffer) == _write_buffer.maxlen:
            logger.warning(
                "Neutral write buffer full; dropping the oldest record")
        _write_buffer.append((msg_id, record))
    logger.warning(
        f"Storage unreachable ({exception!r}); buffered neutral record "
        f"{msg_id} ({len(_write_buffer)} waiting)")

def _flush_buffer(db):
    """Write every buffered record, oldest first.

    Returns None once the buffer is empty, or the exception that stopped
    the flush. A record whose write fails goes back at the front, ahead
    of the ones behind it, so an outage that returns mid-flush loses
    nothing and the order is preserved.
    """
    while True:
        with _buffer_lock:
            if not _write_buffer:
                break
            msg_id, record = _write_buffer.popleft()
        try:
            _commit_with_retry(_write_message_record, db, msg_id, record)
        except Exception as exception:
            ## Any failure, not just an unreachable server: the record is
            ## already out of the buffer, so anything not put back here
            ## is lost. An exhausted conflict retry is the likely case.
            with _buffer_lock:
                if len(_write_buffer) == _write_buffer.maxlen:
                    ## appendleft on a full deque evicts the newest
                    ## record; say so rather than losing it silently.
                    logger.warning(
                        "Neutral write buffer full; dropping the newest "
                        "record to requeue an older one")
                _write_buffer.appendleft((msg_id, record))
            logger.warning(
                f"Buffered write failed ({exception!r}); "
                f"{len(_write_buffer)} records still buffered")
            return exception
        logger.info(f"Flushed buffered neutral record {msg_id}")
    return None

def _write_message_record(db, msg_id, record):
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'messages'):
            root.messages = BTrees.OOBTree.OOBTree()
        root.messages[msg_id] = record
        return msg_id

def _build_record(envelope, direction: str = 'in'):
        ## NOTE: this is the global messages.fs schema and uses 'platform'
        ## (the Envelope field name). The per-chat chat_store uses
        ## 'connector' for the same value — deliberately distinct schemas
        ## for distinct stores; do not "unify" the key without migrating
        ## both stores and their readers.
        record = {
            'platform': envelope.platform,
            'sender_ref': envelope.sender_ref,
            'conversation_ref': envelope.conversation_ref,
            'text': envelope.text,
            'reply_ref': envelope.reply_ref,
            'tags': list(envelope.tags),
            'direction': direction,
            'native_message_id': getattr(envelope, 'native_message_id', None),
            'person_id': getattr(envelope, 'person_id', None),
            ## UTC epoch seconds; platform time when supplied, else now.
            ## Old records lack these keys — readers use .get().
            'timestamp': getattr(envelope, 'timestamp', None) or time.time(),
        }
        return record
