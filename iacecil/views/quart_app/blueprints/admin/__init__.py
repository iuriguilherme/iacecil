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

from quart import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    request,
    render_template,
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
from iacecil.views.quart_app.blueprints.admin.routes import (
    files,
    messages_texts_list,
    messages_list,
    send_message,
    updates,
)

blueprint = Blueprint(
    'admin',
    'admin',
    template_folder = 'iacecil/views/quart_app/templates/admin',
)
blueprint.add_url_rule(
    '/files/',
    'files',
    files,
    methods = ['GET', 'POST'],
)
blueprint.add_url_rule(
    '/messages/',
    'messages',
    messages_list,
    methods = ['GET', 'POST'],
)
blueprint.add_url_rule(
    '/texts/',
    'texts',
    messages_texts_list,
    methods = ['GET', 'POST'],
)
blueprint.add_url_rule(
    '/send_message/',
    'send_message',
    send_message,
    methods = ['GET', 'POST'],
)
blueprint.add_url_rule(
    '/updates/',
    'updates',
    updates,
    methods = ['GET', 'POST'],
)

@blueprint.route('/', defaults={'page': 'index'})
@blueprint.route('/<page>')
async def show(page):
    try:
        return await render_template(
            "admin/{0}.html".format(page),
            commit = commit,
            name = actual_name,
            title = page,
            version = version,
        )
    except TemplateNotFound as e:
        logger.warning(u"Template not found for {}".format(str(page)))
        await abort(404)
