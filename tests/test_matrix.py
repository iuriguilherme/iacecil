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


def test_is_authorized():
    conn, _ = make_connector()
    conn.config['channels'] = ['!authorized:example.org', '#alias:example.org']
    
    # Mock rooms with different attributes
    mock_auth = SimpleNamespace(users={'@a', '@b', '@c'}, room_id='!authorized:example.org')
    
    mock_alias = SimpleNamespace(users={'@a', '@b', '@c'}, room_id='!other:example.org', 
                                 canonical_alias='#alias:example.org')
    
    mock_dm = SimpleNamespace(users={'@a', '@b'}, room_id='!dm:example.org', member_count=2)
    
    mock_unauth = SimpleNamespace(users={'@a', '@b', '@c'}, room_id='!unauth:example.org',
                                  canonical_alias='#unauth:example.org', member_count=3)

    conn.client = SimpleNamespace(rooms={
        '!authorized:example.org': mock_auth,
        '!other:example.org': mock_alias,
        '!dm:example.org': mock_dm,
        '!unauth:example.org': mock_unauth
    })
    
    # 1. Match by ID
    assert conn.is_authorized(Envelope('matrix', '@a', '!authorized:example.org', 't')) is True
    
    # 2. Match by Alias
    assert conn.is_authorized(Envelope('matrix', '@a', '!other:example.org', 't')) is True
    
    # 3. Match DM (member_count)
    assert conn.is_authorized(Envelope('matrix', '@a', '!dm:example.org', 't')) is True
    
    # 4. No match
    assert conn.is_authorized(Envelope('matrix', '@a', '!unauth:example.org', 't')) is False


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

    async def fake_sync(timeout, since, full_state=None):
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

    async def fake_sync(timeout, since, full_state=None):
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

    async def fake_sync(timeout, since, full_state=None):
        conn.running = False
        return responses.pop(0)

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    await conn.listen()

    assert order == ['dispatch', 'save']
    assert saved == ['new']


@pytest.mark.asyncio
async def test_unknown_pos_discards_token_and_resyncs():
    """A server-rejected sync position (M_UNKNOWN_POS) must self-heal:
    discard the stale token and re-sync fresh, not brick forever."""
    conn, manager = make_connector()
    conn.SYNC_BACKOFF_BASE = 0
    conn._save_token('stale')
    conn.next_batch = 'stale'
    responses = [
        SimpleNamespace(status_code='M_UNKNOWN_POS'),
        sync_response('fresh1', [message_event(body='hi')]),
    ]

    async def fake_sync(timeout, since, full_state=None):
        r = responses.pop(0)
        if not responses:
            conn.running = False
        return r

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    await conn.listen()

    ## Recovery sync is treated as a first sync: token persisted, no echo.
    assert manager.dispatch.call_count == 0
    with open(conn._token_path()) as f:
        assert f.read() == 'fresh1'


def test_token_file_is_private():
    """The persisted sync token must not be world-readable."""
    import stat
    conn, _ = make_connector()
    conn._save_token('secret-cursor')
    mode = stat.S_IMODE(os.stat(conn._token_path()).st_mode)
    assert mode == 0o600


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
async def test_send_ignores_unverified_devices():
    """Replies into encrypted rooms must pass ignore_unverified_devices so a
    headless bot (no interactive verification) can still deliver them."""
    conn, _ = make_connector()
    conn.client = SimpleNamespace(room_send=AsyncMock())
    await conn.send(Envelope('matrix', 'u', '!room:example.org', 'hi'))
    calls = conn.client.room_send.call_args_list
    assert calls
    for call in calls:
        assert call.kwargs['ignore_unverified_devices'] is True


def _keymgmt_client(sync, **flags):
    """Fake client exposing the E2EE key-lifecycle surface."""
    return SimpleNamespace(
        sync=sync,
        olm=object(),
        should_upload_keys=flags.get('upload', False),
        should_query_keys=flags.get('query', False),
        keys_upload=AsyncMock(),
        keys_query=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_listen_runs_key_maintenance_on_sync():
    """A manual sync loop must drive keys_upload/keys_query like
    sync_forever — otherwise the bot never obtains Megolm keys and every
    encrypted message stays undecryptable, so echo never fires."""
    conn, _ = make_connector()
    conn.next_batch = 'old'  # not a first sync

    async def fake_sync(timeout, since, full_state=None):
        conn.running = False
        return sync_response('new', [message_event(body='hi')])

    client = _keymgmt_client(fake_sync, upload=True, query=True)
    conn.client = client
    conn.running = True
    await conn.listen()

    client.keys_upload.assert_awaited_once()
    client.keys_query.assert_awaited_once()


@pytest.mark.asyncio
async def test_key_maintenance_failure_does_not_break_loop():
    """A failing key call is logged and swallowed; the sync loop and message
    dispatch continue unaffected."""
    conn, manager = make_connector()
    conn.next_batch = 'old'

    async def fake_sync(timeout, since, full_state=None):
        conn.running = False
        return sync_response('new', [message_event(body='hi')])

    client = _keymgmt_client(fake_sync, upload=True)
    client.keys_upload = AsyncMock(side_effect=RuntimeError('boom'))
    conn.client = client
    conn.running = True
    await conn.listen()
    assert manager.dispatch.await_count == 1


@pytest.mark.asyncio
async def test_plaintext_mode_skips_key_maintenance():
    """No olm machine (plaintext-only) → no key calls and no AttributeError."""
    conn, manager = make_connector()
    conn.next_batch = 'old'

    async def fake_sync(timeout, since, full_state=None):
        conn.running = False
        return sync_response('new', [message_event(body='hi')])

    conn.client = SimpleNamespace(sync=fake_sync)  # no olm / should_* attrs
    conn.running = True
    await conn.listen()
    assert manager.dispatch.await_count == 1


@pytest.mark.asyncio
async def test_first_sync_requests_full_state_then_incremental():
    """On (re)start the client must request full room state exactly once.
    Without it an incremental resume never learns a room is encrypted (sends
    go out as plaintext) nor loads member lists (DM member-count auth fails);
    later syncs must stay incremental."""
    conn, _ = make_connector()
    conn.next_batch = 'tok'  # restart resuming from a stored token
    seen = []
    responses = [
        sync_response('b1', [message_event(body='one')]),
        sync_response('b2', [message_event(body='two')]),
    ]

    async def fake_sync(timeout, since, full_state=None):
        seen.append(full_state)
        r = responses.pop(0)
        if not responses:
            conn.running = False
        return r

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    await conn.listen()

    assert seen[0] is True
    assert all(v is False for v in seen[1:])


@pytest.mark.asyncio
async def test_sync_error_raises_after_max_failures():
    """Repeated transient sync errors (no next_batch) eventually mark the
    connector down — but only after SYNC_MAX_FAILURES retries, not on the
    first blip."""
    conn, _ = make_connector()
    conn.SYNC_BACKOFF_BASE = 0  # no real sleeping in the test
    conn.SYNC_MAX_FAILURES = 3
    attempts = 0

    async def failing_sync(timeout, since, full_state=None):
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

    async def failing_sync(timeout, since, full_state=None):
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

    async def fake_sync(timeout, since, full_state=None):
        r = responses.pop(0)
        if not responses:
            conn.running = False  # stop after the successful sync
        return r

    conn.client = SimpleNamespace(sync=fake_sync)
    conn.running = True
    await conn.listen()
    assert manager.dispatch.await_count == 1
