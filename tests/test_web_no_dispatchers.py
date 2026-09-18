"""Web routes run with no live dispatchers (R8, AE4).

The web unit has no aiogram dispatcher in its process any more, so every
route that used to read `current_app.dispatchers` had to be re-sourced.
These tests boot the real Quart app and request the real routes: an
AttributeError from a missing attribute is exactly the failure they
exist to catch, and a mock would hide it.
"""

import pytest
import pytest_asyncio

from iacecil.views.quart_app import quart_startup


def identity(bot_id='123456', name='mybot', first_name='Cecil'):
    return {
        'id': bot_id,
        'name': name,
        'first_name': first_name,
        'username': name,
        'status': None,
    }


@pytest.fixture
def app():
    return quart_startup({}, [identity(), identity(
        '789', 'otherbot', 'Other')])


@pytest_asyncio.fixture
async def client(app):
    async with app.test_app() as test_app:
        yield test_app.test_client()


@pytest.mark.asyncio
async def test_status_page_renders_from_config(client):
    """Covers AE4: the home page no longer calls get_me()."""
    response = await client.get('/status/')

    assert response.status_code == 200
    body = await response.get_data(as_text=True)
    assert 'Cecil' in body
    assert 'Other' in body


@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['/admin/files/', '/admin/messages/',
    '/admin/texts/'])
async def test_read_routes_load_without_dispatchers(client, path):
    """Covers AE4: the read pages are the ones that must keep working."""
    response = await client.get(path)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_bot_selector_lists_every_configured_bot(client):
    """The selector used to be built from live get_me() calls."""
    response = await client.get('/admin/files/')

    body = await response.get_data(as_text=True)
    assert 'Cecil' in body
    assert 'Other' in body
    assert '123456' in body


@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['/admin/polling/', '/admin/send_message/',
    '/admin/updates/'])
async def test_control_routes_say_they_are_unavailable(client, path):
    """Covers AE4: a control route acts on a live bot, which this
    process does not have. It answers plainly instead of 500-ing."""
    response = await client.get(path)

    assert response.status_code == 503
    payload = await response.get_json()
    assert payload['error'] == 'not available'
    assert 'slice 2' in payload['available_in']


@pytest.mark.asyncio
async def test_no_bots_configured_still_renders(client, app):
    """Edge: an empty bot list must not break the page."""
    empty = quart_startup({}, [])
    async with empty.test_app() as test_app:
        response = await test_app.test_client().get('/status/')

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_choices_come_from_storage_not_from_a_live_bot(tmp_path,
        monkeypatch):
    """Chat titles used to come from bot.get_chat(). Without a live bot,
    the stored chat id is the label."""
    import iacecil.views.quart_app.blueprints.admin.routes as routes

    chats = tmp_path / 'instance' / 'zodb' / 'bots' / '123456' / 'chats'
    chats.mkdir(parents=True)
    (chats / '-100123.fs').write_text('')
    (chats / '456.fs').write_text('')
    monkeypatch.chdir(tmp_path)

    choices = routes.stored_chat_choices('123456')

    assert choices == [('-100123', '-100123'), ('456', '456')]


def test_missing_chat_directory_is_not_an_error(tmp_path, monkeypatch):
    """A bot that has never stored a chat renders an empty selector
    rather than creating directories from a read path."""
    import iacecil.views.quart_app.blueprints.admin.routes as routes

    monkeypatch.chdir(tmp_path)

    assert routes.stored_chat_choices('nosuchbot') == []
    assert not (tmp_path / 'instance').exists()
