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

import asyncio, json, secrets
from quart import (
    Quart,
    current_app,
    flask_patch,
    jsonify,
    render_template,
)
from aiogram import (
    Bot,
    Dispatcher,
    types,
)
from iacecil.controllers.aiogram_bot import (
    add_filters,
    add_handlers,
)
from iacecil.views.blueprints import (
    admin,
    root,
)

async def add_blueprints():
    current_app.register_blueprint(
        root.blueprint,
        url_prefix = '/',
    )
    logging.debug(root.blueprint.template_folder)
    current_app.register_blueprint(
        admin.blueprint,
        url_prefix = '/admin',
    )


def quart_startup(dispatchers):
    quart_app = Quart(
        __name__,
        # ~ template_folder = '../views/templates',
        # ~ static_folder = '../views/static',
    )
    quart_app.secret_key = secrets.token_urlsafe(32)
    @quart_app.before_serving
    async def quart_before_serving():
        logger.info("Starting up Quart...")
        setattr(current_app, 'dispatchers', dispatchers)
        loop = asyncio.get_event_loop()
        for dispatcher in dispatchers:
            await add_filters(dispatcher)
            await add_handlers(dispatcher)
            loop.create_task(dispatcher.start_polling(
                reset_webhook = True,
                timeout = 20,
                relax = 0.1,
                fast = True,
                allowed_updates = None,
            ))
            try:
                await dispatcher.bot.send_message(
                    chat_id = dispatcher.users['special']['info'],
                    text = u"Mãe tá #on",
                    disable_notification = True,
                )
            except Exception as e:
                logger.critical(u"logs not configured properly: {}\
                ".format(e))
                raise
        loop.create_task(add_blueprints())
    @quart_app.after_serving
    async def quart_after_serving():
        logger.info("Shutting down Quart...")
        for dispatcher in dispatchers:
            try:
                await dispatcher.bot.send_message(
                    chat_id = dispatcher.users['special']['info'],
                    text = u"Mãe tá #off",
                    disable_notification = True,
                )
            except Exception as e:
                logger.critical(u"logs not configured properly: {}\
                ".format(e))
                raise
    return quart_app
