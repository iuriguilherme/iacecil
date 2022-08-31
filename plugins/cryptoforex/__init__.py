# vim:fileencoding=utf-8
#  Plugin cryptoforex para ia.cecil: Comandos para conversão de 
#   criptomoedas
#  Copyleft (C) 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
logger = logging.getLogger(__name__)

import datetime, locale
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from plugins.cryptoforex.api_coinmarketcap import (
    price_v1 as coinmarketcap_price,
    conv_v2 as coinmarketcap_conv,
)

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'C')
        except Exception as e:
            logger.warning(repr(e))

async def price(dispatcher, message, converts, comando):
    # Presumindo bitcoin quando não há argumentos
    moeda = "BTC"
    if message.get_args() != "":
        moeda = message.get_args()
    ## TODO verificar se a moeda existe
    try:
        resposta = await coinmarketcap_price(
            dispatcher.config['info']['coinmarketcap']['token'],
            moeda,
            converts,
        )
        logger.info(resposta)
        logger.info(type(resposta))
        if resposta['status']['error_code'] > 0:
            await error_callback(
                resposta['status']['error_message'],
                message,
                None,
                ['cryptoforex', 'coinmarketcap', 'price'],
            )
            await message.reply(u"""Erro tentando calcular preço. O pes\
soal que cuida do desenvolvimento já foi avisado, eu acho. Verifique se\
 a moeda existe e o símbolo está correto (por exemplo BTC, LTC, ETH)...\
""")
        else:
            text = """
Price information for {nome} (from coinmarketcap.com)

Price of 1 {simbolo} at {data}:
U$$ {preco_dolar} USD

Marketcap: U$$ {marketcap}

Price change since last
hour: {variacao_1h}%
day: {variacao_1d}%
week: {variacao_1s}%
month: {variacao_1m}%
two months: {variacao_2m}%
three months: {variacao_3m}%

Last 24 hours volume: U$$ {volume_1d}
Last week volume: U$$ {volume_1s}
Last month volume: U$$ {volume_1m}

Available supply: {oferta} {simbolo}
Total supply: {oferta_total} {simbolo}
""".format(
                nome = resposta['data'][moeda.upper()]['name'],
                # '2021-05-03T22:52:02.000Z'
                # ~ data = datetime.datetime.strptime(resposta['data'][
                    # ~ moeda.upper()]['last_updated'],
                    # ~ '%Y-%m-%dT%H:%M:%S.000Z').strftime('%c'),
                ## FIXME: Above code sometimes short circuits
                data = str(datetime.datetime.now()),
                marketcap = '{:,.2f}'.format(float(resposta['data'][
                    moeda.upper()]['quote']['USD']['market_cap'])),
                simbolo = resposta['data'][moeda.upper()]['symbol'],
                preco_dolar = '{:,.2f}'.format(float(resposta['data'][
                    moeda.upper()]['quote']['USD']['price'])),
                ## FIXME converter pra euro e real
                ## tem que pagar um plano mais caro da api da
                ## coinmarketcap e usar o parâmetro convert com
                ## EUR,BRL,BTC
                # ~ preco_euro='{:,.2f}'.format(resposta['data'][
                    # ~ moeda.upper()]['quote']['USD']['price']),
                # ~ preco_real='{:,.2f}'.format(resposta['data'][
                    # ~ moeda.upper()]['quote']['USD']['price']),
                # ~ preco_btc='{:,.8f}'.format(resposta['data'][
                    # ~ moeda.upper()]['quote']['USD']['price']),
                variacao_1h='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['percent_change_1h'
                    ]),
                variacao_1d='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['percent_change_24h'
                    ]),
                variacao_1s='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['percent_change_7d']
                    ),
                variacao_1m='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['percent_change_30d']
                    ),
                variacao_2m='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['percent_change_60d']
                    ),
                variacao_3m='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['percent_change_90d']
                    ),
                volume_1d='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['volume_24h']),
                volume_1s='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['volume_7d']),
                volume_1m='{:,.2f}'.format(resposta['data'][
                    moeda.upper()]['quote']['USD']['volume_30d']),
                oferta='{:,.8f}'.format(resposta['data'][moeda.upper()][
                    'circulating_supply']),
                oferta_total='{:,.8f}'.format(resposta['data'][
                    moeda.upper()]['total_supply']),
            )
            command = await message.reply(text)
            await command_callback(
                command,
                [comando, message.chat.type],
            )
    except Exception as exception:
        await error_callback(
            u"Erro contatando coinmarketcap.com",
            message,
            exception,
            ['cryptoforex', 'price'],
        )
        await message.reply(u"""Erro tentando calcular preço. O pessoal\
 que cuida do desenvolvimento já foi avisado, eu acho...""")

async def conv(dispatcher, message):
    # Presumindo bitcoin quando não há argumentos
    left = "BTC"
    right = "USD"
    try:
        much, left, right = *message.get_args().split(' ')[:2], \
            message.get_args().split(' ')[2:]
    except Exception as exception:
        logger.warning(repr(exception))
        return f"""
Usage: {message.get_command()} 1 BTC USD

Where 1 is the desired amount to convert, BTC is the crypto/fiat to con\
vert FROM and USD is the crypto/fiat to convert TO. In this example we \
convert one Bitcoin to American Dollars, which is the same behaviour of\
 the /price command.

Another example: {message.get_command()} 0.2 ETH BRL

This one show the current value in Brazilian Reals of 0.2 Ethereum.
"""
## FIXME current plan doesn't allow this
# ~ + """
# ~ You can convert to up to 120 fiat / cryptos like this:

# ~ {message.get_command()} 1 BTC USD BRL EUR

# ~ This would show the price of 1 BTC in American Dollars, Brazilian Reals\
# ~ and Euros, respectively.
# ~ """
    ## TODO verificar se a moeda existe
    try:
        response = await coinmarketcap_conv(
            dispatcher.config['info']['coinmarketcap']['token'],
            float(much),
            left,
            ','.join(right),
        )
        if response['status']['error_code'] > 0:
            await error_callback(
                response['status']['error_message'],
                message,
                None,
                ['cryptoforex', 'coinmarketcap', 'conv'],
            )
            return """Erro tentando converter valores. O pessoal que cu\
ida do desenvolvimento já foi avisado, eu acho. Verifique se a moeda ex\
iste, a quantidade é um número e o símbolo está correto (por exemplo BT\
C, LTC, ETH)..."""
        else:
            for conv in response['data']:
                for quote in right:
                    logger.info(f"{conv['amount']} {conv['name']} {conv['quote'][quote.upper()]['price']} {quote.upper()}")
            return '\n'.join([f"""(from coinmarketcap.com): \
{conv['amount']} {conv['name']} = {result}\
""" for result in [f"""
{conv['quote'][quote.upper()]['price']} \
{quote.upper()}""" for quote in right] for conv in response['data']])
    except Exception as exception:
        await error_callback(
            u"Erro contatando coinmarketcap.com",
            message,
            exception,
            ['cryptoforex', 'price'],
        )
        return """Erro tentando calcular preço. O pessoal que cuida do \
desenvolvimento já foi avisado, eu acho..."""

## Aiogram
async def add_handlers(dispatcher):
    try:
        ## Lista o "preço" atual da criptomoeda
        @dispatcher.message_handler(
            commands=['price', 'p'],
        )
        async def price_callback(message):
            await message_callback(
                message,
                ['price', message.chat.type],
            )
            await price(dispatcher, message, 'USD', 'price')

        # ## Dados de exchanges brasileiras
        # @dispatcher.message_handler(
        #     commands=['preco'],
        # )
        # async def preco_callback(message):
        #     await message_callback(message, ['preco', message.chat.type])
        #     await price(dispatcher, message, 'BRL', 'preco')
    #         moeda = message.get_args()[1]
    #         ## FIXME
    #         response = [
    #             '',
    #             {
    #                 'ticker': {
    #                     'last': 1.0,
    #                     'high': 1.0,
    #                     'low': 1.0,
    #                     'vol': 1.0,
    #                     'buy': 1.0,
    #                     'sell': 1.0,
    #                 },
    #             },
    #         ]
    #         texto = list()
    #         texto.append('Informação das ultimas 24 horas para %s (de mercadobitco\
    # in.com.br)' % (str(moeda)))
    #         texto.append('\nValor')
    #         texto.append('atual: R$ %s' % (
    #             '{:,.2f}'.format(float(response[1]['ticker']['last']))))
    #         texto.append('maior: R$ %s' % (
    #             '{:,.2f}'.format(float(response[1]['ticker']['high']))))
    #         texto.append('menor: R$ %s' % (
    #             '{:,.2f}'.format(float(response[1]['ticker']['low']))))
    #         texto.append('\nVolume: %s BTC' % (
    #             '{:,.8f}'.format(float(response[1]['ticker']['vol']))))
    #         texto.append('\nMaior oferta de')
    #         texto.append('compra: R$ %s' % (
    #             '{:,.2f}'.format(float(response[1]['ticker']['buy']))))
    #         texto.append('venda: R$ %s' % (
    #             '{:,.2f}'.format(float(response[1]['ticker']['sell']))))
    #         command = await message.reply(texto)
    #         await command_callback(command, ['preco', message.chat.type])

        ## Converte valores entre moedas (criptomoeda ou fiduciário)
        @dispatcher.message_handler(
            commands=['conv', 'convert', 'converter', 'c'],
        )
        async def conv_callback(message):
            await message_callback(message, ['conv', message.chat.type])
            command = await message.reply(await conv(dispatcher,
                message))
            await command_callback(
                command,
                ['conv', message.chat.type],
            )
    except Exception as exception:
        logger.warning(f"""Error importing plugin {__name__}: \
{repr(exception)}""")
        raise
