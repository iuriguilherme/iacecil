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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

### Lista de textos gerados aleatoriamente
## FIXME Sentenças adicionadas manualmente a partir das respostas de usuários.
## Nenhuma dessas frases é criação ou responsabilidade dos desenvolvedores, são
## as pessoas no Telegram ensinando a bot. Criar um sistema de filtro com banco
## de dados e machine learning vai diminuir o trabalho manual, mas também vai
## criar resultados potencialmente indesejados (por razões óbvias).

import logging
logger = logging.getLogger(__name__)

import random

try:
    import instance.personalidades.pave.random_texts as pave
except Exception as exception:
    import plugins.personalidades.pave.random_texts as pave
    logger.debug(u"Não consegui achar o arquivo: {}".format(
        repr(exception)))

def adjetivos():
    return pave.adjetivos() + [
        u"direitopata",
        u"esquerdopata",
        u"gentalha",
    ]

def respostas_adjetivos():
    return random.choice(adjetivos())

def piadas():
    return pave.piadas()

def respostas_piadas():
    return random.choice(piadas())

def ignorante(admin):
    return pave.ignorante(admin)

def respostas_ignorante(admin):
    return random.choice([
        ignorante(admin),
        piadas(),
        respostas_adjetivos(),
    ])

def bebidas():
    return pave.bebidas()

def respostas_bebida():
    return random_texts.respostas_bebida()

def bye(admin):
    return pave.bye(admin)

def respostas_bye(admin):
    return random.choice(bye(admin))

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
