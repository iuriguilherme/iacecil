# vim:fileencoding=utf-8
#  Plugin personalidades para ia.cecil: Robô também é gente?
#  Copyleft (C) 2020-2022 Iuri Guilherme <https://iuri.neocities.org/>
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
#  along with this program.
#  If not, see <http://www.gnu.org/licenses/>.

import logging
logger = logging.getLogger(__name__)

from iacecil.models import Iteration

try:
    from instance.personalidades.pave import random_texts
except Exception as exception:
    from iacecil.controllers.personalidades.pave import random_texts
    logger.debug(u"Não consegui achar o arquivo: {}".format(
        repr(exception)))

async def furhat_papagaio(config, message):
    return message.split(' ')[1:]

async def furhat_naoentendi(config, message):
    return u"Não entendi"

async def furhat_naosou(config, message):
    return u"Acho que tu me confundiu"

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

async def furhat_bebida(config, message):
    return random_texts.respostas_bebida()

async def furhat_versiculo(config, message):
    return random_texts.versiculos_md()

async def furhat_adjetivo(config, message):
    for adjetivo in random_texts.adjetivos():
        for submessage in message.split(' '):
            if adjetivo == submessage:
                return adjetivo + ' é tu. E tu é um {}'.format(
                    random_texts.respostas_adjetivos()
                )

async def furhat_tchau(config, message):
    return random_texts.respostas_bye('Iuri')

async def furhat_startswith_iterations():
    return [
        Iteration(text = 'repete', callback = furhat_papagaio),
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

async def furhat_contains_iterations():
    return [
        Iteration(text = 'tchau', callback = furhat_tchau),
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
            callback = furhat_adjetivo,
        ) for subtext in set(random_texts.adjetivos())
    ] + [
        Iteration(
            text = subtext,
            callback = furhat_bebida,
        ) for subtext in set(random_texts.bebidas())
    ]
