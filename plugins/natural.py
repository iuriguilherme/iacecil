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

import nltk, string
from nltk import (
    word_tokenize
)
from plugins.persistence.zodb_orm import (
    get_messages_texts_list
)

async def remove_punctuation(sent_list):
    try:
        return [word for word in sent_list if not any([(punctuation in \
            word) for punctuation in string.punctuation])]
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def tokenize_list(sent_list):
    try:
        sent_list = await remove_punctuation(sent_list)
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

async def generate(sent_list):
    try:
        text = await text_from_list(sent_list)
        logger.debug(str(text))
        return text.generate()
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
        logger.debug(str(text))
        concordances = text.concordance_list(word)
        return concordances
    except Exception as exception:
        logger.warning(repr(exception))
        raise

async def count(sent_list, word):
    try:
        text = await text_from_list(sent_list)
        logger.debug(str(text))
        return text.count(word)
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

async def common_contexts(sent_list, words):
    try:
        text = await text_from_list(sent_list)
        return text.common_contexts(words)
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
