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
    flash,
    jsonify,
    request,
    render_template,
)
from flask_wtf import FlaskForm
from wtforms import (
    Form,
    StringField,
    SubmitField,
    RadioField,
    TextAreaField,
)
from jinja2 import TemplateNotFound
from iacecil import (
    actual_name,
    version,
)

logger = logging.getLogger('blueprints.root')

blueprint = Blueprint('root', 'index')

@blueprint.route('/', defaults={'page': 'index'})
@blueprint.route('/<page>')
async def show(page):
    try:
        return await render_template(
            '{0}.html'.format(page),
            title = actual_name,
            version = version,
            canonical = current_app.canonical,
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
        title = actual_name,
        version = version,
        names = names,
        users = users,
        canonical = current_app.canonical,
    )

@blueprint.route("/send_message", methods=['GET', 'POST'])
async def send_message():
    message = None
    bots = [
        (user['id'], user['first_name']) for
        user in [await dispatcher.bot.get_me() for
        dispatcher in current_app.dispatchers]
    ]
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
    class SendMessageForm(SubFlaskForm):
        bot_id_field = RadioField(
            u"select bot id",
            choices = bots,
        )
        chat_id_field = StringField(
            u"select chat id",
        )
        text_field = TextAreaField(
            u"Text",
        )
        submit = SubmitField(u"Send")
    form = SendMessageForm(formdata = await request.form)
    if request.method == "POST":
        try:
            form = await request.form
            dispatcher = [dispatcher for 
                dispatcher in current_app.dispatchers if 
                int(form['bot_id_field']) == int((
                await dispatcher.bot.get_me())['id'])
            ][0]
            message = await dispatcher.bot.send_message(
                chat_id = form['chat_id_field'],
                text = form['text_field'],
                parse_mode = "MarkdownV2",
            )
        except Exception as e:
            return jsonify(repr(e))
    return await render_template(
        "send_message.html",
        title = actual_name,
        version = version,
        message = message,
        form = form,
        canonical = current_app.canonical,
    )
