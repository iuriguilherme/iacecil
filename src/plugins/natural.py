"""
Plugin natural para ia.cecil: PLN com NLTK

ia.cecil

Copyleft 2025 Iuri Guilherme <https://iuri.neocities.org/>

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

import io
import nltk
import pandas
import string
from aiogram import (
    Dispatcher,
    filters,
)
from contextlib import redirect_stdout
from io import BytesIO
from matplotlib import pyplot
from nltk import (
    word_tokenize
)
from iacecil.controllers.persistence.zodb_orm import (
    get_aiogram_messages,
    get_aiogram_messages_texts,
    get_messages_texts_list,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    message_callback,
    error_callback,
    exception_callback,
)

async def remove_punctuation(sent_list):
    try:
        return [word for word in sent_list if not any([(punctuation in \
            word) for punctuation in string.punctuation])]
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def remove_punctuation_1(sent_list):
    try:
        return [''.join([word.replace(punctuation, '') for punctuation \
            in string.punctuation]) for word in sent_list]
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def tokenize_list(sent_list):
    try:
        # ~ sent_list = await remove_punctuation_1(sent_list)
        return word_tokenize(' '.join([word for sent in sent_list for \
            word in sent.split(' ')]))
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def text_from_list(sent_list):
    try:
        text = await tokenize_list(sent_list)
        return nltk.Text(text)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def lexical_diversity(text):
    return len(set(text))

async def percentage(word, text):
    return (100 * word) / text

async def generate(sent_list):
    try:
        text = await text_from_list(sent_list)
        return text.generate()
    except ValueError:
        return "nada pra gerar"
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def collocations(sent_list):
    try:
        text = await text_from_list(sent_list)
        return text.collocations()
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def concordance(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        concordances = text.concordance_list(word)
        return concordances
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def concordance_1(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        with redirect_stdout(io.StringIO()) as f:
            text.concordance_list(word)
        return f.getvalue()
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def count(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        return text.count(word)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def count_1(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        count = text.count(word)
        lexical_diversity = len(set(text))
        percentage = 100 * count / lexical_diversity
        return {
            'count': count,
            'percentage': percentage,
        }
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def similar(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        return text.similar(word)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def similar_1(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        with redirect_stdout(io.StringIO()) as f:
            text.similar(word)
        return f.getvalue()
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def common_contexts(sent_list, words):
    try:
        text = await text_from_list(sent_list)
        return text.common_contexts(words)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def common_contexts_1(sent_list, words):
    try:
        text = await text_from_list(sent_list)
        with redirect_stdout(io.StringIO()) as f:
            text.common_contexts(words)
        return f.getvalue()
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def dispersion_plot(sent_list, words):
    try:
        text = await text_from_list(sent_list)
        return text.dispersion_plot(words)
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def dispersion_plot_1(sent_list, words):
    try:
        text = list(await text_from_list(sent_list))
        words.reverse()
        words_to_comp = list(map(str.lower, words))
        text_to_comp = list(map(str.lower, text))
        points = [
            (x, y)
            for x in range(len(text_to_comp))
            for y in range(len(words_to_comp))
            if text_to_comp[x] == words_to_comp[y]
        ]
        if points:
            x, y = list(zip(*points))
        else:
            x = y = ()
        pyplot.plot(x, y, "b|", scalex=0.1)
        pyplot.yticks(list(range(len(words))), words, color = "b")
        pyplot.ylim(-1, len(words))
        pyplot.title("dispersão léxica: uso do termo ao longo do tempo")
        pyplot.xlabel("<== mais recente para mais antigo ==>")
        figure_buffer = BytesIO()
        pyplot.savefig(figure_buffer, format = "png")
        return figure_buffer
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def add_handlers(dispatcher: Dispatcher) -> None:
    """Register Aiogram Handlers to Dispatcher"""
    try:
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['ngen', 'ngenerate'],
        )
        async def ngenerate_callback(message):
            await message_callback(message, ['natural', 'generate',
                message.chat.type])
            limit = None
            if len(message.get_args()) > 0:
                limit = int(message.get_args())
            texts = await get_aiogram_messages_texts(
                bot_id = dispatcher.bot.id,
                chat_id = message.chat.id,
                offset = 0,
                limit = limit,
            )
            generated = await generate(texts[1])
            command = await message.reply(generated)
            await command_callback(command, ['natural',
                'generate', message.chat.type])
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['ncnt', 'ncount'],
        )
        async def ncount_callback(message):
            await message_callback(message, ['natural', 'count',
                message.chat.type])
            word = None
            command = None
            if len(message.get_args()) > 0:
                word = message.get_args()
            if word is not None:
                texts = await get_aiogram_messages_texts(
                    bot_id = dispatcher.bot.id,
                    chat_id = message.chat.id,
                    offset = 0,
                    limit = None,
                )
                counted = await count_1(texts[1], word)
                command = await message.reply(u"""{} já foi dito aqui \
{} vezes, sendo {:.2f}% do que já foi dito.""".format(word,
                    counted['count'], counted['percentage']))
                await command_callback(command, ['natural',
                    'count', message.chat.type])
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['nsim', 'nsimilar'],
        )
        async def nsimilar_callback(message):
            await message_callback(message, ['natural', 'similar',
                message.chat.type])
            word = None
            command = None
            if len(message.get_args()) > 0:
                word = message.get_args()
            if word is not None:
                texts = await get_aiogram_messages_texts(
                    bot_id = dispatcher.bot.id,
                    chat_id = message.chat.id,
                    offset = 0,
                    limit = None,
                )
                similars = await similar_1(texts[1], word)
                command = await message.reply(
                    u"palavras similares a {}:\n{}".format(
                    word, similars)
                )
                await command_callback(command, ['natural',
                    'similar', message.chat.type]
                )
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['ncon', 'nconcordance'],
        )
        async def nconcordance_callback(message):
            await message_callback(message, ['natural', 'concordance',
                message.chat.type])
            word = None
            command = None
            if len(message.get_args()) > 0:
                word = message.get_args()
            if word is not None:
                texts = await get_aiogram_messages_texts(
                    bot_id = dispatcher.bot.id,
                    chat_id = message.chat.id,
                    offset = 0,
                    limit = None,
                )
                concordances = await concordance_1(texts[1], word)
                command = await message.reply(
                    u"Concordâncias para {}:\n{}".format(
                    word, concordances)
                )
                await command_callback(command, ['natural',
                    'concordance', message.chat.type]
                )
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['ncom', 'ncontext'],
        )
        async def ncontext_callback(message):
            await message_callback(message, ['natural', 'context',
                message.chat.type])
            words = None
            command = None
            if len(message.get_args()) > 0:
                words = message.get_args().split(' ')
            if words not in [None, '', ' ']:
                texts = await get_aiogram_messages_texts(
                    bot_id = dispatcher.bot.id,
                    chat_id = message.chat.id,
                    offset = 0,
                    limit = None,
                )
                contexts = await common_contexts_1(texts[1], words)
                command = await message.reply(
                    u"Contextos comuns para {}:\n{}".format(
                    words, contexts)
                )
                await command_callback(command, ['natural', 'context',
                    message.chat.type])
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                    dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['nlex', 'ndispersion'],
        )
        async def ndispersion_callback(message):
            await message_callback(message, ['natural', 'dispersion', 
                message.chat.type])
            words = None
            command = None
            if len(message.get_args()) > 0:
                words = message.get_args().split(' ')
            if words not in [None, '', ' ']:
                texts = await get_aiogram_messages_texts(
                    bot_id = dispatcher.bot.id,
                    chat_id = message.chat.id,
                    offset = 0,
                    limit = None,
                )
                plot = BytesIO()
                try:
                    plot.close()
                    plot = await dispersion_plot_1(texts[1], words)
                    command = await message.reply_photo(
                        plot.getbuffer(), caption = u"""Dispersão léxic\
a para os termos: {}""".format(' '.join(words)))
                    await command_callback(command, ['natural',
                        'dispersion', message.chat.type])
                except Exception as exception:
                    await erro_callback(
                        u"Error trying to send graphic",
                        message,
                        exception,
                        ['natural', 'dispersion', 'exception'],
                    )
                finally:
                    plot.close()
        @dispatcher.message_handler(
            filters.IDFilter(
                user_id = dispatcher.config.telegram['users']['alpha'] + \
                dispatcher.config.telegram['users']['beta'],
            ),
            commands = ['nstats', 'nstatistics'],
        )
        async def nstatistics_callback(message):
            await message_callback(message, ['natural', 'statistics',
                message.chat.type])
            limit = None
            if message.get_args() not in [None, '', ' '] and \
                message.get_args().isdigit():
                limit = int(message.get_args())
            messages = await get_aiogram_messages(
                bot_id = dispatcher.bot.id,
                chat_id = message.chat.id,
                offset = 0,
                limit = limit,
            )
            dataframe_messages = [{
                'date': message['date'],
                'text': message.get('text', ''),
                'message_id': message['message_id'],
                'from_id': message['from']['id'],
                'from_is_bot': message['from']['is_bot'],
                'from_first_name': message['from']['first_name'],
                'from_last_name': message['from'].get('last_name', ''),
                'from_username': message['from'].get('username', ''),
                'from_language_code': message['from'].get(
                    'language_code', ''),
                } for message in messages[1]]
            df = pandas.DataFrame(dataframe_messages)
            texts = [message.get('text', '') for message in messages[1]]
            words = await text_from_list(texts)
            series = pandas.Series(words)
            reply_text = f"""
Estatísticas para {message.chat.mention}:

Mensagens pesquisadas: últimas {len(messages[1])} de um total de \
{messages[0]}
Total de palavras: {len(words)}
Diversidade léxica (porcentagem de palavras únicas): \
{(len(set(words)) / len(words)):.2f}% ({len(set(words))} palavras única\
s)
Palavra mais usada: {words.vocab().most_common(1)[0][0]} (\
{words.vocab().most_common(1)[0][1]} vezes)
Pessoa que escreve mais: \
{df['from_first_name'].value_counts().idxmax()} \
({len([message for message in dataframe_messages if 
message['from_first_name'] == df['from_first_name'
].value_counts().idxmax()])} mensagens)
"""
            command = await message.reply(reply_text)
            await command_callback(command, ['natural', 'statistics',
                message.chat.type])
    except Exception as e:
        logger.exception(e)
        raise
