"""
Models for Furhat API

ia.cecil

Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

class BasicParam(object):
    BasicParam: object = None
    def __init__(self, BasicParam):
        self.BasicParam = BasicParam
    def __repr__(self):
        return "<BasicParam(BasicParam={BasicParam})>".format(
            BasicParam = self.BasicParam,
        )

class Frame(object):
    time: float = None
    params: BasicParam = None
    def __init__(self, time, params):
        self.time = time
        self.params = params
    def __repr__(self):
        return "<Frame(time={time}, params={params})>".format(
            time = self.time,
            params = self.params,
        )

class Status(object):
    success: bool = False
    message: str = ''
    def __init__(self, success = False, message = ''):
        self.success = success
        self.message = message
    def __repr__(self):
        return "<Status(success={success}, message={message})>".format(
            success = self.success,
            message = self.message,
        )

class Gesture(object):
    name: str = None
    duration: float = None
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration
    def __repr__(self):
        return "<Gesture(name={name}, duration={duration})>".format(
            name = self.name,
            duration = self.duration,
        )

class GestureDefinition(object):
    name: str = None
    frames: Frame = None
    class_: str = 'furhatos.gestures.Gesture'
    def __init__(self, name, frames, class_):
        self.name = name
        self.frames = frames
        self.class_ = class_
    def __repr__(self):
        return """<GestureDefinition(name={name}, frames={frames}, 
class_={class_})>""".format(
            name = self.name,
            frames = self.frames,
            class_ = self.class_,
        )

class Rotation(object):
    x: float = None
    y: float = None
    z: float = None
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def __repr__(self):
        return "<Rotation(x={x}, y={y}, z={z}>".format(
            x = self.x,
            y = self.y,
            z = self.z,
        )

class Location(object):
    x: float = None
    y: float = None
    z: float = None
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def __repr__(self):
        return "<Location(x={x}, y={y}, z={z}>".format(
            x = self.x,
            y = self.y,
            z = self.z,
        )

class User(object):
    id: str = None
    rotation: Rotation = None
    location: Location = None
    def __init__(self, id, rotation, location):
        self.id = id
        self.rotation = rotation
        self.location = location
    def __repr__(self):
        return """<User(id={id}, rotation={rotation}, location=\
{location})>""".format(
            id = self.id,
            rotation = self.rotation,
            location = self.location,
        )

class Voice(object):
    name: str = None
    language: str = None
    def __init__(self, name, language):
        self.name = name
        self.language = language
    def __repr__(self):
        return "<Voice(name={name}, language={language})>".format(
            name = self.name,
            language = self.language,
        )
