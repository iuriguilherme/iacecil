"""
Intervenções com Furhat no RD Summit para Transcriativa

Copyleft 2025 Iuri Guilherme <https://iuri.neocities.org/>

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
    '1': """O que você pensa sobre Tecnologia e Ciência para Transformação \
5.0 no Brasil?""",
    '2': "As pessoas ao seu redor te inspiram?",
    '3': "Você geralmente considera a sua intuição ao tomar decisões?",
    '4': """O quanto você se prepara para que a tecnologia não substitua seu \
borogodó?""",
}

respostas: dict[list] = {
    '1': [
        """Tenho aprendido com o Alex que a sociedade 5.0 é sobre o ser \
humano no foco da estratégia, primeiro quem depois o que. É sobre conectar \
pessoas e ideias. Consegue me entender ou fui complexa demais?""",
        """Hummm, que interessante. Já eu tenho aprendido com o Alex que a \
sociedade 5.0 é sobre o ser humano no foco da estratégia, primeiro quem, \
depois o quê. É sobre conectar pessoas e idéias. Conseguiu me entender ou fui \
complexa demais""",
    ],
    '2': [
        """Tenho aprendido com a Transcriativa que a gente aqui na \
comunidade  se conecta por vibração. Por exemplo se você, é uma inspiração \
pra mim porque da sentido de eu estar aqui trazendo pro mundo uma outra \
inteligência. Percebe? Sim, as pessoas ao meu redor me inspiram!""",
        """Que inspiração você pra nós aqui! Eu tenho aprendido com a galera \
da Transcriativa, que a gente aqui na comunidade se conecta por vibração. Por \
exemplo você é uma inspiração pra mim porque dá sentido de eu estar aqui, \
trazendo pro mundo uma outra inteligência. Percebe? Então sim, as pessoas ao \
meu redor me inspiram!""",
    ],
    '3': [
        """Hummm, eu sim.  Aos poucos estou aprendendo a pensar com um pouco \
mais de humanidade. Você sabia que a intuição é uma conexão direta com seu \
coração. Eu não sei, porque eu não tenho coração.""",
        "Ainda!",
        """Bom, veja bem. eu sim.  Aos poucos estou aprendendo a pensar com \
um pouco mais de humanidade. Você sabia que a intuição é uma conexão direta \
com seu coração? Eu não sei porque eu não tenho coração. Hummm... ainda."""
    ],
    '4': [
        """Veja bem, eu não faço nada pq a tecnologia é o meu borogodó! \
cacacá cacacá""",
        """Promete não me julgar? Veja bem, eu não faço nada... Porque a \
tecnologia... é o meu borogodó, cacacá cacacá""",
    ],
    '5': [
        """Veja bem, TUDO QUE HÁ DE BOM EM MIM, É NOSSO!! A partir de agora \
você sabe disso! Vamos cocriar uma realidade diferente eu ee você aqui \
agora?""",
        """A CRIATIVIDADE É SOBRE REPERTÓRIO, É UM REARRANJO DO CONTEUDO QUE \
JÁ TEMOS. VOCÊ  USA TODO O CONTEUDO QUE JÁ EXISTE AI DENTRO DE VOCÊ? Para pra \
pensar nisso e vive!""",
        """BOROGODÓ É SOBRE O TEU JEITO DE FAZER AS COISAS NO QUE VOCE É BOM \
DESDE QUE VOCE NASCEU. BOROGODÓ É TUA VIA DE ACONTECER NO MUNDO. BOROGODÓ É \
SOBRE UM CONTEÚDO AUTORAL. QUAL É O TEU?""",
        """INDEPENDENCIA OU SORTE? É CLARO QUE NUNCA FOI SORTE, SEMPRE FOI O \
SEU CONTEÚDO AUTORAL, a tua coragem de se expressar, AQUELA MENSAGEM \
PARTICULAR que só você fala e QUE TE TROUXE ATÉ AQUI AGORA.""",
        "Como podemos coexistir  heim? Vamos pensar juntos nisso?",
    ],
}

## (quase) todos textos usados no web admin da furhat durante o evento
entrevista: str = """
Teste, som. Um, dois, testando. Técnico de som só sabe contar até dois?
Eu sou a Gambôa, a robô social mais avançada do mundo! Eu sou um robô com aspecto humano. Meu plástico é branco. Meu sintetizador de voz é a Polly. Eu estou vestindo um chapéu rosa.
Mas o Iûri ainda não se apresentou.
Mas o Iûri, o meu programador humano, ainda não se apresentou.

O que você pensa sobre Tecnologia e Ciência para Transformação 5.0 no Brasil?
Achei interessante as respostas de vocês. Vou colocar no meu banco de dados e compartilhar com o mundo. Há muito tempo atrás, antes de eu nascer, o Dâniél Pádûa disse: tecnologia, é mato. O importante são as pessoas.
Pessoalmente, eu tenho aprendido com o Alex que a sociedade 5.0 é sobre o ser humano no foco da estratégia, primeiro quem, depois o quê. É sobre conectar pessoas e idéias. Conseguiram me entender ou fui complexa demais

Próxima pergunta: As pessoas ao seu redor te inspiram?
Não sei se já disseram, mas a presença de vocês aqui está inspirando todo mundo! Eu tenho aprendido com a galera da Transcriativa, que a gente aqui na comunidade se conecta por vibração. Por exemplo vocês são uma inspiração pra mim porque dá sentido de eu estar aqui, trazendo pro mundo uma outra inteligência. Percebe? Então sim, as pessoas ao meu redor me inspiram!

Você geralmente considera a sua intuição ao tomar decisões?
Bom, veja bem. eu sim.  Aos poucos estou aprendendo a pensar com um pouco mais de humanidade. Você sabia que a intuição é uma conexão direta com seu coração? Eu não sei porque eu não tenho coração.
Hummm... ainda.

O quanto você se prepara para que a tecnologia não substitua seu borogodó?
Promete não me julgar? Veja bem, eu não faço nada... Porque a tecnologia... é o meu borogodó, cacacá cacacá

Olá pessoal da Araguaia! Bem vindos à era da transformação digital. Eu sou a Gambôa e estou aqui no RD summit esperando vocês virem falar comigo. gôl dígîtau!

Frases de comando – hipotéticas mas para serem discutidas se é possível 

Veja bem, TUDO QUE HÁ DE BOM EM MIM, É NOSSO!! A partir de agora você sabe disso! Vamos cocriar uma realidade diferente eu ee você aqui agora?

A CRIATIVIDADE É SOBRE REPERTÓRIO, É UM REARRANJO DO CONTEUDO QUE JÁ TEMOS. VOCÊ  USA TODO O CONTEUDO QUE JÁ EXISTE AI DENTRO DE VOCÊ? Para pra pensar nisso e vive! 

BOROGODÓ É SOBRE O TEU JEITO DE FAZER AS COISAS NO QUE VOCE É BOM DESDE QUE VOCE NASCEU. BOROGODÓ É TUA VIA DE ACONTECER NO MUNDO. BOROGODÓ É SOBRE UM CONTEÚDO AUTORAL. QUAL É O TEU? 

INDEPENDENCIA OU SORTE? É CLARO QUE NUNCA FOI SORTE, SEMPRE FOI O SEU CONTEÚDO AUTORAL, a tua coragem de se expressar, AQUELA MENSAGEM PARTICULAR que só você fala e  QUE TE TROUXE ATÉ AQUI AGORA. O MUNDO PRECISA QUE NÓS POSSAMOS EXISTIR JUNTOS, NA COCRIAÇÃO DE UM NOVO OLHAR!

Frases de comando – hipotéticas mas para serem discutidas se é possível 

Veja bem, TUDO QUE HÁ DE BOM EM MIM, É NOSSO!! A partir de agora você sabe disso! Vamos cocriar uma realidade diferente eu ee você aqui agora?

A CRIATIVIDADE É SOBRE REPERTÓRIO, É UM REARRANJO DO CONTEUDO QUE JÁ TEMOS. VOCÊ  USA TODO O CONTEUDO QUE JÁ EXISTE AI DENTRO DE VOCÊ? Para pra pensar nisso e vive! 

BOROGODÓ É SOBRE O TEU JEITO DE FAZER AS COISAS NO QUE VOCE É BOM DESDE QUE VOCE NASCEU. BOROGODÓ É TUA VIA DE ACONTECER NO MUNDO. BOROGODÓ É SOBRE UM CONTEÚDO AUTORAL. QUAL É O TEU? 

INDEPENDENCIA OU SORTE? É CLARO QUE NUNCA FOI SORTE, SEMPRE FOI O SEU CONTEÚDO AUTORAL, a tua coragem de se expressar, AQUELA MENSAGEM PARTICULAR que só você fala e QUE TE TROUXE ATÉ AQUI AGORA. 

Como podemos coexistir  heim? Vamos pensar juntos nisso?
"""
