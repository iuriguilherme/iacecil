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

import base64, BTrees, glob, json, os, transaction, ZODB
from io import BytesIO
from matplotlib.figure import Figure
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
from iacecil.controllers.persistence.zodb_orm import (
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
        name = actual_name,
        title = u"Graphics",
        version = version,
    )
