"""
Plugin garimpo para ia.cecil: Coleta links

ia.cecil

Copyleft 2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import BTrees
import transaction
import validators
import ZODB
from aiogram import (
    Dispatcher,
    filters,
    types,
)
from aiogram.utils.markdown import escape_md
from typing import Union
from iacecil import (
    commit,
    name,
    version,
)
from iacecil.controllers.persistence.zodb_orm import get_messages_garimpo
from iacecil.controllers.log import (
    info_logger,
    debug_logger,
    exception_logger,
    zodb_logger,
)

async def varre_link(message: str) -> Union[types.Message, None]:
    """
    Procura link na mensagem e se encontra, armazena no banco de dados,
    envia para o grupo de garimpo de links
    """
    try:
        dispatcher = Dispatcher.get_current()
        if dispatcher.config.get('personalidade', None) in [
            'default',
            'metarec',
            'matebot',
            'iacecil',
        ]:
            url = None
            garimpo_id = dispatcher.config.telegram.get('users').get('special'
                ).get('garimpo')
            if message.entities is not None:
                for entity in message.entities:
                    if entity['type'] == "url":
                        url =  message.text[
                            entity['offset']:entity['length'] + \
                            entity['offset']
                        ]
            if url and validators.url(url):
                fw_message = await message.forward(
                    chat_id = garimpo_id,
                )
                db = None
                try:
                    db, pms = await get_messages_garimpo(garimpo_id)
                    try:
                        try:
                            pfm = pms[fw_message.message_id]
                        except KeyError:
                            pms[fw_message.message_id] = \
                                BTrees.OOBTree.OOBTree()
                            pfm = pms[fw_message.message_id]
                        pfm[name + '_version'] = version
                        pfm[name + '_commit'] = commit
                        pfm['chat_id'] = message.chat.id
                        pfm['reply_to_message_id'] = message.message_id
                        transaction.commit()
                    except Exception as e1:
                        transaction.abort()
                        await debug_logger(
                            u"Message NOT added to database",
                            message,
                            e1,
                            ['garimpo', 'varre_links', 'zodb',
                                'exception'],
                        )
                    finally:
                        try:
                            db.close()
                        except Exception as e2:
                            logger.warning(u"""db was never created on\
{}: {}""".format(__name__, repr(e2),))
                except Exception as e3:
                    await exception_logger(
                        e3,
                        ['garimpo', 'varre_links', 'zodb'],
                    )
                return fw_message
    except Exception as exception:
        await debug_logger(u"Erro tentando garimpar link", message,
            exception, ['garimpo', 'exception'],
        )
        return None

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register Aiogram Handlers to Dispatcher"""
    try:
        ## Pra onde VAI
        garimpo_id = dispatcher.config.telegram.get('users').get('special'
            ).get('garimpo')
        ## De onde VEM
        garimpos_ids = dispatcher.config.telegram.get('users').get('garimpo')
        ## Salva link em outro grupo

        ## FIXME implementar garimpo total (garimpa_tudo_callback) com
        ## filtro de chat_id em grupos exclusivos, e estes dois outros
        ## filtros em todos grupos
        # ~ @dispatcher.message_handler(filters.Command([
            # ~ 'g', 'garimpo', 'garimpa', 'salva', 'verdepois', 'vouver',
        # ~ ]))
        # ~ async def garimpo_callback(message):
            # ~ await info_logger(message, ['garimpo', message.chat.type])
            # ~ command = await varre_link(message)
            # ~ await info_logger(command, ['command', 'garimpo',
                # ~ message.chat.type],
            # ~ )

        # ~ @dispatcher.message_handler(filters.Text([
            # ~ 'depois eu vejo',
            # ~ 'um dia eu vejo',
            # ~ 'uma hora eu vejo',
            # ~ 'vou ver',
            # ~ 'já vejo',
            # ~ 'salva',
            # ~ 'garimpo',
            # ~ 'garimpa',
        # ~ ]))
        # ~ async def procastinacao_callback(message):
            # ~ await info_logger(message, ['procastinacao',
                # ~ message.chat.type])
            # ~ if message.reply_to_message is not None:
                # ~ command = await varre_link(message.reply_to_message)
                # ~ await info_logger(command, ['command', 'procastinacao',
                    # ~ message.chat.type]
                # ~ )

        ## Encaminha respostas para links
        @dispatcher.message_handler(filters.IDFilter(chat_id = garimpo_id))
        async def forward_reply_callback(message):
            await zodb_logger(message)
            if 'reply_to_message' in message \
                and message.reply_to_message.is_forward:
                    db = None
                    try:
                        db, pms = await get_messages_garimpo(garimpo_id)
                        try:
                            pfm = pms[
                                message.reply_to_message.message_id]
                            await dispatcher.bot.send_message(
                                chat_id = pfm['chat_id'],
                                # ~ text = f"""
# ~ [{message.from_user.first_name}](tg://user?id={message.from_user.id}) \
# ~ disse: {escape_md(message.text)}""",
                                text = f"""
{message.from_user.first_name} disse: {escape_md(message.text)}""",
                                reply_to_message_id = pfm[
                                    'reply_to_message_id'],
                                parse_mode = 'MarkdownV2',
                                allow_sending_without_reply = True,
                            )
                        except KeyError:
                            pass
                        except Exception as e1:
                            await debug_logger(
                                u"Message NOT retreived from database",
                                message,
                                e1,
                                ['garimpo', 'forward_reply', 'zodb',
                                    'exception'],
                            )
                        finally:
                            try:
                                db.close()
                            except Exception as e2:
                                logger.warning(u"""db was never created\
on {}: {}""".format(__name__, repr(e2),))
                    except Exception as exception:
                        await exception_logger(
                            exception,
                            ['garimpo', 'forward_reply', 'zodb'],
                        )

        ## TODO garimpa todos links de todos grupos pra estas
        ## personalidades
        ## WARNING this must be placed last in handlers
        @dispatcher.message_handler(
            filters.IDFilter(chat_id = garimpos_ids),
            filters.ContentTypeFilter(types.message.ContentType.TEXT),
        )
        async def garimpa_tudo_callback(message):
            await zodb_logger(message)
            command = await varre_link(message)
            if command is not None:
                await info_logger(
                    command,
                    ['command', 'garimpo', message.chat.type],
                )
    except Exception as e:
        logger.exception(e)
        raise
