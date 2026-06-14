import logging
import os
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from iacecil.models.envelope import Envelope
import iacecil.connectors.matrix as matrix_mod
from iacecil.connectors.matrix import Connector


@pytest.fixture(autouse=True)
def isolated_token_dir(tmp_path, monkeypatch):
    """Matrix sync tokens never touch the real instance/ tree."""
    monkeypatch.setattr(matrix_mod, 'TOKEN_DIR', str(tmp_path / 'matrix'))
    yield


class FakeEvent(SimpleNamespace):
    pass


class MegolmEvent(SimpleNamespace):
    """Name matters: connector detects encrypted events by class name."""
    pass


def make_connector(bot_id='default'):
    manager = AsyncMock()
    manager.bot_id = bot_id
    conn = Connector(manager, {
        'homeserver': 'https://example.org',
        'token': 't0ken',
        'user': '@bot:example.org',
    })
    conn.user_id = '@bot:example.org'
    return conn, manager


def sync_response(next_batch, events=()):
    timeline = SimpleNamespace(events=list(events))
    room = SimpleNamespace(timeline=timeline)
    rooms = SimpleNamespace(join={'!room:example.org': room})
    return SimpleNamespace(next_batch=next_batch, rooms=rooms)


def message_event(sender='@user:example.org', body='hi', event_id='$e1'):
    return FakeEvent(sender=sender, body=body, event_id=event_id,
        server_timestamp=1700000000000)


def test_activation_rules():
    assert Connector.is_active({'homeserver': 'h', 'token': 't'}) is True
    assert Connector.is_active({'homeserver': 'h', 'user': 'u',
        'password': 'p'}) is True
    assert Connector.is_active({'homeserver': 'h'}) is False
    assert Connector.is_active({'token': 't'}) is False
    assert Connector.is_active({}) is False


@pytest.mark.asyncio
async def test_event_becomes_envelope():
    conn, manager = make_connector()
    await conn._on_event('!room:example.org', message_event())

    manager.dispatch.assert_called_once()
    env = manager.dispatch.call_args[0][0]
    assert env.platform == 'matrix'
    assert env.sender_ref == '@user:example.org'
    assert env.conversation_ref == '!room:example.org'
    assert env.text == 'hi'
    assert env.native_message_id == '$e1'
    assert env.timestamp == 1700000000.0


@pytest.mark.asyncio
async def test_own_events_skipped():
    conn, manager = make_connector()
    await conn._on_event('!room:example.org',
        message_event(sender='@bot:example.org'))
    manager.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_encrypted_room_warns_once(caplog):
    conn, manager = make_connector()
    encrypted = MegolmEvent(sender='@user:example.org')
    with caplog.at_level(logging.WARNING):
        await conn._on_event('!room:example.org', encrypted)
        await conn._on_event('!room:example.org', encrypted)
    manager.dispatch.assert_not_called()
    warnings = [r for r in caplog.records if 'encrypted' in r.getMessage()]
    assert len(warnings) == 1


@pytest.mark.asyncio
async def test_first_sync_acquires_token_without_dispatch():
    """Tokenless first boot: backlog delivered by the initial sync must
    produce zero dispatches; the token is persisted; the second sync
    dispatches normally."""
    conn, manager = make_connector()
    responses = [
        sync_response('batch1', [message_event(body='backlog')]),
        sync_response('batch2', [message_event(body='fresh')]),
    ]

    async def fake_sync(timeout, since):
        response = responses.pop(0)
        if not responses:
            conn.running = False
        return response

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    conn.next_batch = None

    await conn.listen()

    assert manager.dispatch.call_count == 1
    assert manager.dispatch.call_args[0][0].text == 'fresh'
    with open(conn._token_path()) as f:
        assert f.read() == 'batch2'


@pytest.mark.asyncio
async def test_restart_with_token_dispatches_immediately():
    conn, manager = make_connector()
    conn._save_token('saved-batch')
    assert conn._load_token() == 'saved-batch'

    responses = [sync_response('batch9', [message_event(body='hello')])]

    async def fake_sync(timeout, since):
        assert since == 'saved-batch'
        conn.running = False
        return responses.pop(0)

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    conn.next_batch = conn._load_token()

    await conn.listen()
    assert manager.dispatch.call_count == 1


@pytest.mark.asyncio
async def test_token_saved_after_dispatch_on_normal_sync():
    """On a non-first sync the token must be persisted only after the
    batch's events were dispatched, so a crash mid-batch re-syncs from the
    previous token (replay deduped) instead of dropping messages."""
    conn, manager = make_connector()
    conn.next_batch = 'old'  # not a first sync
    order = []

    async def rec_dispatch(env):
        order.append('dispatch')

    manager.dispatch = AsyncMock(side_effect=rec_dispatch)
    saved = []
    conn._save_token = lambda t: (order.append('save'), saved.append(t))

    responses = [sync_response('new', [message_event(body='hi')])]

    async def fake_sync(timeout, since):
        conn.running = False
        return responses.pop(0)

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    await conn.listen()

    assert order == ['dispatch', 'save']
    assert saved == ['new']


def test_corrupt_token_warns_and_fresh_syncs(caplog):
    conn, _ = make_connector()
    path = conn._token_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('')
    with caplog.at_level(logging.WARNING):
        assert conn._load_token() is None
    assert any('corrupt' in r.getMessage() for r in caplog.records)


def test_token_write_is_atomic():
    conn, _ = make_connector()
    conn._save_token('abc')
    path = conn._token_path()
    assert not os.path.exists(path + '.tmp')
    with open(path) as f:
        assert f.read() == 'abc'


@pytest.mark.asyncio
async def test_send_chunks_under_event_bound():
    conn, _ = make_connector()
    conn.client = SimpleNamespace(room_send=AsyncMock())

    env = Envelope('matrix', 'u', '!room:example.org', 'x' * 20000)
    await conn.send(env)

    calls = conn.client.room_send.call_args_list
    assert len(calls) == 2
    for call in calls:
        assert len(call.kwargs['content']['body']) <= Connector.MAX_TEXT
        assert call.kwargs['room_id'] == '!room:example.org'
        assert call.kwargs['content']['msgtype'] == 'm.text'


@pytest.mark.asyncio
async def test_sync_error_raises_after_max_failures():
    """Repeated transient sync errors (no next_batch) eventually mark the
    connector down — but only after SYNC_MAX_FAILURES retries, not on the
    first blip."""
    conn, _ = make_connector()
    conn.SYNC_BACKOFF_BASE = 0  # no real sleeping in the test
    conn.SYNC_MAX_FAILURES = 3
    attempts = 0

    async def failing_sync(timeout, since):
        nonlocal attempts
        attempts += 1
        return SimpleNamespace(message='boom')  # transient: no status_code

    conn.client = SimpleNamespace(sync=failing_sync)
    conn.running = True
    with pytest.raises(ConnectionError):
        await conn.listen()
    assert attempts == 3  # retried, not raised on the first error


@pytest.mark.asyncio
async def test_permanent_sync_error_raises_immediately():
    """A permanent error (e.g. unknown access token) cannot be retried
    away — mark down at once without burning retries."""
    conn, _ = make_connector()
    conn.SYNC_BACKOFF_BASE = 0
    attempts = 0

    async def failing_sync(timeout, since):
        nonlocal attempts
        attempts += 1
        return SimpleNamespace(status_code='M_UNKNOWN_TOKEN')

    conn.client = SimpleNamespace(sync=failing_sync)
    conn.running = True
    with pytest.raises(ConnectionError):
        await conn.listen()
    assert attempts == 1  # no retry on a permanent error


@pytest.mark.asyncio
async def test_transient_sync_error_recovers():
    """A transient sync error is retried; once sync succeeds the connector
    keeps running and dispatches normally."""
    conn, manager = make_connector()
    conn.SYNC_BACKOFF_BASE = 0
    conn.next_batch = 'have_token'  # not a first sync; dispatch immediately
    responses = [
        SimpleNamespace(message='temporary glitch'),  # transient error
        sync_response('batch2', [message_event(body='hello')]),
    ]

    async def fake_sync(timeout, since):
        r = responses.pop(0)
        if not responses:
            conn.running = False  # stop after the successful sync
        return r

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    await conn.listen()
    assert manager.dispatch.await_count == 1
