"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2025 Iuri Guilherme <https://iuri.neocities.org/>

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

### Lista de textos gerados aleatoriamente
## FIXME Sentenças adicionadas manualmente a partir das respostas de usuários.
## Nenhuma dessas frases é criação ou responsabilidade dos desenvolvedores, são
## as pessoas no Telegram ensinando a bot. Criar um sistema de filtro com banco
## de dados e machine learning vai diminuir o trabalho manual, mas também vai
## criar resultados potencialmente indesejados (por razões óbvias).

import logging
logger = logging.getLogger(__name__)

import random

from aiogram import types

try:
    import instance.personalidades.pave.random_texts as pave
except Exception as e:
    logger.debug("""random_texts em instance não encontrada para pave \
(hardcoded)""")
    # ~ logger.exception(e)
    try:
        from ..pave import random_texts as pave
    except Exception as e1:
        logger.debug("no random_texts at all for pave (hardcoded)")
        # ~ logger.exception(e1)

def adjetivos():
    return set().union(pave.adjetivos(), set([
        u"direitopata",
        u"esquerdopata",
        u"gentalha",
    ]))

def respostas_adjetivos():
    return random.choice(list(adjetivos()))

def piadas():
    return set().union(pave.piadas())

def respostas_piadas():
    return random.choice(list(piadas()))

def ignorante(admin):
    return set().union(pave.ignorante(admin))

def respostas_ignorante(admin):
    return random.choice(list(set().union(
        ignorante(admin),
        piadas(),
        adjetivos(),
    )))

def bebidas():
    return set().union(pave.bebidas())

def respostas_bebida():
    return random_texts.respostas_bebida()

def bye(admin):
    return set().union(pave.bye(admin))

def respostas_bye(admin):
    return random.choice(list(bye(admin)))

def respostas_quanto():
    return pave.respostas_quanto()

def versiculos_md():
    return pave.versiculos_md()

def rimas_ao():
    return random.choice([
        u"e tu, que é um trouxão?",
    ])

def start(message):
    return pave.start(message)

def welcome(message, count, admin):
    return pave.welcome(message, count, admin)

def chatgpt_prompt(message: types.Message) -> str:
    """Get personalidade ChatGPT Prompt"""
    return pave.chatgpt_prompt(message, name = "Tiozão do Churrasco")
