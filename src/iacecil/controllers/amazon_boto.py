"""
ia.cecil

Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import boto3
import os
import subprocess
import sys
import uuid
from aiogram import Dispatcher
from boto3 import Session
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)
from contextlib import closing
from pydantic import BaseSettings
from tempfile import gettempdir
from typing import Union

async def get_session(region: str = 'us-east-1') -> Union[Session, None]:
    """Returns boto3 Session with configured credentials"""
    dispatcher = Dispatcher.get_current()
    try:
        return boto3.Session(
            aws_access_key_id = dispatcher.config.furhat['synthesizer'][
                'amazon']['key'],
            aws_secret_access_key = dispatcher.config.furhat['synthesizer'][
                'amazon']['secret'],
            region_name = region,
        )
    except Exception as e:
        logger.exception(e)
        return None

async def get_audio(
    Text: Union[str, None] = None,
    LanguageCode: str = 'pt-BR',
    VoiceId: str = 'Camila',
    OutputFormat: str = 'ogg_vorbis',
    Engine: Union[str, None] = None,
    **kwargs,
):
    """Returns polly TTS audio file from given Text"""
    output: Union[str, None]; speech: Union[object, None]; \
        stream: Union[object, None] = None, None, None
    dispatcher: Union[Dispatcher, None] = Dispatcher.get_current()
    if dispatcher is not None:
        Engine: str = dispatcher.config.furhat.get('synthesizer').get(
            'amazon').get('engine')
        VoiceId: str = dispatcher.config.furhat.get('voice')
        LanguageCode: str = dispatcher.config.furhat.get('language')
    Extension: str = kwargs.get('Extension', 'ogg')
    try:
        speech: dict = ((await get_session()).client('polly')
            ).synthesize_speech(
            Engine = Engine,
            LanguageCode = LanguageCode,
            Text = Text,
            OutputFormat = OutputFormat,
            VoiceId = VoiceId,
        )
        if 'AudioStream' in speech:
            with closing(speech['AudioStream']) as stream:
                output: str = os.path.join(gettempdir(), "ic.{}.{}".format(
                    uuid.uuid4(), Extension))
                with open(output, "wb") as _file:
                    _file.write(stream.read())
                return output
    except (BotoCoreError, ClientError, FileNotFoundError, IOError) as e:
        logging.exception(e)
        output.close()
    finally:
        del(stream)
        del(speech)
