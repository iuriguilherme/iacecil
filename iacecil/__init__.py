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

### Meta
__version__ = '0.1.7.3'
name = 'iacecil'
version = __version__
## Actual Name (tm)
actual_name = "ia.cecil"

### Logging
import logging
# ~ logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import quart.flask_patch

### Config
try:
    from instance.config import Config
    config = Config()
except Exception as e:
    logger.critical(u"Config file not found or somehow wrong. RTFM.\n{}\
    ".format(str(e)))
    raise

### ia.cecil
try:
    from iacecil.controllers.aiogram_bot import aiogram_startup
    from iacecil.controllers.quart_app import quart_startup
except Exception as e:
    logger.critical(u"{} modules not properly loaded. RTFM.\n{}\
    ".format(actual_name, str(e)))
    raise

app = quart_startup(aiogram_startup(config, [
    'iacecil',
    'tiodochurrasbot',
    'tiozao_bot',
    'tropixelbot',
]))

def get_app(bots):
    return quart_startup(aiogram_startup(config, bots))

def run_app(quart_app):
    quart_app.run()
