"""The connector unit announces its own liveness (R12, AE7).

The "Mãe tá #on/#off" ping used to fire from the web app's serving
hooks, so it reported that *the web layer* was up. With the web layer
gone from this process, the ping fires here — and until slice 2's health
view exists, it is the operator's only in-chat liveness signal, so it
has to mean connector liveness.
"""

import asyncio

import pytest

from iacecil.controllers._iacecil import connectors_runner
from iacecil.models.envelope import Envelope


class FakeConnector:
    def __init__(self, running=True):
        self.running = running


class FakeManager:
    """Enough ConnectorManager for the liveness path."""

    def __init__(self, bot_id='mybot', info_chat='12345',
            connectors=('telegram',), running=True, send_error=None):
        self.bot_id = bot_id
        self.sent = []
        self.send_error = send_error
        self.connectors = {name: FakeConnector(running)
            for name in connectors}
        telegram = {'token': '1:a'}
        if info_chat is not None:
            telegram['users'] = {'special': {'info': info_chat}}
        self._conf = {'telegram': telegram}
        self.ran = False

    def _config_as_dict(self):
        return self._conf

    async def send(self, envelope):
        if self.send_error:
            raise self.send_error
        self.sent.append(envelope)
        return True

    async def run_all(self):
        self.ran = True
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_online_ping_is_sent_when_connectors_come_up():
    """Covers AE7."""
    manager = FakeManager()

    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_ON)

    assert [envelope.text for envelope in manager.sent] == ['Mãe tá #on']
    assert manager.sent[0].platform == 'telegram'
    assert manager.sent[0].conversation_ref == '12345'


@pytest.mark.asyncio
async def test_offline_ping_is_sent_on_shutdown():
    """Covers AE7."""
    manager = FakeManager()

    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_OFF)

    assert [envelope.text for envelope in manager.sent] == ['Mãe tá #off']


@pytest.mark.asyncio
async def test_no_ping_without_a_configured_operator_chat():
    """A bot that never configured the info chat is not an error."""
    manager = FakeManager(info_chat=None)

    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_ON)

    assert manager.sent == []


@pytest.mark.asyncio
async def test_no_ping_without_a_telegram_connector():
    manager = FakeManager(connectors=('xmpp',))

    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_ON)

    assert manager.sent == []


@pytest.mark.asyncio
async def test_a_failed_ping_does_not_stop_the_connectors():
    """Edge: the ping is best-effort. Bots serving matters more than an
    operator notification."""
    manager = FakeManager(send_error=RuntimeError('telegram is down'))

    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_ON)

    assert manager.sent == []


@pytest.mark.asyncio
async def test_ping_waits_for_the_connector_to_come_up():
    """Sending before connect() finishes would silently drop."""
    manager = FakeManager(running=False)

    async def come_up_later():
        await asyncio.sleep(0.05)
        manager.connectors['telegram'].running = True

    asyncio.create_task(come_up_later())
    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_ON, timeout=2.0)

    assert [envelope.text for envelope in manager.sent] == ['Mãe tá #on']


@pytest.mark.asyncio
async def test_a_connector_that_never_comes_up_times_out():
    """The announcement must not hold the runner open forever."""
    manager = FakeManager(running=False)

    await connectors_runner.announce_liveness(
        [manager], connectors_runner.LIVENESS_ON, timeout=0.2)

    assert manager.sent == []


@pytest.mark.asyncio
async def test_run_managers_announces_on_and_off_around_the_run():
    """Covers AE7 end to end through the runner's own lifecycle."""
    manager = FakeManager()

    await connectors_runner.run_managers([manager])

    assert manager.ran
    assert [envelope.text for envelope in manager.sent] == [
        'Mãe tá #on', 'Mãe tá #off']


@pytest.mark.asyncio
async def test_offline_ping_fires_even_when_a_bot_crashed():
    """A crash is exactly when the operator wants to hear #off."""
    class CrashingManager(FakeManager):
        async def run_all(self):
            raise RuntimeError('bot exploded')

    manager = CrashingManager()

    await connectors_runner.run_managers([manager])

    assert 'Mãe tá #off' in [envelope.text for envelope in manager.sent]


def test_web_app_no_longer_sends_it():
    """R12: exactly one process owns this signal."""
    import inspect

    from iacecil.views.quart_app import quart_startup

    source = inspect.getsource(quart_startup)
    assert 'send_message' not in source


def test_liveness_envelope_is_marked_as_outbound_operator_traffic():
    """Tagging keeps an operator ping out of conversation analytics."""
    envelope = connectors_runner.liveness_envelope('12345',
        connectors_runner.LIVENESS_ON)

    assert isinstance(envelope, Envelope)
    assert 'liveness' in envelope.tags


@pytest.mark.asyncio
async def test_a_slow_bot_does_not_delay_the_others():
    """One bot whose connector never comes up must not hold the
    announcement for every bot behind it."""
    slow = FakeManager(bot_id='slow', running=False)
    quick = FakeManager(bot_id='quick')

    await connectors_runner.announce_liveness(
        [slow, quick], connectors_runner.LIVENESS_ON, timeout=0.3)

    assert [envelope.text for envelope in quick.sent] == ['Mãe tá #on']
    assert slow.sent == []
