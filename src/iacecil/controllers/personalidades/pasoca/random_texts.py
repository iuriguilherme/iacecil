"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import random

async def bomdia():
    return random.choice([
        u"bom dia.",
        u"bom dia!",
        u"Bom dia <3",
    ])

async def welcome():
    return random.choice([
        u"Seja bem vindo!",
        u"Mais um abençoado pro nosso grupo maravilhoso!",
        u"Que bom que você veio!",
        u"Deus te abençoe, meu filho!",
    ])
