"""
Plugin web3_wrapper para ia.cecil: Experimentos com web3

ia.cecil

Copyleft 2021-2022 Iuri Guilherme <https://iuri.neocities.org/>

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
from web3 import (
    Web3,
    AsyncHTTPProvider,
    HTTPProvider,
)
from web3.middleware import (
    async_geth_poa_middleware,
    geth_poa_middleware,
)
from web3.eth import AsyncEth
from web3.net import AsyncNet
from web3.geth import (
    Geth,
    AsyncGethAdmin,
    AsyncGethPersonal,
    AsyncGethTxPool,
)
from .bsc_handlers import add_handlers as add_bsc_handlers
from .eth_handlers import add_handlers as add_eth_handlers

async def get_web3(provider):
    w3 = Web3(HTTPProvider(provider))
    w3.middleware_onion.inject(geth_poa_middleware, layer = 0)
    return w3

async def get_async_web3(provider):
    return Web3(
        AsyncHTTPProvider(provider),
        modules = {
            'eth': (AsyncEth),
            'geth': (
                Geth,
                {
                    'admin' : (AsyncGethAdmin),
                    'personal': (AsyncGethPersonal),
                    'txpool': (AsyncGethTxPool),
                },
            ),
            'net': (AsyncNet),
        },
        middlewares = [
            async_geth_poa_middleware,
        ],
    )

async def add_handlers(dispatcher):
    try:
        await add_bsc_handlers(dispatcher, get_web3, get_async_web3)
        await add_eth_handlers(dispatcher, get_web3, get_async_web3)
    except Exception as exception:
        raise
