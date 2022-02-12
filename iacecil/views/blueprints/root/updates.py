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

import BTrees, glob, json, transaction, ZODB
from quart import (
    abort,
    current_app,
    flash,
    jsonify,
    request,
    render_template,
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

_Auto = object()
class SubFlaskForm(Form):
    def __init__(self, formdata = _Auto, **kwargs):
        super().__init__(formdata = formdata, **kwargs)

async def show_updates():
    messages = None
    chats = None
    count = {'total': 0, 'current': 0}
    bots = [user for user in [await dispatcher.bot.get_me() for \
        dispatcher in current_app.dispatchers]]
    class UpdatesForm(SubFlaskForm):
        bot_id_field = RadioField(
            u"select bot",
            choices = [(user['id'], user['first_name']
                ) for user in bots],
        )
        chat_id_field = RadioField(
            u"select chat",
            choices = [],
        )
        limit_field = IntegerField(
            'limit',
            default = 30,
        )
        offset_field = IntegerField(
            'offset',
            default = 0,
        )
        submit = SubmitField(u"Send")
    form = UpdatesForm(formdata = await request.form)
    if form['bot_id_field'].data:
        try:
            bot_current = [dispatcher.bot for dispatcher in \
                current_app.dispatchers if str(dispatcher.bot.id
                ) == form['bot_id_field'].data
            ][0]
            chats_list = set([chat.strip('instance/zodb/').split('.')[
                1] for chat in glob.glob('instance/zodb/{}.*.fs'.format(
                form['bot_id_field'].data))]
            )
            chats_info = [chat_object for chat_object in [
                await bot_current.get_chat(chat_id) for chat_id in \
                chats_list]
            ]
            chats = [{'id': chat['id'], 'desc': chat['title']
                } if chat['title'
                ] is not None else {'id': chat['id'], 'desc': chat[
                'first_name']} for chat in chats_info
            ]
            form['chat_id_field'].choices = [(int(chat['id']),
                chat['desc']) for chat in chats]
        except Exception as exception:
            return jsonify(repr(exception))
    if request.method == "POST":
        try:
            db = None
            try:
                db, pms = await get_bot_messages(
                    form['bot_id_field'].data,
                    form['chat_id_field'].data,
                )
                if db and pms:
                    try:
                        count['total'] = len(pms)
                        messages = [{k:v for (k,v) in pm.items()
                            } for pm in pms.values()][
                                form['offset_field'].data:form[
                                'limit_field'].data+form['offset_field'
                                ].data]
                        count['current'] = len(messages)
                    except Exception as e1:
                        await error_callback(
                            u"Message NOT retrieved from database",
                            message,
                            e1,
                            ['quart', 'updates', 'index', 'zodb',
                                'exception'],
                        )
                        raise
                    finally:
                        try:
                            db.close()
                        except Exception as e2:
                            logger.warning(
                                u"db was never created on {}: {}".format(
                                __name__,
                                repr(e2),
                            ))
                            raise
            except Exception as e3:
                await exception_callback(
                    e3,
                    ['quart', 'updates', 'index', 'zodb'],
                )
                raise
        except Exception as exception:
            return jsonify(repr(exception))
    return await render_template(
        "updates.html",
        canonical = current_app.canonical,
        commit = commit,
        count = count,
        bots = bots,
        chats = chats,
        form = form,
        messages = messages,
        title = actual_name,
        version = version,
    )

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
        message = message,
        title = actual_name,
        version = version,
    )
