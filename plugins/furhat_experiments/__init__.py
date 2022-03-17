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

from iacecil import actual_name
from plugins.furhat_experiments.papagaio import papagaio
from plugins.furhat_experiments.personas import personas

try:
    from instance.config import Config
    config = Config()
    bots_config = config.bots
    furhat_config = config.furhat
except Exception as exception:
    logger.critical(u"""{} config file not found or somehow wrong. RTFM\
.\n{}""".format(actual_name, str(exception)))
    raise

## This one just repeats everything that's being said
async def run_papagaio(bot, skip_intro):
    await papagaio(bots_config[bot], skip_intro = skip_intro)

## This one process messages using iacecil's personalities
async def run_personas(bots, *args, **kwargs):
    await personas(bots, furhat_config, bots_config, *args, **kwargs)
