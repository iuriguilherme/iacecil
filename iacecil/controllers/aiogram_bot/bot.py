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

    async def exception_handler(
        self,
        function,
        function_name,
        super_function,
        *args,
        **kwargs,
    ):
        self.command = None
        try:
            self.command = await super_function(*args, **kwargs)
            return self.command
        except exceptions.RetryAfter as exception:
            logging.info(u"Flood control: waiting {} seconds...\
            ".format(exception.timeout))
            await asyncio.sleep(exception.timeout)
            return await function(*args, **kwargs)
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
                        [function_name, 'BotKicked', 'exception'],
                    )
                except Exception as e1:
                    try:
                        await exception_callback(
                            e1,
                            [function_name, 'BotKicked'],
                        )
                    except Exception as e2:
                        logging.warning(repr(e2))
        except exceptions.BotBlocked as exception:
            try:
                await error_callback(
                    u"Probably blocked by this user",
                    self.command,
                    exception,
                    [function_name, 'BotBlocked', 'exception'],
                )
            except Exception as e1:
                try:
                    await exception_callback(
                        e1,
                        [function_name, 'BotBlocked'],
                    )
                except Exception as e2:
                    logging.warning(repr(e2))
        except exceptions.ChatNotFound as exception:
            try:
                await error_callback(
                    u"Probably group pressed the red button",
                    self.command,
                    exception,
                    [function_name, 'ChatNotFound', 'exception'],
                )
            except Exception as e1:
                try:
                    await exception_callback(
                        e1,
                        [function_name, 'ChatNotFound'],
                    )
                except Exception as e2:
                    logging.critical(repr(e2))
        except exceptions.UserDeactivated as exception:
            try:
                await error_callback(
                    u"Probably the user pressed the red button",
                    self.command,
                    exception,
                    [function_name, 'UserDeactivated', 'exception'],
                )
            except Exception as e1:
                try:
                    await exception_callback(
                        e1,
                        [function_name, 'UserDeactivated'],
                    )
                except Exception as e2:
                    logging.warning(repr(e2))
        except exceptions.TerminatedByOtherGetUpdates as exception:
            logging.critical(u"""Trying to login with the same token el\
sewhere!\n{}""".format(repr(exception)))
        except exceptions.TelegramAPIError as exception:
            descriptions = {
                'too_long': "MessageIsTooLong('Message is too long')",
                'rights': """BadRequest('Have no rights to send a messa\
ge')""",
                'not_found': "BadRequest('Replied message not found')",
                'deactivated': """UserDeactivated('Forbidden: user is d\
eactivated')""",
            }
            reason = u"I don't know what just happened"
            if repr(exception) == descriptions['rights']:
                reason = None
                chat_id = 0
                try:
                    chat_id = self.command.chat.id
                except AttributeError:
                    pass
                logging.info(
                    u"Bot has no rights in {}, skipping...".format(
                        str(chat_id),
                ))
            elif repr(exception) == descriptions['not_found']:
                reason = u"Probably message has been erased already"
            elif repr(exception) == descriptions['deactivated']:
                reason = u"Probably user no longer exists"
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
                        await function(*args, **kwargs)
                self.command['text'] = u"empty"
                return self.command
            if reason is not None:
                try:
                    await error_callback(
                        reason,
                        self.command,
                        exception,
                        [function_name, 'TelegramAPIError',
                            'exception'],
                    )
                except Exception as e1:
                    try:
                        await exception_callback(
                            e1,
                            [function_name, 'TelegramAPIError'],
                        )
                    except Exception as e2:
                        logging.critical(repr(e2))
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    [function_name, 'NotTelegram'],
                )
            except Exception as e:
                logging.warning(repr(e))
        return self.command

    async def send_photo(self, *args, **kwargs):
        return await self.exception_handler(
            self.send_photo,
            'sendPhoto',
            super().send_photo,
            *args,
            **kwargs,
        )

    async def send_voice(self, *args, **kwargs):
        return await self.exception_handler(
            self.send_voice,
            'sendVoice',
            super().send_voice,
            *args,
            **kwargs,
        )

    async def send_video(self, *args, **kwargs):
        return await self.exception_handler(
            self.send_video,
            'sendVideo',
            super().send_video,
            *args,
            **kwargs,
        )

    async def send_message(self, *args, **kwargs):
        return await self.exception_handler(
            self.send_message,
            'sendMessage',
            super().send_message,
            *args,
            **kwargs,
        )
