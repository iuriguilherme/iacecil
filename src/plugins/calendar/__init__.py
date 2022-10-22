"""
Plugin calendar para ia.cecil: Grupo pra dar bom dia, boa tarde, boa noite

ia.cecil

Copyleft 2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import datetime
import pytz
from importlib import import_module
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.interval import IntervalTrigger
from iacecil.controllers.aiogram_bot.callbacks import (
    exception_callback,
)
from iacecil.controllers.util import get_job_id

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

async def add_job(job, scheduler, dispatcher, *args, **kwargs):
    try:
        job_id = (await get_job_id(
            str(dispatcher.bot.id),
            job['name'],
        ))
        timezone = pytz.timezone(dispatcher.config.timezone)
        scheduler.add_job(
            getattr(
                import_module('.'.join([
                    'plugins.calendar.jobs',
                    job['pack'],
                ])),
                job['func'],
            ),
            trigger = (await getattr(
                import_module('.'.join([
                    'plugins.calendar.jobs',
                    job['pack'],
                ])),
                'get_trigger_' + job['func'],
            )(
                timezone = timezone,
                **job['trigger'],
            )),
            args = job['args'],
            kwargs = dict(
                job['kwargs'].copy(),
                dispatcher = dispatcher,
                timezone = timezone,
            ),
            id = job_id,
            name = job['name'],
            # ~ misfire_grace_time = undefined,
            # ~ coalesce = undefined,
            # ~ max_instances = undefined,
            # ~ next_run_time = undefined,
            jobstore = 'default',
            executor = 'default',
            replace_existing = False,
        )
        if 'reschedule' in job:
            scheduler.add_job(
                getattr(
                    import_module('.'.join([
                        'plugins.calendar.jobs',
                        job['pack'],
                    ])),
                    'reschedule_' + job['func'],
                ),
                trigger = (await getattr(
                    import_module('.'.join([
                        'plugins.calendar.jobs',
                        job['pack'],
                    ])),
                    'get_trigger_' + job['func'],
                )(
                    timezone = timezone,
                    **job['reschedule'],
                )),
                args = job['args'],
                kwargs = {
                    'scheduler': scheduler,
                    'trigger': dict(
                        job['trigger'].copy(),
                        timezone = timezone,
                    ),
                    'job_id': job_id,
                },
                id = (await get_job_id(
                    str(dispatcher.bot.id),
                    'reschedule',
                    job['name'],
                )),
                name = 'reschedule_' + job['name'],
                # ~ misfire_grace_time = undefined,
                # ~ coalesce = undefined,
                # ~ max_instances = undefined,
                # ~ next_run_time = undefined,
                jobstore = 'default',
                executor = 'default',
                replace_existing = False,
            )
    except Exception as exception:
        logger.warning(repr(exception))
        # ~ raise

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
                    # ~ dispatcher.config.timezone,
                    # ~ seconds = int(message.get_args()),
                # ~ )
                # ~ command = await message.reply(u"""Adicionei o lembrete \
# ~ pra daqui a {} segundos""".format(message.get_args()))
                # ~ await command_callback(command, ['reminder',
                    # ~ message.chat.type])
        pass
    except Exception as exception:
        logger.warning(repr(exception))
        # ~ raise
