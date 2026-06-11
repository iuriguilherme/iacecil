import pytest
import sys
import types
import logging
from unittest.mock import AsyncMock

from iacecil.controllers._iacecil.connectors_runner import (
    build_managers,
    load_bot_configs,
    run_managers,
)


def test_load_bot_configs_without_instance_falls_back(monkeypatch, caplog):
    """Missing instance/_bots.py must not raise; runner falls back to
    the built-in default config under the 'default' bot name."""
    ## A None entry in sys.modules makes the import raise — simulates a
    ## machine without local instance/ files regardless of this one.
    monkeypatch.setitem(sys.modules, "instance._bots", None)
    monkeypatch.setitem(sys.modules, "instance.bots", None)
    monkeypatch.setitem(sys.modules, "instance.bots.default", None)
    with caplog.at_level(logging.ERROR):
        configs = load_bot_configs(['python', 'connectors'])
    assert 'default' in configs


def test_load_bot_configs_two_bots(monkeypatch):
    _bots = types.ModuleType("instance._bots")
    _bots.bots = ['alpha', 'beta']
    monkeypatch.setitem(sys.modules, "instance", types.ModuleType("instance"))
    monkeypatch.setitem(sys.modules, "instance._bots", _bots)
    bots_pkg = types.ModuleType("instance.bots")
    monkeypatch.setitem(sys.modules, "instance.bots", bots_pkg)

    class FakeBotConfig:
        pass
    for name in ('alpha', 'beta'):
        mod = types.ModuleType(f"instance.bots.{name}")
        mod.BotConfig = FakeBotConfig
        monkeypatch.setitem(sys.modules, f"instance.bots.{name}", mod)

    configs = load_bot_configs(['python', 'connectors'])
    assert set(configs) == {'alpha', 'beta'}


def test_build_managers_isolates_bot_failure(monkeypatch, caplog):
    """One bot's manager construction failing must not stop siblings."""
    import iacecil.controllers._iacecil.connectors_runner as runner_mod
    import iacecil.connectors as connectors_pkg

    built = []

    class FakeManager:
        def __init__(self, config, bot_id="default"):
            if config.get('boom'):
                raise ValueError("bad config")
            self.bot_id = bot_id
            built.append(bot_id)

    monkeypatch.setattr(connectors_pkg, 'ConnectorManager', FakeManager)
    with caplog.at_level(logging.ERROR):
        managers = build_managers({
            'good': {'loopback': {'enabled': True}},
            'bad': {'boom': True},
        })
    assert built == ['good']
    assert len(managers) == 1
    assert "Failed to build manager for bot bad" in caplog.text


@pytest.mark.asyncio
async def test_run_managers_logs_crashed_bot(caplog):
    class FakeManager:
        def __init__(self, bot_id, crash=False):
            self.bot_id = bot_id
            self.crash = crash

        async def run_all(self):
            if self.crash:
                raise RuntimeError("runtime boom")

    good = FakeManager('good')
    bad = FakeManager('bad', crash=True)
    with caplog.at_level(logging.ERROR):
        await run_managers([good, bad])
    assert "Bot bad crashed" in caplog.text
    assert "Bot good crashed" not in caplog.text
