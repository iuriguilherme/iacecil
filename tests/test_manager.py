import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

from iacecil.connectors import ConnectorManager
from iacecil.connectors.base import BaseConnector
from iacecil.models.envelope import Envelope

# We create some fake connectors for testing
import sys
import types

class FakeConnector(BaseConnector):
    async def connect(self): pass
    async def listen(self): pass
    async def send(self, env): pass
    async def disconnect(self): pass

class FakeRaisingConnector(BaseConnector):
    async def connect(self): pass
    async def listen(self): raise ValueError("Crash!")
    async def send(self, env): pass
    async def disconnect(self): pass

# Patch import machinery to allow fake connectors
@pytest.fixture(autouse=True)
def mock_connectors(monkeypatch):
    telegram_mod = types.ModuleType("iacecil.connectors.telegram")
    telegram_mod.Connector = FakeConnector
    sys.modules["iacecil.connectors.telegram"] = telegram_mod

    xmpp_mod = types.ModuleType("iacecil.connectors.xmpp")
    xmpp_mod.Connector = FakeConnector
    sys.modules["iacecil.connectors.xmpp"] = xmpp_mod

    bad_mod = types.ModuleType("iacecil.connectors.loopback")
    bad_mod.Connector = FakeRaisingConnector
    sys.modules["iacecil.connectors.loopback"] = bad_mod

    yield
    del sys.modules["iacecil.connectors.telegram"]
    del sys.modules["iacecil.connectors.xmpp"]
    del sys.modules["iacecil.connectors.loopback"]


@pytest.mark.asyncio
async def test_manager_loading(caplog):
    config = {
        'telegram': {'token': '123'},
        'xmpp': {'jid': 'user@host', 'password': 'pw'},
        'discord': {}, # empty credentials -> inactive
        'openai': {'api_key': 'fake'}, # non-connector section
    }

    with caplog.at_level(logging.DEBUG):
        manager = ConnectorManager(config)

    assert 'telegram' in manager.connectors
    assert 'xmpp' in manager.connectors
    assert 'discord' not in manager.connectors
    assert 'openai' not in manager.connectors
    ## Non-connector sections are a quiet skip, not an error storm
    assert "ERROR" not in [r.levelname for r in caplog.records
        if 'openai' in r.getMessage()]


@pytest.mark.asyncio
async def test_manager_import_failure_logs_error(caplog, monkeypatch):
    """A connector module that exists but fails to import (missing
    platform dependency) logs an error; siblings still load."""
    import iacecil.connectors as connectors_pkg
    real_import = connectors_pkg.import_module

    def fake_import(name, package=None):
        if name == '.matrix' and package == 'iacecil.connectors':
            raise ImportError("missing dependency nio")
        return real_import(name, package)

    monkeypatch.setattr(connectors_pkg, 'import_module', fake_import)
    config = {
        'telegram': {'token': '123'},
        'matrix': {'homeserver': 'https://x', 'token': 't'},
    }
    with caplog.at_level(logging.ERROR):
        manager = ConnectorManager(config)

    assert 'telegram' in manager.connectors
    assert 'matrix' not in manager.connectors
    assert "Failed to load connector matrix" in caplog.text


@pytest.mark.asyncio
async def test_manager_send_routes_and_warns_once(caplog):
    manager = ConnectorManager({'xmpp': {'jid': 'user@host', 'password': 'pw'}})
    manager.connectors['xmpp'].running = True
    manager.connectors['xmpp'].send = AsyncMock()

    env = Envelope("xmpp", "s", "c", "hi")
    assert await manager.send(env) is True
    manager.connectors['xmpp'].send.assert_called_once_with(env)

    missing = Envelope("matrix", "s", "c", "hi")
    with caplog.at_level(logging.WARNING):
        assert await manager.send(missing) is False
        assert await manager.send(missing) is False
    warnings = [r for r in caplog.records
        if "Drop envelope for matrix" in r.getMessage()]
    assert len(warnings) == 1


@pytest.mark.asyncio
async def test_manager_send_never_raises():
    manager = ConnectorManager({'xmpp': {'jid': 'user@host', 'password': 'pw'}})
    manager.connectors['xmpp'].running = True
    manager.connectors['xmpp'].send = AsyncMock(side_effect=RuntimeError("boom"))
    assert await manager.send(Envelope("xmpp", "s", "c", "hi")) is False


@pytest.mark.asyncio
async def test_dummy_connector_activates_with_zero_manager_edits():
    """R13 acceptance: a new platform is one module + one config
    section; the manager needs no edits."""
    dummy_mod = types.ModuleType("iacecil.connectors.dummy")
    class DummyConnector(FakeConnector):
        required_keys = ('secret',)
    dummy_mod.Connector = DummyConnector
    sys.modules["iacecil.connectors.dummy"] = dummy_mod
    try:
        manager = ConnectorManager({'dummy': {'secret': 's3cr3t'}})
        assert 'dummy' in manager.connectors
        inactive = ConnectorManager({'dummy': {'secret': ''}})
        assert 'dummy' not in inactive.connectors
    finally:
        del sys.modules["iacecil.connectors.dummy"]


@pytest.mark.asyncio
async def test_manager_bot_id_default_and_explicit():
    manager = ConnectorManager({'xmpp': {'jid': 'u@h', 'password': 'pw'}})
    assert manager.bot_id == "default"
    named = ConnectorManager({'xmpp': {'jid': 'u@h', 'password': 'pw'}},
        bot_id="mybot")
    assert named.bot_id == "mybot"


@pytest.mark.asyncio
async def test_manager_run_all(caplog):
    config = {
        'telegram': {'token': '123'}, # fake
        'loopback': {'enabled': True} # fake raising
    }
    manager = ConnectorManager(config)
    
    with caplog.at_level(logging.ERROR):
        await manager.run_all()
    
    # Loopback crashed and is marked down; telegram exited cleanly and is NOT marked down
    assert "Connector loopback failed: Crash!" in caplog.text
    assert "Connector loopback marked down." in caplog.text
    assert "Connector telegram marked down." not in caplog.text


@pytest.mark.asyncio
async def test_dispatch_routing():
    manager = ConnectorManager({'xmpp': {'jid': 'user@host', 'password': 'pw'}})
    manager.connectors['xmpp'].running = True

    start_handler = AsyncMock(return_value="Hello Start")
    default_handler = AsyncMock(return_value="Hello Default")

    manager.register_command("start", start_handler)
    manager.set_default_handler(default_handler)

    manager.connectors['xmpp'].send = AsyncMock()

    env1 = Envelope("xmpp", "s", "c", "/start args")
    await manager.dispatch(env1)
    start_handler.assert_called_once()
    ## dispatch() enriches the envelope with the resolved person_id
    ## before handing it to the handler, so compare stable fields
    ## rather than the original (person_id=None) instance.
    handled1 = start_handler.call_args[0][0]
    assert (handled1.platform, handled1.sender_ref,
        handled1.conversation_ref, handled1.text) == (
        env1.platform, env1.sender_ref, env1.conversation_ref, env1.text)
    assert handled1.person_id is not None
    default_handler.assert_not_called()
    manager.connectors['xmpp'].send.assert_called_once()

    start_handler.reset_mock()
    manager.connectors['xmpp'].send.reset_mock()

    env2 = Envelope("xmpp", "s", "c", "normal text")
    await manager.dispatch(env2)
    start_handler.assert_not_called()
    default_handler.assert_called_once()
    handled2 = default_handler.call_args[0][0]
    assert (handled2.platform, handled2.sender_ref,
        handled2.conversation_ref, handled2.text) == (
        env2.platform, env2.sender_ref, env2.conversation_ref, env2.text)
    assert handled2.person_id is not None
    manager.connectors['xmpp'].send.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_skips_telegram_registry():
    """Telegram-origin envelopes are persisted but never dispatched to the
    command registry -- legacy aiogram handlers own Telegram replies (R6)."""
    manager = ConnectorManager({'telegram': {'token': '123'}})

    start_handler = AsyncMock(return_value="Hello Start")
    default_handler = AsyncMock(return_value="Hello Default")
    manager.register_command("start", start_handler)
    manager.set_default_handler(default_handler)
    manager.connectors['telegram'].send = AsyncMock()

    await manager.dispatch(Envelope("telegram", "s", "c", "/start args"))
    await manager.dispatch(Envelope("telegram", "s", "c", "plain text"))

    start_handler.assert_not_called()
    default_handler.assert_not_called()
    manager.connectors['telegram'].send.assert_not_called()


@pytest.mark.asyncio
async def test_set_default_handler_warns_on_overwrite(caplog):
    """Two plugins registering add_envelope_handlers would silently clobber
    each other; the second registration must warn."""
    manager = ConnectorManager({'xmpp': {'jid': 'u@h', 'password': 'pw'}})
    h1 = AsyncMock()
    h1.__name__ = 'first'
    h2 = AsyncMock()
    h2.__name__ = 'second'
    manager.set_default_handler(h1)
    with caplog.at_level(logging.WARNING):
        manager.set_default_handler(h2)
    assert manager.default_handler is h2
    assert any('overwritten' in r.getMessage() for r in caplog.records)


@pytest.mark.asyncio
async def test_missing_platform_dependency_logs_error(caplog, monkeypatch):
    """A connector module present but missing its platform library (a
    ModuleNotFoundError whose name is NOT the connector module itself) is
    an error, not a silent debug skip."""
    import iacecil.connectors as connectors_pkg
    real_import = connectors_pkg.import_module

    def fake_import(name, package=None):
        if name == '.matrix' and package == 'iacecil.connectors':
            raise ModuleNotFoundError("No module named 'nio'", name='nio')
        return real_import(name, package)

    monkeypatch.setattr(connectors_pkg, 'import_module', fake_import)
    with caplog.at_level(logging.DEBUG):
        manager = ConnectorManager(
            {'matrix': {'homeserver': 'h', 'token': 't'}})
    assert 'matrix' not in manager.connectors
    assert "missing dependency 'nio'" in caplog.text
    assert "Skipping non-connector section matrix" not in caplog.text


@pytest.mark.asyncio
async def test_absent_connector_module_is_quiet_skip(caplog):
    """A config section with no connector module at all is a quiet skip,
    not an error."""
    with caplog.at_level(logging.DEBUG):
        manager = ConnectorManager({'totally_not_a_connector': {'k': 'v'}})
    assert 'totally_not_a_connector' not in manager.connectors
    assert not [r for r in caplog.records if r.levelname == 'ERROR'
        and 'totally_not_a_connector' in r.getMessage()]


@pytest.mark.asyncio
async def test_telegram_v3_suppresses_legacy_telegram():
    """When both telegram and telegram_v3 are active, the legacy telegram
    connector is dropped in favor of telegram_v3 (strangler-fig)."""
    manager = ConnectorManager({
        'telegram': {'token': '123:abc'},
        'telegram_v3': {'token': '123:abc'},
    })
    assert 'telegram_v3' in manager.connectors
    assert 'telegram' not in manager.connectors


@pytest.mark.asyncio
async def test_legacy_telegram_kept_without_v3():
    """Without telegram_v3, the legacy telegram connector loads normally."""
    manager = ConnectorManager({'telegram': {'token': '123:abc'}})
    assert 'telegram' in manager.connectors
