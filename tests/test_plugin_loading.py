import pytest
import logging
import sys
import types
from unittest.mock import AsyncMock
from iacecil.connectors import load_plugin

@pytest.fixture(autouse=True)
def mock_plugins(monkeypatch):
    # Fake plugin with only 'add_handlers'
    p1 = types.ModuleType("plugins.plugin_legacy")
    p1.add_handlers = AsyncMock()
    sys.modules["plugins.plugin_legacy"] = p1

    # Fake plugin with 'add_handlers_xmpp'
    p2 = types.ModuleType("plugins.plugin_xmpp")
    p2.add_handlers_xmpp = AsyncMock()
    sys.modules["plugins.plugin_xmpp"] = p2

    # Fake plugin with neither
    p3 = types.ModuleType("plugins.plugin_empty")
    sys.modules["plugins.plugin_empty"] = p3

    yield
    del sys.modules["plugins.plugin_legacy"]
    del sys.modules["plugins.plugin_xmpp"]
    del sys.modules["plugins.plugin_empty"]

@pytest.mark.asyncio
async def test_plugin_legacy_telegram(caplog):
    target = object()
    with caplog.at_level(logging.INFO):
        await load_plugin('telegram', 'plugin_legacy', target)
    sys.modules["plugins.plugin_legacy"].add_handlers.assert_called_once_with(target)
    assert "Activated plugin plugin_legacy for telegram" in caplog.text

@pytest.mark.asyncio
async def test_plugin_legacy_xmpp(caplog):
    target = object()
    await load_plugin('xmpp', 'plugin_legacy', target)
    sys.modules["plugins.plugin_legacy"].add_handlers.assert_not_called()
    assert "Plugin plugin_legacy has no entry point add_handlers_xmpp for connector xmpp" in caplog.text

@pytest.mark.asyncio
async def test_plugin_xmpp_xmpp(caplog):
    target = object()
    with caplog.at_level(logging.INFO):
        await load_plugin('xmpp', 'plugin_xmpp', target)
    sys.modules["plugins.plugin_xmpp"].add_handlers_xmpp.assert_called_once_with(target)
    assert "Activated plugin plugin_xmpp for xmpp" in caplog.text

@pytest.mark.asyncio
async def test_plugin_empty(caplog):
    target = object()
    await load_plugin('xmpp', 'plugin_empty', target)
    assert "Plugin plugin_empty has no entry point add_handlers_xmpp for connector xmpp" in caplog.text
