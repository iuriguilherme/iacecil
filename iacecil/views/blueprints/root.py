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

import logging
from quart import (
    abort,
    Blueprint,
    current_app,
    jsonify,
    request,
    render_template,
)
from jinja2 import TemplateNotFound
from iacecil import name, version

logger = logging.getLogger('blueprints.root')

blueprint = Blueprint('root', 'index')

@blueprint.route('/', defaults={'page': 'index'})
@blueprint.route('/<page>')
async def show(page):
    try:
        return await render_template(
            '{0}.html'.format(page),
            title = name,
            version = version,
        )
    except TemplateNotFound as e:
        logger.warning(u"Template not found for {}".format(str(page)))
        await abort(404)

@blueprint.route("/status")
async def status():
    users = [{
        'user': await dispatcher.bot.get_me(),
        'status': dispatcher.is_polling(),
    } for dispatcher in current_app.dispatchers]
    return await render_template(
        "status.html",
        title = name,
        version = version,
        users = users,
    )

@blueprint.route("/map")
async def map():
    return jsonify(str(current_app.url_map))

@blueprint.route("/get_me")
async def get_me():
    users = [await dispatcher.bot.get_me() for dispatcher in current_app.dispatchers]
    names = [user['first_name'] for user in users]
    return await render_template(
        "get_me.html",
        title = name,
        version = version,
        names = names,
        users = users,
    )

@blueprint.route("/send_message", methods=['GET', 'POST'])
@blueprint.route("/send_message/<bot_id>/<chat_id>/<text>", methods=['GET'])
async def send_message(bot_id = None, chat_id = None, text = None):
    message = None
    if request.method == 'POST':
        try:
            form = await request.form
            dispatcher = [dispatcher for dispatcher in current_app.dispatchers if int(form['bot_id']) == int((await dispatcher.bot.get_me())['id'])][0]
            message = await dispatcher.bot.send_message(
                chat_id = form['chat_id'],
                text = form['text'],
            )
        except Exception as e:
            return jsonify(repr(e))
    elif bot_id and chat_id and text:
        dispatcher = [dispatcher for dispatcher in current_app.dispatchers if int(bot_id) == int((await dispatcher.bot.get_me())['id'])][0]
        message = await dispatcher.bot.send_message(
            chat_id = chat_id,
            text = text,
        )
    return await render_template(
        "send_message.html",
        title = name,
        version = version,
        message = message,
    )
