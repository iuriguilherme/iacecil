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

import boto3, os, subprocess, sys, uuid
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
from tempfile import gettempdir
from aiogram import Dispatcher

try:
    from instance.config import Config
    config = Config()
except Exception as exception:
    logger.critical(u"""{} config file not found or somehow wrong. RTFM\
.\n{}""".format(actual_name, str(exception)))
    raise

async def get_session(region = 'us-east-1'):
    return boto3.Session(
        aws_access_key_id = config.furhat['synthesizer']['amazon'][
            'key'],
        aws_secret_access_key = config.furhat['synthesizer']['amazon'][
            'secret'],
        region_name = 'us-east-1',
    )

async def get_audio(
    Text = None,
    LanguageCode = 'pt-BR',
    VoiceId = 'Camila',
    OutputFormat = 'ogg_vorbis',
    Engine = config.furhat['synthesizer']['amazon']['engine'],
    **kwargs,
):
    output = None
    dispatcher = Dispatcher.get_current()
    Engine = dispatcher.bot.config['furhat']['synthesizer']['amazon'][
        'engine']
    VoiceId = dispatcher.bot.config['furhat']['voice']
    try:
        speech = ((await get_session()).client('polly')
            ).synthesize_speech(
            Engine = Engine,
            LanguageCode = LanguageCode,
            Text = Text,
            OutputFormat = OutputFormat,
            VoiceId = VoiceId,
        )
        if 'AudioStream' in speech:
            with closing(speech['AudioStream']) as stream:
                output = os.path.join(gettempdir(), "{}.ogg".format(
                    uuid.uuid4()))
                with open(output, "wb") as file:
                    file.write(stream.read())
                return output
    except IOError as exception:
        logging.debug(repr(exception))
    except BotoCoreError as exception:
        logging.debug(repr(exception))
    except ClientError as exception:
        logging.debug(repr(exception))
    except FileNotFoundError as exception:
        logging.debug(repr(exception))
    except Exception as exception:
        logging.warning(repr(exception))
