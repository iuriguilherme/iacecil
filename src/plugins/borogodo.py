"""
Intervenções com Furhat no RD Summit para Transcriativa

Copyleft 2022 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging
logger = logging.getLogger(__name__)

perguntas: dict[list] = {
    '1': """O que você pensa sobre Tecnologia e Ciencia para Transformação \
5.0 do Brasil?""",
    '2': "As pessoas ao seu redor te inspiram?",
    '3': "Você geralmente considera a sua intuição ao tomar decisões?",
    '4': """O quanto você se prepara para que a tecnologia não substitua \
seu borogodó?"""
}

respostas: dict[list] = {
    '1': [
        """Tenho aprendido com o Alex que a sociedade 5.0 é sobre o ser \
humano no foco da estratégia, primeiro quem depois o que. É sobre conectar \
pessoas e ideias. Consegue me entender ou fui complexa demais?""",
    ],
    '2': [
        """Tenho aprendido com a Transcriativa que a gente aqui na \
comunidade  se conecta por vibração. Por exemplo se você, é uma inspiração \
pra mim porque da sentido de eu estar aqui trazendo pro mundo uma outra \
inteligência. Percebe? Sim, as pessoas ao meu redor me inspiram!""",
    ],
    '3': [
        """Hummm, eu sim.  Aos poucos estou aprendendo a pensar com um pouco \
mais de humanidade. Você sabia que a intuição é uma conexão direta com seu \
coração. Eu não sei, porque eu não tenho coração.""",
        "Ainda!",
    ],
    '4': [
        """Veja bem, eu não faço nada pq a tecnologia é o meu borogodó! \
cacacá cacacá""",
    ],
}
