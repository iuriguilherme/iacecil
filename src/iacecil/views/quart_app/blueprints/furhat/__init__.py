"""
ia.cecil

Copyleft 2012-2025 Iuri Guilherme <https://iuri.neocities.org/>

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

from jinja2 import TemplateNotFound
from quart import (
    abort,
    Blueprint,
    current_app,
    render_template,
)
from ..... import (
    name,
    commit,
    version,
)
from .routes import (
    tests,
)

active_tab = {
    'tests': '',
}

blueprint = Blueprint(
    'furhat',
    'furhat',
    template_folder = 'iacecil/views/quart_app/templates/furhat',
)
blueprint.add_url_rule(
    '/tests/',
    'tests',
    tests,
    methods = ['GET'],
    defaults = {'active_tab': active_tab},
)

@blueprint.route('/', defaults={'page': 'index'})
@blueprint.route('/<page>')
async def show(page):
    try:
        return await render_template(
            'furhat/{0}.html'.format(page),
            active = {
                'nav': dict(
                    current_app.active_nav.copy(),
                    furhat = ' active',
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
        logger.warning(u"Template not found for {}".format(str(page)))
        await abort(404)
