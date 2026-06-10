import pytest
from iacecil.controllers.persistence.neutral import (
    resolve_person,
    merge_persons,
    persist_envelope,
)
from iacecil.models.envelope import Envelope

async def _mappings_for(person_id):
    import iacecil.controllers.persistence.neutral as neutral
    db = await neutral.get_people_db()
    with db.transaction() as conn:
        return set(conn.root.people[person_id].mappings)

@pytest.mark.asyncio
async def test_resolve_person_new_and_existing():
    p1 = await resolve_person("telegram", "12345")
    assert ("telegram", "12345") in await _mappings_for(p1)

    p2 = await resolve_person("telegram", "12345")
    assert p1 == p2

    p3 = await resolve_person("xmpp", "user@host.com")
    assert p1 != p3

@pytest.mark.asyncio
async def test_merge_persons():
    p1 = await resolve_person("telegram", "111")
    p2 = await resolve_person("xmpp", "222")

    merged = await merge_persons(p1, p2)
    mappings = await _mappings_for(merged)
    assert ("telegram", "111") in mappings
    assert ("xmpp", "222") in mappings

    p1_again = await resolve_person("telegram", "111")
    p2_again = await resolve_person("xmpp", "222")
    assert p1_again == p2_again == merged

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
