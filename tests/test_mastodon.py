import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from iacecil.models.envelope import Envelope
from iacecil.connectors.mastodon import Connector, strip_html


def make_connector():
    manager = AsyncMock()
    return Connector(manager, {'api_base_url': 'https://h',
        'access_token': 'x'}), manager


def fake_status(content="<p>hello fedi</p>", account_id=111, status_id=333,
        created_at=None):
    return {
        'id': status_id,
        'account': {'id': account_id},
        'content': content,
        'created_at': created_at,
    }


def test_activation_rule():
    assert Connector.is_active(
        {'api_base_url': 'https://h', 'access_token': 'x'}) is True
    assert Connector.is_active({'api_base_url': 'https://h'}) is False
    assert Connector.is_active({'access_token': 'x'}) is False
    assert Connector.is_active({'api_base_url': '', 'access_token': ''}) is False
    assert Connector.is_active({}) is False


def test_strip_html_preserves_breaks_and_unescapes():
    assert strip_html('<p>hello world</p>') == 'hello world'
    assert strip_html('<p>a</p><p>b</p>') == 'a\n\nb'
    assert strip_html('line<br />two') == 'line\ntwo'
    assert strip_html('<p>a &amp; b</p>') == 'a & b'
    assert strip_html('') == ''
    assert strip_html(None) == ''


@pytest.mark.asyncio
async def test_status_becomes_envelope():
    conn, _ = make_connector()
    created = datetime(2026, 6, 13, 12, 0, tzinfo=timezone.utc)
    env = conn._status_to_envelope(
        fake_status(content="<p>hi there</p>", created_at=created))
    assert env.platform == 'mastodon'
    assert env.sender_ref == '111'
    assert env.conversation_ref == '333'
    assert env.reply_ref == '333'
    assert env.native_message_id == '333'
    assert env.text == 'hi there'
    assert env.timestamp == created.timestamp()


@pytest.mark.asyncio
async def test_mention_dispatched():
    conn, manager = make_connector()
    conn.own_account_id = 999
    await conn._handle_status(fake_status(account_id=111))
    manager.dispatch.assert_called_once()
    env = manager.dispatch.call_args[0][0]
    assert env.platform == 'mastodon'
    assert env.sender_ref == '111'


@pytest.mark.asyncio
async def test_self_status_skipped():
    """Own status streamed back: no dispatch (echo-loop guard)."""
    conn, manager = make_connector()
    conn.own_account_id = 111
    await conn._handle_status(fake_status(account_id=111))
    manager.dispatch.assert_not_called()


@pytest.mark.asyncio
async def test_send_at_exact_limit_single_chunk():
    conn, _ = make_connector()
    conn.client = MagicMock()
    await conn.send(Envelope('mastodon', 'u', '1', 'x' * 500))
    calls = conn.client.status_post.call_args_list
    assert len(calls) == 1
    assert calls[0].args[0] == 'x' * 500


@pytest.mark.asyncio
async def test_send_over_limit_chunks_in_order():
    conn, _ = make_connector()
    conn.client = MagicMock()
    text = 'a' * 500 + 'b'
    await conn.send(Envelope('mastodon', 'u', '1', text))
    chunks = [c.args[0] for c in conn.client.status_post.call_args_list]
    assert len(chunks) == 2
    assert all(len(c) <= 500 for c in chunks)
    assert ''.join(chunks) == text


@pytest.mark.asyncio
async def test_send_threads_reply_then_unsets():
    conn, _ = make_connector()
    conn.client = MagicMock()
    text = 'a' * 500 + 'b'
    await conn.send(Envelope('mastodon', 'u', '1', text, reply_ref='333'))
    calls = conn.client.status_post.call_args_list
    ## First chunk replies to the original status; the rest chain off it.
    assert calls[0].kwargs['in_reply_to_id'] == '333'
    assert calls[1].kwargs['in_reply_to_id'] is None


@pytest.mark.asyncio
async def test_send_threads_on_conversation_ref_when_no_reply_ref():
    """Echo replies from dispatch() carry no reply_ref; the answer must
    still thread onto the source status via conversation_ref, not post
    as an orphan."""
    conn, _ = make_connector()
    conn.client = MagicMock()
    await conn.send(Envelope('mastodon', 'u', '333', 'echo me'))
    call = conn.client.status_post.call_args_list[0]
    assert call.kwargs['in_reply_to_id'] == '333'


@pytest.mark.asyncio
async def test_send_without_client_warns(caplog):
    import logging
    conn, _ = make_connector()
    with caplog.at_level(logging.WARNING):
        await conn.send(Envelope('mastodon', 'u', '1', 'hi'))
    assert any('client not initialized' in r.getMessage()
        for r in caplog.records)
