"""
Plugin calendar para ia.cecil: Grupo pra dar bom dia, boa tarde, boa noite

ia.cecil

Copyleft 2025 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
logger = logging.getLogger(__name__)

import random
import uuid
from aiogram import Dispatcher
from apscheduler.triggers.cron import CronTrigger
from iacecil.controllers.aiogram_bot.callbacks import (
    exception_callback,
)

async def bom_dia(*args, **kwargs):
    try:
        for group in kwargs['groups']:
            await kwargs['dispatcher'].bot.send_message(
                chat_id = group,
                text = kwargs['message'],
            )
    except Exception as exception:
        await exception_callback(exception, ['calendar'], ['bomDia'])

async def get_trigger_bom_dia(*args, **kwargs):
    ## Randomize minute every reschedule to mimic human behaviour
    ## At least non english humans
    return CronTrigger(minute = random.randint(1, 59), **kwargs)

async def reschedule_bom_dia(*args, **kwargs):
    trigger = await get_trigger_bom_dia(**kwargs['trigger'])
    kwargs['scheduler'].reschedule_job(
        kwargs['job_id'],
        jobstore = 'default',
        trigger = trigger,
    )
