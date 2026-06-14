import asyncio
import logging
import os
import time
import uuid
import BTrees
import transaction
import zc.zlibstorage
import ZODB
import ZODB.FileStorage
from ZODB.POSException import ConflictError
import persistent

logger = logging.getLogger(__name__)

zodb_path = 'instance/zodb'
## Concurrent writers race on lazy root-structure init; messages.fs and
## people.fs are shared across all chats, so retry the standard ZODB way.
_MAX_COMMIT_RETRIES = 5
_people_db = None
_messages_db = None

def _get_shared_db(db_path):
    try:
        storage = ZODB.FileStorage.FileStorage(db_path)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        storage = ZODB.FileStorage.FileStorage(db_path)
    compressed_storage = zc.zlibstorage.ZlibStorage(storage)
    return ZODB.DB(compressed_storage)

async def get_people_db():
    global _people_db
    if _people_db is None:
        db_path = f"{zodb_path}/people.fs"
        _people_db = _get_shared_db(db_path)
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
        _messages_db = _get_shared_db(db_path)
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
    db = await get_messages_db()
    return await asyncio.to_thread(
        _commit_with_retry, _persist_envelope_sync, db, envelope, direction)

def _persist_envelope_sync(db, envelope, direction: str = 'in'):
    with db.transaction() as connection:
        root = connection.root
        if not hasattr(root, 'messages'):
            root.messages = BTrees.OOBTree.OOBTree()

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

        msg_id = str(uuid.uuid4())
        root.messages[msg_id] = record
        return msg_id
