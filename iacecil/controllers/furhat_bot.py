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
async def set_face(furhat, mask, character):
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
    return furhat.gesture(name = name)
async def do_listen(furhat, language):
    return furhat.listen(language = language)
async def do_say_text(furhat, text):
    return furhat.say(text = text)
async def do_say_url(furhat, url):
    return furhat.say(url = url, lipsync = True)
def block_do_listen(furhat, language):
    return furhat.listen(language = language)
def block_do_say_text(furhat, text):
    return furhat.say(text = text)
def block_do_say_url(furhat, url):
    return furhat.say(url = url, lipsync = True)

async def run_tests(config):
    try:
        ## Create an instance of the FurhatRemoteAPI class, providing 
        ## the address of the robot or the SDK running the virtual robot
        furhat = await get_furhat(config['address'])
        ## Get the voices on the robot
        # ~ voices = furhat.get_voices()
        ## Set the voice of the robot
        await set_voice(furhat, config['voice'])
        ## Say "Hi there!"
        furhat.say(text = "Hi there!")
        ## Play an audio file (with lipsync automatically added) 
        furhat.say(
            url = """https://www2.cs.uic.edu/~i101/SoundFiles/gettysbur\
g10.wav""",
            lipsync = True,
        )
        ## Listen to user speech and return ASR result
        # ~ result = furhat.listen()
        ## Perform a named gesture
        furhat.gesture(name = "BrowRaise")
        ## Perform a custom gesture
        # ~ furhat.gesture(
            # ~ definition = {
                # ~ "frames": [
                    # ~ {
                        # ~ "time": [
                            # ~ 0.33
                        # ~ ],
                        # ~ "params": {
                            # ~ "BLINK_LEFT": 1.0
                        # ~ },
                    # ~ },
                    # ~ {
                        # ~ "time": [
                            # ~ 0.67
                        # ~ ],
                        # ~ "params": {
                            # ~ "reset": True
                        # ~ },
                    # ~ },
                # ~ ],
                # ~ "class": "furhatos.gestures.Gesture",
            # ~ },
        # ~ )

        ## Get the users detected by the robot 
        # ~ users = furhat.get_users()
        ## Attend the user closest to the robot
        furhat.attend(user = "CLOSEST")
        ## Attend a user with a specific id
        furhat.attend(userid = "virtual-user-1")
        ## Attend a specific location (x,y,z)
        furhat.attend(location = "0.0,0.2,1.0")
        ## Set the LED lights
        furhat.set_led(red = 200, green = 50, blue = 50)
        return {
            'furhat': str(furhat),
            'voices': str(furhat.get_voices()),
            'gestures': str(furhat.get_gestures()),
            'users': str(furhat.get_users()),
        }
    except Exception as exception:
        logger.warning(
            u"Furhat not working: {}".format(repr(exception))
        )
        return False
