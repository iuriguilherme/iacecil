"""Shared storage server: `python -m iacecil zeo`, or the supervisor's
ZEO child.

FileStorage takes an exclusive lock, so only one process can open a
`.fs` file. With the connectors and the web app in separate processes,
both need the same data, so a ZEO server owns the files and both units
connect to it as clients (R9).

A ZEO server serves only the storages its configuration names, and that
set is fixed when it starts. The chat store therefore keeps one storage
per bot rather than one per chat (R13): a chat that first appears at
runtime lands in a storage the server already serves, and adding a *bot*
is what requires a restart.

Storage names:

    people          the Person registry
    messages        the global neutral records
    chats_<bot_id>  one per configured bot

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
import os
import signal
import time

logger = logging.getLogger(__name__)

DEFAULT_ADDRESS = ('localhost', 8100)
DEFAULT_ZODB_PATH = 'instance/zodb'


def storage_paths(configs: dict, zodb_path: str = DEFAULT_ZODB_PATH) -> dict:
    """Every storage this server will serve, as {name: path}.

    Built from configuration at startup and never added to afterwards,
    which is what R13's consolidation makes possible.
    """
    from iacecil.controllers.persistence.chat_store import chat_db_path
    from iacecil.controllers.persistence.storage import storage_name_for_bot
    base = os.path.abspath(zodb_path)
    storages = {
        'people': os.path.join(base, 'people.fs'),
        'messages': os.path.join(base, 'messages.fs'),
    }
    for bot_id in (configs or {}):
        ## chat_db_path owns this layout. Joining it here instead would
        ## skip the sanitizer, and a bot id with an uppercase letter or
        ## an `@` would be served from a different file than the one the
        ## chat store writes when ZEO is off.
        storages[storage_name_for_bot(bot_id)] = chat_db_path(
            bot_id, zodb_path)
    return storages


def storage_conf(storages: dict) -> str:
    """The ZEO storage configuration for those storages."""
    sections = []
    for storage_name, path in storages.items():
        sections.append(
            "<filestorage {name}>\n  path {path}\n</filestorage>".format(
                name=storage_name, path=path))
    return "\n".join(sections) + "\n"


def zeo_address(configs: dict):
    """The first configured ZEO address, or the default."""
    from iacecil.controllers.persistence.storage import address_from_configs
    address = address_from_configs(configs)
    return address if address is not None else DEFAULT_ADDRESS


def prepare_directories(storages: dict) -> None:
    """Create each storage's directory before the server opens it."""
    for path in storages.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)


def start_server(configs: dict, zodb_path: str = DEFAULT_ZODB_PATH):
    """Start the storage server. Returns (address, stop)."""
    import ZEO

    storages = storage_paths(configs, zodb_path)
    prepare_directories(storages)
    address = zeo_address(configs)
    host, port = address if isinstance(address, tuple) else (address, 0)
    if host not in ('localhost', '127.0.0.1'):
        ## The server always binds loopback this slice; exposing it on a
        ## network needs authentication, which is later work. Say so
        ## rather than silently ignoring the configured host.
        logger.warning(
            f"ZEO binds loopback only; configured host {host} is ignored")
    logger.info(
        f"Starting ZEO on 127.0.0.1:{port} serving {sorted(storages)}")
    return ZEO.server(
        storage_conf=storage_conf(storages),
        port=port,
        threaded=True,
    )


def run_zeo(argv=None) -> None:
    """Run the storage server until signalled.

    The supervisor spawns this as a child, so it reads `instance/`
    itself rather than receiving live config objects.
    """
    from .connectors_runner import load_bot_configs

    argv = list(argv or [])
    configs = load_bot_configs(argv)
    address, stop = start_server(configs)
    logger.info(f"ZEO serving at {address}")

    running = {'value': True}

    def handle_signal(signum, frame):
        logger.info(f"ZEO received signal {signum}; stopping")
        running['value'] = False

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, handle_signal)
        except ValueError:  ## pragma: no cover - not the main thread
            logger.debug(f"Cannot install handler for {sig}")

    try:
        while running['value']:
            time.sleep(0.5)
    finally:
        logger.info("Stopping ZEO")
        stop()
