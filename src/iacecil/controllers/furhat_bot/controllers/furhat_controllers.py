"""
ia.cecil

Copyleft 2012-2025 Iuri Guilherme <https://iuri.neocities.org/>

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

import asyncio
import glob
import os
import random
import uuid
from urllib3.exceptions import MaxRetryError
from ..remote_api import (
    get_furhat,
    get_voices,
    set_face,
    set_led,
    set_voice,
    do_attend_location,
    do_attend_user,
    do_listen,
    do_say_text,
    do_say_url,
    block_do_listen,
    block_do_say_text,
    block_do_say_url,
)
from ....models.furhat_models import Status
from ...persistence.zodb_orm import (
    get_messages_texts_list,
    get_furhat_texts_messages,
    set_furhat_text,
)
from plugins.natural import (
    generate,
    concordance,
    collocations,
    common_contexts,
    count,
    similar,
)

async def shutup(furhat):
    return furhat.say(text = 'ta', abort = True)

async def change_voice(furhat, voices, language):
    await set_voice(furhat, random.choice([voice.name for voice in \
        voices if voice.language == language]))

async def led_blue(furhat):
    await set_led(furhat, red = 0, green = 0, blue = 255)

async def led_green(furhat):
    await set_led(furhat, red = 0, green = 255, blue = 0)

async def led_yellow(furhat):
    await set_led(furhat, red = 255, green = 255, blue = 0)

async def led_red(furhat):
    await set_led(furhat, red = 255, green = 0, blue = 0)

async def led_white(furhat):
    await set_led(furhat, red = 255, green = 255, blue = 255)

async def led_blank(furhat):
    await set_led(furhat, red = 0, green = 0, blue = 0)

async def blue_speak(furhat, message):
    await asyncio.sleep(1)
    await led_blue(furhat)
    await do_attend_user(furhat, 'RANDOM')
    await do_say_text(furhat, message)
