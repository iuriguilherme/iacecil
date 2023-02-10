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

from furhat_remote_api import FurhatRemoteAPI

### From https://docs.furhat.io/remote-api/#python-remote-api
async def get_furhat(address):
    return FurhatRemoteAPI(address)

async def get_gestures(furhat):
    return furhat.get_gestures()

async def get_users(furhat):
    return furhat.get_users()

async def get_voices(furhat):
    return furhat.get_voices()

async def set_led(furhat, red = 0, green = 0, blue = 0):
    return furhat.set_led(red = red, green = green, blue = blue)

async def set_face(furhat, mask = "adult", character = "Titan"):
    return furhat.set_face(mask = mask, character = character)

async def set_voice(furhat, name):
    return furhat.set_voice(name = name)

async def do_attend_location(furhat, x = 0, y = 0, z = 0):
    return furhat.attend(location = ','.join([str(x), str(y), str(z)]))

async def do_attend_user(furhat, user):
    return furhat.attend(user = user)

async def do_attend_id(furhat, user_id):
    return furhat.attend(userid = user_id)

async def do_gesture(furhat, name):
    # ~ logger.critical(f"do_gesture = {name}")
    return furhat.gesture(name = name)

async def do_listen(furhat, language):
    # ~ logger.critical(f"do_listen = {language}")
    return furhat.listen(language = language)

async def do_say_text(furhat, text):
    # ~ logger.critical(f"do_say_text = {text}")
    return furhat.say(text = text)

async def do_say_url(furhat, url):
    # ~ logger.critical(f"do_say_url = {url}")
    return furhat.say(url = url, lipsync = True)

def block_do_listen(furhat, language):
    # ~ logger.critical(f"block_do_listen = {language}")
    return furhat.listen(language = language)

def block_do_say_text(furhat, text):
    # ~ logger.critical(f"block_do_say_text = {text}")
    return furhat.say(text = text)

def block_do_say_url(furhat, url):
    # ~ logger.critical(f"block_do_say_url = {url}")
    return furhat.say(url = url, lipsync = True)
