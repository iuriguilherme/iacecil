"""
Wrapper for ffmpeg package - https://pypi.org/project/ffmpeg-python/

Copyleft 2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import ffmpeg
import glob
import os
from typing import Union

async def telegram_voice(input_file: str) -> Union[None, str]:
    """
    Converts audio files to telegram sendVoice format.
    Returns string containing file path.
    """
    output_file = '.'.join([
        *input_file.split('.')[:2],
        'opus',
        input_file.split('.')[2]
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
    except FileNotFoundError as e:
        logger.warning("probably no ffmpeg in the system:")
        logger.exception(e)
        return None
    except Exception as e:
        logger.exception(e)
        raise
    finally:
        if input_file is not None:
            os.remove(input_file)

async def storify(
    input_file: str,
    *args,
    h: str = '00',
    m: str = '00',
    s: str = '15',
    **kwargs
) -> Union[None, list]:
    """
    Splits video file in chunks of h hours, m minutes, s seconds.
    Returns buffer with the video object.
    """
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
    except FileNotFoundError as e:
        logger.warning("probably no ffmpeg in the system:")
        logger.exception(e)
        return None
    except Exception as e:
        logger.exception(e)
        raise
    finally:
        if input_file is not None:
            os.remove(input_file)
