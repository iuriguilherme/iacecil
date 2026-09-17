import asyncio
import collections
import logging
import os
import time
import uuid
import BTrees
import transaction
import ZODB
from ZODB.POSException import ConflictError
import persistent

from . import storage

logger = logging.getLogger(__name__)

zodb_path = 'instance/zodb'
## Concurrent writers race on lazy root-structure init; messages.fs and
## people.fs are shared across all chats, so retry the standard ZODB way.
_MAX_COMMIT_RETRIES = 5
_people_db = None
_messages_db = None

## Availability over durability (R11): when shared storage is
## unreachable, connectors keep answering and their message records wait
## here until a write succeeds again. In memory only, so the bound is the
## accepted loss — a connector process that dies mid-outage takes the
## buffer with it. Oldest records are dropped first once it is full.
_WRITE_BUFFER_MAX = 10000
_write_buffer = collections.deque(maxlen=_WRITE_BUFFER_MAX)

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

async def get_people_db():
    global _people_db
    if _people_db is None:
        db_path = f"{zodb_path}/people.fs"
        _people_db = _get_shared_db(db_path, 'people')
        ## Pre-create roots once (on the single-threaded loop) so the
        ## concurrent to_thread writers below never race to replace a
        ## root attribute (unresolvable conflict).
        with _people_db.transaction() as connection:
            root = connection.root
            if not hasattr(root, 'people'):
                root.people = BTrees.OOBTree.OOBTree()
            if not hasattr(root, 'mappings'):
                root.mappings = BTrees.OOBTree.OOBTree()
    return _people_db

async def get_messages_db():
    global _messages_db
    if _messages_db is None:
        db_path = f"{zodb_path}/messages.fs"
        _messages_db = _get_shared_db(db_path, 'messages')
        with _messages_db.transaction() as connection:
            root = connection.root
            if not hasattr(root, 'messages'):
                root.messages = BTrees.OOBTree.OOBTree()
    return _messages_db

def _commit_with_retry(fn, *args):
    """Re-run a transaction function on ConflictError (concurrent writers
    racing on shared ZODB roots). Runs inside asyncio.to_thread."""
    for attempt in range(_MAX_COMMIT_RETRIES):
        try:
            return fn(*args)
        except ConflictError:
            if attempt == _MAX_COMMIT_RETRIES - 1:
                raise

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
    while _write_buffer:
        msg_id, record = _write_buffer.popleft()
        try:
            _commit_with_retry(_write_message_record, db, msg_id, record)
        except _STORAGE_UNREACHABLE as exception:
            _write_buffer.appendleft((msg_id, record))
            logger.warning(
                f"Storage unreachable during flush ({exception!r}); "
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
