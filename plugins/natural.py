# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
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

import logging
logger = logging.getLogger(__name__)

import io, nltk, string
from contextlib import redirect_stdout
from nltk import (
    word_tokenize
)
from iacecil.controllers.persistence.zodb_orm import (
    get_messages_texts_list
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

async def add_handlers(dispatcher):
    pass
