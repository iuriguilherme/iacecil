import pytest
import os
import shutil
from iacecil.controllers.persistence.neutral import resolve_person, merge_persons, persist_envelope, _people_db, _messages_db
from iacecil.models.envelope import Envelope

@pytest.fixture(autouse=True)
def clean_zodb():
    import iacecil.controllers.persistence.neutral as neutral
    if os.path.exists("instance/zodb"):
        shutil.rmtree("instance/zodb")
    neutral._people_db = None
    neutral._messages_db = None
    yield
    if neutral._people_db:
        neutral._people_db.close()
    if neutral._messages_db:
        neutral._messages_db.close()

@pytest.mark.asyncio
async def test_resolve_person_new_and_existing():
    p1 = await resolve_person("telegram", "12345")
    assert ("telegram", "12345") in p1.mappings
    
    p2 = await resolve_person("telegram", "12345")
    assert p1.id == p2.id

    p3 = await resolve_person("xmpp", "user@host.com")
    assert p1.id != p3.id

@pytest.mark.asyncio
async def test_merge_persons():
    p1 = await resolve_person("telegram", "111")
    p2 = await resolve_person("xmpp", "222")
    
    merged = await merge_persons(p1.id, p2.id)
    assert ("telegram", "111") in merged.mappings
    assert ("xmpp", "222") in merged.mappings

    p1_again = await resolve_person("telegram", "111")
    p2_again = await resolve_person("xmpp", "222")
    assert p1_again.id == p2_again.id == merged.id

@pytest.mark.asyncio
async def test_persist_envelope():
    env = Envelope(
        platform="telegram",
        sender_ref="123",
        conversation_ref="456",
        text="test msg",
        raw=object(),
        extra={"foo": "bar"}
    )
    msg_id = await persist_envelope(env)
    assert msg_id is not None
    
    import iacecil.controllers.persistence.neutral as neutral
    db = await neutral.get_messages_db()
    with db.transaction() as conn:
        record = conn.root.messages[msg_id]
        assert record['text'] == "test msg"
        assert 'raw' not in record
        assert 'extra' not in record
