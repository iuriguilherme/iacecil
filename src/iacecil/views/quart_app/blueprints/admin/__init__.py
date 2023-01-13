"""
ia.cecil

Copyleft 2012-2023 Iuri Guilherme <https://iuri.neocities.org/>

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
from ..... import (
    name,
    commit,
    version,
)
from .....controllers.aiogram_bot.callbacks import (
    error_callback,
    exception_callback,
)
from .routes import (
    files,
    messages_texts_list,
    messages_list,
    polling,
    send_message,
    updates,
)

active_tab = {
    'files': '',
    'messages': '',
    'texts': '',
    'send_message': '',
    'updates': '',
    'polling': '',
}

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
    defaults = {'active_tab': active_tab},
)
blueprint.add_url_rule(
    '/messages/',
    'messages',
    messages_list,
    methods = ['GET', 'POST'],
    defaults = {'active_tab': active_tab},
)
blueprint.add_url_rule(
    '/texts/',
    'texts',
    messages_texts_list,
    methods = ['GET', 'POST'],
    defaults = {'active_tab': active_tab},
)
blueprint.add_url_rule(
    '/send_message/',
    'send_message',
    send_message,
    methods = ['GET', 'POST'],
    defaults = {'active_tab': active_tab},
)
blueprint.add_url_rule(
    '/updates/',
    'updates',
    updates,
    methods = ['GET', 'POST'],
    defaults = {'active_tab': active_tab},
)
blueprint.add_url_rule(
    '/polling/',
    'polling',
    polling,
    methods = ['GET', 'POST'],
    defaults = {'active_tab': active_tab},
)

@blueprint.route('/', defaults={'page': 'index'})
@blueprint.route('/<page>')
async def show(page):
    try:
        return await render_template(
            "admin/{0}.html".format(page),
            active = {
                'nav': dict(
                    current_app.active_nav.copy(),
                    admin = ' active',
                ),
                'tab': dict(
                    active_tab.copy(),
                    page = ' active',
                ),
            },
            commit = commit,
            name = name,
            title = page,
            version = version,
        )
    except TemplateNotFound as e:
        logger.warning(f"Template not found for {page}")
        await abort(404)
