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

import BTrees, glob, transaction, ZODB
from quart import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    request,
    render_template,
    # ~ websocket,
)
from flask_wtf import FlaskForm
from wtforms import (
    Form,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    RadioField,
    TextAreaField,
)
from jinja2 import TemplateNotFound
# ~ from functools import partial, wraps
from iacecil import (
    actual_name,
    commit,
    version,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    error_callback,
    exception_callback,
)
from iacecil.controllers.zodb_orm import (
    get_messages,
    get_bot_messages,
)
# ~ from iacecil.models import (
    # ~ FormBot,
    # ~ FormChat,
# ~ )

blueprint = Blueprint('root', 'index')

_Auto = object()
class SubFlaskForm(Form):
    def __init__(self, formdata = _Auto, **kwargs):
        super().__init__(formdata = formdata, **kwargs)
    # ~ def __init__(self, *args, **kwargs):
        # ~ super().__init__(*args, **kwargs)
    # ~ async def wrap_formdata(self, form, formdata):
        # ~ return super().wrap_formdata(self, form, formdata)
    # ~ async def is_submitted(self):
        # ~ return super().is_submitted(self)
    # ~ async def validate_on_submit(self):
        # ~ return super().validate_on_submit(self)
    # ~ async def hidden_tag(self, *fields):
        # ~ return super().hidden_tag(self, *fields)
    # ~ async def _is_submitted():
        # ~ return super()._is_submitted()

@blueprint.route('/', defaults={'page': 'index'})
@blueprint.route('/<page>')
async def show(page):
    try:
        return await render_template(
            '{0}.html'.format(page),
            canonical = current_app.canonical,
            commit = commit,
            title = actual_name,
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
    names = [user['user']['first_name'] for user in users]
    await flash(
        u"Total configured bots: {0}\nTotal running bots: {1}".format(
            len(users),
            len([user['status'] for user in users if user['status']]),
        ), 'info')
    return await render_template(
        "status.html",
        canonical = current_app.canonical,
        commit = commit,
        names = names,
        title = actual_name,
        users = users,
        version = version,
    )

@blueprint.route("/send_message", methods=['GET', 'POST'])
async def send_message():
    message = None
    bots = [
        (user['id'], user['first_name']) for
        user in [await dispatcher.bot.get_me() for
        dispatcher in current_app.dispatchers]
    ]
    class SendMessageForm(SubFlaskForm):
        bot_id_field = RadioField(
            u"select bot",
            choices = bots,
        )
        chat_id_field = StringField(
            u"type a valid chat_id",
            default = 1,
        )
        text_field = TextAreaField(
            u"message",
            default = u"Nada",
        )
        submit = SubmitField(u"Send")
    form = SendMessageForm(formdata = await request.form)
    if request.method == "POST":
        try:
            # ~ form = await request.form
            dispatcher = [dispatcher for 
                dispatcher in current_app.dispatchers if 
                int(form['bot_id_field'].data) == int((
                await dispatcher.bot.get_me())['id'])
            ][0]
            message = await dispatcher.bot.send_message(
                chat_id = int(form['chat_id_field'].data),
                text = str(form['text_field'].data),
                parse_mode = None,
            )
        except Exception as exception:
            return jsonify(repr(exception))
    return await render_template(
        "send_message.html",
        canonical = current_app.canonical,
        commit = commit,
        form = form,
        message = message.to_python() or None,
        title = actual_name,
        version = version,
    )

# ~ @blueprint.route("/updates", methods = ['GET', 'POST'])
# ~ async def updates():
    # ~ messages = None
    # ~ chats = None
    # ~ count = {'total': 0, 'current': 0}
    # ~ bots = [
        # ~ {'select': (user['id'], user['first_name'])} for
        # ~ user in [await dispatcher.bot.get_me() for
        # ~ dispatcher in current_app.dispatchers]
    # ~ ]
    # ~ class UpdatesForm(SubFlaskForm):
        # ~ bot_id_field = RadioField(
            # ~ u"select bot",
            # ~ choices = [bot['select'] for bot in bots],
        # ~ )
        # ~ chat_id_field = RadioField(
            # ~ u"select chat",
            # ~ choices = [],
        # ~ )
        # ~ limit_field = IntegerField(
            # ~ 'limit',
            # ~ default = 30,
        # ~ )
        # ~ offset_field = IntegerField(
            # ~ 'offset',
            # ~ default = 0,
        # ~ )
        # ~ submit = SubmitField(u"Send")
    # ~ form = UpdatesForm(formdata = await request.form)
    # ~ if form['bot_id_field'].data:
        # ~ chats = set([chat.strip('instance/zodb/').split('.')[1] \
            # ~ for chat in glob.glob('instance/zodb/{}.*.fs'.format(
            # ~ form['bot_id_field'].data))]
        # ~ )
        # ~ form['chat_id_field'].choices = [(int(chat), str(chat)) for \
            # ~ chat in chats]
    # ~ if request.method == "POST":
        # ~ try:
            # ~ db = None
            # ~ try:
                # ~ db, pms = await get_bot_messages(
                    # ~ form['bot_id_field'].data,
                    # ~ form['chat_id_field'].data,
                # ~ )
                # ~ if db and pms:
                    # ~ try:
                        # ~ count['total'] = len(pms)
                        # ~ messages = [{k:v for (k,v) in pm.items()
                            # ~ } for pm in pms.values()][
                                # ~ form['offset_field'].data:form[
                                # ~ 'limit_field'].data+form['offset_field'
                                # ~ ].data]
                        # ~ count['current'] = len(messages)
                    # ~ except Exception as e1:
                        # ~ await error_callback(
                            # ~ u"Message NOT retrieved from database",
                            # ~ message,
                            # ~ e1,
                            # ~ ['quart', 'root', 'updates', 'zodb',
                                # ~ 'exception'],
                        # ~ )
                        # ~ raise
                    # ~ finally:
                        # ~ try:
                            # ~ db.close()
                        # ~ except Exception as e2:
                            # ~ logger.warning(
                                # ~ u"db was never created on {}: {}".format(
                                # ~ __name__,
                                # ~ repr(e2),
                            # ~ ))
                            # ~ raise
            # ~ except Exception as e3:
                # ~ await exception_callback(
                    # ~ e3,
                    # ~ ['quart', 'root', 'updates', 'zodb'],
                # ~ )
                # ~ raise
        # ~ except Exception as exception:
            # ~ return jsonify(repr(exception))
    # ~ return await render_template(
        # ~ "updates.html",
        # ~ canonical = current_app.canonical,
        # ~ commit = commit,
        # ~ count = count,
        # ~ bots = bots,
        # ~ chats = chats,
        # ~ form = form,
        # ~ messages = messages,
        # ~ title = actual_name,
        # ~ version = version,
    # ~ )

# ~ @blueprint.websocket("/ws")
# ~ async def ws():
    # ~ while True:
        # ~ data = await websocket.receive()
        # ~ await websocket.send(f"echo {data}")

# ~ def collect_websocket(func):
    # ~ @wraps(func)
    # ~ async def wrapper(*args, **kwargs):
        # ~ global connected_websockets
        # ~ queue = asyncio.Queue()
        # ~ connected_websockets.add(queue)
        # ~ try:
            # ~ return await func(queue, *args, **kwargs)
        # ~ finally:
            # ~ connected_websockets.remove(queue)
    # ~ return wrapper

# ~ @blueprint.websocket("api/v2/ws")
# ~ @collect_websocket
# ~ async def ws_v2(queue):
    # ~ while True:
        # ~ data = await queue.get()
        # ~ await websocket.send(data)

# ~ connected_websockets = set()

# ~ async def broadcast(message):
    # ~ for queue in connected_websockets:
        # ~ await queue.put(message)
