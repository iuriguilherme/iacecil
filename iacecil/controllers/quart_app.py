# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2021 Iuri Guilherme <https://iuri.neocities.org/>
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

import asyncio, json, logging
from quart import (
    Quart,
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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def quart_startup(dispatcher):
    quart_app = Quart(
        __name__,
        template_folder = '../views/templates',
    )
    @quart_app.before_serving
    async def quart_before_serving():
        logger.info("Starting up Quart...")
        loop = asyncio.get_event_loop()
        await add_filters(dispatcher)
        await add_handlers(dispatcher)
        loop.create_task(dispatcher.start_polling(
            reset_webhook = True,
            timeout = 20,
            relax =0.1,
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
            logging.critical(u"logs not configured properly: {}\
            ".format(e))
    @quart_app.after_serving
    async def quart_after_serving():
        logger.info("Shutting down Quart...")
        try:
            await dispatcher.bot.send_message(
                chat_id = dispatcher.users['special']['info'],
                text = u"Mãe tá #off",
                disable_notification = True,
            )
        except Exception as e:
            logging.critical(u"logs not configured properly: {}\
            ".format(e))
    @quart_app.route("/")
    async def quart_webapp():
        return u"Hello Quart"
    @quart_app.route("/status")
    async def quart_status():
        return jsonify(dispatcher.is_polling())
    @quart_app.route("/get_me")
    async def get_me():
        user = await dispatcher.bot.get_me()
        return await render_template(
            "get_me.html",
            title = user['first_name'],
            user = user,
        )
    @quart_app.route("/send_message/<chat_id>/<text>")
    async def send_message(chat_id=1, text=u"Nada"):
        user = await dispatcher.bot.get_me()
        message = await dispatcher.bot.send_message(
            chat_id = chat_id,
            text = text,
        )
        return await render_template(
            "send_message.html",
            title = user['first_name'],
            message = message,
        )
    return quart_app
