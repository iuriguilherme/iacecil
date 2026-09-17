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

import logging
logger = logging.getLogger(__name__)

from quart import (
    current_app,
    flash,
    render_template,
)
from ..... import (
    name,
    commit,
    version,
)

async def status(active_tab = {}):
    ## Identity from configuration, not from a live bot: the connectors
    ## run in their own process now (R8). Whether each one is actually
    ## polling is connector-process knowledge, so this page reports what
    ## is configured and says plainly that it cannot see run state until
    ## slice 2 adds the connector health view.
    identities = list(getattr(current_app, 'bot_identities', []))
    users = [{
        'user': identity,
        'status': identity.get('status'),
    } for identity in identities]
    names = [user['user']['first_name'] for user in users]
    await flash(
        u"Total configured bots: {0}\nRunning state: unknown from the web \
process until the connector health view lands".format(len(users)), 'info')
    return await render_template(
        "root/status.html",
        active = {
            'nav': dict(
                current_app.active_nav.copy(),
                root = ' active',
            ),
            'tab': dict(
                active_tab.copy(),
                status = ' active',
            ),
        },
        commit = commit,
        name = name,
        names = names,
        title = u"Status",
        users = users,
        version = version,
    )
