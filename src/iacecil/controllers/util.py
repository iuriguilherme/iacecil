"""
ia.cecil

Copyleft 2012-2023 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
logger = logging.getLogger(__name__)

import random
import uuid

async def dice(number: int) -> int:
    """Retorna um número aleatório entre 1 e number"""
    return random.randint(1, number)

async def dice_low(number: int) -> bool:
    """Retorna verdadeiro em uma chance de 1 para number"""
    return (await dice(number)) == 1

async def dice_high(number: int) -> bool:
    """Retorna verdadeiro em uma chance de 1 para len(number) - 1"""
    return (await dice(number)) > 1

async def get_job_id(*args) -> str:
    """Retorna um uuid5 a partir de args"""
    return str(uuid.uuid5(uuid.UUID(int = 0), '.'.join(args)))
