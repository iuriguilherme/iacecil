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

import datetime, pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.interval import IntervalTrigger
# ~ from iacecil.controllers.aiogram_bot.callbacks import (
    # ~ command_callback,
    # ~ message_callback,
    # ~ error_callback,
    # ~ exception_callback,
# ~ )

# ~ async def bom_dia(dispatcher, message = u"bom dia"):
    # ~ for group in dispatcher.bot.config['telegram']['users']['bomdia']:
        # ~ try:
            # ~ dispatcher.bot.send_message(group, message)
        # ~ except Exception as exception:
            # ~ await exception_callback(exception, ['bomdia'])

## Test job for testing purposes
async def test_now(*args, **kwargs):
    logger.info('\n'.join([
        f"agora = {datetime.datetime.now(pytz.timezone(kwargs['tz']))}",
        f"*args = {args}",
        f"**kwargs = {kwargs}",
    ]))

async def job_test_now(*args, **kwargs):
    trigger_args = dict(
        weeks = 0,
        days = 0,
        hours = 0,
        # ~ minutes = 0,
        minutes = 1,
        seconds = 0,
        start_date = None,
        end_date = None,
        timezone = pytz.timezone(kwargs['tz']),
        jitter = None,
    )
    trigger = IntervalTrigger(**trigger_args)
    return test_now, dict(
        trigger = trigger,
        args = args,
        kwargs = kwargs,
        id = None,
        name = None,
        # ~ misfire_grace_time = undefined,
        # ~ coalesce = undefined,
        # ~ max_instances = undefined,
        # ~ next_run_time = undefined,
        jobstore = 'default',
        executor = 'default',
        replace_existing = False,
        **trigger_args,
    )

allowed_jobs = {
    'test_now': job_test_now,
}

def get_scheduler():
    try:
        return AsyncIOScheduler(
            jobstores = {
                'default': MemoryJobStore(),
            },
            executors = {
                'default': AsyncIOExecutor(),
            },
            # ~ event_loop = asyncio.get_current_loop(),
        )
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def add_job(job, scheduler, *args, **kwargs):
    try:
        the_job = await allowed_jobs[job['name']](*job['args'],
            **kwargs, **job['kwargs'])
        scheduler.add_job(the_job[0], **the_job[1])
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def add_handlers(dispatcher):
    try:
        # ~ @dispatcher.message_handler(commands = ['lembrete', 'lembra',
            # ~ 'reminder', 'remind'])
        # ~ async def reminder_callback(message):
            # ~ await message_callback(message, ['reminder',
                # ~ message.chat.type])
            # ~ if message.get_args() not in [None, '', ' '] and \
                # ~ message.get_args().isdigit():
                # ~ await add_job('reminder', dispatcher.scheduler,
                    # ~ dispatcher.config['info']['timezone'],
                    # ~ seconds = int(message.get_args()),
                # ~ )
                # ~ command = await message.reply(u"""Adicionei o lembrete \
# ~ pra daqui a {} segundos""".format(message.get_args()))
                # ~ await command_callback(command, ['reminder',
                    # ~ message.chat.type])
        pass
    except Exception as exception:
        logger.warning(repr(exception))
        raise
