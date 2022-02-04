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

# ~ from sqlalchemy import (
    # ~ Column,
    # ~ Integer,
    # ~ Sequence,
    # ~ String,
# ~ )
# ~ from flask_sqlalchemy import (
    # ~ declarative_base,
# ~ )

# ~ Base = declarative_base()

# ~ class FormBot(Base):
    # ~ __tablename__ = 'bots'
    # ~ id = Column(
        # ~ Integer,
        # ~ Sequence('bot_id_seq'),
        # ~ primary_key = True,
    # ~ )
    # ~ first_name = Column(String(64))
    # ~ def __repr__(self):
        # ~ return "<FormBot(id={id}), first_name={first_name}".format(
            # ~ id = self.id,
            # ~ first_name = self.first_name,
        # ~ )

# ~ class FormChat(Base):
    # ~ __tablename__ = 'chats'
    # ~ id = Column(
        # ~ Integer,
        # ~ Sequence('chat_id_seq'),
        # ~ primary_key = True,
    # ~ )
    # ~ title = Column(String(64))
    # ~ def __repr__(self):
        # ~ return "<FormChat(id={id}), title={title}".format(
            # ~ id = self.id,
            # ~ title = self.title,
        # ~ )
