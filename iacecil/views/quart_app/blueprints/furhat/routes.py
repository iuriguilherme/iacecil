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

from aiogram import Dispatcher
from quart import (
    current_app,
    render_template,
)
from iacecil import (
    actual_name,
    commit,
    version,
)
from iacecil.controllers.furhat_bot.tests import run_tests

async def tests(active_tab = {}):
    furhat = await run_tests(Dispatcher.get_current().config['furhat'])
    return await render_template(
        "furhat/tests.html",
        active = {
            'nav': dict(
                current_app.active_nav.copy(),
                furhat = ' active',
            ),
            'tab': dict(
                active_tab.copy(),
                tests = ' active',
            ),
        },
        commit = commit,
        name = actual_name,
        furhat = furhat,
        title = u"Furhat Tests",
        version = version,
    )
