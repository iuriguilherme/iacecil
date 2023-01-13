"""
ia.cecil

Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>

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
import natsort
import os

## FIXME: Chupa
logging.basicConfig(level = "INFO")
logger = logging.getLogger(__name__)

name: str = 'iacecil'
description: str = "Chatbot framework and set of tools"
version: str = '0.0.0.0'
commit: str = '0000000'

try:
    from . import _version
    version: str = _version.__version__
except Exception as e:
    logger.debug(f"""Unable to get version from _version file, using \
{version}""")
    # ~ logger.exception(e)
try:
    ## Using latest git tag as version
    version: str = [tag for tag in \
        natsort.natsorted(os.listdir('.git/refs/tags')) \
        if tag not in ['alpha', 'beta', 'latest', 'pre-alpha', 'stable']][-1]
except Exception as e:
    logger.debug(f"Latest git tag not found, version will be {version}")
    # ~ logger.exception(e)

try:
    ## Lookup latest commit hash
    with open(os.path.abspath('.git/HEAD')) as git_head:
        git_head.seek(5)
        with open('.git/' + git_head.read().strip('\n')) as git_ref:
            commit = git_ref.read(7)
except Exception as e:
    logger.debug(f"git repository not found, commit will be {commit}")
    # ~ logger.exception(e)

__name__: str = name
__version__: str = version
__description__: str = description

__all__: list = [
    name,
    commit,
    __version__,
    __description__,
    'config',
    'controllers',
    'models',
    'views',
    # ~ 'plugins',
]
