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

    # Fake plugin with only the generic envelope loader
    p4 = types.ModuleType("plugins.plugin_generic")
    p4.add_envelope_handlers = AsyncMock()
    sys.modules["plugins.plugin_generic"] = p4

    # Fake plugin with both generic and per-connector loaders
    p5 = types.ModuleType("plugins.plugin_both")
    p5.add_envelope_handlers = AsyncMock()
    p5.add_handlers_xmpp = AsyncMock()
    sys.modules["plugins.plugin_both"] = p5

    yield
    for name in ("plugin_legacy", "plugin_xmpp", "plugin_empty",
            "plugin_generic", "plugin_both"):
        del sys.modules[f"plugins.{name}"]

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
    assert ("Plugin plugin_legacy has no entry point add_handlers_xmpp"
        " or add_envelope_handlers for connector xmpp") in caplog.text

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
    assert ("Plugin plugin_empty has no entry point add_handlers_xmpp"
        " or add_envelope_handlers for connector xmpp") in caplog.text

@pytest.mark.asyncio
async def test_plugin_generic_binds_non_telegram(caplog):
    """Generic envelope loader serves any non-telegram connector."""
    target = object()
    with caplog.at_level(logging.INFO):
        await load_plugin('xmpp', 'plugin_generic', target)
        await load_plugin('discord', 'plugin_generic', target)
    generic = sys.modules["plugins.plugin_generic"].add_envelope_handlers
    assert generic.call_count == 2
    assert "Activated plugin plugin_generic for xmpp" in caplog.text
    assert "Activated plugin plugin_generic for discord" in caplog.text

@pytest.mark.asyncio
async def test_plugin_generic_skipped_on_telegram():
    """Telegram resolves only the legacy aiogram loader; the generic
    envelope loader never binds there (arbitration rule)."""
    target = object()
    await load_plugin('telegram', 'plugin_generic', target)
    sys.modules["plugins.plugin_generic"].add_envelope_handlers.assert_not_called()

@pytest.mark.asyncio
async def test_plugin_both_per_connector_wins():
    """Per-connector loader beats the generic one for that connector;
    the generic still covers connectors without an override."""
    target = object()
    mod = sys.modules["plugins.plugin_both"]

    await load_plugin('xmpp', 'plugin_both', target)
    mod.add_handlers_xmpp.assert_called_once_with(target)
    mod.add_envelope_handlers.assert_not_called()

    await load_plugin('discord', 'plugin_both', target)
    mod.add_envelope_handlers.assert_called_once_with(target)
