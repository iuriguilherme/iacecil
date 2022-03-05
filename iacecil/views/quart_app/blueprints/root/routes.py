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
    current_app,
    flash,
    render_template,
)
from iacecil import (
    actual_name,
    commit,
    version,
)

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
        "root/status.html",
        commit = commit,
        name = actual_name,
        names = names,
        title = u"Status",
        users = users,
        version = version,
    )
