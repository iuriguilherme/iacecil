"""
ia.cecil

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
import sys

logger = logging.getLogger(__name__)

def _cwd_is_trusted(path):
    """True when ``path`` is safe to add to ``sys.path``.

    A world-writable or foreign-owned directory could contain an
    attacker-planted ``instance`` package that would execute on import, so we
    only trust directories owned by the current user and not writable by
    others. On platforms without POSIX ownership (no ``os.geteuid``) we defer
    to the OS file ACLs and trust the path.
    """
    try:
        st = os.stat(path)
    except OSError:
        return False
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None:
        return True
    return st.st_uid == geteuid() and not (st.st_mode & 0o002)

def main():
    try:
        # The runtime expects to be invoked from the project root, where the
        # local-only ``instance`` package and ``.git`` live. PEP 660 editable
        # installs (and wheels) only expose ``src`` on ``sys.path``, so add the
        # working directory back to keep ``import instance`` working. Append,
        # not insert(0): cwd must not shadow installed/stdlib packages (e.g.
        # the shipped ``plugins`` package) — we only need it to resolve
        # ``instance``, which has no installed counterpart. Only do this for a
        # trusted cwd: a world-writable or foreign-owned directory could hold a
        # planted ``instance`` package that runs arbitrary code on import.
        cwd = os.getcwd()
        if _cwd_is_trusted(cwd):
            if cwd not in sys.path:
                sys.path.append(cwd)
        else:
            # cwd is world-writable or foreign-owned. Python itself prepends
            # cwd (as '' under ``python -m`` / direct script runs) to
            # sys.path, so a planted ``instance`` module there would execute
            # on import. Strip every cwd-equivalent entry rather than trust it.
            for entry in ('', os.curdir, cwd):
                while entry in sys.path:
                    sys.path.remove(entry)
            logger.warning(f"""Untrusted working directory {cwd!r} (world-\
writable or not owned by the current user); removed it from sys.path. \
'import instance' will fail here — run iacecil from your own project root.""")
        from . import __name__, __version__
        try:
            logger.critical(f"""Running {__name__} v{__version__} with \
args: {sys.argv[1:]}""")
        except:
            logger.critical(f"Running {__name__} {__version__}")
        if len(sys.argv) > 1:
            if (sys.argv[1] in \
                ['production', 'staging']) or \
                os.environ.get('ENV', None) in ['production', 'staging']:
                from .controllers._iacecil import production
            elif (sys.argv[1] in ['fpersonas']):
                from .controllers._iacecil import fpersonas
            elif (sys.argv[1] in ['connectors']):
                from .controllers._iacecil.connectors_runner import run_app
                run_app(*sys.argv)
            elif (sys.argv[1] in ['connectors_v3']):
                from .controllers._iacecil.connectors_v3_runner import run_app
                run_app(*sys.argv)
            elif (sys.argv[1] in [
            'chatgpt',
            'furhat',
            'furhatgpt',
            ]):
                from .controllers._iacecil import furhatgpt
            else:
                from .controllers._iacecil.testing import run_app
                run_app(*sys.argv)
        else:
            logger.info("No arguments provided, using testing mode")
            from .controllers._iacecil.testing import run_app
            run_app(*sys.argv)
    except Exception as e:
        logger.exception(e)
        sys.exit("RTFM")

if __name__ == "__main__":
    main()
