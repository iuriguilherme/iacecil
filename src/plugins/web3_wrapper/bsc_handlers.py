"""
Plugin web3_wrapper para ia.cecil: Experimentos com web3

ia.cecil

Copyleft 2021-2025 Iuri Guilherme <https://iuri.neocities.org/>

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

import web3
from aiogram.utils.markdown import (
    escape_md,
    bold,
    code,
    spoiler,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

async def add_handlers(dispatcher, get_web3, get_async_web3):
    @dispatcher.message_handler(commands = ['btest', 'btes', 'bte'])
    async def btest_callback(message):
        try:
            await message_callback(message, ['web3', 'btest',
                message.chat.type])
            w3 = await get_async_web3(dispatcher.bot.config['info'][
                'web3']['binance']['bsc_mainnet'])
            command = await message.reply(await w3.isConnected())
            await command_callback(command, ['web3', 'btest',
                message.chat.type])
        except Exception as exception:
            await error_callback(
                'btest error',
                message,
                exception,
                ['exception', 'web3', 'btest'],
            )
    
    @dispatcher.message_handler(commands = ['bblock', 'bblo', 'bbl'])
    async def bblock_callback(message):
        try:
            await message_callback(message, ['web3', 'bblock',
                message.chat.type])
            w3 = await get_async_web3(dispatcher.bot.config['info'][
                'web3']['binance']['bsc_mainnet'])
            block = 'latest'
            if message.get_args() not in [None, '', ' ']:
                block = message.get_args()
            response = await w3.eth.get_block(block)
            command = await message.reply(str(response))
            await command_callback(command, ['web3', 'bblock',
                message.chat.type])
        except Exception as exception:
            await error_callback(
                'bblock error',
                message,
                exception,
                ['exception', 'web3', 'bblock'],
            )
    
    @dispatcher.message_handler(commands = ['bbalance', 'bbal', 'bba',
        'bb'])
    async def bbalance_callback(message):
        try:
            await message_callback(message, ['web3', 'bbalance',
                message.chat.type])
            if message.get_args() not in [None, '', ' ']:
                w3 = await get_async_web3(dispatcher.bot.config['info'][
                    'web3']['binance']['bsc_mainnet'])
                address = message.get_args()
                balance = await w3.eth.get_balance(address)
                command = await message.reply(u"Balance: {} BNB".format(
                    w3.fromWei(balance, 'ether')))
                await command_callback(command, ['web3', 'bbalance',
                    message.chat.type])
        except Exception as exception:
            await error_callback(
                'bbalance error',
                message,
                exception,
                ['exception', 'web3', 'bbalance'],
            )
    
    @dispatcher.message_handler(commands = ['btransaction', 'btrans',
        'btx', 'bt'])
    async def btransaction_callback(message):
        try:
            await message_callback(message, ['web3', 'btransaction',
                message.chat.type])
            if message.get_args() not in [None, '', ' ']:
                w3 = await get_async_web3(dispatcher.bot.config['info'][
                    'web3']['binance']['bsc_mainnet'])
                txid = message.get_args()
                tx = await w3.eth.get_transaction(txid)
                reply = u"Transaction not found"
                if tx is not None:
                    reply = str(tx)
                command = await message.reply(reply)
                await command_callback(command, ['web3', 'btransaction',
                    message.chat.type])
        except Exception as exception:
            await error_callback(
                'btransaction error',
                message,
                exception,
                ['exception', 'web3', 'btransaction'],
            )
    
    ## WARNING never log those callbacks, users are supposed to handle
    ## private keys of their wallets
    @dispatcher.message_handler(commands = ['bcreate', 'bcre', 'bcr',
        'bc'])
    async def bcreate_callback(message):
        try:
            # ~ w3 = await get_async_web3(dispatcher.bot.config['info'][
                # ~ 'web3']['binance']['bsc_mainnet'])
            w3 = await get_web3(dispatcher.bot.config['info'][
                'web3']['binance']['bsc_mainnet'])
            account = None
            if message.get_args() not in [None, '', ' ']:
                # ~ account = await w3.eth.accounts.privateKeyToAccount(
                    # ~ message.get_args())
                account = w3.eth.account.privateKeyToAccount(
                    message.get_args())
            else:
                # ~ account = await w3.eth.account.create()
                account = w3.eth.account.create()
                command = await message.reply(
                    ''.join([
                        escape_md('New BNB account created.\n\n'),
                        bold("""WARNING: This is not a safe way to hand\
le private keys. This account shall be used for learning and testing pu\
rposes. Don't trust too much funds for too much time with addresses gen\
erated in such a way."""),
                        escape_md('\n\nAddress: '),
                        '{}'.format(code(str(account.address))),
                        escape_md('\n\nPrivate Key: '),
                        '{}'.format(spoiler(account.key.hex())),
                    ]),
                        parse_mode = 'MarkdownV2',
                )
        except Exception as exception:
            await error_callback(
                'bcreate error',
                message,
                exception,
                ['exception', 'web3', 'bcreate'],
            )
