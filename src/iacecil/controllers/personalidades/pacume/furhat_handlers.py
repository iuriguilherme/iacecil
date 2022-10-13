"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import random
from ....models import Iteration

try:
    from instance.personalidades.pacume import random_texts
except Exception as e:
    logger.debug(f"random_texts em instance não encontrada para {__name__}")
    # ~ logger.exception(e)
    from . import random_texts

async def furhat_papagaio(config, message):
    return message.split(' ')[1:]

async def furhat_naoentendi(config, message):
    return u"Não entendi"

async def furhat_naosou(config, message):
    return random.choice([
        u"Acho que tu me confundiu",
        u"Eu tenho cara de robô?",
    ])

async def furhat_sevira(config, message):
    return u"Eu não sou {}, {}".format(
        random.choice([
            u"a Alexa",
            u"o OK Google",
            u"a Siri",
        ]),
        random.choice([
            u"usa o teu cêlôlá",
            u"se vira",
            u"",
        ]),
    )

async def furhat_quanto(config, message):
    return random_texts.respostas_quanto()

async def furhat_bebida(config, message):
    return random_texts.respostas_bebida()

async def furhat_versiculo(config, message):
    return random_texts.versiculos_md()

async def furhat_piada(config, message):
    return random_texts.respostas_piadas().lower()

async def furhat_rima_ao(config, message):
    if len(message.split(' ')[-1]) > 3:
        return random_texts.rimas_ao().lower()

async def furhat_replica_adjetivo(config, message):
    for adjetivo in random_texts.adjetivos():
        for submessage in message.split(' '):
            if adjetivo.lower() == submessage.lower():
                return adjetivo.lower() + ' é tu. E tu é um {}.'.format(
                    random_texts.respostas_adjetivos().lower()
                )

async def furhat_adjetivo(config, message):
    return 'tu é um {}.'.format(
        random_texts.respostas_adjetivos().lower())

async def furhat_ignorante(config, message):
    return random_texts.respostas_ignorante('Iuri')

async def furhat_tchau(config, message):
    return random_texts.respostas_bye('Iuri')

async def furhat_menine(config, message):
    return 'o certo é: meni-ne.'

async def furhat_startswith_iterations():
    return [
        Iteration(text = 'repete', callback = furhat_papagaio),
        Iteration(text = 'vai', callback = furhat_ignorante),
        Iteration(text = 'quanto custa', callback = furhat_quanto),
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_naosou,
        ) for subtext in [
            'alexa',
            'google',
            'siri',
        ]
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_sevira,
        ) for subtext in [
            'fab',
            'fabi',
            'fáb',
            'fábi',
            'fábio',
            'fabio',
        ]
    ]

async def furhat_endswith_iterations():
    return [
        Iteration(text = 'por favor', callback = furhat_naoentendi),
        Iteration(text = 'ão', callback = furhat_rima_ao),
        Iteration(text = 'é tu', callback = furhat_adjetivo),
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_naosou,
        ) for subtext in [
            'alexa',
            'a lexa',
            'google',
            'siri',
        ]
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_sevira,
        ) for subtext in [
            'fab',
            'fabi',
            'fáb',
            'fábi',
            'fábio',
            'fabio',
        ]
    ]

async def furhat_contains_iterations():
    return [
        Iteration(text = 'tchau', callback = furhat_tchau),
        Iteration(text = 'piada', callback = furhat_piada),
        Iteration(text = 'bíblia', callback = furhat_versiculo),
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_naosou,
        ) for subtext in [
            'alexa',
            'google',
            'siri',
        ]
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_replica_adjetivo,
        ) for subtext in set(random_texts.adjetivos())
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_bebida,
        ) for subtext in set(random_texts.bebidas())
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_menine,
        ) for subtext in [
            'menina',
            'menino',
        ]
    ]
