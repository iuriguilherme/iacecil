"""
ia.cecil

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

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

## TODO
## - [ ] Move ZODB to controllers/zodb_orm
## - [ ] Organize imports
## - [ ] Figure out async WTForms and get rid of _Auto = object()

import logging
logger = logging.getLogger(__name__)

import asyncio
import BTrees
import glob
import json
import os
import transaction
import ZODB
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
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    RadioField,
    TextAreaField,
)
from jinja2 import TemplateNotFound
from ..... import (
    name,
    commit,
    version,
)
from .....controllers.persistence.zodb_orm import (
    get_aiogram_messages,
    get_messages,
    get_messages_list,
    get_messages_texts_list,
    get_bot_messages,
    get_bot_files,
)
from plugins.natural import (
    generate,
    tokenize_list,
)

# ~ _Auto = object()
# ~ class SubFlaskForm(Form):
    # ~ def __init__(self, *args, formdata = _Auto, **kwargs):
        # ~ super().__init__(*args, formdata = formdata, **kwargs)

# ~ class BotChatTextForm(SubFlaskForm):
def configured_bots() -> list:
    """Bot identities this process knows, read from configuration.

    The connectors run in their own process now, so there is no live
    dispatcher to ask (R8). Identity comes from `instance/` instead.
    """
    return list(getattr(current_app, 'bot_identities', []))


def bot_choices() -> list:
    return [(identity['id'], identity['first_name'])
        for identity in configured_bots()]


def stored_chat_choices(bot_id) -> list:
    """Chats this bot has stored data for.

    Titles used to come from `bot.get_chat()` on a live bot object.
    Without one in this process, the stored chat id is the label; slice
    2's control channel is what can enrich it again.
    """
    db_path = 'instance/zodb/bots/{}/chats'.format(bot_id)
    try:
        chats_list = set([os.path.basename(chat).split('.')[0]
            for chat in glob.glob('{}/*.fs'.format(db_path))])
    except FileNotFoundError:
        chats_list = set()
    return [(chat_id, chat_id) for chat_id in sorted(chats_list)]


class BotChatLimitOffsetForm(FlaskForm):
    bot_id_field = RadioField(
        u"select bot",
        choices = [('0', 'nenhum')],
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
    async def validate_bot_id_field(form, field):
        field.choices = bot_choices()
    async def validate_chat_id_field(form, field, bot_id):
        field.choices = stored_chat_choices(bot_id)

class BotChatTextForm(FlaskForm):
    bot_id_field = RadioField(
        u"select bot",
        choices = [('0', 'nenhum')],
    )
    chat_id_field = RadioField(
        u"select chat",
        choices = [],
    )
    text_field = TextAreaField(
        u"message",
        default = u"Nada",
    )
    submit = SubmitField(u"Send")
    async def validate_bot_id_field(form, field):
        field.choices = bot_choices()
    async def validate_chat_id_field(form, field, bot_id):
        field.choices = stored_chat_choices(bot_id)

class BotForm(FlaskForm):
    bot_id_field = HiddenField()
    submit = SubmitField()
    # ~ async def validate_bot_id_field(form, field):
        # ~ field.choices = [
            # ~ (user['id'], user['first_name']) for
            # ~ user in [await dispatcher.bot.get_me() for
            # ~ dispatcher in current_app.dispatchers]
        # ~ ]

async def send_message(active_tab = {}):
    """SLICE-2: requires the connector control channel.

    This route acted on a live in-process aiogram bot. The connectors
    run in their own process now, so the web unit has nothing to act on
    until slice 2 adds the control channel. The previous implementation
    is in git history at the commit that disabled it.
    """
    return jsonify({
        'error': 'not available',
        'reason': 'sending a message needs a live bot in this process',
        'available_in': 'slice 2 (connector control channel)',
    }), 503

async def updates(active_tab = {}):
    """SLICE-2: requires the connector control channel.

    This route acted on a live in-process aiogram bot. The connectors
    run in their own process now, so the web unit has nothing to act on
    until slice 2 adds the control channel. The previous implementation
    is in git history at the commit that disabled it.
    """
    return jsonify({
        'error': 'not available',
        'reason': 'fetching updates needs a live bot in this process',
        'available_in': 'slice 2 (connector control channel)',
    }), 503

async def files(active_tab = {}):
    files = None
    count = {'total': 0, 'current': 0}
    bots = configured_bots()
    class FilesForm(BotChatLimitOffsetForm):
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
        active = {
            'nav': dict(
                current_app.active_nav.copy(),
                admin = ' active',
            ),
            'tab': dict(
                active_tab.copy(),
                files = ' active',
            ),
        },
        commit = commit,
        count = count,
        bots = bots,
        form = form,
        files = files,
        name = name,
        title = u"Files",
        version = version,
    )

async def messages_texts_list(active_tab = {}):
    show_messages = None
    messages = (0, None)
    chats = None
    count = {'total': 0, 'current': 0}
    bots = configured_bots()
    class MessagesTextsForm(BotChatLimitOffsetForm):
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
            default = -1,
        )
        submit = SubmitField(u"Send")
    form = MessagesTextsForm(formdata = await request.form)
    if form['bot_id_field'].data:
        try:
            chats = [{'id': chat_id, 'desc': label}
                for chat_id, label in stored_chat_choices(
                    form['bot_id_field'].data)]
            form['chat_id_field'].choices = [(chat['id'], chat['desc'])
                for chat in chats]
        except Exception as exception:
            return jsonify(repr(exception))
    if request.method == "POST":
        try:
            offset = -1
            limit = 0
            if form['limit_field'].data > 0:
                limit = -(2+form['limit_field'].data+form[
                    'offset_field'].data)
            if form['offset_field'].data > 0:
                offset = -(1+form['offset_field'].data)
                limit = limit + 1
            try:
                messages = await get_messages_texts_list(
                    bot_id = form['bot_id_field'].data,
                    chat_id = form['chat_id_field'].data,
                    offset = offset,
                    limit = limit,
                )
                count['total'] = messages[0]
                count['current'] = len(messages[1])
                show_messages = await generate(messages[1])
            except Exception as e1:
                logger.warning(repr(e1))
                raise
        except Exception as exception:
            return jsonify(repr(exception))
    return await render_template(
        "admin/messages_texts.html",
        active = {
            'nav': dict(
                current_app.active_nav.copy(),
                admin = ' active',
            ),
            'tab': dict(
                active_tab.copy(),
                texts = ' active',
            ),
        },
        commit = commit,
        count = count,
        bots = bots,
        chats = chats,
        form = form,
        messages = show_messages,
        name = name,
        title = u"Messages Texts",
        version = version,
    )

async def messages_list(active_tab = {}):
    messages = (0, None)
    chats = None
    count = {'total': 0, 'current': 0}
    bots = configured_bots()
    class MessagesForm(BotChatLimitOffsetForm):
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
    form = MessagesForm(formdata = await request.form)
    if form['bot_id_field'].data:
        try:
            chats = [{'id': chat_id, 'desc': label}
                for chat_id, label in stored_chat_choices(
                    form['bot_id_field'].data)]
            form['chat_id_field'].choices = [(chat['id'], chat['desc'])
                for chat in chats]
        except Exception as exception:
            return jsonify(repr(exception))
    if request.method == "POST":
        try:
            # ~ offset = -1
            # ~ limit = 0
            # ~ if form['limit_field'].data > 0:
                # ~ limit = -(2+form['limit_field'].data+form[
                    # ~ 'offset_field'].data)
            # ~ if form['offset_field'].data > 0:
                # ~ offset = -(1+form['offset_field'].data)
                # ~ limit = limit + 1
            try:
                messages = await get_aiogram_messages(
                    bot_id = form['bot_id_field'].data,
                    chat_id = form['chat_id_field'].data,
                    offset = form['offset_field'].data,
                    limit = form['limit_field'].data,
                )
                count['total'] = messages[0]
                count['current'] = len(messages[1])
            except Exception as e1:
                logger.warning(repr(e1))
                raise
        except Exception as exception:
            return jsonify(repr(exception))
    return await render_template(
        "admin/messages.html",
        active = {
            'nav': dict(
                current_app.active_nav.copy(),
                admin = ' active',
            ),
            'tab': dict(
                active_tab.copy(),
                messages = ' active',
            ),
        },
        commit = commit,
        count = count,
        bots = bots,
        chats = chats,
        form = form,
        messages = messages[1],
        name = name,
        title = u"Messages",
        version = version,
    )

async def polling(active_tab = {}):
    """SLICE-2: requires the connector control channel.

    This route acted on a live in-process aiogram bot. The connectors
    run in their own process now, so the web unit has nothing to act on
    until slice 2 adds the control channel. The previous implementation
    is in git history at the commit that disabled it.
    """
    return jsonify({
        'error': 'not available',
        'reason': 'polling status and control live in the connector process',
        'available_in': 'slice 2 (connector control channel)',
    }), 503
