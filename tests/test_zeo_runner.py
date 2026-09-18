"""The shared storage server unit (R9, R13, AE5).

The storage set is fixed when the server starts, so what these tests
pin is which storages it decides to serve and that both units can then
reach them.
"""

import os

import pytest

import iacecil.controllers.persistence.chat_store as chat_store
import iacecil.controllers.persistence.neutral as neutral
import iacecil.controllers.persistence.storage as storage
from iacecil.controllers._iacecil import zeo_runner
from iacecil.models.envelope import Envelope


class FakeConfig:
    def __init__(self, enabled=True, address=None):
        self.zeo = {'enabled': enabled, 'address': address or []}


def test_storage_set_is_people_messages_and_one_per_bot():
    """R13: per bot, never per chat — a chat appears at runtime and the
    server cannot serve a storage its config never named."""
    storages = zeo_runner.storage_paths(
        {'mybot': FakeConfig(), 'otherbot': FakeConfig()}, 'instance/zodb')

    assert sorted(storages) == [
        'chats_mybot', 'chats_otherbot', 'messages', 'people']
    assert storages['chats_mybot'].endswith('bots/mybot/chats.fs')
    assert storages['people'].endswith('instance/zodb/people.fs')


def test_storage_names_match_what_the_clients_ask_for():
    """A name mismatch would fail only at runtime, on the first write."""
    storages = zeo_runner.storage_paths({'mybot': FakeConfig()})

    assert storage.storage_name_for_bot('mybot') in storages


def test_no_bots_still_serves_the_shared_storages():
    storages = zeo_runner.storage_paths({})

    assert sorted(storages) == ['messages', 'people']


def test_storage_conf_declares_every_storage():
    conf = zeo_runner.storage_conf({
        'people': '/tmp/people.fs', 'chats_mybot': '/tmp/chats.fs'})

    assert '<filestorage people>' in conf
    assert '<filestorage chats_mybot>' in conf
    assert 'path /tmp/people.fs' in conf


def test_address_comes_from_configuration():
    address = zeo_runner.zeo_address(
        {'mybot': FakeConfig(address=['127.0.0.1', 9100])})

    assert address == ('127.0.0.1', 9100)


def test_address_falls_back_to_the_default():
    assert zeo_runner.zeo_address({}) == zeo_runner.DEFAULT_ADDRESS
    assert zeo_runner.zeo_address(
        {'mybot': FakeConfig(enabled=False, address=['h', 1])}
    ) == zeo_runner.DEFAULT_ADDRESS


def test_directories_are_created_before_the_server_opens_them(tmp_path):
    storages = {'people': str(tmp_path / 'zodb' / 'people.fs'),
        'chats_mybot': str(tmp_path / 'zodb' / 'bots' / 'mybot' / 'chats.fs')}

    zeo_runner.prepare_directories(storages)

    assert (tmp_path / 'zodb').is_dir()
    assert (tmp_path / 'zodb' / 'bots' / 'mybot').is_dir()


@pytest.mark.asyncio
async def test_both_units_share_one_server(tmp_path, monkeypatch):
    """Covers AE5: what one unit writes, the other reads — the whole
    reason the storage server exists."""
    configs = {'mybot': FakeConfig(address=['127.0.0.1', 0])}
    address, stop = zeo_runner.start_server(configs, str(tmp_path / 'zodb'))
    monkeypatch.setattr(storage, 'zeo_address', address)
    try:
        ## The connector unit's writes
        person_id = await neutral.resolve_person('loopback', 'user1')
        await chat_store.store_message('mybot',
            Envelope('loopback', 'user1', 'local_chat', 'hello'))

        ## The web unit's reads, through its own client connections
        people = storage.open_db('unused', 'people')
        chats = storage.open_db('unused', storage.storage_name_for_bot(
            'mybot'))
        try:
            with people.transaction() as connection:
                assert person_id in connection.root.people
            with chats.transaction() as connection:
                chat = connection.root.chats[
                    chat_store._chat_key('loopback', 'local_chat')]
                assert [record['text'] for record in
                    chat['messages'].values()] == ['hello']
        finally:
            people.close()
            chats.close()
    finally:
        stop()


def test_server_serves_a_storage_for_every_configured_bot(tmp_path):
    """A bot whose storage the server forgot would fail on first write."""
    configs = {'mybot': FakeConfig(address=['127.0.0.1', 0]),
        'otherbot': FakeConfig()}
    address, stop = zeo_runner.start_server(configs, str(tmp_path / 'zodb'))
    try:
        for bot_id in configs:
            db = None
            try:
                import ZEO.ClientStorage
                client = ZEO.ClientStorage.ClientStorage(
                    address, storage=storage.storage_name_for_bot(bot_id),
                    wait=True)
                client.close()
            finally:
                if db is not None:
                    db.close()
    finally:
        stop()


def test_supervisor_zeo_child_runs_this_module():
    from iacecil.controllers._iacecil import supervisor
    import inspect

    assert 'run_zeo' in inspect.getsource(supervisor.zeo_unit)


def test_zeo_mode_runs_the_storage_server_alone():
    """`python -m iacecil zeo` runs it under another supervisor or by
    hand, without the other two units."""
    import inspect

    import iacecil.__main__ as main_module

    source = inspect.getsource(main_module)
    assert "'zeo'" in source
    assert 'from .controllers._iacecil.zeo_runner import run_zeo' in source


def test_a_non_loopback_host_is_reported_not_silently_ignored(tmp_path,
        caplog):
    """ZEO binds loopback this slice; a configured host that will not be
    honored must be visible to the operator."""
    configs = {'mybot': FakeConfig(address=['0.0.0.0', 0])}

    address, stop = zeo_runner.start_server(configs, str(tmp_path / 'zodb'))
    try:
        assert address[0] in ('localhost', '127.0.0.1')
        assert any('binds loopback only' in record.message
            for record in caplog.records)
    finally:
        stop()


def test_storage_path_matches_the_chat_store_for_awkward_bot_ids():
    """The storage server and the chat store must agree on the file.

    A bot id with an uppercase letter or an `@` encodes through
    sanitize_component; a second hand-rolled join would serve a
    different file than the one the chat store writes with ZEO off.
    """
    from iacecil.controllers.persistence.chat_store import chat_db_path

    base = chat_store.zodb_path
    for bot_id in ('mybot', 'MateHackersBot', 'bot@host'):
        storages = zeo_runner.storage_paths({bot_id: FakeConfig()}, base)
        served = storages[storage.storage_name_for_bot(bot_id)]
        assert served == chat_db_path(bot_id, base), bot_id
