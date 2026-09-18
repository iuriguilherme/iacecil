"""The defining survival guarantee (R3, R4, AE1, AE2, AE3).

Kill the web process; the bots keep serving. Everything else in slice 1
exists to make this true, so this test uses real spawned processes, real
signals and a real ZEO server rather than fakes.

The children are stand-ins for the three units, not the units
themselves: booting the real connector unit would need live credentials
and would talk to real networks. What they reproduce is the structure
that the guarantee depends on — siblings under one supervisor, storage
shared through ZEO, no unit parented by another.
"""

import multiprocessing
import os
import signal
import time

import pytest

from iacecil.controllers._iacecil.supervisor import ChildSpec, Supervisor

## Each step waits for an observable state change rather than sleeping a
## fixed time, with a ceiling so a broken run fails instead of hanging.
TIMEOUT = 20.0
POLL = 0.05


class Config:
    """Minimal stand-in for a BotConfig's zeo section."""

    def __init__(self, port):
        self.zeo = {'enabled': True, 'address': ['127.0.0.1', port]}


def zeo_child(zodb_path, port):
    """The storage unit."""
    from iacecil.controllers._iacecil import zeo_runner

    address, stop = zeo_runner.start_server({'mybot': Config(port)},
        zodb_path)
    try:
        while True:
            time.sleep(0.2)
    finally:
        stop()


def connector_child(zodb_path, port, marker_dir):
    """The connector unit: keeps working, and proves it by writing.

    Each loop stores one message through the real chat store, so
    "still serving" means records actually landing in shared storage,
    not merely a process still existing.
    """
    import asyncio

    import iacecil.controllers.persistence.chat_store as chat_store
    import iacecil.controllers.persistence.storage as storage
    from iacecil.models.envelope import Envelope

    storage.zeo_address = ('127.0.0.1', port)
    chat_store.zodb_path = zodb_path
    counter = 0

    async def serve():
        nonlocal counter
        while True:
            await chat_store.store_message('mybot', Envelope(
                'loopback', 'user1', 'local_chat', f'message {counter}'))
            counter += 1
            with open(os.path.join(marker_dir, 'connector.alive'), 'w') as f:
                f.write(f"{os.getpid()} {counter}")
            await asyncio.sleep(0.1)

    asyncio.run(serve())


def web_child(marker_dir):
    """The web unit: it only has to exist, and to be killable."""
    with open(os.path.join(marker_dir, 'web.alive'), 'w') as marker:
        marker.write(str(os.getpid()))
    while True:
        time.sleep(0.2)


def wait_for(predicate, timeout=TIMEOUT, what='condition'):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(POLL)
    raise AssertionError(f"timed out waiting for {what}")


def read_marker(marker_dir, name):
    path = os.path.join(marker_dir, name)
    try:
        with open(path) as marker:
            return marker.read()
    except FileNotFoundError:
        return None


def free_port():
    import socket

    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


@pytest.fixture
def running_units(tmp_path):
    """The three units, spawned and supervised for real."""
    zodb_path = str(tmp_path / 'zodb')
    markers = tmp_path / 'markers'
    markers.mkdir()
    port = free_port()

    context = multiprocessing.get_context('spawn')
    supervisor = Supervisor([
        ChildSpec('zeo', zeo_child, (zodb_path, port)),
        ChildSpec('connectors', connector_child,
            (zodb_path, port, str(markers))),
        ChildSpec('web', web_child, (str(markers),)),
    ], process_factory=context.Process, ready_interval=POLL)

    supervisor.start()
    try:
        wait_for(lambda: read_marker(markers, 'connector.alive'),
            what='the connector unit to start serving')
        wait_for(lambda: read_marker(markers, 'web.alive'),
            what='the web unit to start')
        yield supervisor, markers
    finally:
        supervisor.shutdown()


def pid_of(supervisor, name):
    return supervisor._state[name].process.pid


def records_written(markers):
    marker = read_marker(markers, 'connector.alive')
    return int(marker.split()[1]) if marker else 0


def test_killing_the_web_process_leaves_the_connectors_serving(
        running_units):
    """Covers AE1 — the defining test of the whole slice.

    SIGKILL rather than SIGTERM: a crash, not a shutdown.
    """
    supervisor, markers = running_units
    connector_pid = pid_of(supervisor, 'connectors')
    zeo_pid = pid_of(supervisor, 'zeo')
    written_before = records_written(markers)

    os.kill(pid_of(supervisor, 'web'), signal.SIGKILL)

    ## The bots keep storing messages while the web process is gone
    wait_for(lambda: records_written(markers) > written_before + 2,
        what='the connectors to keep serving after the web process died')
    assert pid_of(supervisor, 'connectors') == connector_pid
    assert pid_of(supervisor, 'zeo') == zeo_pid


def test_supervisor_restarts_only_the_web_child(running_units):
    """Covers AE2."""
    supervisor, markers = running_units
    connector_pid = pid_of(supervisor, 'connectors')
    zeo_pid = pid_of(supervisor, 'zeo')
    web_pid = pid_of(supervisor, 'web')

    os.kill(web_pid, signal.SIGKILL)
    wait_for(lambda: (supervisor.tick(), pid_of(supervisor, 'web'))[1]
        != web_pid, what='the supervisor to restart the web unit')

    assert pid_of(supervisor, 'web') != web_pid
    assert pid_of(supervisor, 'connectors') == connector_pid
    assert pid_of(supervisor, 'zeo') == zeo_pid
    assert supervisor._state['web'].process.is_alive()


def test_a_crashed_connector_unit_is_restarted_alone(running_units):
    """Covers AE3: brief connector downtime, then self-healed."""
    supervisor, markers = running_units
    connector_pid = pid_of(supervisor, 'connectors')
    web_pid = pid_of(supervisor, 'web')

    os.kill(connector_pid, signal.SIGKILL)
    wait_for(lambda: (supervisor.tick(),
        pid_of(supervisor, 'connectors'))[1] != connector_pid,
        what='the supervisor to restart the connector unit')

    ## It serves again after the restart
    written = records_written(markers)
    wait_for(lambda: records_written(markers) > written,
        what='the restarted connector unit to serve again')
    assert pid_of(supervisor, 'web') == web_pid


def test_records_written_across_the_split_are_readable_afterwards(
        running_units, monkeypatch):
    """Covers AE5: one process writes, another reads, no lock crash.

    This is the test that would have failed under FileStorage, whose
    exclusive lock is what made the process split impossible.
    """
    supervisor, markers = running_units
    import iacecil.controllers.persistence.chat_store as chat_store
    import iacecil.controllers.persistence.storage as storage

    wait_for(lambda: records_written(markers) > 1,
        what='the connector unit to store messages')
    _, port = supervisor.specs[0].args

    monkeypatch.setattr(storage, 'zeo_address', ('127.0.0.1', port))
    db = storage.open_db('unused', storage.storage_name_for_bot('mybot'))
    try:
        with db.transaction() as connection:
            chat = connection.root.chats[
                chat_store._chat_key('loopback', 'local_chat')]
            assert len(chat['messages']) > 0
    finally:
        db.close()


def test_shutdown_stops_every_unit(running_units):
    """R7: one SIGTERM to the supervisor ends the whole tree."""
    supervisor, markers = running_units

    supervisor.shutdown()

    for name in ('zeo', 'connectors', 'web'):
        assert not supervisor._state[name].process.is_alive(), name
