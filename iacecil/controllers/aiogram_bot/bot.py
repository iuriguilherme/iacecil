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

import asyncio, logging, sys
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

    async def send_message(self, *args, **kwargs):
        try:
            self.command = await super().send_message(*args, **kwargs)
            return self.command
        except exceptions.RetryAfter as exception:
            logging.warning(u"Flood control: waiting {} seconds...\
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
                        str(kwargs),
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
            # ~ description = kwargs.get('description', None)
            reason = u"I don't know what just happened"
            # ~ logging.debug(u"""\ntype(args): {args_type}\nargs: {args}\n\
# ~ type(kwargs): {kwargs_type}\nkwargs: {kwargs}\ndescription: \
# ~ {description}\n'too_long': {too_long} {is_too_long}\n'rights': {rights}\
 # ~ {is_rights}\nexception: {exception}\n""".format(
                # ~ kwargs_type = type(kwargs),
                # ~ kwargs = str(kwargs),
                # ~ args_type = type(args),
                # ~ args = str(args),
                # ~ description = description,
                # ~ too_long = descriptions['too_long'],
                # ~ is_too_long = (
                    # ~ descriptions['too_long'] == repr(exception)),
                # ~ rights = descriptions['rights'],
                # ~ is_rights = (
                    # ~ descriptions['rights'] == repr(exception)),
                # ~ exception = repr(exception),
            # ~ ))
            if repr(exception) == descriptions['rights']:
                reason = u"Probably blocked in this group"
            elif repr(exception) == descriptions['not_found']:
                reason = u"Probably message has been erased already"
            elif repr(exception) == descriptions['too_long']:
                reason = u"Message is too long"
                if kwargs.get('text', '') != '':
                    kwargs['text'] = 'apagado'
                # ~ logging.warning(
                    # ~ u"Message is too long, stripping...",
                # ~ )
                # ~ limit = 4000 # Telegram limit is 4096
                # ~ text = kwargs.get('text', 'nada')
                # ~ chunks = [text[i:i+limit] for i in range(
                    # ~ 0, len(text), limit)
                # ~ ]
                # ~ chunks = wrap(text, limit)
                # ~ for count, chunk in enumerate(chunks):
                    # ~ if kwargs.get('parse_mode', None) == "MarkdownV2":
                        # ~ chunk = chunk.translate(
                            # ~ str.maketrans('', '', '\\`')
                        # ~ )
                        # ~ chunk = markdown.pre(chunk)
                    # ~ logging.debug(markdown.escape_md(
                        # ~ u"\n#thread ({}/{}):\n\n{}".format(count, 
                        # ~ len(chunks))) + chunk
                    # ~ )
                    # ~ logging.debug(
                        # ~ u"\n#thread ({}/{}):\n\n".format(count, 
                        # ~ len(chunks))
                    # ~ )
                    # ~ return await self.send_message(*args, **kwargs)
                    # ~ pass
            try:
                await error_callback(
                    reason,
                    str(kwargs),
                    exception,
                    ['sendMessage', 'TelegramAPIError', 'exception'],
                )
            except Exception as e:
                try:
                    await exception_callback(
                        e,
                        ['sendMessage', 'TelegramAPIError'],
                    )
                except Exception as e:
                    logging.warning(repr(e))
        except exceptions.BotBlocked as exception:
            try:
                await error_callback(
                    u"Probably blocked by this user",
                    str(kwargs),
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
                    str(kwargs),
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
                    logging.warning(repr(e))
        except exceptions.UserDeactivated as exception:
            try:
                await error_callback(
                    u"Probably the user pressed the red button",
                    str(kwargs),
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
            logging.warning(u"""Trying to login with the same token els\
ewhere!\n{}""".format(repr(exception)))
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'NotTelegram'],
                )
            except Exception as e:
                logging.warning(repr(e))
        return None
