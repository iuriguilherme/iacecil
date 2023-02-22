"""
ia.cecil

Copyleft 2020-2023 Iuri Guilherme <https://iuri.neocities.org/>

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
logger: logging.Logger = logging.getLogger(__name__)

import aiohttp
import openai
logging.getLogger('openai').setLevel('INFO')

from urllib3.exceptions import (
    MaxRetryError,
    NewConnectionError,
)

async def openai_start_session(api_key: str, *args, **kwargs) -> bool:
    """Start new async session"""
    try:
        openai.api_key: str = api_key
        openai.aiosession.set(aiohttp.ClientSession())
        return bool(openai.aiosession.get())
    except Exception as e:
        logger.exception(e)
        return False

async def openai_stop_session(*args, **kwargs) -> None:
    """Close current async session"""
    try:
        if openai.aiosession.get() is not None:
            await openai.aiosession.get().close()
    except Exception as e:
        logger.exception(e)
        logger.critical("OpenAI session may be still open")

async def get_completion(*args, **kwargs) -> str | None:
    """https://platform.openai.com/docs/api-reference/completions"""
    try:
        if openai.aiosession.get() is None:
            print("Session with OpenAI was closed, opening.", end = '')
            while not await openai_start_session(kwargs.get('api_key')):
                print(".", end = '')
        ckwargs: dict = {k: kwargs[k] for k in [
            'suffix',
            'n',
            'stream',
            'logpbrobs',
            'echo',
            'stop',
            'presence_penalty',
            'frequency_penalty',
            'best_of',
            'logit_bias',
        ] if k in kwargs}
        ckwargs['prompt'] = kwargs.get('prompt')
        ckwargs['model'] = kwargs.get('model', 'text-davinci-003')
        ckwargs['max_tokens'] = kwargs.get('model', 4000) - \
            len(ckwargs['prompt'])
        ckwargs['user'] = kwargs.get('user', str(None))
        if 'temperature' in kwargs:
            ckwargs['temperature'] = kwargs['temperature']
        elif 'top_p' in kwargs:
            ckwargs['top_p'] = kwargs['top_p']
        logger.info("""Fazendo requisição para completação com a API \
do OpenAI. Se isto travar, vai travar o loop inteiro. Aí, só esperando \
dar timeout xD...""")
        return openai.Completion.create(**ckwargs)
    except (
        openai.error.RateLimitError,
        openai.error.ServiceUnavailableError,
        openai.error.Timeout,
    ) as e:
        logger.exception(e)
    except (
        openai.error.APIError,
        openai.error.InvalidRequestError,
        Exception,
    ) as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)
    return None
