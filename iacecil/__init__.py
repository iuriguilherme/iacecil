# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import logging
logger = logging.getLogger(__name__)

import os
import quart.flask_patch

### Meta
__version__ = '0.1.12.3'
name = 'iacecil'
version = __version__
commit = 0
try:
    with open(os.path.abspath('.git/HEAD')) as git_head:
        git_head.seek(5)
        with open('.git/' + git_head.read().strip('\n')) as git_ref:
            commit = git_ref.read(7)
except Exception as exception:
    logger.warning(u"git repository not found: {}".format(exception))
## Actual Name (tm)
actual_name = "ia.cecil"

logger.info(u"Starting {} v{} commit {}".format(
    actual_name,
    version,
    commit,
))

### Config
## We are not using .env
try:
    from instance.config import Config
    config = Config()
except Exception as exception:
    logger.critical(u"""{} config file not found or somehow wrong. RTFM\
.\n{}""".format(actual_name, str(exception)))
    raise

### ia.cecil
## Current implementation of script is using aiogram as middleware into 
## a quart app
try:
    from iacecil.controllers.aiogram_bot import aiogram_startup
    from iacecil.views.quart_app import quart_startup
except Exception as exception:
    logger.critical(u"{} modules not properly loaded. RTFM.\n{}".format(
        actual_name, str(exception))
    )
    raise

## Default when just importing
app = quart_startup(
    config.quart,
    aiogram_startup(
        config.aiogram,
        ['iacecil'],
    ),
)

## Default when defining all bot tokens on startup
def get_app(bots):
    return quart_startup(
        config.quart,
        aiogram_startup(
            config.aiogram,
            bots,
        ),
    )

## Default when blocking the thread
def run_app(quart_app):
    quart_app.run()
