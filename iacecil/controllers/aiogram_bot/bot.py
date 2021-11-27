# -*- coding: utf-8 -*-
#
#    ia.cecil
#    
#    Copyleft 2012-2021 Iuri Guilherme <https://github.com/iuriguilherme>
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#    MA 02110-1301, USA.
#    

import asyncio, logging, sys

from aiogram import (
    Bot,
    exceptions,
    types,
)

from iacecil.controllers.aiogram_bot.callbacks import (
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
        super().__init__(*args, **kwargs)

    async def send_message(self, *args, **kwargs):
        try:
            return await super().send_message(*args, **kwargs)
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
                    await exception_callback(
                        exception,
                        ['sendMessage', 'BotKicked'],
                    )
                except Exception as e:
                    logging.warning(repr(e))
        except exceptions.BotBlocked as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'BotBlocked'],
                )
            except Exception as e:
                logging.warning(repr(e))
        except exceptions.ChatNotFound as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'ChatNotFound'],
                )
                message = kwargs.get('message')
            except Exception as e:
                logging.warning(repr(e))
        except exceptions.UserDeactivated as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'UserDeactivated'],
                )
                message = kwargs.get('message')
            except Exception as e:
                logging.warning(repr(e))
        except exceptions.TelegramAPIError as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'TelegramAPIError'],
                )
                message = kwargs.get('message')
            except Exception as e:
                logging.warning(repr(e))
        except exceptions.TerminatedByOtherGetUpdates as exception:
            logging.warning(repr(exception))
        except Exception as exception:
            try:
                await exception_callback(
                    exception,
                    ['sendMessage', 'NotTelegram'],
                )
            except Exception as e:
                logging.warning(repr(e))
        return None
