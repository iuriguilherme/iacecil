"""How a ZODB storage is opened, for every clean-layer store.

Two modes, chosen by ``zeo_address``:

- Unset (the default): open ``FileStorage`` at the given path, exactly
  as before. One process may hold it, because FileStorage takes an
  exclusive lock.
- Set: connect to the ZEO server at that address and ask for a named
  storage. Several processes may connect, which is what lets the
  connector unit and the web unit run separately (R9, R10 of
  docs/plans/2026-06-24-001-refactor-decouple-web-survival-slice1-plan.md).

Storage names are fixed when the ZEO server starts: ``people``,
``messages``, and one ``chats_<bot_id>`` per configured bot. Nothing
here may invent a name at runtime — a ZEO server serves only the
storages its own configuration names.

Both modes wrap the storage in ZlibStorage, so data written in one mode
stays readable in the other.
"""

import logging
import os

import zc.zlibstorage
import ZODB
import ZODB.FileStorage

logger = logging.getLogger(__name__)

## Module-level so the config layer and the test fixtures can repoint it,
## the same way zodb_path is repointed on neutral and chat_store.
zeo_address = None


def configure(zeo_conf) -> None:
    """Point every store at a ZEO server, or back at local files.

    Called once per process at startup with a bot config's ``zeo``
    section. Anything falsy, or ``enabled`` false, leaves storage local,
    so a single-process deployment needs no config change.
    """
    global zeo_address
    if not zeo_conf or not zeo_conf.get('enabled'):
        zeo_address = None
        return
    address = zeo_conf.get('address')
    if not address:
        logger.warning(
            "zeo enabled without an address; using local storage")
        zeo_address = None
        return
    zeo_address = tuple(address) if isinstance(address, list) else address
    logger.info(f"Persistence connecting to ZEO at {zeo_address}")


def storage_name_for_bot(bot_id: str) -> str:
    """Name of the storage holding one bot's chats."""
    from .path_utils import sanitize_component
    return 'chats_{}'.format(sanitize_component(bot_id))


def open_db(path: str, storage_name=None, read_only: bool = False,
        wait: bool = True) -> ZODB.DB:
    """Open one storage as a ZODB.DB.

    ``storage_name`` is the name the ZEO server serves it under. Without
    one — legacy stores, which keep their own per-chat layout — the
    FileStorage path is used even when ZEO is configured.
    """
    if zeo_address is not None and storage_name is not None:
        base = _client_storage(storage_name, read_only=read_only, wait=wait)
    else:
        base = _file_storage(path, read_only=read_only)
    return ZODB.DB(zc.zlibstorage.ZlibStorage(base))


def _client_storage(storage_name: str, read_only: bool, wait: bool):
    ## Imported lazily: a deployment that never enables ZEO does not need
    ## the server package importable at startup.
    import ZEO.ClientStorage
    logger.debug(
        f"Opening ZEO storage {storage_name} at {zeo_address}")
    return ZEO.ClientStorage.ClientStorage(
        _address(), storage=storage_name, read_only=read_only, wait=wait)


def _address():
    """ZEO takes a (host, port) tuple or a socket path."""
    if isinstance(zeo_address, (list, tuple)):
        return tuple(zeo_address)
    return zeo_address


def _file_storage(path: str, read_only: bool):
    try:
        return ZODB.FileStorage.FileStorage(path, read_only=read_only)
    except FileNotFoundError:
        ## A read-only open of a store that was never written is a real
        ## error; only the writer creates directories.
        if read_only:
            raise
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return ZODB.FileStorage.FileStorage(path)
