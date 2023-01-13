"""
ia.cecil

Copyleft 2012-2023 Iuri Guilherme <https://iuri.neocities.org/>

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

try:
    from . import __name__, __version__
    try:
        logger.critical(f"""Running {__name__} v{__version__} with args: \
{sys.argv[1:]}""")
    except:
        logger.critical(f"Running {__name__} {__version__}")
    if (len(sys.argv) > 1 and sys.argv[1] in ['production', 'staging']) or \
        os.environ.get('ENV', None) in ['production', 'staging']:
        from .controllers._iacecil import production
    elif (len(sys.argv) > 1 and sys.argv[1] in ['fpersonas']):
        from .controllers._iacecil import fpersonas
    else:
        from .controllers._iacecil.testing import run_app
        run_app(*sys.argv)
except Exception as e:
    logger.exception(e)
    sys.exit("RTFM")
