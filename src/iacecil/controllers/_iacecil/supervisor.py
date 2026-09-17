"""Sibling process supervision for the production runtime.

The connectors used to run as a task on uvicorn's event loop, so a web
crash cancelled every bot with it. Here ZEO, the connectors and the web
app are siblings: each is a child of this supervisor and none is a child
of another, so a crash restarts only the unit that crashed (R3, R4).

Honest scope: this guards against a *child* dying. The supervisor
parents all three, so its own death leaves a later crash unrestarted.
Production supervises the supervisor itself (systemd `Restart=always`
or equivalent); that is a named dependency, not something this module
provides.

Children are spawned, never forked: a forked child would inherit the
parent's event loop and aiogram/Quart state. Configuration crosses the
process boundary as argv, and each child loads `instance/` itself (R5).

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
import multiprocessing
import signal
import socket
import time
from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Optional

logger = logging.getLogger(__name__)

START_METHOD = 'spawn'

## Restart pacing. The first failure restarts immediately; a unit that
## keeps failing waits longer each time so it cannot spin; a unit that
## ran fine for the stability window starts over from immediate.
BACKOFF_BASE = 1.0
BACKOFF_CAP = 60.0
STABILITY_WINDOW = 120.0

## How long to wait for ZEO to accept connections before starting the
## units that open storage on boot.
READY_TIMEOUT = 10.0
READY_INTERVAL = 0.5

## How long a child gets to honor SIGTERM before it is killed.
SHUTDOWN_GRACE = 10.0


@dataclass
class ChildSpec:
    """One supervised unit."""

    name: str
    target: Callable
    args: tuple = ()
    ready_check: Optional[Callable[[], bool]] = None


@dataclass
class _ChildState:
    process: object = None
    failures: int = 0
    started_at: float = 0.0
    next_attempt: float = 0.0


class Supervisor:
    """Start the units, keep them alive, and stop them together."""

    def __init__(self, specs, process_factory=None, monotonic=time.monotonic,
            sleep=time.sleep, backoff_base=BACKOFF_BASE,
            backoff_cap=BACKOFF_CAP, stability_window=STABILITY_WINDOW,
            ready_timeout=READY_TIMEOUT, ready_interval=READY_INTERVAL,
            shutdown_grace=SHUTDOWN_GRACE):
        self.specs = list(specs)
        ## Injectable so tests drive restart and backoff with fake
        ## processes and a fake clock instead of real timing.
        self._process_factory = process_factory
        self._monotonic = monotonic
        self._sleep = sleep
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.stability_window = stability_window
        self.ready_timeout = ready_timeout
        self.ready_interval = ready_interval
        self.shutdown_grace = shutdown_grace
        self.running = True
        self._state = {spec.name: _ChildState() for spec in self.specs}

    ## ------------------------------------------------------------ start

    def start(self) -> None:
        """Start every unit in order, gating on each one's readiness."""
        for spec in self.specs:
            self._spawn(spec)
            self._await_ready(spec)

    def _spawn(self, spec: ChildSpec) -> None:
        factory = self._process_factory or multiprocessing.get_context(
            START_METHOD).Process
        process = factory(target=spec.target, args=spec.args, name=spec.name)
        process.daemon = False
        process.start()
        state = self._state[spec.name]
        state.process = process
        state.started_at = self._monotonic()
        logger.info(f"Started {spec.name} unit (pid {process.pid})")

    def _await_ready(self, spec: ChildSpec) -> None:
        """Block until this unit reports ready, or the timeout expires.

        A timeout is not fatal: the units that follow open storage
        lazily and buffer failed writes, so starting them late-but-anyway
        beats deadlocking the whole tree behind one slow unit.
        """
        if spec.ready_check is None:
            return
        deadline = self._monotonic() + self.ready_timeout
        while self._monotonic() < deadline:
            if spec.ready_check():
                logger.info(f"{spec.name} unit is ready")
                return
            self._sleep(self.ready_interval)
        logger.error(
            f"{spec.name} unit not ready after {self.ready_timeout}s; "
            "starting the remaining units anyway")

    ## ------------------------------------------------------------- loop

    def supervise(self) -> None:
        """Watch the children until a signal stops the loop."""
        self._install_signal_handlers()
        while self.running:
            self.tick()
            self._sleep(self.ready_interval)
        self.shutdown()

    def tick(self) -> None:
        """One supervision pass: restart whatever died and is due."""
        if not self.running:
            return
        now = self._monotonic()
        for spec in self.specs:
            state = self._state[spec.name]
            process = state.process
            if process is None or process.is_alive():
                continue
            self._record_failure(spec, state, now)
            if now < state.next_attempt:
                continue
            logger.info(f"Restarting {spec.name} unit")
            self._spawn(spec)
            self._await_ready(spec)

    def _record_failure(self, spec, state, now) -> None:
        """Count this death once, and schedule the retry.

        Called on every tick the unit is found dead, but the failure is
        counted only when a restart was actually scheduled — otherwise a
        unit waiting out its backoff would inflate its own delay just by
        being looked at.
        """
        if state.next_attempt > state.started_at:
            return
        ran_for = now - state.started_at
        if ran_for >= self.stability_window:
            state.failures = 0
        state.failures += 1
        delay = self.backoff_for(spec.name)
        state.next_attempt = now + delay
        logger.warning(
            f"{spec.name} unit exited (code "
            f"{getattr(state.process, 'exitcode', None)}) after "
            f"{ran_for:.1f}s; restarting in {delay:.0f}s")

    def backoff_for(self, name: str) -> float:
        """Delay before the next restart of this unit.

        The first failure restarts at once — a single crash should cost
        the bots a moment, not a second of silence. Backoff starts from
        the second failure, which is where a restart loop would.
        """
        failures = self._state[name].failures
        if failures <= 1:
            return 0.0
        return min(self.backoff_base * (2 ** (failures - 2)), self.backoff_cap)

    ## --------------------------------------------------------- shutdown

    def _install_signal_handlers(self) -> None:
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, self.handle_signal)
            except ValueError:  ## pragma: no cover - not the main thread
                logger.debug(f"Cannot install handler for {sig}")

    def handle_signal(self, signum, frame) -> None:
        logger.info(f"Received signal {signum}; stopping every unit")
        self.running = False

    def shutdown(self) -> None:
        """Ask every child to stop, then make sure it did."""
        self.running = False
        for spec in self.specs:
            state = self._state[spec.name]
            process = state.process
            if process is None:
                continue
            logger.info(f"Stopping {spec.name} unit")
            process.terminate()
            process.join(self.shutdown_grace)
            if process.is_alive():
                logger.warning(
                    f"{spec.name} unit ignored SIGTERM; killing it")
                process.kill()
                process.join(self.shutdown_grace)


## ------------------------------------------------------------- units
##
## Each unit is a module-level function so `spawn` can pickle it by
## reference. They take argv rather than config objects: a spawned child
## re-reads `instance/` itself (R5).


def zeo_unit(argv) -> None:
    """Run the shared storage server."""
    from .zeo_runner import run_zeo
    run_zeo(argv)


def connector_unit(argv) -> None:
    """Run every bot's connectors, with no Quart in the process."""
    from .connectors_runner import run_app
    run_app(*argv)


def web_unit(argv) -> None:
    """Run uvicorn + Quart, with no ConnectorManager in the process."""
    import_module('iacecil.controllers._iacecil.production')


def zeo_is_ready(argv) -> Callable[[], bool]:
    """A readiness probe for the configured ZEO address.

    Connectors and web open storage on boot, so they start only once the
    server accepts connections.
    """
    def _ready() -> bool:
        address = zeo_address_from_config(argv)
        if address is None:
            ## No ZEO configured: nothing to wait for.
            return True
        try:
            with socket.create_connection(address, timeout=1.0):
                return True
        except OSError:
            return False
    return _ready


def zeo_address_from_config(argv):
    """First configured ZEO address, or None when none is enabled."""
    from .connectors_runner import load_bot_configs
    try:
        configs = load_bot_configs(list(argv))
    except Exception as exception:
        logger.warning(f"Could not load bot configs: {exception!r}")
        return None
    for config in configs.values():
        zeo = getattr(config, 'zeo', None) or {}
        if zeo.get('enabled') and zeo.get('address'):
            address = zeo['address']
            return tuple(address) if isinstance(address, list) else address
    return None


def default_specs(argv) -> list:
    """The three units, in boot order."""
    argv = list(argv)
    return [
        ChildSpec('zeo', zeo_unit, (argv,), ready_check=zeo_is_ready(argv)),
        ChildSpec('connectors', connector_unit, (argv,)),
        ChildSpec('web', web_unit, (argv,)),
    ]


def run_app(*argv) -> None:
    """Entry point: supervise the three units until signalled."""
    try:
        multiprocessing.set_start_method(START_METHOD)
    except RuntimeError:
        ## Already set by an earlier call in this process.
        logger.debug(f"Start method already set to "
            f"{multiprocessing.get_start_method()}")
    supervisor = Supervisor(default_specs(argv))
    supervisor.start()
    supervisor.supervise()
