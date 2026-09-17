"""Sibling process supervision (R4, R5, R7).

The survival guarantee is structural: ZEO, the connectors and the web
app are siblings under one supervisor, so no unit is another's parent
and a crash restarts only the unit that crashed. These tests drive the
supervisor with fake processes and a fake clock, so restart and backoff
behavior is observed rather than timed.
"""

import signal

import pytest

from iacecil.controllers._iacecil.supervisor import (
    ChildSpec,
    Supervisor,
    default_specs,
)


class FakeProcess:
    """Stands in for multiprocessing.Process."""

    instances = []

    def __init__(self, target=None, args=(), kwargs=None, name=None,
            daemon=None):
        self.target = target
        self.args = args
        self.name = name
        self.daemon = daemon
        self.alive = False
        self.started = 0
        self.terminated = 0
        self.joined = 0
        self.killed = 0
        self.pid = 1000 + len(FakeProcess.instances)
        self.exitcode = None
        FakeProcess.instances.append(self)

    def start(self):
        self.alive = True
        self.started += 1

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.terminated += 1
        self.alive = False
        self.exitcode = -signal.SIGTERM

    def kill(self):
        self.killed += 1
        self.alive = False

    def join(self, timeout=None):
        self.joined += 1

    def crash(self, exitcode=1):
        self.alive = False
        self.exitcode = exitcode


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture(autouse=True)
def fresh_processes():
    FakeProcess.instances = []
    yield
    FakeProcess.instances = []


def noop(*args, **kwargs):  # child target stand-in
    return None


def build(specs=None, clock=None, **kwargs):
    specs = specs or [
        ChildSpec('zeo', noop),
        ChildSpec('connectors', noop),
        ChildSpec('web', noop),
    ]
    clock = clock or FakeClock()
    return Supervisor(specs, process_factory=FakeProcess,
        monotonic=clock.monotonic, sleep=clock.sleep, **kwargs), clock


def children_of(supervisor, name):
    return [p for p in FakeProcess.instances if p.name == name]


def test_starts_every_unit_as_a_sibling():
    """R3: no unit is another unit's parent — all three are children of
    the supervisor, started by it directly."""
    supervisor, _ = build()

    supervisor.start()

    assert sorted(p.name for p in FakeProcess.instances) == [
        'connectors', 'web', 'zeo']
    assert all(p.alive for p in FakeProcess.instances)


def test_web_crash_restarts_only_web():
    """Covers AE2: the web unit dies, the bots keep serving."""
    supervisor, _ = build()
    supervisor.start()
    zeo, connectors, web = FakeProcess.instances

    web.crash()
    supervisor.tick()

    assert len(children_of(supervisor, 'web')) == 2
    assert len(children_of(supervisor, 'connectors')) == 1
    assert len(children_of(supervisor, 'zeo')) == 1
    assert zeo.alive and connectors.alive


def test_connector_crash_restarts_only_connectors():
    """Covers AE3: brief connector downtime, self-healed."""
    supervisor, _ = build()
    supervisor.start()
    zeo, connectors, web = FakeProcess.instances

    connectors.crash()
    supervisor.tick()

    assert len(children_of(supervisor, 'connectors')) == 2
    assert len(children_of(supervisor, 'web')) == 1
    assert zeo.alive and web.alive


def _crash_and_restart(supervisor, clock, name='web'):
    """Crash the unit, then let its backoff elapse so it restarts."""
    children_of(supervisor, name)[-1].crash()
    supervisor.tick()
    clock.now += supervisor.backoff_for(name)
    supervisor.tick()


def test_first_crash_restarts_immediately():
    """One crash should cost the bots a moment, not a second of silence."""
    clock = FakeClock()
    supervisor, _ = build(clock=clock)
    supervisor.start()

    children_of(supervisor, 'web')[-1].crash()
    supervisor.tick()

    assert supervisor.backoff_for('web') == 0.0
    assert len(children_of(supervisor, 'web')) == 2


def test_repeated_crashes_back_off_exponentially():
    """A unit that cannot start must not be restarted in a hot loop."""
    clock = FakeClock()
    supervisor, _ = build(clock=clock)
    supervisor.start()

    delays = []
    for _ in range(5):
        _crash_and_restart(supervisor, clock)
        delays.append(supervisor.backoff_for('web'))

    assert delays == [0.0, 1.0, 2.0, 4.0, 8.0]


def test_backoff_delays_the_restart_rather_than_blocking():
    """While a unit waits out its backoff, the supervisor keeps
    supervising its siblings."""
    clock = FakeClock()
    supervisor, _ = build(clock=clock)
    supervisor.start()

    _crash_and_restart(supervisor, clock)       # immediate restart
    children_of(supervisor, 'web')[-1].crash()  # second failure: 1s wait
    supervisor.tick()
    assert len(children_of(supervisor, 'web')) == 2

    clock.now += 0.5
    supervisor.tick()
    assert len(children_of(supervisor, 'web')) == 2

    clock.now += 0.5
    supervisor.tick()
    assert len(children_of(supervisor, 'web')) == 3


def test_backoff_resets_after_a_stable_run():
    """A unit that ran fine for the stability window starts over, so one
    bad night does not punish it forever."""
    clock = FakeClock()
    supervisor, _ = build(clock=clock, stability_window=120.0)
    supervisor.start()

    for _ in range(3):
        _crash_and_restart(supervisor, clock)
    assert supervisor.backoff_for('web') == 2.0

    clock.now += 500.0
    children_of(supervisor, 'web')[-1].crash()
    supervisor.tick()

    assert supervisor.backoff_for('web') == 0.0


def test_backoff_is_capped():
    """However long the outage lasts, the retry interval stops growing."""
    clock = FakeClock()
    supervisor, _ = build(clock=clock, backoff_cap=4.0)
    supervisor.start()

    for _ in range(8):
        _crash_and_restart(supervisor, clock)

    assert supervisor.backoff_for('web') == 4.0


def test_zeo_readiness_gates_the_other_units():
    """Connectors and web open storage on boot; starting them before ZEO
    accepts connections is what the gate prevents."""
    ready_calls = []

    def ready():
        ready_calls.append(True)
        return len(ready_calls) >= 3

    specs = [
        ChildSpec('zeo', noop, ready_check=ready),
        ChildSpec('connectors', noop),
        ChildSpec('web', noop),
    ]
    clock = FakeClock()
    supervisor, _ = build(specs=specs, clock=clock)

    supervisor.start()

    assert len(ready_calls) == 3
    assert [p.name for p in FakeProcess.instances] == [
        'zeo', 'connectors', 'web']


def test_unready_zeo_does_not_deadlock_the_supervisor():
    """Edge: readiness never arrives. The supervisor logs and carries on
    rather than blocking forever."""
    specs = [
        ChildSpec('zeo', noop, ready_check=lambda: False),
        ChildSpec('connectors', noop),
    ]
    clock = FakeClock()
    supervisor, _ = build(specs=specs, clock=clock, ready_timeout=2.0,
        ready_interval=0.5)

    supervisor.start()

    assert [p.name for p in FakeProcess.instances] == ['zeo', 'connectors']
    assert sum(clock.slept) >= 2.0


def test_shutdown_terminates_every_child():
    """R7: SIGTERM to the supervisor reaches every unit."""
    supervisor, _ = build()
    supervisor.start()

    supervisor.shutdown()

    assert all(p.terminated == 1 for p in FakeProcess.instances)
    assert all(p.joined >= 1 for p in FakeProcess.instances)
    assert not any(p.alive for p in FakeProcess.instances)


def test_shutdown_kills_a_child_that_ignores_sigterm():
    supervisor, _ = build()
    supervisor.start()
    stubborn = FakeProcess.instances[1]
    stubborn.terminate = lambda: None  # ignores the signal

    supervisor.shutdown()

    assert stubborn.killed == 1


def test_signal_stops_the_supervise_loop():
    """The loop exits on the flag the signal handler sets, so children
    are shut down through the normal path."""
    supervisor, _ = build()
    supervisor.start()

    supervisor.handle_signal(signal.SIGTERM, None)
    supervisor.supervise()

    assert not supervisor.running
    assert all(p.terminated == 1 for p in FakeProcess.instances)


def test_dead_child_is_not_restarted_after_shutdown_begins():
    supervisor, _ = build()
    supervisor.start()
    supervisor.running = False

    FakeProcess.instances[2].crash()
    supervisor.tick()

    assert len(children_of(supervisor, 'web')) == 1


def test_default_specs_are_the_three_units_in_boot_order():
    specs = default_specs(['__main__.py', 'production'])

    assert [spec.name for spec in specs] == ['zeo', 'connectors', 'web']
    assert specs[0].ready_check is not None
    ## Config crosses the boundary by argv, never as a live object (R5)
    assert all(spec.args == (['__main__.py', 'production'],)
        for spec in specs)


def test_children_are_spawned_not_forked():
    """R5: a forked child would inherit the parent's event loop and
    aiogram/Quart state."""
    from iacecil.controllers._iacecil import supervisor as supervisor_module

    assert supervisor_module.START_METHOD == 'spawn'


def write_marker(path):
    """Child target for the real-process test (importable for spawn)."""
    import time
    with open(path, 'w') as marker:
        marker.write('alive')
    time.sleep(30)


def test_supervises_real_spawned_processes(tmp_path):
    """The fake-process tests prove the logic; this proves the wiring —
    a real spawned child starts and stops through the supervisor."""
    import multiprocessing
    import time as clock

    marker = tmp_path / 'child.marker'
    context = multiprocessing.get_context('spawn')
    supervisor = Supervisor(
        [ChildSpec('worker', write_marker, (str(marker),))],
        process_factory=context.Process,
        ready_interval=0.05)

    supervisor.start()
    try:
        deadline = clock.monotonic() + 10
        while not marker.exists() and clock.monotonic() < deadline:
            clock.sleep(0.05)
        assert marker.exists(), "spawned child never ran"
        assert supervisor._state['worker'].process.is_alive()
    finally:
        supervisor.shutdown()

    assert not supervisor._state['worker'].process.is_alive()
