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

import ffmpeg, glob

## Converts audio files to telegram sendVoice format
async def telegram_voice(input_file):
    output_file = '.'.join([
        input_file.split('.')[0],
        'opus',
        input_file.split('.')[1]
    ])
    try:
        proccess = (
            ffmpeg
            .input(input_file)
            .output(
                output_file,
                **{
                    'ac': 1,
                    'map': '0:a',
                    'strict': 2,
                    'acodec': 'libopus',
                    'audio_bitrate': '128k',
                    'ar': 24000,
                },
            )
            .run_async()
        )
        if proccess.wait(timeout = 30) == 0:
            return output_file
        else:
            return None
    except FileNotFoundError as exception:
        logger.warning(u"probably no ffmpeg in the system: {}".format(
            repr(exception)))
        return None

async def storify(input_file, h = '00', m = '00', s = '15', **kwargs):
    try:
        proccess = (
            ffmpeg
            .input(input_file)
            .output(
                '.'.join([
                    input_file.split('.')[0],
                    '%03d',
                    input_file.split('.')[1]
                ]),
                **{
                    'c': 'copy',
                    'map': '0',
                    'segment_time': ':'.join([h, m, s]),
                    'f': 'segment',
                    'reset_timestamps': 1,
                },
            )
            .run_async()
        )
        if proccess.wait(timeout = 30) == 0:
            return glob.glob('.'.join([
                input_file.split('.')[0],
                '*',
                input_file.split('.')[1]
            ]))
        else:
            return None
    except FileNotFoundError as exception:
        logger.warning(u"probably no ffmpeg in the system: {}".format(
            repr(exception)))
        return None
    except Exception as exception:
        logger.debug(repr(exception))
        raise
