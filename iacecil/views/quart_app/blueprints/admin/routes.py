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

## TODO
## - [ ] Move ZODB to controllers/zodb_orm
## - [ ] Organize imports
## - [ ] Figure out async WTForms and get rid of _Auto = object()

import logging
logger = logging.getLogger(__name__)

import BTrees, glob, json, os, transaction, ZODB
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
from iacecil.controllers.zodb_orm import (
    get_messages,
    get_bot_messages,
    get_bot_files,
)

import base64
from io import BytesIO
from matplotlib.figure import Figure

_Auto = object()
class SubFlaskForm(Form):
    def __init__(self, formdata = _Auto, **kwargs):
        super().__init__(formdata = formdata, **kwargs)

async def graphic():
    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return await render_template(
        "admin/graphic.html",
        commit = commit,
        data = data,
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
        "admin/send_message.html",
        commit = commit,
        form = form,
        message = message,
        title = actual_name,
        version = version,
    )

async def updates():
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
            db_path = 'instance/zodb/bots/{}/chats'.format(
                    form['bot_id_field'].data
            )
            try:
                chats_list = set([os.path.basename(chat).split('.')[0
                    ] for chat in glob.glob('{}/*.fs'.format(db_path))]
                )
            except FileNotFoundError:
                os.makedirs(db_path)
                chats_list = set([os.path.basename(chat).split('.')[0
                    ] for chat in glob.glob('{}/*.fs'.format(db_path))]
                )
            chats_info = list()
            for chat_id in chats_list:
                try:
                    chats_info.append(
                        await bot_current.get_chat(chat_id)
                    )
                except:
                    chats_info.append({
                        'id': chat_id,
                        'title': u"Unknown",
                    })
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
                        offset = None
                        limit = None
                        if form['limit_field'].data > 0:
                            limit = -(1+form['limit_field'].data+form[
                                'offset_field'].data)
                        if form['offset_field'].data > 0:
                            offset = -(1+form['offset_field'].data)
                            limit = limit + 1
                        messages = [{k:v for (k,v) in pm.items()
                            } for pm in pms.values()][offset:limit:-1]
                        count['current'] = len(messages)
                        logger.debug(messages)
                    except Exception as e1:
                        logger.warning(
                            u"Message NOT retrieved from database",
                        )
                        raise
                    finally:
                        try:
                            db.close()
                        except Exception as e2:
                            logger.warning(u"""db was never created on \
{}: {}""".format(__name__, repr(e2)))
                            raise
            except Exception as e3:
                logger.warning(repr(e3))
                raise
        except Exception as exception:
            return jsonify(repr(exception))
    return await render_template(
        "admin/updates.html",
        commit = commit,
        count = count,
        bots = bots,
        chats = chats,
        form = form,
        messages = messages,
        title = actual_name,
        version = version,
    )

async def files():
    files = None
    count = {'total': 0, 'current': 0}
    bots = [user for user in [await dispatcher.bot.get_me() for \
        dispatcher in current_app.dispatchers]]
    class FilesForm(SubFlaskForm):
        bot_id_field = RadioField(
            u"select bot",
            choices = [(user['id'], user['first_name']
                ) for user in bots],
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
    form = FilesForm(formdata = await request.form)
    if request.method == "POST":
        try:
            db = None
            try:
                db, _files = await get_bot_files(
                    form['bot_id_field'].data,
                )
                if db and _files:
                    try:
                        count['total'] = len(_files)
                        offset = None
                        limit = None
                        if form['limit_field'].data > 0:
                            limit = -(1+form['limit_field'].data+form[
                                'offset_field'].data)
                        if form['offset_field'].data > 0:
                            offset = -(1+form['offset_field'].data)
                            limit = limit + 1
                        files = [{k:v for (k,v) in _files[_file].items()
                            } for _file in _files][
                            offset:limit:-1]
                        count['current'] = len(files)
                    except TypeError as e3:
                        files = None
                        logger.warning(repr(e3))
                        raise
                    except Exception as e2:
                        logger.warning(u"""Files NOT retrieved from dat\
abase: {}""".format(repr(e2))
                        )
                        raise
                    finally:
                        try:
                            db.close()
                        except Exception as e4:
                            logger.warning(u"""db was never created on \
{}: {}""".format(__name__, repr(e4)))
                            raise
            except Exception as e1:
                logger.warning(repr(e1))
                raise
        except Exception as exception:
            return jsonify(repr(exception))
    return await render_template(
        "admin/files.html",
        commit = commit,
        count = count,
        bots = bots,
        form = form,
        files = files,
        title = actual_name,
        version = version,
    )
