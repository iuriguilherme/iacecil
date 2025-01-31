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

import base64
import BTrees
import glob
import json
import os
import transaction
import ZODB
from io import BytesIO
from matplotlib.figure import Figure
from flask_wtf import FlaskForm
from jinja2 import TemplateNotFound
from quart import (
    abort,
    current_app,
    flash,
    jsonify,
    request,
    render_template,
)
from wtforms import (
    Form,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    RadioField,
    TextAreaField,
)
from ..... import (
    name,
    commit,
    version,
)
from .....controllers.persistence.zodb_orm import (
    get_messages,
    get_messages_texts_list,
    get_bot_messages,
    get_bot_files,
)

async def graphic(active_tab = {}):
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
        "plots/graphic.html",
        active = {
            'nav': dict(
                current_app.active_nav.copy(),
                plots = ' active',
            ),
            'tab': dict(
                active_tab.copy(),
                graphic = ' active',
            ),
        },
        commit = commit,
        data = data,
        name = name,
        title = u"Graphics",
        version = version,
    )
