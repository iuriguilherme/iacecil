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
from eth_account import Account
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)

async def add_handlers(dispatcher, get_web3, get_async_web3):
    @dispatcher.message_handler(commands = ['etest', 'etes', 'ete'])
    async def etest_callback(message):
        try:
            await message_callback(message, ['web3', 'etest',
                message.chat.type])
            w3 = await get_async_web3(dispatcher.bot.config['info'][
                'web3']['infura']['eth_mainnet'])
            command = await message.reply(await w3.isConnected())
            await command_callback(command, ['web3', 'etest',
                message.chat.type])
        except Exception as exception:
            await error_callback(
                'etest error',
                message,
                exception,
                ['exception', 'web3', 'etest'],
            )
    
    @dispatcher.message_handler(commands = ['eblock', 'eblo', 'ebl'])
    async def eblock_callback(message):
        try:
            await message_callback(message, ['web3', 'eblock',
                message.chat.type])
            w3 = await get_async_web3(dispatcher.bot.config['info'][
                'web3']['infura']['eth_mainnet'])
            block = 'latest'
            if message.get_args() not in [None, '', ' ']:
                block = message.get_args()
            response = await w3.eth.get_block(block)
            command = await message.reply(str(response))
            await command_callback(command, ['web3', 'eblock',
                message.chat.type])
        except Exception as exception:
            await error_callback(
                'eblock error',
                message,
                exception,
                ['exception', 'web3', 'eblock'],
            )
    
    @dispatcher.message_handler(commands = ['ebalance', 'ebal', 'eba',
        'eb'])
    async def ebalance_callback(message):
        try:
            await message_callback(message, ['web3', 'ebalance',
                message.chat.type])
            if message.get_args() not in [None, '', ' ']:
                w3 = await get_async_web3(dispatcher.bot.config['info'][
                    'web3']['infura']['eth_mainnet'])
                address = message.get_args()
                balance = await w3.eth.get_balance(address)
                command = await message.reply(u"Balance: {} ETH".format(
                    w3.fromWei(balance, 'ether')))
                await command_callback(command, ['web3', 'ebalance',
                    message.chat.type])
        except Exception as exception:
            await error_callback(
                'ebalance error',
                message,
                exception,
                ['exception', 'web3', 'ebalance'],
            )
    
    @dispatcher.message_handler(commands = ['etransaction', 'etrans',
        'etx', 'et'])
    async def etransaction_callback(message):
        try:
            await message_callback(message, ['web3', 'etransaction',
                message.chat.type])
            if message.get_args() not in [None, '', ' ']:
                w3 = await get_async_web3(dispatcher.bot.config['info'][
                    'web3']['infura']['eth_mainnet'])
                txid = message.get_args()
                tx = await w3.eth.get_transaction(txid)
                reply = u"Transaction not found"
                if tx is not None:
                    reply = str(tx)
                command = await message.reply(reply)
                await command_callback(command, ['web3', 'etransaction',
                    message.chat.type])
        except Exception as exception:
            await error_callback(
                'etransaction error',
                message,
                exception,
                ['exception', 'web3', 'etransaction'],
            )
    
    ## WARNING never log those callbacks, users are supposed to handle
    ## private keys of their wallets
    @dispatcher.message_handler(commands = ['ecreate', 'ecr', 'ec'])
    async def ecreate_callback(message):
        try:
            account = None
            if message.get_args() not in [None, '', ' ']:
                account = Account.privateKeyToAccount(
                    message.get_args())
            else:
                account = Account.create()
                command = await message.reply(
                    ''.join([
                        escape_md('New ETH account created.\n\n'),
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
                'ecreate error',
                message,
                exception,
                ['exception', 'web3', 'ecreate'],
            )
