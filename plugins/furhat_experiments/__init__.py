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

# ~ import asyncio, glob, os, random, uuid
# ~ from urllib3.exceptions import MaxRetryError
# ~ from iacecil.controllers.furhat_bot.remote_api import (
    # ~ get_furhat,
    # ~ get_voices,
    # ~ set_face,
    # ~ set_led,
    # ~ set_voice,
    # ~ do_attend_location,
    # ~ do_attend_user,
    # ~ do_listen,
    # ~ do_say_text,
    # ~ do_say_url,
    # ~ block_do_listen,
    # ~ block_do_say_text,
    # ~ block_do_say_url,
# ~ )
# ~ from iacecil.models.furhat_models import Status
# ~ from plugins.persistence.zodb_orm import (
    # ~ get_messages_texts_list,
    # ~ get_furhat_texts_messages,
    # ~ set_furhat_text,
# ~ )
# ~ from plugins.natural import (
    # ~ generate,
    # ~ concordance,
    # ~ collocations,
    # ~ common_contexts,
    # ~ count,
    # ~ similar,
# ~ )
from iacecil import actual_name
from plugins.furhat_experiments.papagaio import papagaio
from plugins.furhat_experiments.personas import personas

try:
    from instance.config import Config
    config = Config()
    furhat_config = config.bots
except Exception as exception:
    logger.critical(u"""{} config file not found or somehow wrong. RTFM\
.\n{}""".format(actual_name, str(exception)))
    raise

async def run_papagaio(bot, skip_intro):
    await papagaio(furhat_config[bot], skip_intro = skip_intro)

async def run_personalidades(skip_intro = False):
    await personalidades(bots, skip_intro = skip_intro)
