"""
Plugin cryptoforex para ia.cecil: Comandos para conversão de criptomoedas

ia.cecil

Copyleft 2016-2025 Iuri Guilherme <https://iuri.neocities.org/>

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

import json
from requests import (
    Request,
    Session,
)
from requests.exceptions import (
    ConnectionError,
    Timeout,
    TooManyRedirects,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    exception_callback,
)

async def price_v1(token, coin, converts):
    """https://coinmarketcap.com/api/documentation/v1/#operation/getV1C\
ryptocurrencyQuotesLatest"""

    url = '''https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes\
/latest'''

    parameters = {
        'symbol': coin,
        'aux': ','.join(['is_fiat', 'volume_7d', 'volume_30d',
            'circulating_supply', 'total_supply']),
        # 'convert': ','.join(converts)
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': token,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as exception:
        await exception_callback(exception, ['cryptoforex',
            'coinmarketcap', 'price', 'price_v1'])
        raise

async def conv_v2(token, amount, symbol, convert):
    """https://coinmarketcap.com/api/documentation/v1/#operation/getV2T\
oolsPriceconversion"""

    url = 'https://pro-api.coinmarketcap.com/v2/tools/price-conversion'

    parameters = {
        'amount': amount,
        'symbol': symbol,
        'convert': convert,
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': token,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as exception:
        await exception_callback(exception, ['cryptoforex',
            'coinmarketcap', 'conv', 'conv_v2'])
        raise

async def get_fiat_id(token, symbol):
    """https://coinmarketcap.com/api/documentation/v1/#operation/getV1F\
iatMap"""

    url = 'https://pro-api.coinmarketcap.com/v1/fiat/map'

    parameters = {
        ' include_metals': 'true',
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': token,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        try:
            return [slug for slug in data['data'] if \
                slug['symbol'] == symbol.upper()][0]
        except Exception as exception:
            return {'id': 0, 'name': "Nenhuma", 'sign': '$',
                'symbol': 'NAC'}
    except (ConnectionError, Timeout, TooManyRedirects) as exception:
        await exception_callback(exception, ['cryptoforex',
            'coinmarketcap', 'fiat', 'get_fiat_id'])
        raise

