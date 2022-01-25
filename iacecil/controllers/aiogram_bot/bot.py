# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://github.com/iuriguilherme>
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

import asyncio, logging, re, sys
from textwrap import wrap
from aiogram import (
    Bot,
    exceptions,
    types,
)
from aiogram.utils import markdown
from iacecil.controllers.aiogram_bot.callbacks import (
    error_callback,
    exception_callback,
)

## Sub class of aiogram.Bot made to add exception handling
class IACecilBot(Bot):
    def __init__(self, *args, **kwargs):
        config = kwargs.get('config')
        name = kwargs.get('name', 'iacecil')
        setattr(self, 'info',
        config.bots[name]['info'] or config.default_bot['info'])
        setattr(self, 'plugins',
        config.bots[name]['plugins'] or config.default_bot['plugins'])
        setattr(self, 'users',
        config.bots[name]['users'] or config.default_bot['users'])
        kwargs.pop('config', None)
        kwargs.pop('name', None)
        self.command = None
        super().__init__(*args, **kwargs)

    async def send_photo(self, *args, **kwargs):
        self.command = None
        try:
            self.command = await super().send_voice(*args, **kwargs)
            return self.command
        except exceptions.RetryAfter as exception:
            logging.info(u"Flood control: waiting {} seconds...\
            ".format(exception.timeout))
            await asyncio.sleep(exception.timeout)
            return await self.send_photo(*args, **kwargs)
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendPhoto'],
                )
            except Exception as e:
                logging.critical(repr(e))
        return self.command

    async def send_voice(self, *args, **kwargs):
        self.command = None
        try:
            self.command = await super().send_voice(*args, **kwargs)
            return self.command
        except exceptions.RetryAfter as exception:
            logging.info(u"Flood control: waiting {} seconds...\
            ".format(exception.timeout))
            await asyncio.sleep(exception.timeout)
            return await self.send_voice(*args, **kwargs)
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendVoice'],
                )
            except Exception as e:
                logging.critical(repr(e))
        return self.command

    async def send_video(self, *args, **kwargs):
        self.command = None
        try:
            self.command = await super().send_video(*args, **kwargs)
            return self.command
        except exceptions.RetryAfter as exception:
            logging.info(u"Flood control: waiting {} seconds...\
            ".format(exception.timeout))
            await asyncio.sleep(exception.timeout)
            return await self.send_video(*args, **kwargs)
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendVideo'],
                )
            except Exception as e:
                logging.critical(repr(e))
        return self.command

    async def send_message(self, *args, **kwargs):
        self.command = None
        try:
            self.command = await super().send_message(*args, **kwargs)
            return self.command
        except exceptions.RetryAfter as exception:
            logging.info(u"Flood control: waiting {} seconds...\
            ".format(exception.timeout))
            await asyncio.sleep(exception.timeout)
            return await self.send_message(*args, **kwargs)
        except exceptions.BotKicked as exception:
            if kwargs['chat_id'] in [
                self.users['special']['debug'],
                self.users['special']['info']
            ]:
                sys.exit(u"""\n***TERMINATED***\nBot was kicked from th\
e logging groups! Fix this before continuing! Either change the ids fro\
m the log  groups in the config file, or ensure the bot is part of the \
logging groups. Exiting...""")
            else:
                try:
                    await error_callback(
                        u"Probably kicked from this group",
                        str(self.command),
                        exception,
                        ['sendMessage', 'BotKicked', 'exception'],
                    )
                except Exception as e:
                    try:
                        await exception_callback(
                            e,
                            ['sendMessage', 'BotKicked'],
                        )
                    except Exception as e:
                        logging.warning(repr(e))
        except exceptions.TelegramAPIError as exception:
            descriptions = {
                'too_long': "MessageIsTooLong('Message is too long')",
                'rights': """BadRequest('Have no rights to send a messa\
ge')""",
                'not_found': "BadRequest('Replied message not found')",
            }
            reason = u"I don't know what just happened"
            reply = self.command
            if repr(exception) == descriptions['rights']:
                reason = None
                logging.info(
                    u"Bot has no rights in {}, skipping...".format(
                        reply['chat']['id'],
                ))
            elif repr(exception) == descriptions['not_found']:
                reason = u"Probably message has been erased already"
            elif repr(exception) == descriptions['too_long']:
                reason = u"Message is too long"
                limit = 2048 # Telegram limit is 4096
                text = kwargs.get('text', u"empty")
                if len(text) >= limit:
                    logging.info(
                        u"Message is too long, stripping...",
                    )
                    chunks = [text[i:i+limit] for i in range(
                        0, len(text), limit)
                    ]
                    for count, chunk in enumerate(chunks, start = 1):
                        chunk = chunk.translate(
                            str.maketrans('', '', '\\`')
                        )
                        kwargs['text'] = markdown.escape_md(
                            u"#thread ({}/{}):\n\n".format(count, 
                            len(chunks))
                        ) + markdown.pre(chunk)
                        await self.send_message(*args, **kwargs)
                self.command['text'] = u"empty"
                return self.command
            if reason is not None:
                try:
                    await error_callback(
                        reason,
                        self.command,
                        exception,
                        ['sendMessage', 'TelegramAPIError',
                            'exception'],
                    )
                except Exception as e:
                    try:
                        await exception_callback(
                            e,
                            ['sendMessage', 'TelegramAPIError'],
                        )
                    except Exception as e:
                        logging.critical(repr(e))
        except exceptions.BotBlocked as exception:
            try:
                await error_callback(
                    u"Probably blocked by this user",
                    self.command,
                    exception,
                    ['sendMessage', 'BotBlocked', 'exception'],
                )
            except Exception as e:
                try:
                    await exception_callback(
                        e,
                        ['sendMessage', 'BotBlocked'],
                    )
                except Exception as e:
                    logging.warning(repr(e))
        except exceptions.ChatNotFound as exception:
            try:
                await error_callback(
                    u"Probably group pressed the red button",
                    self.command,
                    exception,
                    ['sendMessage', 'ChatNotFound', 'exception'],
                )
            except Exception as e:
                try:
                    await exception_callback(
                        e,
                        ['sendMessage', 'ChatNotFound'],
                    )
                except Exception as e:
                    logging.critical(repr(e))
        except exceptions.UserDeactivated as exception:
            try:
                await error_callback(
                    u"Probably the user pressed the red button",
                    self.command,
                    exception,
                    ['sendMessage', 'UserDeactivated', 'exception'],
                )
            except Exception as e:
                try:
                    await exception_callback(
                        e,
                        ['sendMessage', 'UserDeactivated'],
                    )
                except Exception as e:
                    logging.warning(repr(e))
        except exceptions.TerminatedByOtherGetUpdates as exception:
            logging.critical(u"""Trying to login with the same token el\
sewhere!\n{}""".format(repr(exception)))
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'NotTelegram'],
                )
            except Exception as e:
                logging.warning(repr(e))
        return self.command
