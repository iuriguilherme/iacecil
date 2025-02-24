"""
ia.cecil

Copyleft 2012-2025 Iuri Guilherme <https://iuri.neocities.org/>

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

# ~ from pytz import utc

# ~ from apscheduler.schedulers.background import BackgroundScheduler
# ~ from apscheduler.jobstores.mongodb import MongoDBJobStore
# ~ from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# ~ from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


# ~ jobstores = {
    # ~ 'mongo': MongoDBJobStore(),
    # ~ 'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
# ~ }
# ~ executors = {
    # ~ 'default': ThreadPoolExecutor(20),
    # ~ 'processpool': ProcessPoolExecutor(5)
# ~ }
# ~ job_defaults = {
    # ~ 'coalesce': False,
    # ~ 'max_instances': 3
# ~ }
# ~ scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)

import asyncio
import json
import quart_flask_patch
import secrets
from aiogram import (
    Bot,
    Dispatcher,
    types,
)
from quart import (
    Quart,
    current_app,
    jsonify,
    render_template,
)
from ... import name
from ...controllers.aiogram_bot import (
    add_filters,
    add_handlers,
    add_jobs,
)
from .blueprints import (
    admin,
    furhat,
    plots,
    root,
)

async def add_blueprints():
    current_app.register_blueprint(
        root.blueprint,
        url_prefix = '/',
    )
    current_app.register_blueprint(
        admin.blueprint,
        url_prefix = '/admin/',
    )
    current_app.register_blueprint(
        plots.blueprint,
        url_prefix = '/plots/',
    )
    current_app.register_blueprint(
        furhat.blueprint,
        url_prefix = '/furhat/',
    )

def quart_startup(config, dispatchers):
    quart_app = Quart(
        name,
        template_folder = 'views/quart_app/templates',
        static_folder = 'views/quart_app/static',
    )
    active_page = {
        'root': '',
        'admin': '',
        'plots': '',
        'furhat': '',
    }
    ## FIXME issue #2
    ## This approach doesn't even work
    # ~ quart_app.QUART_ENV = "development"
    # ~ quart_app.DEBUG = True
    # ~ quart_app.TESTING = True
    quart_app.secret_key = secrets.token_urlsafe(32)
    quart_app.config.from_mapping(config)
    ## TODO finish testing template folders lookup
    # ~ quart_app.EXPLAIN_TEMPLATE_LOADING = True
    # ~ logger.debug(quart_app.root_path)
    # ~ logger.debug(quart_app.template_folder)
    @quart_app.before_serving
    async def quart_before_serving():
        logger.info("Starting up Quart...")
        setattr(current_app, 'quart_config', config)
        setattr(current_app, 'aiogram', False)
        setattr(current_app, 'furhat', False)
        setattr(current_app, 'dispatchers', dispatchers)
        setattr(current_app, 'active_nav', active_page)
        loop = asyncio.get_event_loop()
        for dispatcher in dispatchers:
            await add_filters(dispatcher)
            await add_handlers(dispatcher)
            await add_jobs(dispatcher)
            dispatcher.scheduler.start()
            loop.create_task(dispatcher.start_polling(
                reset_webhook = True,
                timeout = 20,
                relax = 0.1,
                fast = True,
                allowed_updates = None,
            ))
            try:
                await dispatcher.bot.send_message(
                    chat_id = dispatcher.config.telegram['users'][
                        'special']['info'],
                    text = "Mãe tá #on",
                    disable_notification = True,
                )
            except Exception as e:
                logger.warning("""logs not configured properly, did not told \
telegram group we're online""")
                logger.exception(e)
        loop.create_task(add_blueprints())
    @quart_app.after_serving
    async def quart_after_serving():
        logger.info("Shutting down Quart...")
        for dispatcher in dispatchers:
            dispatcher.scheduler.shutdown(wait = True)
            try:
                await dispatcher.bot.send_message(
                    chat_id = dispatcher.config.telegram['users'][
                        'special']['info'],
                    text = u"Mãe tá #off",
                    disable_notification = True,
                )
            except Exception as exception:
                logger.critical(u"""logs not configured properly: {}\
""".format(exception))
                raise
            await dispatcher.storage.close()
            await dispatcher.storage.wait_closed()
        ## https://docs.aiohttp.org/en/stable/client_advanced.html
        await asyncio.sleep(0.250)
    return quart_app
