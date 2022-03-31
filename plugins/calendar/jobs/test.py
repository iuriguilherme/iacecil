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

import datetime
from apscheduler.triggers.interval import IntervalTrigger
from iacecil.controllers.aiogram_bot.callbacks import (
    exception_callback,
)

## Test job for testing purposes
async def test_now(*args, **kwargs):
    try:
        logger.info('\n'.join([f"""agora = {datetime.datetime.now(
            pytz.timezone(kwargs['timezone']))}""",
            f"*args = {args}",
            f"**kwargs = {kwargs}",
        ]))
    except Exception as exception:
        await exception_callback(exception, ['calendar', 'testNow'])

async def get_trigger_test_now(*args, **kwargs):
    return IntervalTrigger(
        # ~ weeks = 0,
        # ~ days = 0,
        # ~ hours = 0,
        # ~ minutes = 0,
        # ~ minutes = 1,
        # ~ seconds = 0,
        # ~ start_date = None,
        # ~ end_date = None,
        # ~ timezone = pytz.timezone(kwargs['tz']),
        # ~ jitter = None,
        **kwargs,
    )
